# Procheiron — Claims Ledger (proven vs. not proven)

Procheiron is a provenance and trust layer, so this ledger holds our own claims to the same
standard we ask of any memory: a claim counts as proven only with cited, reproducible evidence.
Everything else gets labeled for what it is. One rule governs the whole file: no "production-ready"
or "production-replicable" claim until a second real deployment passes conformance.

- Last updated: 2026-07-10
- Published package: `procheiron` **0.2.2** (PyPI, sdist + wheel) — tamper-evident hash-chained
  audit log plus optional ed25519 signing; 0.2.1/0.2.2 added the branded README, the pip-only
  first-run fixes, and cross-OS CI. 0.1.0 remains installable pinned but predates the chain.
  Rows below say which version each claim holds for. (An external independent audit on 2026-07-09
  drove the trusted-read and minimal-validator fixes below; those land in the next release.)

---

## ✅ Proven (verified, with evidence)

| Claim | Evidence | Where it holds |
| --- | --- | --- |
| Package is MIT, **zero runtime deps**, stdlib-only | `pyproject.toml` (`dependencies = []`); `pip install procheiron` verified | 0.1.0 (published) |
| CLI works: `version` / `init` / `validate` / `conformance` / `mcp` | `src/procheiron/cli.py`; verified end-to-end from a fresh-venv PyPI install (`init` + `validate` PASS) | 0.2.0 (published) |
| Conformance passes — **at fixture level** | `conformance/run_conformance.py` → **16/16 base (stdlib) + 18/18 with the `crypto` extra** (Meridian generic-vault + 5-file minimal + negatives incl. tilde-weld, chain-break, signed/forged/stripped signatures + doctrine-currency, version-consistency, and tool-currency guards) | 0.2.1 |
| Conformance runs the **one Core validator**, not a per-fixture copy | de-vendored: fixtures carry data only; `run_conformance.py` invokes `python3 -m procheiron.validate` | 0.2.0 (published) |
| Constitution is current **4.6 doctrine** (git → preservation-executor) | `SELF_ACTION_POLICY.md`; fixture copy byte-identical to live canon; doctrine-currency guard fails a stale doc | 0.2.0 (published; 0.1.0 ships the pre-4.6 fixture — see caveats) |
| **Rego policy executes in CI** and agrees with the stdlib backend | `.github/workflows/ci.yml` `policy-opa` job: `opa test` **11/11 PASS** (run 28715087170, 2026-07-04) | 0.2.0 (published) |
| `memory_promotion_gate` **enforces** independent review | `memory_promote.py`: refuses self-review (§8.7), same-actor-group laundering, active-without-authority; tested e2e | live deployment + package |
| The gate **durably records its blocks** | refusals append a schema-valid `promotion_refused` audit event (≠ `memory_promoted`/`memory_validated`, never false-corroborates); tested | live + package (0.1.1 staged) |
| MCP server is packaged + **deployment-portable** | `src/procheiron/mcp_server.py` (config-resolved paths, no hardcoded deployment paths); `conformance/test_mcp_smoke.py` passes against the generic fixture deployment | 0.1.1 staged |
| Lifecycle + provenance model | draft→candidate→validated→active→superseded/archived/disputed; `active` requires `reviewed_by ≠ created_by` + corroborating audit event; validator enforces | live + package |
| **Audit log is tamper-evident** (hash-chained) | `chain.py` (BLAKE2b, stdlib, zero-dep); the validator recomputes the chain when lint `verify_audit_chain` is on; conformance `chain-break` negative FAILS on a silently-edited event; the reference writer emits the chain (`chain.append_event`) | 0.2.0 package |
| **Optional ed25519 signing** of audit entries | `signing.py` (opt-in `procheiron[crypto]`); conformance proves a signed log verifies AND a forged signature is caught; a verification that cannot run (crypto absent + signatures required) is a hard error, never a silent pass | 0.2.0 package |

## ❌ Not proven / honest caveats (the load-bearing part)

| Claim status | Detail |
| --- | --- |
| **Production-replicability: NOT proven** | Conformance is **fixture-level only**. The "second deployment" (Meridian) is fictional, and the fixtures are home-team (same authors wrote the validator and the fixtures). A v1.0 / "production-replicable" claim requires a **real, independent second deployment** passing conformance. |
| **Single real deployment** | Procheiron currently governs exactly one system — the authors' own multi-agent deployment. The core promise ("a *different* agent can trust this memory") is exercised **internally** (an ingesting agent proposes → an independent agent promotes → consuming agents read → a human authorizes), not yet across independent organizations. |
| **9 of 10 gates are inert** | The constitution defines 10 gates; only `memory_promotion_gate` is implemented + enforced. The rest are "policy defines gates; it does not implement them." |
| **Pinned 0.1.0 is stale** | Installing `procheiron==0.1.0` gets the **pre-4.6 git-welded** fixture constitution and no tamper-evident chain. Fixed in 0.2.0 (the PyPI latest); 0.1.0 is kept only for pinned installs. |
| **MCP not armed for all agents** | Packaged + portable + armed for one session; broad per-agent `--allow-writes` rollout pending. |
| **Trust-loop longevity unproven** | A 30-day continuous trust-loop run (promotions + recorded blocks) is not yet complete. Checkpoint ~2026-07-26. |
| **Single-trust-domain limit (chain + signing)** | `verify_chain` checks only *internal* continuity, so a writer can rebuild the whole chain from GENESIS; and `known_actor_keys` (the public-key registry) lives in the same writable profile, so an insider who can write the audit log can also re-register fresh keys and re-sign the rewrite (red-team Attack #1, reproduced). Chain + signing therefore close the dual-write forgery **only with BOTH** (a) an externally-anchored head (`validate --expect-head <hex>`, git-pinned) **and** (b) the key registry out of the writer's write scope (separate OS user / HSM / Sigstore keyless). On one shared machine without those, you get tamper-**evidence** (detectable via the anchor), not tamper-**prevention**. Private keys on a shared filesystem are additionally only as strong as their file permissions. |
| **Crypto not yet in the live deployment** | The tamper-evident chain + optional signing are proven in the package + conformance; the authors' own live deployment has **not yet migrated** its audit log onto the chain (an available follow-up, kept separate to avoid disturbing a running system). |
| **Tail truncation needs the anchor** | Deleting the *newest* audit events is the one edit the hash chain alone cannot see (`chain.py` verifies internal continuity, which a truncated log still has). It is caught only with an externally-anchored head (`validate --expect-head <hex>`). Editing or reordering any existing event is caught by the chain unconditionally. |

## Fixed after the 2026-07-09 independent audit (in the next release, not yet on PyPI)

| Fix | What was wrong | Evidence |
| --- | --- | --- |
| **MCP reads are trusted-by-default** | `memory.search` with no `status` returned unreviewed `candidate` records — an agent could consume exactly what the review gate is meant to quarantine. Now returns only `active`/`validated` by default; candidates need an explicit `status` or `include_untrusted=true`. | `mcp_server.py` `TRUSTED_STATUSES`; conformance pip-journey asserts the default search hides a fresh candidate |
| **Minimal validator enforces independent review properly** | The minimal tier compared actors with raw `==` (so `BOB` passed review against `bob`) and only checked that *a* promotion event existed, not that its actor was the independent reviewer. Now NFKC+casefolds identities and checks the promoting actor is neither the creator nor a mismatch for `reviewed_by` — matching the full tier. | `validate_minimal.py` `_norm_actor`; conformance negative fixture for a case-variant self-review |

## Discipline

- A row moves from ❌ to ✅ **only** with cited, reproducible evidence.
- No "production-replicable" claim until a second real deployment passes conformance.
- If this ledger and a headline ever disagree, **this ledger wins** — it is the provenance system applied to itself.
