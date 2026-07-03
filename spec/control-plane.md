# Procheiron Control Plane Spec v0.1-draft

Status: proposal-only draft skeleton.
Normative target: `procheiron-core` v0.1 control-plane contract.

## 1. Purpose

The control plane governs how proposals become approved actions without turning evidence into authority. Its job is to record, validate, and constrain authority-bearing transitions. It does not grant authority by existing.

## 2. Core invariant

A compliant control plane MUST preserve this invariant:

> Validators may block; validators do not grant.

Evidence, retrieval, health, prior success, clean git state, candidate memory, and proposal artifacts are all non-authority unless paired with an explicit approval under the deployment's authority model.

## 3. Minimal action lifecycle

A full deployment SHOULD model authority-bearing work as:

1. `proposal` — what is requested, why, source basis, exact scope
2. `review` — role-separated technical/operational/authority review as required
3. `decision` — explicit approval or rejection by the correct authority
4. `audit_event` — append-only record of transition, actor, authorization, scope, and evidence
5. `execution` — exact approved action only
6. `postflight` — verification against the approved scope
7. `supersession` or `rollback` — explicit, separately authorized where required

A minimal v0.1 adopter MAY omit runtime execution support entirely and still be compliant if it preserves proposal/review/decision/audit semantics for memory promotion.

## 4. One-ledger discipline

The control plane SHOULD use one operative ledger story per deployment. For v0.1, the recommended shape is:

- `DECISIONS.md` or equivalent human-readable decision log for constitutional/batch/canonical approvals
- `index/audit.jsonl` or equivalent append-only structured audit log for status transitions and executed actions

Deployments SHOULD NOT create a parallel approval ledger unless it directly extends this operative ledger and has a separately approved need. A separate ceremony lane that duplicates record+validate without gating a real authorized action is noncompliant with the v0.1 design intent.

## 5. Approval record minimums

When a deployment records an approval, the record SHOULD include:

- request or proposal id
- request version
- gate or action class
- required authority level or equivalent
- granted authority level or equivalent
- proposer
- drafter
- reviewers required
- reviewers completed
- approver
- approved scope
- approved paths
- approved commands or payloads where applicable
- approved recipients/resources where applicable
- executor binding where applicable
- expiration or single-use terms
- source artifacts and hashes where applicable
- explicit non-authority clauses acknowledged

## 6. Executor abstraction

Core MUST NOT require git. Core defines a preservation/execution interface; profiles bind concrete executors.

Possible profile-bound executors include:

- filesystem draft writer
- git commit/push preservation
- local script runner
- service manager
- MCP tool
- no executor / proposal-only mode

If git is used, commit and push are separate authority-bearing actions. If another executor is used, the deployment MUST define equivalent scope, preflight, execution, and postflight checks.

## 7. Runtime roots and gates

Runtime roots are absent by default. Creating, populating, wiring, or scheduling a runtime root is a mutation and requires explicit approval. Documentation-only inert scaffolds carry no operative authority.

Advanced deployments MAY define gates for memory promotion, policy edits, runtime mutation, production repair, external action, or self-action adoption. Minimal deployments MAY omit those gates if they do not perform those actions.

## 8. Invalid transitions

A compliant control plane MUST reject or flag these transitions:

- proposal to implementation without approval
- retrieval hit to authority
- health ok to repair/mutation
- candidate memory to active without independent review/approval
- no-send packet to send
- sandbox success to production repair
- commit approval to push approval
- one approval to adjacent action
- actor approving its own expanded authority
- failed action to retry/rollback without retry/rollback authority

## 9. Memory current-guidance transition as the reference control action

The v0.1 reference action is memory promotion or validation into current guidance because it is useful, local,
and bounded. A compliant deployment SHOULD prove:

1. a candidate can be proposed through the sanctioned write path
2. schema/provenance validation can block bad candidates
3. independent review can recommend validation or promotion
4. explicit authority is required before a record becomes `validated` or `active`
5. audit events can reconstruct the transition

## 10. External actions

External sends/writes are forbidden by default. A deployment that supports external action MUST require exact recipient/resource, payload, tool/API/channel, scope, expiration, approver, reviewer roles, and rollback/retraction plan.

No-send, dry-run, and draft artifacts never authorize external action.
