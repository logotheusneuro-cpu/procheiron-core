#!/usr/bin/env python3
"""Tamper-evident hash chain for the audit log (stdlib-only, zero deps).

The audit log is append-only. Without a chain, an insider with write access can
silently rewrite, insert, delete, or reorder past events — the exact hole the
honor-system model left open. This module links each event to its predecessor:

    entry_hash(i) = BLAKE2b( prev_hash(i) || "\\n" || canonical(event_i) )
    prev_hash(i)  = entry_hash(i-1)          (genesis prev_hash = GENESIS)

To alter event k you must recompute entry_hash(k) and every entry_hash after it,
so any change is detectable by anyone holding a later chain head. Anchor the head
where the writer cannot retroactively rewrite it (a git commit, an external
transparency log, a printed digest) and the log becomes tamper-EVIDENT — a
Rekor-style guarantee with no dependency. Authorship proof is a separate layer
(see signing.py); this layer proves the *sequence* was not edited after the fact.

Canonicalization excludes the chain/signature fields themselves so the hash covers
event CONTENT, and is byte-identical between writer and validator (sorted keys,
compact separators, UTF-8).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

# Fields the hash/signature layer adds — excluded from the canonical content so a
# hash never covers itself and re-verification is deterministic.
META_FIELDS = ("prev_hash", "entry_hash", "sig", "sig_key_id")
GENESIS = "0" * 64
_DIGEST_SIZE = 32  # 256-bit BLAKE2b


def canonical(event: Dict[str, Any]) -> bytes:
    """Deterministic content bytes for an event (excludes chain/sig meta fields).

    Sorted keys + compact separators + ensure_ascii=False → the writer and the
    validator produce identical bytes for identical content."""
    content = {k: v for k, v in event.items() if k not in META_FIELDS}
    return json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def entry_hash(prev_hash: str, event: Dict[str, Any]) -> str:
    """The chain hash binding this event's content to the prior entry."""
    h = hashlib.blake2b(digest_size=_DIGEST_SIZE)
    h.update((prev_hash or GENESIS).encode("utf-8"))
    h.update(b"\n")
    h.update(canonical(event))
    return h.hexdigest()


def link(prev_entry_hash: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of `event` stamped with prev_hash + entry_hash. Writers call
    this with the entry_hash of the last event in the log (GENESIS if empty)."""
    prev = prev_entry_hash or GENESIS
    stamped = {k: v for k, v in event.items() if k not in ("prev_hash", "entry_hash")}
    stamped["prev_hash"] = prev
    stamped["entry_hash"] = entry_hash(prev, stamped)
    return stamped


def head(events: List[Dict[str, Any]]) -> str:
    """entry_hash of the last chained event, or GENESIS for an empty/unchained log."""
    for ev in reversed(events):
        if isinstance(ev, dict) and ev.get("entry_hash"):
            return str(ev["entry_hash"])
    return GENESIS


def verify_chain(events: List[Dict[str, Any]]) -> List[str]:
    """Verify an unbroken chain over ALL events, in file order. Returns a list of
    human-readable error strings (empty = intact). Enforced only when a deployment
    opts in via lint `verify_audit_chain`; every event must then carry prev_hash +
    entry_hash forming a continuous chain from GENESIS.

    Catches: content edits (entry_hash mismatch), reordering / deletion / insertion
    (prev_hash discontinuity), and truncation of the head is caught by an external
    anchor, not here."""
    errors: List[str] = []
    expected_prev = GENESIS
    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            errors.append(f"audit event {i}: not an object")
            return errors
        stored_prev = ev.get("prev_hash")
        stored_eh = ev.get("entry_hash")
        if stored_prev is None or stored_eh is None:
            errors.append(f"audit event {i} (id={ev.get('id') or ev.get('event_id') or '?'}): "
                          f"missing chain fields (prev_hash/entry_hash) — chain verification is on")
            return errors  # a gap breaks continuity; stop to avoid noise
        if stored_prev != expected_prev:
            errors.append(f"audit event {i}: chain broken — prev_hash {str(stored_prev)[:12]}… "
                          f"!= expected {expected_prev[:12]}… (event reordered/inserted/deleted)")
            return errors
        recomputed = entry_hash(str(stored_prev), ev)
        if recomputed != stored_eh:
            errors.append(f"audit event {i} (id={ev.get('id') or ev.get('event_id') or '?'}): "
                          f"entry_hash mismatch — content was altered after it was written")
            return errors
        expected_prev = str(stored_eh)
    return errors


def rechain(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Recompute the whole chain over `events` in order (migration/fixture helper).
    Returns new event dicts with correct prev_hash/entry_hash; preserves any `sig`
    (though a sig over a changed entry_hash will no longer verify — re-sign after)."""
    out: List[Dict[str, Any]] = []
    prev = GENESIS
    for ev in events:
        stamped = link(prev, ev)
        out.append(stamped)
        prev = stamped["entry_hash"]
    return out


def head_from_file(path) -> str:
    """entry_hash of the last event in an audit.jsonl, or GENESIS if empty/unchained.
    Reads only the final non-empty line — O(1)-ish, safe under the writer's lock."""
    import os
    try:
        size = os.path.getsize(path)
    except OSError:
        return GENESIS
    if size == 0:
        return GENESIS
    with open(path, "rb") as fh:  # walk back to the last newline-delimited record
        chunk = min(size, 65536)
        fh.seek(-chunk, os.SEEK_END)
        tail = fh.read().decode("utf-8", errors="replace").strip().splitlines()
    for line in reversed(tail):
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            return GENESIS  # unparse-able tail — let the validator flag it; don't chain onto garbage
        return str(ev.get("entry_hash") or GENESIS)
    return GENESIS


def append_event(path, event: Dict[str, Any], key_hex: Optional[str] = None) -> Dict[str, Any]:
    """Link `event` onto the chain in `path` and atomically append it. If `key_hex`
    is given, ed25519-sign the entry_hash (requires the optional `crypto` extra) and
    stamp `sig` + `sig_key_id`. Returns the stamped event. Caller must hold the
    single-writer lock. Uses O_APPEND + O_NOFOLLOW, matching the writers' discipline."""
    import os
    stamped = link(head_from_file(path), event)
    if key_hex:
        from . import signing
        stamped["sig"] = signing.sign(key_hex, stamped["entry_hash"])
        stamped.setdefault("sig_key_id", str(event.get("actor") or ""))
    line = json.dumps(stamped, ensure_ascii=False, separators=(",", ":")) + "\n"
    payload = line.encode("utf-8")
    try:  # keep one record per line even if the file lacks a trailing newline
        if os.path.getsize(path) > 0:
            with open(path, "rb") as fh:
                fh.seek(-1, os.SEEK_END)
                if fh.read(1) != b"\n":
                    payload = b"\n" + payload
    except OSError:
        pass
    fd = os.open(str(path), os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o644)
    try:
        written = 0
        while written < len(payload):
            written += os.write(fd, payload[written:])
    finally:
        os.close(fd)
    return stamped


def _demo() -> None:
    events = [{"action": "a", "actor": "x", "at": "t0"},
              {"action": "b", "actor": "y", "at": "t1"},
              {"action": "c", "actor": "z", "at": "t2"}]
    chained = rechain(events)
    assert verify_chain(chained) == [], "fresh chain must verify"
    # tamper with content of the middle event
    bad = [dict(e) for e in chained]
    bad[1]["actor"] = "attacker"
    assert verify_chain(bad), "content edit must be detected"
    # delete the middle event (reorder/deletion)
    gap = [chained[0], chained[2]]
    assert verify_chain(gap), "deletion must break continuity"
    # missing chain fields
    assert verify_chain([{"action": "a", "actor": "x", "at": "t0"}]), "unchained event must fail when verifying"
    # a genuine append verifies
    nxt = link(head(chained), {"action": "d", "actor": "w", "at": "t3"})
    assert verify_chain(chained + [nxt]) == [], "honest append must verify"
    print("chain self-check: PASS (fresh ok; edit/deletion/gap detected; append ok)")


if __name__ == "__main__":
    _demo()
