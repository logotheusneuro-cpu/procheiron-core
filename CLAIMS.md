# Procheiron — Claims Ledger (proven vs. not proven)

Procheiron is a provenance and trust layer, so this ledger holds our own claims to the same
standard we ask of any memory: a claim counts as proven only with cited, reproducible evidence.
Everything else gets labeled for what it is. One rule governs the whole file: no "production-ready"
or "production-replicable" claim until a second real deployment passes conformance.

- Last updated: 2026-07-10
- Published package: `procheiron` **0.2.4** (PyPI, sdist + wheel) — tamper-evident hash-chained
  audit log plus optional ed25519 signing. 0.2.1/0.2.2 added the branded README, the pip-only
  first-run fixes, and cross-OS CI; **0.2.3/0.2.4 close the trust-boundary gaps a second
  independent audit (2026-07-09) found** (see below). 0.1.0 remains installable pinned but
  predates the chain. Rows below say which version each claim holds for.

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
| **Optional ed25519 signing** of audit entries | `signing.py` (opt-in `procheiron[crypto]`); `procheiron keygen` mints a keypair (private key → 0600 file, public key → stdout for `known_actor_keys`); conformance proves a signed log verifies, a forged signature is caught, a stripped signature is caught, AND a **correctly-chained forged append by a keyed actor is rejected** (the chain passes it; signing catches it); a verification that cannot run (crypto absent + signatures required) is a hard error, never a silent pass | 0.2.0 package; keygen + append-forgery guard unreleased |

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

## Trust-boundary fixes from the second independent audit (2026-07-09, shipped in 0.2.3/0.2.4)

The first round of these was cosmetic — a second audit showed the "trusted read" filtered a
mutable field and MCP promotion took the reviewer as a free string. These are the real fixes.

| Fix | What was wrong | Evidence |
| --- | --- | --- |
| **MCP reviewer is the authenticated actor** | `memory.promote` took `reviewer`/`approver` as tool arguments, so a client bound as `alice` could promote alice's own record by passing `reviewer:"bob"`. The identity binding was discarded at the authority boundary. Now the reviewer/authorizer IS the bound `--actor`; a differing argument is rejected. | `mcp_server.py` `promote_memory` actor-binding; `check_trust_boundary` conformance guard |
| **Trusted reads are evidence-derived, not status-filtered** | `memory.search` trusted `status` alone — flipping a candidate to `active` in place made it served. Now a record is served on the default path only if its status is backed by the audit log's latest transition (independent actor). `memory.get` returns an explicit `trusted` boolean. | `lifecycle.py`; `mcp_server.search_memories`/`get_memory`; `check_trust_boundary` forges an active record and asserts it is hidden |
| **Latest-transition lifecycle check (both tiers)** | A stale promotion event vouched for a record later archived and flipped back to `active`. Both validators now require the record's status to equal the audit log's *latest* transition. | `validate.py` `latest_trans`; `validate_minimal.py`; reproduced archived→active now FAILs |
| **Minimal validator casefold + promoter identity** | Raw `==` let `BOB` clear review against `bob`, and only checked a promotion event existed. Now NFKC+casefold + the promoter must be the independent reviewer. | `validate_minimal.py` `_norm_actor`; pip-journey case-variant guard |
| **Writers preflight the chain, fail closed** | On a missing chain helper the writers appended an *unchained* event and reported success (invalid deployment). Now they refuse before writing anything. | `memory_promote.py`/`memory_propose.py` `_require_chain` |
| **`init` won't flip a legacy verdict; `--force` won't destroy data** | Re-running `init` on an unchained log silently added the chain lint (now checks every event at the configured path and refuses); plain `--force` emptied the indexes (now needs `--reset-data`). | `init.py` `_has_unchained_audit`, `--reset-data` guard |
| **Strict boolean on `include_untrusted`** | `include_untrusted:"false"` (a string) coerced to truthy and leaked candidates. Now only a real JSON `true` opens the untrusted view. | `mcp_server.py` `is True` check |

### Still NOT closed (honest residual)
| Limit | Detail |
| --- | --- |
| **Append-forgery needs signing WITH out-of-band key custody** | Turning on `procheiron[crypto]` signing (`verify_signatures` + `known_actor_keys`) now *rejects* a correctly-chained forged append by a keyed actor — the chain passes it, signing catches it (proven by the `forged chained append` conformance guard, and reachable via `procheiron keygen`). What signing on one shared machine does **not** close: the private key and the `known_actor_keys` registry both live in the writer's write scope, so an insider can re-register a fresh key and re-sign the forgery. The residual is fully closed only with (a) the head externally anchored (`validate --expect-head`) and (b) key custody out of the writer's reach (separate OS user / HSM / Sigstore). Until then, signing narrows append-forgery from "any string" to "needs the private key + an anchored registry" — a real bar-raise, not a full close. This is the boundary between tamper-*evidence* and authenticated *provenance*. |

## Discipline

- A row moves from ❌ to ✅ **only** with cited, reproducible evidence.
- No "production-replicable" claim until a second real deployment passes conformance.
- If this ledger and a headline ever disagree, **this ledger wins** — it is the provenance system applied to itself.
