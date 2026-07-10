# Procheiron Porting Guide — Compliant in 3 Steps

Get from zero to a validator-passing Procheiron memory commons in 3 commands.

---

## What You Get

Running `procheiron init` creates 11 files under your chosen root:

```
<root>/
  .procheiron/
    config.yaml                 ← version 0.1, your profile, path declarations
  console/
    CONSOLE.md                  ← doctrine one-pager (all 5 validator checks pass)
  memory/
    SCHEMA.md                   ← human-readable field/lifecycle documentation
    index/
      memories.jsonl            ← empty JSONL index (zero records is valid)
      audit.jsonl               ← empty audit log
  schemas/
    memory_record.schema.json   ← machine schema (Draft 2020-12, copied from adopter)
  validate_minimal.py           ← stdlib-only conformance validator
  procheiron_schema.py          ← validator helper (required by validate_minimal.py)
  memory_propose.py             ← candidate-record append helper (see note below)
  memory_promote.py             ← status promotion gate (see note below)
  .procheiron/
    profiles/<profile>/lint.json ← turns on verify_audit_chain (tamper-evident by default)
```

**What init gives you:** a minimal 5-file memory commons (config + CONSOLE.md +
SCHEMA.md + JSON schema + empty index files) that passes `validate_minimal.py`
on first run. Zero records is explicitly valid.

**What init does NOT give you:** the advanced governance module. The L0-L9
authority ladder, gate registry, decision ledger, retrieval policy, and
known-actor registry are optional and NOT required by the minimal validator.
See the "Adding Governance" section at the bottom for where those are added.

---

## Prerequisites

- Python 3.9+ (the commons and its validator are stdlib-only)
- `pip install procheiron` (the CLI ships the scaffolder and the validator)

---

## Step 1 — Scaffold the tree

```bash
procheiron init /your/project/root --profile yourprofilename
```

Replace `/your/project/root` with the directory you want to initialize (will be
created if absent). Replace `yourprofilename` with a slug identifying this
deployment (e.g., `myapp`, `acme`, `demo`).

**Expected output:**

```
Procheiron v0.1 init → /your/project/root  (profile='yourprofilename')

  CREATED  .procheiron/config.yaml
  CREATED  console/CONSOLE.md
  CREATED  memory/SCHEMA.md
  CREATED  memory/index/memories.jsonl
  CREATED  memory/index/audit.jsonl
  CREATED  schemas/memory_record.schema.json
  CREATED  validate_minimal.py
  CREATED  procheiron_schema.py
  CREATED  memory_propose.py
  CREATED  memory_promote.py
  CREATED  .procheiron/profiles/yourprofilename/lint.json

Done: 11 created, 0 skipped, 0 overwritten.
```

If you re-run without `--force`, every file is reported as `SKIPPED (already
present)` — init is idempotent.

---

## Step 2 — Validate

```bash
python3 /your/project/root/validate_minimal.py \
    --root /your/project/root \
    --json
```

**Expected output:**

```json
{
  "status": "PASS",
  "root": "/your/project/root",
  "records": 0,
  "errors": [],
  "warnings": []
}
```

If you see `"status": "FAIL"`, the `errors` array lists exactly what failed.
The most common causes and fixes are in the Troubleshooting section below.

---

## Step 3 — Confirm idempotency (optional but recommended)

```bash
procheiron init /your/project/root --profile yourprofilename
```

Every file should be reported as `SKIPPED (already present)`. Summary line:
`Done: 0 created, 11 skipped, 0 overwritten.`

---

## That Is It for Day-1 Conformance

At this point you have a conformant Procheiron memory commons. The validator
passes. You can add it to CI:

```bash
python3 validate_minimal.py --root . --json
```

Exit code 0 = PASS. Exit code 1 = FAIL (with errors in JSON output).

---

## Adding Memory Records

### Note on memory_propose.py and memory_promote.py

`memory_propose.py` and `memory_promote.py` are **copied into your tree by
init** for self-containment, but they require a small shared library
(`.procheiron/lib/`) that is part of the full Procheiron Core package, not
the minimal adopter. Without it, they refuse at startup:

```
memory_propose: REFUSED — no complete Procheiron lib found at the specified root
```

To use these tools, copy the lib files from the Procheiron Core package:

```bash
cp -r /path/to/procheiron_core/conformance/generic-vault/.procheiron/lib \
      /your/project/root/.procheiron/lib
```

Required lib files (4 modules):
- `procheiron_resolve.py` — config resolver
- `procheiron_patterns.py` — secret-pattern guard
- `procheiron_paths.py` — path normalisation
- `procheiron_lock.py` — single-writer lock

### Proposing a candidate record

```bash
python3 /your/project/root/memory_propose.py \
  --root /your/project/root \
  --type fact \
  --scope project \
  --profile yourprofilename \
  --subject "Example deployment fact" \
  --statement "Procheiron was initialised for this deployment on 2026-06-12." \
  --source-path "console/CONSOLE.md" \
  --confidence 0.9 \
  --created-by "your-agent-id"
```

This appends one candidate record to `memory/index/memories.jsonl` and one
audit event to `memory/index/audit.jsonl`. Candidate records do NOT require
independent review — only `active` and `validated` records do.

### Promoting to active

Promotion requires an independent reviewer (different `created-by` vs
`reviewed-by`) plus a corroborating audit event. The validator enforces this.

```bash
python3 /your/project/root/memory_promote.py \
  --root /your/project/root \
  --memory-id <id-from-propose-output> \
  --new-status active \
  --reviewer "reviewer-agent-id" \
  --reason "Independently verified against console/CONSOLE.md source" \
  --authorized-by "human-or-task-reference"
```

After promotion, re-validate:

```bash
python3 /your/project/root/validate_minimal.py --root /your/project/root --json
```

The validator will confirm the active record has independent review and a
corroborating `memory_promoted` audit event.

---

## Troubleshooting

| Error | Fix |
|---|---|
| `missing .procheiron/config.yaml` | Re-run init or create the file manually. |
| `CONSOLE.md missing doctrine: agent_neutral` | CONSOLE.md must contain the literal string `agent-neutral`. |
| `CONSOLE.md missing doctrine: human_visible` | CONSOLE.md must contain `human-visible`. |
| `CONSOLE.md missing doctrine: provenance` | CONSOLE.md must contain `provenance`. |
| `CONSOLE.md missing doctrine: propose_not_promote` | CONSOLE.md must contain `propose`, `self-authorize`, and `promotion`. |
| `CONSOLE.md missing doctrine: runtime_constraints_binding` | CONSOLE.md must contain `runtime`, `developer`, and `remain binding`. |
| `missing memory/SCHEMA.md` | Re-run init. |
| `missing schemas/memory_record.schema.json` | Re-run init. |
| `<id>: no provenance (source_paths/source_ids)` | Add at least one `source_path` or `source_id` to the record. |
| `<id>: active record has no reviewed_by` | Active records need a reviewer different from the creator. |
| `<id>: active record self-reviewed by its creator` | Reviewer must be a different actor than `created_by`. |
| `<id>: active record has no corroborating memory_promoted audit event` | Run `memory_promote.py` to create the record — do not write active records by hand. |
| `secret-pattern finding: <filename>` | A secret-like string (API key, private key, etc.) was found. Remove it. |
| `machine-absolute source_path` | Use root-relative paths like `console/CONSOLE.md`, not `/home/user/...`. |

---

## Adding Advanced Governance (Later)

The minimal validator does not require any of these. Add them as your
deployment matures:

| Module | What it provides | Where to start |
|---|---|---|
| L0–L9 authority ladder | Graduated permissions by agent trust level | `console/SELF_ACTION_POLICY.md` |
| Gate registry | Named governance gates with approval requirements | `.procheiron/policy/` |
| Decision ledger | Structured decision records with audit linkage | `console/DECISIONS.md` + `audit.jsonl` decision events |
| Retrieval policy | Controls what agents may read from the commons | `console/RETRIEVAL_POLICY.md` |
| Known-actor registry | Validates `created_by`/`reviewed_by` against declared actors | `.procheiron/profiles/<profile>/lint.json` |
| Agent boot protocol | Standardised agent startup sequence | `console/AGENT_BOOT.md` |

Each module is optional and additive. The minimal validator ignores them. The
full validator (`validate_procheiron2.py`) enforces them when present.

A complete governance-enabled deployment looks like the `conformance/generic-vault`
fixture in the Procheiron Core package. Use it as a reference.

---

## Re-initializing or Force-overwriting

```bash
procheiron init <dir> --profile <name> --force
```

`--force` overwrites every existing non-empty file. Use with care: it will
reset CONSOLE.md and config.yaml to defaults and **empty the JSONL indexes**,
destroying any records in them.
