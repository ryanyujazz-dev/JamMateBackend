from __future__ import annotations

import random

from jammate_engine.core.form.form_expander import expand_form_to_regions
from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.generation.bass_foundation import (
    BassFoundationGenerator,
    BassFoundationPolicy,
    effective_lane_weights_for_candidate,
)
from jammate_engine.styles.medium_swing.bass_foundation_patterns import (
    THREE_BEAT_SKELETONS,
    get_bass_foundation_policy,
    get_pattern_candidates,
)


OLD_ENGINE_SKELETON_TABLE = {
    "C01_R_Third_Fifth": ("chord", ("R", "Third", "Fifth"), 14.00, 12.00, 10.67, False),
    "C02_R_Fifth_Third": ("chord", ("R", "Fifth", "Third"), 9.50, 9.00, 8.50, False),
    "C03_R_R_Fifth": ("chord", ("R", "R", "Fifth"), 9.56, 9.00, 8.44, True),
    "C04_R_Fifth_R": ("chord", ("R", "Fifth", "R"), 4.00, 4.00, 3.60, True),
    "C05_R_R_Third": ("chord", ("R", "R", "Third"), 10.12, 9.00, 8.44, True),
    "C06_R_Third_R": ("chord", ("R", "Third", "R"), 3.00, 3.00, 2.70, True),
    "C07_R_Fifth_Seventh": ("chord", ("R", "Fifth", "Seventh"), 8.36, 9.00, 10.29, False),
    "C08_R_Seventh_Fifth": ("chord", ("R", "Seventh", "Fifth"), 9.75, 12.00, 15.00, False),
    "C09_R_Third_Seventh": ("chord", ("R", "Third", "Seventh"), 5.25, 6.00, 6.75, False),
    "C10_R_Seventh_Third": ("chord", ("R", "Seventh", "Third"), 4.88, 6.00, 7.12, False),
    "C11_R_R_Seventh": ("chord", ("R", "R", "Seventh"), 7.50, 9.00, 10.50, True),
    "C12_R_Seventh_R": ("chord", ("R", "Seventh", "R"), 2.70, 3.00, 3.00, True),
    "S01_R_Second_Third": ("scale", ("R", "Second", "Third"), 12.50, 10.00, 8.75, False),
    "S02_R_Third_Fourth": ("scale", ("R", "Third", "Fourth"), 11.88, 10.00, 9.38, False),
    "S03_R_Fourth_Fifth": ("scale", ("R", "Fourth", "Fifth"), 7.29, 6.00, 5.57, False),
    "S04_R_Fifth_Sixth": ("scale", ("R", "Fifth", "Sixth"), 4.57, 4.00, 4.00, False),
    "S05_R_Sixth_Seventh": ("scale", ("R", "Sixth", "Seventh"), 2.00, 2.00, 2.33, False),
    "S06_R_Third_Second": ("scale", ("R", "Third", "Second"), 4.00, 4.00, 4.50, False),
    "S07_R_Fourth_Third": ("scale", ("R", "Fourth", "Third"), 2.00, 2.00, 2.14, False),
    "S08_R_Fifth_Fourth": ("scale", ("R", "Fifth", "Fourth"), 1.86, 2.00, 2.29, False),
    "S09_R_Sixth_Fifth": ("scale", ("R", "Sixth", "Fifth"), 1.86, 2.00, 2.43, False),
    "S10_R_Seventh_Sixth": ("scale", ("R", "Seventh", "Sixth"), 7.31, 9.00, 11.25, False),
}


def test_three_beat_skeleton_table_exactly_matches_old_engine_weights() -> None:
    actual = {spec.identifier: spec for spec in THREE_BEAT_SKELETONS}
    assert set(actual) == set(OLD_ENGINE_SKELETON_TABLE)
    for identifier, (group, degrees, low, mid, high, allow_repetition) in OLD_ENGINE_SKELETON_TABLE.items():
        spec = actual[identifier]
        assert spec.group == group
        assert spec.degrees == degrees
        assert spec.weight_low == low
        assert spec.weight_mid == mid
        assert spec.weight_high == high
        assert spec.allow_repetition is allow_repetition


def test_lane_weights_are_old_engine_table_times_degree_multipliers_without_caps() -> None:
    policy = BassFoundationPolicy.from_dict(get_bass_foundation_policy())
    candidate = next(c for c in get_pattern_candidates({"region_duration_beats": 4.0}) if c.metadata.get("skeleton_id") == "S02_R_Third_Fourth")
    weights = effective_lane_weights_for_candidate("high", candidate, policy)

    # Old engine formula for high zone S02: base high table (13/82/5), then
    # Third@1.0 and Fourth@0.85 multipliers. No extra register-gravity cap.
    expected_upper = 13.0 * (3.00 ** 1.0) * (2.40 ** 0.85)
    expected_lower = 82.0 * (0.20 ** 1.0) * (0.30 ** 0.85)
    expected_mixed = 5.0 * (0.35 ** 1.0) * (0.40 ** 0.85)
    assert abs(weights["upper"] - expected_upper) < 1e-9
    assert abs(weights["lower"] - expected_lower) < 1e-9
    assert abs(weights["mixed"] - expected_mixed) < 1e-9


def test_candidate_preflight_filters_illegal_skeletons_before_weighted_choice() -> None:
    chart = {
        "title": "Major skeleton filter",
        "key": "C",
        "bars": [
            {"chords": [{"symbol": "Cmaj7", "beats": 4}]},
            {"chords": [{"symbol": "Fmaj7", "beats": 4}]},
            {"chords": [{"symbol": "Bbmaj7", "beats": 4}]},
        ],
    }
    timeline = expand_form_to_regions(normalize_leadsheet(parse_leadsheet(chart)), choruses=1)
    plan = BassFoundationGenerator().generate(
        regions=timeline.regions,
        pattern_source=get_pattern_candidates,
        policy=BassFoundationPolicy.from_dict(get_bass_foundation_policy()),
        rng=random.Random(112),
    )
    for segment in plan.metadata["segments"]:
        if segment.get("chord_symbol") == "Cmaj7":
            assert "Fourth" not in tuple(segment.get("skeleton_degrees", ()))[1:]
            assert segment.get("candidate_preflight") == "old_engine_legal_skeleton_pool"
            assert segment.get("legal_skeleton_pool_size", 0) > 0


def test_old_engine_selection_does_not_apply_immediate_history_ban() -> None:
    generation_source = __import__(
        "jammate_engine.generation.bass_foundation",
        fromlist=["BassFoundationGenerator"],
    ).__loader__.get_source("jammate_engine.generation.bass_foundation")
    assert 'c.name != history.get("last_candidate")' not in generation_source
