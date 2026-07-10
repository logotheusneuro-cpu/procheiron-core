#!/usr/bin/env python3
"""Procheiron v0.1 MINIMAL validator — the 5-file adopter's enforcement.

A documented SUBSET of the full validator. It enforces the memory-commons core:
  - config resolves (root + console + memory)
  - CONSOLE.md carries the five agent-neutral doctrine terms
  - SCHEMA.md + schemas/memory_record.schema.json are present and load
  - every memory record is schema-valid and carries provenance
  - active / validated records are reviewed by a DIFFERENT actor than their
    creator AND have a corroborating promotion/validation audit event
  - no secret patterns, no machine-absolute paths in records

The advanced governance MODULE (L0–L9 authority ladder, gate registry, decision
ledger, retrieval policy) is OPTIONAL and intentionally NOT required here — a
stranger adopts with five files; governance is added later. Stdlib-only.

Usage: python3 validate_minimal.py --root <vault> [--json]
Exit 0 iff conformant.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import procheiron_schema as pschema  # noqa: E402  (shipped beside the validator)


def _norm_actor(value: Any) -> str:
    """Normalized identity for comparison: strip + NFKC + casefold — same rule as the
    full validator's norm_actor, so 'BOB' cannot pass independent review against 'bob'."""
    if not isinstance(value, str):
        return ""
    return unicodedata.normalize("NFKC", value.strip()).casefold()

DOCTRINE = {
    "agent_neutral": ["agent-neutral"],
    "human_visible": ["human-visible"],
    "provenance": ["provenance"],
    "propose_not_promote": ["propose", "self-authorize", "promotion"],
    "runtime_constraints_binding": ["runtime", "developer", "remain binding"],
}
SECRET = [
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b"), re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}\b"), re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
ABS = re.compile(r"(?:^|[\s\"'(=:])(/[A-Za-z0-9._-]+){2,}/?")
LIVE = {"active", "validated"}


def read_config(root: Path) -> Dict[str, str]:
    """Minimal YAML reader for the flat config (stdlib only): root + paths.*"""
    cfg = (root / ".procheiron" / "config.yaml").read_text(encoding="utf-8")
    paths: Dict[str, str] = {}
    in_paths = False
    for line in cfg.splitlines():
        if re.match(r"^paths:\s*$", line):
            in_paths = True
            continue
        if in_paths:
            m = re.match(r"^\s+([a-z_]+):\s*(\S+)", line)
            if m:
                paths[m.group(1)] = m.group(2).strip()
            elif line and not line[0].isspace():
                in_paths = False
    return paths


def main() -> int:
    ap = argparse.ArgumentParser(description="Procheiron v0.1 minimal validator.")
    ap.add_argument("--root", required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).expanduser().resolve()
    errors: List[str] = []
    warnings: List[str] = []

    if not (root / ".procheiron" / "config.yaml").is_file():
        print(json.dumps({"status": "FAIL", "errors": ["missing .procheiron/config.yaml"]}))
        return 1
    paths = read_config(root)
    console = root / paths.get("console", "console")
    memory = root / paths.get("memory", "memory")

    # CONSOLE.md + doctrine
    console_md = console / "CONSOLE.md"
    if not console_md.is_file():
        errors.append("missing console/CONSOLE.md")
    else:
        text = console_md.read_text(encoding="utf-8").lower()
        for label, terms in DOCTRINE.items():
            if not all(t.lower() in text for t in terms):
                errors.append(f"CONSOLE.md missing doctrine: {label}")

    # SCHEMA.md + the machine schema
    if not (memory / "SCHEMA.md").is_file():
        errors.append("missing memory/SCHEMA.md")
    schema_path = root / "schemas" / "memory_record.schema.json"
    schema = None
    if not schema_path.is_file():
        errors.append("missing schemas/memory_record.schema.json")
    else:
        schema = pschema.load_schema(schema_path)

    # Records: schema-valid + provenance + independent review + corroborating audit
    mem_path = memory / "index" / "memories.jsonl"
    audit_path = memory / "index" / "audit.jsonl"
    records: List[Dict[str, Any]] = []
    if mem_path.is_file():
        for n, line in enumerate(mem_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                errors.append(f"memories.jsonl:{n}: invalid JSON ({exc})")
    audit = []
    if audit_path.is_file():
        for line in audit_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    audit.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    promo_actor = {(e.get("memory_id"), str(e.get("action", ""))): e.get("actor")
                   for e in audit}

    for r in records:
        rid = r.get("id", "<none>")
        if schema is not None:
            for f in pschema.validate(schema, r):
                errors.append(f"{rid}: {f['instance_path']} {f['message']}")
        if not r.get("source_paths") and not r.get("source_ids"):
            errors.append(f"{rid}: no provenance (source_paths/source_ids)")
        for sp in r.get("source_paths") or []:
            if ABS.match(str(sp)):
                errors.append(f"{rid}: machine-absolute source_path {sp!r}")
        status = str(r.get("status") or "")
        if status in LIVE:
            creator = _norm_actor(r.get("created_by"))
            reviewer = _norm_actor(r.get("reviewed_by"))
            if not reviewer:
                errors.append(f"{rid}: {status} record has no reviewed_by")
            elif reviewer == creator:
                errors.append(f"{rid}: {status} record self-reviewed by its creator")
            action = "memory_promoted" if status == "active" else "memory_validated"
            promoter = promo_actor.get((rid, action))
            if promoter is None:
                errors.append(f"{rid}: {status} record has no corroborating {action} audit event")
            else:
                # The promotion event's actor must BE the independent reviewer, not the
                # creator — otherwise a record can claim reviewed_by:bob while alice
                # actually promoted it (full validator checks this; minimal must too).
                np = _norm_actor(promoter)
                if np == creator:
                    errors.append(f"{rid}: {status} record promoted by its own creator "
                                  f"({promoter!r}) — not independent review")
                elif reviewer and np != reviewer:
                    errors.append(f"{rid}: {status} record's {action} actor ({promoter!r}) "
                                  f"does not match reviewed_by ({r.get('reviewed_by')!r})")

    # secret + console scan
    for base in (console, memory):
        if base.is_dir():
            for p in base.rglob("*"):
                if p.is_file() and p.stat().st_size <= 500_000 and p.suffix in (".md", ".jsonl", ".json", ".txt"):
                    body = p.read_text(encoding="utf-8", errors="ignore")
                    for pat in SECRET:
                        if pat.search(body):
                            errors.append(f"secret-pattern finding: {p.name}")
                            break

    status = "FAIL" if errors else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    result = {"status": status, "root": str(root), "records": len(records),
              "errors": errors, "warnings": warnings}
    print(json.dumps(result, indent=2) if args.json
          else f"minimal validator: {status} ({len(records)} records, {len(errors)} errors)")
    if not args.json:
        for e in errors:
            print(f"  FAIL {e}")
    return 0 if status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
