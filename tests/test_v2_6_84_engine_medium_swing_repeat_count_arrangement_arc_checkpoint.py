from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.styles.medium_swing import arrangement_policy, voicing_policy
from jammate_engine.styles.medium_swing.arrangement_policy import resolve_repeat_count_arrangement_arc, simulate_repeat_count_arrangement_arc


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_medium_swing_repeat_count_arrangement_arc_checkpoint.py"
    spec = importlib.util.spec_from_file_location("generate_medium_swing_repeat_count_arrangement_arc_checkpoint", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_6_84_declares_repeat_count_aware_arrangement_arc_without_behavior_change() -> None:
    arrangement = arrangement_policy.get_arrangement_policy()
    policy = voicing_policy.get_voicing_policy()

    assert arrangement["medium_swing_drum_piano_interaction_audit_version"] == "v2_6_83"
    assert arrangement["medium_swing_repeat_count_aware_arrangement_arc_checkpoint"] is True
    assert arrangement["medium_swing_repeat_count_aware_arrangement_arc_checkpoint_version"] == "v2_6_84"
    assert "1x, 2x, 3x, 5x, 6x, 8x, 9x, 10x" in arrangement["medium_swing_repeat_count_aware_arrangement_arc_checkpoint_contract"]
    assert "50x" in arrangement["medium_swing_repeat_count_aware_arrangement_arc_checkpoint_contract"]
    assert "does not add new patterns" in arrangement["medium_swing_repeat_count_aware_arrangement_arc_checkpoint_contract"]
    assert arrangement["medium_swing_repeat_count_aware_arrangement_arc_checkpoint_milestone"] == "v2_6_84_medium_swing_repeat_count_aware_arrangement_arc_checkpoint"

    nested = policy.metadata["medium_swing_existing_voicing_capability_usage_policy"]
    assert nested["enabled"] is False
    assert nested["ordinary_runtime_default"] is False
    assert nested["no_core_voicing_change"] is True
    assert policy.preferred_density == 4
    assert policy.preferred_disposition.value == "open"


def test_v2_6_84_repeat_arc_handles_short_medium_and_long_repeat_counts() -> None:
    assert [item["phase"] for item in simulate_repeat_count_arrangement_arc(1)] == ["single_pass_balanced"]
    assert [item["phase"] for item in simulate_repeat_count_arrangement_arc(2)] == ["head_in_clear", "final_head_out_release"]
    assert [item["phase"] for item in simulate_repeat_count_arrangement_arc(3)] == ["head_in_clear", "late_build", "final_head_out_release"]

    five = [item["phase"] for item in simulate_repeat_count_arrangement_arc(5)]
    assert five == ["head_in_clear", "loop_wave_develop", "loop_wave_peak", "loop_wave_release", "final_head_out_release"]

    ten = [item["phase"] for item in simulate_repeat_count_arrangement_arc(10)]
    assert ten[0] == "head_in_clear"
    assert ten[-1] == "final_head_out_release"
    assert "loop_wave_reset" in ten
    assert "loop_wave_peak" in ten
    assert ten.count("loop_wave_peak") == 2

    fifty = simulate_repeat_count_arrangement_arc(50)
    phases = [item["phase"] for item in fifty]
    assert phases[0] == "head_in_clear"
    assert phases[-1] == "final_head_out_release"
    assert phases.count("loop_wave_peak") >= 10
    assert phases.count("loop_wave_reset") >= 10
    assert all(item["monotonic_ramp_allowed"] is False for item in fifty)
    assert all(item["long_loop_safe"] is True for item in fifty)


def test_v2_6_84_repeat_arc_clamps_out_of_range_chorus_indices() -> None:
    assert resolve_repeat_count_arrangement_arc(-3, 5)["chorus_index"] == 0
    assert resolve_repeat_count_arrangement_arc(99, 5)["chorus_index"] == 4
    assert resolve_repeat_count_arrangement_arc(99, 5)["phase"] == "final_head_out_release"


def test_v2_6_84_static_audit_and_mock_acceptance_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()

    assert static["checkpoint_version"] == "v2_6_84"
    assert static["repeat_count_aware_arrangement_arc_enabled"] is True
    assert static["repeat_count_aware_arrangement_arc_version"] == "v2_6_84"
    assert static["previous_drum_piano_interaction_audit_version"] == "v2_6_83"
    assert static["long_loop_50x_has_wave_reset"] is True
    assert static["long_loop_50x_has_wave_peak"] is True
    assert static["long_loop_50x_final_phase"] == "final_head_out_release"
    assert static["long_loop_50x_monotonic_ramp_allowed"] is False
    assert static["long_loop_50x_all_long_loop_safe"] is True
    assert static["three_chorus_not_hardcoded"] is True

    outputs = [
        {
            "requested_choruses": 3,
            "track_presence_ok": True,
            "piano_note_events": 773,
            "bass_note_events": 456,
            "drum_note_events": 864,
            "piano_active_pattern_events": 192,
            "active_anticipation_count": 5,
            "piano_voicing_events": 192,
            "five_note_events": 5,
            "six_note_events": 0,
            "ordinary_body_5_6_events": 0,
            "low_register_dense_events": 0,
            "voice_leading_warning_events": 0,
            "pedal_cc64_event_count": 0,
        },
        {
            "requested_choruses": 5,
            "track_presence_ok": True,
            "piano_note_events": 1288,
            "bass_note_events": 760,
            "drum_note_events": 1440,
            "piano_active_pattern_events": 320,
            "active_anticipation_count": 24,
            "piano_voicing_events": 320,
            "five_note_events": 5,
            "six_note_events": 0,
            "ordinary_body_5_6_events": 0,
            "low_register_dense_events": 0,
            "voice_leading_warning_events": 0,
            "pedal_cc64_event_count": 0,
        },
    ]
    aggregate = module._aggregate(outputs)
    acceptance = module._acceptance(static, outputs, aggregate)

    assert aggregate["runtime_chorus_counts"] == [3, 5]
    assert aggregate["total_active_anticipation_count"] == 29
    assert acceptance["passed"] is True
