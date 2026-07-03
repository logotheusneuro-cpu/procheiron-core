# Memory Validation

This file defines the local validation expectations for Procheiron Phase 1/2 in the meridian deployment.

## Phase 1/2 Checks

- Deployment root exists.
- Governance files exist or proposed alternatives exist.
- `{paths.sources}/`, `{paths.memory}/`, `{paths.adapters}/`, and `.procheiron/` scaffolds exist.
- JSONL index files are valid or empty.
- `.procheiron/config.yaml` contains no credentials.
- Created files do not contain obvious secret values.
- Reports list created, modified, skipped, and blocked actions.

## Memory Record Validation (meridian)

The meridian profile enables full memory record validation:
- `validate_memory_records: true` — all records in `index/memories.jsonl` are schema-checked.
- `forbid_absolute_paths_in_memory_records: true` — source_paths must be root-relative or use
  `{paths.*}` token form; machine-absolute paths are an error.
- Active and validated records require an independent reviewer from a different actor group and a
  corroborating promotion audit event in `index/audit.jsonl`.
- Superseded records require a matching entry in `index/supersessions.jsonl`.

## Validation Reports

Validation reports belong under `{paths.memory}/lint/reports/` for recurring checks and under
`{paths.outputs}/` for human reports.

## Non-Goals

Phase 1/2 validation does not enable hooks, schedulers, external services, package installs, or
automatic memory promotion.
