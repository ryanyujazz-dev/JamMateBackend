from __future__ import annotations

import random

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.voicing import ContentFamily, Disposition, RootSupportPolicy, VoicingPolicy, VoicingRequest, VoicingResolver, VoicingState, generate_candidates, score_candidate
from jammate_engine.styles.registry import get_style
from jammate_engine.styles.medium_swing import comping_patterns


def _request(event_id: str, symbol: str, resolver_policy: VoicingPolicy, onset: float) -> VoicingRequest:
    return VoicingRequest(
        event_id=event_id,
        chord_symbol=symbol,
        track="piano",
        gesture_type="simultaneous_onset",
        gesture=simultaneous_onset(),
        expression_articulation="short",
        ensemble_context={"bass_present": True},
        policy=resolver_policy,
        onset_beat=onset,
        rng=random.Random(11),
    )


def test_voicing_resolver_carries_previous_state_between_harmonic_events() -> None:
    policy = VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B, ContentFamily.SEVENTH_BASIC),
        preferred_content=ContentFamily.ROOTLESS_A,
        allowed_dispositions=(Disposition.OPEN, Disposition.CLOSED),
        register_low=48,
        register_high=76,
        top_voice_low=60,
        top_voice_high=72,
        selector_temperature=0.0,
    )
    resolver = VoicingResolver()
    first = resolver.resolve(_request("e1", "Dm7", policy, 0.0))
    second = resolver.resolve(_request("e2", "G7", policy, 1.5))

    assert first.notes
    assert second.notes
    assert second.metadata["previous_voicing_state"]["previous_event_id"] == "e1"
    assert second.metadata["score_breakdown"]["details"]["voice_leading_distance"] is not None


def test_voice_leading_scorer_prefers_nearby_top_voice_over_octave_jump() -> None:
    policy = VoicingPolicy(top_voice_low=60, top_voice_high=72, max_top_voice_leap=7, selector_temperature=0.0)
    state = VoicingState.empty().advance(
        event_id="prev",
        chord_symbol="Dm7",
        notes=(53, 60, 64, 69),
        degrees=("b3", "b7", "9", "13"),
        onset_beat=0.0,
    )
    candidates = generate_candidates("G7", policy)
    low_motion = min(candidates, key=lambda c: abs(max(c.notes) - 69))
    big_jump = max(candidates, key=lambda c: max(c.notes))

    low_score = score_candidate(low_motion, policy, state).total
    jump_score = score_candidate(big_jump, policy, state).total
    assert low_score >= jump_score


def test_medium_swing_voicing_policy_exposes_musicality_weights() -> None:
    style = get_style("medium_swing")
    policy = style.voicing_policy
    assert policy.voice_leading_weight > 1.0
    assert policy.top_voice_weight > 1.0
    assert policy.top_voice_high <= 72
    assert policy.selection_pool_size >= 3


def test_medium_swing_piano_comping_candidates_have_density_and_weight_calibration_metadata() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    densities = {candidate.metadata.get("density") for candidate in candidates}
    calibration_classes = {candidate.metadata.get("weight_calibration_class") for candidate in candidates}
    assert "medium" in densities
    assert "sparse" in densities
    assert {"stable", "offbeat", "active", "tail_push"}.issubset(calibration_classes)
    assert all(candidate.metadata.get("weight_calibration_policy_version") == "v2_6_58" for candidate in candidates)


def test_medium_swing_history_guard_can_avoid_immediate_stable_pattern_repeat_after_v2_6_58_calibration() -> None:
    style = get_style("medium_swing")
    region1 = HarmonicRegion(
        region_id="r1",
        chord_symbol="Dm7",
        next_chord_symbol="G7",
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=0.0,
        duration_beats=4.0,
    )
    region2 = HarmonicRegion(
        region_id="r2",
        chord_symbol="G7",
        next_chord_symbol="Cmaj7",
        chorus_index=0,
        bar_index=1,
        chord_index=0,
        start_beat=4.0,
        duration_beats=4.0,
    )
    history: dict[str, str] = {}
    # With v2_6_58 calibration, the deterministic no-RNG choice is the stable
    # region-start anchor. The history guard should still prevent immediate
    # exact repetition on the following region.
    plan1 = style.plan_region(region1, {"style_pattern_history": history})
    plan2 = style.plan_region(region2, {"style_pattern_history": history})
    first_piano = next(event for event in plan1.events if event.track == "piano")
    second_piano_events = [event for event in plan2.events if event.track == "piano"]

    assert first_piano.metadata["candidate"] == "medium_swing_piano_anchor_1"
    assert all(event.metadata["candidate"] != "medium_swing_piano_anchor_1" for event in second_piano_events)
