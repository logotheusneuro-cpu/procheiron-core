# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/)
with the project's own rule that numbers are earned by conformance, not declared (see
`CONTRIBUTING.md`).

## [Unreleased]

### Fixed (security)
- **Full validator derives trust from the same canonical lifecycle logic as MCP.** The full
  validator's inline latest-transition map tracked status only — an older valid promotion could
  hide a later same-status transition performed by an actor who is not the record's named
  reviewer (MCP would distrust the record while `validate` passed it). Both surfaces now use
  `lifecycle.trust_error()`; a forged latest promotion must also match `reviewed_by`, not just
  any actor. Adversarial regression added to `check_trust_boundary` (verified to fail on the
  previous code). Note: exploiting this required the disclosed append-forgery residual — this
  narrows that residual, it does not close it; signing does.
- **`lifecycle.latest_transitions` honors legacy `event_type`** — MCP and the validator no
  longer render different trust verdicts on logs using the legacy field name.

### Changed
- Duplicate identity/transition logic removed from `validate.py` (single `norm_actor`,
  single trust decision; net −5 lines).

## [0.2.4] — 2026-07-10

Second trust-boundary release. A re-review of 0.2.3 showed the first round was cosmetic — the
"trusted read" filtered a mutable field, and MCP promotion took the reviewer as a free string.
These are the real fixes; two of the "critical" gaps are now closed with an adversarial guard.

### Fixed (security)
- **MCP promotion binds identity to the authenticated actor.** `memory.promote` took
  `reviewer`/`approver` as arguments, so a client bound as `alice` could promote alice's own
  record by claiming `reviewer:"bob"`. The reviewer/authorizer is now the bound `--actor`; a
  differing argument is rejected. "The agent that wrote a memory cannot approve it" is true again.
- **Trusted reads are derived from audit evidence, not the `status` field.** Flipping a candidate
  to `active` in place used to make it served by default. `memory.search` now serves a record on
  the default path only if its status is backed by the audit log's latest transition; a forged
  `active` is hidden. `memory.get` returns an explicit `trusted` boolean + `trust_reason`.
- **Latest-transition lifecycle check in both validators.** A stale promotion no longer vouches
  for a record that was later archived/superseded and flipped back to `active`.
- **Writers preflight the hash-chain helper and fail closed** — no more appending an unchained
  event and reporting success. Nothing is written when the helper is unavailable.
- **`init` checks every audit event at the configured path** before enabling the chain lint (a
  mixed chained/unchained log is detected); **plain `--force` no longer destroys data** — emptying
  the indexes needs an explicit `--reset-data`.
- **Strict boolean** on `include_untrusted` — a string like `"false"` no longer coerces to truthy.

### Added
- `lifecycle.py`: the single source of "is this record backed by independent-review evidence",
  shared by the validator and the MCP read path.
- `check_trust_boundary` conformance guard: forges an `active` record with no promotion evidence
  and asserts it is hidden from default reads and that MCP promotion binds the reviewer. 20/20.

### Honesty
- `CLAIMS.md` corrected (it lagged at 0.2.2) and given an explicit "append-forgery needs signing"
  residual; README comparison-table footnote and FAQ made precise; `INSTALL_FOR_AGENTS.md` and the
  `init/` description no longer overclaim.

## [0.2.3] — 2026-07-10

Trust-boundary release. An external independent audit found that the enforcement had real gaps
behind the working happy path; this closes them.

### Fixed (security / correctness)
- **Trusted-consumption boundary on reads.** The MCP `memory.search` tool returned unreviewed
  `candidate` records by default — an agent could consume exactly what the review gate is meant
  to quarantine. It now returns only `active`/`validated` records by default; candidates require
  an explicit `status` or `include_untrusted=true`.
- **Minimal validator enforces independent review properly.** It compared actors with raw `==`
  (so `BOB` cleared review against `bob`) and only checked that *a* promotion event existed, not
  that its actor was the reviewer. It now NFKC+casefolds identities and verifies the promoting
  actor is neither the creator nor a mismatch for `reviewed_by` — matching the full tier.
- **`procheiron mcp` accepts a positional root** (`procheiron mcp ./commons`), matching `init`
  and `validate`; the MCP server reports the real package version (was hardcoded `0.1.0`).
- **`init` no longer changes a legacy deployment's verdict.** Re-running `procheiron init` on a
  commons whose audit log is not hash-chained refuses to add the `verify_audit_chain` lint
  (which would flip its result); it prints a migration note instead.
- Scaffolded writers no longer fall back **silently** to an unchained audit append when the
  chain helper is missing — they warn loudly (a missing stdlib helper means a broken install).

### Changed / removed
- Removed the broken standalone `init/procheiron_init.py` (it could not locate the adopter
  files, scaffolded an incomplete tree, and printed a validate command for a file it never
  created). `procheiron init` is the one scaffold path; `PORTING_GUIDE.md` updated to match.
- README honesty pass: "adds no memory engine of its own" replaces the overclaimed "stores
  nothing"; the how-it-works note is precise that tail truncation is caught only with an
  external anchor; the comparison table no longer wins every cell (git ties on tamper-evidence)
  and its setup column discloses the anchor + key-custody cost.
- `CLAIMS.md` refreshed to 0.2.2/0.2.3 with the two fixes above and a tail-truncation caveat.

### Added
- Conformance: MCP smoke asserts the trusted-by-default read boundary; the pip-journey guard
  asserts a case-variant self-review is refused. 19/19 base.

## [0.2.2] — 2026-07-09

First-run integrity release: a freshly scaffolded commons now delivers what the README
promises, from a plain pip install, on Linux, macOS, and Windows.

### Fixed
- A commons scaffolded by `procheiron init` now works from a plain pip install: the adopter
  tools (`memory_propose.py`, `memory_promote.py`) fall back to the installed `procheiron`
  package when a deployment ships no pinned `.procheiron/lib` (a deployment's own lib still
  wins when present).
- `memory_propose.py` hash-chains its audit event exactly like `memory_promote.py`, so a
  fresh commons is chained from genesis instead of starting with an unchained event.
- Tamper-evident by default, for real: `procheiron init` scaffolds a lint profile with
  `verify_audit_chain: true`, and minimal-tier `procheiron validate` honors it — rewriting a
  past audit event in a fresh scaffold now fails validation (it silently passed before).
- Conformance subprocesses use `sys.executable` instead of a hardcoded `python3`, and the
  default read-log path is computed portably.

### Added
- Conformance guard for the pip-only first session: init → propose → self-review refused →
  independent promote → validate PASS → tamper → caught. 19/19 base.
- CI runs the stdlib conformance matrix on Windows and macOS as well as Linux.
- Issue templates (bug report, deployment report) and GitHub Discussions.
- `procheiron init` prints a propose/promote quickstart with the independence rule.

## [0.2.1] — 2026-07-09

Documentation and fixture-hygiene release; no behavior changes.

### Changed
- README rewritten and restructured: plainer language, no product comparisons, the trust model
  explained in one place; a real tamper-detection demo up top, and install/commands/FAQ sections.
- Brand identity in `assets/`: the hand-and-flame coin mark, a Marcus Aurelius hero portrait,
  and a three-scene lifecycle illustration (write → independent review → chain → tamper caught),
  plus favicon and social-preview card.
- README images and repo-file links use absolute URLs so the PyPI project page renders them.
- CLAIMS.md refreshed to match the published state: 0.2.0 on PyPI, and the Rego policy's
  `opa test` CI job confirmed passing (11/11) — moved from caveat to proven.
- Conformance fixtures resynced to the adopter template (the chained-audit/refuse upgrade had
  drifted) and a tool-currency guard added: fixture copies of `memory_promote.py` must stay
  byte-identical to the packaged adopter reference. Now 16/16 base, 18/18 with the crypto extra.

## [0.2.0] — 2026-07-04

The "make trust real" release: closes the honor-system gap by making the audit trail
tamper-evident by default and cryptographically signable by choice.

### Added
- **Tamper-evident audit chain** (`chain.py`, pure stdlib BLAKE2b): every audit event carries
  `prev_hash`/`entry_hash`; silent edits, reorders, and deletions break the chain.
- **Optional ed25519 signing** (`signing.py`, `pip install "procheiron[crypto]"`): signatures
  bind the *recomputed* entry hash; a verification that cannot run is a hard error.
- Validator gates: `verify_audit_chain`, `verify_signatures`, `require_signatures`, and a
  `known_actor_keys` registry — an unsigned event from a keyed actor is **rejected**
  (signature stripping fails, it does not pass).
- External anchoring: `validate --expect-head <hex>` detects a full chain rewrite;
  `--expect-lint <fp>` catches a lint-profile downgrade.
- Conformance: signed-chain and forged-signature fixtures (crypto), chain-break fixture
  (stdlib). 14/14 base with zero dependencies; signature checks self-skip cleanly without the
  crypto extra and run for real with it.
- CI: stdlib matrix (3.9/3.12) + crypto job + `opa test` job — the Rego reference policy
  executes in CI rather than merely shipping.
- Package/version consistency guard.

### Changed
- Threat model documented up front (README + `CLAIMS.md`): tamper-*evidence* vs
  tamper-*prevention*, the single-trust-domain residual, and the two conditions
  (external head anchor + out-of-scope key custody) under which signing stops an insider.
- Hardened after a 5-attack adversarial review: signature-strip rejected, `sig_key_id`
  must match the actor, signatures verify over recomputed (not stored) hashes.

## [0.1.0] — 2026-06-25

Initial public package.

### Added
- Spec v0.1 (`spec/`): governance, memory commons, control plane, normative conformance
  MUST-list, Core/Profile boundary.
- Conformance suite + fixtures: `generic-vault/` (a complete fictional deployment) and
  `minimal-vault/` (5-file minimal adopter), plus negative fixtures.
- Stdlib validator, policy check (with a Rego reference policy), CLI, MCP server,
  `procheiron init` scaffolder, porting guide.
- Zero runtime dependencies.
