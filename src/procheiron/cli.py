#!/usr/bin/env python3
"""Procheiron CLI — version, init, validate, conformance."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _find_conformance_runner() -> Path | None:
    """Return path to run_conformance.py if we can locate it.

    Checks two candidates:
    1. Three levels up from this file (covers editable / src-layout installs).
    2. cwd/conformance/run_conformance.py (invoked from repo root).
    """
    here = Path(__file__).resolve().parent
    # src/procheiron/ -> src/ -> project_root/ -> conformance/
    candidate_repo = here.parent.parent / "conformance" / "run_conformance.py"
    if candidate_repo.is_file():
        return candidate_repo
    candidate_cwd = Path.cwd() / "conformance" / "run_conformance.py"
    if candidate_cwd.is_file():
        return candidate_cwd
    return None


def _cmd_version(_args: argparse.Namespace) -> int:
    from . import __version__
    print(__version__)
    return 0


def _cmd_init(args: argparse.Namespace) -> int:
    from .init import main as init_main
    argv = ["--root", args.root, "--profile", args.profile]
    if args.force:
        argv.append("--force")
    return init_main(argv) or 0


def _detect_tier(root: str) -> str:
    """minimal-memory-commons vs full-governance-profile.

    The full validator requires `paths.sources`; the minimal adopter has none.
    Detect from config.yaml WITHOUT importing the (sources-requiring) resolver, so a
    minimal deployment never trips the full loader. Conservative default: 'full' when
    a config can't be read (the full validator then emits a clear, specific error).
    """
    cfg = Path(root) / ".procheiron" / "config.yaml"
    try:
        lines = cfg.read_text(encoding="utf-8").splitlines()
    except OSError:
        return "full"
    for ln in lines:
        if ln.strip().startswith("sources:"):
            return "full"
    return "minimal"


def _cmd_validate(args: argparse.Namespace) -> int:
    tier = "minimal" if args.minimal else "full" if args.full else _detect_tier(args.root)
    if tier == "minimal":
        # Tier 1: run the bundled minimal-memory-commons validator (self-contained,
        # ships its own procheiron_schema sibling under data/adopter/).
        mv = Path(__file__).resolve().parent / "data" / "adopter" / "validate_minimal.py"
        proc = subprocess.run([sys.executable, str(mv), "--root", args.root, "--json"],
                              capture_output=True, text=True)
        try:
            result = json.loads(proc.stdout)
        except (json.JSONDecodeError, ValueError):
            result = {"status": "FAIL",
                      "errors": [proc.stderr.strip() or "minimal validator produced no JSON output"]}
    else:
        from .validate import run
        try:
            result = run(args.root, records=args.records)
        except Exception as exc:  # noqa: BLE001
            result = {"status": "FAIL", "errors": [f"{type(exc).__name__}: {exc}"]}

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        status = result.get("status", "FAIL")
        print(f"Procheiron validation ({tier} tier): {status}")
        for err in result.get("errors", []):
            print(f"  ERROR: {err}")
        for warn in result.get("warnings", []):
            print(f"  WARNING: {warn}")
    return 0 if result.get("status") in {"PASS", "PASS_WITH_WARNINGS"} else 1


def _cmd_conformance(args: argparse.Namespace) -> int:
    runner = _find_conformance_runner()
    if runner is None:
        print(
            "conformance fixtures are not bundled with the installed package.\n"
            "Clone the repo and run:  python3 conformance/run_conformance.py\n"
            "  https://github.com/procheiron/procheiron-core"
        )
        return 1
    cmd = [sys.executable, str(runner)]
    if getattr(args, "json", False):
        cmd.append("--json")
    proc = subprocess.run(cmd)
    return proc.returncode


def _cmd_mcp(args: argparse.Namespace) -> int:
    from .mcp_server import main as mcp_main
    argv: list[str] = []
    if args.root:
        argv += ["--root", args.root]
    argv += ["--actor", args.actor]
    if args.scripts_dir:
        argv += ["--scripts-dir", args.scripts_dir]
    if args.read_log:
        argv += ["--read-log", args.read_log]
    if args.allow_writes:
        argv.append("--allow-writes")
    if args.boot_context:
        argv.append("--boot-context")
    return mcp_main(argv) or 0


def _cmd_scorecard(args: argparse.Namespace) -> int:
    from .scorecard import main as sc_main
    argv: list[str] = []
    if args.root:
        argv += ["--root", args.root]
    if args.start:
        argv += ["--start", args.start]
    if args.end:
        argv += ["--end", args.end]
    if args.read_log:
        argv += ["--read-log", args.read_log]
    if args.json:
        argv.append("--json")
    return sc_main(argv) or 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="procheiron",
        description="Procheiron governance and provenance layer for agent memory.",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # version
    sub.add_parser("version", help="Print version and exit.")

    # init
    p_init = sub.add_parser("init", help="Scaffold a minimal Procheiron memory commons.")
    p_init.add_argument("root", help="Directory to initialise (created if absent).")
    p_init.add_argument("--profile", default="default",
                        help="Profile name for config.yaml (default: 'default').")
    p_init.add_argument("--force", action="store_true",
                        help="Overwrite existing non-empty files.")

    # validate
    p_val = sub.add_parser("validate", help="Validate a Procheiron deployment.")
    p_val.add_argument("root", help="Root directory of the deployment to validate.")
    p_val.add_argument("--json", action="store_true",
                       help="Print full JSON result.")
    p_val.add_argument("--records", action="store_true",
                       help="Force memory-record validation (overrides profile lint).")
    p_val.add_argument("--full", action="store_true",
                       help="Force full-governance-profile validation.")
    p_val.add_argument("--minimal", action="store_true",
                       help="Force minimal-memory-commons validation.")

    # conformance
    p_conf = sub.add_parser("conformance",
                             help="Run the Procheiron conformance suite (repo checkout required).")
    p_conf.add_argument("--json", action="store_true", help="Print JSON report.")

    # mcp
    p_mcp = sub.add_parser("mcp", help="Run the Procheiron MCP server (stdio JSON-RPC) for a deployment.")
    p_mcp.add_argument("--root", help="Deployment root (default: ancestor discovery / cwd).")
    p_mcp.add_argument("--actor", default="mcp_client", help="Bound client identity (created_by / policy actor).")
    p_mcp.add_argument("--scripts-dir", help="Dir holding memory_propose.py / memory_promote.py "
                                             "(default: config paths.scripts, else root).")
    p_mcp.add_argument("--read-log", help="Path for the best-effort read log.")
    p_mcp.add_argument("--allow-writes", action="store_true",
                       help="Permit real propose/promote writes (default: dry-run only).")
    p_mcp.add_argument("--boot-context", action="store_true",
                       help="One-shot: print boot_context JSON and exit.")

    # scorecard
    p_sc = sub.add_parser("scorecard", help="Trust-loop scorecard: records, independent promotions, blocks caught.")
    p_sc.add_argument("--root", help="Deployment root (default: ancestor discovery / cwd).")
    p_sc.add_argument("--start", help="Window start YYYY-MM-DD (default: 30 days before --end).")
    p_sc.add_argument("--end", help="Window end YYYY-MM-DD (default: today).")
    p_sc.add_argument("--read-log", help="MCP read-log path (default: <root>/.procheiron/logs/mcp_reads.jsonl).")
    p_sc.add_argument("--json", action="store_true", help="Print JSON report.")

    args = parser.parse_args()
    dispatch = {
        "version": _cmd_version,
        "init": _cmd_init,
        "validate": _cmd_validate,
        "conformance": _cmd_conformance,
        "mcp": _cmd_mcp,
        "scorecard": _cmd_scorecard,
    }
    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
