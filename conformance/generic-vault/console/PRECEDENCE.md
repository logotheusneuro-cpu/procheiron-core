# Precedence

This file defines the narrow canonical precedence model for Procheiron in the current deployment profile.

## 1. Active Task Safety Restrictions Win

The active task's explicit safety restrictions override broader legacy or standing instructions.

Examples:

- If the active task forbids external messages, do not send email, chat/Telegram, DMs, posts, issues, PRs, comments, calendar events, or notifications.
- If the active task forbids git state changes, do not run the vault commit script, `git add`, `git commit`, `git push`, `git tag`, or `git merge`.
- If the active task is proposal-only, do not patch canonical governance files unless the task explicitly names those canonical changes as allowed.

## 2. System, Developer, and Runtime Constraints Remain Binding

Runtime identity, harness limits, write boundaries, tool restrictions, and safety constraints remain binding. A vault file cannot grant authority that the current runtime, harness, system instruction, or developer instruction forbids.

## 3. Procheiron Core Governs Shared Memory and Source-of-Truth Claims

For shared truth, memory lifecycle, provenance, agent-neutral governance, promotion, and canonical source-of-truth hierarchy, Procheiron Core governs.

Core governance files include:

- `{paths.console}/PROCHEIRON.md`
- `{paths.console}/PRECEDENCE.md`
- `{paths.console}/AGENT_BOOT.md`
- `{paths.console}/SOURCE_OF_TRUTH.md`
- `{paths.console}/SELF_ACTION_POLICY.md`
- `{paths.console}/AGENT_REGISTRY.md`
- `{paths.console}/RETRIEVAL_POLICY.md`
- `{paths.console}/DECISIONS.md`
- `{paths.console}/BLOCKERS.md`
- `{paths.console}/ACTIVE_PROJECTS.md`
- `{paths.memory}/README.md`
- `{paths.memory}/SCHEMA.md`
- `{root}/.procheiron/config.yaml` and the active deployment profile under `{root}/.procheiron/profiles/` — these bind the path tokens and the constitutional-authority role; they are canonical authority surfaces.

The authoritative, complete list of protected canonical surfaces is `{paths.console}/SELF_ACTION_POLICY.md` §12; this list defers to it.

## 4. Adapter and Profile Authority Is Scoped

Adapters and profile rules grant authority only within their declared runtime, profile, write roots, and active task scope. Profile-specific authority does not become Procheiron Core authority by implication.

No agent receives external-action authority, canonical-promotion authority, git-write authority, or secret-handling expansion merely because it can read the vault.

## 5. Legacy Profile Governance Remains Authoritative Inside Its Profile Until Migrated

Existing legacy profile governance remains authoritative until migrated: it continues to govern current operations until an approved migration supersedes it.

This means legacy profile files may continue to govern normal deployment-profile operations, including:

- the operational agent's core rules file under `{paths.legacy_governance}/` (the active profile names the concrete file)
- `{paths.legacy_governance}/STANDING_ORDERS.md`
- `{paths.legacy_governance}/TELEGRAM_ROUTING.md`
- `{paths.legacy_governance}/GOALS.md`
- `{paths.legacy_governance}/DAILY_LOG.md`
- the host runtime's workspace boot file (e.g. `{paths.workspace}/BOOT.md`)
- the host runtime's harness instruction file (the active profile maps its concrete location)

These files do not silently define Procheiron Core. When a claim must become shared, agent-neutral truth, it must be promoted into the correct Procheiron surface with provenance and approval.

## 6. Narrower Rule Wins

When two instructions conflict, follow the narrower or safer rule unless the constitutional authority explicitly authorizes the broader action.

Examples:

- Existing standing orders may require a chat/Telegram update, but an active task that forbids external messages means no message is sent.
- Normal harness or operational-agent write-back may require the vault commit script, but an active task that forbids git state changes means write-back is skipped.
- A profile may allow writes to a broad root, but a task-authorized root narrows writes to that task root only.

## 7. Agents May Propose but May Not Self-Authorize Promotion

Agents may create proposal documents, proposed adapter manifests, draft/candidate memories, validation reports, and recommendation artifacts in authorized roots.

Agents may not silently self-authorize:

- canonical governance changes outside explicit task scope
- active memory promotion
- permission or trust-level expansion
- external actions
- git stage/commit/push/tag/merge
- cron, hook, scheduler, service, package, retrieval, or vector database changes
- deletion, migration, or renaming of production paths

Promotion requires explicit authority, provenance, and the relevant adapter/profile permission.
