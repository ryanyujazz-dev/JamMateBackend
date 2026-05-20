from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.core.timeline.chord_region_timeline import build_chord_region_timeline
from jammate_engine.core.anticipation import AnticipationPolicy, AnticipationResolver
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.styles.medium_swing import arrangement_policy
from jammate_engine.styles.registry import get_style


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_medium_swing_full_band_ending_realization_checkpoint.py"
    spec = importlib.util.spec_from_file_location("generate_medium_swing_full_band_ending_realization_checkpoint", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tiny_leadsheet() -> dict:
    return {
        "schema_version": "jammate_leadsheet_v2",
        "title": "Tiny Swing Ending Test",
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


def test_v2_6_87_declares_full_band_ending_realization_checkpoint_without_behavior_change() -> None:
    policy = arrangement_policy.get_arrangement_policy()

    assert policy["medium_swing_arrangement_arc_runtime_intent_usage_version"] == "v2_6_85"
    assert policy["medium_swing_arrangement_arc_runtime_listening_refinement_version"] == "v2_6_86"
    assert policy["medium_swing_full_band_ending_realization_checkpoint"] is True
    assert policy["medium_swing_full_band_ending_realization_checkpoint_version"] == "v2_6_87"
    contract = policy["medium_swing_full_band_ending_realization_checkpoint_contract"]
    assert "full-band" in contract
    assert "ending" in contract
    assert "no new ending patterns" in contract
    assert "core voicing" in contract
    assert policy["medium_swing_full_band_ending_realization_checkpoint_milestone"] == "v2_6_87_medium_swing_full_band_ending_realization_checkpoint"


def test_v2_6_87_style_planner_stamps_ending_checkpoint_metadata_on_piano_events() -> None:
    leadsheet = normalize_leadsheet(parse_leadsheet(_tiny_leadsheet()))
    timeline = build_chord_region_timeline(leadsheet, choruses=3)
    style = get_style("medium_swing")
    history: dict[str, object] = {}

    ending_rows = []
    for region in timeline.regions:
        plan = style.plan_region(region, context={"style_pattern_history": history, "tempo": 132, "ensemble": {}})
        for event in plan.events:
            if event.track != "piano":
                continue
            metadata = dict(event.metadata)
            assert metadata["medium_swing_arrangement_arc_runtime_intent_usage_version"] == "v2_6_85"
            assert metadata["medium_swing_arrangement_arc_runtime_listening_refinement_version"] == "v2_6_86"
            assert metadata["medium_swing_full_band_ending_realization_checkpoint_version"] == "v2_6_87"
            assert metadata["medium_swing_full_band_ending_realization_checkpoint_behavior_change"] is False
            assert metadata["medium_swing_full_band_ending_realization_checkpoint_scope"] == "full_band_ending_audit_metadata_only"
            if metadata.get("region_chorus_index") == metadata.get("region_total_choruses", 0) - 1 and metadata.get("region_is_last_bar_of_chorus"):
                ending_rows.append(metadata)

    assert ending_rows
    assert all(row["medium_swing_arrangement_arc_runtime_intent_phase"] == "final_head_out_release" for row in ending_rows)
    assert all(row.get("ending_specific_subset_policy_applied") is True for row in ending_rows)


def test_v2_6_87_generic_anticipation_guard_does_not_move_terminal_ending_downbeat() -> None:
    previous = HarmonicRegion(
        region_id="prev",
        chord_symbol="G7",
        next_chord_symbol="Cmaj7",
        chorus_index=2,
        bar_index=10,
        chord_index=0,
        start_beat=40.0,
        duration_beats=4.0,
        total_choruses=3,
    )
    terminal = HarmonicRegion(
        region_id="terminal",
        chord_symbol="Cmaj7",
        next_chord_symbol=None,
        chorus_index=2,
        bar_index=11,
        chord_index=0,
        start_beat=44.0,
        duration_beats=4.0,
        total_choruses=3,
        is_last_bar_of_chorus=True,
        is_last_bar_of_section=True,
    )
    event = PatternEvent(
        event_id="terminal_piano",
        track="piano",
        region_id="terminal",
        chord_symbol="Cmaj7",
        onset_beat=44.0,
        local_beat=0.0,
        role="harmonic",
        metadata={
            "region_chorus_index": 2,
            "region_total_choruses": 3,
            "region_is_last_bar_of_chorus": True,
            "region_is_last_bar_of_section": True,
        },
    )
    policy = AnticipationPolicy(enabled=True, probability=1.0, debug_name="terminal_guard_test")
    resolved = AnticipationResolver().resolve([event], policy, __import__("random").Random(1), regions=[previous, terminal])

    assert len(resolved) == 1
    assert resolved[0].event_id == "terminal_piano"
    assert resolved[0].status == "active"
    assert "anticipation" not in resolved[0].metadata


def test_v2_6_87_static_audit_contract_and_mock_acceptance() -> None:
    module = _load_script_module()
    static = module.build_static_audit()

    assert static["checkpoint_version"] == "v2_6_87"
    assert static["ending_realization_checkpoint_enabled"] is True
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
    assert aggregate["min_ending_checkpoint_coverage_ratio"] == 1.0
    assert aggregate["total_ending_push_or_active_events"] == 0
    assert acceptance["passed"] is True
