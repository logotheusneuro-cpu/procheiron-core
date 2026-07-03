# Adopt Procheiron with 5 Files

Procheiron is a governance layer for agent memory: a structured commons that enforces provenance, lifecycle, and independent review so agent-generated claims can be treated as auditable operational truth rather than unchecked output.

The minimal adopter ships in five components. That is all you need for a conformant deployment.

---

## The 5 Components

| # | Component | What it does |
|---|---|---|
| 1 | `console/CONSOLE.md` | Operator boot doc. Defines the governance doctrine: agent-neutral commons, precedence order, memory lifecycle, propose-not-promote rule, and runtime/developer constraints. |
| 2 | `memory/SCHEMA.md` | Human-readable schema narrative. Documents every field, lifecycle status, provenance requirement, and the independent-review rule for active/validated records. |
| 3 | `schemas/memory_record.schema.json` | Machine-readable JSON Schema (Draft 2020-12). The single-record contract consumed by the validator. |
| 4 | `validate_minimal.py` (+ `procheiron_schema.py`) | Stdlib-only conformance validator. Enforces: config resolution, CONSOLE.md doctrine terms, schema presence, record validity, provenance, independent review, corroborating audit events, and secret-pattern absence. |
| 5 | `memory_propose.py` + `memory_promote.py` | Write helpers. `memory_propose.py` appends candidate records (proposal-only, never self-promotes). `memory_promote.py` is the only sanctioned status writer, enforcing independent review and audit events. |

---

## What Is Optional

Advanced governance is a separate, optional module. The minimal 5-file deployment does **not** require:

- The **L0–L9 authority ladder** (graduated permissions by agent trust level)
- A **gate registry** (named governance gates with approval requirements)
- A **decision ledger** (`DECISIONS.md` + `audit.jsonl` decision events)
- A **retrieval policy** (`RETRIEVAL_POLICY.md` controlling what agents can read)
- A **known-actor registry** (`lint.json` with `known_actors`/`known_actor_groups`)

Add these as your deployment matures. The minimal validator explicitly skips them — it enforces only the memory-commons core.

---

## Adoption Steps

1. **Copy the 5 components** into your deployment root.

2. **Create `.procheiron/config.yaml`** with at minimum:

   ```yaml
   version: "0.1"
   profile: <your-profile-name>
   root: .
   paths:
     console: console
     memory: memory
   ```

3. **Bootstrap the index files** (empty but valid JSONL):

   ```bash
   mkdir -p memory/index
   touch memory/index/memories.jsonl
   touch memory/index/audit.jsonl
   ```

4. **Run the validator** to confirm baseline conformance:

   ```bash
   python3 validate_minimal.py --root . --json
   ```

   Expected: `{"status": "PASS", "errors": []}` (zero records is fine on day one).

5. **Propose your first memory record**:

   ```bash
   python3 memory_propose.py \
     --type fact \
     --scope project \
     --profile <your-profile> \
     --subject "Example claim" \
     --statement "This is a candidate memory record for demonstration." \
     --source-path console/CONSOLE.md \
     --confidence 0.9 \
     --created-by agent-id-here
   ```

6. **Promote when reviewed** (requires a different actor as reviewer):

   ```bash
   python3 memory_promote.py \
     --memory-id <id-from-step-5> \
     --new-status active \
     --reviewer reviewer-agent-id \
     --reason "Independently verified against source" \
     --authorized-by human-or-task-reference
   ```

7. **Re-validate** after each promotion cycle. The validator confirms every active/validated record has independent review and a corroborating audit event.

---

## Conformance

A deployment is conformant when `python3 validate_minimal.py --root <vault> --json` returns:

```json
{"status": "PASS", "errors": []}
```

The conformance runner (`conformance/run_conformance.py`) tests this against the `minimal-vault` fixture as part of the project's automated suite.
