#!/usr/bin/env python3
"""Procheiron authority policy — evaluator (roadmap 3.2).

Two execution backends, ONE semantics:
- if `opa` is on PATH: shell to `opa eval` against procheiron.rego (the production
  path once opa is adopted — a single static binary, no daemon);
- otherwise: a stdlib-only reference evaluator that mirrors procheiron.rego line
  for line, reading the SAME policy_data.json.

The reference backend is the executable spec for now (opa is a static-binary
install, deferred to adoption). ../tests/test_policy.py drives shared cases
through the reference backend AND, when opa is present, asserts opa agrees.

This is what validate/promote/proposer/MCP call to authorize an action:
  decide({"actor": ..., "gate": ..., "level": ..., "reviewer": ...,
          "reviewers_completed": [...], "approver": ..., "approver_role": ...,
          "transition": {"from": ..., "to": ...}}) -> {"allow": bool, ...}
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List


def _same_identity(a: Any, b: Any) -> bool:
    """Identity equality for self-review/self-approval checks. When both sides are
    strings, compare NFKC + casefold — matching the validator's norm_actor — so a
    case or unicode-width variant of the actor's own name ('Alice' vs 'alice') cannot
    slip a self-review past the gate. Non-string operands fall back to raw equality,
    preserving prior behavior on absent/degenerate inputs."""
    if isinstance(a, str) and isinstance(b, str):
        na = unicodedata.normalize("NFKC", a.strip()).casefold()
        nb = unicodedata.normalize("NFKC", b.strip()).casefold()
        return na == nb
    return a == b

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / "data" / "policy" / "policy_data.json"
REGO_PATH = HERE / "data" / "policy" / "procheiron.rego"


def load_data(path: Path = DATA_PATH) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def decide_reference(inp: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    """Stdlib mirror of procheiron.rego. Must stay byte-equivalent in verdicts."""
    gates = data["gates"]
    gate = gates.get(inp.get("gate"))
    known_gate = gate is not None
    g = gate or {}

    allowed_levels = g.get("allowed_levels", [])
    level_ok = inp.get("level") in allowed_levels

    required_reviewers = g.get("required_reviewers", [])
    reviewers_completed = inp.get("reviewers_completed", [])
    missing_reviewers = [r for r in required_reviewers if r not in reviewers_completed]
    reviewers_ok = len(missing_reviewers) == 0

    needs_l9 = inp.get("level") == 9
    if needs_l9:
        expected_approver = g.get("l9_approver_role", g.get("approver_role"))
    else:
        expected_approver = g.get("approver_role")
    approver_required = isinstance(expected_approver, str)
    approver_ok = (not approver_required) or (inp.get("approver_role", "") == expected_approver)

    needs_ext = g.get("requires_explicit_human_external_approval", False)
    external_ok = (not needs_ext) or (inp.get("human_external_approval", False) is True)

    self_approval = _same_identity(inp.get("actor"), inp.get("approver"))
    self_review = _same_identity(inp.get("actor"), inp.get("reviewer"))

    transition = inp.get("transition", {}) or {}
    t_from = transition.get("from", "")
    t_to = transition.get("to", "")
    bad_transition = any(t[0] == t_from and t[1] == t_to for t in data["invalid_transitions"])

    deny: List[str] = []
    if not known_gate:
        deny.append("unknown gate")
    else:
        if not level_ok:
            deny.append(f"level {inp.get('level')} not allowed for gate {inp.get('gate')} (allowed: {allowed_levels})")
        if not reviewers_ok:
            deny.append(f"missing required reviewer roles: {json.dumps(sorted(missing_reviewers))}")
        if approver_required and not approver_ok:
            deny.append(f"approver role {inp.get('approver_role', '<none>')} != required {expected_approver}")
        if not external_ok:
            deny.append("external action requires explicit human external approval (§15)")
    if self_approval:
        deny.append("self-approval forbidden (§3 / §8.7)")
    if self_review:
        deny.append("self-review forbidden (§8.7 independence)")
    if bad_transition:
        deny.append(f"invalid transition {t_from} -> {t_to} (§8)")

    allow = bool(
        known_gate and level_ok and reviewers_ok and approver_ok and external_ok
        and not self_approval and not self_review and not bad_transition
    )
    return {
        "allow": allow,
        "gate": inp.get("gate"),
        "required_levels": allowed_levels,
        "required_reviewers": required_reviewers,
        "missing_reviewers": missing_reviewers,
        "expected_approver": expected_approver,
        "reasons": sorted(deny),
    }


def opa_available() -> bool:
    return shutil.which("opa") is not None


def decide_opa(inp: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate via the opa binary (production backend).

    opa 1.x returns {"result": [...]} when the queried expression is defined,
    or {} (no "result" key) when it is undefined.  The procheiron.rego decision
    rule is total (always defined once data.gates resolves), so {} should never
    appear in practice — but we handle it defensively by falling back to the
    reference backend rather than raising KeyError.
    """
    proc = subprocess.run(
        ["opa", "eval", "-d", str(DATA_PATH), "-d", str(REGO_PATH),
         "-I", "--format=json", "data.procheiron.authority.decision"],
        input=json.dumps(inp), capture_output=True, text=True, check=True,
    )
    out = json.loads(proc.stdout)
    raw = out.get("result")
    if not raw:
        # Undefined decision (should not happen with a total rule; fall back to reference).
        return decide_reference(inp, load_data())
    result = raw[0]["expressions"][0]["value"]
    # opa returns sets as lists in arbitrary order; normalize reasons for comparison.
    result["reasons"] = sorted(result.get("reasons", []))
    result["missing_reviewers"] = sorted(result.get("missing_reviewers", []))
    return result


def decide(inp: Dict[str, Any], data: Dict[str, Any] | None = None, prefer_opa: bool = True) -> Dict[str, Any]:
    if prefer_opa and opa_available():
        try:
            return decide_opa(inp)
        except Exception as exc:  # noqa: BLE001 — fall back to reference, note it
            sys.stderr.write(f"procheiron_policy: opa eval failed ({exc}); using reference backend\n")
    return decide_reference(inp, data or load_data())


def _norm(d: Dict[str, Any]) -> Dict[str, Any]:
    d = dict(d)
    d["reasons"] = sorted(d.get("reasons", []))
    d["missing_reviewers"] = sorted(d.get("missing_reviewers", []))
    return d


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Evaluate a Procheiron authority decision.")
    ap.add_argument("input", help="path to an input JSON file, or - for stdin")
    ap.add_argument("--reference-only", action="store_true", help="force the stdlib backend")
    args = ap.parse_args()
    raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text()
    inp = json.loads(raw)
    backend = "reference" if (args.reference_only or not opa_available()) else "opa"
    res = decide(inp, prefer_opa=not args.reference_only)
    print(json.dumps({"backend": backend, "decision": _norm(res)}, indent=2))
    raise SystemExit(0 if res["allow"] else 2)
