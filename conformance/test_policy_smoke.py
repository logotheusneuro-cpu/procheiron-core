#!/usr/bin/env python3
"""Tier-A smoke for the authority policy's self-review/self-approval independence.

Run:  PYTHONPATH=src python3 conformance/test_policy_smoke.py

Guards the identity-normalization fix: a case or unicode-width variant of the
actor's own name must NOT slip a self-review/self-approval past the gate (the
raw `==` here previously let 'Alice' review 'alice'). assert-based, no framework,
no opa dependency — exercises the stdlib reference backend directly.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from procheiron import policy  # noqa: E402


def main() -> int:
    data = policy.load_data()
    base = {"gate": "memory_promotion_gate", "level": 4,
            "transition": {"from": "candidate", "to": "validated"}}

    # case-variant self-review -> denied
    r = policy.decide_reference({**base, "actor": "Alice", "reviewer": "alice"}, data)
    assert not r["allow"] and any("self-review" in x for x in r["reasons"]), r

    # unicode-width variant self-approval (ﬁ ligature / fullwidth) -> denied
    r = policy.decide_reference({**base, "actor": "Dana_Okoro", "approver": "dana_okoro"}, data)
    assert not r["allow"] and any("self-approval" in x for x in r["reasons"]), r

    # genuinely distinct actors -> no false self-review positive
    r = policy.decide_reference({**base, "actor": "alice", "reviewer": "bob"}, data)
    assert not any("self-review" in x for x in r["reasons"]), r

    print("policy smoke: PASS (case/width-variant self-review + self-approval denied; distinct actors clean)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
