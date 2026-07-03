#!/usr/bin/env python3
"""Procheiron conformance runner (roadmap 4.2). Stdlib-only, read-only on the repo.

Runs the SAME reference implementation (resolver + validator + authority policy)
against every fixture in `manifest.json` and checks each reaches its declared verdict:

  - kind "pass": the validator returns PASS / PASS_WITH_WARNINGS with NO errors.
    Positive fixtures (generic-vault, minimal-vault) are stored, complete deployments.
  - kind "fail": a NEGATIVE — a single declared tamper is applied to a fresh COPY of
    the generic vault in a tempdir, validated, then discarded. The validator MUST FAIL
    and every `expect_reasons` substring must appear. Negatives are generated, not
    stored, so no duplicated trees and no secret-shaped strings live in the repo.

The headline this earns — and ONLY this, at fixture level — is:
"a second deployment passes conformance." Not "portable", not "production-replicable".

Usage:  python3 run_conformance.py [--json] [--reference DIR]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List

HERE = Path(__file__).resolve().parent
GENERIC = HERE / "generic-vault"
SRC = HERE.parent / "src"  # de-vendored: the ONE Core validator lives in the package, not the fixture


# --------------------------------------------------------------- negative tampers
def _edit_jsonl(p: Path, fn: Callable[[List[dict]], List[dict]]) -> None:
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    p.write_text("\n".join(json.dumps(r) for r in fn(rows)) + "\n", encoding="utf-8")


_ACTIVE = "mem_20260612_meridian_procheiron_adoption_commons_definition"


def _t_secret(d: Path) -> None:
    # write a secret-SHAPED string at test time (never stored in the repo)
    with (d / "console" / "BLOCKERS.md").open("a", encoding="utf-8") as fh:
        fh.write("\n<!-- leaked --> AKIA" + "0123456789ABCDEF" + "\n")


def _t_missing_file(d: Path) -> None:
    (d / "console" / "PROCHEIRON.md").unlink()


def _t_absolute_path(d: Path) -> None:
    def fn(rows):
        for r in rows:
            if r.get("status") == "candidate":
                r["source_paths"] = ["/etc/hosts"]
                break
        return rows
    _edit_jsonl(d / "memory" / "index" / "memories.jsonl", fn)


def _t_active_without_review(d: Path) -> None:
    def fn(rows):
        return [e for e in rows if not (e.get("memory_id") == _ACTIVE and "promot" in str(e.get("action", "")))]
    _edit_jsonl(d / "memory" / "index" / "audit.jsonl", fn)


def _t_self_reviewed(d: Path) -> None:
    def fn(rows):
        for r in rows:
            if r.get("id") == _ACTIVE:
                r["reviewed_by"] = r["created_by"]
        return rows
    _edit_jsonl(d / "memory" / "index" / "memories.jsonl", fn)


def _t_prose_supersession(d: Path) -> None:
    def fn(rows):
        for r in rows:
            if r.get("status") == "candidate":
                r["notes"] = (r.get("notes") or "") + " This record supersedes mem_20260101_meridian_phantom_record entirely."
                break
        return rows
    _edit_jsonl(d / "memory" / "index" / "memories.jsonl", fn)


def _t_dangling_token(d: Path) -> None:
    cfg = d / ".procheiron" / "config.yaml"
    cfg.write_text("\n".join(l for l in cfg.read_text().splitlines()
                             if not l.strip().startswith("wiki:")) + "\n", encoding="utf-8")


def _t_weld(d: Path) -> None:
    with (d / "console" / "PROCHEIRON.md").open("a", encoding="utf-8") as fh:
        fh.write("\nDeployed for MeridianAtelier.\n")


def _t_tilde_weld(d: Path) -> None:
    # A home-relative (~/…) deployment path re-welded into a Core doc. Distinct
    # from _t_weld (a deployment literal): this guards the ABSOLUTE_PATH_RE tilde
    # arm — before that arm existed, ~/ paths slipped the structural weld check.
    with (d / "console" / "PROCHEIRON.md").open("a", encoding="utf-8") as fh:
        fh.write("\nDeployed under ~/.local/share/vault/console on the host.\n")


TAMPERS: Dict[str, Callable[[Path], None]] = {
    "secret": _t_secret, "missing-file": _t_missing_file, "absolute-path": _t_absolute_path,
    "active-without-review": _t_active_without_review, "self-reviewed": _t_self_reviewed,
    "prose-supersession": _t_prose_supersession, "dangling-token": _t_dangling_token,
    "weld": _t_weld, "tilde-weld": _t_tilde_weld,
}


# --------------------------------------------------------------- validators
def _env() -> Dict[str, str]:
    env = dict(os.environ)
    env.setdefault("PROCHEIRON_READ_LOG", "/tmp/procheiron_conformance_reads.jsonl")
    return env


def run_validator(root: Path) -> Dict[str, Any]:
    """Run the ONE Core validator (the package) against a deployment root.
    De-vendored: a fixture no longer ships its own validator copy, so conformance proves
    'the Core validator passes a second deployment' — not 'a copy validates itself'."""
    env = _env()
    env["PYTHONPATH"] = str(SRC) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    cmd = ["python3", "-m", "procheiron.validate",
           "--root", str(root), "--records", "--json"]
    if (root / ".procheiron" / "profiles").is_dir():
        cmd += ["--profiles-dir", str(root / ".procheiron" / "profiles")]
    return _parse(subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120))


def run_minimal(root: Path) -> Dict[str, Any]:
    val = HERE.parent / "examples" / "minimal-adopter" / "validate_minimal.py"
    return _parse(subprocess.run(["python3", str(val), "--root", str(root), "--json"],
                                 capture_output=True, text=True, env=_env(), timeout=120))


def _parse(proc: subprocess.CompletedProcess) -> Dict[str, Any]:
    out = proc.stdout.strip()
    try:
        return json.loads(out) if out.startswith("{") else {"status": "CRASH", "errors": [proc.stderr[-400:] or "no json"]}
    except json.JSONDecodeError as exc:
        return {"status": "CRASH", "errors": [f"json parse: {exc}", proc.stderr[-300:]]}


def run_negative(tamper: str) -> Dict[str, Any]:
    tmp = Path(tempfile.mkdtemp(prefix="pk_conf_"))
    try:
        dst = tmp / "vault"
        shutil.copytree(GENERIC, dst, ignore=shutil.ignore_patterns("__pycache__"))
        TAMPERS[tamper](dst)
        return run_validator(dst)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------- doctrine currency
# ponytail: marker-presence check, not full doctrine equivalence. The package ships no
# single in-repo canonical SELF_ACTION_POLICY to hash against, so we assert the shipped
# fixture constitution carries CURRENT doctrine (the 4.6 preservation-executor
# generalization). A stale pre-4.6 constitution — the 0.1.0 release bug — fails here.
# Upgrade path: hash the fixture against a canonical in-repo doctrine source once one exists.
DOCTRINE_MARKERS = ("## 13. Preservation executor policy", "Core does not require git")


def check_doctrine_currency() -> Dict[str, Any]:
    pol = GENERIC / "console" / "SELF_ACTION_POLICY.md"
    text = pol.read_text(encoding="utf-8") if pol.is_file() else ""
    missing = [m for m in DOCTRINE_MARKERS if m not in text]
    ok = not missing
    detail = ("current 4.6 preservation-executor doctrine present" if ok
              else f"STALE constitution shipped — missing doctrine marker(s): {missing}")
    return {"name": "doctrine currency (generic-vault constitution)", "kind": "guard", "ok": ok, "detail": detail}


# --------------------------------------------------------------- evaluate + main
def evaluate(fx: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    status, errors = result.get("status", "CRASH"), result.get("errors", []) or []
    if fx["kind"] == "pass":
        ok = status in ("PASS", "PASS_WITH_WARNINGS") and not errors
        detail = f"status={status} errors={len(errors)}" + (f" :: {errors[0][:110]}" if not ok and errors else "")
    else:
        missing = [r for r in fx.get("expect_reasons", []) if r not in " || ".join(errors)]
        ok = status in ("FAIL", "CRASH") and not missing
        detail = f"status={status} errors={len(errors)} unmatched_reasons={missing}"
    return {"name": fx["name"], "kind": fx["kind"], "ok": ok, "detail": detail}


def main() -> int:
    ap = argparse.ArgumentParser(description="Procheiron conformance suite runner.")
    ap.add_argument("--manifest", type=Path, default=HERE / "manifest.json")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    fixtures = json.loads(args.manifest.read_text(encoding="utf-8"))["fixtures"]
    results = []
    for fx in fixtures:
        if fx.get("tamper"):
            results.append(evaluate(fx, run_negative(fx["tamper"])))
            continue
        root = (HERE / fx["root"]).resolve()
        if not root.is_dir():
            results.append({"name": fx["name"], "kind": fx["kind"], "ok": False, "detail": f"missing dir {root}"})
            continue
        result = run_minimal(root) if fx.get("validator") == "minimal" else run_validator(root)
        results.append(evaluate(fx, result))

    results.append(check_doctrine_currency())  # shipped constitution must carry current doctrine

    passed = sum(1 for r in results if r["ok"])
    report = {"validator": "procheiron package (src/procheiron)", "passed": passed, "total": len(results),
              "all_green": passed == len(results), "results": results}
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("== Procheiron conformance suite (validator: procheiron package) ==")
        for r in results:
            print(f"  [{'PASS' if r['ok'] else 'FAIL'}] {r['kind']:>4}  {r['name']:<46} {r['detail']}")
        print(f"  ----> {passed}/{len(results)} fixtures reached their declared verdict")
        print("  ==> GREEN. At fixture level: a second deployment passes conformance."
              if report["all_green"] else "  ==> RED. See failures above.")
    return 0 if report["all_green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
