# Procheiron

[![ci](https://github.com/logotheusneuro-cpu/procheiron-core/actions/workflows/ci.yml/badge.svg)](https://github.com/logotheusneuro-cpu/procheiron-core/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/procheiron)](https://pypi.org/project/procheiron/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Procheiron is a small, dependency-free trust layer for AI agent memory. It answers a question
that gets surprisingly hard once more than one agent shares a source of truth: **who wrote this
memory, who checked it, and has anyone tampered with the record since?**

Memory tools are good at storing and recalling. Trust is the part nobody owns. Give several
agents a shared memory and any one of them can write a "fact" the others will happily build on.
Nobody reviewed it, nobody approved it, and when it turns out to be wrong there is no clean way
to trace it or retire it.

Procheiron adds the missing discipline, and enforces it with a validator rather than a convention:

- Every memory moves through a lifecycle: `draft → candidate → validated → active → superseded`.
- A memory only becomes `active` — trusted — after review by someone who did not write it.
  Self-review is refused, not discouraged.
- Every step lands in an append-only audit log whose entries are hash-chained (BLAKE2b, pure
  standard library). Editing, reordering, or deleting a past event breaks the chain, and
  `procheiron validate` will say so.
- If you want authorship you can verify cryptographically, install the optional crypto extra and
  sign entries with ed25519. A signature check that cannot run is a hard error, never a silent pass.

Procheiron stores nothing and retrieves nothing. Bring whatever memory you already use — a vector
database, a knowledge graph, a folder of markdown files. It governs the records; your engine keeps
doing the remembering.

## Quick start

```bash
pipx install procheiron          # or: pip install procheiron
                                 # zero runtime dependencies, stdlib-only Python

procheiron init ./my-commons     # scaffold a governed memory commons
procheiron validate ./my-commons # check it against the spec
```

Or straight from a checkout, no install:

```bash
python3 conformance/run_conformance.py   # prove the spec holds against the bundled fixtures
python3 init/procheiron_init.py --root ./my-commons
```

## What the audit log does and doesn't protect you from

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

We keep a running ledger of what's proven versus merely claimed in **[CLAIMS.md](CLAIMS.md)**,
with evidence cited per claim. If anything in this README ever disagrees with that file, the
file is right.

## Where the project stands

Version 0.2.x, spec v0.1. The conformance suite passes against the bundled fixtures, including a
complete fictional deployment that the core has never seen. What it hasn't had yet is a second
*real* deployment run by someone who isn't us — that's the milestone we care about most, and
until it happens we don't claim production-readiness anywhere.

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

## License

MIT — see [LICENSE](LICENSE).
