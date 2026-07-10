#!/usr/bin/env python3
"""Profile-agnostic Procheiron validator — v2.1 (Phase 0/1 extension).

Read-only. Stdlib-only. Uses config.yaml for topology instead of hardcoded
deployment paths. Optional per-profile lint files add deployment-specific checks.

v2.1 (2026-06-11, roadmap items 0.6 + 1.1) extends the Tier-1 draft with:
- per-file Core-doc lint scoping: `core_docs` + `forbid_absolute_paths_in_core_docs`
  + `forbidden_core_doc_literals` (a reintroduced deployment weld in any
  parameterized Core doc fails, without failing live deployment ledgers)
- `required_console_extra`: profile-required console files (e.g. the adopted
  constitution) beyond the portable Core minimum
- memory-record validation (`validate_memory_records` or --records): schema
  fields, lifecycle/status enums, provenance, active/validated => independent
  reviewer + matching promotion audit event, structured-supersession
  consistency (prose supersession claims without supersedes[] fail),
  proposal-only records may not be active, duplicate ids fail
- `forbid_absolute_paths_in_memory_records`: machine-absolute source_paths in
  memories.jsonl fail (the data-plane weld the *.md-only scan could not see)
- restored adapter-manifest checks from v1 (proposed-only unless allowlisted),
  skipped cleanly when a deployment has no manifests directory
- unified secret patterns shared with memory_propose/memory_promote via
  lib/procheiron_patterns.py (11 patterns; the v2.0 regression to 3 is fixed)

All new lint keys default off/absent, so existing profile lints
(portable-strict, demo-generic) behave exactly as before.

THREAT MODEL (read before trusting record validation):
Record validation corroborates an active/validated record against a promotion
event in audit.jsonl, and ties that event's actor to the named reviewer and the
actor registry — catching naive forgery, hand-flipped status, self-review, and
confused-agent errors. With `verify_audit_chain` on, the audit log is also
tamper-EVIDENT (chain.py): a silent edit/insert/delete/reorder of a past event
breaks the hash chain. With `verify_signatures` + `known_actor_keys`, forging an
event additionally requires the actor's ed25519 private key.
BUT this is a SINGLE-TRUST-DOMAIN model. An adversary with write access to the
audit log can rebuild the whole chain from GENESIS (verify_chain sees only
internal continuity), and — because `known_actor_keys` lives in the same writable
profile — can also swap the registered public keys and re-sign the rewrite. So
chain + signing close the dual-write forgery ONLY when BOTH (a) the chain head is
externally anchored (validate `--expect-head <hex>`, git-pinned) AND (b) the key
registry is out of the writer's write scope (separate OS user / HSM / Sigstore
keyless). On their own, in one trust domain, they raise the cost but do not
prevent a determined insider. Do not describe this validator as preventing forged
records absent those two out-of-band anchors.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve()
from . import lifecycle
from .resolve import ResolveError, load_config
from .patterns import SECRET_PATTERNS, normalize_for_scan

REQUIRED_CONSOLE = [
    'PROCHEIRON.md', 'PRECEDENCE.md', 'AGENT_BOOT.md', 'SOURCE_OF_TRUTH.md',
    'AGENT_REGISTRY.md', 'DECISIONS.md', 'BLOCKERS.md', 'ACTIVE_PROJECTS.md',
]
REQUIRED_MEMORY = ['README.md', 'SCHEMA.md', 'VALIDATION.md']
CORE_DOCTRINE = {
    'agent_neutral': ['agent-neutral'],
    'human_visible': ['human-visible'],
    'provenance': ['provenance'],
    'propose_not_promote': ['propose', 'self-authorize', 'promotion'],
    'runtime_constraints_binding': ['runtime', 'developer', 'remain binding'],
}
# Case-insensitive, broader root set, plus Windows drive/UNC paths. A Core doc
# must carry NO machine-absolute path, so over-matching here is acceptable; the
# prior 6-root case-sensitive set let /root, /srv, /data, /usr, /media, /Home,
# and C:\ through (review finding HIGH abs-path-regex).
ABSOLUTE_PATH_RE = re.compile(
    r'(?i)(?:/(?:home|users|mnt|var|opt|etc|root|srv|data|usr|media|run)/[^\s`)\]]+'
    r'|~/[^\s`)\]]+'
    r'|\$HOME/[^\s`)\]]+'
    r'|[a-z]:\\[^\s`)\]]+'
    r'|\\\\[a-z0-9._-]+\\[^\s`)\]]+)'
)
# Record source_paths legitimately reference root-relative paths and {paths.*}
# tokens; only true machine-absolutes are flagged there.
ABSOLUTE_RECORD_PATH_RE = re.compile(r'(?i)^(?:/(?:home|users|mnt|var|opt|etc|root|srv|data|usr|media|run)/|~/|\$HOME/|[a-z]:\\|\\\\)')

MEMORY_STATUSES = {'draft', 'candidate', 'validated', 'active', 'superseded', 'archived', 'disputed'}
MEMORY_TYPES = {'fact', 'decision', 'preference', 'lesson', 'procedure_pointer', 'blocker', 'relation', 'task_state'}
MEMORY_SCOPES = {'global', 'profile', 'business', 'project', 'agent', 'user', 'customer', 'system'}
SENSITIVITY_LEVELS = {'public', 'internal', 'confidential', 'restricted', 'secret_ref'}
VISIBILITY_LEVELS = {'human_visible', 'restricted_summary', 'metadata_only'}
REQUIRED_RECORD_FIELDS = ['id', 'type', 'scope', 'profile', 'subject', 'statement',
                          'status', 'confidence', 'created_at', 'created_by']
PROMOTION_EVENT_ACTIONS = {'memory_promoted', 'memory_validated'}
# Heuristic backstop only — structured supersedes[]/supersessions.jsonl are the
# authority. Broadened to common synonyms; a negation guard avoids flagging
# "does NOT supersede mem_x" (review findings).
PROSE_SUPERSESSION_RE = re.compile(
    r'(?i)\b(?:supersed\w*|replaces?|obsoletes?|deprecates?)\b[^\n]{0,200}?\bmem_[a-z0-9][a-z0-9_]+')
PROSE_NEGATION_RE = re.compile(r"(?i)\b(?:not|never|n't|without|unlike|no longer)\b")
_SENTENCE_BOUNDARY_RE = re.compile(r'[.!?\n]')


def is_negated_claim(text: str, match_start: int, match_end: int) -> bool:
    """True if a negation governs the supersession verb. Negation is scoped to
    the verb's OWN clause: scan only from the last sentence boundary before the
    match. This avoids a stray 'not' in a prior sentence ('token rotation, not
    scope edits. Supersedes mem_x') causing a false negative on a real claim."""
    boundaries = [m.end() for m in _SENTENCE_BOUNDARY_RE.finditer(text, 0, match_start)]
    clause_start = boundaries[-1] if boundaries else 0
    return bool(PROSE_NEGATION_RE.search(text[clause_start:match_end]))


def _lint_fingerprint(lint: Dict[str, Any]) -> str:
    """Short stable hash of the lint's enforcement-bearing keys, so a CI/reviewer
    can detect a downgraded lint in force (review finding LOW operator-lint)."""
    import hashlib
    keys = ['forbid_absolute_paths_in_core', 'forbid_absolute_paths_in_core_docs',
            'forbid_absolute_paths_in_memory_records', 'validate_memory_records',
            'core_docs', 'forbidden_core_doc_literals', 'required_console_extra',
            'required_literals', 'forbidden_core_literals',
            'verify_audit_chain', 'verify_signatures', 'require_signatures']
    payload = json.dumps({k: lint.get(k) for k in keys}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def read(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')


# Profiles that legitimately ship no lint file (run core-only without warning).
_CORE_ONLY_PROFILES = {'core', 'core-only', 'core_only'}

_LINT_LIST_KEYS = [
    'core_docs', 'required_console_extra', 'deprecated_or_duplicate_roots',
    'required_literals', 'forbidden_core_literals', 'forbidden_core_doc_literals',
    'known_actors', 'known_actor_groups',
]


def load_profile_lint(root: Path, profile: str, profiles_dir: Optional[str]) -> Tuple[Dict[str, Any], Optional[str]]:
    """Return (lint, source_path). source_path is None when no file was found."""
    candidates: List[Path] = []
    if profiles_dir:
        candidates.append(Path(profiles_dir) / profile / 'lint.json')
    candidates.append(root / '.procheiron' / 'profiles' / profile / 'lint.json')
    for path in candidates:
        if path.is_file():
            return json.loads(path.read_text(encoding='utf-8')), str(path)
    return {'profile': profile, 'lint_level': 'core_only'}, None


def check_lint_schema(lint: Dict[str, Any], errors: List[str]) -> None:
    """Type-check lint fields so a malformed-but-valid-JSON lint fails cleanly
    instead of raising an uncaught TypeError mid-scan (review finding MEDIUM)."""
    for key in _LINT_LIST_KEYS:
        if key in lint and not isinstance(lint[key], list):
            errors.append(f'lint key {key!r} must be a list, got {type(lint[key]).__name__}')
    for key in ['forbid_absolute_paths_in_core', 'forbid_absolute_paths_in_core_docs',
                'forbid_absolute_paths_in_memory_records', 'validate_memory_records',
                'verify_audit_chain', 'verify_signatures', 'require_signatures']:
        if key in lint and not isinstance(lint[key], bool):
            errors.append(f'lint key {key!r} must be a boolean, got {type(lint[key]).__name__}')
    if 'known_actor_keys' in lint and not isinstance(lint['known_actor_keys'], dict):
        errors.append(f"lint key 'known_actor_keys' must be an object, got {type(lint['known_actor_keys']).__name__}")
    for group in lint.get('known_actor_groups', []) if isinstance(lint.get('known_actor_groups'), list) else []:
        if not isinstance(group, list):
            errors.append('each known_actor_groups entry must be a list')


_MAX_SCAN_LINE = 50_000  # ReDoS guard: skip pathologically long single lines


def scan_file_for_secrets(root: Path, path: Path) -> List[str]:
    """Scan a file line-by-line for secrets. No whole-file size cap — a real key
    padded past 500 KB previously evaded the scan (review finding MEDIUM). Each
    line is checked raw and NFKC/zero-width-normalized (homoglyph evasion)."""
    findings: List[str] = []
    try:
        with path.open('r', encoding='utf-8', errors='replace') as handle:
            for lineno, line in enumerate(handle, 1):
                if len(line) > _MAX_SCAN_LINE:
                    line = line[:_MAX_SCAN_LINE]
                norm = normalize_for_scan(line)
                for label, pat in SECRET_PATTERNS:
                    if pat.search(line) or (norm != line and pat.search(norm)):
                        findings.append(f'{rel(root, path)}:{lineno}:{label}')
    except OSError as exc:
        findings.append(f'{rel(root, path)}:0:unreadable ({exc})')
    return findings


def has_non_ascii_letter(line: str) -> bool:
    """True if the line contains a letter outside Basic Latin — a homoglyph
    smuggling vector in Core docs, which are expected to be ASCII prose."""
    for ch in line:
        if ch.isalpha() and ord(ch) > 0x7F:
            return True
    return False


def parse_jsonl(path: Path, errors: List[str], root: Path) -> List[Tuple[int, Dict[str, Any]]]:
    """Parse a JSONL file; malformed lines are validation errors, not crashes."""
    records: List[Tuple[int, Dict[str, Any]]] = []
    if not path.is_file():
        return records
    for lineno, line in enumerate(read(path).splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f'{rel(root, path)}:{lineno}: invalid JSON ({exc})')
            continue
        if isinstance(obj, dict):
            records.append((lineno, obj))
        else:
            errors.append(f'{rel(root, path)}:{lineno}: record is not a JSON object')
    return records


def _strip_inline_comment(val: str) -> str:
    """Drop a ' #...' inline comment (YAML-ish), preserving '#' inside quotes."""
    in_s = in_d = False
    for i, ch in enumerate(val):
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s:
            in_d = not in_d
        elif ch == '#' and not in_s and not in_d and (i == 0 or val[i - 1] in ' \t'):
            return val[:i]
    return val


def manifest_fields(path: Path) -> Dict[str, Any]:
    """Extract status/authority fields at ANY indentation, stripping inline
    comments. The prior parser skipped indented lines and kept inline comments,
    so `metadata:\\n  status: active` and `status: active # x` both read as
    unset (review finding HIGH manifest-nesting)."""
    data: Dict[str, Any] = {'all_statuses': []}
    for line in read(path).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or ':' not in stripped:
            continue
        key, val = stripped.split(':', 1)
        key = key.strip()
        val = _strip_inline_comment(val).strip().strip('\'"')
        if key == 'adapter_id':
            data['adapter_id'] = val
        elif key == 'status':
            data['all_statuses'].append(val.lower())
        elif key in ('promotion_authority', 'external_action_authority'):
            data[key] = val.lower() in ('true', 'yes', '1')
    return data


def check_manifests(root: Path, errors: List[str], warnings: List[str]) -> List[str]:
    """Restored from validator v1: adapter manifests must be proposed-only
    unless allowlisted. Deployments with no manifests directory skip cleanly."""
    manifests_dir = root / '.procheiron' / 'manifests'
    observed: List[str] = []
    if not manifests_dir.is_dir():
        return observed
    yaml_files = sorted(manifests_dir.glob('*.yaml'))
    if not yaml_files:
        return observed

    allowlist: set = set()
    allowlist_path = manifests_dir / 'active_manifest_allowlist.txt'
    if allowlist_path.is_file():
        allowlist = {ln.strip() for ln in read(allowlist_path).splitlines()
                     if ln.strip() and not ln.strip().startswith('#')}

    for path in yaml_files:
        fields = manifest_fields(path)
        statuses = fields.get('all_statuses', [])
        is_proposed_name = path.name.endswith('.proposed.yaml')
        looks_active = ('active' in statuses or '.active.' in path.name
                        or path.name.endswith('.active.yaml'))
        allowlisted = rel(root, path) in allowlist or path.name in allowlist
        observed.append(f'{rel(root, path)}:status={",".join(statuses) or "<unset>"}')
        if is_proposed_name and 'active' in statuses:
            errors.append(f'manifest declares active inside a .proposed.yaml: {rel(root, path)}')
        if not is_proposed_name and looks_active and not allowlisted:
            errors.append(f'active adapter manifest without allowlist: {rel(root, path)}')
        # An authority-granting manifest must never be live unless explicitly
        # allowlisted, regardless of how its status line is dressed up.
        if (fields.get('promotion_authority') or fields.get('external_action_authority')) and not allowlisted:
            errors.append(f'manifest grants promotion/external authority without allowlist: {rel(root, path)} '
                          f'(promotion={fields.get("promotion_authority", False)}, '
                          f'external={fields.get("external_action_authority", False)})')
        if not is_proposed_name and not looks_active:
            warnings.append(f'manifest is neither .proposed.yaml nor allowlisted-active: {rel(root, path)}')
    return observed


def validate_memory_records(cfg: Any, lint: Dict[str, Any], errors: List[str],
                            warnings: List[str]) -> Dict[str, Any]:
    """Roadmap item 1.1: the memory-record contract as code."""
    root = cfg.root
    memory = cfg.path('memory')
    index = memory / 'index'
    memories_path = index / 'memories.jsonl'
    audit_path = index / 'audit.jsonl'
    supersessions_path = index / 'supersessions.jsonl'
    adapters_path = index / 'adapters.jsonl'

    summary: Dict[str, Any] = {'records': 0, 'by_status': {}, 'checked': False}
    if not memories_path.is_file():
        errors.append(f'missing memory index: {rel(root, memories_path)}')
        return summary
    if not audit_path.is_file():
        errors.append(f'missing audit index: {rel(root, audit_path)}')
        return summary
    summary['checked'] = True

    memories = parse_jsonl(memories_path, errors, root)
    audit_events = parse_jsonl(audit_path, errors, root)
    supersessions = parse_jsonl(supersessions_path, errors, root)
    adapters = parse_jsonl(adapters_path, errors, root)

    known_actors = set(lint.get('known_actors', []))
    for _, adapter in adapters:
        adapter_id = str(adapter.get('adapter_id', '')).strip()
        if adapter_id:
            known_actors.add(adapter_id)
    actor_groups = [set(group) for group in lint.get('known_actor_groups', []) if isinstance(group, list)]

    def same_group(a: str, b: str) -> bool:
        return any(a in g and b in g for g in actor_groups)

    # --- tamper-evident audit chain (opt-in: lint `verify_audit_chain`) ---
    # Verifies the append-only log was not edited/reordered/deleted after the fact.
    if lint.get('verify_audit_chain', False):
        from . import chain as _chain
        for e in _chain.verify_chain([ev for _, ev in audit_events]):
            errors.append(f'audit chain: {e}')

    # --- cryptographic authorship (opt-in: lint `verify_signatures`) ---
    # Each signed event's `sig` must verify its `entry_hash` against the actor's
    # registered ed25519 public key. A verification that cannot RUN (crypto not
    # installed) is an error, never a silent pass.
    actor_keys = lint.get('known_actor_keys', {}) if isinstance(lint.get('known_actor_keys'), dict) else {}
    if lint.get('verify_signatures', False):
        from . import signing as _signing
        from . import chain as _chain
        require_sig = bool(lint.get('require_signatures', False))
        if not _signing.available():
            errors.append('verify_signatures is on but the `cryptography` package is not installed '
                          '(pip install "procheiron[crypto]") — refusing to pass unverifiable signatures')
        else:
            for lineno, ev in audit_events:
                sig = ev.get('sig')
                actor = str(ev.get('actor') or '')
                key_id = ev.get('sig_key_id')
                # sig_key_id is unauthenticated (hash-excluded) — it must not name a
                # different signer than the actor whose key is actually checked.
                if key_id is not None and str(key_id) != actor:
                    errors.append(f'audit event line {lineno}: sig_key_id {str(key_id)!r} != actor {actor!r} '
                                  f'(the signer identity must be the acting actor)')
                if not sig:
                    # An actor with a REGISTERED key is declared to sign; an unsigned
                    # event from them is a stripped/forged entry, not an opt-out — so
                    # `verify_signatures` alone (no require_signatures) still can't be
                    # bypassed by dropping the sig. require_signatures additionally
                    # demands a signature from every actor, keyed or not.
                    if actor in actor_keys:
                        errors.append(f'audit event line {lineno}: actor {actor!r} has a registered signing key '
                                      f'but this event is unsigned (signature stripped or never applied)')
                    elif require_sig:
                        errors.append(f'audit event line {lineno}: missing required signature (actor {actor!r})')
                    continue
                pub = actor_keys.get(actor)
                if not pub:
                    errors.append(f'audit event line {lineno}: signed by actor {actor!r} with no registered '
                                  f'public key (known_actor_keys)')
                    continue
                # Verify over the entry_hash RECOMPUTED from content, not the stored one:
                # a stored entry_hash is attacker-controlled, so signing it would bind
                # nothing when verify_audit_chain is off. Recomputing ties the signature
                # to the actual event body independently of the chain check.
                recomputed = _chain.entry_hash(str(ev.get('prev_hash') or _chain.GENESIS), ev)
                if not _signing.verify(str(pub), recomputed, str(sig)):
                    errors.append(f'audit event line {lineno}: signature does not verify for actor {actor!r} '
                                  f'(forged, wrong key, or content altered)')

    # --- external head anchor (opt-in: --expect-head) ---
    # verify_chain checks internal continuity only; a writer can rebuild the whole
    # chain from GENESIS and it stays self-consistent. An externally-anchored head
    # (git-pinned digest, printed value) is the ONLY thing that detects a full
    # rechain — this makes that anchor a machine-checked input, not just prose.
    expect_head = lint.get('_expect_head')
    if expect_head:
        from . import chain as _chain
        actual_head = _chain.head([ev for _, ev in audit_events])
        if str(expect_head) != actual_head:
            errors.append(f'audit chain head {actual_head[:12]}… != expected {str(expect_head)[:12]}… '
                          f'(the log was rebuilt/rewritten, or the anchor is stale)')

    promotion_events: Dict[str, List[Dict[str, Any]]] = {}
    for _, event in audit_events:
        action = str(event.get('action') or event.get('event_type') or '')
        memory_id = str(event.get('memory_id') or '')
        if action in PROMOTION_EVENT_ACTIONS and memory_id:
            promotion_events.setdefault(memory_id, []).append(event)
    latest_trans = lifecycle.latest_transitions([event for _, event in audit_events])

    def event_supports(memory_id: str, created_by: str, reviewed_by: Any, want: set) -> bool:
        """A promotion event counts only if it independently corroborates the
        promotion: right target, status_after in the wanted set, actor is the
        reviewer (not the creator) and a known actor. This raises a naive forge
        from 'append one 2-field line' to 'forge a fully-consistent event whose
        actor is a registered reviewer' (review finding CRITICAL, within the
        honor-system model — true tamper-evidence is Phase 3)."""
        cby = lifecycle.norm_actor(created_by)
        rby = lifecycle.norm_actor(reviewed_by)
        for event in promotion_events.get(memory_id, []):
            status_after = str(event.get('status_after') or '')
            actor = event.get('actor')
            nactor = lifecycle.norm_actor(actor)
            if want and (not status_after or status_after not in want):
                continue  # a corroborating event MUST carry a wanted status_after
            if nactor == cby:
                continue  # promoter cannot be the creator
            if reviewed_by is not None and nactor != rby:
                continue  # the event's actor must be the named reviewer
            if known_actors and isinstance(actor, str) and actor not in known_actors:
                continue  # promoter must be a registered actor
            return True
        return False

    supersession_pairs = set()
    for lineno, entry in supersessions:
        old_id = str(entry.get('old_id') or entry.get('superseded_id') or '')
        new_id = str(entry.get('new_id') or entry.get('superseding_id') or '')
        if not old_id or not new_id:
            errors.append(f'{rel(root, supersessions_path)}:{lineno}: entry missing old_id/new_id')
            continue
        supersession_pairs.add((old_id, new_id))

    seen_ids: Dict[str, int] = {}
    all_ids = {str(record.get('id') or '') for _, record in memories}
    laundering_suspects: List[str] = []
    forbid_abs_paths = bool(lint.get('forbid_absolute_paths_in_memory_records', False))

    for lineno, record in memories:
        summary['records'] += 1
        loc = f'{rel(root, memories_path)}:{lineno}'
        rid = str(record.get('id') or '')
        status = str(record.get('status') or '')
        summary['by_status'][status] = summary['by_status'].get(status, 0) + 1

        for field in REQUIRED_RECORD_FIELDS:
            if record.get(field) in (None, '', []):
                errors.append(f'{loc}: missing required field {field} (id={rid or "<none>"})')
        if rid:
            if rid in seen_ids:
                errors.append(f'{loc}: duplicate memory id {rid} (first at line {seen_ids[rid]})')
            seen_ids[rid] = lineno

        if status and status not in MEMORY_STATUSES:
            errors.append(f'{loc}: invalid status {status!r} ({rid})')
        rtype = str(record.get('type') or '')
        if rtype and rtype not in MEMORY_TYPES:
            warnings.append(f'{loc}: non-standard type {rtype!r} ({rid})')
        scope = str(record.get('scope') or '')
        if scope and scope not in MEMORY_SCOPES:
            warnings.append(f'{loc}: non-standard scope {scope!r} ({rid})')
        sensitivity = record.get('sensitivity')
        if sensitivity is not None and sensitivity not in SENSITIVITY_LEVELS:
            errors.append(f'{loc}: invalid sensitivity {sensitivity!r} ({rid})')
        visibility = record.get('visibility')
        if visibility is not None and visibility not in VISIBILITY_LEVELS:
            errors.append(f'{loc}: invalid visibility {visibility!r} ({rid})')

        confidence = record.get('confidence')
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not (0.0 <= float(confidence) <= 1.0):
            errors.append(f'{loc}: confidence must be numeric in [0,1] ({rid})')

        source_paths = record.get('source_paths') or []
        source_ids = record.get('source_ids') or []
        notes = str(record.get('notes') or '')
        write_policy = str(record.get('write_policy') or '')
        if not source_paths and not source_ids:
            if 'bootstrap' in (notes + ' ' + write_policy).lower():
                warnings.append(f'{loc}: provenance-free bootstrap record ({rid})')
            else:
                errors.append(f'{loc}: no source_paths or source_ids ({rid}) — durable memory requires provenance')

        if forbid_abs_paths:
            for sp in source_paths:
                if isinstance(sp, str) and ABSOLUTE_RECORD_PATH_RE.match(sp):
                    errors.append(f'{loc}: machine-absolute source_path {sp!r} ({rid}) — use root-relative or {{paths.*}} token form')

        created_by = str(record.get('created_by') or '')
        reviewed_by = record.get('reviewed_by')
        if reviewed_by is not None and not isinstance(reviewed_by, str):
            errors.append(f'{loc}: reviewed_by must be a string, got {type(reviewed_by).__name__} ({rid})')
        if known_actors and created_by and created_by not in known_actors:
            warnings.append(f'{loc}: created_by {created_by!r} not in known actors ({rid})')
        if known_actors and isinstance(reviewed_by, str) and reviewed_by and reviewed_by not in known_actors:
            warnings.append(f'{loc}: reviewed_by {reviewed_by!r} not in known actors ({rid})')

        if status in {'active', 'validated'}:
            if status == 'active' and write_policy == 'proposal_only':
                errors.append(f'{loc}: write_policy proposal_only record is active ({rid}) — proposals may not self-activate (SCHEMA rule 9); promotion must set approved_canonical')
            trust_issue = lifecycle.trust_error(record, latest_trans.get(rid))
            if trust_issue:
                errors.append(f'{loc}: {status} record failed trust check: {trust_issue} ({rid})')
            if reviewed_by and lifecycle.norm_actor(reviewed_by) != lifecycle.norm_actor(created_by) and same_group(created_by, str(reviewed_by)):
                laundering_suspects.append(rid)
            if known_actors and isinstance(reviewed_by, str) and reviewed_by and reviewed_by not in known_actors:
                errors.append(f'{loc}: {status} record reviewer {reviewed_by!r} is not a registered actor ({rid})')
            if not record.get('reviewed_at'):
                errors.append(f'{loc}: {status} record has no reviewed_at ({rid})')
            want = {'active', 'validated'} if status == 'active' else {'validated', 'active'}
            if rid and not event_supports(rid, created_by, reviewed_by, want):
                errors.append(f'{loc}: {status} record has no corroborating promotion audit event '
                              f'(need action memory_promoted/validated for {rid}, status_after {status}, '
                              f'actor=reviewer≠creator and a known actor) — forged/hand-flipped record')

        supersedes = record.get('supersedes') or []
        if supersedes:
            for target in supersedes:
                target = str(target)
                if target not in all_ids:
                    errors.append(f'{loc}: supersedes unknown record {target} ({rid})')
                elif (target, rid) not in supersession_pairs:
                    errors.append(f'{loc}: supersedes {target} but supersessions.jsonl has no matching entry ({rid})')
        else:
            prose = f'{record.get("statement") or ""} {notes}'
            match = PROSE_SUPERSESSION_RE.search(prose)
            # Skip negated/hypothetical claims ("does NOT supersede mem_x"),
            # scoping the negation to the verb's own clause (is_negated_claim).
            if match and not is_negated_claim(prose, match.start(), match.end()):
                errors.append(f'{loc}: prose supersession claim without structured supersedes[] ({rid}): {match.group(0)[:80]!r}')

        if status == 'superseded':
            if rid and not any(old == rid for old, _ in supersession_pairs):
                errors.append(f'{loc}: superseded record has no supersessions.jsonl lineage entry ({rid})')

    if laundering_suspects:
        warnings.append(
            'same-harness review (authority-laundering risk, profile actor-group match) on '
            f'{len(laundering_suspects)} active/validated record(s): {", ".join(laundering_suspects[:4])}'
            + ('…' if len(laundering_suspects) > 4 else '')
        )
    return summary


def validate(args: argparse.Namespace) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    cfg = load_config(explicit_root=args.root)
    profile = args.profile or cfg.profile
    lint, lint_source = load_profile_lint(cfg.root, profile, args.profiles_dir)
    check_lint_schema(lint, errors)

    # A named profile with no lint file silently lost all its checks before
    # (review finding HIGH silent-policy-evaporation). Surface it loudly: a
    # warning always, and an error for a non-core named profile in strict mode.
    if lint_source is None and profile not in _CORE_ONLY_PROFILES:
        msg = (f'no lint file found for profile {profile!r}; running core-only — '
               'all profile-specific checks (welds, literals, record validation) are OFF')
        if args.strict_lint_presence:
            errors.append(msg)
        else:
            warnings.append(msg)

    if lint.get('expected_profile') and lint['expected_profile'] != profile:
        errors.append(f'profile lint expected {lint["expected_profile"]}, got {profile}')

    for key in ['console', 'memory', 'sources']:
        try:
            cfg.path(key)
        except ResolveError as exc:
            errors.append(str(exc))
    if str(cfg.raw.get('profile', '')).strip() != profile and not args.profile:
        errors.append('config profile is empty or inconsistent')

    console = cfg.path('console')
    memory = cfg.path('memory')
    sources = cfg.path('sources')

    present_console: List[str] = []
    present_memory: List[str] = []
    required_console = REQUIRED_CONSOLE + [
        name for name in lint.get('required_console_extra', []) if name not in REQUIRED_CONSOLE
    ]
    for name in required_console:
        path = console / name
        if path.is_file():
            present_console.append(rel(cfg.root, path))
        else:
            errors.append(f'missing console file: {rel(cfg.root, path)}')
    for name in REQUIRED_MEMORY:
        path = memory / name
        if path.is_file():
            present_memory.append(rel(cfg.root, path))
        else:
            errors.append(f'missing memory file: {rel(cfg.root, path)}')
    if not sources.is_dir():
        errors.append(f'missing sources directory: {rel(cfg.root, sources)}')

    doctrine_hits: List[str] = []
    core_text_parts: List[str] = []
    for path in [console / 'PROCHEIRON.md', console / 'PRECEDENCE.md', console / 'SOURCE_OF_TRUTH.md']:
        if path.is_file():
            core_text_parts.append(read(path).lower())
    core_text = '\n'.join(core_text_parts)
    for label, terms in CORE_DOCTRINE.items():
        if all(t.lower() in core_text for t in terms):
            doctrine_hits.append(label)
        else:
            errors.append(f'missing core doctrine: {label}')

    # Legacy required/forbidden-literal checks must see ALL Core docs, not just
    # the 3 doctrine docs — a literal in AGENT_BOOT/REGISTRY/SELF_ACTION_POLICY
    # previously evaded portable-strict (review finding MEDIUM literal-scope).
    literal_scan_docs = ['PROCHEIRON.md', 'PRECEDENCE.md', 'SOURCE_OF_TRUTH.md',
                         'AGENT_BOOT.md', 'AGENT_REGISTRY.md', 'SELF_ACTION_POLICY.md']
    literal_text_parts: List[str] = []
    for name in literal_scan_docs:
        path = console / name
        if path.is_file():
            literal_text_parts.append(read(path).lower())
    literal_text = '\n'.join(literal_text_parts)

    secret_findings: List[str] = []
    # No file-size cap: scan_file_for_secrets streams line-by-line with a per-line
    # cap, so a key padded past any size is still caught (a >500 KB cap here was
    # the caller-side hole the function's own no-cap fix could not close). sources/
    # is provenance raw-drop — credentials are never legitimate there either.
    for root_dir in [console, memory, sources]:
        if not root_dir.exists():
            continue
        for path in root_dir.rglob('*'):
            if path.is_file():
                secret_findings.extend(scan_file_for_secrets(cfg.root, path))
    if secret_findings:
        errors.extend(f'secret-pattern finding: {f}' for f in secret_findings)

    absolute_findings: List[str] = []
    if lint.get('forbid_absolute_paths_in_core', False):
        for root_dir in [console, memory]:
            if not root_dir.exists():
                continue
            for path in root_dir.rglob('*.md'):
                for lineno, line in enumerate(read(path).splitlines(), 1):
                    if ABSOLUTE_PATH_RE.search(line):
                        absolute_findings.append(f'{rel(cfg.root, path)}:{lineno}')
        if absolute_findings:
            errors.extend(f'absolute path in core doc: {f}' for f in absolute_findings)

    # v2.1 — per-file Core-doc lint scoping (roadmap 0.6): the parameterized Core
    # set must stay free of machine-absolute paths and deployment literals even
    # when live deployment ledgers (DECISIONS/BLOCKERS/...) legitimately carry both.
    core_docs = [name for name in lint.get('core_docs', [])]
    core_doc_findings: List[str] = []
    if core_docs:
        forbid_abs = bool(lint.get('forbid_absolute_paths_in_core_docs', False))
        # Skip empty/whitespace literals — "" matches every line (review finding LOW).
        forbidden_literals = [str(x) for x in lint.get('forbidden_core_doc_literals', []) if str(x).strip()]
        dropped = len(lint.get('forbidden_core_doc_literals', [])) - len(forbidden_literals)
        if dropped:
            warnings.append(f'ignored {dropped} empty forbidden_core_doc_literals entr(y/ies)')
        for name in core_docs:
            path = console / name
            if not path.is_file():
                continue  # absence is already reported by the required-file check
            for lineno, line in enumerate(read(path).splitlines(), 1):
                if forbid_abs and ABSOLUTE_PATH_RE.search(line):
                    core_doc_findings.append(f'{rel(cfg.root, path)}:{lineno}:absolute-path')
                # Homoglyph guard: a non-ASCII letter in an (ASCII-prose) Core doc
                # is a literal-scan evasion vector (review finding HIGH homoglyph).
                if has_non_ascii_letter(line):
                    warnings.append(f'non-ASCII letter in Core doc {rel(cfg.root, path)}:{lineno} '
                                    '(homoglyph-smuggling risk; verify deployment names are not disguised)')
                low = normalize_for_scan(line).lower()
                raw_low = line.lower()
                for literal in forbidden_literals:
                    lit = literal.lower()
                    if lit in raw_low or lit in low:
                        core_doc_findings.append(f'{rel(cfg.root, path)}:{lineno}:literal:{literal}')
        if core_doc_findings:
            errors.extend(f'deployment weld in Core doc: {f}' for f in core_doc_findings)

    deprecated_observations: List[str] = []
    for item in lint.get('deprecated_or_duplicate_roots', []):
        path = cfg.root / item
        deprecated_observations.append(f'{item}:{"present" if path.exists() else "absent"}')

    for literal in lint.get('required_literals', []):
        if str(literal).strip() and str(literal).lower() not in literal_text:
            errors.append(f'profile-required literal missing: {literal}')

    for literal in lint.get('forbidden_core_literals', []):
        if str(literal).strip() and str(literal).lower() in literal_text:
            errors.append(f'profile-forbidden literal present in core text: {literal}')

    manifest_observations = check_manifests(cfg.root, errors, warnings)

    records_enabled = bool(lint.get('validate_memory_records', False))
    if args.records:
        records_enabled = True
    if args.no_records:
        records_enabled = False
    # External anchors (opt-in): a downgraded/flipped lint and a full audit-chain
    # rewrite are both invisible to internal checks — pin them from outside CI/git.
    if getattr(args, 'expect_lint', None):
        actual_fp = _lint_fingerprint(lint)
        if actual_fp != args.expect_lint:
            errors.append(f'lint fingerprint {actual_fp} != expected {args.expect_lint} '
                          '(enforcement-bearing lint keys were changed — possible downgrade)')
    if getattr(args, 'expect_head', None):
        lint = {**lint, '_expect_head': args.expect_head}

    record_summary: Dict[str, Any] = {'checked': False}
    if records_enabled:
        record_summary = validate_memory_records(cfg, lint, errors, warnings)

    # A2-37 dangling-token closure (Phase-3 B1 additive adoption, 2026-06-12):
    # every {paths.*} a parameterized Core/profile doc references must be defined
    # in config. The validator already fails closed on the tokens it resolves; this
    # generalizes it to the documented doc-set union. Degrades to a skip if the
    # schema data is absent so it can never crash the governance gate. NOTE: the
    # record-loop schema swap (staged_diffs/validator_consumes_schemas.staged.md)
    # is intentionally DEFERRED — that behavior-identical refactor was never proven
    # by an equivalence harness and adds nothing the trial measures.
    _reqtok_path = HERE.parent / 'data' / 'schemas' / 'required_tokens.json'
    if _reqtok_path.is_file():
        try:
            _reqtok = json.loads(_reqtok_path.read_text())
            _defined = set(cfg.paths.keys())
            _needed = set()
            for _tok in (_reqtok['doc_sets']['core']['union']
                         + _reqtok['doc_sets']['profile']['docs']['profile.md']):
                if _tok != '{root}':
                    _needed.add(_tok[len('{paths.'):-1])
            for _missing in sorted(_needed - _defined):
                errors.append(f'dangling token {{paths.{_missing}}} referenced by a '
                              f'Core/profile doc but not defined in {cfg.config_path}')
        except (KeyError, ValueError) as _exc:
            warnings.append(f'token-closure check skipped: malformed required_tokens.json ({_exc})')

    return {
        'status': 'FAIL' if errors else ('PASS_WITH_WARNINGS' if warnings else 'PASS'),
        'root': str(cfg.root),
        'config': str(cfg.config_path),
        'config_version': cfg.version,
        'profile': profile,
        'config_was_read': True,
        'lint_source': lint_source,
        'lint_fingerprint': _lint_fingerprint(lint),
        'paths': {k: str(v) for k, v in cfg.paths.items()},
        'present_console': present_console,
        'present_memory': present_memory,
        'doctrine_hits': doctrine_hits,
        'profile_lint': lint.get('profile', profile),
        'deprecated_observations': deprecated_observations,
        'absolute_findings': absolute_findings,
        'core_doc_findings': core_doc_findings,
        'manifest_observations': manifest_observations,
        'memory_records': record_summary,
        'secret_findings': secret_findings,
        'warnings': warnings,
        'errors': errors,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='Validate Procheiron using config-driven paths')
    parser.add_argument('--root', help='explicit fallback root')
    parser.add_argument('--profile', help='override profile name for lint lookup')
    parser.add_argument('--profiles-dir', help='directory containing <profile>/lint.json')
    parser.add_argument('--records', action='store_true',
                        help='force memory-record validation regardless of profile lint')
    parser.add_argument('--no-records', action='store_true',
                        help='skip memory-record validation regardless of profile lint')
    parser.add_argument('--strict-lint-presence', action='store_true',
                        help='FAIL (not warn) when a named profile has no lint file')
    parser.add_argument('--expect-head',
                        help='hex the audit-chain head MUST equal (external anchor; catches a full rechain)')
    parser.add_argument('--expect-lint',
                        help='lint fingerprint the profile MUST match (catches a downgraded/flipped lint)')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = validate(args)
    except (ResolveError, OSError, json.JSONDecodeError, TypeError, ValueError, KeyError) as exc:
        result = {'status': 'FAIL', 'errors': [f'{type(exc).__name__}: {exc}']}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Procheiron2 validation: {result['status']}")
        for error in result.get('errors', []):
            print(f'ERROR: {error}')
        for warning in result.get('warnings', []):
            print(f'WARNING: {warning}')
    return 0 if result.get('status') in {'PASS', 'PASS_WITH_WARNINGS'} else 1


def run(root: str, records: bool = True, profiles_dir: Optional[str] = None) -> Dict[str, Any]:
    """Thin callable wrapper over validate() for the CLI and library consumers."""
    args = argparse.Namespace(root=root, profile=None, profiles_dir=profiles_dir,
                              records=records, no_records=False,
                              strict_lint_presence=False, json=False)
    return validate(args)


if __name__ == '__main__':
    raise SystemExit(main())
