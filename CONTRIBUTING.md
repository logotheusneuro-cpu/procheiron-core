# Contributing to Procheiron

Procheiron is a spec + reference implementation for governed agent memory. Contributions are welcome,
with one rule that comes from the project's own subject matter: **claims trail proofs.**

## Ground rules

1. **Every behavioral claim must be backed by the conformance suite.** If you change governance behavior,
   add or update a fixture in `conformance/` and make `run_conformance.py` green. A PR that changes
   behavior without a fixture will be asked for one.
2. **Zero runtime dependencies.** Anything a deployment runs at runtime must be standard-library Python.
   Dev/CI-only tools (jsonschema, opa) are fine but must never be required to run the validator, init, or
   the minimal adopter.
3. **No secrets, ever.** No real credentials, tokens, identities, or private deployment content in any
   fixture, example, or test. Secret-*shaped* strings used to test detection must be generated at runtime,
   not committed (see `run_conformance.py`).
4. **Portable Core, specific Profile.** Keep deployment-specific detail (paths, identities, ladder/gate
   tables, executor bindings) in profiles/examples — not in the normative spec. See `spec/boundary.md`.
5. **Number honestly.** Version numbers are earned, not declared. v1.0 requires a second *real*
   deployment passing conformance — not a fixture pass, a single deployment, or authority approval alone.
   (See `CHANGELOG.md` for what each released version actually proved.)

## How to propose a change

- Open an issue describing the behavior and why.
- For spec changes, edit `spec/` and update `conformance.md` (the MUST-list) together.
- Run `python3 conformance/run_conformance.py` and include the output in your PR.

## What's most wanted right now

See the Roadmap in `README.md` — the standalone, `--root`-relative MCP server is the top item.
