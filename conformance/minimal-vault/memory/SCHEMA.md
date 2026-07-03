# Procheiron Memory Record Schema (v0.1)

Schema source: `schemas/memory_record.schema.json` (JSON Schema Draft 2020-12).  
Index location: `{paths.memory}/index/memories.jsonl` — one JSON object per non-empty line.

---

## Required Fields

Every record must carry all of the following at write time:

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique record identifier. Recommended pattern: `mem_YYYYMMDD_<slug>`. Must be non-empty. |
| `type` | enum | One of: `fact`, `decision`, `preference`, `lesson`, `procedure_pointer`, `blocker`, `relation`, `task_state`. |
| `scope` | enum | One of: `global`, `profile`, `business`, `project`, `agent`, `user`, `customer`, `system`. |
| `profile` | string | The deployment profile this record belongs to. Non-empty. |
| `subject` | string | Short human-readable subject label. Non-empty. |
| `statement` | string | The declarative memory text. Non-empty, max 1200 characters. |
| `status` | enum | Lifecycle status (see below). |
| `confidence` | number | Float in [0.0, 1.0]. JSON booleans are not valid here. |
| `created_at` | string | ISO-8601 timestamp of creation. |
| `created_by` | string | Agent id of the creating agent or harness. Non-empty. |

---

## Optional Fields

| Field | Type | Description |
|---|---|---|
| `source_ids` | string[] | References to other record ids that justify this record. |
| `source_paths` | string[] | Root-relative or tokenised paths (`{paths.<key>}/...`) that justify this claim. Machine-absolute paths are forbidden. |
| `valid_from` | string | ISO date (`YYYY-MM-DD`) from which the record is considered current. |
| `valid_until` | string or null | ISO date at which the record expires. Null means indefinite. |
| `supersedes` | string[] | Ids of records this record replaces. Each entry must begin with `mem_`. |
| `sensitivity` | enum | One of: `public`, `internal`, `confidential`, `restricted`, `secret_ref`. |
| `visibility` | enum | One of: `human_visible`, `restricted_summary`, `metadata_only`. |
| `reviewed_by` | string or null | Reviewer agent id. String for reviewed records; null for unreviewed proposals. Must never be a list. |
| `reviewed_at` | string or null | ISO-8601 timestamp of the review. |
| `write_policy` | enum | One of: `proposal_only`, `approved_canonical`, `system_generated`. |
| `notes` | string | Free-text annotation. |

No additional properties are permitted (`additionalProperties: false`).

---

## Lifecycle Statuses

| Status | Meaning |
|---|---|
| `draft` | Rough proposal; not yet submitted. |
| `candidate` | Submitted via `memory_propose.py`; under review. `write_policy` is forced to `proposal_only`. |
| `validated` | Reviewed and approved by an independent actor. |
| `active` | Promoted operational truth. `write_policy` must be `approved_canonical` (never `proposal_only`). |
| `superseded` | Replaced by another record. Kept for lineage. |
| `archived` | Retired without a replacement. |
| `disputed` | Flagged as contested. Can transition back to `candidate` with independent review. |

---

## Provenance Requirement

Every record must carry provenance: at least one entry in `source_paths` or `source_ids`. The validator refuses records with neither. Source paths must be root-relative or use the `{paths.<key>}/...` token form — machine-absolute paths (beginning with `/` or a drive letter) are explicitly forbidden.

---

## Independent Review for Promotion

`active` and `validated` records carry additional schema constraints:

1. `reviewed_by` must be present and non-null (a non-empty string).
2. `reviewed_at` must be present and non-null (a non-empty string).
3. `reviewed_by` must differ from `created_by` — self-review is refused.
4. A corroborating audit event (`memory_promoted` for `active`, `memory_validated` for `validated`) must exist in `memory/index/audit.jsonl` with the matching `memory_id` and the reviewer as `actor`.

These rules are enforced by `validate_minimal.py` at runtime, not only by the JSON Schema, because they involve cross-record and cross-file checks that JSON Schema cannot express.

---

## Secret Pattern Guard

Free-text fields (`statement`, `subject`, `notes`) must not contain credential-like patterns (API keys, private keys, tokens). The propose helper enforces this at write time; the validator scans all `.md`, `.jsonl`, `.json`, and `.txt` files in the deployment tree.
