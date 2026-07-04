# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/)
with the project's own rule that numbers are earned by conformance, not declared (see
`CONTRIBUTING.md`).

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
