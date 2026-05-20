from __future__ import annotations

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles import base
from jammate_engine.styles.medium_swing import comping_patterns
from jammate_engine.styles.registry import get_style

SOURCE_KEY = "medium_swing:0:jammate_engine.styles.medium_swing.comping_patterns.get_pattern_candidates"


def _region(chord: str, *, previous: str | None = None, next_chord: str | None = None, first_section: bool = False, last_section: bool = False) -> HarmonicRegion:
    return HarmonicRegion(
        region_id="r",
        chord_symbol=chord,
        next_chord_symbol=next_chord,
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=0.0,
        duration_beats=4.0,
        is_first_bar_of_section=first_section,
        is_last_bar_of_section=last_section,
        metadata={"previous_chord_symbol": previous} if previous else {},
    )


def test_v2_6_60_style_policy_exposes_harmonic_function_without_parallel_selector() -> None:
    policy = get_style("medium_swing").arrangement_policy
    assert policy["piano_region_length_pattern_vocabulary_version"] == "v2_6_56"
    assert policy["piano_region_length_candidate_lookup_policy_version"] == "v2_6_57"
    assert policy["piano_region_length_weight_calibration_policy_version"] == "v2_6_58"
    assert policy["piano_comping_history_continuity_scorer_version"] == "v2_6_59"
    assert policy["piano_comping_harmonic_function_policy"] is True
    assert policy["piano_comping_harmonic_function_policy_version"] == "v2_6_60"
    assert "ChordRegion-length candidate pool" in policy["piano_comping_harmonic_function_contract"]
    assert "parallel selector" in policy["piano_comping_harmonic_function_contract"]
    assert "two-chord-bar" in policy["piano_comping_harmonic_function_contract"]


def test_v2_6_60_dominant_resolution_boosts_answer_tail_without_forcing_tail_push() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    region = _region("G7", previous="Dm7", next_chord="Cmaj7")
    adjusted = base._apply_piano_comping_harmonic_function_policy(candidates, region=region, context={"region": region})
    by_name = {candidate.name: candidate for candidate in adjusted}

    answer_tail = by_name["medium_swing_piano_2and_4_answer"]
    push = by_name["medium_swing_piano_1_4and_rare_push"]
    anchor = by_name["medium_swing_piano_anchor_1"]
    assert answer_tail.metadata["harmonic_function_comping_policy_version"] == "v2_6_60"
    assert answer_tail.metadata["harmonic_function_context_label"] == "dominant_resolution"
    assert answer_tail.metadata["harmonic_function_multiplier"] > 1.0
    assert "dominant_resolution_answer_tail_bonus" in answer_tail.metadata["harmonic_function_reasons"]
    assert push.metadata["harmonic_function_multiplier"] < 1.0
    assert "dominant_resolution_tail_push_control" in push.metadata["harmonic_function_reasons"]
    assert anchor.metadata["harmonic_function_current_to_next_type"] == "v_i_major"


def test_v2_6_60_tonic_resolution_and_section_start_prefer_stable_anchor() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    tonic_region = _region("Cmaj7", previous="G7", next_chord="Fmaj7")
    tonic_adjusted = base._apply_piano_comping_harmonic_function_policy(candidates, region=tonic_region, context={"region": tonic_region})
    tonic_by_name = {candidate.name: candidate for candidate in tonic_adjusted}
    stable = tonic_by_name["medium_swing_piano_anchor_1_3"]
    active = tonic_by_name["medium_swing_piano_1_2and_4"]
    assert stable.metadata["harmonic_function_context_label"] == "tonic_resolution"
    assert stable.metadata["harmonic_function_multiplier"] > 1.0
    assert active.metadata["harmonic_function_multiplier"] < 1.0

    section_region = _region("Cmaj7", next_chord="Fmaj7", first_section=True)
    section_adjusted = base._apply_piano_comping_harmonic_function_policy(candidates, region=section_region, context={"region": section_region})
    section_by_name = {candidate.name: candidate for candidate in section_adjusted}
    assert section_by_name["medium_swing_piano_anchor_1"].metadata["harmonic_function_context_label"] == "section_start"
    assert section_by_name["medium_swing_piano_anchor_1"].metadata["harmonic_function_multiplier"] > 1.0


def test_v2_6_60_plan_region_marks_selected_piano_events_after_harmonic_then_history_scorer() -> None:
    style = get_style("medium_swing")
    history: dict[str, object] = {}
    region = _region("G7", previous="Dm7", next_chord="Cmaj7")
    plan = style.plan_region(region, {"style_pattern_history": history})
    piano_events = [event for event in plan.events if event.track == "piano"]
    assert piano_events
    for event in piano_events:
        assert event.metadata["harmonic_function_comping_policy_version"] == "v2_6_60"
        assert event.metadata["harmonic_function_comping_policy_applied"] is True
        assert event.metadata["harmonic_function_context_label"] == "dominant_resolution"
        assert event.metadata["history_continuity_scorer_version"] == "v2_6_59"
        assert event.metadata["history_continuity_scorer_applied"] is True
        assert "two_chord_bar" not in str(event.metadata)
        assert "midi_note" not in event.metadata
        assert "velocity" not in event.metadata
        assert "duration" not in event.metadata
