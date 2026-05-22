from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.styles.medium_swing import arrangement_policy
from jammate_engine.styles.bossa_nova import comping_patterns
from jammate_engine.styles.registry import get_style


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_medium_swing_baseline_handoff_or_next_style_selection.py"
    spec = importlib.util.spec_from_file_location("generate_engine_medium_swing_baseline_handoff_or_next_style_selection", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_6_89_declares_medium_swing_handoff_without_behavior_change() -> None:
    policy = arrangement_policy.get_arrangement_policy()

    assert policy["medium_swing_style_baseline_phase_completion_checkpoint"] is True
    assert policy["medium_swing_style_baseline_phase_completion_checkpoint_version"] == "v2_6_88"
    assert policy["medium_swing_baseline_handoff_or_next_style_selection"] is True
    assert policy["medium_swing_baseline_handoff_or_next_style_selection_version"] == "v2_6_89"
    assert policy["medium_swing_baseline_handoff_behavior_change"] is False
    assert policy["medium_swing_baseline_handoff_no_pattern_change"] is True
    assert policy["medium_swing_baseline_handoff_no_core_voicing_change"] is True
    assert policy["medium_swing_baseline_handoff_no_expression_numeric_change"] is True
    assert policy["medium_swing_baseline_handoff_no_api_agent_harmonyos_change"] is True
    assert policy["medium_swing_baseline_handoff_freeze_condition"] == "freeze_medium_swing_unless_user_reports_specific_listening_issue"
    assert policy["medium_swing_baseline_handoff_recommended_next_style"] == "bossa_nova"
    assert policy["medium_swing_baseline_handoff_recommended_next_task"] == "v2_6_90_engine_bossa_nova_style_baseline_audit_from_latest_v2_10_28"
    assert policy["medium_swing_baseline_handoff_or_next_style_selection_milestone"] == "v2_6_89_engine_medium_swing_baseline_handoff_or_next_style_selection"


def test_v2_6_89_keeps_repeat_count_policy_safe_for_long_practice_loops() -> None:
    counts = (1, 2, 3, 5, 6, 8, 9, 10, 50)
    arcs = {count: arrangement_policy.simulate_repeat_count_arrangement_arc(count) for count in counts}

    assert arcs[1][0]["phase"] == "single_pass_balanced"
    assert arcs[2][0]["phase"] == "head_in_clear"
    assert arcs[2][-1]["phase"] == "final_head_out_release"
    assert arcs[50][-1]["phase"] == "final_head_out_release"
    assert any(item["phase"] == "loop_wave_reset" for item in arcs[50])
    assert any(item["phase"] == "loop_wave_peak" for item in arcs[50])
    assert all(item["monotonic_ramp_allowed"] is False for arc in arcs.values() for item in arc)


def test_v2_6_89_confirms_bossa_nova_as_next_audit_runway_not_music_change() -> None:
    style = get_style("bossa_nova")
    library = comping_patterns.describe_pattern_library({"region_duration_beats": 4.0})
    candidates = list(library["candidates"])
    core = [candidate for candidate in candidates if candidate["name"] == "bossa_piano_core_batida_1_2_3and"]

    assert style.name == "bossa_nova"
    assert library["version"] in {"v2_0_42", "v2_6_90"}
    assert library["boundary_notes"] == [
        "pitchless",
        "style_owned",
        "identity_anchor_only_for_current_runtime",
        "no_voicing_logic",
        "no_final_expression_values",
    ]
    assert len(core) == 1
    assert core[0]["rhythm_beats"] == [0.0, 1.0, 2.5]
    assert [event["expression_hint"] for event in core[0]["events"]] == ["core_short", "core_short", "core_sustain"]


def test_v2_6_89_static_handoff_audit_acceptance_passes() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static)

    assert static["checkpoint_version"] == "v2_6_89"
    assert static["medium_swing_baseline_complete"] is True
    assert static["medium_swing_baseline_version"] == "v2_6_88"
    assert static["handoff_enabled"] is True
    assert static["handoff_version"] == "v2_6_89"
    assert static["recommended_next_style"] == "bossa_nova"
    findings = static["bossa_nonblocking_next_audit_findings"]
    assert "audit generic AnticipationResolver behavior across Bossa barlines and two-bar continuity" in findings
    assert not any("two_chord_bar" in finding for finding in findings)
    assert acceptance["passed"] is True
