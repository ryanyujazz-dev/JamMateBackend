from __future__ import annotations

import importlib.util
import random
from pathlib import Path

from jammate_engine.core.form.form_expander import expand_form_to_regions
from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.styles.bossa_nova import arrangement_policy, comping_patterns
from jammate_engine.styles.registry import get_style

MILESTONE_ID = "v2_6_99"
COMPLETED_VERSIONS = (
    "v2_6_90",
    "v2_6_91",
    "v2_6_92",
    "v2_6_93",
    "v2_6_94",
    "v2_6_103",
    "v2_6_96",
    "v2_6_97",
    "v2_6_98",
)


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_style_baseline_phase_completion_checkpoint.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_style_baseline_phase_completion_checkpoint", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tiny_bossa_leadsheet() -> dict:
    return {
        "schema_version": "jammate_leadsheet_v2",
        "title": "Tiny Bossa Phase Completion Test",
        "tempo": 140,
        "sections": [
            {
                "id": "A",
                "label": "A",
                "bars": [
                    {"chords": [{"symbol": "Cm7", "beat": 1}]},
                    {"chords": [{"symbol": "Fm7", "beat": 1}, {"symbol": "Bb7", "beat": 3}]},
                    {"chords": [{"symbol": "Ebmaj7", "beat": 1}]},
                    {"chords": [{"symbol": "Dø7", "beat": 1}, {"symbol": "G7", "beat": 3}]},
                ],
            }
        ],
        "written_form": [{"section": "A"}],
    }


def test_v2_6_99_declares_bossa_style_baseline_phase_completion_checkpoint() -> None:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()

    assert style.arrangement_policy == policy
    assert policy["bossa_nova_full_band_arrangement_arc_listening_refinement_version"] == "v2_6_98"
    assert policy["bossa_nova_style_baseline_phase_completion_checkpoint"] is True
    assert policy["bossa_nova_style_baseline_phase_completion_checkpoint_version"] == MILESTONE_ID
    assert policy["bossa_nova_style_baseline_phase_completion_checkpoint_behavior_change"] is False
    assert policy["bossa_nova_style_baseline_phase_completion_checkpoint_no_parallel_selector"] is True
    assert policy["bossa_nova_style_baseline_phase_completion_checkpoint_no_bar_first_restore"] is True
    assert policy["bossa_nova_style_baseline_phase_completion_checkpoint_no_new_pattern_vocabulary"] is True
    assert policy["bossa_nova_style_baseline_phase_completion_checkpoint_no_expression_numeric_change"] is True
    assert policy["bossa_nova_style_baseline_phase_completion_checkpoint_no_core_voicing_change"] is True
    assert policy["bossa_nova_style_baseline_phase_completion_checkpoint_no_api_agent_harmonyos_change"] is True
    assert policy["bossa_nova_style_baseline_phase_completion_checkpoint_tracks"] == ("piano", "bass", "drums")
    assert policy["bossa_nova_style_baseline_phase_completion_checkpoint_completed_versions"] == COMPLETED_VERSIONS
    contract = policy["bossa_nova_style_baseline_phase_completion_checkpoint_contract"]
    assert "metadata/audit/demo checkpoint only" in contract
    assert "does not add pattern vocabulary" in contract


def test_v2_6_99_keeps_expected_bossa_piano_vocabulary_shape() -> None:
    library = comping_patterns.describe_pattern_library({"region_duration_beats": 4.0})

    assert library["version"] == "v2_6_92"
    assert library["core_candidate_count"] == 1
    assert library["class_A_candidate_count"] == 6
    assert library["class_B_candidate_count"] == 6
    assert library["candidate_count"] == 13

    candidate_names = {candidate["name"] for candidate in library["candidates"]}
    assert "bossa_piano_core_batida_1_2_3and" in candidate_names
    assert "bossa_piano_cell_A_1_3and" in candidate_names
    assert "bossa_piano_cell_B_1and_3" in candidate_names


def test_v2_6_99_runtime_stamps_phase_completion_metadata_on_full_band_events() -> None:
    leadsheet = normalize_leadsheet(parse_leadsheet(_tiny_bossa_leadsheet()))
    timeline = expand_form_to_regions(leadsheet, choruses=5)
    style = get_style("bossa_nova")
    history: dict[str, object] = {}
    rng = random.Random(2299)

    track_events: dict[str, list] = {"piano": [], "bass": [], "drums": []}
    for region in timeline.regions:
        plan = style.plan_region(
            region,
            context={"style_pattern_history": history, "tempo": 140, "rng": rng, "ensemble": {"bass_present": True}},
        )
        for event in plan.events:
            if event.track in track_events:
                track_events[event.track].append(event)

    for track, events in track_events.items():
        assert events, track
        assert all(event.metadata.get("bossa_style_baseline_phase_completion_checkpoint_version") == MILESTONE_ID for event in events), track
        assert all(event.metadata.get("bossa_style_baseline_phase_completion_checkpoint_behavior_change") is False for event in events), track

    assert all(event.metadata.get("walking_bass") is False for event in track_events["bass"])
    assert all(event.metadata.get("drum_identity") == "shaker_cross_stick_light_kick" for event in track_events["drums"])
    assert all(event.metadata.get("swing_ride_pattern") is False for event in track_events["drums"])
    assert all(event.metadata.get("rock_backbeat_pattern") is False for event in track_events["drums"])


def test_v2_6_99_repeat_arc_simulation_remains_repeat_count_aware() -> None:
    simulated = [
        {"total_choruses": count, "phases": arrangement_policy.simulate_repeat_count_arrangement_arc(count)}
        for count in (1, 2, 3, 5, 10, 50)
    ]
    phases_by_count = {item["total_choruses"]: [phase["phase"] for phase in item["phases"]] for item in simulated}

    assert phases_by_count[1] == ["single_pass_clear_light"]
    assert phases_by_count[2] == ["head_in_core_identity", "final_soft_release"]
    assert "gentle_lift" in phases_by_count[3]
    assert "loop_wave_breath_space" in phases_by_count[5]
    assert "loop_wave_reset" in phases_by_count[10]
    assert "loop_wave_reset" in phases_by_count[50]


def test_v2_6_99_static_audit_and_mock_acceptance_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static, [])

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["phase_completion_version"] == MILESTONE_ID
    assert static["completed_versions"] == list(COMPLETED_VERSIONS)
    assert static["piano_core_candidate_count"] == 1
    assert static["piano_class_A_candidate_count"] == 6
    assert static["piano_class_B_candidate_count"] == 6
    assert acceptance["checks"]["runtime_blue_bossa_phase_completion_passes"] is False
    assert acceptance["passed"] is False


def test_v2_6_99_blue_bossa_runtime_acceptance_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 5, "seed": 22995, "slug": "blue_bossa_5x_pytest_v2_6_99"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert runtime["piano_phase_completion_coverage_ratio"] == 1.0
    assert runtime["bass_phase_completion_coverage_ratio"] == 1.0
    assert runtime["drums_phase_completion_coverage_ratio"] == 1.0
    assert runtime["phase_completion_behavior_change_events"] == 0
    assert runtime["piano_rhythm_class_counts"].get("class_A", 0) > 0
    assert runtime["piano_rhythm_class_counts"].get("class_B", 0) > 0
    assert runtime["native_4and_anticipated_event_count"] == 0
    assert runtime["bass_walking_like_events"] == 0
    assert runtime["drum_swing_or_rock_events"] == 0
    assert runtime["bass_full_band_arc_band_counts"].get("breath_space", 0) > 0
    assert runtime["drum_full_band_arc_band_counts"].get("breath_space", 0) > 0
    assert acceptance["passed"] is True
