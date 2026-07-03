# Meridian Atelier — Procheiron Deployment Profile

**Profile name:** `meridian`
**Deployment root:** `{root}`
**Constitutional authority:** Dana Okoro
**Profile version:** 0.1
**Adopted:** 2026-06-12

---

## Deployment Identity

Meridian Atelier is an independent furniture design studio specializing in bespoke residential and
commercial pieces. The studio operates a shared operational knowledge base (this Procheiron deployment)
to coordinate design intent, material sourcing research, project state, and production decisions across
a small team of design agents and human curators.

This profile binds the agent-neutral Procheiron Core governance to the concrete paths, actors, and
policies of the Meridian Atelier deployment.

---

## Directory Topology

| Token | Resolved path | Purpose |
|---|---|---|
| `{root}` | `.` | Deployment root |
| `{paths.console}` | `console` | Core governance docs and deployment ledgers |
| `{paths.memory}` | `memory` | Structured memory commons (JSONL index) |
| `{paths.sources}` | `sources` | Immutable raw source material |
| `{paths.wiki}` | `knowledge` | Rebuildable synthesis cache |
| `{paths.outputs}` | `outputs` | Agent work products and deliverables |
| `{paths.adapters}` | `adapters` | Adapter manifest directory |
| `{paths.legacy_governance}` | `studio` | Legacy studio governance documents |
| `{paths.workspace}` | `workspace` | Active working drafts |
| `{paths.runtime_root}` | `runtime/procheiron` | Procheiron runtime scratch space |
| `{paths.runtime_state}` | `runtime/state/STATE.json` | Live operational state (do not index) |
| `{paths.scripts}` | `scripts` | Operational scripts |

---

## Constitutional Authority

Dana Okoro is the constitutional authority for this deployment. She is the sole human with authority
to authorize Tier-B promotions, unlock enforcement gates, and grant new agents promotion authority.
Any claim that "Dana authorized X" without a signed DECISIONS.md entry under her name should be
treated as unverified.

---

## Agent Actor Registry

| Actor id | Role | Group |
|---|---|---|
| `atlas_drafter` | Design proposal agent, distiller | atlas |
| `atlas_review_bot` | Automated review assistant for atlas outputs | atlas |
| `vera_curator` | Curation and promotion agent | vera |
| `vera_ingest_bot` | Source ingest and candidate-proposal bot | vera |
| `dana_okoro` | Constitutional authority (human) | — |

Actor groups exist so that cross-group review can be verified: an `atlas_*` actor proposing a record
must be reviewed by a `vera_*` actor (or `dana_okoro`) for that record to reach `active` status.

---

## Promotion Lifecycle (meridian)

Records follow the standard Procheiron lifecycle: `draft` → `candidate` → `validated` → `active` →
`superseded`/`archived`/`disputed`. Meridian-specific rule: `atlas_*` agents may create and propose
records; only `vera_*` agents or `dana_okoro` may act as reviewers for the promotion audit event.

---

## Retrieval Policy Reference

See `{root}/.procheiron/profiles/meridian/retrieval.md` for the concrete no-index globs and
root-to-canonicality mapping. The doctrine itself lives at `{paths.console}/RETRIEVAL_POLICY.md`.

---

## Policy Defaults

All policy defaults from `{root}/.procheiron/config.yaml` apply. Key constraints:
- `agents_may_propose_not_promote: true` — agents may draft and propose records; they may not
  self-authorize promotion to `active`.
- `secrets_allowed: false` — no credentials, tokens, or private keys in `{paths.memory}`.
- `provenance_required: true` — every durable memory record must cite at least one `source_paths`
  entry pointing to a file within `{root}`.
- `raw_sources_immutable: true` — files under `{paths.sources}` may not be edited after capture.

---

## Gate-Class Changes (meridian)

Lint edits, config topology changes, and retrieval policy changes are gate-class. Any relaxation
of lint enforcement keys (`validate_memory_records`, `forbid_absolute_paths_in_memory_records`,
`forbidden_core_doc_literals`) requires an L4 or higher record in `{paths.console}/DECISIONS.md`
authorized by Dana Okoro.
