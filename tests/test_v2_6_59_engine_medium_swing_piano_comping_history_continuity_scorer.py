from __future__ import annotations

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles import base
from jammate_engine.styles.medium_swing import comping_patterns
from jammate_engine.styles.registry import get_style


def test_v2_6_59_style_policy_exposes_history_continuity_scorer_without_parallel_selector() -> None:
    style = get_style("medium_swing")
    policy = style.arrangement_policy
    assert policy["piano_region_length_pattern_vocabulary_version"] == "v2_6_56"
    assert policy["piano_region_length_candidate_lookup_policy_version"] == "v2_6_57"
    assert policy["piano_region_length_weight_calibration_policy_version"] == "v2_6_58"
    assert policy["piano_comping_history_continuity_scorer"] is True
    assert policy["piano_comping_history_continuity_scorer_version"] == "v2_6_59"
    assert "existing region-length candidate pool" in policy["piano_comping_history_continuity_contract"]
    assert "parallel selector" in policy["piano_comping_history_continuity_contract"]


def test_v2_6_59_scorer_penalizes_recent_offbeat_and_active_without_removing_candidates() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    source_key = "medium_swing:0:jammate_engine.styles.medium_swing.comping_patterns.get_pattern_candidates"
    history = {
        f"{source_key}:recent_comping": [
            {
                "name": "medium_swing_piano_2and_4_answer",
                "category": "region_lookup_offbeat_tail",
                "rhythm_family": "offbeat_tail",
                "weight_calibration_class": "offbeat",
                "continuity_class": "offbeat",
                "tail_push_risk": "none",
                "density": "medium",
            },
            {
                "name": "medium_swing_piano_reverse_charleston_1and_3",
                "category": "region_lookup_offbeat_conversation",
                "rhythm_family": "offbeat_conversation",
                "weight_calibration_class": "offbeat",
                "continuity_class": "offbeat",
                "tail_push_risk": "none",
                "density": "medium",
            },
            {
                "name": "medium_swing_piano_1_2and_4",
                "category": "region_lookup_charleston_tail",
                "rhythm_family": "charleston_tail",
                "weight_calibration_class": "active",
                "continuity_class": "active",
                "tail_push_risk": "none",
                "density": "active",
            },
        ]
    }
    adjusted = base._apply_piano_comping_history_continuity_scorer(candidates, history=history, source_key=source_key)
    by_name = {candidate.name: candidate for candidate in adjusted}

    assert len(adjusted) == len(candidates)
    offbeat = by_name["medium_swing_piano_2and_4_answer"]
    active = by_name["medium_swing_piano_1_2and_4"]
    stable = by_name["medium_swing_piano_anchor_1_3"]
    assert offbeat.metadata["history_continuity_scorer_version"] == "v2_6_59"
    assert offbeat.metadata["history_continuity_multiplier"] < 0.4
    assert "recent_offbeat_cluster_penalty" in offbeat.metadata["history_continuity_reasons"]
    assert active.metadata["history_continuity_multiplier"] < 0.2
    assert "recent_active_penalty" in active.metadata["history_continuity_reasons"]
    assert stable.metadata["history_continuity_multiplier"] >= 1.0


def test_v2_6_59_plan_region_marks_selected_piano_events_and_keeps_pitchless_boundary() -> None:
    style = get_style("medium_swing")
    history: dict[str, object] = {}
    region = HarmonicRegion(
        region_id="r1",
        chord_symbol="Cmaj7",
        next_chord_symbol="F7",
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=0.0,
        duration_beats=4.0,
    )
    plan = style.plan_region(region, {"style_pattern_history": history})
    piano_events = [event for event in plan.events if event.track == "piano"]
    assert piano_events
    for event in piano_events:
        assert event.metadata["history_continuity_scorer_version"] == "v2_6_59"
        assert event.metadata["history_continuity_scorer_applied"] is True
        assert event.metadata["history_continuity_contract"].startswith("Existing region-length candidate pool")
        assert "two_chord_bar" not in str(event.metadata)
        assert "midi_note" not in event.metadata
        assert "velocity" not in event.metadata
        assert "duration" not in event.metadata
    recent_keys = [key for key in history if key.endswith(":recent_comping")]
    assert recent_keys
