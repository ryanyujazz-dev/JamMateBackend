from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.voicing import ContentFamily, RootSupportPolicy
from jammate_engine.realization.voicing_policy_context_adapter import policy_with_event_voicing_context
from jammate_engine.styles.bossa_nova import arrangement_policy, comping_patterns, voicing_policy
from jammate_engine.styles.registry import get_style

MILESTONE_ID = "v2_6_103"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_no_forced_low_density_voicing_audit.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _region(region_id: str, chord: str, start: float, duration: float) -> HarmonicRegion:
    return HarmonicRegion(
        region_id=region_id,
        chord_symbol=chord,
        next_chord_symbol=None,
        chorus_index=0,
        total_choruses=3,
        bar_index=int(start // 4),
        chord_index=0,
        start_beat=start,
        duration_beats=duration,
        source_bar_index=int(start // 4),
        performance_bar_index=int(start // 4),
    )


def _candidate(name: str, *, duration: float):
    for candidate in comping_patterns.get_pattern_candidates({"region_duration_beats": duration}, apply_context_policy=False):
        if candidate.name == name:
            return candidate
    raise AssertionError(f"candidate not found: {name}")


def test_v2_6_102_bossa_harmonic_rhythm_clarity_policy_metadata_registered() -> None:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()
    voicing = voicing_policy.get_voicing_policy()

    assert style.arrangement_policy == policy
    assert policy["bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_active"] is True
    assert policy["bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_version"] == MILESTONE_ID
    assert policy["bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_parallel_selector"] is True
    assert policy["bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_bar_first_restore"] is True
    assert policy["bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_new_pattern_vocabulary"] is True
    assert policy["bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_expression_numeric_change"] is True
    assert policy["bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_core_voicing_change"] is True
    assert voicing.metadata["bossa_harmonic_rhythm_region_clarity_and_voicing_intent_active"] is True
    assert voicing.metadata["bossa_harmonic_rhythm_region_clarity_and_voicing_intent_version"] == MILESTONE_ID
    assert voicing.metadata["bossa_harmonic_rhythm_region_clarity_and_voicing_intent_no_core_voicing_change"] is True


def test_v2_6_102_short_region_candidate_stays_chord_region_first_and_marks_light_clarity_intent() -> None:
    library = comping_patterns.describe_pattern_library({"region_duration_beats": 2.0})
    candidate = library["candidates"][0]
    metadata = candidate["metadata"]
    tags = set(candidate["tags"])

    assert library["candidate_count"] == 1
    assert candidate["name"] == "bossa_piano_half_region_1_2"
    assert candidate["rhythm_beats"] == [0.0, 1.0]
    assert metadata["region_shape"] == "two_beat_region"
    assert metadata["pattern_function"] == "dense_harmonic_rhythm_normal_voicing_adaptation"
    assert metadata["bossa_harmonic_rhythm_region_clarity_and_voicing_intent_version"] == MILESTONE_ID
    assert "two_beat_region" in tags
    assert "dense_harmonic_region" in tags
    assert "light_clarity_voicing_intent" not in tags
    assert "chord_region_first" in tags
    assert "two_chord_bar" not in tags
    assert "bar_first" not in tags
    assert "split_bar" not in tags


def test_v2_6_102_event_scoped_adapter_keeps_normal_bossa_voicing_for_short_regions() -> None:
    base_policy = voicing_policy.get_voicing_policy()
    short_region = _region("r_short", "Dm7b5", 0.0, 2.0)
    ordinary_region = _region("r_full", "Cm7", 0.0, 4.0)
    short_plan = _candidate("bossa_piano_half_region_1_2", duration=2.0).instantiate(short_region)
    ordinary_plan = _candidate("bossa_piano_cell_A_1_3and", duration=4.0).instantiate(ordinary_region)

    short_policy = policy_with_event_voicing_context(base_policy, short_plan.events[0])
    ordinary_policy = policy_with_event_voicing_context(base_policy, ordinary_plan.events[0])

    assert short_policy.metadata["bossa_harmonic_rhythm_region_clarity_and_voicing_intent_version"] == MILESTONE_ID
    assert short_policy.metadata["bossa_harmonic_rhythm_region_clarity_and_voicing_intent_applied"] is False
    assert short_policy.metadata["bossa_harmonic_rhythm_region_clarity_and_voicing_intent_reason"] == "dense_short_region_keeps_normal_bossa_open_4_to_5_note_drop_family_policy_v2_6_104"
    assert short_policy.preferred_content == base_policy.preferred_content
    assert short_policy.root_support == base_policy.root_support
    assert short_policy.preferred_density == 4
    assert short_policy.min_density == 4
    assert short_policy.max_density == 5
    assert short_policy.max_voicing_span == base_policy.max_voicing_span
    assert ordinary_policy.metadata["bossa_harmonic_rhythm_region_clarity_and_voicing_intent_applied"] is False
    assert ordinary_policy.metadata["bossa_harmonic_rhythm_region_clarity_and_voicing_intent_reason"] == "ordinary_full_region_keeps_base_bossa_voicing_policy"
    assert ordinary_policy.preferred_density == base_policy.preferred_density
    assert ordinary_policy.max_density == base_policy.max_density


def test_v2_6_102_static_audit_acceptance_requires_runtime_for_full_pass() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static, [])

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["arrangement_policy_version"] == MILESTONE_ID
    assert static["voicing_policy_metadata_version"] == MILESTONE_ID
    assert static["dense_config_enabled"] is False
    assert static["dense_config_preferred_density"] == 4
    assert static["dense_config_min_density"] == 4
    assert static["dense_config_max_density"] == 5
    assert static["dense_config_avoid_forced_2_note"] is True
    assert static["dense_config_avoid_forced_3_note"] is True
    assert static["half_region_pattern_function"] == "dense_harmonic_rhythm_normal_voicing_adaptation"
    assert acceptance["checks"]["runtime_blue_bossa_full_band_passes"] is False
    assert acceptance["passed"] is False


def test_v2_6_102_blue_bossa_runtime_keeps_short_regions_light_and_clear() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 22705, "slug": "blue_bossa_3x_pytest_v2_6_102"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert runtime["note_events_by_track"]["piano"] > 0
    assert runtime["note_events_by_track"]["bass"] > 0
    assert runtime["note_events_by_track"]["drums"] > 0
    assert runtime["short_region_piano_event_count"] > 0
    assert "guide_tone" not in set(runtime["short_region_content_family_counts"])
    assert all(int(value) >= 4 for value in runtime["short_region_density_counts"])
    assert all(int(value) not in {2, 3} for value in runtime["short_region_density_counts"])
    assert runtime["short_region_span_violation_count"] >= 0
    assert runtime["expression_warning_count"] == 0
    assert runtime["expression_missing_count"] == 0
    assert runtime["expression_cross_region_count"] == 0
    assert runtime["expression_cross_next_event_count"] == 0
    assert runtime["pedal_cc64_event_count"] == 0
    assert acceptance["passed"] is True
