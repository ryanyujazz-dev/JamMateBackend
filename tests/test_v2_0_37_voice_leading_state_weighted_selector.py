from __future__ import annotations

import random

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.voicing import (
    VOICING_CONTRACT_VERSION,
    VOICING_CORE_PIPELINE,
    ContentFamily,
    Disposition,
    RootSupportPolicy,
    VoicingCandidate,
    VoicingPolicy,
    VoicingRequest,
    VoicingResolver,
    VoicingState,
    analyze_voice_leading,
    generate_candidates,
    score_candidate,
    select_candidate,
)


def _request(event_id: str, symbol: str, policy: VoicingPolicy, onset: float = 0.0) -> VoicingRequest:
    return VoicingRequest(
        event_id=event_id,
        chord_symbol=symbol,
        track="piano",
        gesture_type="simultaneous_onset",
        gesture=simultaneous_onset(),
        expression_articulation="sustain",
        ensemble_context={"bass_present": True},
        policy=policy,
        onset_beat=onset,
        rng=random.Random(17),
    )


def test_voice_leading_profile_is_public_and_explains_previous_state() -> None:
    assert VOICING_CONTRACT_VERSION >= "v2_0_37"
    assert "voice_leading_profile" in VOICING_CORE_PIPELINE
    assert "selector_decision" in VOICING_CORE_PIPELINE

    state = VoicingState.empty().advance(
        event_id="prev",
        chord_symbol="Dm7",
        notes=(53, 60, 64, 69),
        degrees=("b3", "b7", "9", "13"),
        onset_beat=0.0,
    )
    profile = analyze_voice_leading((55, 59, 65, 71), state, max_top_voice_leap=7).to_debug_dict()

    assert profile["has_previous"] is True
    assert profile["previous_top_note"] == 69
    assert profile["current_top_note"] == 71
    assert profile["top_voice_motion"] == 2
    assert profile["top_voice_direction"] == "up"
    assert profile["voice_leading_distance"] is not None
    assert profile["smoothness_label"] in {"smooth", "moderate", "jumpy"}


def test_score_breakdown_contains_voice_leading_profile_and_top_leap_guard() -> None:
    policy = VoicingPolicy(max_top_voice_leap=7, top_voice_low=60, top_voice_high=76)
    state = VoicingState.empty().advance(
        event_id="prev",
        chord_symbol="Cmaj7",
        notes=(52, 59, 64, 67),
        degrees=("R", "7", "3", "5"),
    )
    candidate = VoicingCandidate(notes=[60, 64, 67, 79], degrees=["R", "3", "5", "7"], score=1.0)

    details = score_candidate(candidate, policy, state).to_metadata()["details"]
    profile = details["voice_leading_profile"]

    assert details["voice_leading_distance"] == profile["voice_leading_distance"]
    assert profile["top_voice_motion"] == 12
    assert profile["top_voice_leap_exceeds_max"] is True
    assert details["top_voice_leap_exceeds_max"] is True


def test_weighted_selector_exposes_pool_probabilities_without_changing_candidate_contract() -> None:
    policy = VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B, ContentFamily.SEVENTH_BASIC),
        preferred_content=ContentFamily.ROOTLESS_A,
        allowed_dispositions=(Disposition.OPEN, Disposition.CLOSED),
        selector_temperature=0.25,
        selection_pool_size=3,
    )
    state = VoicingState.empty().advance(
        event_id="prev",
        chord_symbol="Dm7",
        notes=(53, 60, 64, 69),
        degrees=("b3", "b7", "9", "13"),
    )
    selected = select_candidate(generate_candidates("G7", policy), policy=policy, state=state, rng=random.Random(4))
    debug = selected.to_debug_dict()
    decision = debug["selector_decision"]

    assert decision["mode"] == "weighted_pool"
    assert decision["candidate_count"] >= decision["pool_size"] == 3
    assert 1 <= decision["selected_rank"] <= 3
    assert decision["has_previous_state"] is True
    assert decision["previous_event_id"] == "prev"
    assert len(decision["pool"]) == 3
    assert round(sum(item["probability"] for item in decision["pool"]), 6) == 1.0
    assert debug["voice_leading_profile"]["has_previous"] is True
    assert debug["metadata"]["selector_decision"] == decision


def test_resolver_plan_and_next_state_preserve_selector_decision_metadata() -> None:
    policy = VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B, ContentFamily.SEVENTH_BASIC),
        preferred_content=ContentFamily.ROOTLESS_A,
        allowed_dispositions=(Disposition.OPEN, Disposition.CLOSED),
        selector_temperature=0.0,
    )
    resolver = VoicingResolver()
    first = resolver.resolve(_request("e1", "Dm7", policy, 0.0))
    second = resolver.resolve(_request("e2", "G7", policy, 4.0))
    third = resolver.resolve(_request("e3", "Cmaj7", policy, 8.0))

    assert first.selector_decision["mode"] == "deterministic_top_score"
    assert second.voice_leading_profile["has_previous"] is True
    assert second.selector_decision["has_previous_state"] is True
    assert second.metadata["selector_decision"] == second.selector_decision
    assert second.metadata["voice_leading_profile"] == second.voice_leading_profile
    assert third.metadata["previous_voicing_state"]["previous_event_id"] == "e2"
    assert third.metadata["previous_voicing_state"]["previous_selector_decision"]["mode"] == "deterministic_top_score"
