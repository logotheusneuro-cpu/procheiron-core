#!/usr/bin/env python3
"""Shared Procheiron secret-pattern registry.

Single source of truth for secret detection across the validator
(validate_procheiron2.py), the candidate-append helper (memory_propose.py),
and the promotion gate (memory_promote.py). Reunified 2026-06-11 per the
A-to-Z audit finding that the v2 validator had regressed to 3 patterns
(AKIA dropped) while memory_propose carried 11 unshared.

Stdlib-only. Importing this module must never require third-party packages.
"""
from __future__ import annotations

import re
import unicodedata
from typing import List, Tuple

# (label, compiled pattern). Labels are stable identifiers used in reports.
SECRET_PATTERNS: List[Tuple[str, "re.Pattern[str]"]] = [
    ("openai_style_key", re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b")),
    ("stripe_key", re.compile(r"\bsk_(live|test)_[A-Za-z0-9]{16,}\b")),
    ("github_token", re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b")),
    ("github_fine_grained", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b")),
    ("aws_access_key_id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.")),
    ("bearer_token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-_\.=]{16,}")),
    (
        "credential_assignment",
        re.compile(r"(?i)[\"']?(password|passwd|api[_-]?key|secret|token)[\"']?\s*[:=]\s*[\"']?\S{12,}"),
    ),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]


_ZERO_WIDTH = {"​", "‌", "‍", "⁠", "﻿"}


def normalize_for_scan(text: str) -> str:
    """NFKC-normalize and strip zero-width/format chars before secret scanning.

    Defeats the common evasions: a zero-width space inside a key, a fullwidth
    colon in `password：`, an NBSP in a token. Without this, the regexes run on
    the raw bytes and a single invisible character hides a live credential
    (review finding L-1). We strip Unicode Cf (format) chars and the explicit
    zero-width set, then NFKC-fold width/compatibility variants.
    """
    if not text:
        return ""
    out = []
    for ch in text:
        if ch in _ZERO_WIDTH:
            continue
        if unicodedata.category(ch) == "Cf":
            continue
        out.append(ch)
    return unicodedata.normalize("NFKC", "".join(out))


def scan_text(text: str) -> List[Tuple[int, str]]:
    """Return (line_number, label) findings for every secret-pattern hit.

    Each line is scanned both raw and normalized, so an evaded credential is
    still caught while line numbers stay meaningful.
    """
    findings: List[Tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        norm = normalize_for_scan(line)
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(line) or (norm != line and pattern.search(norm)):
                findings.append((lineno, label))
    return findings


def first_match_label(text: str) -> str | None:
    """Return the label of the first matching pattern, or None.

    Scans both the raw and normalized forms so zero-width / homoglyph evasions
    do not slip a live secret past the guard.
    """
    raw = text or ""
    norm = normalize_for_scan(raw)
    for label, pattern in SECRET_PATTERNS:
        if pattern.search(raw) or (norm != raw and pattern.search(norm)):
            return label
    return None
