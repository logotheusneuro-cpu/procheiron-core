# Procheiron Agent Boot

This boot protocol applies to any agent using this vault: any coding/CLI agent, hosted assistant, the host runtime, or future agents.

## 0. Token Resolution (read this first)

Procheiron Core documents are parameterized. Path tokens written as `{root}` or `{paths.<key>}` are not literal paths; they resolve through the deployment configuration:

1. Discover the deployment root, most-explicit-wins: an explicitly task-given root, then the `PROCHEIRON_ROOT` environment variable, then the nearest ancestor directory containing `.procheiron/config.yaml`.
2. Read `{root}/.procheiron/config.yaml` — it defines every `{paths.<key>}` value for this deployment.
3. Read the active deployment profile under `{root}/.procheiron/profiles/<profile>/` (`profile.md` and `lint.json`) — it binds abstract roles, including the constitutional authority, and records profile-specific facts.

A token that cannot be resolved fails closed: treat any guard, forbidden root, or protected surface that names an unresolvable token as in force, stop the affected action, and record the blocker. Never guess a token's value from examples in prose.

## 1. Verify Root

Before using Procheiron, verify the local root exists (resolved per §0):

`{root}`

If the root cannot be verified, stop the affected action and record the blocker if a safe write path exists.

## Precedence and Mixed Boot Modes

Before resolving conflicts between active task instructions, Procheiron Core, profile adapters, and legacy profile governance, read `{paths.console}/PRECEDENCE.md`.

Boot mode depends on the task:

- For Procheiron governance or memory tasks, read Procheiron boot files first.
- For normal deployment-profile operations, the existing deployment-profile boot remains valid within the deployment profile.
- For mixed tasks, read Procheiron Core first for governance, then deployment-profile files for operational context.

## 2. Read Order

Read in this order before making durable Procheiron governance, source-of-truth, memory, or promotion claims or writes:

1. `{root}/.procheiron/config.yaml` and the active profile under `{root}/.procheiron/profiles/` (token resolution, §0)
2. `{paths.console}/PROCHEIRON.md`
3. `{paths.console}/SOURCE_OF_TRUTH.md`
4. `{paths.console}/AGENT_BOOT.md`
5. `{paths.console}/SELF_ACTION_POLICY.md` — the adopted constitution (authority ladder, gates, stop conditions)
6. `{paths.console}/AGENT_REGISTRY.md`
7. `{paths.console}/RETRIEVAL_POLICY.md`
8. `{paths.console}/DECISIONS.md`
9. `{paths.console}/BLOCKERS.md`
10. `{paths.console}/ACTIVE_PROJECTS.md`
11. `{paths.memory}/README.md`
12. `{paths.memory}/SCHEMA.md`
13. Topic-relevant files in the business-context root, `{paths.wiki}/`, `{paths.sources}/`, `{paths.memory}/profiles/`, `{paths.outputs}/`, and agent workspaces.

## 3. Write Boundaries

Agents must write only where their registry entry or task-specific authorization allows.

General defaults:

- Canonical shared truth belongs in `{paths.console}/`, the business-context root, `{paths.wiki}/`, `{paths.memory}/`, or `{paths.sources}/` according to file purpose.
- Agent-specific notes, drafts, and diaries belong in the agent's workspace.
- Work products belong in `{paths.outputs}/` or the task-authorized output root.
- Raw source files under `{paths.sources}/` are append-only/immutable once captured.
- Candidate changes belong in `.proposed.md`, `.proposed.yaml`, or `{paths.memory}/evolution/proposals/` unless canonical promotion has been explicitly approved.

## 4. Source Citation Rules

Durable claims must cite source paths or source IDs.

Minimum citation fields for structured memory:

- `source_ids`
- `source_paths`
- `created_by`
- `created_at`
- `confidence`
- `status`

If a claim is inferred rather than directly stated, mark it as inferred and lower confidence accordingly.

## 5. Memory Write Rules

- Raw evidence goes in `{paths.sources}/` and should not be edited after capture.
- Derived memory goes in `{paths.memory}/index/*.jsonl` as candidate/draft unless approved.
- Canonical Markdown updates must be additive and cite sources.
- Supersession is explicit: never silently replace old memory.
- Sensitive information must be classified and never exposed in reports.
- Secrets do not belong in memory.

## Active Procheiron Memory Use

For Procheiron, memory, or governance tasks, agents must read the command-center Procheiron files and `{paths.memory}/` schema/index files before making durable claims or canonical changes.

For ordinary deployment-profile operations, agents should consult relevant `active` Procheiron records in `{paths.memory}/index/memories.jsonl` as an additional shared-memory layer. Legacy deployment-profile boot remains valid inside the deployment profile unless explicitly superseded by approved Procheiron governance.

Status semantics:

- `active` and `validated` records may guide work.
- `candidate` and `draft` records are evidence or proposals only.
- `disputed`, `superseded`, and `archived` records are history only unless a task explicitly asks for historical review.

Durable memory claims must cite source paths or source IDs. Agents may propose memory changes, but may not self-authorize promotion unless the current task explicitly grants validator or curator authority and validation passes.

External actions remain forbidden unless separately authorized by the active task and allowed by registry/policy. Agent folders are workspaces and diaries, not shared truth.

## 6. External Action Restrictions

Agents must not send emails, DMs, posts, notifications, issues, PRs, comments, calendar events, or other external actions unless the active task explicitly authorizes that action and the registry/policy permits it.

Phase 1/2 explicitly forbids:

- External sending/posting/publishing/notifying.
- Spending or provisioning.
- Cron, scheduler, hook, launch-agent, or service changes.
- Package installs/upgrades.
- Git stage/commit/push/tag/merge.
- Secret exposure.

## 7. When Blocked Without Asking Questions

If blocked and user clarification is unavailable or forbidden:

1. Choose the least destructive additive interpretation if one exists.
2. If no safe additive path exists, skip the unsafe action.
3. Record the skipped action in `{paths.console}/BLOCKERS.md` or the task report.
4. Continue with other safe work.
5. Do not invent missing authority.

## 8. Promotion Rule

Agents may propose improvements. Agents may not silently self-authorize canonical changes, active memory promotion, permission expansion, hooks, automations, deletion policies, or external actions.
