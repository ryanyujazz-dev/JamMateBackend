from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

from jammate_engine.styles.bossa_nova import arrangement_policy, comping_patterns
from jammate_engine.styles.registry import get_style

MILESTONE_ID = "v2_6_92"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_context_archetype_policy_audit.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_context_archetype_policy_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _region(**overrides):
    data = {
        "chorus_index": 0,
        "total_choruses": 3,
        "performance_bar_index": 4,
        "source_bar_index": 4,
        "duration_beats": 4.0,
        "is_first_bar_of_section": False,
        "is_first_bar_of_chorus": False,
        "is_last_bar_of_section": False,
        "is_last_bar_of_chorus": False,
        "section_role": "normal",
        "phrase": "A",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_v2_6_92_declares_in_place_context_archetype_policy() -> None:
    style = get_style("bossa_nova")
    policy = style.arrangement_policy

    assert policy == arrangement_policy.get_arrangement_policy()
    assert policy["bossa_nova_context_archetype_policy_active"] is True
    assert policy["bossa_nova_context_archetype_policy_version"] == MILESTONE_ID
    assert policy["bossa_nova_context_archetype_policy_behavior_change"] is True
    assert policy["bossa_nova_context_archetype_policy_replaces_simple_v2_6_91_weighting"] is True
    assert policy["bossa_nova_context_archetype_policy_no_parallel_selector"] is True
    assert policy["bossa_nova_context_archetype_policy_no_bar_first_restore"] is True
    assert policy["bossa_nova_context_archetype_policy_no_new_pattern_vocabulary"] is True
    assert policy["bossa_nova_context_archetype_policy_no_core_voicing_change"] is True
    assert policy["bossa_nova_context_archetype_policy_no_expression_numeric_change"] is True
    assert policy["bossa_nova_context_archetype_policy_recommended_next_task"].startswith("v2_6_93")


def test_v2_6_92_keeps_same_pattern_vocabulary_but_updates_policy_metadata() -> None:
    full = comping_patterns.describe_pattern_library({"region_duration_beats": 4.0})
    half = comping_patterns.describe_pattern_library({"region_duration_beats": 2.0})

    assert full["version"] == MILESTONE_ID
    assert full["candidate_count"] == 13
    assert full["class_A_candidate_count"] == 6
    assert full["class_B_candidate_count"] == 6
    assert full["core_candidate_count"] == 1
    assert half["candidate_count"] == 1
    assert "context_archetype_policy_active" in full["boundary_notes"]
    for candidate in full["candidates"]:
        metadata = candidate["metadata"]
        assert metadata["bossa_context_archetype_policy_active"] is True
        assert metadata["bossa_context_archetype_policy_version"] == MILESTONE_ID


def test_v2_6_92_context_archetype_probes_shape_existing_candidates() -> None:
    opening = comping_patterns.get_pattern_candidates(
        {"region": _region(chorus_index=0, performance_bar_index=0, source_bar_index=0, is_first_bar_of_section=True, is_first_bar_of_chorus=True), "region_duration_beats": 4.0}
    )
    steady = comping_patterns.get_pattern_candidates({"region": _region(performance_bar_index=4, source_bar_index=4), "region_duration_beats": 4.0})
    breath = comping_patterns.get_pattern_candidates({"region": _region(performance_bar_index=10, source_bar_index=2, section_role="bridge", phrase="B"), "region_duration_beats": 4.0})
    transition = comping_patterns.get_pattern_candidates({"region": _region(performance_bar_index=7, source_bar_index=7, is_last_bar_of_section=True), "region_duration_beats": 4.0})
    release = comping_patterns.get_pattern_candidates(
        {"region": _region(chorus_index=2, total_choruses=3, performance_bar_index=47, source_bar_index=15, is_last_bar_of_chorus=True, is_last_bar_of_section=True), "region_duration_beats": 4.0}
    )
    short = comping_patterns.get_pattern_candidates({"region": _region(duration_beats=2.0), "region_duration_beats": 2.0})

    assert [candidate.name for candidate in opening] == ["bossa_piano_core_batida_1_2_3and"]
    assert {candidate.metadata["bossa_context_archetype"] for candidate in steady} == {"steady_batida_flow"}
    assert {candidate.metadata["bossa_context_archetype"] for candidate in breath} == {"breath_space"}
    assert {candidate.metadata["bossa_context_archetype"] for candidate in transition} == {"transition_lift"}
    assert {candidate.metadata["bossa_context_archetype"] for candidate in release} == {"release"}
    assert {candidate.metadata["bossa_context_archetype"] for candidate in short} == {"dense_harmonic_marks"}


def test_v2_6_92_history_guard_downweights_recent_class_B_without_parallel_selector() -> None:
    source_key = "bossa_nova:0:jammate_engine.styles.bossa_nova.comping_patterns.get_pattern_candidates"
    history = {
        source_key: "bossa_piano_cell_B_1and_3",
        f"{source_key}:category": "bossa_cell_B",
        f"{source_key}:recent_bossa_comping": [
            {"name": "bossa_piano_cell_B_1and_3", "category": "bossa_cell_B", "rhythm_class": "class_B", "hit_count": 2, "native_4and": False},
            {"name": "bossa_piano_cell_A_1_2_3and", "category": "bossa_cell_A", "rhythm_class": "class_A", "hit_count": 3, "native_4and": False},
            {"name": "bossa_piano_cell_B_1and", "category": "bossa_cell_B", "rhythm_class": "class_B", "hit_count": 1, "native_4and": False},
        ],
    }
    candidates = comping_patterns.get_pattern_candidates({"region": _region(performance_bar_index=6, source_bar_index=6), "region_duration_beats": 4.0, "style_pattern_history": history})
    class_b_multipliers = [candidate.metadata["bossa_context_weighting_multiplier"] for candidate in candidates if candidate.metadata.get("rhythm_class") == "class_B"]

    assert class_b_multipliers
    assert max(class_b_multipliers) < 0.2
    assert all(candidate.metadata["bossa_context_history_recent_class_B_count"] >= 2 for candidate in candidates)


def test_v2_6_92_static_audit_acceptance_passes() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static, [])

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["style_registered"] is True
    assert static["arrangement_policy_version"] == MILESTONE_ID
    assert static["pattern_library_version"] == MILESTONE_ID
    assert static["full_region_candidate_count"] == 13
    assert static["context_probes"]["opening"]["has_only_core"] is True
    assert static["context_probes"]["short_region"]["archetypes"] == ["dense_harmonic_marks"]
    assert acceptance["checks"]["runtime_blue_bossa_full_band_passes"] is False
    assert acceptance["passed"] is False


def test_v2_6_92_blue_bossa_runtime_stamps_archetypes_and_preserves_boundaries() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 22702, "slug": "blue_bossa_3x_pytest_v2_6_92"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert runtime["note_events_by_track"]["piano"] > 0
    assert runtime["note_events_by_track"]["bass"] > 0
    assert runtime["note_events_by_track"]["drums"] > 0
    assert runtime["piano_non_core_pattern_event_count"] > 0
    assert runtime["piano_class_A_event_count"] > runtime["piano_class_B_event_count"]
    assert runtime["piano_class_B_ratio_of_non_core_events"] <= 0.22
    assert runtime["opening_first_two_bars_core_only"] is True
    assert "core_batida_anchor" in runtime["piano_archetype_counts"]
    assert "steady_batida_flow" in runtime["piano_archetype_counts"]
    assert len(runtime["piano_archetype_counts"]) >= 4
    assert runtime["active_anticipation_count"] > 0
    assert runtime["terminal_ending_anticipation_count"] == 0
    assert runtime["anticipation_timing_grids"] == ["straight_upbeat"]
    assert runtime["expression_warning_count"] == 0
    assert runtime["expression_missing_count"] == 0
    assert runtime["expression_cross_region_count"] == 0
    assert runtime["expression_cross_next_event_count"] == 0
    assert runtime["pedal_cc64_event_count"] == 0
    assert acceptance["passed"] is True
