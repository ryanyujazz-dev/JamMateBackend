from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.core.timeline.chord_region_timeline import build_chord_region_timeline
from jammate_engine.styles.medium_swing import arrangement_policy
from jammate_engine.styles.registry import get_style


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_medium_swing_arrangement_arc_runtime_intent_usage.py"
    spec = importlib.util.spec_from_file_location("generate_medium_swing_arrangement_arc_runtime_intent_usage", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tiny_leadsheet() -> dict:
    return {
        "schema_version": "jammate_leadsheet_v2",
        "title": "Tiny Swing Arc Test",
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


def test_v2_6_85_declares_runtime_intent_usage_without_core_boundary_change() -> None:
    policy = arrangement_policy.get_arrangement_policy()

    assert policy["medium_swing_repeat_count_aware_arrangement_arc_checkpoint_version"] == "v2_6_84"
    assert policy["medium_swing_arrangement_arc_runtime_intent_usage"] is True
    assert policy["medium_swing_arrangement_arc_runtime_intent_usage_version"] == "v2_6_85"
    contract = policy["medium_swing_arrangement_arc_runtime_intent_usage_contract"]
    assert "runtime style intent" in contract
    assert "50x" in contract
    assert "no new pattern vocabulary" in contract
    assert "no core voicing changes" in contract
    assert policy["medium_swing_arrangement_arc_runtime_intent_usage_milestone"] == "v2_6_85_medium_swing_arrangement_arc_runtime_intent_usage"


def test_v2_6_85_resolves_runtime_intent_for_arbitrary_repeat_counts() -> None:
    one = arrangement_policy.resolve_runtime_arrangement_arc_intent(0, 1)
    fifty = arrangement_policy.resolve_runtime_arrangement_arc_intent(25, 50)
    final = arrangement_policy.resolve_runtime_arrangement_arc_intent(99, 50)

    assert one["runtime_intent_usage_version"] == "v2_6_85"
    assert one["piano_comping_runtime_intent"] == "single_pass_balanced"
    assert fifty["long_loop_safe"] is True
    assert fifty["not_three_chorus_hardcoded"] is True
    assert fifty["phase"] in {"loop_wave_reset", "loop_wave_develop", "loop_wave_peak", "loop_wave_release"}
    assert final["phase"] == "final_head_out_release"
    assert final["piano_comping_runtime_intent"] == "settled_release"


def test_v2_6_85_style_planner_stamps_runtime_arc_intent_on_piano_events() -> None:
    leadsheet = normalize_leadsheet(parse_leadsheet(_tiny_leadsheet()))
    timeline = build_chord_region_timeline(leadsheet, choruses=5)
    style = get_style("medium_swing")
    history: dict[str, object] = {}

    phases_seen: set[str] = set()
    for region in timeline.regions:
        plan = style.plan_region(region, context={"style_pattern_history": history, "tempo": 132, "ensemble": {}})
        for event in plan.events:
            if event.track != "piano":
                continue
            metadata = dict(event.metadata)
            assert metadata["medium_swing_arrangement_arc_runtime_intent_usage_version"] == "v2_6_85"
            assert metadata["medium_swing_arrangement_arc_runtime_intent_not_three_chorus_hardcoded"] is True
            assert metadata["medium_swing_arrangement_arc_runtime_intent_boundary"] == "style_intent_metadata_and_candidate_weighting_only"
            assert isinstance(metadata["medium_swing_arrangement_arc_runtime_intent_multiplier"], float)
            phases_seen.add(str(metadata["medium_swing_arrangement_arc_runtime_intent_phase"]))

    assert "head_in_clear" in phases_seen
    assert "loop_wave_peak" in phases_seen
    assert "final_head_out_release" in phases_seen


def test_v2_6_85_candidate_multiplier_is_small_and_semantic_only() -> None:
    stable = {
        "weight_calibration_class": "stable",
        "rhythm_family": "stable",
        "requires_region_start_anchor": True,
        "density": "sparse",
    }
    busy = {
        "weight_calibration_class": "busy",
        "rhythm_family": "busy_fill",
        "optional_fill_variation_vocabulary_candidate": True,
        "optional_fill_variation_role": "busy_fill",
        "density": "dense",
    }
    reset_intent = arrangement_policy.resolve_runtime_arrangement_arc_intent(0, 8)
    peak_intent = arrangement_policy.resolve_runtime_arrangement_arc_intent(2, 8)

    stable_multiplier, stable_reasons, stable_status = arrangement_policy.arrangement_arc_runtime_candidate_multiplier(stable, reset_intent)
    busy_multiplier, busy_reasons, busy_status = arrangement_policy.arrangement_arc_runtime_candidate_multiplier(busy, peak_intent)

    assert 1.0 < stable_multiplier < 1.2
    assert "stable" in " ".join(stable_reasons)
    assert stable_status == "arc_prefers_stable_anchor"
    assert 0.0 < busy_multiplier < 0.6
    assert "busy" in " ".join(busy_reasons)
    assert busy_status == "arc_busy_guard"


def test_v2_6_85_static_audit_and_mock_acceptance_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()

    assert static["checkpoint_version"] == "v2_6_85"
    assert static["repeat_count_aware_arrangement_arc_version"] == "v2_6_84"
    assert static["arrangement_arc_runtime_intent_usage_enabled"] is True
    assert static["arrangement_arc_runtime_intent_usage_version"] == "v2_6_85"
    assert static["long_loop_50x_has_wave_reset"] is True
    assert static["three_chorus_not_hardcoded"] is True

    outputs = [
        {
            "requested_choruses": 3,
            "track_presence_ok": True,
            "piano_active_pattern_events": 192,
            "active_anticipation_count": 8,
            "arrangement_arc_runtime_intent_event_count": 192,
            "arrangement_arc_runtime_intent_coverage_ratio": 1.0,
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
            "piano_active_pattern_events": 320,
            "active_anticipation_count": 20,
            "arrangement_arc_runtime_intent_event_count": 320,
            "arrangement_arc_runtime_intent_coverage_ratio": 1.0,
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
    assert aggregate["min_arrangement_arc_runtime_intent_coverage_ratio"] == 1.0
    assert acceptance["passed"] is True
