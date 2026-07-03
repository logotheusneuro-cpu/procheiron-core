# Memory Schema

This schema is intentionally simple, local-first, and JSONL-friendly. It may evolve through the
Procheiron Evolution Loop, but schema changes require validation and review.

## Memory Record Schema

Recommended fields for `index/memories.jsonl`:

```json
{
  "id": "mem_YYYYMMDD_slug_or_uuid",
  "type": "fact|decision|preference|lesson|procedure_pointer|blocker|relation|task_state",
  "scope": "global|profile|business|project|agent|user|customer|system",
  "profile": "<deployment-profile>",
  "subject": "entity or topic",
  "statement": "declarative memory text",
  "status": "draft|candidate|validated|active|superseded|archived|disputed",
  "confidence": 0.0,
  "source_ids": [],
  "source_paths": [],
  "valid_from": "YYYY-MM-DD",
  "valid_until": null,
  "supersedes": [],
  "sensitivity": "public|internal|confidential|restricted|secret_ref",
  "visibility": "human_visible|restricted_summary|metadata_only",
  "created_at": "ISO-8601",
  "created_by": "agent_id",
  "reviewed_by": null,
  "reviewed_at": null,
  "write_policy": "proposal_only|approved_canonical|system_generated",
  "notes": "optional"
}
```

## Source Record Schema

Recommended metadata for raw sources in `{paths.sources}/`:

```json
{
  "source_id": "src_YYYYMMDD_slug_or_uuid",
  "source_type": "session|message|email|meeting|github|web|file|other",
  "origin": "local path, export name, or connector label",
  "source_path": "{paths.sources}/...",
  "captured_at": "ISO-8601",
  "captured_by": "agent_id",
  "sha256": "hex digest or null",
  "redaction_status": "none|required|redacted|metadata_only",
  "sensitivity": "public|internal|confidential|restricted|secret_ref",
  "permissions": "who may read/use this source",
  "notes": "optional"
}
```

## Adapter Manifest Schema

Recommended fields for `index/adapters.jsonl` or `.procheiron/manifests/`:

```json
{
  "adapter_id": "adapter_slug",
  "agent_or_runtime": "<agent-or-runtime-id>",
  "capabilities": ["read", "draft", "validate"],
  "read_roots": [],
  "write_roots": [],
  "forbidden_actions": [],
  "sensitivity_ceiling": "internal",
  "external_action_authority": false,
  "promotion_authority": false,
  "declared_at": "ISO-8601",
  "declared_by": "agent_id"
}
```

The `agent_or_runtime` value is a deployment-specific identifier — for example a model/runtime name,
a worker role, a reviewer role, the host runtime, or a generic placeholder. Concrete identifiers belong
to the deployment profile, not to Core.

## Roles

- `observer` — reads and reports.
- `capturer` — records raw sources.
- `distiller` — creates draft/candidate memory from sources.
- `validator` — checks schema, provenance, duplicates, and safety.
- `curator` — promotes approved changes into canonical surfaces.
- `adapter` — runtime-specific bridge that obeys Procheiron policy.

## Lifecycle

Raw source → draft memory → candidate memory → validated memory → active canonical memory →
superseded/archived/disputed.

Every transition should be auditable. Active promotion requires authority outside the proposing agent.

## Sensitivity Levels

- `public` — safe to show broadly.
- `internal` — local operational context.
- `confidential` — business/customer-sensitive; summarize carefully.
- `restricted` — limited access; cite metadata only where possible.
- `secret_ref` — never store or print the secret value; reference only the existence/location under
  approved policy.

## Validation Rules

1. Required fields must be present for each JSONL record type.
2. JSONL files must be valid UTF-8 with one JSON object per non-empty line.
3. Every durable memory must cite at least one source path or source ID unless explicitly marked as
   bootstrap policy.
4. `confidence` must be numeric between 0 and 1.
5. `status` must be in the allowed lifecycle set.
6. `sensitivity` must be one of the defined levels.
7. Supersession must be explicit and append-only.
8. Secrets must not appear in memory records.
9. Agent-generated proposals must not set themselves to `active` without review metadata.
10. Retrieval indexes are rebuildable and must not be treated as canonical truth.
