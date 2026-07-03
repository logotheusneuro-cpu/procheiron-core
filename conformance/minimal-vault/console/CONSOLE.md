# Procheiron v0.1 — Operator Boot and Governance Primer

## What the Memory Commons Is

Procheiron is an agent-neutral memory commons: a shared, human-visible store of structured facts, decisions, lessons, and procedures that any agent or operator can read, but that only authorised actors can promote to authoritative status. It is designed so that the governance rules travel with the deployment — not with the agents that consume it.

The commons is not tied to any one model, harness, or cloud provider. Any agent that can read files and append JSON lines can participate.

---

## Precedence Order

When claims conflict, this hierarchy resolves them:

1. **Constitution** — the core governance document. Supersedes everything else. Changes require the designated constitutional authority.
2. **Canon** — validated, author-reviewed domain documents and standing decisions. Supersedes memory records.
3. **Active memory** — promoted, independently-reviewed records in `memory/index/memories.jsonl` with status `active`. These are current operational truths.
4. **Candidate memory** — proposed records with status `candidate` or `validated`. Treat as evidence under review, not settled truth.

A lower-tier claim cannot override a higher-tier claim without an explicit, audited supersession.

---

## Memory Lifecycle

Records move through a defined lifecycle. The stages are:

```
draft → candidate → validated → active
                 ↘            ↘
                  superseded / archived / disputed
```

- **draft** — rough proposal, not yet submitted for review.
- **candidate** — submitted via `memory_propose.py`; awaits review. Status `candidate`, write policy `proposal_only`.
- **validated** — reviewed and approved by an actor independent of the creator. Not yet promoted to operational truth.
- **active** — the current authoritative record; requires promotion with `approved_canonical` write policy and an independent reviewer.
- **superseded / archived / disputed** — retired states; kept for audit lineage.

A record's provenance — `source_paths` or `source_ids` — must be present from creation. Durable claims without provenance are refused.

---

## The Propose → Promote Rule

Agents propose; they do not self-authorize promotion.

Any agent may call `memory_propose.py` to append a candidate record. The tool forces status to `candidate` and write_policy to `proposal_only`. No agent may elevate its own proposal. Promotion (candidate → validated → active) requires:

1. A **different actor** than the creator — independent review is mandatory.
2. An **audit event** corroborating the transition (`memory_validated` or `memory_promoted`) in `memory/index/audit.jsonl`.
3. An **authorised-by** reference for active promotions — a human or task authorization, not another agent vote.

This rule exists because agents share deployment context. Without it, a single agent could write, review, and activate its own claims, making the commons indistinguishable from unchecked agent output.

---

## Runtime and Developer Constraints

Runtime constraints and developer-set invariants remain binding regardless of memory status. An active memory record that contradicts a runtime constraint does not override it — the constraint wins until explicitly revised at the constitutional level.

Specifically:
- **runtime** configuration (environment variables, service parameters, infrastructure state) is source of truth for operational conditions; memory records describe what was observed, not what is currently true.
- **developer** policy embedded in the constitution or canon (schema rules, write-policy rules, the self-authorize prohibition) cannot be waived by promoting a contrary memory record.
- Both **remain binding** unless the governing authority amends them through the sanctioned process.

---

## Files in a Minimal Deployment

| File | Role |
|---|---|
| `console/CONSOLE.md` | This document — operator boot + doctrine |
| `memory/SCHEMA.md` | Human-readable memory-record schema |
| `schemas/memory_record.schema.json` | Machine-readable schema (JSON Schema Draft 2020-12) |
| `validate_minimal.py` | Minimal conformance validator (stdlib-only) |
| `memory_propose.py` + `memory_promote.py` | Propose-and-promote helper scripts |

Advanced governance (L0–L9 authority ladder, gate registry, decision ledger, retrieval policy) is an optional module. The five files above are sufficient for a conformant deployment.
