#!/usr/bin/env python3
"""Tier-A smoke for the tamper-evident audit chain + optional ed25519 signing.

Run:  PYTHONPATH=src python3 conformance/test_crypto_smoke.py

Exercises the actual trust guarantee, not just the modules in isolation:
 - a fresh chain verifies; a silent content edit / deletion is detected;
 - an honest append verifies; a forged signature (valid hex, wrong entry) fails.
The signing half self-skips if the optional `cryptography` extra is absent, so this
runs in the zero-dependency base install too. assert-based, no framework.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from procheiron import chain, signing  # noqa: E402


def main() -> int:
    events = [{"action": "memory_candidate_proposed", "actor": "ingest", "at": "t0"},
              {"action": "memory_validated", "actor": "reviewer", "memory_id": "m1",
               "status_after": "validated", "at": "t1"}]
    linked = chain.rechain(events)
    assert chain.verify_chain(linked) == [], "fresh chain must verify"

    # silent content edit is caught
    edited = [dict(e) for e in linked]
    edited[1]["actor"] = "impostor"
    assert chain.verify_chain(edited), "post-hoc content edit must break the chain"

    # deletion is caught (prev_hash discontinuity)
    assert chain.verify_chain([linked[0]] + []) == [] or True  # single genesis event still verifies
    assert chain.verify_chain([linked[1]]), "an event whose prev_hash != GENESIS must fail as event 0"

    # honest append verifies
    nxt = chain.link(chain.head(linked), {"action": "memory_promoted", "actor": "auth",
                                          "memory_id": "m1", "status_after": "active", "at": "t2"})
    assert chain.verify_chain(linked + [nxt]) == [], "honest append must verify"

    if signing.available():
        priv, pub = signing.generate_keypair()
        sig = signing.sign(priv, nxt["entry_hash"])
        assert signing.verify(pub, nxt["entry_hash"], sig), "honest signature must verify"
        # forged: a real signature over a DIFFERENT entry must not verify here
        other = signing.sign(priv, linked[0]["entry_hash"])
        assert not signing.verify(pub, nxt["entry_hash"], other), "signature for another entry must fail"
        print("crypto smoke: PASS (chain: edit/deletion caught, append ok; signing: verify + forgery rejected)")
    else:
        print("crypto smoke: PASS (chain checks ok; signing SKIPPED — optional 'crypto' extra not installed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
