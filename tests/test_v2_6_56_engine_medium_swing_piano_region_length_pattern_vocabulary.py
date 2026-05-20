from __future__ import annotations

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles.medium_swing import comping_patterns
from jammate_engine.styles.registry import get_style


FORBIDDEN_PATTERN_KEYS = {"midi_note", "midi_notes", "notes", "velocity", "duration", "duration_beats", "pedal", "voicing", "voicing_type"}


def _assert_pitchless(candidate) -> None:
    assert candidate.metadata["pattern_library_version"] == "v2_6_56"
    assert candidate.metadata["time_reference"] == "region_local_beats"
    assert candidate.metadata["voicing_boundary"] == "pattern_is_pitchless"
    assert candidate.metadata["expression_boundary"] == "pattern_carries_semantic_hint_not_final_values"
    assert "two_chord_bar" not in candidate.category
    assert "two_chord_bar" not in candidate.name
    assert "two_chord_bar" not in candidate.tags
    for key in FORBIDDEN_PATTERN_KEYS:
        assert key not in candidate.metadata
    for event in candidate.events:
        for key in FORBIDDEN_PATTERN_KEYS:
            assert key not in event.metadata
        assert event.track == "piano"
        assert event.role == "harmonic"
        assert event.metadata["time_reference"] == "region_local_beats"
        assert event.metadata.get("semantic_expression_hint") in {"soft_hold", "light_stab", "accent_stab", "accent_hold", "backbeat_hold", "final_hold"}


def test_v2_6_56_four_beat_region_vocabulary_is_region_local_and_expanded() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    names = {candidate.name for candidate in candidates}
    cells = {candidate.metadata["rhythmic_cell"] for candidate in candidates}
    families = {candidate.metadata["rhythm_family"] for candidate in candidates}

    assert len(candidates) >= 12
    assert "medium_swing_piano_anchor_1_3" in names
    assert "medium_swing_piano_reverse_charleston_1and_3" in names
    assert "medium_swing_piano_2and_4_answer" in names
    assert "medium_swing_piano_1_2and_4" in names
    assert "1_3" in cells
    assert "1and_3" in cells
    assert "2and_4" in cells
    assert "1_2and_4" in cells
    assert "tail_push" in families
    assert "offbeat_conversation" in families

    for candidate in candidates:
        _assert_pitchless(candidate)
        assert candidate.metadata["region_length_family"] == "four_beat_region"
        assert candidate.metadata["region_shape"] == "four_beat_region"
        assert max(candidate.rhythm_beats, default=0.0) < 4.0


def test_v2_6_56_two_beat_region_replaces_two_chord_bar_path() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 2.0})
    names = {candidate.name for candidate in candidates}
    cells = {candidate.metadata["rhythmic_cell"] for candidate in candidates}

    assert len(candidates) >= 6
    assert "medium_swing_piano_two_beat_region_start_anchor" in names
    assert "medium_swing_piano_two_beat_region_start_local1and" in names
    assert "medium_swing_piano_two_beat_region_start_local2" in names
    assert "start" in cells
    assert "start_local1and" in cells
    assert "start_local2" in cells
    assert "start_local2and" in cells

    for candidate in candidates:
        _assert_pitchless(candidate)
        assert candidate.metadata["region_length_family"] == "two_beat_region"
        assert max(candidate.rhythm_beats, default=0.0) < 2.0


def test_v2_6_56_one_beat_region_has_anchor_offbeat_and_rest_if_covered() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 1.0})
    cells = {candidate.metadata["rhythmic_cell"] for candidate in candidates}
    assert cells == {"start", "local_and", "rest_if_covered"}
    for candidate in candidates:
        _assert_pitchless(candidate)
        assert candidate.metadata["region_length_family"] == "one_beat_region"
        assert max(candidate.rhythm_beats, default=0.0) < 1.0


def test_v2_6_56_pattern_describe_contract_exposes_region_length_boundary() -> None:
    description = comping_patterns.describe_pattern_library({"region_duration_beats": 4.0})
    assert description["version"] == "v2_6_56"
    assert "region_length_aware" in description["boundary_notes"]
    assert "no_bar_first_two_chord_bar_logic" in description["boundary_notes"]


def test_v2_6_56_style_planner_selects_region_length_candidates_without_parallel_source() -> None:
    style = get_style("medium_swing")
    assert style.arrangement_policy["piano_region_length_pattern_vocabulary_version"] == "v2_6_56"
    region = HarmonicRegion(
        region_id="short_r1",
        chord_symbol="G7",
        next_chord_symbol="Cmaj7",
        chorus_index=0,
        bar_index=0,
        chord_index=1,
        start_beat=2.0,
        duration_beats=2.0,
    )
    plan = style.plan_region(region, {"style_pattern_history": {}})
    piano_events = [event for event in plan.events if event.track == "piano"]
    assert piano_events
    assert all(event.metadata["region_duration_beats"] == 2.0 for event in piano_events)
    assert all(event.metadata["candidate"].startswith("medium_swing_piano_two_beat_region_") for event in piano_events)
