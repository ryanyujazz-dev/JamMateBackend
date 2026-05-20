from __future__ import annotations

from dataclasses import replace

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles import base
from jammate_engine.styles.medium_swing import comping_patterns
from jammate_engine.styles.medium_swing.arrangement_policy import get_arrangement_policy
from jammate_engine.styles.registry import get_style

SOURCE_KEY = "medium_swing:0:jammate_engine.styles.medium_swing.comping_patterns.get_pattern_candidates"


def _region() -> HarmonicRegion:
    return HarmonicRegion(
        region_id="r1",
        chord_symbol="Cmaj7",
        next_chord_symbol="F7",
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=0.0,
        duration_beats=4.0,
    )


def test_v2_6_67_policy_exposes_active_fill_busy_multi_region_history_contract() -> None:
    policy = get_arrangement_policy()
    assert policy["piano_comping_history_continuity_scorer"] is True
    # Compatibility contract remains for the older continuity scorer.
    assert policy["piano_comping_history_continuity_scorer_version"] == "v2_6_59"
    assert policy["piano_comping_active_fill_busy_multi_region_history_scorer"] is True
    assert policy["piano_comping_active_fill_busy_multi_region_history_scorer_version"] == "v2_6_67"
    contract = policy["piano_comping_active_fill_busy_multi_region_history_contract"]
    assert "multi-region active/fill/busy/push/tail-push memory" in contract
    assert "ChordRegion-first" in contract
    assert "bar-first" in contract


def test_v2_6_67_scorer_penalizes_active_busy_and_tail_push_clusters_without_removing_candidates() -> None:
    candidates = list(comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0}))
    active_candidate = next(c for c in candidates if c.name == "medium_swing_piano_1_2and_4")
    busy_candidate = replace(
        active_candidate,
        name="probe_busy_fill_candidate",
        category="probe_busy_fill",
        metadata={
            **dict(active_candidate.metadata),
            "density": "busy",
            "weight_calibration_class": "busy",
            "rhythm_family": "busy_fill",
            "phrase_role": "phrase_fill",
            "pattern_function": "busy_fill_probe",
        },
    )
    candidates.append(busy_candidate)
    history = {
        f"{SOURCE_KEY}:recent_comping": [
            {
                "name": "prev_tail_push",
                "rhythm_family": "tail_push",
                "weight_calibration_class": "tail_push",
                "continuity_class": "tail_push",
                "activity_class": "tail_push",
                "tail_push_risk": "high",
                "density": "rare_push",
                "is_active": False,
                "is_fill": False,
                "is_busy": False,
                "is_push": True,
                "is_tail_push": True,
                "is_offbeat": False,
            },
            {
                "name": "prev_active",
                "rhythm_family": "charleston_tail",
                "weight_calibration_class": "active",
                "continuity_class": "active",
                "activity_class": "active",
                "tail_push_risk": "none",
                "density": "active",
                "is_active": True,
                "is_fill": False,
                "is_busy": False,
                "is_push": False,
                "is_tail_push": False,
                "is_offbeat": False,
            },
            {
                "name": "prev_busy",
                "rhythm_family": "busy_fill",
                "weight_calibration_class": "busy",
                "continuity_class": "busy",
                "activity_class": "busy",
                "tail_push_risk": "none",
                "density": "busy",
                "is_active": True,
                "is_fill": True,
                "is_busy": True,
                "is_push": False,
                "is_tail_push": False,
                "is_offbeat": False,
            },
        ]
    }
    adjusted = base._apply_piano_comping_history_continuity_scorer(candidates, history=history, source_key=SOURCE_KEY, region=_region(), context={})
    by_name = {candidate.name: candidate for candidate in adjusted}

    assert len(adjusted) == len(candidates)
    active = by_name["medium_swing_piano_1_2and_4"]
    busy = by_name["probe_busy_fill_candidate"]
    tail_push = by_name["medium_swing_piano_1_4and_rare_push"]
    assert active.metadata["medium_swing_active_fill_busy_history_policy_version"] == "v2_6_67"
    assert active.metadata["history_recent_active_count"] >= 1
    assert active.metadata["history_continuity_multiplier"] < 0.2
    assert "recent_active_penalty" in active.metadata["history_continuity_reasons"]
    assert busy.metadata["history_candidate_is_busy"] is True
    assert busy.metadata["history_continuity_multiplier"] < 0.01
    assert "busy_after_busy_near_block" in busy.metadata["history_continuity_reasons"]
    assert "busy_outside_explicit_high_energy_or_phrase_end_near_block" in busy.metadata["history_continuity_reasons"]
    assert tail_push.metadata["history_candidate_is_tail_push"] is True
    assert tail_push.metadata["history_continuity_multiplier"] < 0.02
    assert "recent_tail_push_penalty" in tail_push.metadata["history_continuity_reasons"]


def test_v2_6_67_scorer_rewards_stable_no_4and_recovery_after_recent_push() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    history = {
        f"{SOURCE_KEY}:recent_comping": [
            {
                "name": "prev_tail_push",
                "rhythm_family": "tail_push",
                "weight_calibration_class": "tail_push",
                "continuity_class": "tail_push",
                "activity_class": "tail_push",
                "tail_push_risk": "high",
                "density": "rare_push",
                "is_active": False,
                "is_fill": False,
                "is_busy": False,
                "is_push": True,
                "is_tail_push": True,
                "is_offbeat": False,
            }
        ]
    }
    adjusted = base._apply_piano_comping_history_continuity_scorer(candidates, history=history, source_key=SOURCE_KEY, region=_region(), context={})
    by_name = {candidate.name: candidate for candidate in adjusted}
    recovery = by_name["medium_swing_piano_1_4_tail"]

    assert recovery.metadata["history_candidate_is_no_4and_delayed_tail"] is True
    assert recovery.metadata["history_continuity_multiplier"] > 1.0
    assert "stable_reset_after_active_bonus" in recovery.metadata["history_continuity_reasons"]
    assert "no_4and_delayed_tail_after_recent_push_bonus" in recovery.metadata["history_continuity_reasons"]


def test_v2_6_67_plan_region_marks_selected_events_and_keeps_boundaries_pitchless() -> None:
    style = get_style("medium_swing")
    history: dict[str, object] = {}
    plan = style.plan_region(_region(), {"style_pattern_history": history})
    piano_events = [event for event in plan.events if event.track == "piano"]
    assert piano_events
    for event in piano_events:
        metadata = event.metadata
        assert metadata["history_continuity_scorer_version"] == "v2_6_59"
        assert metadata["medium_swing_active_fill_busy_history_policy_version"] == "v2_6_67"
        assert metadata["active_fill_busy_multi_region_history_policy_version"] == "v2_6_67"
        assert metadata["history_continuity_scorer_applied"] is True
        assert "parallel selector" in metadata["history_continuity_contract"]
        assert "two_chord_bar" not in str(metadata)
        assert "midi_note" not in metadata
        assert "velocity" not in metadata
        assert "duration" not in metadata
    recent_keys = [key for key in history if key.endswith(":recent_comping")]
    assert recent_keys
    recent = history[recent_keys[0]]
    assert isinstance(recent, list)
    assert recent[-1]["activity_class"] in {"stable", "offbeat", "active", "fill", "busy", "tail_push"}
