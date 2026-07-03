# Meridian Atelier — Decision Ledger

This file is the authoritative record of significant governance, policy, and architectural decisions
for the Meridian Atelier Procheiron deployment. All L3+ decisions must be recorded here with
authorization reference before taking effect.

Constitutional authority: Dana Okoro.

---

## Decision Log

### 2026-06-12 — D001: Initial Procheiron adoption at Meridian Atelier

**Level:** L4 (topology change)
**Authorized by:** Dana Okoro
**Authorization ref:** meridian-adoption-20260612

**Decision:** Adopt Procheiron v0.1 as the shared operational knowledge base for Meridian Atelier
design studio. Deploy with profile `meridian`, two agent actor groups (`atlas_*` for design agents,
`vera_*` for curation agents), and Dana Okoro as constitutional authority.

**Rationale:** The studio needs a durable, provenance-bearing, cross-agent memory layer for design
decisions, material sourcing findings, and project state. Procheiron's agent-neutral, local-first,
human-visible model fits the studio's small-team, inspection-first culture.

**Scope:** Deployment root `.`, paths as defined in `.procheiron/config.yaml`. Memory validation
enabled from day one.

---

### 2026-06-12 — D002: Actor group separation for independent review

**Level:** L3 (governance policy)
**Authorized by:** Dana Okoro
**Authorization ref:** meridian-actorgroup-20260612

**Decision:** Define two actor groups for independent review enforcement:
- `atlas` group: `atlas_drafter`, `atlas_review_bot` — design proposal and review assistance.
- `vera` group: `vera_curator`, `vera_ingest_bot` — curation, source ingest, and promotion.

**Rule:** An active or validated memory record proposed by an `atlas_*` actor must be reviewed by
a `vera_*` actor or by `dana_okoro`. Self-review and same-group review produce an authority-laundering
warning in the validator.

**Rationale:** Separating design-proposal from curation-review prevents a single agent from both
proposing and promoting its own records to canonical status.

---

### 2026-06-12 — D003: Enable full memory record validation

**Level:** L4 (lint enforcement gate)
**Authorized by:** Dana Okoro
**Authorization ref:** meridian-memvalidation-20260612

**Decision:** Set `validate_memory_records: true` and `forbid_absolute_paths_in_memory_records: true`
in `.procheiron/profiles/meridian/lint.json` from day one of the deployment.

**Rationale:** Starting with full validation avoids accumulating un-validated records that would
require a later migration pass (as observed in reference deployments). Enforcing absolute-path
prohibition from the start keeps source_paths portable and avoids weld accumulation.
