# Procheiron Memory Commons Spec v0.1-draft

Status: proposal-only draft skeleton.
Normative target: `procheiron-core` v0.1 memory contract.

## 1. Purpose

The memory commons is a local-first, inspectable, provenance-bearing substrate for durable memory across agents and runtimes. It is not a hidden database and not an agent diary.

## 2. Required memory surface

A compliant full deployment SHOULD provide a memory root located via `paths.memory` with:

- `README.md`
- `SCHEMA.md`
- `index/memories.jsonl`
- `index/entities.jsonl` where needed
- `index/relations.jsonl` where needed
- `index/supersessions.jsonl` where needed
- `index/tasks.jsonl` where needed
- `index/adapters.jsonl`
- `index/audit.jsonl`

A minimal v0.1 adopter MAY reduce this to `SCHEMA.md`, memory schema JSON, and `index/memories.jsonl`, provided conformance still enforces provenance, lifecycle status, sensitivity, and proposal/promotion separation.

## 3. Memory record contract

Each memory record MUST be one JSON object per JSONL line. The standard record shape includes the fields below.
A deployment's conformance tier MUST declare which fields are required; at minimum, every non-draft record MUST
include identity, lifecycle status, subject/statement, provenance, confidence, sensitivity, creator, and write policy.

The standard fields are:

- `id`
- `type`
- `scope`
- `profile`
- `subject`
- `statement`
- `status`
- `confidence`
- `source_ids`
- `source_paths`
- `valid_from`
- `valid_until`
- `supersedes`
- `sensitivity`
- `visibility`
- `created_at`
- `created_by`
- `reviewed_by`
- `reviewed_at`
- `write_policy`
- `notes`

Conformance MUST reject malformed JSONL, missing required fields, invalid lifecycle states, invalid sensitivity values, confidence outside 0..1, and active/validated records that lack the required review/promotion evidence under the deployment policy.

## 4. Lifecycle states

The standard lifecycle states are:

- `draft` — captured but not validated
- `candidate` — source-linked and ready for validation
- `validated` — checked against evidence and schema
- `active` — promoted for current shared use by an approved reviewer/policy
- `superseded` — replaced by explicit lineage
- `archived` — retained for history, not current guidance
- `disputed` — contested or uncertain

Default retrieval MUST treat only `active` and `validated` as current guidance. `candidate` and `draft` are proposal/evidence only. `superseded`, `archived`, and `disputed` are historical/noncurrent unless explicitly requested.

## 5. Provenance

Every durable memory MUST cite at least one usable `source_id` or `source_path`, unless the deployment explicitly marks it as bootstrap policy. If a statement is inferred rather than directly stated by sources, the record SHOULD say so in notes and lower confidence.

Raw evidence belongs in `paths.sources`; derived memory belongs in `paths.memory`. Raw sources SHOULD be immutable after capture.

## 6. Sensitivity

Standard sensitivity levels:

- `public`
- `internal`
- `confidential`
- `restricted`
- `secret_ref`

Secrets, tokens, cookies, credentials, private keys, and raw secret values MUST NOT be stored in memory records. `secret_ref` may identify the existence or approved metadata of a secret-bearing surface, never the secret value.

## 7. Proposal and promotion

Agents MAY create `draft` or `candidate` records when their adapter/profile allows writes to the target root.

Agents MUST NOT promote their own generated memory to `active` or `validated` without independent review and
explicit promotion authority. Promotion or validation of a current-guidance record MUST be auditable: either an
append-only event in `index/audit.jsonl` or a tier-declared equivalent MUST record actor, reviewer/authorizer,
status transition, reason, timestamp, and source record.

A passing validator verdict can block promotion. It cannot grant promotion authority.

## 8. Supersession

Corrections MUST be explicit. A newer record SHOULD list prior records in `supersedes`; the older record should become `superseded` only through the sanctioned promotion/status workflow. Silent replacement is noncompliant.

## 9. Adapters

Adapter declarations SHOULD include:

- adapter/runtime identity
- capabilities
- read roots
- write roots
- forbidden actions
- sensitivity ceiling
- external action authority
- promotion authority

Readable adapter declarations do not grant authority beyond their fields and active task constraints.

## 10. Audit and rebuildability

The memory layer SHOULD be rebuildable from raw sources plus audit events where practical. Derived indexes, retrieval caches, embeddings, and synthesized wiki pages are not canonical unless explicitly declared by the deployment and covered by conformance.
