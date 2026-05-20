from __future__ import annotations

import random

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles.medium_swing import comping_patterns
from jammate_engine.styles.registry import get_style


def _positive_candidate_names(duration: float) -> set[str]:
    return {candidate.name for candidate in comping_patterns.get_pattern_candidates({"region_duration_beats": duration}) if candidate.weight > 0.0}


def test_v2_6_57_four_beat_region_lookup_activates_v2_6_56_vocabulary_without_bar_first_route() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    names = _positive_candidate_names(4.0)
    assert "medium_swing_piano_anchor_1_3" in names
    assert "medium_swing_piano_reverse_charleston_1and_3" in names
    assert "medium_swing_piano_2and_4_answer" in names
    assert "medium_swing_piano_1_2and_4" in names
    assert "medium_swing_piano_1_4and_rare_push" in names

    for candidate in candidates:
        assert candidate.metadata["pattern_library_version"] == "v2_6_56"
        assert candidate.metadata["candidate_lookup_policy_version"] == "v2_6_57"
        assert candidate.metadata["candidate_lookup_policy"] == "region_length_aware"
        assert candidate.metadata["candidate_lookup_key"] == "four_beat_region"
        assert candidate.metadata["time_reference"] == "region_local_beats"
        assert "two_chord_bar" not in candidate.name
        assert "two_chord_bar" not in candidate.category
        assert "two_chord_bar" not in candidate.tags
        assert max(candidate.rhythm_beats, default=0.0) < 4.0


def test_v2_6_57_two_beat_region_lookup_activates_short_region_candidates_only() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 2.0})
    names = _positive_candidate_names(2.0)
    assert "medium_swing_piano_two_beat_region_start_local2" in names
    assert "medium_swing_piano_two_beat_region_start_local1and" in names
    assert "medium_swing_piano_two_beat_region_local1and_only" in names
    assert all(candidate.name.startswith("medium_swing_piano_two_beat_region_") for candidate in candidates)
    assert all(candidate.metadata["candidate_lookup_key"] == "two_beat_region" for candidate in candidates)
    assert all(max(candidate.rhythm_beats, default=0.0) < 2.0 for candidate in candidates)


def test_v2_6_57_one_beat_region_lookup_keeps_anchor_dominant_and_rest_guarded() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 1.0})
    by_cell = {candidate.metadata["rhythmic_cell"]: candidate for candidate in candidates}
    assert by_cell["start"].weight > by_cell["local_and"].weight > 0.0
    assert by_cell["rest_if_covered"].weight == 0.0
    assert by_cell["rest_if_covered"].metadata["context_gate"] == "covered_by_neighboring_regions_only"
    assert all(candidate.metadata["candidate_lookup_key"] == "one_beat_region" for candidate in candidates)
    assert all(max(candidate.rhythm_beats, default=0.0) < 1.0 for candidate in candidates)


def test_v2_6_57_style_planner_routes_by_chord_region_length_not_bar_shape() -> None:
    style = get_style("medium_swing")
    assert style.arrangement_policy["piano_region_length_candidate_lookup_policy_version"] == "v2_6_57"
    history: dict[str, str] = {}
    rng = random.Random(12)

    four = HarmonicRegion(
        region_id="four_r1",
        chord_symbol="Cmaj7",
        next_chord_symbol="F7",
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=0.0,
        duration_beats=4.0,
    )
    two = HarmonicRegion(
        region_id="two_r1",
        chord_symbol="G7",
        next_chord_symbol="Cmaj7",
        chorus_index=0,
        bar_index=1,
        chord_index=1,
        start_beat=2.0,
        duration_beats=2.0,
    )
    one = HarmonicRegion(
        region_id="one_r1",
        chord_symbol="D7",
        next_chord_symbol="G7",
        chorus_index=0,
        bar_index=2,
        chord_index=3,
        start_beat=3.0,
        duration_beats=1.0,
    )

    for region, expected_prefix, expected_duration in (
        (four, "medium_swing_piano_", 4.0),
        (two, "medium_swing_piano_two_beat_region_", 2.0),
        (one, "medium_swing_piano_one_beat_region_", 1.0),
    ):
        plan = style.plan_region(region, {"rng": rng, "style_pattern_history": history})
        piano_events = [event for event in plan.events if event.track == "piano"]
        assert piano_events
        assert all(event.pattern_id.startswith(expected_prefix) for event in piano_events)
        assert all(event.metadata["region_duration_beats"] == expected_duration for event in piano_events)
        assert all(event.metadata["time_reference"] == "region_local_beats" for event in piano_events)
