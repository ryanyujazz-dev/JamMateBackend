from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.core.expression.expression_resolver import ExpressionResolver
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles.bossa_nova import arrangement_policy, comping_patterns, expression_policy
from jammate_engine.styles.registry import get_style

MILESTONE_ID = "v2_6_94"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_distance_aware_expression_calibration_audit.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_distance_aware_expression_calibration_audit", script_path)
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


def _candidate(name: str):
    for candidate in comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0}, apply_context_policy=False):
        if candidate.name == name:
            return candidate
    raise AssertionError(f"candidate not found: {name}")


def test_v2_6_94_bossa_distance_expression_policy_metadata_registered() -> None:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()
    expression = expression_policy.get_expression_policy()

    assert style.arrangement_policy == policy
    assert policy["bossa_nova_distance_aware_expression_active"] is True
    assert policy["bossa_nova_distance_aware_expression_version"] == MILESTONE_ID
    assert policy["bossa_nova_distance_aware_expression_no_parallel_resolver"] is True
    assert policy["bossa_nova_distance_aware_expression_no_style_specific_runtime"] is True
    assert policy["bossa_nova_distance_aware_expression_no_pattern_numeric_values"] is True
    assert expression.metadata["bossa_distance_aware_expression_active"] is True
    assert expression.metadata["bossa_distance_aware_expression_version"] == MILESTONE_ID
    assert expression.metadata["bossa_distance_aware_expression_no_parallel_resolver"] is True


def test_v2_6_94_bossa_cell_profiles_declare_policy_driven_distance_articulation() -> None:
    profiles = expression_policy.get_expression_policy().profiles
    for name in ("cell_close_gap_short", "cell_soft_hold"):
        profile = profiles[name]
        assert profile.metadata["bossa_distance_aware_expression_version"] == MILESTONE_ID
        assert profile.metadata["distance_articulation"] == "short_if_close_else_sustain"
        assert profile.metadata["distance_threshold_beats"] == 1.0
        assert profile.metadata["distance_short_duration_beats"] <= 0.45
        assert profile.metadata["distance_sustain_duration_beats"] >= 1.0
        # Keep backward audit compatibility for the v2_6_91 alias milestone.
        assert profile.metadata["numeric_source_profile"] in {"core_short", "core_sustain"}


def test_v2_6_94_shared_expression_resolver_shortens_close_bossa_cell_gap_after_timeline_finalization() -> None:
    region = _region("r0", "Cm7", 0.0, 4.0)
    plan = _candidate("bossa_piano_cell_A_1_2_3and").instantiate(region)
    expression = ExpressionResolver().resolve(list(plan.events), expression_policy.get_expression_policy(), timing_policy={"feel": "straight"})

    first = expression.events[plan.events[0].event_id]
    second = expression.events[plan.events[1].event_id]
    third = expression.events[plan.events[2].event_id]

    assert first.articulation == "short"
    assert first.duration_beats <= 0.45
    assert first.pedal == "none"
    assert first.metadata["distance_articulation_applied"] is True
    assert first.metadata["distance_articulation_branch"] == "short"
    assert second.articulation == "sustain"
    assert second.metadata["distance_articulation_branch"] == "sustain"
    assert third.articulation == "sustain"


def test_v2_6_94_shared_expression_resolver_sustains_wide_bossa_cell_gap_without_crossing_region() -> None:
    region = _region("r0", "Cm7", 0.0, 4.0)
    plan = _candidate("bossa_piano_cell_A_1_3and").instantiate(region)
    expression = ExpressionResolver().resolve(list(plan.events), expression_policy.get_expression_policy(), timing_policy={"feel": "straight"})

    first = expression.events[plan.events[0].event_id]
    second = expression.events[plan.events[1].event_id]

    assert first.articulation == "sustain"
    assert first.metadata["distance_articulation_applied"] is True
    assert first.metadata["distance_articulation_branch"] == "sustain"
    assert first.duration_beats <= 2.5
    assert second.articulation == "sustain"
    assert second.duration_beats <= 1.5


def test_v2_6_94_static_audit_acceptance_requires_runtime_for_full_pass() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static, [])

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["arrangement_policy_version"] == MILESTONE_ID
    assert static["distance_sensitive_profiles"] == ["cell_close_gap_short", "cell_soft_hold"]
    assert static["legacy_alias_metadata_preserved"] is True
    assert acceptance["checks"]["runtime_blue_bossa_full_band_passes"] is False
    assert acceptance["passed"] is False


def test_v2_6_94_blue_bossa_runtime_uses_distance_articulation_without_expression_warnings() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 22704, "slug": "blue_bossa_3x_pytest_v2_6_94"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert runtime["distance_articulation_event_count"] > 0
    assert runtime["distance_articulation_branch_counts"]["short"] > 0
    assert runtime["distance_articulation_branch_counts"]["sustain"] > 0
    assert runtime["distance_close_gap_short_violation_count"] == 0
    assert runtime["distance_wide_gap_sustain_violation_count"] == 0
    assert runtime["expression_warning_count"] == 0
    assert runtime["expression_missing_count"] == 0
    assert runtime["expression_cross_region_count"] == 0
    assert runtime["expression_cross_next_event_count"] == 0
    assert runtime["expression_short_overlap_count"] == 0
    assert runtime["expression_sustain_chop_risk_count"] == 0
    assert runtime["pedal_cc64_event_count"] == 0
    assert acceptance["passed"] is True
