from __future__ import annotations

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime import PatternPlan
from jammate_engine.styles import base
from jammate_engine.styles.registry import get_style


def _region(region_id: str = "r", *, chord: str = "Cmaj7", duration: float = 4.0) -> HarmonicRegion:
    return HarmonicRegion(
        region_id=region_id,
        chord_symbol=chord,
        next_chord_symbol="Fmaj7",
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=8.0,
        duration_beats=duration,
    )


def test_v2_6_62_medium_swing_policy_exposes_region_first_backup_only_coverage_guard() -> None:
    policy = get_style("medium_swing").arrangement_policy
    assert policy["piano_region_first_coverage_guard"] is True
    assert policy["piano_region_first_coverage_guard_version"] == "v2_6_62"
    assert "backup-only" in policy["piano_region_first_coverage_guard_contract"]
    assert "ChordRegion" in policy["piano_region_first_coverage_guard_contract"]
    assert "two-chord-bar" in policy["piano_region_first_coverage_guard_contract"]


def test_v2_6_62_plan_region_stamps_coverage_metadata_without_inserting_when_selected_pattern_covers_region() -> None:
    style = get_style("medium_swing")
    plan = style.plan_region(_region(duration=2.0), {"style_pattern_history": {}})
    piano_events = [event for event in plan.events if event.track == "piano" and event.role == "harmonic"]

    assert piano_events
    assert plan.metadata["piano_region_first_coverage_guard_version"] == "v2_6_62"
    assert plan.metadata["piano_region_first_coverage_guard_checked"] is True
    assert plan.metadata["piano_region_first_coverage_guard_inserted"] is False
    for event in piano_events:
        metadata = event.metadata
        assert metadata["piano_region_first_coverage_guard_version"] == "v2_6_62"
        assert metadata["piano_region_first_coverage_guard_checked"] is True
        assert metadata["piano_region_first_coverage_guard_inserted"] is False
        assert metadata["piano_region_first_coverage_guard_outcome"] == "covered_by_selected_region_length_pattern"
        assert metadata["coverage_time_reference"] == "region_local_beats"
        assert metadata["coverage_region_duration_beats"] == 2.0
        assert metadata["coverage_region_length_family"] == "two_beat_region"
        assert metadata["coverage_guard_is_backup_only"] is True
        assert "two_chord_bar" not in str(metadata)
        assert "midi_note" not in metadata
        assert "velocity" not in metadata
        assert "duration" not in metadata


def test_v2_6_62_coverage_guard_inserts_single_pitchless_region_start_anchor_only_when_uncovered() -> None:
    region = _region(region_id="uncovered_two_beat", chord="G7", duration=2.0)
    empty_plan = PatternPlan(events=[], metadata={"style": "medium_swing", "selected_candidates": []})

    guarded = base._apply_piano_region_first_coverage_guard(
        empty_plan,
        region=region,
        style_name="medium_swing",
        enabled=True,
    )
    piano_events = [event for event in guarded.events if event.track == "piano" and event.role == "harmonic"]

    assert len(piano_events) == 1
    event = piano_events[0]
    assert event.pattern_id == "piano_region_first_coverage_fallback_anchor"
    assert event.local_beat == 0.0
    assert event.onset_beat == region.start_beat
    assert event.expression_hint == "comp_short"
    assert event.metadata["piano_region_first_coverage_guard_inserted"] is True
    assert event.metadata["piano_region_first_coverage_guard_outcome"] == "inserted_region_start_fallback_anchor"
    assert event.metadata["coverage_region_length_family"] == "two_beat_region"
    assert event.metadata["coverage_requires_region_start_anchor"] is True
    assert guarded.tail_policy.occupied_local_beats == (0.0,)
    assert guarded.beat1_movability.movable is False


def test_v2_6_62_coverage_guard_is_disabled_when_policy_flag_is_false() -> None:
    region = _region(region_id="disabled", duration=1.0)
    empty_plan = PatternPlan(events=[], metadata={})
    guarded = base._apply_piano_region_first_coverage_guard(
        empty_plan,
        region=region,
        style_name="medium_swing",
        enabled=False,
    )
    assert guarded is empty_plan
