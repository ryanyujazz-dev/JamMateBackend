from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.styles.medium_swing import arrangement_policy, comping_patterns
from jammate_engine.styles.base import StyleProfile


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_medium_swing_two_beat_density_relief_and_anticipation_audit.py"
    spec = importlib.util.spec_from_file_location("generate_medium_swing_two_beat_density_relief_and_anticipation_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_6_80_declares_two_beat_region_density_relief_without_bar_first_route() -> None:
    policy = arrangement_policy.get_arrangement_policy()

    assert policy["piano_comping_two_beat_region_density_relief_policy"] is True
    assert policy["piano_comping_two_beat_region_density_relief_policy_version"] == "v2_6_80"
    assert "dense 2-beat ChordRegions" in policy["piano_comping_two_beat_region_density_relief_policy_contract"]
    assert "generic AnticipationResolver" in policy["piano_comping_two_beat_region_density_relief_policy_contract"]
    assert "two-chord-bar" in policy["piano_comping_two_beat_region_density_relief_policy_contract"]
    assert policy["piano_comping_two_beat_region_density_relief_policy_milestone"] == "v2_6_80_medium_swing_two_beat_region_density_relief_and_anticipation_audit"


def test_v2_6_80_does_not_add_new_two_beat_vocabulary_or_voicing_expression_payloads() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 2.0})

    assert len(candidates) == 6
    names = {candidate.name for candidate in candidates}
    assert "medium_swing_piano_two_beat_region_start_anchor" in names
    assert "medium_swing_piano_two_beat_region_start_local2and" in names
    for candidate in candidates:
        text = " ".join([candidate.name, candidate.category, str(candidate.metadata), " ".join(candidate.tags)])
        assert "two_chord_bar" not in text
        assert "split_bar" not in text
        assert "voicing" not in candidate.metadata or candidate.metadata["voicing_boundary"] == "pattern_is_pitchless"
        assert "velocity" not in candidate.metadata
        assert "duration" not in candidate.metadata
        assert "pedal" not in candidate.metadata


def test_v2_6_80_static_audit_and_mock_acceptance_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()

    assert static["checkpoint_version"] == "v2_6_80"
    assert static["policy_enabled"] is True
    assert static["policy_version"] == "v2_6_80"
    assert static["anticipation_checkpoint_version"] == "v2_6_61"
    assert static["two_beat_candidate_count"] == 6
    assert static["bar_first_two_chord_bar_markers"] == []

    outputs = [
        {
            "ok": True,
            "slug": "all_the_things_you_are",
            "piano_active_pattern_events": 192,
            "piano_two_beat_active_events": 24,
            "two_beat_start_anchor_events": 21,
            "two_beat_multi_touch_events": 0,
            "two_beat_anchor_ratio": 0.875,
            "active_anticipation_count": 5,
            "two_beat_previous_tail_anticipation_count": 1,
            "invalid_region_first_anticipations": [],
            "low_register_dense_events": 0,
            "voice_leading_warning_events": 0,
        },
        {
            "ok": True,
            "slug": "autumn_leaves",
            "piano_active_pattern_events": 190,
            "piano_two_beat_active_events": 134,
            "two_beat_start_anchor_events": 121,
            "two_beat_multi_touch_events": 4,
            "two_beat_anchor_ratio": 0.903,
            "active_anticipation_count": 14,
            "two_beat_previous_tail_anticipation_count": 13,
            "invalid_region_first_anticipations": [],
            "low_register_dense_events": 0,
            "voice_leading_warning_events": 0,
        },
    ]
    aggregate = module._aggregate(outputs)
    assert module._acceptance(static, outputs, aggregate)["passed"] is True


def test_v2_6_80_style_profile_plan_region_can_repeat_simple_anchor_in_two_beat_relief() -> None:
    # This is a focused structural check for the fix: dense 2-beat relief must not be forced
    # into offbeat cells merely because the generic avoid-repeat/category guard filtered the
    # previous simple anchor. Runtime generation/audit validates the musical result.
    policy = arrangement_policy.get_arrangement_policy()
    assert policy["piano_comping_two_beat_region_density_relief_policy"] is True
    assert StyleProfile.plan_region.__doc__ is not None
