# Procheiron — Claims Ledger (proven vs. not proven)

Procheiron is a provenance and trust layer. This ledger holds **its own** claims to the
same standard it asks of any memory: a claim is **proven** only with cited, reproducible
evidence — everything else is labeled honestly. The governing rule: *no "production-ready"
or "production-replicable" claim until a second real deployment passes conformance.*

- Last updated: 2026-07-03
- Published package: `procheiron` **0.1.0** (PyPI). Current repo / **0.2.0 (staged, unpublished)** is ahead — 0.2.0 adds the tamper-evident hash-chained audit log + optional ed25519 signing. Rows below say which version each claim holds for.

---

## ✅ Proven (verified, with evidence)

| Claim | Evidence | Where it holds |
| --- | --- | --- |
| Package is MIT, **zero runtime deps**, stdlib-only | `pyproject.toml` (`dependencies = []`); `pip install procheiron` verified | 0.1.0 (published) |
| CLI works: `version` / `init` / `validate` / `conformance` / `mcp` | `src/procheiron/cli.py`; `mcp` added in 0.1.1 | `mcp` = 0.1.1 staged; rest = 0.1.0 |
| Conformance passes — **at fixture level** | `conformance/run_conformance.py` → **14/14 base (stdlib) + 15/15 with the `crypto` extra** (Meridian generic-vault + 5-file minimal + 10 negatives incl. tilde-weld & chain-break + crypto-gated signed/forged + doctrine-currency guard) | 0.2.0 package |
| Conformance runs the **one Core validator**, not a per-fixture copy | de-vendored: fixtures carry data only; `run_conformance.py` invokes `python3 -m procheiron.validate` | 0.1.1 staged |
| Constitution is current **4.6 doctrine** (git → preservation-executor) | `SELF_ACTION_POLICY.md`; fixture copy byte-identical to live canon; doctrine-currency guard fails a stale doc | 0.1.1 staged (0.1.0 ships the pre-4.6 fixture — see caveats) |
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
| **Released fixture is stale (0.1.0)** | PyPI 0.1.0 still ships the **pre-4.6 git-welded** fixture constitution. Fixed in 0.1.1 (staged, unpublished). |
| **MCP not armed for all agents** | Packaged + portable + armed for one session; broad per-agent `--allow-writes` rollout pending. |
| **Trust-loop longevity unproven** | A 30-day continuous trust-loop run (promotions + recorded blocks) is not yet complete. Checkpoint ~2026-07-26. |
| **OPA/Rego: CI job added, not yet confirmed green** | `procheiron.rego` now has a CI job that runs `opa test` (`.github/workflows/ci.yml` → `policy-opa`), closing the "nothing executes it" gap in principle. The stdlib `policy.py` remains the production backend. Still ❌ until the CI job is observed passing (no `opa` in the authoring environment to run it locally). |
| **Single-trust-domain limit (chain + signing)** | `verify_chain` checks only *internal* continuity, so a writer can rebuild the whole chain from GENESIS; and `known_actor_keys` (the public-key registry) lives in the same writable profile, so an insider who can write the audit log can also re-register fresh keys and re-sign the rewrite (red-team Attack #1, reproduced). Chain + signing therefore close the dual-write forgery **only with BOTH** (a) an externally-anchored head (`validate --expect-head <hex>`, git-pinned) **and** (b) the key registry out of the writer's write scope (separate OS user / HSM / Sigstore keyless). On one shared machine without those, you get tamper-**evidence** (detectable via the anchor), not tamper-**prevention**. Private keys on a shared filesystem are additionally only as strong as their file permissions. |
| **Crypto not yet in the live deployment** | The tamper-evident chain + optional signing are proven in the package + conformance; the authors' own live deployment has **not yet migrated** its audit log onto the chain (an available follow-up, kept separate to avoid disturbing a running system). |

## Discipline

- A row moves from ❌ to ✅ **only** with cited, reproducible evidence.
- No "production-replicable" claim until a second real deployment passes conformance.
- If this ledger and a headline ever disagree, **this ledger wins** — it is the provenance system applied to itself.
