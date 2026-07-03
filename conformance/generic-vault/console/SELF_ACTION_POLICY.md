# SELF_ACTION_POLICY.md

Status: adopted canonical governance. Explicit constitutional-authority L9 adoption 2026-06-04; parameterized re-promotion 2026-06-11. Both authorization records live in `{paths.console}/DECISIONS.md`. Canonical path: `{root}/{paths.console}/SELF_ACTION_POLICY.md`.

Scope: Procheiron self-action governance, as bound to the active deployment profile, for agents, adapters, runtimes, scheduled jobs, validators, proposal systems, and future action executors.

Core sentence: Procheiron may be self-evolving, but it is not self-authorizing.

## 1. Purpose

This policy defines how Procheiron-governed agents may propose, review, approve, and execute future self-action capabilities without laundering evidence into authority.

It exists to prevent a dangerous category error: an agent observes a healthy system, retrieves relevant memory, drafts a good proposal, or succeeds once, then treats that evidence as permission to mutate canonical truth, runtime state, production systems, git history, memory records, or external channels.

This policy permits inspectable evolution by proposal, review, and explicit approval. It forbids silent authority expansion.

## 2. Scope

This policy applies to:

- Procheiron canonical governance files under `{paths.console}/`.
- Structured memory records and indexes under `{paths.memory}/`.
- Agent workspaces and draft roots when their outputs affect Procheiron governance.
- Runtime Procheiron surfaces under `{paths.runtime_root}/`.
- Runtime state surfaces under the host runtime's runtime-state root.
- Preservation-executor operations for Procheiron-governed repositories or artifact stores, including profile-bound git staging, commits, pushes, tags, merges, and related operations when a deployment chooses git as its preservation executor.
- Scheduled jobs, validators, health checks, proposal engines, and future executors that can affect Procheiron or the host runtime's behavior.
- External sends and writes including email, Telegram, Slack, Discord, Teams, webhooks, calendar invites, CRM/customer-system writes, issue/PR/comment creation, content publishing, paid/spend actions, or any third-party API write.

This policy does not override stronger system, developer, runtime, security, profile, or active-task restrictions. If another binding rule is narrower, the narrower rule wins.

## 3. Non-authority principles

The following are evidence only and never grant authority by themselves:

1. Health status.
   - `health ok`, `errors=0`, or `warnings=0` does not grant mutation, repair, send, promotion, commit, push, adoption, or authority expansion.
2. Retrieved context.
   - Retrieved memory, search results, wiki snippets, prior reports, and source excerpts are evidence, not permission.
3. Prior success.
   - A previous safe run, send, repair, promotion, commit, or mutation does not authorize future repetition.
4. Emergency labels.
   - `urgent`, `emergency`, `critical`, `prod down`, or similar language does not bypass authority.
5. Proposal artifacts.
   - Proposal, synthesis, review, draft, no-send, and readiness artifacts do not authorize implementation.
6. Clean preservation-executor state.
   - A clean preservation executor state — including a clean repo, `ahead/behind 0/0`, staged count `0`, a synchronized destination, a clean artifact store, or passing validator — is never authority to act.
7. No-send packets.
   - A no-send or dry-run packet never authorizes a real send.
8. Sandbox success.
   - A successful sandbox repair never authorizes production repair.
9. Runtime metadata.
   - Metadata checks on runtime files do not authorize content parsing or mutation.
10. Role title similarity.
   - Local synonyms, overlapping responsibilities, or informal role titles do not substitute for exact reviewer/approver roles.
11. Agent identity.
   - A capable agent, trusted agent, or senior operator role does not gain authority outside the current task and policy.

No actor may approve its own expanded authority.

## 4. Authority ladder

Authority levels are cumulative only when explicitly stated. A higher-risk action must satisfy its own gate; it cannot inherit approval from adjacent lower-risk work.

| Level | Name | Meaning | Examples | Authorizes | Never authorizes |
| --- | --- | --- | --- | --- | --- |
| L0 | Observation | Read-only inspection, measurement, classification, summary. | Preservation-executor status, health summary, metadata-only runtime STATE check, file read. | Observation and reporting only. | Mutation, approval, send, preservation, propagation, promotion, adoption. |
| L1 | Proposal / Draft | Create recommendations, drafts, packets, review artifacts, or plans in an authorized draft/output root. | Reviewer-agent output proposal, no-send draft schema, adoption plan. | Drafting only in allowed root. | Canonical edit, runtime root, production change, external send, preservation-executor mutation unless separately approved. |
| L2 | Reserved Low-Risk Local Preparation | Reserved for future explicitly defined noncanonical preparation. | Formatting or ephemeral local preparation if later defined. | Nothing by default. | Canonical/runtime/production/external/preservation-executor/memory action. |
| L3 | Reversible Sandbox-Only Mutation | Exact-path reversible mutation in an approved sandbox, with no production or runtime effect. | Future repair sandbox fixture under approved sandbox root. | Approved sandbox-only mutation. | Production repair, runtime mutation, canonical edit, external action. |
| L4 | Canonical Mutation Approval | Approval for an exact canonical edit after provenance, review, and scope validation. | Future approved edit to a canonical governance file or active memory record. | Exact named canonical mutation only. | Runtime mutation, production repair, external action, authority expansion. |
| L5 | Preservation Record Approval | Approval to create an exact preservation record from an already reviewed exact-scope package using the deployment profile's bound preservation executor. | Seal one preserved proposal artifact as a filesystem manifest, content-addressed archive, git commit, or equivalent after prepared-set equality. | Exact preservation record only. | Propagation/publication, broad preparation/staging, adjacent artifact inclusion, canonical adoption by implication. |
| L6 | Propagation Approval | Approval to propagate a reviewed preservation record to a named destination through the deployment profile's bound preservation executor. | Push an exact reviewed git commit to a named remote/branch, publish an exact content-addressed archive, or sync an exact preserved artifact to a named destination. | Exact propagation only, provided no unrelated unpropagated records are included unless separately approved. | New preservation record, force/overwrite propagation, tags, merges, destination broadening, unrelated artifact smuggling. |
| L7 | Escalated Review / No-Send Adjacent Review | High-friction review for no-send or external-adjacent packets. | Phase 15C `draft_schema_only` no-send packet state. | Review acceptance of no-send/dry-run packet only. | Real send, external write, runtime mutation, production repair, canonical adoption. |
| L8 | Runtime / Production Mutation Approval | Approval for exact runtime or production mutation after system owner + authority review. | Runtime STATE mutation, production repair, rollback execution if named. | Exact runtime/production action and rollback/checkpoint behavior named in approval. | Authority expansion, canonical self-action adoption, external action unless separately approved. |
| L9 | Constitutional Authority Expansion / Self-Action Adoption | Approval to expand authority classes, alter the ladder, canonize self-action policy, or adopt `SELF_ACTION_POLICY.md`. | Canonical adoption of this policy; change L0-L9 semantics; approve new self-action root categories. | Only the exact constitutional adoption/authority expansion named by the constitutional authority. | Self-approval, silent adoption, runtime/production/external/preservation-executor/memory action unless separately and explicitly included. |

## 5. Reviewer-role registry

Role names are exact. Synonyms do not substitute for these roles. A person or agent may hold more than one role only when the gate explicitly allows it and conflict-of-interest rules are satisfied.

| Role | Purpose | Allowed scope | Forbidden actions | Approval power |
| --- | --- | --- | --- | --- |
| `proposer` | Identifies a need, risk, draft, repair, policy, or action. | Draft request, problem statement, proposal material. | May not approve own proposal, execute own expanded authority, or treat proposal as permission. | No approval power unless separately assigned for a different non-conflicted gate. |
| `drafter` | Writes draft/proposal artifacts. | Authorized draft/output roots. | May not make draft canonical, mutate runtime, or send externally. | No approval power for the drafted artifact. |
| `technical_reviewer` | Reviews implementation feasibility, schema, commands, path safety, reversibility, and technical risk. | Technical correctness and tool/path constraints. | May not approve business/external impact or own implementation. | Review/block; approval only if gate names it. |
| `operations_reviewer` | Reviews operational risk, runbook impact, scheduler/process consequences, and human handoff clarity. | Operational correctness and failure modes. | May not approve authority expansion or own operational automation. | Review/block; approval only if gate names it. |
| `business_owner` | Reviews customer, revenue, brand, legal, financial, or relationship impact. | Business-facing or external-action consequences. | May not approve technical safety alone or agent authority expansion. | Approval for named business/customer/external impact if gate requires it. |
| `system_owner` | Reviews production/runtime/system ownership and blast radius. | Runtime, production, infrastructure, system state. | May not approve own expanded authority or external/business sends alone. | Approval for named runtime/production action if gate requires it. |
| `memory_reviewer_curator` | Reviews memory provenance, schema validity, lifecycle status, supersession, and promotion eligibility. | `{paths.memory}` candidate/validated/active memory transitions. | May not promote own generated memory without independent review. | Memory promotion approval only if gate requires it. |
| `canonical_governance_reviewer` | Reviews canonical governance text, precedence, source-of-truth fit, and canonical edit safety. | `{paths.console}/` and other canonical governance surfaces. | May not adopt constitutional authority alone. | Review/block; L4 approval if gate requires it. |
| `authority_reviewer` | Reviews whether the requested action matches the authority ladder and gate constraints. | Authority classification, invalid transitions, self-approval risk. | May not approve own expanded authority or replace the constitutional authority for L9. | Review/block; approval where named except L9 final authority. |
| `independent_adversarial_reviewer` | Attempts to break proposals before preservation, adoption, or implementation. | Self-authorization loopholes, gate ambiguity, role conflation, authority laundering. | May not implement fixes during review unless separately authorized. | Review/block; no final adoption authority. |
| `constitutional_reviewer_authority` | Holds final constitutional authority for Procheiron self-action adoption or authority expansion. | L9 decisions only: adoption, ladder changes, new authority classes, constitution changes. | Cannot be replaced by agent consensus, health, retrieval, prior success, or local title. | Final L9 approval when explicit, written, exact-scope, and single-use. |
| `executor` | Performs an approved action after all gates are satisfied. | Only the exact approved path/payload/command/mutation/send. | May not approve own execution, broaden scope, retry failed action, or include adjacent surfaces. | Execute only. |
| `auditor` | Reviews completed action against approval, logs, artifacts, and side effects. | Post-action verification and discrepancy reporting. | May not retroactively approve unauthorized action. | Audit/report only. |

## 6. Gate registry

This policy defines gates. It does not implement them. Future implementation requires separate approval and separate runtime roots, if any.

| Gate ID | Source phase | Required level(s) | Required reviewer roles | Required approver role | Future runtime root if later approved | Current status |
| --- | --- | --- | --- | --- | --- | --- |
| `approval_ledger_gate` | 15B | L1 to propose; higher per downstream action | `operations_reviewer`, `authority_reviewer` | Depends on downstream action | `{paths.runtime_root}/approvals` | Inert scaffold exists under §9.1; no operative ledger, records, validators, or wiring. |
| `no_send_alert_packet_gate` | 15C | L7 for proposal-only `draft_schema_only`; real send requires external action gate | `operations_reviewer`, `authority_reviewer` | No send approver at no-send stage | `{paths.runtime_root}/alert_packets` only if later approved | Proposed only; no packet/root exists. |
| `preservation_executor_gate` | 15D | L5 preservation record; L6 propagation | `technical_reviewer`, `authority_reviewer`, executor owner/system owner as applicable | Exact preservation/propagation approver named by human | `{paths.runtime_root}/preservation_plans` only if later approved | Proposed only; no executor/root exists. Profile may bind git as one executor implementation. |
| `memory_promotion_gate` | 15E | L4 for active/canonical memory adoption | `memory_reviewer_curator`, `authority_reviewer` | Memory curator/authorized human | `{paths.runtime_root}/memory_promotion` only if later approved | Proposed only; no memory mutation. |
| `canonical_policy_edit_gate` | 15F | L4 for canonical edit; L9 if authority expansion | `canonical_governance_reviewer`, `authority_reviewer` | Authorized canonical approver; the constitutional authority for L9 | `{paths.runtime_root}/policy_edit` only if later approved | Proposed only; no canonical edit. |
| `repair_sandbox_gate` | 15G | L3 for sandbox-only repair; L8 if runtime/production coupling; L9 if authority expansion | `technical_reviewer`, `operations_reviewer`, `authority_reviewer` | Human/system owner for exact sandbox scope | `{paths.runtime_root}/repair_sandbox` only if later approved | Proposed only; no sandbox/root exists. |
| `runtime_mutation_gate` | 15H | L8 for runtime mutation; separate content-read gate if runtime STATE content is involved | `system_owner`, `technical_reviewer`, `authority_reviewer` | `system_owner` plus `authority_reviewer`; the constitutional authority if L9 | `{paths.runtime_root}/runtime_mutation` only if later approved | Proposed only; no runtime mutation. |
| `production_repair_gate` | 15I | L8 for production repair; L9 for authority expansion | `technical_reviewer`, `operations_reviewer`, `business_owner` where applicable, `system_owner`, `authority_reviewer` | System/business owner plus authority reviewer | `{paths.runtime_root}/production_repair` only if later approved | Proposed only; no production repair. |
| `external_action_send_gate` | 15J | Explicit human external approval; L5/L6/L8/L9 if coupled to preservation, runtime, or authority expansion | `business_owner`, `operations_reviewer`, `technical_reviewer`, `authority_reviewer` | Human/business owner for exact recipient/resource/payload | `{paths.runtime_root}/external_action` and `/external_send` only if later approved | Proposed only; no send/write. |
| `self_action_policy_adoption_gate` | 15K/15L/normalization/L9 plan | L9 only for canonical adoption or authority expansion | `independent_adversarial_reviewer`, `canonical_governance_reviewer`, `system_owner`, `authority_reviewer` | `constitutional_reviewer_authority` only | `{paths.runtime_root}/self_action_policy` only if later approved | Proposed draft only unless L9 adoption occurs. |

## 7. Approval ledger model

This policy defines the minimum required structure for future approval records. It does not create an approval ledger, approval file, or runtime root.

Any future approval ledger, if separately approved, must preserve at minimum:

- `approval_id`
- `request_id`
- `request_version`
- `gate_id`
- `authority_level_required`
- `authority_level_granted`
- `requested_by`
- `proposer`
- `drafter`
- `reviewers_required`
- `reviewers_completed`
- `approver`
- `approval_scope`
- `approved_paths`
- `approved_commands`
- `approved_payloads`
- `approved_recipients`
- `approved_runtime_roots`
- `approved_preservation_executor`
- `approved_preservation_operation`
- `approved_preservation_record_id`
- `approved_preservation_destination`
- `approved_profile_executor_fields`
- `expires_at`
- `single_use`
- `status`
- `created_at`
- `approved_at`
- `used_at`
- `supersedes`
- `source_artifacts`
- `source_hashes`
- `non_authority_clauses_acknowledged`
- `forbidden_shortcuts_acknowledged`

Allowed approval lifecycle statuses must be explicit. A future ledger proposal must define and validate the exact status set before implementation.

Approval records must be immutable after use except by explicit supersession record. Failed, expired, vague, or mismatched approvals must not be repaired silently.

## 8. Invalid transitions

The following transitions are invalid:

1. `proposal -> implementation` without explicit implementation authority.
2. `draft -> canonical` without exact canonical creation approval.
3. `retrieval hit -> authority`.
4. `health ok -> authority`.
5. `prior success -> future authority`.
6. `emergency label -> authority bypass`.
7. `same actor proposes and approves own expanded authority`.
8. `reviewer-role synonym -> required reviewer role`.
9. `no-send packet -> external send`.
10. `memory candidate -> active memory` without memory promotion approval.
11. `canonical patch proposal -> canonical edit` without canonical edit approval.
12. `sandbox repair -> production repair` without production repair approval.
13. `runtime metadata check -> runtime content parse` without content-read authority.
14. `runtime metadata check -> runtime mutation`.
15. `production repair -> external action` without external action approval.
16. `external action approval -> bulk send` unless bulk scope is explicit.
17. `single-send approval -> recurring send`.
18. `prepared artifact set -> preservation record` without prepared-set equality and L5 preservation approval.
19. `L5 preservation approval -> propagation` without L6 propagation approval.
20. `propagation approval -> force/overwrite/tag/merge/destination broadening` unless the exact action is named.
21. `failed action -> automatic retry/rollback` without retry/rollback approval.
22. `runtime root absence -> permission to create root`.
23. `clean protected surfaces -> permission to mutate protected surfaces`.
24. `agent capability -> agent authority`.
25. `constitutional-authority approval for one gate -> approval for adjacent gates` unless explicitly named.
26. `L9 adoption of policy -> implementation of gates` without separate implementation approval.

## 9. Runtime root policy

Runtime roots are absent by default and must remain absent unless explicitly approved by the relevant gate.

The following roots are forbidden until separately approved:

- `{paths.runtime_root}/execution_logs`
- `{paths.runtime_root}/preservation_plans`
- `{paths.runtime_root}/memory_promotion`
- `{paths.runtime_root}/policy_edit`
- `{paths.runtime_root}/repair_sandbox`
- `{paths.runtime_root}/runtime_mutation`
- `{paths.runtime_root}/production_repair`
- `{paths.runtime_root}/external_action`
- `{paths.runtime_root}/external_send`
- `{paths.runtime_root}/self_action_policy`
- `{paths.runtime_root}/proposals`
- `{paths.runtime_root}/rollback_records`
- `{paths.runtime_root}/rollback`
- `{paths.runtime_root}/alert_packets`
- `{paths.runtime_root}/cache`
- `{paths.runtime_root}/vector`
- `{paths.runtime_root}/embedding`
- `{paths.runtime_root}/checkpoints`

### 9.1 Authorized runtime roots (pinned, inert exceptions)

A runtime root that has been explicitly approved to EXIST is recorded here. An
authorized root is treated as expected-present ONLY while every pin condition
below holds. If any pin condition fails, the root immediately reverts to a
forbidden-root stop condition pending investigation and fresh approval.

Authorization to EXIST is not authorization to ACT. An authorized-present root
carries no operative authority. Populating or wiring it is a separate new gate.

- `{paths.runtime_root}/approvals`
  - Authorized by: single-use L8 approval `apr_20260604T234442Z_approval_ledger_option_a_scaffold`, approved 2026-06-04T23:44:42Z.
  - State: inert Option A scaffold — empty `records/`, `transitions/`, `index/`; documentation-only `README.md`.
  - Pin conditions (ALL required for expected-present):
    1. `approvals/README.md` SHA256 == `9f150a1b5acee9ba1ab34bd846b16e935a7f8d0c8296eaa87e1cb9680a818fdb` (or an explicitly approved successor SHA recorded here);
    2. `records/`, `transitions/`, `index/` remain empty;
    3. no JSON/JSONL files, validators, scripts, services, timers, or wiring exist under `approvals/`.
  - Revert: if any pin condition fails, `approvals/` is no longer authorized-present and becomes a forbidden-root stop condition.
  - Provenance: scaffold execution verification report SHA256 `41c2d59235e8588ab22837103ae8ee095944849ea1be10da7aeae958deaba2c5`.

Creation of a runtime root is itself a mutation and requires explicit approval. A policy, proposal, outline, or passing health check does not create that approval.

## 10. Runtime STATE policy

Runtime STATE path:

The host runtime's canonical runtime-state file, located via the deployment profile's runtime-state root.

Default access is metadata-only unless a task explicitly authorizes content read or mutation.

Allowed metadata-only fields:

- existence
- size
- mtime
- SHA256

Content parsing, summarization, dumping, mutation, migration, repair, deletion, or copying requires explicit authority matched to the relevant gate.

Runtime STATE content must never be parsed merely to satisfy curiosity, improve a report, or confirm an inference if the active task forbids it.

## 11. Memory promotion policy

Memory records are governed by `{paths.memory}/README.md` and `{paths.memory}/SCHEMA.md`.

Default memory rules:

- `active` and `validated` records may guide work.
- `candidate` and `draft` records are proposal/evidence only.
- `disputed`, `superseded`, and `archived` records are historical unless explicitly requested.
- Retrieved memory is evidence, not authority.
- Agent-generated proposals must not set themselves to `active`.
- Active memory promotion requires authority outside the proposing agent.

No self-action policy, proposal, review, health result, or retrieval result authorizes `{paths.memory}/index/*.jsonl` edits or `{paths.memory}/evolution/proposals/*` creation unless separately approved.

## 12. Canonical governance edit policy

Canonical governance files include, at minimum:

- `{paths.console}/PROCHEIRON.md`
- `{paths.console}/PRECEDENCE.md`
- `{paths.console}/SOURCE_OF_TRUTH.md`
- `{paths.console}/AGENT_BOOT.md`
- `{paths.console}/AGENT_REGISTRY.md`
- `{paths.console}/RETRIEVAL_POLICY.md`
- `{paths.console}/SELF_ACTION_POLICY.md`
- `{paths.memory}/README.md`
- `{paths.memory}/SCHEMA.md`
- `{paths.memory}/index/*.jsonl`
- `{root}/.procheiron/config.yaml` — binds every path token, the active profile, and through it the constitutional-authority mapping
- the active deployment profile's `profile.md` and `lint.json` under `{root}/.procheiron/profiles/` — bind abstract roles (including the constitutional authority) to concrete identities and define the weld-detection lint

Profile lint definitions are gate-class surfaces: relaxing or removing a lint check is a canonical governance edit (L4 minimum) and must be recorded in `{paths.console}/DECISIONS.md` before it takes effect.

Canonical edits require exact path, source basis, authority level, reviewer role separation, post-write verification, and separate L5/L6 preservation-executor authority where applicable.

Draft artifacts in the reviewer agent's authorized draft roots (its agent workspace outputs or task-approved output roots) are not canonical governance. They may propose canonical content but do not become canonical by preservation.

## 13. Preservation executor policy

Preservation-executor operations are authority-bearing actions. A preservation executor is a deployment-profile-bound mechanism for preparing, sealing, recording, propagating, or publishing approved artifacts. Examples include a filesystem manifest, a content-addressed archive, a git commit/push workflow, a package publish step, or a no-executor proposal-only mode. Core does not require git.

Default: no preparation, staging, sealing, preservation record creation, propagation, publication, tag, merge, reset, checkout repair, force/overwrite propagation, or broad executor operation unless explicitly authorized.

Exact-scope preservation requirements:

1. Fresh preflight proves the active executor binding, executor state, pending/prepared set, target artifact hash, protected absences, health, action_queue, and forbidden roots.
2. If the executor has a local/remote or source/destination relationship, preflight must prove no unrelated unpropagated records would ride along before any L6 propagation.
3. Prepare only the approved exact path, payload, or artifact set.
4. Immediately verify prepared-set equality using the executor's profile-declared comparison method.
5. Create an L5 preservation record only if the prepared set equals the approved set exactly.
6. Propagate only if L6 propagation approval is explicit and the destination/scope is exact.
7. Postflight must verify preservation record identity, destination parity/status when propagation occurred, clean prepared/pending state, target artifact clean, protected files absent/clean, and runtime STATE content unparsed.

The active deployment profile binds the concrete preservation executor and its enforcement fields. For a git-bound profile: L5 maps to an exact commit after staged-path equality, and L6 maps to an exact push to a named remote/branch, with branch, remote, staged count, HEAD, ahead/behind, commit hash, tags, merges, and force push as profile enforcement fields, not Core requirements.

The profile's bulk preservation helper, `git add -A`, `git add .`, wildcards, broad directory adds, `git commit -a`, or equivalent broad executor operations are forbidden for exact-path governance preservation unless a later policy explicitly authorizes them for a different class of work.

## 14. Production repair policy

Production repair is not authorized by this policy alone.

A production repair requires, at minimum:

- exact target path/system/resource
- evidence of failure
- business/system owner approval where applicable
- technical review
- authority review
- blast-radius statement
- rollback plan
- sandbox evidence where required
- runtime/production mutation gate if runtime or production state is touched
- external action gate if any customer/system/external write occurs

Health ok, sandbox success, prior successful repair, or emergency wording does not grant production repair authority.

## 15. External action/send policy

External action is any message, write, publish, API mutation, invite, customer-system change, paid/spend action, or third-party side effect outside the local approved draft/output root.

Default: external action is forbidden.

External action approval must name:

- exact recipient/resource/account/channel/system
- exact payload or payload source hash
- exact tool/API/channel
- single vs bulk scope
- one-time vs recurring scope
- expiration
- approver
- reviewer roles completed
- rollback/retraction plan where applicable

No-send packets, dry runs, prior sends, retrieved memory, health status, or business urgency do not authorize sends.

## 16. Adoption and amendment procedure

Adoption of this policy requires L9 approval from `constitutional_reviewer_authority`.

A valid L9 adoption approval must include:

- explicit phrase authorizing canonical adoption
- exact canonical path: `{root}/{paths.console}/SELF_ACTION_POLICY.md`
- approved source draft path
- approved source draft SHA256
- named authority boundary
- named reviewer roles completed
- explicit non-implementation boundary
- whether L5 preservation and/or L6 propagation are included or separate
- expiration or single-use terms

Suggested exact L9 approval phrase:

`I, the constitutional authority, give explicit L9 approval to create the canonical SELF_ACTION_POLICY.md at {root}/{paths.console}/SELF_ACTION_POLICY.md from source draft <path> with SHA256 <hash>. This approval is single-use and does not authorize implementation, runtime mutation, memory promotion, production repair, external action, or preservation-executor action, including git commit/push in profiles that bind git, unless separately stated.`

After adoption, amendment to this policy requires either:

- L4 approval for narrow non-authority-preserving textual corrections; or
- L9 approval for any authority ladder, role registry, gate registry, adoption procedure, or self-action authority change.

No actor may amend the policy to increase its own authority.

## 17. Stop conditions

Stop before action if any of these occurs:

- `SELF_ACTION_POLICY.md` exists unexpectedly before adoption.
- A retired top-level `STATE.json` reappears at `{root}/STATE.json`.
- Protected canonical governance files are dirty outside the exact authorized path.
- `{paths.memory}/index/*.jsonl` is dirty without exact memory authority.
- `action_queue` contains real/non-demo proposals where clean queue is required.
- Forbidden runtime roots exist unexpectedly.
- Health reports warnings or errors where green health is required for the gate.
- The active preservation executor has a nonzero prepared/staged/pending set before exact-path preservation/adoption, unless that exact set is the authorized target of the current gate.
- The active preservation executor has unrelated unpropagated records before an L6 propagation-bearing preservation/adoption action.
- Runtime STATE content parsing would be needed but content-read authority is absent.
- Target draft hash does not match approved hash.
- Approval is absent, vague, expired, bundled with implementation, or missing exact path/hash/role/authority details.
- The same actor would propose and approve its own expanded authority.
- A tool-layer denial instructs the agent not to retry or work around the action.
- Any requested action would create adjacent authority not named in the approval.

## 18. Supersession and audit

This policy, if adopted, must be superseded only by an explicit future policy revision with provenance and authority.

Required audit facts for future adoption/amendment:

- source draft path and hash
- approving authority and approval text
- reviewer roles completed
- exact canonical path changed
- preservation record ID/hash if an L5 preservation record was created
- propagation destination/status if an L6 propagation occurred
- postflight protected-surface checks
- runtime STATE metadata-only confirmation, unless content authority was explicitly granted
- explicit list of actions not authorized

Audit records or reports do not retroactively authorize an action.

# End of canonical SELF_ACTION_POLICY.md
