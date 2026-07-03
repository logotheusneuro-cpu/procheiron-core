#!/usr/bin/env python3
"""Source-path normalization for Procheiron memory records.

Converts machine-absolute provenance paths into self-describing, portable
forms so records survive a deployment move (the data-plane weld from the
2026-06-10/11 audits):

- a path under the deployment root becomes root-relative
- a path under any absolute `paths.<key>` from config.yaml becomes
  `{paths.<key>}/<rest>` (longest prefix wins)
- any other absolute path is returned unchanged and reported by the caller

Used by memory_propose.py (normalize at write time) and migrate_records.py
(repair existing records). Stdlib-only.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional, Tuple


def normalize_source_path(cfg: Any, raw: str) -> Tuple[str, bool]:
    """Return (normalized_path, changed). Non-absolute input passes through."""
    if not raw or not raw.startswith('/'):
        return raw, False
    # Collapse `..`/`.` segments BEFORE prefix matching so a path like
    # `/v/memory/../secret/x` does not falsely tokenize under {paths.memory}
    # (review finding L-4). normpath is lexical only — it never touches disk
    # or resolves symlinks, so it cannot leak filesystem state.
    raw = os.path.normpath(raw)
    candidate = Path(raw)
    best_key: Optional[str] = None
    best_len = -1
    for key, value in cfg.paths.items():
        base = Path(str(value))
        if not base.is_absolute():
            continue
        try:
            rest = candidate.relative_to(base)
        except ValueError:
            continue
        if len(str(base)) > best_len:
            best_key, best_len = key, len(str(base))
            best_rest = rest
    root = Path(str(cfg.root))
    try:
        root_rest = candidate.relative_to(root)
        root_len = len(str(root))
    except ValueError:
        root_rest, root_len = None, -1

    if root_rest is not None and root_len >= best_len:
        return root_rest.as_posix(), True
    if best_key is not None:
        rest_str = best_rest.as_posix()
        if rest_str == '.':
            return '{paths.%s}' % best_key, True
        return '{paths.%s}/%s' % (best_key, rest_str), True
    return raw, False
