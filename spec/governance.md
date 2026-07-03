# Procheiron Governance Spec v0.1-draft

Status: proposal-only draft skeleton.
Normative target: `procheiron-core` v0.1 governance contract.

## 1. Purpose

Procheiron governance exists to make agent memory and self-action inspectable without letting useful evidence become authority. The governing sentence is:

> Procheiron may be self-evolving, but it is not self-authorizing.

## 2. Core principles

A compliant deployment MUST preserve these principles:

1. Agent-neutral: no model, harness, vendor, CLI, MCP server, scheduler, or database is required by Core.
2. Human-visible truth: canonical surfaces are inspectable Markdown and structured JSONL.
3. Provenance everywhere: durable claims cite source paths or source IDs.
4. Temporal by default: memory and decisions carry lifecycle state and dates.
5. Local-first: deployments can operate from a filesystem without a hosted service.
6. Profile-bound authority: Core defines roles and interfaces; a deployment profile binds names, paths, and executors.
7. Active safety restrictions win over broad standing rules.
8. Agents may draft and propose; they may not silently approve, promote, mutate, send, or expand their own authority.

## 3. Required deployment configuration

Every compliant deployment MUST provide `.procheiron/config.yaml` with:

- `version`
- `profile`
- `root`
- `paths.console`
- `paths.memory`

A full governance deployment MUST also provide:

- `paths.sources`
- `paths.outputs`
- any path tokens used by its Core, profile, or conformance documents

Optional recognized paths include: `paths.wiki`, `paths.adapters`, `paths.runtime_root`, `paths.workspace`,
`paths.scripts`, and deployment-specific executor/runtime roots.

Path tokens use the grammar:

- `{root}`
- `{paths.<key>}`

Resolution precedence MUST be:

1. explicit task/root argument
2. environment root, if provided by the implementation
3. nearest ancestor containing `.procheiron/config.yaml`

An unresolved token in a guard, forbidden root, protected surface, canonical path, or conformance rule MUST fail closed.

## 4. Required console surface

A compliant full governance deployment SHOULD provide these console files, located via `paths.console`:

- `PROCHEIRON.md`
- `PRECEDENCE.md`
- `AGENT_BOOT.md`
- `SOURCE_OF_TRUTH.md`
- `AGENT_REGISTRY.md`
- `RETRIEVAL_POLICY.md`
- `DECISIONS.md`
- `BLOCKERS.md`
- `ACTIVE_PROJECTS.md`

A minimal v0.1 adopter MAY collapse boot + precedence + source-of-truth into a shorter `CONSOLE.md`, provided conformance can still prove the same rules.

## 5. Source-of-truth hierarchy

A deployment MUST distinguish:

1. governance console
2. business/domain truth, if any
3. immutable raw sources
4. structured memory
5. rebuildable synthesis/cache layers
6. work products and proposals
7. agent workspaces/diaries

Agent workspaces MUST NOT become shared truth by proximity. A claim becomes shared truth only by being written to the correct canonical surface with provenance and, where required, approval.

## 6. Precedence

A compliant deployment MUST implement this conflict order:

1. active task safety restrictions
2. system/developer/runtime constraints
3. Procheiron Core for shared memory/source-of-truth/promotion claims
4. deployment profile rules within their scoped runtime
5. legacy profile governance until explicitly migrated
6. narrower/safer rule when ambiguity remains

## 7. Authority model

Core defines authority classes abstractly. A deployment MAY implement the full L0-L9 ladder or a smaller equivalent if it preserves these invariants:

- observation does not authorize mutation
- proposal does not authorize implementation
- retrieval does not authorize action
- health does not authorize repair
- candidate memory does not authorize active memory
- no-send does not authorize send
- sandbox success does not authorize production repair
- commit does not authorize push
- one approval does not authorize adjacent actions
- no actor approves its own expanded authority

Advanced deployments MAY use a named ladder and gate registry. Minimal deployments MUST still enforce the non-authority invariants above.

## 8. Profile binding

A deployment profile MUST bind:

- concrete paths for every required token
- concrete actors/adapters to abstract roles
- constitutional or final authority, if the deployment uses constitutional governance
- executor bindings such as git, filesystem preservation, service manager, or none
- profile-specific no-index and sensitivity rules

Changing profile bindings that affect authority or protected paths is a governance mutation and MUST require explicit approval under the deployment's authority model.

## 9. Retrieval discipline

Retrieval results are evidence, never authority. Retrieval MUST preserve lifecycle status for structured memory and provenance for Markdown snippets. Retrieval caches are rebuildable and MUST NOT become canonical truth.

## 10. Non-authority boundary

This spec does not require or authorize external sends, vector databases, cron jobs, runtime repair, package installs, public publishing, or automatic memory promotion.
