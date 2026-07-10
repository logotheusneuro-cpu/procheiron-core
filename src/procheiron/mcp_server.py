#!/usr/bin/env python3
"""Procheiron MCP server — packaged, deployment-portable.

The console, memory, and writer-script locations resolve from
`{root}/.procheiron/config.yaml` via ``procheiron.resolve``, so the SAME server
runs against any deployment — there are no hardcoded deployment paths.

Tools:
  memory.search   (read-only)  filter memories.jsonl by query/status/scope/type
  memory.get      (read-only)  fetch one record by id
  memory.propose  (write)      append a CANDIDATE via the sanctioned memory_propose.py
  memory.promote  (write)      GATED by procheiron.policy.decide; only on allow does
                               it call the deployment's memory_promote.py
Resources:
  procheiron://boot_context           resolved canon: token map + read order + status
  procheiron://canon/<DOC>            the text of a canonical Core doc

SAFETY:
- Stdlib-only. Implements the MCP wire protocol (JSON-RPC 2.0 over stdio) directly,
  so it runs with ZERO third-party packages. At adoption it can be re-hosted on the
  official ``mcp`` SDK without changing the pure handler functions below.
- NOT a second writer: propose/promote SHELL OUT to the deployment's sanctioned
  scripts, preserving single-writer + lock + audit discipline.
- DRY-RUN BY DEFAULT: mutates nothing unless started with --allow-writes.
- IDENTITY from the client binding: --actor is the bound client identity, used as
  created_by for propose and as the acting actor for the promote policy check.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import policy
from .resolve import ResolveError, load_config

CANON_DOCS = [
    "PROCHEIRON.md", "SOURCE_OF_TRUTH.md", "AGENT_BOOT.md", "SELF_ACTION_POLICY.md",
    "AGENT_REGISTRY.md", "RETRIEVAL_POLICY.md", "PRECEDENCE.md",
    "DECISIONS.md", "BLOCKERS.md", "ACTIVE_PROJECTS.md",
]
from . import __version__

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "procheiron", "version": __version__}

# Set once in main() from --scripts-dir / --read-log (or env). Kept as module state
# because the stdio server is a single bound process.
_SCRIPTS_DIR: Optional[Path] = None
_READ_LOG: Optional[Path] = None


# ---------------------------------------------------------------- path resolution

@lru_cache(maxsize=8)
def _layout(root_str: str) -> Dict[str, Any]:
    """Resolve console/memory dirs from the deployment config — the de-weld.
    Falls back to conventional sibling dirs (console/, memory/) if config is
    absent, so read tools still work on a bare tree."""
    root = Path(root_str)
    console, mem = root / "console", root / "memory"
    profile: Optional[str] = None
    version: Optional[str] = None
    try:
        cfg = load_config(explicit_root=root_str)
        if "console" in cfg.paths:
            console = cfg.path("console")
        if "memory" in cfg.paths:
            mem = cfg.path("memory")
        profile, version = cfg.profile, cfg.version
    except ResolveError:
        pass
    return {"root": root, "console": console, "mem_index": mem / "index",
            "profile": profile, "version": version}


def _scripts_dir(root: Path) -> Path:
    """Where the deployment's sanctioned memory_propose.py / memory_promote.py live.
    --scripts-dir wins; else config paths.scripts; else the root (init'd-adopter layout)."""
    if _SCRIPTS_DIR is not None:
        return _SCRIPTS_DIR
    try:
        cfg = load_config(explicit_root=str(root))
        if "scripts" in cfg.paths:
            return cfg.path("scripts")
    except ResolveError:
        pass
    return root


# ---------------------------------------------------------------- pure handlers

def _load_memories(root: Path) -> List[Dict[str, Any]]:
    path = _layout(str(root))["mem_index"] / "memories.jsonl"
    out: List[Dict[str, Any]] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


# A trusted record is one that cleared independent review. The default read path
# returns ONLY these — an agent must not silently consume a memory Procheiron is
# meant to be quarantining. Unreviewed records are reachable only on explicit
# request (status="candidate", or include_untrusted=True).
TRUSTED_STATUSES = ("active", "validated")


def search_memories(root: Path, query: str = "", status: Optional[str] = None,
                    scope: Optional[str] = None, mtype: Optional[str] = None,
                    limit: int = 20, include_untrusted: bool = False) -> List[Dict[str, Any]]:
    q = (query or "").lower()
    res = []
    for m in _load_memories(root):
        st = m.get("status")
        if status:
            if st != status:
                continue
        elif not include_untrusted and st not in TRUSTED_STATUSES:
            continue  # default: trusted-only
        if scope and m.get("scope") != scope:
            continue
        if mtype and m.get("type") != mtype:
            continue
        if q and q not in (str(m.get("subject", "")) + " " + str(m.get("statement", ""))).lower():
            continue
        res.append({k: m.get(k) for k in ("id", "type", "scope", "status", "subject", "statement",
                                          "confidence", "created_by", "reviewed_by", "valid_from")})
    return res[:limit]


def get_memory(root: Path, memory_id: str) -> Optional[Dict[str, Any]]:
    for m in _load_memories(root):
        if m.get("id") == memory_id:
            return m
    return None


def propose_memory(root: Path, actor: str, mtype: str, scope: str, subject: str,
                   statement: str, source_paths: List[str], confidence: float,
                   allow_writes: bool, dry_run: bool = True) -> Dict[str, Any]:
    if not source_paths:
        return {"error": "at least one source_path is required (provenance, AGENT_BOOT §4)"}
    propose = _scripts_dir(root) / "memory_propose.py"
    cmd = [sys.executable, str(propose), "--root", str(root), "--type", mtype, "--scope", scope,
           "--subject", subject, "--statement", statement, "--confidence", str(confidence),
           "--created-by", actor]
    for sp in source_paths:
        cmd += ["--source-path", sp]
    if dry_run or not allow_writes:
        cmd.append("--dry-run")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {"ok": proc.returncode == 0, "dry_run": dry_run or not allow_writes,
            "stdout": proc.stdout, "stderr": proc.stderr}


def promote_memory(root: Path, actor: str, memory_id: str, new_status: str, reviewer: str,
                   reviewer_role: str, reviewers_completed: List[str], approver: str,
                   approver_role: str, reason: str, transition_from: str, transition_to: str,
                   allow_writes: bool, dry_run: bool = True) -> Dict[str, Any]:
    # Policy gate FIRST — the MCP server authorizes via the same reference policy the
    # validator/promoter use; identity is the bound client actor.
    level = 4  # memory_promotion_gate
    decision = policy.decide({
        "actor": actor, "gate": "memory_promotion_gate", "level": level,
        "paths": ["memory/index/memories.jsonl"],
        "reviewer": reviewer, "reviewers_completed": reviewers_completed,
        "approver": approver, "approver_role": approver_role,
        "transition": {"from": transition_from, "to": transition_to},
    })
    if not decision.get("allow"):
        return {"allow": False, "policy": decision, "ran_promote": False}
    promote = _scripts_dir(root) / "memory_promote.py"
    cmd = [sys.executable, str(promote), "--root", str(root), "--memory-id", memory_id,
           "--new-status", new_status, "--reviewer", reviewer, "--reviewer-role", reviewer_role,
           "--reason", reason]
    if new_status == "active":
        cmd += ["--authorized-by", approver]
    if dry_run or not allow_writes:
        cmd.append("--dry-run")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {"allow": True, "policy": decision, "ran_promote": True,
            "dry_run": dry_run or not allow_writes,
            "ok": proc.returncode == 0, "stdout": proc.stdout, "stderr": proc.stderr}


def boot_context(root: Path) -> Dict[str, Any]:
    lay = _layout(str(root))
    console = lay["console"]
    return {
        "root": str(root),
        "profile": lay["profile"] or "<unresolved>",
        "config_version": lay["version"] or "<unresolved>",
        "console": str(console),
        "read_order": CANON_DOCS,
        "constitution_present": (console / "SELF_ACTION_POLICY.md").is_file(),
        "canon_resources": [f"procheiron://canon/{d}" for d in CANON_DOCS if (console / d).is_file()],
    }


def read_canon(root: Path, doc: str) -> Optional[str]:
    if doc not in CANON_DOCS:
        return None
    path = _layout(str(root))["console"] / doc
    return path.read_text(encoding="utf-8") if path.is_file() else None


# ---------------------------------------------------------------- MCP wire layer

TOOLS = [
    {"name": "memory.search",
     "description": "Search Procheiron memory records (read-only). Returns only TRUSTED "
                    "(active/validated) records by default; pass status='candidate' or "
                    "include_untrusted=true to see records that have not cleared review.",
     "inputSchema": {"type": "object", "properties": {
         "query": {"type": "string"}, "status": {"type": "string"}, "scope": {"type": "string"},
         "type": {"type": "string"}, "limit": {"type": "integer"},
         "include_untrusted": {"type": "boolean"}}}},
    {"name": "memory.get",
     "description": "Get one memory record by id (read-only). Returns the record with its "
                    "status field; an untrusted record is only returned because you named it.",
     "inputSchema": {"type": "object", "required": ["memory_id"],
                     "properties": {"memory_id": {"type": "string"}}}},
    {"name": "memory.propose", "description": "Append a CANDIDATE memory (proposal-only, via the sanctioned writer).",
     "inputSchema": {"type": "object", "required": ["type", "scope", "subject", "statement", "source_paths", "confidence"],
                     "properties": {"type": {"type": "string"}, "scope": {"type": "string"},
                                    "subject": {"type": "string"}, "statement": {"type": "string"},
                                    "source_paths": {"type": "array", "items": {"type": "string"}},
                                    "confidence": {"type": "number"}, "dry_run": {"type": "boolean"}}}},
    {"name": "memory.promote", "description": "Promote a memory record — GATED by the authority policy.",
     "inputSchema": {"type": "object",
                     "required": ["memory_id", "new_status", "reviewer", "reviewers_completed", "approver", "approver_role", "reason", "transition_from", "transition_to"],
                     "properties": {"memory_id": {"type": "string"}, "new_status": {"type": "string"},
                                    "reviewer": {"type": "string"}, "reviewer_role": {"type": "string"},
                                    "reviewers_completed": {"type": "array", "items": {"type": "string"}},
                                    "approver": {"type": "string"}, "approver_role": {"type": "string"},
                                    "reason": {"type": "string"}, "transition_from": {"type": "string"},
                                    "transition_to": {"type": "string"}, "dry_run": {"type": "boolean"}}}},
]


def _text_result(payload: Any) -> Dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(payload, indent=2, ensure_ascii=False)}]}


def _log_read(actor: str, kind: str, detail: str = "") -> None:
    # Best-effort read log (boot/MCP read counting). A logging failure must NEVER
    # break a read — the server stays available no matter what.
    if _READ_LOG is None:
        return
    try:
        import datetime as _dt
        _READ_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _READ_LOG.open("a", encoding="utf-8") as _fh:
            _fh.write(json.dumps({"at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
                                  "actor": actor, "kind": kind, "detail": detail},
                                 ensure_ascii=False) + "\n")
    except Exception:
        pass


def handle_request(req: Dict[str, Any], root: Path, actor: str, allow_writes: bool) -> Optional[Dict[str, Any]]:
    method = req.get("method")
    rid = req.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": PROTOCOL_VERSION, "serverInfo": SERVER_INFO,
            "capabilities": {"tools": {}, "resources": {}}}}
    if method in ("notifications/initialized", "initialized"):
        return None  # notification: no response
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "resources/list":
        console = _layout(str(root))["console"]
        resources = [{"uri": "procheiron://boot_context", "name": "Procheiron boot context",
                      "mimeType": "application/json"}]
        for d in CANON_DOCS:
            if (console / d).is_file():
                resources.append({"uri": f"procheiron://canon/{d}", "name": d, "mimeType": "text/markdown"})
        return {"jsonrpc": "2.0", "id": rid, "result": {"resources": resources}}
    if method == "resources/read":
        uri = req.get("params", {}).get("uri", "")
        if uri == "procheiron://boot_context":
            _log_read(actor, "boot_context")
            return {"jsonrpc": "2.0", "id": rid, "result": {"contents": [
                {"uri": uri, "mimeType": "application/json",
                 "text": json.dumps(boot_context(root), indent=2)}]}}
        if uri.startswith("procheiron://canon/"):
            doc = uri.split("/")[-1]
            _log_read(actor, "canon", doc)
            text = read_canon(root, doc)
            if text is None:
                return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": f"unknown canon doc {doc}"}}
            return {"jsonrpc": "2.0", "id": rid, "result": {"contents": [
                {"uri": uri, "mimeType": "text/markdown", "text": text}]}}
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": f"unknown resource {uri}"}}
    if method == "tools/call":
        params = req.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {}) or {}
        if name in ("memory.search", "memory.get"):
            _log_read(actor, name, str(args.get("memory_id", args.get("query", ""))))
        try:
            result = dispatch_tool(name, args, root, actor, allow_writes)
            return {"jsonrpc": "2.0", "id": rid, "result": _text_result(result)}
        except Exception as exc:  # noqa: BLE001
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32603, "message": str(exc)}}
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"method not found: {method}"}}


def dispatch_tool(name: str, args: Dict[str, Any], root: Path, actor: str, allow_writes: bool) -> Any:
    if name == "memory.search":
        return search_memories(root, args.get("query", ""), args.get("status"), args.get("scope"),
                               args.get("type"), int(args.get("limit", 20)),
                               bool(args.get("include_untrusted", False)))
    if name == "memory.get":
        return get_memory(root, args["memory_id"]) or {"error": "not found"}
    if name == "memory.propose":
        return propose_memory(root, actor, args["type"], args["scope"], args["subject"], args["statement"],
                              args.get("source_paths", []), float(args["confidence"]), allow_writes,
                              bool(args.get("dry_run", True)))
    if name == "memory.promote":
        return promote_memory(root, actor, args["memory_id"], args["new_status"], args["reviewer"],
                              args.get("reviewer_role", "memory_reviewer_curator"),
                              args.get("reviewers_completed", []), args["approver"], args["approver_role"],
                              args["reason"], args["transition_from"], args["transition_to"], allow_writes,
                              bool(args.get("dry_run", True)))
    raise ValueError(f"unknown tool {name}")


def serve(root: Path, actor: str, allow_writes: bool) -> None:
    """Blocking stdio JSON-RPC loop (one JSON object per line)."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": None,
                             "error": {"code": -32700, "message": "parse error"}}) + "\n")
            sys.stdout.flush()
            continue
        resp = handle_request(req, root, actor, allow_writes)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


def main(argv: Optional[List[str]] = None) -> int:
    global _SCRIPTS_DIR, _READ_LOG
    ap = argparse.ArgumentParser(description="Procheiron MCP server (deployment-portable).")
    ap.add_argument("--root", help="deployment root (default: ancestor discovery / cwd)")
    ap.add_argument("--actor", default="mcp_client", help="bound client identity (created_by / policy actor)")
    ap.add_argument("--scripts-dir", help="dir holding the deployment's memory_propose.py / memory_promote.py "
                                          "(default: config paths.scripts, else root)")
    ap.add_argument("--read-log", help="path for the best-effort read log (default: <root>/.procheiron/logs/mcp_reads.jsonl)")
    ap.add_argument("--allow-writes", action="store_true",
                    help="permit real propose/promote writes (default: dry-run only)")
    ap.add_argument("--boot-context", action="store_true",
                    help="one-shot: print boot_context JSON (logged as a read) and exit")
    args = ap.parse_args(argv)

    if args.root:
        root = Path(args.root).expanduser()
    else:
        # portable: discover the deployment root from cwd via config ancestor search
        try:
            root = load_config().root
        except ResolveError:
            root = Path.cwd()
    if args.scripts_dir:
        _SCRIPTS_DIR = Path(args.scripts_dir).expanduser()
    _READ_LOG = (Path(args.read_log).expanduser() if args.read_log
                 else Path(os.environ.get("PROCHEIRON_READ_LOG",
                                          str(root / ".procheiron" / "logs" / "mcp_reads.jsonl"))))

    if args.boot_context:
        _log_read(args.actor, "boot_context", "cli")
        print(json.dumps(boot_context(root), indent=2))
        return 0
    serve(root, args.actor, args.allow_writes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
