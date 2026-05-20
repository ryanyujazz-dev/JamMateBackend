from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.core.timeline.chord_region_timeline import build_chord_region_timeline
from jammate_engine.styles.medium_swing import arrangement_policy
from jammate_engine.styles.registry import get_style


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_medium_swing_style_baseline_phase_completion_checkpoint.py"
    spec = importlib.util.spec_from_file_location("generate_medium_swing_style_baseline_phase_completion_checkpoint", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tiny_leadsheet() -> dict:
    return {
        "schema_version": "jammate_leadsheet_v2",
        "title": "Tiny Swing Baseline Phase Completion Test",
        "tempo": 132,
        "sections": [
            {
                "id": "A",
                "label": "A",
                "bars": [
                    {"chords": [{"symbol": "Cmaj7", "beat": 1}, {"symbol": "F7", "beat": 3}]},
                    {"chords": [{"symbol": "Bbmaj7", "beat": 1}, {"symbol": "E7", "beat": 3}]},
                    {"chords": [{"symbol": "Am7", "beat": 1}, {"symbol": "D7", "beat": 3}]},
                    {"chords": [{"symbol": "G7", "beat": 1}, {"symbol": "Cmaj7", "beat": 3}]},
                ],
            }
        ],
        "written_form": [{"section": "A"}],
    }


def test_v2_6_88_declares_medium_swing_style_baseline_phase_completion_checkpoint() -> None:
    policy = arrangement_policy.get_arrangement_policy()

    assert policy["medium_swing_full_band_ending_realization_checkpoint_version"] == "v2_6_87"
    assert policy["medium_swing_style_baseline_phase_completion_checkpoint"] is True
    assert policy["medium_swing_style_baseline_phase_completion_checkpoint_version"] == "v2_6_88"
    contract = policy["medium_swing_style_baseline_phase_completion_checkpoint_contract"]
    assert "v2_6_56-v2_6_87" in contract
    assert "full-band baseline" in contract
    assert "does not add vocabulary" in contract
    assert "core voicing" in contract
    assert policy["medium_swing_style_baseline_phase_completion_checkpoint_milestone"] == "v2_6_88_medium_swing_style_baseline_phase_completion_checkpoint"


def test_v2_6_88_style_planner_stamps_baseline_phase_completion_metadata_on_piano_events() -> None:
    leadsheet = normalize_leadsheet(parse_leadsheet(_tiny_leadsheet()))
    timeline = build_chord_region_timeline(leadsheet, choruses=5)
    style = get_style("medium_swing")
    history: dict[str, object] = {}

    rows = []
    for region in timeline.regions:
        plan = style.plan_region(region, context={"style_pattern_history": history, "tempo": 132, "ensemble": {}})
        for event in plan.events:
            if event.track != "piano":
                continue
            metadata = dict(event.metadata)
            assert metadata["medium_swing_arrangement_arc_runtime_intent_usage_version"] == "v2_6_85"
            assert metadata["medium_swing_arrangement_arc_runtime_listening_refinement_version"] == "v2_6_86"
            assert metadata["medium_swing_full_band_ending_realization_checkpoint_version"] == "v2_6_87"
            assert metadata["medium_swing_style_baseline_phase_completion_checkpoint_version"] == "v2_6_88"
            assert metadata["medium_swing_style_baseline_phase_completion_checkpoint_behavior_change"] is False
            assert metadata["medium_swing_style_baseline_phase_completion_checkpoint_scope"] == "full_band_baseline_summary_metadata_only"
            rows.append(metadata)

    assert rows
    assert {row["medium_swing_arrangement_arc_runtime_intent_total_choruses"] for row in rows} == {5}
    assert any(row["medium_swing_arrangement_arc_runtime_intent_phase"] == "loop_wave_peak" for row in rows)
    assert any(row["medium_swing_arrangement_arc_runtime_intent_phase"] == "final_head_out_release" for row in rows)


def test_v2_6_88_static_audit_and_mock_acceptance() -> None:
    module = _load_script_module()
    static = module.build_static_audit()

    assert static["checkpoint_version"] == "v2_6_88"
    assert static["style_baseline_phase_completion_checkpoint_enabled"] is True
    assert static["style_baseline_phase_completion_checkpoint_version"] == "v2_6_88"
    assert static["ending_realization_checkpoint_version"] == "v2_6_87"
    assert static["arrangement_arc_runtime_listening_refinement_version"] == "v2_6_86"
    assert static["long_loop_50x_has_wave_reset"] is True
    assert static["long_loop_50x_final_phase"] == "final_head_out_release"

    outputs = [
        {
            "requested_choruses": 3,
            "track_presence_ok": True,
            "piano_active_pattern_events": 190,
            "active_anticipation_count": 12,
            "ending_anticipation_count": 0,
            "arrangement_arc_runtime_intent_coverage_ratio": 1.0,
            "arrangement_arc_runtime_listening_refinement_coverage_ratio": 1.0,
            "ending_checkpoint_coverage_ratio": 1.0,
            "ending_checkpoint_behavior_change_events": 0,
            "style_baseline_phase_completion_coverage_ratio": 1.0,
            "style_baseline_phase_completion_behavior_change_events": 0,
            "ending_pattern_events": 1,
            "ending_stable_settle_events": 1,
            "ending_stable_settle_ratio": 1.0,
            "ending_push_or_active_events": 0,
            "ending_arc_final_release_ratio": 1.0,
            "piano_voicing_events": 190,
            "five_note_events": 4,
            "six_note_events": 0,
            "ordinary_body_5_6_events": 0,
            "ending_five_six_events": 1,
            "low_register_dense_events": 0,
            "ending_low_register_dense_events": 0,
            "voice_leading_warning_events": 0,
            "ending_voice_leading_warning_events": 0,
            "bass_span_violations": 0,
            "bass_target_continuity_mismatches": 0,
            "bass_repeated_root_violations": 0,
            "pedal_cc64_event_count": 0,
            "piano_note_events": 780,
            "bass_note_events": 460,
            "drum_note_events": 864,
        },
        {
            "requested_choruses": 5,
            "track_presence_ok": True,
            "piano_active_pattern_events": 320,
            "active_anticipation_count": 18,
            "ending_anticipation_count": 0,
            "arrangement_arc_runtime_intent_coverage_ratio": 1.0,
            "arrangement_arc_runtime_listening_refinement_coverage_ratio": 1.0,
            "ending_checkpoint_coverage_ratio": 1.0,
            "ending_checkpoint_behavior_change_events": 0,
            "style_baseline_phase_completion_coverage_ratio": 1.0,
            "style_baseline_phase_completion_behavior_change_events": 0,
            "ending_pattern_events": 1,
            "ending_stable_settle_events": 1,
            "ending_stable_settle_ratio": 1.0,
            "ending_push_or_active_events": 0,
            "ending_arc_final_release_ratio": 1.0,
            "piano_voicing_events": 320,
            "five_note_events": 4,
            "six_note_events": 0,
            "ordinary_body_5_6_events": 0,
            "ending_five_six_events": 1,
            "low_register_dense_events": 0,
            "ending_low_register_dense_events": 0,
            "voice_leading_warning_events": 0,
            "ending_voice_leading_warning_events": 0,
            "bass_span_violations": 0,
            "bass_target_continuity_mismatches": 0,
            "bass_repeated_root_violations": 0,
            "pedal_cc64_event_count": 0,
            "piano_note_events": 1300,
            "bass_note_events": 768,
            "drum_note_events": 1440,
        },
    ]
    aggregate = module._aggregate(outputs)
    acceptance = module._acceptance(static, outputs, aggregate)

    assert aggregate["runtime_chorus_counts"] == [3, 5]
    assert aggregate["min_style_baseline_phase_completion_coverage_ratio"] == 1.0
    assert aggregate["style_baseline_phase_completion_behavior_change_events"] == 0
    assert acceptance["passed"] is True
