# meridian profile — retrieval literals

Deployment-specific retrieval data for the **meridian** profile. The agent-neutral doctrine lives in
`{paths.console}/RETRIEVAL_POLICY.md`; this file binds that doctrine to concrete meridian paths. Editing
this file is a gate-class change (SELF_ACTION_POLICY §12) — it controls what retrieval may and may not read.

Install target: `{root}/.procheiron/profiles/meridian/retrieval.md`.

## Included roots — canonicality (meridian)

| Root | Canonicality label | Default |
|---|---|---:|
| `{paths.console}/*.md` | `canonical` | yes |
| `{paths.memory}/index/*.jsonl` | `canonical-structured-memory` | yes |
| `{paths.memory}/README.md`, `{paths.memory}/SCHEMA.md`, `{paths.memory}/VALIDATION.md` | `canonical` | yes |
| `{paths.wiki}/wiki/*.md` | `synthesis-cache` | yes |
| `{paths.legacy_governance}/*.md` | `profile-canonical-or-agent-workspace` | selective |
| `{paths.outputs}/**/*.md` | `work-product` | selective |

`{paths.sources}/` is metadata/scoped by default; raw source content is not globally indexed unless a
redacted source policy explicitly allows it.

## No-index globs (meridian) — by doctrine class

These enumerate the RETRIEVAL_POLICY "No-Index Rules" classes for this deployment. No global index,
search cache, snippet store, or retrieval result may include content matching any of these.

```text
# Runtime state and operational JSON
runtime/**
**/STATE.json
**/runtime-state*.json
**/pending_batch*.json

# Secrets and credentials
**/.env
**/.env.*
**/*token*
**/*secret*
**/*credential*
**/*cookie*
**/auth*.json
**/oauth*.json
**/credentials*.json

# Logs and transcripts
**/*.log
**/sessions/**
**/runs/**

# Repository internals
**/.git/**
**/__pycache__/**
**/node_modules/**
**/.venv/**
**/venv/**

# Backups
**/*backup*/**
**/*.bak
**/*.bak-*

# Raw captured payloads
**/*raw.json
**/*_raw.json
**/*raw*.json

# Binaries and media
**/*.png
**/*.jpg
**/*.jpeg
**/*.gif
**/*.mp4
**/*.mov
**/*.mp3
**/*.wav
**/*.pdf
**/*.docx
**/*.xlsx
**/*.sqlite
**/*.db
```

No-index rules must be applied before reading file contents. A retrieval tool may report exclusion
metadata (path and matched pattern) but must not read or print excluded file contents.
