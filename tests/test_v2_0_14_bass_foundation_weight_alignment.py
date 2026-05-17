from __future__ import annotations

import json
import random
from pathlib import Path

from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.core.form.form_expander import expand_form_to_regions
from jammate_engine.generation.bass_foundation import (
    BassFoundationGenerator,
    BassFoundationPolicy,
    effective_lane_weights_for_candidate,
    root_zone,
)
from jammate_engine.styles.medium_swing.bass_foundation_patterns import (
    THREE_BEAT_SKELETONS,
    get_bass_foundation_policy,
    get_pattern_candidates,
)

ROOT = Path(__file__).resolve().parents[1]


def test_complete_old_three_beat_skeleton_table_is_style_owned() -> None:
    ids = {spec.identifier: spec for spec in THREE_BEAT_SKELETONS}
    assert len(THREE_BEAT_SKELETONS) >= 22
    assert ids["C01_R_Third_Fifth"].weight_low > ids["C01_R_Third_Fifth"].weight_high
    assert ids["C08_R_Seventh_Fifth"].weight_high > ids["C08_R_Seventh_Fifth"].weight_low
    candidates = get_pattern_candidates({"region_duration_beats": 4.0, "chord_symbol": "Dm7", "next_chord_symbol": "G7"})
    assert any(candidate.metadata.get("skeleton_id") == "C08_R_Seventh_Fifth" for candidate in candidates)


def test_five_zone_lane_probability_and_degree_multiplier_are_active() -> None:
    policy = BassFoundationPolicy.from_dict(get_bass_foundation_policy())
    assert root_zone(28) == "very_low"
    assert root_zone(33) == "low"
    assert root_zone(38) == "middle"
    assert root_zone(43) == "high"
    assert root_zone(47) == "very_high"

    downward_candidate = next(c for c in get_pattern_candidates({}) if c.metadata.get("skeleton_id") == "C08_R_Seventh_Fifth")
    upward_candidate = next(c for c in get_pattern_candidates({}) if c.metadata.get("skeleton_id") == "C01_R_Third_Fifth")
    high_weights = effective_lane_weights_for_candidate("high", downward_candidate, policy)
    low_weights = effective_lane_weights_for_candidate("low", upward_candidate, policy)
    assert high_weights["lower"] > high_weights["upper"]
    assert low_weights["upper"] > low_weights["lower"]


def test_bass_foundation_debug_trace_reports_zone_lane_pattern_and_connector() -> None:
    leadsheet = json.loads((ROOT / "examples" / "leadsheets" / "all_the_things_you_are.json").read_text())
    timeline = expand_form_to_regions(normalize_leadsheet(parse_leadsheet(leadsheet)), choruses=1)
    plan = BassFoundationGenerator().generate(
        regions=timeline.regions,
        pattern_source=get_pattern_candidates,
        policy=BassFoundationPolicy.from_dict(get_bass_foundation_policy()),
        rng=random.Random(214),
    )
    segments = plan.metadata["segments"]
    assert segments
    assert all("zone" in segment for segment in segments)
    assert all("selected_lane" in segment for segment in segments)
    assert all("lane_weights" in segment for segment in segments)
    assert all("pattern_zone_weight" in segment for segment in segments)
    assert all("beat4_connector_kind" in segment for segment in segments)
    notes = [int(event.metadata["resolved_midi_note"]) for event in plan.events]
    assert min(notes) >= 26
    assert max(notes) <= 48


def test_major_and_six_quality_filters_are_applied_to_selected_skeletons() -> None:
    generator = BassFoundationGenerator()
    policy = BassFoundationPolicy.from_dict(get_bass_foundation_policy())

    major_chart = {"title": "Major filter", "key": "C", "bars": [{"chords": [{"symbol": "Cmaj7", "beats": 4}]}, {"chords": [{"symbol": "Fmaj7", "beats": 4}]}]}
    major_timeline = expand_form_to_regions(normalize_leadsheet(parse_leadsheet(major_chart)), choruses=1)
    major_plan = generator.generate(regions=major_timeline.regions, pattern_source=get_pattern_candidates, policy=policy, rng=random.Random(2))
    assert all("Fourth" not in tuple(segment.get("skeleton_degrees", ())[1:]) for segment in major_plan.metadata["segments"] if segment["chord_symbol"] == "Cmaj7")

    six_chart = {"title": "Six filter", "key": "C", "bars": [{"chords": [{"symbol": "C6", "beats": 4}]}, {"chords": [{"symbol": "Fmaj7", "beats": 4}]}]}
    six_timeline = expand_form_to_regions(normalize_leadsheet(parse_leadsheet(six_chart)), choruses=1)
    six_plan = generator.generate(regions=six_timeline.regions, pattern_source=get_pattern_candidates, policy=policy, rng=random.Random(6))
    assert all("Seventh" not in tuple(segment.get("skeleton_degrees", ())[1:]) for segment in six_plan.metadata["segments"] if segment["chord_symbol"] == "C6")


def test_repeated_root_start_disallows_current_root_as_beat4() -> None:
    class Region:
        chord_symbol = "Cmaj7"
        next_chord_symbol = "Fmaj7"

    policy = BassFoundationPolicy.from_dict(get_bass_foundation_policy())
    choices = BassFoundationGenerator()._generate_beat4_candidates(Region(), beat3_note=43, nextR_note=41, policy=policy, disallow_current_root_pc=True)
    assert choices
    assert all(choice.note % 12 != 0 for choice in choices)
