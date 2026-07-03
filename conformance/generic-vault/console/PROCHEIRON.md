# Procheiron

Tagline: Memory that outlives the agent.

## Definition

Procheiron is an agent-neutral memory commons: a local-first, inspectable, provenance-preserving memory substrate for any current or future agent runtime, including the host runtime and any other capable agent or model.

It is not tied to any single deployment profile. It is not an operating system. It is not an agent runtime. It is not a hidden vector database. Its canonical surface is human-visible Markdown and structured JSONL that can be read in Obsidian or any filesystem tool.

## Core Principles

1. Agent-neutral.
2. Human-visible truth in Markdown/Obsidian-compatible files.
3. Raw sources are immutable.
4. Derived memory is rebuildable.
5. Provenance everywhere.
6. Temporal by default.
7. No harness, vendor, or model lock-in.
8. Local-first, sync-capable later.
9. Inspectable before intelligent.
10. Permissions are part of memory.
11. Agents may propose improvements, but may not silently self-authorize canonical changes.

## Current Profile Mapping

For this deployment profile, the Procheiron root is:

`{root}`

The deployment profile is the current host profile, not the definition of Procheiron itself.

- `{paths.console}/` is this profile's Procheiron Console.
- The business knowledge area contains business-specific operational truth for this profile.
- `{paths.sources}/` contains immutable raw evidence.
- `{paths.memory}/` contains structured memory records, indexes, schemas, validation, and evolution proposals.
- `{paths.wiki}/` contains compiled synthesis and knowledge graph-style views.
- `{paths.outputs}/` contains work products and recommendation artifacts.
- The operational agent's and reviewer agent's directories are agent-specific workspaces/diaries, not canonical shared truth.

## No Runtime Lock-In

Procheiron does not require a particular model, CLI, harness, MCP server, vector database, scheduler, or agent runtime. Any capable agent may read it. Any write-capable agent must respect the boundary, provenance, validation, and approval rules in this console.

## Phase Boundaries

### Phase 1: Visible Governance Layer

Create the console and governance files that define source-of-truth hierarchy, agent boot rules, registry, decisions, blockers, and active projects. Phase 1 is Markdown-first and inspectable.

### Phase 2: Structured Memory Skeleton

Create `{paths.sources}/`, `{paths.memory}/`, the adapters layer, `.procheiron/`, validation, and evolution scaffolding. Phase 2 does not install external memory systems, enable hooks, run schedulers, or promote candidate memory automatically.

### Explicitly Out of Scope for Phase 1/2

- External memory services.
- Vector databases or hidden retrieval indexes.
- Cron, hooks, daemons, or scheduler changes.
- External sends, posts, notifications, PRs, issues, or commits.
- Automatic canonical promotion of candidate memory.
- Deletion, migration, or renaming of existing production files.
