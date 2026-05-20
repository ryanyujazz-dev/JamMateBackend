from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.styles.medium_swing import arrangement_policy, percussion_patterns, voicing_policy


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_medium_swing_drum_piano_interaction_audit.py"
    spec = importlib.util.spec_from_file_location("generate_medium_swing_drum_piano_interaction_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_6_83_declares_drum_piano_interaction_audit_without_behavior_change() -> None:
    arrangement = arrangement_policy.get_arrangement_policy()
    policy = voicing_policy.get_voicing_policy()

    assert arrangement["medium_swing_bass_piano_interaction_audit_version"] == "v2_6_82"
    assert arrangement["medium_swing_drum_piano_interaction_audit"] is True
    assert arrangement["medium_swing_drum_piano_interaction_audit_version"] == "v2_6_83"
    assert "drum ride/hi-hat foundation and piano comping interaction" in arrangement["medium_swing_drum_piano_interaction_audit_contract"]
    assert "does not add drum fills" in arrangement["medium_swing_drum_piano_interaction_audit_contract"]
    assert arrangement["medium_swing_drum_piano_interaction_audit_milestone"] == "v2_6_83_medium_swing_drum_piano_interaction_audit"

    nested = policy.metadata["medium_swing_existing_voicing_capability_usage_policy"]
    assert nested["enabled"] is False
    assert nested["ordinary_runtime_default"] is False
    assert nested["no_core_voicing_change"] is True
    assert policy.preferred_density == 4
    assert policy.preferred_disposition.value == "open"


def test_v2_6_83_uses_existing_region_local_drum_ride_candidates_for_audit_only() -> None:
    four = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    two = percussion_patterns.get_pattern_candidates({"region_duration_beats": 2.0})

    assert [candidate.name for candidate in four] == ["medium_swing_drums_spang_a_lang_hat_2_4"]
    assert [candidate.name for candidate in two] == ["medium_swing_drums_two_beat_spang_fragment"]
    assert [candidate.category for candidate in four] == ["ride_time_foundation"]
    assert [candidate.category for candidate in two] == ["ride_time_two_chord_fragment"]
    assert sum(len(candidate.events) for candidate in four) == 8
    assert sum(len(candidate.events) for candidate in two) == 4
    assert all(not candidate.tail_policy.can_receive_next_chord_anticipation for candidate in (*four, *two))
    assert all(candidate.events[0].track == "drums" for candidate in (*four, *two))


def test_v2_6_83_drum_role_reconstruction_maps_swing_offbeats_to_ride_skip() -> None:
    module = _load_script_module()

    assert module._swing_local_beat(1.5) == 1.6667
    assert module._swing_local_beat(3.5) == 3.6667
    assert module._drum_roles_for_piano_hit("four_beat_region", 0.0) == ["ride_medium"]
    assert module._drum_roles_for_piano_hit("four_beat_region", 1.0) == ["ride_soft", "hihat_pedal"]
    assert module._drum_roles_for_piano_hit("four_beat_region", 1.5) == ["ride_skip_ghost"]
    assert module._drum_roles_for_piano_hit("two_beat_region", 1.5) == ["ride_skip_ghost"]
    assert module._drum_roles_for_piano_hit("two_beat_region", 3.0) == []


def test_v2_6_83_static_audit_and_mock_acceptance_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()

    assert static["checkpoint_version"] == "v2_6_83"
    assert static["drum_piano_interaction_audit_enabled"] is True
    assert static["drum_piano_interaction_audit_version"] == "v2_6_83"
    assert static["previous_bass_piano_interaction_audit_version"] == "v2_6_82"
    assert static["two_beat_density_relief_policy_version"] == "v2_6_80"
    assert static["drum_candidates_are_existing_ride_time_only"] is True
    assert static["drum_candidates_do_not_receive_next_chord_anticipation"] is True
    assert static["existing_voicing_capability_default_enabled"] is False
    assert static["existing_voicing_capability_ordinary_runtime_default"] is False

    outputs = [
        {
            "slug": "all_the_things_you_are",
            "track_presence_ok": True,
            "piano_note_events": 773,
            "bass_note_events": 456,
            "drum_note_events": 864,
            "piano_active_pattern_events": 192,
            "piano_voicing_events": 192,
            "piano_two_beat_active_events": 24,
            "two_beat_start_anchor_events": 21,
            "two_beat_anchor_ratio": 0.875,
            "two_beat_multi_touch_events": 0,
            "active_anticipation_count": 5,
            "two_beat_previous_tail_anticipation_count": 1,
            "five_note_events": 5,
            "six_note_events": 0,
            "ordinary_body_5_6_events": 0,
            "low_register_dense_events": 0,
            "voice_leading_warning_events": 0,
            "max_top_note": 73,
            "bass_span_violations": 0,
            "bass_target_continuity_mismatches": 0,
            "bass_repeated_root_violations": 0,
            "pedal_cc64_event_count": 0,
            "pedal_warning_count": 0,
            "piano_drum_joined_events": 173,
            "piano_on_ride_medium_events": 116,
            "piano_on_hihat_events": 21,
            "piano_on_ride_skip_ghost_events": 36,
            "two_beat_piano_non_anchor_with_drums_events": 3,
            "optional_piano_with_drums_events": 0,
            "accented_piano_on_hihat_events": 0,
            "drum_piano_interaction_risk_events": 3,
        },
        {
            "slug": "autumn_leaves",
            "track_presence_ok": True,
            "piano_note_events": 765,
            "bass_note_events": 398,
            "drum_note_events": 768,
            "piano_active_pattern_events": 190,
            "piano_voicing_events": 190,
            "piano_two_beat_active_events": 134,
            "two_beat_start_anchor_events": 121,
            "two_beat_anchor_ratio": 0.903,
            "two_beat_multi_touch_events": 4,
            "active_anticipation_count": 14,
            "two_beat_previous_tail_anticipation_count": 13,
            "five_note_events": 5,
            "six_note_events": 0,
            "ordinary_body_5_6_events": 0,
            "low_register_dense_events": 0,
            "voice_leading_warning_events": 0,
            "max_top_note": 73,
            "bass_span_violations": 0,
            "bass_target_continuity_mismatches": 0,
            "bass_repeated_root_violations": 0,
            "pedal_cc64_event_count": 0,
            "pedal_warning_count": 0,
            "piano_drum_joined_events": 185,
            "piano_on_ride_medium_events": 141,
            "piano_on_hihat_events": 19,
            "piano_on_ride_skip_ghost_events": 25,
            "two_beat_piano_non_anchor_with_drums_events": 13,
            "optional_piano_with_drums_events": 0,
            "accented_piano_on_hihat_events": 0,
            "drum_piano_interaction_risk_events": 13,
        },
    ]
    aggregate = module._aggregate(outputs)
    acceptance = module._acceptance(static, outputs, aggregate)

    assert aggregate["piano_on_hihat_events"] == 40
    assert aggregate["piano_on_ride_skip_ghost_events"] == 61
    assert aggregate["accented_piano_on_hihat_events"] == 0
    assert aggregate["drum_piano_interaction_risk_events"] == 16
    assert acceptance["passed"] is True
