#!/usr/bin/env python3
"""Tier-A smoke test for the packaged, de-welded MCP server.

Run:  PYTHONPATH=src python3 conformance/test_mcp_smoke.py

Drives the in-process handlers against the generic-vault fixture to prove
deployment-portability: console/memory resolve from config (no hardcoded paths),
and the promote gate denies an under-reviewed transition before any write.
assert-based, no framework.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from procheiron import mcp_server as m  # noqa: E402

ROOT = HERE / "generic-vault"


def _rpc(method, **params):
    return m.handle_request({"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                            ROOT, "smoke", False)


def main() -> int:
    # initialize + tools/list
    assert _rpc("initialize")["result"]["serverInfo"]["name"] == "procheiron"
    names = [t["name"] for t in _rpc("tools/list")["result"]["tools"]]
    assert names == ["memory.search", "memory.get", "memory.propose", "memory.promote"], names

    # de-weld: boot_context resolves the fixture's own console/ from config
    bc = m.boot_context(ROOT)
    assert bc["constitution_present"] is True, bc
    assert bc["console"].endswith("console"), bc["console"]
    assert bc["canon_resources"], "expected canon docs resolved from console/"

    # reads pull from the fixture's memory/index/memories.jsonl
    assert m.search_memories(ROOT, limit=5), "expected fixture memory records"

    # promote GATE denies an under-reviewed transition; nothing is written
    res = m.promote_memory(ROOT, "smoke", "x", "active", "r", "memory_reviewer_curator",
                           [], "a", "wrong_role", "t", "validated", "active", allow_writes=False)
    assert res["allow"] is False and res["ran_promote"] is False, res

    print("MCP smoke: PASS (portable reads via config + promote gate denies)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
