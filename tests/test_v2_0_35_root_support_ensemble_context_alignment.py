from __future__ import annotations

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.roles import EnsembleContext
from jammate_engine.core.voicing import (
    RootSupportPolicy,
    VoicingPolicy,
    VoicingRequest,
    VoicingResolver,
    generate_candidates,
    resolve_root_support_decision,
)


def _request(ensemble: dict, policy: VoicingPolicy | None = None) -> VoicingRequest:
    return VoicingRequest(
        event_id="root_support_probe",
        chord_symbol="Dm7",
        track="piano",
        gesture_type="simultaneous_onset",
        gesture=simultaneous_onset(),
        expression_articulation="sustain",
        ensemble_context=ensemble,
        policy=policy or VoicingPolicy(root_support=RootSupportPolicy.ROOTLESS_PREFERRED),
    )


def test_ensemble_context_names_bass_foundation_provider() -> None:
    assert EnsembleContext.from_dict({}).bass_foundation_provider == "bass_track"
    assert EnsembleContext.from_dict({"bass_present": False}).bass_foundation_provider == "piano_lh_bass_foundation"
    assert EnsembleContext.from_dict({"bass_present": False, "piano_split_role_enabled": False}).bass_foundation_provider == "harmonic_voicing"
    assert EnsembleContext.from_dict({"bass_present": False, "piano_split_role_enabled": False, "allow_rootless_without_bass": True}).bass_foundation_provider == "intentional_rootless_texture"


def test_root_support_decision_keeps_bass_present_policy() -> None:
    decision = resolve_root_support_decision(RootSupportPolicy.ROOTLESS_ALLOWED, {"bass_present": True})
    debug = decision.to_debug_dict()
    assert debug["effective_policy"] == "rootless_allowed"
    assert debug["bass_foundation_provider"] == "bass_track"
    assert debug["rootless_allowed"] is True
    assert debug["root_required"] is False
    assert debug["reason"] == "bass_present_use_style_policy"


def test_no_bass_split_role_makes_rh_comping_explainably_rootless_allowed() -> None:
    plan = VoicingResolver().resolve(_request({"bass_present": False}))
    assert plan.root_support == "rootless_allowed"
    assert plan.ensemble_role == "piano_rh_harmonic_comping"
    decision = plan.root_support_decision
    assert decision["requested_policy"] == "rootless_preferred"
    assert decision["effective_policy"] == "rootless_allowed"
    assert decision["bass_foundation_provider"] == "piano_lh_bass_foundation"
    assert decision["reason"] == "no_bass_split_role_lh_foundation"
    assert decision["root_required"] is False
    assert plan.metadata["root_support_decision"] == decision


def test_no_bass_without_split_role_requires_root_in_harmonic_voicing() -> None:
    plan = VoicingResolver().resolve(_request({"bass_present": False, "piano_split_role_enabled": False}))
    assert plan.root_support == "root_required"
    assert plan.root_included is True
    assert "R" in plan.degrees
    assert plan.disposition == "left_root_right_chord"
    assert plan.root_support_decision["bass_foundation_provider"] == "harmonic_voicing"
    assert plan.root_support_decision["reason"] == "no_bass_no_split_role_requires_harmonic_root"


def test_allow_rootless_without_bass_preserves_intentional_floating_texture() -> None:
    plan = VoicingResolver().resolve(
        _request({"bass_present": False, "piano_split_role_enabled": False, "allow_rootless_without_bass": True})
    )
    assert plan.root_support == "rootless_preferred"
    assert plan.root_support_decision["bass_foundation_provider"] == "intentional_rootless_texture"
    assert plan.root_support_decision["rootless_preferred"] is True
    assert plan.root_support_decision["root_required"] is False


def test_candidate_debug_exposes_root_support_decision_metadata() -> None:
    policy = VoicingPolicy(root_support=RootSupportPolicy.ROOTLESS_PREFERRED).with_ensemble_context({"bass_present": False})
    candidate = generate_candidates("Dm7", policy)[0]
    debug = candidate.to_debug_dict()
    assert debug["root_support_decision"]["effective_policy"] == "rootless_allowed"
    assert debug["metadata"]["root_support_decision"]["bass_foundation_provider"] == "piano_lh_bass_foundation"
