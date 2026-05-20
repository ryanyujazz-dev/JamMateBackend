from __future__ import annotations

from collections import defaultdict

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles.medium_swing import comping_patterns
from jammate_engine.styles.registry import get_style


def _weight_ratios(duration: float) -> dict[str, float]:
    weights: dict[str, float] = defaultdict(float)
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": duration})
    total = sum(max(0.0, candidate.weight) for candidate in candidates)
    assert total > 0.0
    for candidate in candidates:
        weights[str(candidate.metadata.get("weight_calibration_class"))] += max(0.0, candidate.weight)
        assert candidate.metadata["pattern_library_version"] == "v2_6_56"
        assert candidate.metadata["candidate_lookup_policy_version"] == "v2_6_57"
        assert candidate.metadata["weight_calibration_policy_version"] == "v2_6_58"
        assert candidate.metadata["weight_calibration_policy"] == "stable_primary_offbeat_secondary_active_and_tail_push_controlled"
        assert "two_chord_bar" not in candidate.name
        assert "two_chord_bar" not in candidate.category
        assert "two_chord_bar" not in candidate.tags
    return {key: value / total for key, value in weights.items()}


def test_v2_6_58_four_beat_weights_make_stable_primary_and_control_push() -> None:
    ratios = _weight_ratios(4.0)
    assert 0.65 <= ratios["stable"] <= 0.78
    assert 0.18 <= ratios["offbeat"] <= 0.30
    assert 0.02 <= ratios["active"] <= 0.08
    assert ratios["tail_push"] <= 0.01

    candidates = {candidate.name: candidate for candidate in comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})}
    assert candidates["medium_swing_piano_charleston_1_2and"].weight < 1.25
    assert candidates["medium_swing_piano_anchor_1_3"].weight >= 0.8
    assert candidates["medium_swing_piano_1_4and_rare_push"].weight < candidates["medium_swing_piano_1_2and_4"].weight


def test_v2_6_58_short_region_weights_keep_anchor_primary_and_offbeats_secondary() -> None:
    two = _weight_ratios(2.0)
    one = _weight_ratios(1.0)
    assert two["stable"] >= 0.80
    assert 0.05 <= two["offbeat"] <= 0.20
    assert one["stable"] >= 0.95
    assert one["offbeat"] <= 0.05

    candidates = {candidate.metadata["rhythmic_cell"]: candidate for candidate in comping_patterns.get_pattern_candidates({"region_duration_beats": 2.0})}
    assert candidates["start"].weight > candidates["start_local2and"].weight
    assert candidates["start"].weight > candidates["start_local1and"].weight


def test_v2_6_58_style_policy_exposes_weight_calibration_without_parallel_selector() -> None:
    style = get_style("medium_swing")
    assert style.arrangement_policy["piano_region_length_pattern_vocabulary_version"] == "v2_6_56"
    assert style.arrangement_policy["piano_region_length_candidate_lookup_policy_version"] == "v2_6_57"
    assert style.arrangement_policy["piano_region_length_weight_calibration_policy_version"] == "v2_6_58"
    assert "existing region-length pattern library" in style.arrangement_policy["piano_region_length_weight_calibration_contract"]
    assert "parallel selector" in style.arrangement_policy["piano_region_length_weight_calibration_contract"]

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
    plan = style.plan_region(region, {"style_pattern_history": {}})
    piano_events = [event for event in plan.events if event.track == "piano"]
    assert piano_events
    assert all(event.metadata["time_reference"] == "region_local_beats" for event in piano_events)
    assert all(event.metadata["region_duration_beats"] == 4.0 for event in piano_events)
