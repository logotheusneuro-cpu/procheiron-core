# Procheiron Core/Profile Boundary Spec v0.1

Status: proposal-only draft; part of `procheiron-core` v0.1 after Batch-3 approval.

## 1. Core

Core is the deployment-independent contract. It defines:

- agent-neutral doctrine
- human-visible canonical surfaces
- tokenized path resolution
- source-of-truth categories
- memory lifecycle and provenance requirements
- non-authority invariants
- conformance tiers
- profile-binding requirements

Core MUST NOT require a particular model, harness, vendor, filesystem root, git remote, service manager,
cron system, MCP server, vector database, or named person/agent.

## 2. Profile

A deployment profile binds Core to a concrete host system. Profile content includes:

- concrete root paths
- deployment name
- named actors and role bindings
- constitutional/final authority mapping, if used
- executor bindings such as git, filesystem-only preservation, service manager, MCP, or none
- profile-specific no-index and sensitivity rules
- deprecated/duplicate roots in that deployment
- runtime roots and pin conditions, if any

Changing profile bindings that affect authority, protected paths, or no-index protections is a governance
mutation under the deployment's authority model.

## 3. Two profile concepts

Deployment profiles under `.procheiron/profiles/<name>/` bind Core to a host system.
Memory-audience profiles under the memory layer, if present, describe audiences/scopes for retrieval and
memory use. These are distinct and MUST NOT be conflated.

## 4. Physical target recommendation

Prove portability through config-driven conformance before standalone package or repository extraction.
Moving files before proving the seam is vanity engineering.

## 5. Tier-B stop line

This boundary spec does not authorize canonical swaps, runtime mutation, memory promotion, package installs,
external actions, service/timer/cron changes, or git preservation. Those require separate approval under the
deployment's authority model.
