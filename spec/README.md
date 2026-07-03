# Procheiron Specification — v0.1

The portable specification for a governed, provenance-first agent-memory commons. This is the **Core**:
what any deployment must satisfy. Deployment-specific bindings (identities, paths, an authority ladder, a
preservation executor like git) live in a *profile*, not here — see `boundary.md`.

## Documents

| File | Scope |
|---|---|
| `governance.md` | Authority and review invariants — who may write, review, and authorize, expressed as non-authority invariants (e.g. "observation does not authorize mutation") that a minimal adopter can enforce without a full L0-L9 ladder. |
| `memory-commons.md` | The memory record model and lifecycle: `draft -> candidate -> validated -> active -> superseded`, fields, provenance, and supersession. |
| `control-plane.md` | How records change state safely - the validator, the policy check, the preservation-executor interface (git is one binding, not a requirement). |
| `conformance.md` | **Normative.** The MUST-list a deployment is checked against by `conformance/run_conformance.py`. |
| `boundary.md` | The Core vs Profile boundary - what is portable spec versus deployment-instance detail. |

## How conformance works

A deployment conforms if `conformance/run_conformance.py` passes the MUST-list in `conformance.md`
against it. The repo ships two passing reference deployments - a complete fictional one
(`conformance/generic-vault/`) and a 5-file minimal one (`conformance/minimal-vault/`) - plus negative
fixtures that must fail for documented reasons.

## Versioning

This spec is **v0.1**. v1.0 is earned only when a second *real* deployment passes conformance - not by a
fixture pass, a single deployment, or authority approval alone. Claims trail proofs.
