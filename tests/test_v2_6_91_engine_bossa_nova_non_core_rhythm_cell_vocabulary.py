from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.styles.bossa_nova import arrangement_policy, comping_patterns, expression_policy
from jammate_engine.styles.registry import get_style


MILESTONE_ID = "v2_6_91"
CURRENT_BOSSA_PATTERN_VERSION = "v2_6_92"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_non_core_rhythm_cell_vocabulary_audit.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_non_core_rhythm_cell_vocabulary_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_6_91_declares_direct_bossa_non_core_vocabulary_activation() -> None:
    style = get_style("bossa_nova")
    policy = style.arrangement_policy

    assert policy == arrangement_policy.get_arrangement_policy()
    assert policy["bossa_nova_non_core_rhythm_cell_vocabulary_active"] is True
    assert policy["bossa_nova_non_core_rhythm_cell_vocabulary_version"] == MILESTONE_ID
    assert policy["bossa_nova_non_core_rhythm_cell_vocabulary_behavior_change"] is True
    assert policy["bossa_nova_non_core_rhythm_cell_vocabulary_replaces_core_only_runtime"] is True
    assert policy["bossa_nova_non_core_rhythm_cell_vocabulary_no_parallel_selector"] is True
    assert policy["bossa_nova_non_core_rhythm_cell_vocabulary_no_bar_first_restore"] is True
    assert policy["bossa_nova_non_core_rhythm_cell_vocabulary_no_core_voicing_change"] is True
    assert policy["bossa_nova_non_core_rhythm_cell_vocabulary_no_api_agent_harmonyos_change"] is True
    assert policy["bossa_nova_non_core_rhythm_cell_vocabulary_expression_numeric_calibration_change"] is False
    assert policy["opening_core_batida_bars"] == 2


def test_v2_6_91_bossa_pattern_library_has_one_core_and_class_A_B_cells() -> None:
    full = comping_patterns.describe_pattern_library({"region_duration_beats": 4.0})
    half = comping_patterns.describe_pattern_library({"region_duration_beats": 2.0})
    full_candidates = list(full["candidates"])
    half_candidates = list(half["candidates"])
    core = [candidate for candidate in full_candidates if candidate["name"] == "bossa_piano_core_batida_1_2_3and"]
    class_a = [candidate for candidate in full_candidates if candidate["metadata"].get("rhythm_class") == "class_A"]
    class_b = [candidate for candidate in full_candidates if candidate["metadata"].get("rhythm_class") == "class_B"]
    all_tags = {tag for candidate in [*full_candidates, *half_candidates] for tag in candidate["tags"]}

    assert full["version"] == CURRENT_BOSSA_PATTERN_VERSION
    assert full["candidate_count"] == 13
    assert len(core) == 1
    assert len(class_a) == 6
    assert len(class_b) == 6
    assert core[0]["rhythm_beats"] == [0.0, 1.0, 2.5]
    assert [event["expression_hint"] for event in core[0]["events"]] == ["core_short", "core_short", "core_sustain"]
    assert half["candidate_count"] >= 1
    assert any(candidate["name"] == "bossa_piano_half_region_1_2" and candidate["rhythm_beats"] == [0.0, 1.0] for candidate in half_candidates)
    assert "chord_region_first" in all_tags
    assert "two_chord_bar" not in all_tags
    assert "bar_first" not in all_tags
    assert "split_bar" not in all_tags


def test_v2_6_91_non_core_cells_use_expression_aliases_not_concrete_values() -> None:
    full = comping_patterns.describe_pattern_library({"region_duration_beats": 4.0})
    non_core_events = [
        event
        for candidate in full["candidates"]
        if candidate["name"] != "bossa_piano_core_batida_1_2_3and"
        for event in candidate["events"]
    ]
    hints = {event["expression_hint"] for event in non_core_events}
    profiles = expression_policy.get_expression_policy().profiles

    assert hints == {"cell_close_gap_short", "cell_soft_hold"}
    assert profiles["cell_close_gap_short"].metadata["numeric_source_profile"] == "core_short"
    assert profiles["cell_soft_hold"].metadata["numeric_source_profile"] == "core_sustain"
    for event in non_core_events:
        metadata = event["metadata"]
        assert metadata["expression_boundary"] == "semantic_hint_only"
        assert metadata["voicing_boundary"] == "pitchless_event_only"
        assert "velocity" not in metadata
        assert "duration_beats" not in metadata
        assert "pedal" not in metadata
        assert "midi_note" not in metadata


def test_v2_6_91_static_audit_acceptance_passes() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static, [])

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["style_registered"] is True
    assert static["arrangement_policy_version"] == MILESTONE_ID
    assert static["full_region_candidate_count"] == 13
    assert static["class_A_candidate_count"] == 6
    assert static["class_B_candidate_count"] == 6
    assert static["core_candidate_count"] == 1
    assert static["legacy_bar_first_tags"] == []
    assert static["core_batida_beats"] == [0.0, 1.0, 2.5]
    assert static["non_core_expression_hints"] == ["cell_close_gap_short", "cell_soft_hold"]
    assert acceptance["checks"]["runtime_blue_bossa_full_band_passes"] is False
    assert acceptance["passed"] is False


def test_v2_6_91_blue_bossa_runtime_uses_non_core_cells_and_preserves_opening_core() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 22702, "slug": "blue_bossa_3x_pytest_v2_6_91"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert runtime["note_events_by_track"]["piano"] > 0
    assert runtime["note_events_by_track"]["bass"] > 0
    assert runtime["note_events_by_track"]["drums"] > 0
    assert runtime["piano_non_core_pattern_event_count"] > 0
    assert runtime["piano_class_A_event_count"] > runtime["piano_class_B_event_count"]
    assert runtime["piano_class_B_ratio_of_non_core_events"] <= 0.22
    assert runtime["opening_first_two_bars_core_only"] is True
    assert runtime["opening_first_two_bars_patterns"] == ["bossa_piano_core_batida_1_2_3and"]
    assert runtime["active_anticipation_count"] > 0
    assert runtime["terminal_ending_anticipation_count"] == 0
    assert runtime["anticipation_timing_grids"] == ["straight_upbeat"]
    assert runtime["expression_warning_count"] == 0
    assert runtime["expression_missing_count"] == 0
    assert runtime["expression_cross_region_count"] == 0
    assert runtime["expression_cross_next_event_count"] == 0
    assert runtime["pedal_cc64_event_count"] == 0
    assert acceptance["passed"] is False
