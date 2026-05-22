from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.styles.medium_swing import arrangement_policy, voicing_policy


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_medium_swing_full_band_post_density_relief_checkpoint.py"
    spec = importlib.util.spec_from_file_location("generate_medium_swing_full_band_post_density_relief_checkpoint", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_6_81_declares_behavior_preserving_full_band_checkpoint_after_density_relief() -> None:
    policy = arrangement_policy.get_arrangement_policy()

    assert policy["piano_comping_two_beat_region_density_relief_policy_version"] == "v2_6_80"
    assert policy["medium_swing_full_band_post_density_relief_checkpoint"] is True
    assert policy["medium_swing_full_band_post_density_relief_checkpoint_version"] == "v2_6_81"
    assert "behavior-preserving full-band checkpoint" in policy["medium_swing_full_band_post_density_relief_checkpoint_contract"]
    assert "All The Things You Are is not over-thinned" in policy["medium_swing_full_band_post_density_relief_checkpoint_contract"]
    assert "does not change pattern" in policy["medium_swing_full_band_post_density_relief_checkpoint_contract"]
    assert policy["medium_swing_full_band_post_density_relief_checkpoint_milestone"] == "v2_6_81_medium_swing_full_band_post_density_relief_checkpoint"


def test_v2_6_81_keeps_existing_voicing_capability_explicit_opt_in_and_core_voicing_unchanged() -> None:
    policy = voicing_policy.get_voicing_policy()
    nested = policy.metadata["medium_swing_existing_voicing_capability_usage_policy"]

    assert policy.metadata["medium_swing_existing_voicing_capability_usage_policy_version"] == "v2_6_77"
    assert policy.metadata["medium_swing_existing_voicing_capability_low_register_clarity_guard_version"] == "v2_6_78"
    assert nested["available"] is True
    assert nested["enabled"] is False
    assert nested["ordinary_runtime_default"] is False
    assert nested["no_core_voicing_change"] is True
    assert policy.preferred_density == 4
    assert policy.preferred_disposition.value == "open"


def test_v2_6_81_static_audit_and_mock_acceptance_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()

    assert static["checkpoint_version"] == "v2_6_81"
    assert static["checkpoint_policy_enabled"] is True
    assert static["checkpoint_policy_version"] == "v2_6_81"
    assert static["two_beat_density_relief_policy_version"] == "v2_6_80"
    assert static["full_band_checkpoint_previous_version"] == "v2_6_79"
    assert static["anticipation_checkpoint_version"] == "v2_6_61"
    assert static["low_register_clarity_guard_version"] == "v2_6_78"
    assert static["existing_voicing_capability_policy_version"] == "v2_6_77"
    assert static["existing_voicing_capability_available"] is True
    assert static["existing_voicing_capability_default_enabled"] is False
    assert static["existing_voicing_capability_ordinary_runtime_default"] is False
    assert static["existing_voicing_capability_no_core_voicing_change"] is True
    assert static["base_preferred_density"] == 4
    assert static["base_preferred_disposition"] == "open"
    assert static["two_beat_candidate_count"] >= 7
    assert static["pattern_forbidden_expression_candidates"] == []
    assert static["pattern_forbidden_voicing_candidates"] == []
    assert static["bar_first_two_chord_bar_candidates"] == []

    outputs = [
        {
            "ok": True,
            "slug": "all_the_things_you_are",
            "track_presence_ok": True,
            "piano_note_events": 800,
            "bass_note_events": 400,
            "drum_note_events": 800,
            "piano_active_pattern_events": 192,
            "piano_two_beat_active_events": 24,
            "two_beat_start_anchor_events": 21,
            "two_beat_multi_touch_events": 0,
            "two_beat_anchor_ratio": 0.875,
            "active_anticipation_count": 5,
            "two_beat_previous_tail_anticipation_count": 1,
            "invalid_region_first_anticipations": [],
            "piano_voicing_events": 200,
            "grouped_spread_events": 8,
            "five_note_events": 6,
            "six_note_events": 2,
            "ordinary_body_5_6_events": 0,
            "optional_selected_events": 3,
            "consecutive_optional_events": 0,
            "voice_leading_warning_events": 0,
            "low_register_dense_events": 0,
            "bar_88_low_register_dense_events": 0,
            "max_top_note": 72,
            "min_piano_low_note": 43,
            "bass_span_violations": 0,
            "bass_target_continuity_mismatches": 0,
            "bass_repeated_root_violations": 0,
            "bass_root_echo_bad_same": 0,
            "bass_root_echo_bad_timing": 0,
            "pedal_cc64_event_count": 0,
            "pedal_warning_count": 0,
            "expression_warning_count": 0,
        },
        {
            "ok": True,
            "slug": "autumn_leaves",
            "track_presence_ok": True,
            "piano_note_events": 900,
            "bass_note_events": 450,
            "drum_note_events": 800,
            "piano_active_pattern_events": 190,
            "piano_two_beat_active_events": 134,
            "two_beat_start_anchor_events": 121,
            "two_beat_multi_touch_events": 4,
            "two_beat_anchor_ratio": 0.903,
            "active_anticipation_count": 14,
            "two_beat_previous_tail_anticipation_count": 13,
            "invalid_region_first_anticipations": [],
            "piano_voicing_events": 230,
            "grouped_spread_events": 7,
            "five_note_events": 5,
            "six_note_events": 2,
            "ordinary_body_5_6_events": 0,
            "optional_selected_events": 0,
            "consecutive_optional_events": 0,
            "voice_leading_warning_events": 0,
            "low_register_dense_events": 0,
            "bar_88_low_register_dense_events": 0,
            "max_top_note": 73,
            "min_piano_low_note": 43,
            "bass_span_violations": 0,
            "bass_target_continuity_mismatches": 0,
            "bass_repeated_root_violations": 0,
            "bass_root_echo_bad_same": 0,
            "bass_root_echo_bad_timing": 0,
            "pedal_cc64_event_count": 0,
            "pedal_warning_count": 0,
            "expression_warning_count": 0,
        },
    ]
    aggregate = module._aggregate(outputs)
    assert module._acceptance(static, outputs, aggregate)["passed"] is True
