<p align="center">
  <img src="https://raw.githubusercontent.com/logotheusneuro-cpu/procheiron-core/master/assets/logo-mark.webp" width="120" alt="Procheiron mark: an open hand holding a flame, struck as a Roman coin">
</p>

<h1 align="center">Procheiron</h1>

<p align="center">
  <em>Who wrote this memory, who checked it — and has anyone touched it since?</em>
</p>

<p align="center">
  <a href="https://github.com/logotheusneuro-cpu/procheiron-core/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/logotheusneuro-cpu/procheiron-core/ci.yml?style=flat-square&label=ci" alt="CI"></a>
  <a href="https://pypi.org/project/procheiron/"><img src="https://img.shields.io/pypi/v/procheiron?style=flat-square" alt="PyPI"></a>
  <img src="https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/runtime%20deps-0-brightgreen?style=flat-square" alt="Zero runtime dependencies">
  <a href="https://github.com/logotheusneuro-cpu/procheiron-core/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT license"></a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/logotheusneuro-cpu/procheiron-core/master/assets/hero-marcus.webp" width="460" alt="Marcus Aurelius — the Stoic emperor who kept his principles procheiron, 'ready at hand'">
</p>

Procheiron is a small, dependency-free trust layer for AI agent memory. Memory tools are good at
storing and recalling; trust is the part nobody owns. Give several agents a shared memory and any
one of them can write a "fact" the others will happily build on — nobody reviewed it, nobody
approved it, and when it turns out to be wrong there's no clean way to trace it or retire it.

Procheiron adds that discipline, and enforces it with a validator rather than a convention. It
stores nothing and retrieves nothing: bring whatever memory you already use — a vector database,
a knowledge graph, a folder of markdown files. It governs the records; your engine keeps doing
the remembering.

## Caught in the act

A deployment validates clean. Then someone with write access quietly rewrites history — a past
promotion suddenly claims a different actor:

```console
$ procheiron validate ./team-memory
Procheiron validation (full tier): PASS

$ # edit team-memory/memory/index/audit.jsonl:  "actor": "vera_curator" → "rogue_agent"

$ procheiron validate ./team-memory
Procheiron validation (full tier): FAIL
  ERROR: audit chain: audit event 0: entry_hash mismatch — content was altered
         after it was written
  ERROR: memories.jsonl:1: active record has no corroborating promotion audit
         event — forged/hand-flipped record
```

<sub>Real output (ids shortened). Reproduce it yourself: `conformance/generic-vault/` is a
complete fictional deployment — copy it, break it, validate it.</sub>

## How it works

<p align="center">
  <img src="https://raw.githubusercontent.com/logotheusneuro-cpu/procheiron-core/master/assets/lifecycle.webp" width="860" alt="Three scenes: one agent writes a record into a shared store; a different agent inspects it and stamps it with a green check; the approved records are joined in a chain — and when an attacker tries to swap one, the chain link snaps and an alarm fires.">
</p>

1. Every memory moves through a lifecycle: `draft → candidate → validated → active → superseded`.
2. A memory only becomes `active` — trusted — after review by someone who did not write it.
   Self-review is refused, not discouraged.
3. Every step lands in an append-only audit log whose entries are hash-chained (BLAKE2b, pure
   standard library). Editing, reordering, or deleting a past event breaks the chain.
4. Want authorship you can verify cryptographically? Install the crypto extra and sign entries
   with ed25519. A signature check that cannot run is a hard error, never a silent pass.

## Install

```bash
pipx install procheiron            # or: pip install procheiron
pip install "procheiron[crypto]"   # optional: ed25519 signing (the chain itself needs nothing)
```

Or straight from a checkout, no install:

```bash
python3 conformance/run_conformance.py       # prove the spec holds against the bundled fixtures
python3 init/procheiron_init.py --root ./my-commons
```

## Commands

| Command | What it does |
|---|---|
| `procheiron init ./my-commons` | Scaffold a governed memory commons. |
| `procheiron validate <root>` | Validate a deployment. Add `--expect-head <hex>` to also check the chain head against an external anchor. |
| `procheiron scorecard <root>` | Trust-loop numbers: records, independent promotions, blocks caught. |
| `procheiron mcp <root>` | Serve the commons to agents over MCP (stdio JSON-RPC). |
| `procheiron conformance` | Run the conformance suite (needs a repo checkout). |
| `procheiron version` | What it says. |

## What the audit log can and can't do

A candid word before you rely on it.

The hash chain makes the log **tamper-evident**: nobody can quietly edit history without breaking
the chain. But the chain only proves the log is internally consistent — someone with write access
to the file can rebuild the whole thing from scratch and it will verify. The fix is to anchor the
newest entry hash somewhere that person can't touch (a git commit works fine) and hand it back at
check time: `procheiron validate --expect-head <hex>`. Now a full rewrite is caught too.

Signing raises the bar further. With the crypto extra and a key registry (`known_actor_keys`),
every event from a registered actor must carry that actor's valid signature. Stripping a
signature fails validation; it does not slip through.

And the honest residual: if one OS user owns the log, the keys, *and* the key registry, a
determined insider can still rewrite and re-sign everything. On a single shared machine you get
tamper-*evidence* (detectable through the external anchor), not tamper-*prevention*. To stop that
insider outright you need the head anchored externally and the keys held out of the writer's
reach — a separate user, an HSM, or keyless signing.

We keep a running ledger of what's proven versus merely claimed in **[CLAIMS.md](https://github.com/logotheusneuro-cpu/procheiron-core/blob/master/CLAIMS.md)**,
with evidence cited per claim. If anything in this README ever disagrees with that file, the
file is right.

## What's in the repo

| Path | What it is |
|---|---|
| `spec/` | The v0.1 specification: governance, memory commons, control plane, the normative conformance MUST-list, and the Core/Profile boundary. |
| `conformance/` | The test of record. `generic-vault/` is a complete fictional deployment ("Meridian Atelier"); `minimal-vault/` is the 5-file minimal adopter; plus negative fixtures that must fail. |
| `examples/minimal-adopter/` | The smallest compliant deployment — provenance and independent review without the heavyweight governance ladder. |
| `init/` | The scaffolder, and `PORTING_GUIDE.md` for bringing Procheiron to an existing project. |

## Design choices

- **Zero runtime dependencies.** Everything a live deployment runs is standard-library Python.
  The one optional extra is `procheiron[crypto]` for ed25519 signing; the hash chain itself needs
  nothing. (`jsonschema` and `opa` appear only as dev/CI cross-checks.)
- **Tamper-evident by default, signed by choice.** See `chain.py` and `signing.py`.
- **Portable core, specific profile.** The spec stays generic; deployment-specific bindings
  (identities, paths, authority ladders) live in a profile. See `spec/boundary.md`.
- **No recall, ever.** Embeddings and retrieval are the memory engine's job. Procheiron will not
  grow a competing one.

## Roadmap

1. **A second, independent real deployment** passing conformance — the point where
   "works for its authors" becomes "works".
2. **A reference adapter** showing Procheiron governing a popular third-party memory engine end
   to end.
3. **Key-custody guidance for production** — separate-user, HSM, and keyless-signing patterns, so
   signing holds up even on a single machine.

Shipped so far: v0.1 brought the spec, conformance suite, CLI, and scaffolder; v0.2 brought the
tamper-evident chain and optional signing.

## FAQ

**Is this a memory engine?** No. It has no embeddings, no retrieval, no recall benchmarks, and
never will. It governs the records your engine holds.

**Can it stop a malicious insider?** Detection, yes; prevention only if you do two things — anchor
the chain head outside the insider's reach and keep signing keys out of their write scope. The
section above spells out exactly where the line is.

**Why zero dependencies?** A trust layer shouldn't ask you to trust a dependency tree. Everything
a live deployment runs is standard-library Python; even the hash chain is stdlib.

**Is it production-ready?** Not by our own rule. Conformance passes at fixture level, but the
"production-replicable" claim is reserved until a second *real* deployment — run by someone who
isn't us — passes the suite. That's roadmap item one.

**What does the name mean?** *Procheiron* (πρόχειρον) is Greek for "ready at hand" — historically,
a short practical handbook of law. A fitting name for a small set of rules you keep within reach.

## License

MIT — see [LICENSE](https://github.com/logotheusneuro-cpu/procheiron-core/blob/master/LICENSE).
