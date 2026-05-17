from __future__ import annotations

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.voicing import (
    Disposition,
    VoicingPolicy,
    VoicingRequest,
    VoicingResolver,
    describe_disposition_placement,
    evaluate_register_guard,
    generate_candidates,
    place_degree_notes,
)


def _request(ensemble: dict | None = None, policy: VoicingPolicy | None = None) -> VoicingRequest:
    return VoicingRequest(
        event_id="register_guard_probe",
        chord_symbol="Cmaj7",
        track="piano",
        gesture_type="simultaneous_onset",
        gesture=simultaneous_onset(),
        expression_articulation="sustain",
        ensemble_context=ensemble or {"bass_present": True},
        policy=policy or VoicingPolicy(),
    )


def test_register_guard_detects_out_of_range_notes() -> None:
    policy = VoicingPolicy(register_low=48, register_high=72)
    guard = evaluate_register_guard([47, 60, 64], policy)
    debug = guard.to_debug_dict()
    assert debug["in_register"] is False
    assert debug["passed"] is False
    assert debug["out_of_range_notes"] == [47]
    assert "outside_absolute_register" in debug["reasons"]


def test_register_guard_detects_max_span_violation() -> None:
    policy = VoicingPolicy(register_low=36, register_high=84, max_voicing_span=18)
    guard = evaluate_register_guard([48, 60, 72], policy)
    assert guard.span == 24
    assert guard.span_ok is False
    assert guard.passed is False
    assert "span_exceeds_max_voicing_span" in guard.reasons


def test_register_guard_detects_low_register_mud_risk() -> None:
    policy = VoicingPolicy(register_low=36, register_high=84)
    guard = evaluate_register_guard([48, 51, 64], policy)
    debug = guard.to_debug_dict()
    assert debug["lowest_interval"] == 3
    assert debug["muddy_low_interval_ok"] is False
    assert debug["passed"] is False
    assert "muddy_low_interval" in debug["reasons"]


def test_disposition_debug_contract_keeps_hand_as_hint_not_core_grouping() -> None:
    policy = VoicingPolicy(preferred_disposition=Disposition.SPREAD)
    placed = place_degree_notes(
        root_pc=0,
        degrees=[("R", 0), ("3", 4), ("5", 7), ("7", 11)],
        low=policy.register_low,
        high=policy.register_high,
        disposition=Disposition.SPREAD,
        policy=policy,
    )
    debug = describe_disposition_placement(placed, Disposition.SPREAD, policy)
    assert debug["disposition"] == "spread"
    assert debug["uses_split_register_hints"] is True
    assert debug["legacy_hand_hints_only"] is True
    assert debug["core_grouping_is_abstract"] is True
    assert debug["left_range_hint"] == [policy.left_hand_low, policy.left_hand_high]


def test_candidate_and_plan_expose_disposition_and_register_guard_metadata() -> None:
    policy = VoicingPolicy(preferred_disposition=Disposition.OPEN, allowed_dispositions=(Disposition.OPEN,))
    candidate = generate_candidates("Cmaj7", policy)[0]
    candidate_debug = candidate.to_debug_dict()
    assert candidate_debug["disposition_guard"]["disposition"] == "open"
    assert candidate_debug["register_guard"]["in_register"] is True
    assert "passed" in candidate_debug["register_guard"]

    plan = VoicingResolver().resolve(_request(policy=policy))
    plan_debug = plan.to_debug_dict()
    assert plan_debug["disposition_guard"]["disposition"] == plan.disposition
    assert plan_debug["register_guard"]["notes"] == plan.midi_notes
    assert plan_debug["metadata"]["register_guard"] == plan_debug["register_guard"]
    assert "disposition_guard" in plan_debug["metadata"]["voicing_core_pipeline"]
    assert "register_guard" in plan_debug["metadata"]["voicing_core_pipeline"]


def test_no_bass_split_role_register_guard_uses_rh_boundaries() -> None:
    plan = VoicingResolver().resolve(_request(ensemble={"bass_present": False}))
    guard = plan.register_guard
    assert plan.ensemble_role == "piano_rh_harmonic_comping"
    assert min(plan.midi_notes) >= guard["register_low"]
    assert guard["register_low"] >= 55
    assert guard["in_register"] is True
    assert guard["passed"] is True
