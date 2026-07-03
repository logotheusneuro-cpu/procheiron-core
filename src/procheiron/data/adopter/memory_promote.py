#!/usr/bin/env python3
"""Procheiron memory promotion gate — the only sanctioned writer of status changes.

Roadmap item 1.2 (2026-06-11): converts SELF_ACTION_POLICY §11 ("active memory
promotion requires authority outside the proposing agent") and the
memory_promotion_gate from prose into code.

Guarantees by construction:
- refuses self-review: reviewer must differ from the record's created_by AND
  must not share a profile-declared actor group with it (same-harness
  role-relabel laundering is refused, per the A-to-Z audit finding)
- reviewer must be a known actor (profile lint known_actors ∪ adapter ids)
- only legal lifecycle transitions are accepted (draft→candidate→validated→
  active; supersession/archival/dispute paths); everything else is refused
- every status change appends a matching audit event to audit.jsonl — the
  exact event validate_procheiron2.py --records requires active/validated
  records to have
- supersession is structured: --superseded-by writes supersessions.jsonl
  lineage and updates the superseding record's supersedes[]
- atomic: rewrites memories.jsonl via tmp+rename only after the full new
  content re-parses; takes a lock under .procheiron/locks/; backs up the
  index to .procheiron/backups/memory/ first
- this tool cannot create records (memory_propose.py does that) and cannot
  edit statements — status, reviewer fields, write_policy, and supersedes[]
  only

It does NOT decide whether promotion is justified. The reviewer named on the
command line is accountable for that judgment, and the audit event records it.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _bootstrap_lib() -> Tuple[Any, Any]:
    """Locate the Procheiron shared lib (resolver + patterns) and import it.

    When an explicit root is given (--root, PROCHEIRON_ROOT, or PROCHEIRON_LIB),
    the lib is loaded ONLY from there — never from a cwd ancestor. The prior
    fall-through let a tool invoked with `--root <vault-without-lib>` import and
    execute code from whatever `.procheiron/lib` happened to sit above the cwd
    (review finding M-1, code execution from an ambient directory). Ambient
    ancestor discovery is used only when no root is specified at all.
    """
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
        lib_candidates = explicit  # explicit root pins the lib; no cwd fall-through
    else:
        here = Path.cwd().resolve()
        lib_candidates = [r / ".procheiron" / "lib" for r in [here, *here.parents]]

    for lib in lib_candidates:
        if (lib / "procheiron_resolve.py").is_file() and (lib / "procheiron_patterns.py").is_file():
            sys.path.insert(0, str(lib))
            import procheiron_resolve  # type: ignore
            import procheiron_patterns  # type: ignore
            return procheiron_resolve, procheiron_patterns
    print(
        "memory_promote: REFUSED — no complete Procheiron lib found at the specified root "
        "(need procheiron_resolve.py + procheiron_patterns.py under <root>/.procheiron/lib; "
        "pass --root, set PROCHEIRON_ROOT/PROCHEIRON_LIB, or run under an installed tree)",
        file=sys.stderr,
    )
    sys.exit(1)


_resolve_mod, _patterns_mod = _bootstrap_lib()

LIFECYCLE = {"draft", "candidate", "validated", "active", "superseded", "archived", "disputed"}
ALLOWED_TRANSITIONS = {
    ("draft", "candidate"),
    ("candidate", "validated"),
    ("candidate", "active"),
    ("validated", "active"),
    ("candidate", "superseded"),
    ("validated", "superseded"),
    ("active", "superseded"),
    ("candidate", "archived"),
    ("validated", "archived"),
    ("active", "archived"),
    ("draft", "archived"),
    ("draft", "disputed"),
    ("candidate", "disputed"),
    ("validated", "disputed"),
    ("active", "disputed"),
    ("disputed", "candidate"),
    ("disputed", "archived"),
}
PROMOTING = {"validated", "active"}
# Transitions that retire or replace shared truth require an independent
# reviewer (not the creator, not a same-group actor). Promoting (validated/
# active) and superseded already did; archiving a live record and un-disputing
# (disputed→candidate) are equally consequential and were ungated before
# (review finding H-4). Self-dispute stays allowed — flagging your own doubt is
# the safe direction and must not be high-friction.
INDEPENDENCE_REQUIRED = {
    ("candidate", "validated"), ("candidate", "active"), ("validated", "active"),
    ("candidate", "superseded"), ("validated", "superseded"), ("active", "superseded"),
    ("validated", "archived"), ("active", "archived"),
    ("disputed", "candidate"),
}
LIVE_STATES = {"candidate", "validated", "active"}
EVENT_ACTION = {
    "validated": "memory_validated",
    "active": "memory_promoted",
    "superseded": "memory_superseded",
    "archived": "memory_archived",
    "disputed": "memory_disputed",
    "candidate": "memory_status_changed",
}


def fail(msg: str) -> None:
    print(f"memory_promote: REFUSED — {msg}", file=sys.stderr)
    sys.exit(1)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        fail(f"index file missing: {path}")
    records: List[Dict[str, Any]] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"{path.name} line {n} is not valid JSON ({exc}); refusing to operate on a corrupt index")
        records.append(obj)
    return records


def assert_unique_ids(records: List[Dict[str, Any]], label: str) -> None:
    """A duplicate id makes by_id collapse to the last copy, so a promotion
    silently desyncs the duplicates (review finding M-3). Refuse up front."""
    seen: Dict[str, int] = {}
    for i, r in enumerate(records, 1):
        rid = str(r.get("id") or "")
        if rid and rid in seen:
            fail(f"corrupt {label}: id {rid} appears at records {seen[rid]} and {i}; "
                 "refusing to operate on a duplicated index")
        seen[rid] = i


def audit_id(action: str, memory_id: str) -> str:
    """Collision-resistant audit id: timestamp + a hash of the FULL memory id
    (truncating to a 20-char tail collided on this project's long ids — M-4)."""
    h = hashlib.sha256(memory_id.encode()).hexdigest()[:10]
    return f"audit_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{action}_{h}"


def dump_jsonl_atomic(path: Path, records: List[Dict[str, Any]]) -> None:
    text = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in records)
    for n, line in enumerate(text.splitlines(), 1):
        json.loads(line)  # re-parse everything before touching disk
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    line = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"
    payload = line.encode("utf-8")
    if path.exists() and path.stat().st_size > 0:
        with path.open("rb") as handle:
            handle.seek(-1, os.SEEK_END)
            if handle.read(1) != b"\n":
                payload = b"\n" + payload
    fd = os.open(str(path), os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o644)
    try:
        written = 0
        while written < len(payload):
            written += os.write(fd, payload[written:])
    finally:
        os.close(fd)


def _append_audit_event(path: Path, event: Dict[str, Any]) -> None:
    """Append an audit event, hash-chaining it (and ed25519-signing it when
    PROCHEIRON_SIGNING_KEY is set) via the installed procheiron package. Falls back
    to a plain append when the package/chain helper is unavailable — the event is
    then unchained, and a deployment running lint `verify_audit_chain` will flag it.
    Preserves the writers' audit-line-first, atomic O_NOFOLLOW append discipline."""
    try:
        from procheiron import chain as _chain  # type: ignore
    except Exception:
        _chain = None
    if _chain is not None:
        _chain.append_event(path, event, key_hex=os.environ.get("PROCHEIRON_SIGNING_KEY") or None)
    else:
        append_jsonl(path, event)


class Lock:
    def __init__(self, root: Path) -> None:
        lock_dir = root / ".procheiron" / "locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        self.path = lock_dir / "memory_index.lock"

    def __enter__(self) -> "Lock":
        try:
            fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            age = dt.datetime.now().timestamp() - self.path.stat().st_mtime
            fail(f"memory index lock held ({self.path}, {int(age)}s old); retry or remove a stale lock manually")
        os.write(fd, f"{os.getpid()} {utc_now()}\n".encode())
        os.close(fd)
        return self

    def __exit__(self, *_exc: Any) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def load_known_actors(cfg: Any) -> Tuple[set, List[set]]:
    actors: set = set()
    groups: List[set] = []
    lint_path = cfg.root / ".procheiron" / "profiles" / cfg.profile / "lint.json"
    if lint_path.is_file():
        try:
            lint = json.loads(lint_path.read_text(encoding="utf-8"))
            actors.update(lint.get("known_actors", []))
            groups = [set(g) for g in lint.get("known_actor_groups", []) if isinstance(g, list)]
        except json.JSONDecodeError:
            pass
    adapters_path = cfg.path("memory") / "index" / "adapters.jsonl"
    if adapters_path.is_file():
        for line in adapters_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                adapter_id = str(json.loads(line).get("adapter_id", "")).strip()
                if adapter_id:
                    actors.add(adapter_id)
            except json.JSONDecodeError:
                continue
    return actors, groups


def main() -> None:
    p = argparse.ArgumentParser(
        description="Change the lifecycle status of ONE Procheiron memory record, with refusal "
        "rules, lineage, and a mandatory audit event. The only sanctioned status writer.",
        allow_abbrev=False,
    )
    p.add_argument("--memory-id", required=True)
    p.add_argument("--new-status", required=True, choices=sorted(LIFECYCLE - {"draft"}))
    p.add_argument("--reviewer", required=True, help="acting reviewer/curator agent id (accountable actor)")
    p.add_argument("--reviewer-role", default="memory_reviewer_curator",
                   help="exact reviewer role per SELF_ACTION_POLICY §5 (default memory_reviewer_curator)")
    p.add_argument("--reason", required=True, help="why this transition is justified (goes in the audit event)")
    p.add_argument("--authorized-by", default=None,
                   help="approving authority for active promotions (human or task authorization reference)")
    p.add_argument("--superseded-by", default=None,
                   help="when --new-status superseded: the id of the record that replaces this one")
    p.add_argument("--allow-unverified-reviewer", action="store_true",
                   help="permit a reviewer not in any actor registry (fail-open override; logged)")
    p.add_argument("--root", default=None, help="explicit Procheiron root")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    reviewer = args.reviewer.strip()
    memory_id = args.memory_id.strip()

    def norm(value: Any) -> str:
        if not isinstance(value, str):
            return f"__nonstring__{type(value).__name__}"
        return unicodedata.normalize("NFKC", value.strip()).casefold()

    for label, text in (("reviewer", reviewer), ("reason", args.reason),
                        ("authorized-by", args.authorized_by or "")):
        hit = _patterns_mod.first_match_label(text)
        if hit:
            fail(f"{label} matches secret-like pattern {hit}; secrets do not belong in memory")

    cfg = _resolve_mod.load_config(explicit_root=args.root)
    index_dir = cfg.path("memory") / "index"
    memories_path = index_dir / "memories.jsonl"
    audit_path = index_dir / "audit.jsonl"
    supersessions_path = index_dir / "supersessions.jsonl"

    # Acquire the lock BEFORE reading: the read-modify-write cycle must be inside
    # the lock or a concurrent committed change is silently reverted by a stale
    # snapshot (review finding H-3, lost update). fail()/SystemExit still releases
    # the lock via the context manager's __exit__.
    with Lock(cfg.root):
        records = load_jsonl(memories_path)
        load_jsonl(audit_path)  # parse-check; corrupt audit aborts before any write
        assert_unique_ids(records, "memories.jsonl")
        by_id = {str(r.get("id")): r for r in records}
        target = by_id.get(memory_id)
        if target is None:
            fail(f"memory id not found: {memory_id}")

        old_status = str(target.get("status") or "")
        new_status = args.new_status
        if old_status == new_status:
            fail(f"record is already {new_status}")
        if (old_status, new_status) not in ALLOWED_TRANSITIONS:
            fail(f"invalid lifecycle transition {old_status} -> {new_status} (SELF_ACTION_POLICY §8/§11)")

        created_by = str(target.get("created_by") or "")
        actors, groups = load_known_actors(cfg)
        if reviewer not in actors:
            if actors:
                fail(f"reviewer {reviewer!r} is not a known actor (profile lint known_actors / adapters.jsonl); "
                     "register the actor before granting review authority")
            elif not args.allow_unverified_reviewer:
                # Empty registry must fail closed, not accept any string (M-2).
                fail("no actor registry available (empty known_actors and no adapters.jsonl); "
                     "cannot verify reviewer. Populate the registry or pass --allow-unverified-reviewer.")
            else:
                print(f"memory_promote: WARNING — reviewer {reviewer!r} unverified (empty registry, "
                      "override in effect)", file=sys.stderr)

        def refuse(reason: str) -> None:
            """Log a schema-valid `promotion_refused` audit event, then fail. Durable
            proof the gate blocked an unauthorized promotion (was stderr-only before).
            A logging failure warns but never swallows the refusal (reliability)."""
            if not args.dry_run:
                _now = utc_now()
                _ev = {"id": audit_id("promotion_refused", memory_id), "event_type": "promotion_refused",
                       "action": "promotion_refused", "profile": cfg.profile, "actor": reviewer,
                       "reviewer_role": args.reviewer_role, "memory_id": memory_id,
                       "status_before": old_status, "status_after": old_status,
                       "attempted_status": new_status, "created_by": created_by, "refused": True,
                       "timestamp": _now, "created_at": _now, "reason": reason, "tool": "memory_promote.py"}
                try:
                    _append_audit_event(audit_path, _ev)
                except Exception as _exc:  # logging must never swallow the refusal
                    print(f"memory_promote: WARNING — could not log refusal ({_exc})", file=sys.stderr)
            fail(reason)

        if (old_status, new_status) in INDEPENDENCE_REQUIRED:
            if norm(reviewer) == norm(created_by):
                refuse(f"self-review: {reviewer!r} created this record (invalid transition §8.7)")
            if any(reviewer in g and created_by in g for g in groups):
                refuse(f"same-harness review: {reviewer!r} and creator {created_by!r} share a declared "
                       "actor group — independent review required (authority-laundering guard)")
        if new_status == "active" and not (args.authorized_by or "").strip():
            refuse("active promotion requires --authorized-by (memory_promotion_gate: curator/authorized human)")

        # B2 (Phase-3 adoption, 2026-06-12): consult the live authority policy
        # (.procheiron/policy, stdlib reference backend — opa-binary adoption is a
        # follow-up: opa 1.17 result-format incompat) and RECORD its verdict on the
        # audit event. Hard-block ONLY on independence/transition denials promote
        # already enforces, so this never introduces a new false refusal. The gate's
        # full multi-reviewer requirement is surfaced as advisory until the CLI
        # models a reviewer set + approver (tracked follow-up).
        policy_decision: Optional[Dict[str, Any]] = None
        try:
            policy_dir = cfg.root / ".procheiron" / "policy"
            if (policy_dir / "procheiron_policy.py").is_file():
                if str(policy_dir) not in sys.path:
                    sys.path.insert(0, str(policy_dir))
                import procheiron_policy as _pp  # type: ignore
                _transition = ({"from": "memory_candidate", "to": "active_memory"}
                               if (old_status, new_status) == ("candidate", "active") else {})
                _reviewers = [args.reviewer_role] + (["authority_reviewer"]
                             if (args.authorized_by or "").strip() else [])
                policy_decision = _pp.decide({
                    "gate": "memory_promotion_gate",
                    "level": 4,
                    "actor": created_by,
                    "reviewer": reviewer,
                    "approver": reviewer,
                    "approver_role": args.reviewer_role,
                    "reviewers_completed": _reviewers,
                    "transition": _transition,
                }, prefer_opa=False)
                _hard = [r for r in policy_decision.get("reasons", [])
                         if "self-review" in r or "self-approval" in r or "invalid transition" in r]
                if _hard:
                    refuse("authority policy denied this transition: " + "; ".join(_hard))
        except SystemExit:
            raise
        except Exception as _exc:  # policy is advisory infra; never break the writer on it
            print(f"memory_promote: policy consult skipped ({type(_exc).__name__}: {_exc})",
                  file=sys.stderr)
            policy_decision = {"consulted": False, "error": str(_exc)}

        superseding_record: Optional[Dict[str, Any]] = None
        if new_status == "superseded":
            if not args.superseded_by:
                fail("--superseded-by is required when marking a record superseded (explicit lineage, SCHEMA rule 7)")
            superseded_by = args.superseded_by.strip()
            superseding_record = by_id.get(superseded_by)
            if superseding_record is None:
                fail(f"superseding record not found: {superseded_by}")
            if superseded_by == memory_id:
                fail("a record cannot supersede itself")
            sstatus = str(superseding_record.get("status") or "")
            if sstatus not in LIVE_STATES:
                fail(f"superseding record {superseded_by} is {sstatus!r}, not a live state "
                     f"({sorted(LIVE_STATES)}); a dead record cannot be the replacement (M-5)")
            # Cycle guard: refuse if the superseder already (transitively) points back.
            seen, frontier = set(), [superseded_by]
            while frontier:
                cur = frontier.pop()
                if cur == memory_id:
                    fail(f"supersession cycle: {superseded_by} already supersedes {memory_id} (M-5)")
                if cur in seen:
                    break
                seen.add(cur)
                rec = by_id.get(cur)
                if rec:
                    frontier.extend(str(x) for x in (rec.get("supersedes") or []))
        else:
            superseded_by = None

        now = utc_now()
        target["status"] = new_status
        if new_status in PROMOTING:
            target["reviewed_by"] = reviewer
            target["reviewed_at"] = now
            if new_status == "active":
                target["write_policy"] = "approved_canonical"
        if superseding_record is not None:
            supersedes = superseding_record.get("supersedes") or []
            if memory_id not in supersedes:
                supersedes.append(memory_id)
            superseding_record["supersedes"] = supersedes

        event: Dict[str, Any] = {
            "id": audit_id(EVENT_ACTION[new_status], memory_id),
            "event_type": EVENT_ACTION[new_status],
            "action": EVENT_ACTION[new_status],
            "profile": cfg.profile,
            "actor": reviewer,
            "reviewer_role": args.reviewer_role,
            "memory_id": memory_id,
            "status_before": old_status,
            "status_after": new_status,
            "timestamp": now,
            "created_at": now,
            "reason": args.reason,
            "tool": "memory_promote.py",
            "authorized_by": args.authorized_by,
            "superseded_by": superseded_by,
            "policy_decision": policy_decision,
        }
        supersession_entry: Optional[Dict[str, Any]] = None
        if superseding_record is not None:
            supersession_entry = {
                "id": f"sup_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{hashlib.sha256(memory_id.encode()).hexdigest()[:10]}",
                "old_id": memory_id,
                "new_id": superseded_by,
                "at": now,
                "actor": reviewer,
                "reason": args.reason,
            }

        if args.dry_run:
            print(json.dumps({"would_update": target, "would_append_audit": event,
                              "would_append_supersession": supersession_entry}, indent=2, ensure_ascii=False))
            print("memory_promote: DRY RUN — nothing written")
            return

        try:
            backup_dir = cfg.root / ".procheiron" / "backups" / "memory"
            backup_dir.mkdir(parents=True, exist_ok=True)
            stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            shutil.copy2(memories_path, backup_dir / f"memories.jsonl.bak-{stamp}")
            # Write order matters for crash safety (review finding H-2): append the
            # audit (and supersession) lines FIRST, rename memories LAST. If the
            # final rename fails, we have a dangling audit event describing a change
            # that didn't land — tolerated (validator checks active⇒event, not the
            # reverse) — rather than a status change with NO audit event, which is
            # exactly the forge-indistinguishable state the gate exists to prevent.
            _append_audit_event(audit_path, event)
            if supersession_entry is not None:
                append_jsonl(supersessions_path, supersession_entry)
            dump_jsonl_atomic(memories_path, records)
        except OSError as exc:
            fail(f"write failed ({exc}); index left unchanged or with a dangling audit event only — "
                 "re-run after fixing the filesystem condition")

    print(f"memory_promote: {args.memory_id} {old_status} -> {new_status} "
          f"(reviewer={args.reviewer}, audit={event['id']})")


if __name__ == "__main__":
    main()
