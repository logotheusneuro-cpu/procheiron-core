#!/usr/bin/env python3
"""Validating candidate-memory append helper for the Procheiron memory commons.

PROPOSAL-ONLY BY CONSTRUCTION:
- status is forced to "candidate"; write_policy is forced to "proposal_only"
- append-only: never edits or deletes existing records, never touches
  active/validated records, never performs promotion
- writes exactly two lines per invocation: one record to memories.jsonl,
  one audit event to audit.jsonl
- refuses records without provenance (at least one --source-path)
- secret-pattern guard on free-text fields (shared registry:
  .procheiron/lib/procheiron_patterns.py)
- refuses to append if the existing index fails to parse (no corruption pile-on)

Promotion (candidate -> active) remains gated: scripts/memory_promote.py is
the only sanctioned status writer. This script cannot perform it.

v2 (2026-06-11, roadmap 1.2): the hardcoded vault root is gone. The index
location resolves most-explicit-wins: --index-dir, --root, PROCHEIRON_ROOT,
nearest ancestor with .procheiron/config.yaml. Machine-absolute --source-path
values under known deployment roots are normalized to portable form
(root-relative or {paths.<key>}/...) at write time, so new records are
self-describing from birth.

Proposed 2026-06-09 by the operational agent (cowork) under owner authorization;
v2 staged under the v1.0 roadmap Batch-2 decision.
Schema reference: {paths.memory}/SCHEMA.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, List, Tuple


def _bootstrap_lib() -> Tuple[Any, Any, Any]:
    """Locate the shared lib. An explicit root (--root/PROCHEIRON_ROOT/
    PROCHEIRON_LIB) pins the lib location; only with no root given do we fall
    back to cwd-ancestor discovery (review finding M-1)."""
    explicit: List[Path] = []
    env_lib = os.environ.get("PROCHEIRON_LIB")
    if env_lib:
        explicit.append(Path(env_lib).expanduser().resolve())
    probe_root = os.environ.get("PROCHEIRON_ROOT")
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--root" and i + 1 < len(args):
            probe_root = args[i + 1]
        elif a.startswith("--root="):
            probe_root = a.split("=", 1)[1]
    if probe_root:
        explicit.append(Path(probe_root).expanduser().resolve() / ".procheiron" / "lib")
    if explicit:
        lib_candidates = explicit
    else:
        here = Path.cwd().resolve()
        lib_candidates = [r / ".procheiron" / "lib" for r in [here, *here.parents]]
    for lib in lib_candidates:
        if all((lib / name).is_file() for name in
               ("procheiron_resolve.py", "procheiron_patterns.py", "procheiron_paths.py", "procheiron_lock.py")):
            sys.path.insert(0, str(lib))
            import procheiron_resolve  # type: ignore
            import procheiron_patterns  # type: ignore
            import procheiron_paths  # type: ignore
            import procheiron_lock  # type: ignore
            return procheiron_resolve, procheiron_patterns, procheiron_paths
    print(
        "memory_propose: REFUSED — no complete Procheiron lib found at the specified root "
        "(pass --root, set PROCHEIRON_ROOT/PROCHEIRON_LIB, or run under an installed tree)",
        file=sys.stderr,
    )
    sys.exit(1)


_resolve_mod, _patterns_mod, _paths_mod = _bootstrap_lib()
from procheiron_lock import Lock  # shared single-writer lock (roadmap 3.6 / B5); same lockfile as memory_promote

ALLOWED_TYPES = {
    "fact", "decision", "preference", "lesson",
    "procedure_pointer", "blocker", "relation", "task_state",
}
ALLOWED_SCOPES = {
    "global", "profile", "business", "project", "agent", "user", "customer", "system",
}
ALLOWED_SENSITIVITY = {"public", "internal", "confidential", "restricted", "secret_ref"}
ALLOWED_VISIBILITY = {"human_visible", "restricted_summary", "metadata_only"}

STATEMENT_MAX = 1200


def fail(msg: str) -> None:
    print(f"memory_propose: REFUSED — {msg}", file=sys.stderr)
    sys.exit(1)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def secret_guard(label: str, text: str) -> None:
    hit = _patterns_mod.first_match_label(text or "")
    if hit:
        fail(f"{label} matches secret-like pattern {hit}; secrets do not belong in memory (SCHEMA.md)")


def validate_existing_jsonl(path: Path) -> None:
    if not path.exists():
        fail(f"index file missing: {path} (refusing to create index files; commons must already exist)")
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"existing {path.name} line {n} is not valid JSON ({exc}); refusing to append to a corrupt index")


def append_line(path: Path, obj: dict) -> None:
    line = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"
    payload = line.encode("utf-8")
    # If the existing file lacks a terminal newline, appending would merge onto
    # (and corrupt) the last record — violating append-only. Prepend a separator.
    if path.stat().st_size > 0:
        with path.open("rb") as handle:
            handle.seek(-1, os.SEEK_END)
            if handle.read(1) != b"\n":
                payload = b"\n" + payload
    fd = os.open(str(path), os.O_WRONLY | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0))
    try:
        written = 0
        while written < len(payload):
            written += os.write(fd, payload[written:])
    finally:
        os.close(fd)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Append one CANDIDATE memory record (proposal-only) to the Procheiron memory commons.",
        allow_abbrev=False,
    )
    p.add_argument("--type", required=True, choices=sorted(ALLOWED_TYPES))
    p.add_argument("--scope", required=True, choices=sorted(ALLOWED_SCOPES))
    p.add_argument("--profile", default=None, help="defaults to the active config profile")
    p.add_argument("--subject", required=True)
    p.add_argument("--statement", required=True)
    p.add_argument("--source-path", action="append", default=[], help="provenance path; repeatable; at least one required")
    p.add_argument("--source-id", action="append", default=[])
    p.add_argument("--confidence", type=float, required=True)
    p.add_argument("--created-by", required=True, help="agent id, e.g. the proposing harness/agent identity")
    p.add_argument("--sensitivity", default="internal", choices=sorted(ALLOWED_SENSITIVITY))
    p.add_argument("--visibility", default="human_visible", choices=sorted(ALLOWED_VISIBILITY))
    p.add_argument("--valid-from", default=dt.date.today().isoformat())
    p.add_argument("--notes", default="")
    p.add_argument("--root", default=None, help="explicit Procheiron root (wins over env and ancestor discovery)")
    p.add_argument("--index-dir", default=None, help="override for sandbox/self-test (wins over --root)")
    p.add_argument("--allow-external-index", action="store_true",
                   help="permit --index-dir outside the resolved root (deliberate sandbox writes)")
    p.add_argument("--dry-run", action="store_true", help="validate and print the record without writing")
    args = p.parse_args()

    cfg = _resolve_mod.load_config(explicit_root=args.root)
    memory_index = (cfg.path("memory") / "index").resolve()
    if args.index_dir:
        index_dir = Path(args.index_dir).resolve()
        # Containment: a candidate must land in THIS commons, not any directory
        # that happens to hold memories.jsonl (review finding M-6). The override
        # stays available for sandboxes/tests via --allow-external-index.
        if index_dir != memory_index and not args.allow_external_index:
            within = index_dir == cfg.root.resolve() or cfg.root.resolve() in index_dir.parents
            if not within:
                fail(f"--index-dir {index_dir} is outside the resolved root {cfg.root}; "
                     "pass --allow-external-index for a deliberate sandbox write")
    else:
        index_dir = cfg.path("memory") / "index"
    profile = args.profile or cfg.profile

    if not args.source_path:
        fail("at least one --source-path is required (durable claims must cite provenance — AGENT_BOOT.md §4)")
    if not (0.0 <= args.confidence <= 1.0):
        fail("confidence must be between 0 and 1")
    if not args.statement.strip():
        fail("statement must be non-empty")
    if len(args.statement) > STATEMENT_MAX:
        fail(f"statement exceeds {STATEMENT_MAX} chars; link a source document instead")
    if len(args.statement.encode("utf-8")) > STATEMENT_MAX * 2:
        fail(f"statement exceeds {STATEMENT_MAX * 2} bytes (multibyte); link a source document instead")

    normalized_paths: List[str] = []
    for raw in args.source_path:
        normalized, _changed = _paths_mod.normalize_source_path(cfg, raw)
        normalized_paths.append(normalized)

    guarded = [
        ("statement", args.statement), ("subject", args.subject), ("notes", args.notes),
        ("created-by", args.created_by), ("profile", profile), ("valid-from", args.valid_from),
    ]
    guarded += [("source-path", sp) for sp in normalized_paths]
    guarded += [("source-id", si) for si in args.source_id]
    for label, text in guarded:
        secret_guard(label, text)

    memories = index_dir / "memories.jsonl"
    audit = index_dir / "audit.jsonl"

    now = utc_now()
    slug = re.sub(r"[^a-z0-9]+", "_", args.subject.lower()).strip("_")[:40] or "record"
    digest = hashlib.sha256(f"{now}{args.statement}".encode()).hexdigest()[:10]
    mem_id = f"mem_{dt.date.today().strftime('%Y%m%d')}_{slug}_{digest}"

    record = {
        "id": mem_id,
        "type": args.type,
        "scope": args.scope,
        "profile": profile,
        "subject": args.subject,
        "statement": args.statement,
        "status": "candidate",            # forced — this tool cannot set any other status
        "confidence": args.confidence,
        "source_ids": args.source_id,
        "source_paths": normalized_paths,
        "valid_from": args.valid_from,
        "valid_until": None,
        "supersedes": [],
        "sensitivity": args.sensitivity,
        "visibility": args.visibility,
        "created_at": now,
        "created_by": args.created_by,
        "reviewed_by": None,
        "reviewed_at": None,
        "write_policy": "proposal_only",  # forced
        "notes": args.notes or "Proposed via memory_propose.py; promotion requires memory_promote.py with an independent reviewer.",
    }
    audit_event = {
        "at": now,
        "actor": args.created_by,
        "action": "memory_candidate_proposed",
        "memory_id": mem_id,
        "tool": "scripts/memory_propose.py",
        "write_policy": "proposal_only",
        "index_dir": _paths_mod.normalize_source_path(cfg, str(index_dir))[0],
    }

    if args.dry_run:
        validate_existing_jsonl(memories)
        validate_existing_jsonl(audit)
        print(json.dumps(record, ensure_ascii=False, indent=2))
        print("memory_propose: DRY RUN — nothing written")
        return

    # B5 (roadmap 3.6): parse-check + both appends run inside the single-writer
    # lock so a concurrent memory_promote rewrite cannot drop this candidate
    # (lost update) and two writers cannot interleave (torn record). Same lockfile
    # as memory_promote's Lock (.procheiron/locks/memory_index.lock).
    with Lock(cfg.root):
        validate_existing_jsonl(memories)
        validate_existing_jsonl(audit)
        append_line(memories, record)
        append_line(audit, audit_event)
    print(f"memory_propose: appended candidate {mem_id} to {memories}")


if __name__ == "__main__":
    main()
