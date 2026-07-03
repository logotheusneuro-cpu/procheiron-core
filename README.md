# Procheiron

**A governance and provenance layer for agent memory.** Not a memory engine — the trust layer that
sits on top of one.

Memory engines (supermemory, mempalace, agentmemory, a vector DB, or plain files) answer *"what does my
agent remember?"* Procheiron answers a different question: **"can a *different* agent trust this memory —
and see who wrote it, who independently reviewed it, and who authorized it, backed by a validator-checked
append-only audit trail?"** It is built for the case a single-agent memory store ignores — **multiple
agents sharing one governed source of truth.** Provenance here is enforced by validation and an audit log,
**not cryptographic signatures**: it detects casual tampering and records authority, but does not *prove*
authorship against an insider with write access (single trust domain). See **[CLAIMS.md](CLAIMS.md)** for
the exact trust model and its limits.

Status: **v0.1 draft, pre-release.** Conformance passes at fixture level (a second, fully fictional
deployment validates against the same Core). Honest scope discipline: nothing here claims more than the
conformance suite proves.

> **[CLAIMS.md](CLAIMS.md)** — the proven-vs-not-proven ledger: every claim with cited evidence, or an
> honest caveat. The provenance system applied to itself. If a headline ever disagrees with the ledger,
> the ledger wins.

## Why this exists

Give an agent keys and it will use them. Give several agents a shared memory and, without governance, any
one of them can write a "fact" the others will trust — no record of who, no independent review, no way to
supersede it cleanly. Procheiron makes the trustworthy path the easy one:

- **Provenance-first lifecycle** — every memory is `draft → candidate → validated → active → superseded`.
  An `active` (trusted) record requires independent review by an actor that is *not* its author.
- **Authority, not vibes** — who may promote, review, or authorize is policy, enforced by a validator and a
  stdlib policy check, not a prompt asking nicely. (A Rego reference policy ships alongside for teams that
  run OPA in CI; the stdlib check is the production backend — see CLAIMS.md.)
- **Provable, replayable** — a conformance suite checks that a deployment obeys the spec; a fictional
  reference deployment (`conformance/generic-vault/`) proves the same Core governs a vault it has never
  seen.

## How this compares to memory engines

Procheiron is **not** a memory engine and does not compete with one — it governs the records a store holds.
The honest landscape (see the [competitive read](CLAIMS.md) for the long version):

| System | What it does | Enforced independent-review gate? | Tamper-evident audit trail? |
|---|---|---|---|
| Mem0 · supermemory · MemPalace · agentmemory | recall engines — embed, store, retrieve, per-user/agent scoping; Mem0 adds a per-memory change log | No | No — a mutable history log |
| Zep / Graphiti | bi-temporal knowledge graph with automatic episode→fact lineage | No | No — strong lineage, not tamper-evident |
| **Procheiron** | no recall at all — an enforced `draft→validated→active` lifecycle where `active` requires review by a non-author plus a distinct authorizer | **Yes** — none of them ship this | **Yes** — hash-chained (stdlib) + optional ed25519 signing |

Use a memory engine to *remember*; add Procheiron when *"who independently vetted this, and has the record
been tampered with since?"* has to be answerable. It rides on top of any of them.

**Trust model, stated up front:** the append-only audit log is **tamper-evident** — every event is
hash-chained (BLAKE2b, pure stdlib), so you cannot silently edit, reorder, or delete a past event without
breaking the chain. Anchor the head where the writer can't rewrite it (a git commit, an external log) and
it is verifiable Rekor-style, with zero dependencies. Authorship can additionally be **cryptographically
signed** — the optional `procheiron[crypto]` extra (ed25519) makes a forged event require the actor's
private key, not just their name. Conformance proves both: a signed log verifies, a forged signature is
caught. **Honest residual:** in a single-OS-user deployment, private keys sitting on the shared filesystem
are only as strong as their file permissions — real cross-trust-domain non-repudiation needs separate key
custody (separate OS users / HSM / Sigstore keyless). The hash chain's tamper-evidence holds regardless.

## What's in this repo

| Path | What it is |
|---|---|
| `spec/` | The v0.1 specification: `governance.md`, `memory-commons.md`, `control-plane.md`, the normative `conformance.md` MUST-list, and the Core/Profile `boundary.md`. |
| `conformance/` | `run_conformance.py` + fixtures. `generic-vault/` is a complete fictional deployment ("Meridian Atelier"); `minimal-vault/` is the 5-file minimal adopter. Run it to prove conformance. |
| `examples/minimal-adopter/` | The smallest compliant deployment — a memory commons with provenance + independent review, no heavyweight governance ladder. |
| `init/` | `procheiron_init.py` scaffolds a new deployment; `PORTING_GUIDE.md` is the step-by-step. |

## Quick start

```bash
# Install (zero runtime dependencies — stdlib-only Python):
pipx install procheiron          # or: pip install procheiron

# Scaffold a governed memory commons and validate it:
procheiron init ./my-commons
procheiron validate ./my-commons
```

From a source checkout (no install required):

```bash
# Prove the spec holds against the bundled fixtures:
python3 conformance/run_conformance.py

# Scaffold via the init script directly:
python3 init/procheiron_init.py --root ./my-commons
```

## Design choices worth knowing

- **Zero runtime dependencies (governance core).** Every tool a live deployment runs is standard-library
  Python. Cryptographic signing is the one *optional* extra (`pip install "procheiron[crypto]"` → ed25519);
  the tamper-evident hash chain needs no dependency at all. (`jsonschema`, `opa` are dev/CI cross-checks
  only.) Adopt it without taking on a dependency tree.
- **Tamper-evident by default, signed by choice.** The audit log is hash-chained in pure stdlib; ed25519
  signatures are opt-in. A verification that cannot run (crypto not installed but signatures required) is a
  hard error, never a silent pass — see `chain.py` / `signing.py`.
- **Bring your own memory engine.** Procheiron governs records and their lifecycle; it does **not** do
  embeddings or retrieval and never will (that is the engine's job). Point it at any store.
- **Core vs Profile.** The spec is portable Core. Deployment-specific bindings (identities, paths, a git
  preservation executor, a full L0–L9 authority ladder) live in a *profile* — see `boundary.md`.

## Not in scope (by design)

No vector/retrieval engine. No recall benchmarks — that is the memory engine's axis, not ours. No claim of
"production-replicable" until a second *real* deployment passes conformance (fixture-level proof is what
exists today, and the README says exactly that).

## Roadmap

1. ~~**Cryptographic trust** — a tamper-evident hash-chained audit log (stdlib) + optional ed25519 signing,
   so the log can't be silently rewritten and authorship is provable. Conformance proves a signed log
   verifies and a forged signature is caught.~~ **Shipped in v0.2.**
2. **A second, independent real deployment** through conformance — the milestone that turns "single
   deployment" from a caveat into proof. *(The biggest remaining gap.)*
3. **A reference integration** — Procheiron governing a third-party memory engine (Mem0 / Zep / supermemory)
   end to end, shipped as an adapter.
4. **Production key-custody guidance** — separate-OS-user / HSM / Sigstore-keyless patterns so signing gives
   real non-repudiation in a single-machine deployment, not just across separate hosts.
5. ~~PyPI / `pipx` packaging + one-command `procheiron init`; a config-resolved standalone MCP server.~~
   **Shipped in v0.1.**

## License

MIT — see `LICENSE`.
