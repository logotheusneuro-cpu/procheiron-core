#!/usr/bin/env python3
"""Procheiron v0.1 scaffolder — creates a minimal, validator-passing skeleton.

Usage:
    python3 procheiron_init.py --root <dir> [--profile NAME] [--force]

IDEMPOTENT: safe to re-run. Never overwrites an existing non-empty file unless
--force is passed. Reports "already present, skipped" for each existing file.

What is created:
    .procheiron/config.yaml          — version 0.1, given profile, minimal paths
    .procheiron/profiles/<profile>/lint.json — verify_audit_chain on (tamper-evident by default)
    console/CONSOLE.md               — doctrine one-pager (all 5 validator terms)
    memory/SCHEMA.md                 — memory record schema documentation
    memory/index/memories.jsonl      — empty index (zero records is valid)
    memory/index/audit.jsonl         — empty audit log
    schemas/memory_record.schema.json — machine schema (copied from adopter)
    validate_minimal.py              — validator (copied)
    procheiron_schema.py             — validator helper (copied)

Stdlib-only. No external packages.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# File templates
# ---------------------------------------------------------------------------

CONFIG_YAML = """\
version: 0.1
profile: {profile}
root: .
paths:
  console: console
  memory: memory
"""

# The README promises tamper-evidence by default; the scaffold must deliver it.
# Chain verification is stdlib-only, so there is no dependency reason to leave
# it off. Signature flags stay opt-in (they need the [crypto] extra and keys).
LINT_JSON = """\
{
  "verify_audit_chain": true
}
"""

CONSOLE_MD = """\
# Procheiron Console

Tagline: Memory that outlives the agent.

## What Procheiron Is

Procheiron is an **agent-neutral** memory commons: a local-first, inspectable,
provenance-preserving memory substrate for any current or future agent runtime.

Its canonical surface is **human-visible** Markdown and structured JSONL —
readable in any text editor or filesystem tool. There is no hidden vector
database, no opaque runtime object.

## Core Doctrine

1. **Agent-neutral.** Procheiron makes no assumptions about which model,
   harness, or agent runtime reads it. Any capable agent may read the commons.

2. **Human-visible truth.** Every durable claim lives in Markdown or structured
   JSONL that a developer can inspect, diff, and audit without special tooling.

3. **Provenance everywhere.** Every memory record must cite at least one
   `source_path` or `source_id`. Undocumented claims are refused at write time.

4. **Propose, do not self-authorize.** Agents may propose improvements via
   `memory_propose.py`, but may not silently self-authorize canonical changes.
   Promotion from candidate to active requires an independent reviewer and an
   explicit promotion event in `audit.jsonl`.

5. **Runtime constraints remain binding.** Whatever a developer declares in
   config or policy applies at every runtime, on every agent, without exception.
   Governance does not degrade silently.

## Memory Lifecycle

```
draft → candidate → validated → active → superseded / archived / disputed
```

Active promotion requires independent review and a corroborating audit event.

## What Init Gives You

- A minimal 5-file memory commons that passes `validate_minimal.py`.
- Append helper: `memory_propose.py --root <dir> ...`
- Promotion gate: `memory_promote.py --root <dir> ...`

## What Is NOT Included Here

The advanced L0–L9 authority ladder, gate registry, decision ledger, retrieval
policy, and full governance module are optional. They are added after your
commons is running. See PORTING_GUIDE.md in the init/ directory for the
step-by-step path from this skeleton to full governance.
"""

SCHEMA_MD = """\
# Memory Schema

This schema is intentionally simple, local-first, and JSONL-friendly. It may
evolve through the Procheiron Evolution Loop, but schema changes require
validation and review.

## Memory Record Schema

Required fields for `memory/index/memories.jsonl`:

```json
{
  "id": "mem_YYYYMMDD_slug_or_uuid",
  "type": "fact|decision|preference|lesson|procedure_pointer|blocker|relation|task_state",
  "scope": "global|profile|business|project|agent|user|customer|system",
  "profile": "<deployment-profile>",
  "subject": "entity or topic",
  "statement": "declarative memory text",
  "status": "draft|candidate|validated|active|superseded|archived|disputed",
  "confidence": 0.0,
  "source_ids": [],
  "source_paths": ["relative/path/to/source"],
  "valid_from": "YYYY-MM-DD",
  "valid_until": null,
  "supersedes": [],
  "sensitivity": "public|internal|confidential|restricted|secret_ref",
  "visibility": "human_visible|restricted_summary|metadata_only",
  "created_at": "ISO-8601",
  "created_by": "agent_id",
  "reviewed_by": null,
  "reviewed_at": null,
  "write_policy": "proposal_only|approved_canonical|system_generated",
  "notes": "optional"
}
```

## Lifecycle

Raw source → draft → candidate → validated → active → superseded/archived/disputed.

Every transition is auditable. Active promotion requires authority outside the
proposing agent (independent reviewer + corroborating audit event).

## Validation Rules

1. Required fields must be present.
2. JSONL files must be valid UTF-8 with one JSON object per non-empty line.
3. Every durable memory must cite at least one source path or source ID.
4. `confidence` must be numeric between 0 and 1.
5. `status` must be in the allowed lifecycle set.
6. `sensitivity` must be one of the defined levels.
7. Supersession must be explicit and append-only.
8. Secrets must not appear in memory records.
9. Agent-generated proposals must not set themselves to `active` without
   independent review metadata and a corroborating promotion audit event.
10. Retrieval indexes are rebuildable; do not treat them as canonical truth.

## Machine Schema

The machine-readable schema is at `schemas/memory_record.schema.json`.
Validate with: `python3 validate_minimal.py --root . --json`
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_file(path: Path, content: str, force: bool) -> str:
    """Write a text file. Returns one of: 'created', 'skipped', 'overwritten'."""
    if path.exists() and path.stat().st_size > 0:
        if not force:
            return "skipped"
        path.write_text(content, encoding="utf-8")
        return "overwritten"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "created"


def _copy_file(src: Path, dst: Path, force: bool) -> str:
    """Copy a file. Returns one of: 'created', 'skipped', 'overwritten'."""
    if not src.is_file():
        return "source-missing"
    if dst.exists() and dst.stat().st_size > 0:
        if not force:
            return "skipped"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return "overwritten"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return "created"


def _ensure_empty_jsonl(path: Path, force: bool) -> str:
    """Ensure an empty JSONL file exists. Never overwrites a non-empty file
    without --force (preserves existing records)."""
    if path.exists():
        if path.stat().st_size > 0:
            if not force:
                return "skipped"
            # With --force: write empty (wipes existing records — intentional for re-init)
            path.write_text("", encoding="utf-8")
            return "overwritten"
        return "skipped"  # already empty, nothing to do
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    return "created"


def _has_unchained_audit(root: Path) -> bool:
    """True if an audit log exists with events that are NOT hash-chained (the first
    real event carries no entry_hash). Used to refuse silently enabling chain
    verification over a legacy log on a re-run of init."""
    audit = root / "memory" / "index" / "audit.jsonl"
    if not audit.is_file():
        return False
    import json as _json
    for line in audit.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            return "entry_hash" not in _json.loads(line)
        except ValueError:
            return True  # unparseable existing log — don't touch its verdict
    return False


def _status_line(action: str, rel: str) -> None:
    if action == "created":
        print(f"  CREATED  {rel}")
    elif action == "skipped":
        print(f"  SKIPPED  {rel}  (already present)")
    elif action == "overwritten":
        print(f"  OVERWROTE {rel}  (--force)")
    elif action == "source-missing":
        print(f"  WARNING  {rel}  (source file not found — skipped)", file=sys.stderr)
    else:
        print(f"  {action.upper()}  {rel}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Scaffold a minimal Procheiron-compliant memory commons.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--root", required=True,
                    help="Directory to initialise (created if absent).")
    ap.add_argument("--profile", default="default",
                    help="Profile name written into config.yaml (default: 'default').")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite existing non-empty files (use with care).")
    args = ap.parse_args(argv)

    root = Path(args.root).expanduser().resolve()
    profile = args.profile.strip() or "default"

    # Locate bundled adopter data (package-relative)
    adopter = Path(__file__).resolve().parent / "data" / "adopter"

    print(f"Procheiron v0.1 init → {root}  (profile={profile!r})")
    print()

    results: dict[str, str] = {}

    # 1. .procheiron/config.yaml
    config_content = CONFIG_YAML.format(profile=profile)
    r = _write_file(root / ".procheiron" / "config.yaml", config_content, args.force)
    results[".procheiron/config.yaml"] = r
    _status_line(r, ".procheiron/config.yaml")

    # 2. console/CONSOLE.md
    r = _write_file(root / "console" / "CONSOLE.md", CONSOLE_MD, args.force)
    results["console/CONSOLE.md"] = r
    _status_line(r, "console/CONSOLE.md")

    # 3. memory/SCHEMA.md
    r = _write_file(root / "memory" / "SCHEMA.md", SCHEMA_MD, args.force)
    results["memory/SCHEMA.md"] = r
    _status_line(r, "memory/SCHEMA.md")

    # 4. memory/index/memories.jsonl  (empty — zero records is valid)
    r = _ensure_empty_jsonl(root / "memory" / "index" / "memories.jsonl", args.force)
    results["memory/index/memories.jsonl"] = r
    _status_line(r, "memory/index/memories.jsonl")

    # 5. memory/index/audit.jsonl  (empty)
    r = _ensure_empty_jsonl(root / "memory" / "index" / "audit.jsonl", args.force)
    results["memory/index/audit.jsonl"] = r
    _status_line(r, "memory/index/audit.jsonl")

    # 6. schemas/memory_record.schema.json  (copy from adopter)
    src_schema = adopter / "schemas" / "memory_record.schema.json"
    r = _copy_file(src_schema, root / "schemas" / "memory_record.schema.json", args.force)
    results["schemas/memory_record.schema.json"] = r
    _status_line(r, "schemas/memory_record.schema.json")

    # 7. validate_minimal.py  (copy from adopter so the deployment is self-contained)
    r = _copy_file(adopter / "validate_minimal.py", root / "validate_minimal.py", args.force)
    results["validate_minimal.py"] = r
    _status_line(r, "validate_minimal.py")

    # 8. procheiron_schema.py  (required by validate_minimal.py)
    r = _copy_file(adopter / "procheiron_schema.py", root / "procheiron_schema.py", args.force)
    results["procheiron_schema.py"] = r
    _status_line(r, "procheiron_schema.py")

    # 9. memory_propose.py  (propose helper — convenience, not required by validator)
    r = _copy_file(adopter / "memory_propose.py", root / "memory_propose.py", args.force)
    results["memory_propose.py"] = r
    _status_line(r, "memory_propose.py")

    # 10. memory_promote.py  (promotion gate — convenience, not required by validator)
    r = _copy_file(adopter / "memory_promote.py", root / "memory_promote.py", args.force)
    results["memory_promote.py"] = r
    _status_line(r, "memory_promote.py")

    # 11. lint profile — audit-chain verification ON, so `procheiron validate`
    # catches a tampered audit log out of the box. But NEVER switch it on over a
    # pre-existing UNCHAINED audit log: re-running init on a legacy commons would
    # silently flip its verdict. Enabling the chain there is a migration, not a
    # scaffold step — refuse and tell the operator.
    lint_rel = f".procheiron/profiles/{profile}/lint.json"
    lint_path = root / ".procheiron" / "profiles" / profile / "lint.json"
    if not lint_path.is_file() and _has_unchained_audit(root):
        print(f"  SKIPPED  {lint_rel}")
        print(f"           existing audit log is not hash-chained — enabling "
              f"verify_audit_chain\n           now would change this deployment's verdict. "
              f"Migrate the log first,\n           then add the lint flag by hand. (See "
              f"PORTING_GUIDE.md.)")
        results[lint_rel] = "skipped"
    else:
        r = _write_file(lint_path, LINT_JSON, args.force)
        results[lint_rel] = r
        _status_line(r, lint_rel)

    print()

    # Summary
    counts = Counter(results.values())
    n_created, n_skipped = counts["created"], counts["skipped"]
    n_overwrote, n_missing_src = counts["overwritten"], counts["source-missing"]

    print(f"Done: {n_created} created, {n_skipped} skipped, {n_overwrote} overwritten", end="")
    if n_missing_src:
        print(f", {n_missing_src} source-missing (helper scripts not available)", end="")
    print(".")
    print()
    print(f"Validate with:")
    print(f"  procheiron validate {root}")
    print(f"  (or, without the CLI:  python3 {root}/validate_minimal.py --root {root} --json)")
    print()
    print(f"First record (from inside {root}):")
    print(f"  python3 memory_propose.py --created-by alice --type decision --scope project \\")
    print(f"      --subject 'retry policy' --statement 'Retries use exponential backoff.' \\")
    print(f"      --source-path docs/decisions.md --confidence 0.9")
    print(f"  python3 memory_promote.py --memory-id <id> --new-status active --reviewer bob \\")
    print(f"      --authorized-by casey --reason 'verified against the source' --allow-unverified-reviewer")
    print(f"  (promotion by the record's author is refused — review must be independent;")
    print(f"   drop --allow-unverified-reviewer once you register actors in adapters.jsonl)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
