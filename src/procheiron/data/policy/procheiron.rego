package procheiron.authority

# Procheiron authority-ladder + gate policy as code (roadmap 3.2, closes A2-35).
#
# Encodes the LOGIC of SELF_ACTION_POLICY §4 (ladder, non-cumulative), §6 (gate
# registry), §3/§5 (no self-approval), and §8 (invalid transitions). The TABLES
# (ladder ranks, gate->level/reviewers/approver, invalid transitions) live in
# policy_data.json and load as top-level `data` keys (data.gates, data.invalid_transitions,
# etc. — NOT data.policy_data, because opa loads plain JSON files at the root namespace),
# so this file and the stdlib
# reference evaluator (procheiron_policy.py) share one source of truth. The
# stdlib reference is the executable spec proven by ../tests/test_policy.py;
# `opa test` over this file is a Decision-B (adoption) verification step (opa is
# a static-binary install, deferred to adoption).
#
# Input contract (roadmap 3.2: {actor, gate, level, paths, reviewer} + the
# fields a real authority decision needs — reviewers_completed, approver,
# approver_role, transition{from,to}, human_external_approval).
# Output: data.procheiron.authority.decision.
#
#   opa eval -d policy_data.json -d procheiron.rego -I \
#     'data.procheiron.authority.decision' < input.json

import rego.v1

# `g` is the gate object, or {} when the gate is unknown (keeps `decision`
# total — it always returns allow:false + a reason rather than going undefined).
g := object.get(data.gates, input.gate, {})

known_gate if data.gates[input.gate]

# --- level: requested level must be EXACTLY one the gate allows. Non-cumulative
# (§4: a higher-risk action satisfies its own gate; no inheritance from below).
allowed_levels := object.get(g, "allowed_levels", [])

level_ok if {
	some lvl in allowed_levels
	lvl == input.level
}

# --- reviewers: every required reviewer role must appear in reviewers_completed.
required_reviewers := object.get(g, "required_reviewers", [])

reviewers_completed := object.get(input, "reviewers_completed", [])

missing_reviewers contains r if {
	some r in required_reviewers
	not r in reviewers_completed
}

reviewers_ok if count(missing_reviewers) == 0

# --- approver: L9 work requires the constitutional authority (l9_approver_role,
# falling back to approver_role for the adoption gate whose approver IS the
# constitutional authority); non-L9 uses the gate's named approver. A null
# approver means no approver is needed at this stage (no-send / inert ledger).
needs_l9 if input.level == 9

expected_approver := object.get(g, "l9_approver_role", object.get(g, "approver_role", null)) if needs_l9

expected_approver := object.get(g, "approver_role", null) if not needs_l9

approver_required if is_string(expected_approver)

approver_ok if not approver_required

approver_ok if {
	approver_required
	object.get(input, "approver_role", "") == expected_approver
}

# --- explicit human external approval for the external-action gate (§15).
external_ok if not object.get(g, "requires_explicit_human_external_approval", false)

external_ok if {
	object.get(g, "requires_explicit_human_external_approval", false)
	object.get(input, "human_external_approval", false) == true
}

# --- self-approval / self-review forbidden (§3, §8.7, §5 conflict-of-interest).
# NOTE: the stdlib reference backend (policy.py) compares identities NFKC+casefold
# so 'Alice' cannot self-review as 'alice'. Rego lacks NFKC; this raw comparison is a
# simplified mirror and is authoritative ONLY once an `opa test` step exists (see
# CLAIMS.md — rego is reference-only until then). Reconcile before wiring opa.
self_approval if input.actor == object.get(input, "approver", null)

self_review if input.actor == object.get(input, "reviewer", null)

# --- invalid transition (§8): a from->to in the table is denied.
bad_transition if {
	some t in data.invalid_transitions
	t[0] == object.get(input.transition, "from", "")
	t[1] == object.get(input.transition, "to", "")
}

# --- the allow decision.
default allow := false

allow if {
	known_gate
	level_ok
	reviewers_ok
	approver_ok
	external_ok
	not self_approval
	not self_review
	not bad_transition
}

# --- human-readable deny reasons.
deny contains "unknown gate" if not known_gate

deny contains sprintf("level %v not allowed for gate %v (allowed: %v)", [input.level, input.gate, allowed_levels]) if {
	known_gate
	not level_ok
}

deny contains sprintf("missing required reviewer roles: %v", [sort(missing_reviewers)]) if {
	known_gate
	not reviewers_ok
}

deny contains sprintf("approver role %v != required %v", [object.get(input, "approver_role", "<none>"), expected_approver]) if {
	known_gate
	approver_required
	not approver_ok
}

deny contains "external action requires explicit human external approval (§15)" if {
	known_gate
	not external_ok
}

deny contains "self-approval forbidden (§3 / §8.7)" if self_approval

deny contains "self-review forbidden (§8.7 independence)" if self_review

deny contains sprintf("invalid transition %v -> %v (§8)", [object.get(input.transition, "from", ""), object.get(input.transition, "to", "")]) if bad_transition

decision := {
	"allow": allow,
	"gate": input.gate,
	"required_levels": allowed_levels,
	"required_reviewers": required_reviewers,
	"missing_reviewers": missing_reviewers,
	"expected_approver": expected_approver,
	"reasons": deny,
}
