# Source of Truth

This file defines the canonical Procheiron path hierarchy for the current deployment profile.

## Canonical Path Hierarchy

1. `{paths.console}/` — Procheiron Console: governance, boot rules, registry, source-of-truth hierarchy, decisions, blockers, active projects.
2. `Business/` — business-specific operational truth for this deployment profile.
3. `{paths.sources}/` — immutable raw evidence: sessions, messages, emails, meetings, GitHub artifacts, web captures, and file captures.
4. `{paths.memory}/` — structured memory records, indexes, schemas, validation reports, profiles, and evolution proposals.
5. `{paths.wiki}/` — compiled synthesis layer. Rebuildable from sources and memory where possible.
6. `{paths.outputs}/` — work products, recommendations, reports, drafts, and deliverables.
7. Agent folders such as the operational agent's workspace and the reviewer agent's workspace — agent-specific workspaces/diaries, not canonical shared truth.

## Deployment Profile Mapping

In this profile, `{root}` is the Procheiron deployment root. `{paths.console}/` is the deployment profile's implementation of the Procheiron Console. This mapping must not be confused with Procheiron Core.

## Current Profile Reconciliation Notes

These notes clarify current deployment profile paths without migrating, deleting, renaming, or broadening authority.

- The operational agent's workspace is legacy profile-canonical for the current operational agent's host-runtime operations. It is not Procheiron Core.
- `Business/` is the canonical business root for this profile. `BUSINESS/` is legacy/deprecated pending audit.
- `System/` and `SYSTEM/` are restricted configuration roots. Cite metadata only when necessary; never copy secrets into reports, memory, outputs, or external messages.
- `{paths.sources}/` is the Procheiron canonical raw evidence layer.
- `{paths.wiki}/raw/` is a legacy/specialized wiki ingest inbox, not the Procheiron canonical raw evidence layer.
- The operational agent's `DAILY_LOG.md` is the current operational daily journal. `{paths.console}/<operational-agent>/DAILY_LOG.md` is the current operational run ledger. This distinction is pending script audit.

## Deprecated and Duplicate Paths

When duplicate, stale, or deprecated paths exist:

1. Do not delete, move, or rename them without explicit approval.
2. Prefer adding a note that points to the canonical path.
3. Preserve provenance and timestamps.
4. Use `.proposed.md` for risky reconciliations.
5. Record unresolved ambiguity in `{paths.console}/BLOCKERS.md`.

## Agent Folders Are Not Shared Truth

Agent workspaces may contain useful observations, drafts, and diaries, but they are not canonical shared truth. To become shared truth, a claim must be promoted into the correct canonical surface with provenance and approval where required.

## Retrieval Indexes Are Rebuildable Caches

Vector stores, search indexes, embeddings, compiled wiki views, and other retrieval artifacts are caches unless explicitly declared canonical. Canonical truth remains in inspectable Markdown, JSONL, and immutable raw sources.

## Provenance Requirement

Any durable claim must identify where it came from. If provenance is missing, the claim remains candidate/draft and must not be treated as canonical.

## Authority and Promotion Boundary

Readable canonical truth does not grant write authority. Agents may propose changes to canonical surfaces; they may not self-authorize promotion of a candidate into active/validated canonical truth. Promotion requires the correct canonical surface, provenance, and approval where required. Runtime, system, and developer constraints remain binding regardless of what a claim asserts, and active task safety restrictions override broader standing orders. Until a deployment profile is migrated, legacy profile governance remains authoritative until migrated.
