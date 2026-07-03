# Memory

`{paths.memory}/` stores structured, provenance-bearing, rebuildable memory records for Procheiron.

## Purpose

The purpose of this layer is to make durable memory inspectable, temporal, source-linked, and portable
across agents. It is a memory commons, not a hidden database.

## What Belongs Here

- Candidate and approved durable memories.
- Entity and relation indexes.
- Supersession records.
- Task state records that need cross-agent visibility.
- Adapter manifests.
- Audit records.
- Profiles describing scopes and audiences.
- Validation and evolution records.

## What Does Not Belong Here

- Secrets, tokens, cookies, credentials, or private keys.
- Raw transcripts without provenance; use `{paths.sources}/`.
- Agent diary entries; use agent workspaces.
- Work products; use `{paths.outputs}/`.
- Procedures better stored as skills or program files.
- Unsourced claims promoted as canonical memory.

## JSONL Index Files

- `index/memories.jsonl` — durable memory records.
- `index/entities.jsonl` — people, businesses, systems, projects, tools, and other named entities.
- `index/relations.jsonl` — typed edges between entities or memories.
- `index/supersessions.jsonl` — explicit replacements, corrections, and archival lineage.
- `index/tasks.jsonl` — cross-agent task records where appropriate.
- `index/adapters.jsonl` — machine-readable adapter capability declarations.
- `index/audit.jsonl` — memory and policy change audit events.

## Promotion Lifecycle

1. `draft` — captured but not validated.
2. `candidate` — source-linked and ready for validation.
3. `validated` — checked against evidence and schema.
4. `active` — promoted into canonical use by approved reviewer/policy.
5. `superseded` — replaced by a newer record with explicit link.
6. `archived` — retained for history but not active guidance.
7. `disputed` — contested or uncertain; do not rely on it without review.

Agents may create draft/candidate records where authorized. They may not silently promote candidate
memory into active canonical memory.

## Using Active Memory

Agents may use `active` and `validated` memory records to guide work. `candidate` and `draft` records
are proposals or evidence only. `disputed`, `superseded`, and `archived` records are historical context
only unless a task explicitly asks for historical review.

Durable claims based on memory must cite source paths or source IDs from the record. If a memory has
no usable provenance, treat it as draft/candidate even if the text seems plausible.
