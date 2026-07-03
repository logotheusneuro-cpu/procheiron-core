#!/usr/bin/env python3
"""Tier-A smoke for the trust-loop scorecard.

Run:  PYTHONPATH=src python3 conformance/test_scorecard_smoke.py

Runs compute() against the Meridian fixture (a generic, non-authoring deployment) and asserts the
metrics resolve, the blocks-caught key is wired, and the 'running' verdict reads off the
package validator. assert-based, no framework.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from procheiron import scorecard as sc  # noqa: E402

ROOT = HERE / "generic-vault"


def main() -> int:
    r = sc.compute(ROOT, "2026-06-01", "2026-06-30")
    t = r["trust_loop"]
    # portable read of the fixture deployment via config
    assert t["operational_records"]["value"] >= 1, t
    assert t["independent_promotions"]["value"] >= 1, t          # reviewer != creator found
    assert "blocks_caught" in t and isinstance(t["blocks_caught"]["value"], int), t
    assert r["integrity"]["validator_status"] in ("PASS", "PASS_WITH_WARNINGS"), r["integrity"]
    assert r["running"] is True, r
    print("scorecard smoke: PASS (portable metrics + blocks-caught wired + running verdict)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
