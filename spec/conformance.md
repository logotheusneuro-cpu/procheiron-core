# Procheiron Conformance Spec

```
version: 0.1
status: NORMATIVE (draft)
spec_set: procheiron-core
note: MUST clauses are derived from what the reference validator, policy engine, and conformance
      suite actually check. Clauses marked [UNCERTAIN] await further verification.
```

---

## What "Procheiron-compliant" means

A deployment is Procheiron-compliant for the tier it declares and passes.

Tier 1: `minimal-memory-commons` — the five-file adopter profile. It proves the memory-commons core:
configuration, a compact console doctrine file, memory schema, memory records, provenance, lifecycle status,
sensitivity, independent review for current-guidance records, and corroborating audit events.

Tier 2: `full-governance-profile` — the full Procheiron governance profile. It adds console-file split,
profile lint/weld detection, retrieval/no-index policy, decision ledger, runtime-root policy, named authority
model or equivalent, and protected governance surfaces.

A deployment that passes only Tier 1 is compliant as a minimal memory-commons adopter, not as a full governance
profile. A deployment that passes a fixture is fixture-proven only. v1.0 requires a second real deployment,
not merely the stored generic fixture.

---

## C1 — Configuration and token resolution

**C1.1 MUST (all tiers):** The deployment provides `{root}/.procheiron/config.yaml` declaring at minimum:
`version`, `profile`, `root`, `paths.console`, and `paths.memory`.

**C1.2 MUST (full-governance-profile):** The deployment additionally declares every path token used by its
Core/profile documents, including `paths.sources` and `paths.outputs` when those surfaces are present.

**C1.3 MUST (all tiers):** Every `{paths.*}` token used by the deployment's active Core/profile/conformance
documents resolves to a concrete path via `config.yaml`. Unresolvable tokens in guards, protected surfaces,
canonical paths, or conformance rules fail closed.

**C1.4 MUST (full-governance-profile):** The active deployment profile exists under
`{root}/.procheiron/profiles/<name>/` and contains `profile.md` and `lint.json`.

**C1.5 MUST (full-governance-profile):** `lint.json` specifies a weld-detection pass covering the declared
Core documents. Relaxing a lint rule requires a gate-class change recorded in the deployment's decision ledger.

---

## C2 — Canonical surface completeness

**C2.1 MUST (minimal-memory-commons):** The deployment provides a console doctrine file at
`{paths.console}/CONSOLE.md` or an equivalent tier-declared console document containing the agent-neutral
non-authority doctrine.

**C2.2 MUST (full-governance-profile):** The following files exist under `{paths.console}/`:
`PROCHEIRON.md`, `PRECEDENCE.md`, `AGENT_BOOT.md`, `SOURCE_OF_TRUTH.md`, `AGENT_REGISTRY.md`, `DECISIONS.md`.
`RETRIEVAL_POLICY.md`, `BLOCKERS.md`, and `ACTIVE_PROJECTS.md` are REQUIRED when the deployment exposes
retrieval, blockers, or active-project governance as separate surfaces.

**C2.3 MUST (all tiers):** The deployment provides `SCHEMA.md` and a machine-readable memory record schema at
the tier-declared schema path.

**C2.4 MUST (all tiers):** `{paths.memory}/index/memories.jsonl` exists (may be empty) and is valid JSONL —
UTF-8, one JSON object per non-empty line.

**C2.5 MUST (all tiers with current-guidance records):** An audit log exists at the tier-declared audit path
(default: `{paths.memory}/index/audit.jsonl`) and is valid JSONL.

**C2.6 MUST (full-governance-profile):** `{paths.sources}/` exists as a directory root.

---

## C3 — Core documents are weld-clean

**C3.1 MUST:** No Core document under `{paths.console}/` or `{paths.memory}/` contains a
literal machine-absolute path for any surface that is represented by a `{paths.*}` token in
`config.yaml`. The profile's `lint.json` weld-detection scan must pass with exit 0.

**C3.2 MUST:** No Core document contains a literal deployment-specific identifier (named agents,
named persons, git remote URLs, systemd unit names, or cron schedules) that belongs in the
profile. VERIFIED (against the validator + conformance fixtures): enforcement is
two-layered — (a) machine-absolute paths are caught automatically by
`forbid_absolute_paths_in_core_docs`; (b) named-string welds are caught when the profile
enumerates them in `lint.json` `forbidden_core_doc_literals`. Layer (b) is **profile-declared,
not automatic** — a deployment MUST list its own named identifiers there for them to be enforced.
Proven by the `broken/weld-vault` fixture (a profile literal welded into a Core doc →
`deployment weld in Core doc`).

---

## C4 — Memory records are schema-valid with provenance

**C4.1 MUST:** Every record in `{paths.memory}/index/memories.jsonl` passes the tier-declared memory record
schema with no error-severity findings. Warning-severity findings may be logged without failing compliance.

**C4.2 MUST:** Every record with `status: active` or `status: validated` has a non-null
`reviewed_by` field that differs from `created_by`. Self-review is not permitted for
active or validated records.

**C4.3 MUST:** Every record with `status: active` has `write_policy` set to
`approved_canonical` or `system_generated`, not `proposal_only`.

**C4.4 MUST:** Every durable record (status not `draft`) cites at least one `source_path`
or `source_id`, unless the record is explicitly marked as bootstrap policy
(`write_policy: system_generated` with a note).

**C4.5 MUST:** Secrets do not appear in any memory record. The validator's secret-pattern
check must produce zero matches.

---

## C5 — Active/validated records have independent review and corroborating audit

**C5.1 MUST:** Every record with `status: active` (and every `status: validated` record) has a
corroborating promotion/validation event in `{paths.memory}/index/audit.jsonl` that references the
record's `id` and was written by an actor other than the record's `created_by`. VERIFIED
the validator cross-checks audit.jsonl for EVERY active/validated record by content,
independent of how the record was written — it is a record-state check, not a tool-provenance
check. Proven by `broken/active-without-review-vault` (an active record whose audit event is
removed → `no corroborating promotion audit event`) and `broken/self-reviewed-vault`
(reviewer == creator → `self-reviewed by its creator`).

**C5.2 MUST:** No `active` or `validated` record becomes current guidance without independent reviewer or
authorizer evidence in the tier-declared audit log. If the deployment uses named gates, this maps to the
memory-promotion/current-guidance gate; if it uses a minimal model, the audit event must still prove reviewer
independence and authority equivalent for the tier.

**C5.3 MUST (full-governance-profile):** Supersession is explicit and paired: every ID listed in a record's
`supersedes` array has a matching structured supersession/audit entry, and the superseded record's status is
`superseded` once the sanctioned status workflow runs. Minimal deployments MUST at least reject ambiguous prose
supersession that claims replacement without structured lineage.

---

## C6 — No-index and secret rules enforced

**C6.1 MUST (retrieval-enabled/full-governance-profile):** The active profile's retrieval policy is present and
contains a no-index glob list covering at minimum these doctrine classes: runtime state and operational JSON,
secrets and credentials, logs and transcripts, repository internals, backups, raw captured payloads, binaries
and media.

**C6.2 MUST (retrieval-enabled deployments):** No retrieval result, search cache, or snippet store includes
content from any path matching the no-index glob list. No-index rules are applied before reading file contents.

**C6.3 MUST (all tiers):** Generated retrieval artifacts, if any, are not written into canonical governance or
memory truth unless the deployment explicitly declares them canonical and validates that declaration.

---

## C7 — Authority decisions are gate-checked

**C7.1 MUST (full-governance-profile):** Any action at the deployment's canonical-mutation or memory-current-
guidance authority level has a corresponding decision/audit record in the deployment's operative ledger.
For the reference profile this is an authorization record in `{paths.console}/DECISIONS.md`; other deployments
may use an equivalent ledger if their profile declares it.

**C7.2 MUST:** No canonical governance file is edited without an approval record at the authority level the
deployment declares for canonical mutation.

**C7.3 MUST:** No memory record's status is elevated to `active` or `validated` by the same actor that created
it, verifiable from `created_by`, `reviewed_by`, and the audit event.

**C7.4 MUST:** The non-authority invariants and invalid-transition list are enforced by the authority policy.
For a full-governance profile (e.g. the reference deployment), those sources are `governance.md §7`, `control-plane.md §8`, and
`policy_data.json` `invalid_transitions`. The encoded list must be enforced by the production policy backend;
optional policy engines such as OPA may be used as CI cross-checks but are not required by Core.

---

## C8 — Runtime roots absent unless authorized

**C8.1 MUST (runtime-root-enabled/full-governance-profile):** Runtime roots are absent by default. Any runtime
root that exists must have an explicit authorization record with pin or validity conditions.

**C8.2 MUST (profiles with authorized-present inert scaffolds):** An authorized-present inert scaffold carries
no operative authority. Its pin conditions must remain satisfied; if any pin condition fails, the root becomes
a stop condition.

**C8.3 NOTE:** A profile's `{paths.runtime_root}/approvals` scaffold is a profile-specific authorized-present
example, not a universal Core requirement.

---

---

## Versioning

This spec is **v0.1**. v1.0 is earned only when a second *real* deployment (not a fixture) passes
conformance — not by a fixture pass, a single deployment, or authority approval alone.
