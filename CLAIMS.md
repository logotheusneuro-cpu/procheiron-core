# Procheiron — Claims Ledger (proven vs. not proven)

Procheiron is a provenance and trust layer. This ledger holds **its own** claims to the
same standard it asks of any memory: a claim is **proven** only with cited, reproducible
evidence — everything else is labeled honestly. The governing rule: *no "production-ready"
or "production-replicable" claim until a second real deployment passes conformance.*

- Last updated: 2026-06-26
- Published package: `procheiron` **0.1.0** (PyPI). Current repo / **0.1.1 (staged, unpublished)** is ahead — rows below say which.

---

## ✅ Proven (verified, with evidence)

| Claim | Evidence | Where it holds |
| --- | --- | --- |
| Package is MIT, **zero runtime deps**, stdlib-only | `pyproject.toml` (`dependencies = []`); `pip install procheiron` verified | 0.1.0 (published) |
| CLI works: `version` / `init` / `validate` / `conformance` / `mcp` | `src/procheiron/cli.py`; `mcp` added in 0.1.1 | `mcp` = 0.1.1 staged; rest = 0.1.0 |
| Conformance passes — **at fixture level** | `conformance/run_conformance.py` → 11/11 (Meridian generic-vault + 5-file minimal + 8 negatives + doctrine-currency guard) | 0.1.1 staged (0.1.0 = 10/10, no guard) |
| Conformance runs the **one Core validator**, not a per-fixture copy | de-vendored: fixtures carry data only; `run_conformance.py` invokes `python3 -m procheiron.validate` | 0.1.1 staged |
| Constitution is current **4.6 doctrine** (git → preservation-executor) | `SELF_ACTION_POLICY.md`; fixture copy byte-identical to live canon; doctrine-currency guard fails a stale doc | 0.1.1 staged (0.1.0 ships the pre-4.6 fixture — see caveats) |
| `memory_promotion_gate` **enforces** independent review | `memory_promote.py`: refuses self-review (§8.7), same-actor-group laundering, active-without-authority; tested e2e | live deployment + package |
| The gate **durably records its blocks** | refusals append a schema-valid `promotion_refused` audit event (≠ `memory_promoted`/`memory_validated`, never false-corroborates); tested | live + package (0.1.1 staged) |
| MCP server is packaged + **deployment-portable** | `src/procheiron/mcp_server.py` (config-resolved paths, no hardcoded deployment paths); `conformance/test_mcp_smoke.py` passes against the generic fixture deployment | 0.1.1 staged |
| Lifecycle + provenance model | draft→candidate→validated→active→superseded/archived/disputed; `active` requires `reviewed_by ≠ created_by` + corroborating audit event; validator enforces | live + package |

## ❌ Not proven / honest caveats (the load-bearing part)

| Claim status | Detail |
| --- | --- |
| **Production-replicability: NOT proven** | Conformance is **fixture-level only**. The "second deployment" (Meridian) is fictional, and the fixtures are home-team (same authors wrote the validator and the fixtures). A v1.0 / "production-replicable" claim requires a **real, independent second deployment** passing conformance. |
| **Single real deployment** | Procheiron currently governs exactly one system — the authors' own multi-agent deployment. The core promise ("a *different* agent can trust this memory") is exercised **internally** (an ingesting agent proposes → an independent agent promotes → consuming agents read → a human authorizes), not yet across independent organizations. |
| **9 of 10 gates are inert** | The constitution defines 10 gates; only `memory_promotion_gate` is implemented + enforced. The rest are "policy defines gates; it does not implement them." |
| **Released fixture is stale (0.1.0)** | PyPI 0.1.0 still ships the **pre-4.6 git-welded** fixture constitution. Fixed in 0.1.1 (staged, unpublished). |
| **MCP not armed for all agents** | Packaged + portable + armed for one session; broad per-agent `--allow-writes` rollout pending. |
| **Trust-loop longevity unproven** | A 30-day continuous trust-loop run (promotions + recorded blocks) is not yet complete. Checkpoint ~2026-07-26. |
| **OPA/Rego is reference-only** | `procheiron.rego` ships as a standards reference but **nothing executes it** (no `opa` on PATH, no CI). The stdlib `policy.py` is the production backend. Treat the `.rego` as documentation until an `opa test` step exists, or it drifts. |

## Discipline

- A row moves from ❌ to ✅ **only** with cited, reproducible evidence.
- No "production-replicable" claim until a second real deployment passes conformance.
- If this ledger and a headline ever disagree, **this ledger wins** — it is the provenance system applied to itself.
