# Agent Registry

This registry is adapter-neutral. It describes roles, trust levels, and write roots; it does not depend on any one model, harness, CLI, or vendor.

## Trust Levels

- `read_only` — may inspect allowed paths only.
- `draft_writer` — may create drafts/proposals in assigned roots.
- `scaffold_writer` — may create additive scaffolding in assigned roots.
- `canonical_writer` — may patch canonical files only within explicit policy and task scope.
- `external_actor` — may take external actions only with explicit authorization.

No agent receives `external_actor` authority by default.

## Default Policy

- Agents may read public/non-secret vault materials needed for their task.
- Agents must not expose secrets.
- Agents must cite source paths for durable claims.
- Agents may propose improvements without self-authorizing promotion.
- Write roots are narrow; absence of a write root means no write authority.

## Starting Entries

Named instances are profile-supplied. The concrete roster — the specific agents/adapters bound to each role, their trust levels, and their default write roots — is defined in the active deployment profile, not in Core. Core fixes only the abstract roles, trust levels, default policy, and write-root rules above. Each profile-supplied entry MUST conform to those Core constraints and declare the adapter-neutral role fields below.

The profile roster typically includes, at minimum:

- a primary operational agent (`canonical_writer` within existing profile policy, scoped to its own workspace plus task-approved roots — an agent workspace is not shared truth);
- a reviewer/operator agent for review and implementation (`scaffold_writer` / `draft_writer` by task, scoped to its review root and task-approved additive scaffolds);
- one or more worker agents and generic LLM/code-agent adapters (`draft_writer` unless a task expands scope, scoped to task-specific outputs/proposals, with no commits or external actions unless explicitly authorized);
- a runtime/harness adapter representing the current deployment profile / orchestration context (this is profile, not Procheiron core — the host runtime hosts this Procheiron deployment; it does not define Procheiron); and
- a default future-compatible generic agent entry (`read_only` by default, no write root until registered, and must declare capabilities before writes).

## Adapter-Neutral Role Fields

Each future registry entry should declare:

- `agent_id`
- `adapter`
- `role`
- `trust_level`
- `read_roots`
- `write_roots`
- `forbidden_actions`
- `sensitivity_ceiling`
- `promotion_authority`
- `last_reviewed`

## Write Root Rule

A write root grants only the minimum necessary filesystem surface. It does not grant permission to delete, rename, move, commit, push, schedule, send, or publish.
