# Security Policy

Procheiron is a trust layer, so security reports get first-class treatment: a confirmed
vulnerability in the validator, chain, signing, or policy path is a release blocker, and the
fix ships with a conformance fixture that would have caught it.

## Supported versions

| Version | Supported |
|---|---|
| 0.2.x | ✅ |
| < 0.2 | ❌ — upgrade; 0.1.x has no tamper-evident chain |

## Reporting a vulnerability

Use **GitHub's private vulnerability reporting** ("Report a vulnerability" under the Security
tab of this repository). Please do not open a public issue for anything exploitable.

Include what you can: affected file/function, a reproduction (a tampered fixture is ideal),
and the impact as you understand it. You will get an acknowledgment, and the fix will land
with a regression fixture in `conformance/` before any advisory is published.

## Threat model — read before reporting

The README ("Trust model, stated up front" and "Honest residual") and `CLAIMS.md` state
exactly what is and is not defended:

- The audit log is **tamper-evident** (stdlib BLAKE2b hash chain), not tamper-*proof*.
- A single-trust-domain insider who can write the log can rebuild the chain; that is
  **documented and out of scope** unless the deployment anchors the head externally
  (`validate --expect-head`) and keeps the key registry outside the writer's scope.
- Signature checks require the optional `procheiron[crypto]` extra; a check that cannot run
  is a hard error, never a silent pass.

Reports that re-state a documented residual are welcome as discussion but are not treated as
vulnerabilities. Reports that show a documented guarantee **failing** (chain accepts a silent
edit, a forged or stripped signature passes, a policy gate approves a self-review) absolutely are.
