package procheiron.authority_test

# opa-native unit tests for procheiron.rego (roadmap 3.2). Run at adoption:
#   opa test -d policy_data.json -d procheiron.rego procheiron_test.rego -v
# These mirror policy_cases.json so the opa backend and the stdlib reference
# backend are proven to agree on the same scenarios. opa is a static-binary
# install deferred to Decision-B; until then the reference backend (exercised by
# ../tests/test_policy.py) is the executable proof.

import data.procheiron.authority
import rego.v1

valid_promotion := {
	"actor": "atlas_review_bot", "gate": "memory_promotion_gate", "level": 4,
	"reviewer": "atlas_drafter",
	"reviewers_completed": ["memory_reviewer_curator", "authority_reviewer"],
	"approver": "dana_okoro", "approver_role": "memory_reviewer_curator",
	"transition": {"from": "candidate", "to": "validated"},
}

test_valid_promotion_allows if {
	authority.allow with input as valid_promotion
}

test_self_review_denied if {
	not authority.allow with input as object.union(valid_promotion, {"reviewer": "atlas_review_bot"})
}

test_missing_reviewer_denied if {
	not authority.allow with input as object.union(valid_promotion, {"reviewers_completed": ["memory_reviewer_curator"]})
}

test_wrong_level_denied if {
	not authority.allow with input as object.union(valid_promotion, {"level": 1})
}

test_invalid_transition_denied if {
	not authority.allow with input as object.union(valid_promotion, {"transition": {"from": "memory_candidate", "to": "active_memory"}})
}

test_unknown_gate_denied if {
	not authority.allow with input as object.union(valid_promotion, {"gate": "made_up_gate"})
}

l9_adoption := {
	"actor": "atlas_review_bot", "gate": "self_action_policy_adoption_gate", "level": 9,
	"reviewer": "independent_reviewer_x",
	"reviewers_completed": ["independent_adversarial_reviewer", "canonical_governance_reviewer", "system_owner", "authority_reviewer"],
	"approver": "dana_okoro", "approver_role": "constitutional_reviewer_authority",
	"transition": {"from": "proposed_draft", "to": "adopted"},
}

test_l9_adoption_with_constitutional_authority_allows if {
	authority.allow with input as l9_adoption
}

test_l9_adoption_wrong_approver_denied if {
	not authority.allow with input as object.union(l9_adoption, {"approver_role": "authority_reviewer"})
}

external_send := {
	"actor": "vera_curator", "gate": "external_action_send_gate", "level": 8,
	"reviewer": "reviewer_x",
	"reviewers_completed": ["business_owner", "operations_reviewer", "technical_reviewer", "authority_reviewer"],
	"approver": "dana_okoro", "approver_role": "business_owner",
	"transition": {"from": "review", "to": "send"},
}

test_external_without_human_approval_denied if {
	not authority.allow with input as external_send
}

test_external_with_human_approval_allows if {
	authority.allow with input as object.union(external_send, {"human_external_approval": true})
}

test_self_approval_denied if {
	not authority.allow with input as {
		"actor": "atlas_review_bot", "gate": "canonical_policy_edit_gate", "level": 4,
		"reviewer": "reviewer_x",
		"reviewers_completed": ["canonical_governance_reviewer", "authority_reviewer"],
		"approver": "atlas_review_bot", "approver_role": "canonical_governance_reviewer",
		"transition": {"from": "proposal", "to": "canonical_edit_approved"},
	}
}
