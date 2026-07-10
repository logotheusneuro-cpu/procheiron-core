"""Trust derived from the audit log, not from a record's mutable `status` field.

A record's `status` is just a string in a text file — a forger can flip a candidate
to `active` in place. What can't be silently flipped is the append-only audit log's
LATEST transition for that record. So the trust decision is: does the record's claimed
active/validated status match the last lifecycle transition actually recorded for it,
made by an actor independent of the creator and matching `reviewed_by`?

Shared by the full validator and the MCP read path so both derive trust the same way.

RESIDUAL (honest): without signatures, an insider with write access can APPEND a
valid-looking promotion event. The hash chain catches edits/reorders/deletes of past
events, not a fresh forged append. Closing that needs `procheiron[crypto]` signing +
`known_actor_keys` with the keys out of the writer's reach. See CLAIMS.md.
"""
from __future__ import annotations

import unicodedata
from typing import Any, Dict, List, Optional, Tuple

# An audit action -> the lifecycle status it moves a record INTO.
ACTION_STATUS = {
    "memory_candidate_proposed": "candidate",
    "memory_validated": "validated",
    "memory_promoted": "active",
    "memory_superseded": "superseded",
    "memory_archived": "archived",
    "memory_disputed": "disputed",
}
TRUSTED_STATUSES = ("active", "validated")


def norm_actor(value: Any) -> str:
    """strip + NFKC + casefold — so 'BOB' cannot pass review against 'bob'."""
    if not isinstance(value, str):
        return ""
    return unicodedata.normalize("NFKC", value.strip()).casefold()


def latest_transitions(audit: List[Dict[str, Any]]) -> Dict[str, Tuple[str, Any]]:
    """memory_id -> (status_after_latest_transition, actor_of_that_transition), in
    append (file) order — the LAST matching event wins, so a stale earlier promotion
    can't vouch for a record that was later archived/superseded."""
    out: Dict[str, Tuple[str, Any]] = {}
    for e in audit:
        mid = e.get("memory_id")
        act = str(e.get("action") or e.get("event_type") or "")
        if mid and act in ACTION_STATUS:
            out[mid] = (ACTION_STATUS[act], e.get("actor"))
    return out


def trust_error(record: Dict[str, Any], last: Optional[Tuple[str, Any]]) -> Optional[str]:
    """None if the record's active/validated status is backed by the audit log's latest
    transition (independent actor, matching reviewed_by). Otherwise a reason string.
    Non-LIVE statuses (candidate/superseded/…) always return None — they make no trust
    claim. `last` is latest_transitions().get(record_id)."""
    status = str(record.get("status") or "")
    if status not in TRUSTED_STATUSES:
        return None
    creator = norm_actor(record.get("created_by"))
    reviewer = norm_actor(record.get("reviewed_by"))
    if not reviewer:
        return "no reviewed_by"
    if reviewer == creator:
        return "self-reviewed by its creator"
    if last is None:
        return f"status {status!r} but no lifecycle transition is recorded in the audit log"
    lt_status, lt_actor = last
    if lt_status != status:
        return (f"status {status!r} does not match the latest audit transition "
                f"({lt_status!r}) — forged or stale status")
    np = norm_actor(lt_actor)
    if np == creator:
        return f"promoted by its own creator ({lt_actor!r}) — not independent review"
    if np != reviewer:
        return (f"promotion actor ({lt_actor!r}) does not match reviewed_by "
                f"({record.get('reviewed_by')!r})")
    return None


def demo() -> None:
    """Self-check: a stale promotion must not vouch for a re-activated record."""
    audit = [
        {"memory_id": "m", "action": "memory_candidate_proposed", "actor": "alice"},
        {"memory_id": "m", "event_type": "memory_promoted", "actor": "bob"},
        {"memory_id": "m", "action": "memory_archived", "actor": "bob"},
    ]
    lt = latest_transitions(audit)
    active = {"id": "m", "status": "active", "created_by": "alice", "reviewed_by": "bob"}
    assert trust_error(active, lt.get("m")) is not None, "archived→active with stale promo must fail"
    archived = {"id": "m", "status": "archived", "created_by": "alice", "reviewed_by": "bob"}
    assert trust_error(archived, lt.get("m")) is None, "non-live status makes no trust claim"
    audit2 = audit[:2]  # candidate then promoted, current
    good = {"id": "m", "status": "active", "created_by": "alice", "reviewed_by": "bob"}
    assert trust_error(good, latest_transitions(audit2).get("m")) is None, "clean active must pass"
    self_rev = {"id": "m", "status": "active", "created_by": "BOB", "reviewed_by": "bob"}
    assert trust_error(self_rev, latest_transitions(audit2).get("m")) is not None, "case-variant self-review must fail"
    print("lifecycle demo: PASS")


if __name__ == "__main__":
    demo()
