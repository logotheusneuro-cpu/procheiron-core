#!/usr/bin/env python3
"""Procheiron trust-loop scorecard — deployment-portable, read-only, stdlib-only.

Answers one question over a window: *is the memory trust-loop actually running?*
It counts operational records produced, distinct actors, **independent** promotions
(reviewer != creator — the core "a different agent vouched for this" event), and — the
load-bearing signal — **blocks caught** (`promotion_refused` audit events: durable proof
the gate refused an unauthorized promotion). Deployment-portable: paths resolve from
config, integrity uses the package validator.

Mutates NOTHING. Never fabricate records to move these numbers — a failed honest
checkpoint outranks a passed fake one.

    procheiron scorecard --root <vault> [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--read-log PATH] [--json]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .resolve import ResolveError, load_config

# Seed/bootstrap records that predate live operation — never counted as operational.
BOOTSTRAP_PREFIXES = ("mem_20260527_", "mem_20260604_")
TEST_MARKERS = ("test", "probe", "verification", "dry-run", "scratch")
PROMOTION_ACTIONS = ("memory_promoted", "memory_validated")
PROPOSE_ACTION = "memory_candidate_proposed"
REFUSED_ACTION = "promotion_refused"


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    o = json.loads(line)
                    if isinstance(o, dict):
                        out.append(o)
                except json.JSONDecodeError:
                    continue
    return out


def _ts(ev: Dict[str, Any]) -> str:
    return str(ev.get("at") or ev.get("timestamp") or ev.get("created_at") or "")


def _in_window(ts: str, start: str, end: str) -> bool:
    return bool(ts) and start <= ts[:10] <= end


def _looks_test(rec: Dict[str, Any]) -> bool:
    blob = " ".join(str(rec.get(k, "")) for k in ("id", "subject", "statement", "notes")).lower()
    return any(m in blob for m in TEST_MARKERS)


def _index_dir(root: Path) -> Path:
    """Resolve <memory>/index from config; fall back to conventional siblings."""
    try:
        cfg = load_config(explicit_root=str(root))
        if "memory" in cfg.paths:
            return cfg.path("memory") / "index"
    except ResolveError:
        pass
    for cand in (root / "_memory" / "index", root / "memory" / "index"):
        if cand.is_dir():
            return cand
    return root / "memory" / "index"


def _validator_status(root: Path) -> str:
    try:
        src = Path(__file__).resolve().parent.parent  # the src/ that holds the procheiron package
        env = {**os.environ, "PYTHONPATH": str(src) + os.pathsep + os.environ.get("PYTHONPATH", "")}
        proc = subprocess.run([sys.executable, "-m", "procheiron.validate", "--root", str(root), "--records", "--json"],
                              capture_output=True, text=True, timeout=120, env=env)
        if proc.stdout.strip().startswith("{"):
            return json.loads(proc.stdout).get("status", "UNKNOWN")
    except Exception as exc:  # noqa: BLE001
        return f"ERROR:{type(exc).__name__}"
    return "UNKNOWN"


def compute(root: Path, start: str, end: str, read_log: Optional[Path] = None) -> Dict[str, Any]:
    idx = _index_dir(root)
    memories = {str(r.get("id")): r for r in _read_jsonl(idx / "memories.jsonl")}
    audit = _read_jsonl(idx / "audit.jsonl")
    reads = _read_jsonl(read_log) if read_log else []

    def win(ev: Dict[str, Any]) -> bool:
        return _in_window(_ts(ev), start, end)

    # Operational candidate records proposed via the sanctioned path (excl. seed + tests).
    records = sorted({mid for ev in audit if ev.get("action") == PROPOSE_ACTION and win(ev)
                      for mid in [str(ev.get("memory_id") or "")]
                      if mid and not mid.startswith(BOOTSTRAP_PREFIXES)
                      and not _looks_test(memories.get(mid, {}))})

    actors = sorted({str(memories.get(m, {}).get("created_by") or "") for m in records} - {""})

    independent: List[Dict[str, str]] = []
    _seen: set = set()  # count DISTINCT records, not events — one record's
    # candidate->validated + validated->active are two events for one promotion.
    for ev in audit:
        if ev.get("action") in PROMOTION_ACTIONS and win(ev):
            mid = str(ev.get("memory_id") or "")
            creator = str(memories.get(mid, {}).get("created_by") or "")
            reviewer = str(ev.get("actor") or "")
            if reviewer and creator and reviewer != creator and mid not in _seen:
                _seen.add(mid)
                independent.append({"memory_id": mid, "creator": creator, "reviewer": reviewer})

    # BLOCKS CAUGHT — the gate actively refusing an unauthorized promotion (proof-of-blocking).
    blocks = [{"memory_id": str(ev.get("memory_id") or ""), "actor": str(ev.get("actor") or ""),
               "attempted": str(ev.get("attempted_status") or ""), "reason": str(ev.get("reason") or "")[:90]}
              for ev in audit if ev.get("action") == REFUSED_ACTION and win(ev)]

    reads_in = [r for r in reads if win(r)]
    validator = _validator_status(root)
    days = (dt.date.fromisoformat(end) - dt.date.fromisoformat(start)).days

    # "Running for real" = real records flowed AND at least one was independently vouched for,
    # with governance integrity intact. Blocks are bonus evidence the gate is live (0 is fine —
    # it can mean nobody tried to cheat), so they don't gate the verdict.
    running = len(records) > 0 and len(independent) >= 1 and validator in ("PASS", "PASS_WITH_WARNINGS")

    return {
        "window": {"start": start, "end": end, "days": days},
        "trust_loop": {
            "operational_records": {"value": len(records), "ids": records},
            "distinct_actors": {"value": len(actors), "actors": actors},
            "independent_promotions": {"value": len(independent), "detail": independent},
            "blocks_caught": {"value": len(blocks), "detail": blocks},
            "reads": {"value": len(reads_in)},
        },
        "integrity": {"validator_status": validator},
        "running": running,
        "_disclaimer": "Read-only snapshot; the human renders the checkpoint verdict. Never fabricate records.",
    }


def _print_human(r: Dict[str, Any]) -> None:
    t = r["trust_loop"]
    w = r["window"]
    print(f"== Procheiron trust-loop scorecard  ({w['start']} .. {w['end']}, {w['days']}d) ==")
    print(f"  operational records produced   : {t['operational_records']['value']:>4}")
    print(f"  distinct actors                : {t['distinct_actors']['value']:>4}  {t['distinct_actors']['actors']}")
    print(f"  independent promotions         : {t['independent_promotions']['value']:>4}  (reviewer != creator)")
    print(f"  BLOCKS CAUGHT (gate refusals)  : {t['blocks_caught']['value']:>4}  (promotion_refused, proof the gate is live)")
    print(f"  MCP/boot reads                 : {t['reads']['value']:>4}")
    print(f"  governance integrity           : {r['integrity']['validator_status']:>8}")
    print(f"  ----> trust-loop running for real: {'YES' if r['running'] else 'NOT YET'}")
    print("  Read-only; the human renders the verdict. Never fabricate records to move these numbers.")


def main(argv: Optional[List[str]] = None) -> int:
    today = dt.date.today()
    ap = argparse.ArgumentParser(description="Procheiron trust-loop scorecard (read-only).")
    ap.add_argument("--root", help="deployment root (default: ancestor discovery / cwd)")
    ap.add_argument("--end", default=today.isoformat(), help="window end YYYY-MM-DD (default: today)")
    ap.add_argument("--start", help="window start YYYY-MM-DD (default: 30 days before --end)")
    ap.add_argument("--read-log", help="MCP read log path (default: <root>/.procheiron/logs/mcp_reads.jsonl)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.root:
        root = Path(args.root).expanduser()
    else:
        try:
            root = load_config().root
        except ResolveError:
            root = Path.cwd()
    end = args.end
    start = args.start or (dt.date.fromisoformat(end) - dt.timedelta(days=30)).isoformat()
    read_log = (Path(args.read_log).expanduser() if args.read_log
                else root / ".procheiron" / "logs" / "mcp_reads.jsonl")

    report = compute(root, start, end, read_log)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        _print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
