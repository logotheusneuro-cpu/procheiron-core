# Meridian Atelier — Blockers Register

Active blockers and impediments to current studio operations. Resolved blockers are superseded in
memory records and archived here for historical context.

Constitutional authority for resolution authorization: Dana Okoro.

---

## Active Blockers

### BLK-001 — Material sourcing database not yet integrated

**Status:** Open
**Owner:** vera_curator
**Opened:** 2026-06-12
**Severity:** Medium

The studio maintains a spreadsheet of approved sustainable timber and fabric suppliers. This data
has not yet been ingested into the Procheiron sources layer. Until ingestion is complete, design
agents must consult the raw spreadsheet directly and cannot rely on memory records for supplier
status.

**Unblocking action:** Ingest supplier spreadsheet as a source document under `sources/`, extract
candidate memory records for key supplier facts, and promote them through the review lifecycle.

---

### BLK-002 — No automated candidate proposal tooling yet deployed

**Status:** Open
**Owner:** atlas_drafter
**Opened:** 2026-06-12
**Severity:** Low

Scripts directory is scaffolded but no automated memory proposal script has been wired to agent
output flows. Candidates must be proposed manually.

**Unblocking action:** Implement a `scripts/memory_propose.py` equivalent for the meridian profile.
Requires Dana Okoro authorization before writing to `memory/index/`.

---

## Resolved Blockers

None yet. This deployment opened 2026-06-12.
