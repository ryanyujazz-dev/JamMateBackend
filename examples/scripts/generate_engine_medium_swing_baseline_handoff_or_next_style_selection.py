from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.styles.medium_swing import arrangement_policy
from jammate_engine.styles.bossa_nova import comping_patterns
from jammate_engine.styles.registry import get_style

DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_89"
MILESTONE_LABEL = "v2_6_89 — Engine Medium Swing Baseline Handoff / Next Style Selection"
DEFAULT_NEXT_STYLE = "bossa_nova"
DEFAULT_NEXT_TASK = "v2_6_90_engine_bossa_nova_style_baseline_audit_from_latest_v2_10_28"
REFERENCE_DEMOS = (
    "v2_6_88_all_the_things_you_are_3x_medium_swing_style_baseline_phase_completion_checkpoint_demo.mid",
    "v2_6_88_autumn_leaves_3x_medium_swing_style_baseline_phase_completion_checkpoint_demo.mid",
    "v2_6_88_all_the_things_you_are_5x_medium_swing_style_baseline_phase_completion_checkpoint_demo.mid",
    "v2_6_88_autumn_leaves_5x_medium_swing_style_baseline_phase_completion_checkpoint_demo.mid",
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    acceptance = _acceptance(static_audit)
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": (
            "Behavior-preserving Engine-line handoff after the v2_6_88 Medium Swing full-band baseline. "
            "This checkpoint freezes Medium Swing as the current reference unless a concrete listening issue is reported, "
            "keeps pattern/expression/voicing/API/Agent/HarmonyOS behavior unchanged, and selects Bossa Nova as the default next style audit target."
        ),
        "static_audit": static_audit,
        "acceptance": acceptance,
        "recommended_next_task": DEFAULT_NEXT_TASK,
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_medium_swing_baseline_handoff_or_next_style_selection_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_medium_swing_baseline_handoff_or_next_style_selection_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    medium_swing_policy = arrangement_policy.get_arrangement_policy()
    bossa_style = get_style(DEFAULT_NEXT_STYLE)
    bossa_library = comping_patterns.describe_pattern_library({"region_duration_beats": 4.0})
    bossa_short_library = comping_patterns.describe_pattern_library({"region_duration_beats": 2.0})
    bossa_candidates = [dict(candidate) for candidate in bossa_library["candidates"]]
    bossa_short_candidates = [dict(candidate) for candidate in bossa_short_library["candidates"]]
    core_candidates = [candidate for candidate in bossa_candidates if "core_batida" in str(candidate.get("name"))]
    legacy_tags = sorted(
        {
            str(tag)
            for candidate in [*bossa_candidates, *bossa_short_candidates]
            for tag in candidate.get("tags", [])
            if str(tag) in {"two_chord_bar", "bar_first", "split_bar"}
        }
    )
    reference_demo_status = {name: (DEMOS_DIR / name).exists() for name in REFERENCE_DEMOS}
    repeat_cases = (1, 2, 3, 5, 6, 8, 9, 10, 50)
    repeat_arcs = {str(count): arrangement_policy.simulate_repeat_count_arrangement_arc(count) for count in repeat_cases}

    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "medium_swing_baseline_complete": bool(medium_swing_policy.get("medium_swing_style_baseline_phase_completion_checkpoint")),
        "medium_swing_baseline_version": medium_swing_policy.get("medium_swing_style_baseline_phase_completion_checkpoint_version"),
        "handoff_enabled": bool(medium_swing_policy.get("medium_swing_baseline_handoff_or_next_style_selection")),
        "handoff_version": medium_swing_policy.get("medium_swing_baseline_handoff_or_next_style_selection_version"),
        "handoff_contract": medium_swing_policy.get("medium_swing_baseline_handoff_or_next_style_selection_contract"),
        "handoff_freeze_condition": medium_swing_policy.get("medium_swing_baseline_handoff_freeze_condition"),
        "handoff_behavior_change": bool(medium_swing_policy.get("medium_swing_baseline_handoff_behavior_change")),
        "handoff_no_pattern_change": bool(medium_swing_policy.get("medium_swing_baseline_handoff_no_pattern_change")),
        "handoff_no_core_voicing_change": bool(medium_swing_policy.get("medium_swing_baseline_handoff_no_core_voicing_change")),
        "handoff_no_expression_numeric_change": bool(medium_swing_policy.get("medium_swing_baseline_handoff_no_expression_numeric_change")),
        "handoff_no_api_agent_harmonyos_change": bool(medium_swing_policy.get("medium_swing_baseline_handoff_no_api_agent_harmonyos_change")),
        "recommended_next_style": medium_swing_policy.get("medium_swing_baseline_handoff_recommended_next_style"),
        "recommended_next_task": medium_swing_policy.get("medium_swing_baseline_handoff_recommended_next_task"),
        "repeat_policy_cases": list(repeat_cases),
        "repeat_policy_long_loop_has_reset": any(item["phase"] == "loop_wave_reset" for item in repeat_arcs["50"]),
        "repeat_policy_long_loop_has_peak": any(item["phase"] == "loop_wave_peak" for item in repeat_arcs["50"]),
        "repeat_policy_50x_final_phase": repeat_arcs["50"][-1]["phase"],
        "reference_medium_swing_demo_status": reference_demo_status,
        "reference_medium_swing_demos_present": all(reference_demo_status.values()),
        "bossa_style_registered": getattr(bossa_style, "name", None) == DEFAULT_NEXT_STYLE,
        "bossa_pattern_library_version": bossa_library.get("version"),
        "bossa_pattern_candidate_count": bossa_library.get("candidate_count"),
        "bossa_short_region_candidate_count": bossa_short_library.get("candidate_count"),
        "bossa_core_batida_candidate_count": len(core_candidates),
        "bossa_core_batida_beats": core_candidates[0].get("rhythm_beats") if core_candidates else [],
        "bossa_core_batida_expression_hints": [event.get("expression_hint") for event in core_candidates[0].get("events", [])] if core_candidates else [],
        "bossa_core_batida_boundary_notes": bossa_library.get("boundary_notes"),
        "bossa_nonblocking_next_audit_findings": _next_audit_findings(legacy_tags),
    }


def _next_audit_findings(legacy_tags: list[str]) -> list[str]:
    findings = [
        "audit opening two bars: pickup/opening should use core_batida as identity anchor",
        "audit generic AnticipationResolver behavior across Bossa barlines and two-bar continuity",
        "audit distance-based articulation after anticipation before touching numeric expression values",
        "audit bass/piano/percussion interaction against the Medium Swing full-band baseline method",
    ]
    if legacy_tags:
        findings.append(f"inspect and clean legacy tag(s) in Bossa pattern metadata if still semantically misleading: {', '.join(legacy_tags)}")
    return findings


def _acceptance(static_audit: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "medium_swing_v2_6_88_baseline_present": static_audit.get("medium_swing_baseline_complete") is True
        and static_audit.get("medium_swing_baseline_version") == "v2_6_88",
        "handoff_metadata_present": static_audit.get("handoff_enabled") is True and static_audit.get("handoff_version") == MILESTONE_ID,
        "handoff_is_behavior_preserving": static_audit.get("handoff_behavior_change") is False
        and static_audit.get("handoff_no_pattern_change") is True
        and static_audit.get("handoff_no_core_voicing_change") is True
        and static_audit.get("handoff_no_expression_numeric_change") is True
        and static_audit.get("handoff_no_api_agent_harmonyos_change") is True,
        "repeat_count_aware_policy_still_safe": static_audit.get("repeat_policy_long_loop_has_reset") is True
        and static_audit.get("repeat_policy_long_loop_has_peak") is True
        and static_audit.get("repeat_policy_50x_final_phase") == "final_head_out_release",
        "reference_demos_present": static_audit.get("reference_medium_swing_demos_present") is True,
        "bossa_default_next_style_ready_for_audit": static_audit.get("recommended_next_style") == DEFAULT_NEXT_STYLE
        and static_audit.get("recommended_next_task") == DEFAULT_NEXT_TASK
        and static_audit.get("bossa_style_registered") is True
        and int(static_audit.get("bossa_core_batida_candidate_count") or 0) >= 1
        and static_audit.get("bossa_core_batida_beats") == [0.0, 1.0, 2.5]
        and static_audit.get("bossa_core_batida_expression_hints") == ["core_short", "core_short", "core_sustain"],
    }
    return {"passed": all(checks.values()), "checks": checks}


def _render_report(summary: dict[str, Any]) -> str:
    static = dict(summary["static_audit"])
    acceptance = dict(summary["acceptance"])
    lines = [
        f"# {MILESTONE_LABEL}",
        "",
        f"Engine version tag: `{summary['contract_version']}`",
        "",
        "## Scope",
        "",
        str(summary["scope"]),
        "",
        "## Handoff decision",
        "",
        f"- Medium Swing baseline: `{static.get('medium_swing_baseline_version')}`",
        f"- Handoff checkpoint: `{static.get('handoff_version')}`",
        f"- Freeze condition: `{static.get('handoff_freeze_condition')}`",
        f"- Recommended next style: `{static.get('recommended_next_style')}`",
        f"- Recommended next task: `{static.get('recommended_next_task')}`",
        "",
        "## Behavior boundary",
        "",
        f"- Pattern change: `{not static.get('handoff_no_pattern_change')}`",
        f"- Core voicing change: `{not static.get('handoff_no_core_voicing_change')}`",
        f"- Expression numeric change: `{not static.get('handoff_no_expression_numeric_change')}`",
        f"- API/Agent/HarmonyOS change: `{not static.get('handoff_no_api_agent_harmonyos_change')}`",
        "",
        "## Bossa Nova audit runway",
        "",
        f"- Style registered: `{static.get('bossa_style_registered')}`",
        f"- Pattern library version: `{static.get('bossa_pattern_library_version')}`",
        f"- Core batida beats: `{static.get('bossa_core_batida_beats')}`",
        f"- Core batida expression hints: `{static.get('bossa_core_batida_expression_hints')}`",
        "",
        "## Non-blocking next audit findings",
        "",
    ]
    for finding in static.get("bossa_nonblocking_next_audit_findings") or []:
        lines.append(f"- {finding}")
    lines.extend([
        "",
        "## Acceptance",
        "",
        f"Passed: `{acceptance.get('passed')}`",
        "",
    ])
    for name, ok in dict(acceptance.get("checks") or {}).items():
        lines.append(f"- `{name}`: `{ok}`")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
