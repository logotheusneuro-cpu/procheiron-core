#!/usr/bin/env python3
"""Single-writer advisory lock for the Procheiron memory indexes (roadmap 3.6).

STAGED ARTIFACT — installs to .procheiron/lib/procheiron_lock.py under the
Phase-3 adoption authorization, shared by memory_promote.py and memory_propose.py
so there is one lock implementation, no drift. Stdlib-only.

Discipline: O_CREAT|O_EXCL create (no auto-steal), age-surfaced contention,
unlink on exit (including SystemExit). Extracted verbatim-in-behavior from the
Lock already living in the live memory_promote.py.
"""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path
from typing import Any


class LockHeld(SystemExit):
    """Raised (as SystemExit, so a CLI exits cleanly) when the lock is held."""


class Lock:
    def __init__(self, root: Path) -> None:
        lock_dir = Path(root) / ".procheiron" / "locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        self.path = lock_dir / "memory_index.lock"

    def __enter__(self) -> "Lock":
        try:
            fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            age = dt.datetime.now().timestamp() - self.path.stat().st_mtime
            raise LockHeld(
                f"memory index lock held ({self.path}, {int(age)}s old); "
                "retry or remove a stale lock manually"
            )
        os.write(fd, f"{os.getpid()} {dt.datetime.now(dt.timezone.utc).isoformat()}\n".encode())
        os.close(fd)
        return self

    def __exit__(self, *_exc: Any) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
