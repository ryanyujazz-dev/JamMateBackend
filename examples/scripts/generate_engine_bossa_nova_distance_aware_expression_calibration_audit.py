from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.bossa_nova import arrangement_policy, expression_policy
from jammate_engine.styles.registry import get_style

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_94"
MILESTONE_LABEL = "v2_6_94 — Engine Bossa Nova Distance-Aware Expression Calibration"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 22704, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 22754, "slug": "blue_bossa_5x"},
)
CORE_BATIDA_PATTERN = "bossa_piano_core_batida_1_2_3and"
HALF_REGION_PATTERN = "bossa_piano_half_region_1_2"


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    runtime_audits = [_generate_runtime_audit(spec) for spec in DEMO_SPECS]
    acceptance = _acceptance(static_audit, runtime_audits)
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": (
            "Calibrate Bossa non-core piano cell expression in place. Style-owned ExpressionProfiles declare distance articulation parameters, "
            "and the shared core ExpressionResolver applies them after anticipation/timeline rewrite. No Bossa-specific resolver, new pattern vocabulary, "
            "core voicing change, MIDI writer change, API, Agent, or HarmonyOS change."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
        "acceptance": acceptance,
        "recommended_next_task": static_audit.get("recommended_next_task"),
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_distance_aware_expression_calibration_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_distance_aware_expression_calibration_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()
    expression = expression_policy.get_expression_policy()
    profiles = expression.profiles
    cell_profiles = {name: profiles[name] for name in ("cell_close_gap_short", "cell_soft_hold")}
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "style_registered": getattr(style, "name", None) == "bossa_nova",
        "arrangement_policy_version": policy.get("bossa_nova_distance_aware_expression_version"),
        "behavior_change": policy.get("bossa_nova_distance_aware_expression_behavior_change"),
        "no_parallel_resolver": policy.get("bossa_nova_distance_aware_expression_no_parallel_resolver"),
        "no_style_specific_runtime": policy.get("bossa_nova_distance_aware_expression_no_style_specific_runtime"),
        "no_pattern_numeric_values": policy.get("bossa_nova_distance_aware_expression_no_pattern_numeric_values"),
        "no_new_pattern_vocabulary": policy.get("bossa_nova_distance_aware_expression_no_new_pattern_vocabulary"),
        "no_core_voicing_change": policy.get("bossa_nova_distance_aware_expression_no_core_voicing_change"),
        "no_api_agent_harmonyos_change": policy.get("bossa_nova_distance_aware_expression_no_api_agent_harmonyos_change"),
        "resolver_hook": policy.get("bossa_nova_distance_aware_expression_resolver_hook"),
        "threshold_beats": policy.get("bossa_nova_distance_aware_expression_threshold_beats"),
        "expression_policy_metadata_version": expression.metadata.get("bossa_distance_aware_expression_version"),
        "expression_policy_no_parallel_resolver": expression.metadata.get("bossa_distance_aware_expression_no_parallel_resolver"),
        "distance_sensitive_profiles": sorted(name for name, profile in profiles.items() if profile.metadata.get("distance_articulation")),
        "cell_profile_thresholds": {name: profile.metadata.get("distance_threshold_beats") for name, profile in cell_profiles.items()},
        "cell_profile_short_durations": {name: profile.metadata.get("distance_short_duration_beats") for name, profile in cell_profiles.items()},
        "cell_profile_sustain_durations": {name: profile.metadata.get("distance_sustain_duration_beats") for name, profile in cell_profiles.items()},
        "legacy_alias_metadata_preserved": all(profile.metadata.get("numeric_source_profile") for profile in cell_profiles.values()),
        "recommended_next_task": policy.get("bossa_nova_distance_aware_expression_recommended_next_task"),
        "known_next_gap": policy.get("bossa_nova_distance_aware_expression_known_next_gap"),
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_distance_aware_expression_calibration_demo.mid"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "bossa_nova",
            "tempo": int(score.get("tempo", 140)),
            "choruses": choruses,
            "seed": seed,
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
        }
    )
    return _summarize_runtime(dict(result.debug), midi_path=midi_path, ok=bool(result.ok), choruses=choruses, seed=seed)


def _summarize_runtime(debug: dict[str, Any], *, midi_path: Path, ok: bool, choruses: int, seed: int) -> dict[str, Any]:
    piano_rows = [row for row in debug.get("piano_musical_audit_events", []) if _pattern_event(row).get("track") == "piano"]
    active_piano = [row for row in piano_rows if _pattern_event(row).get("status") == "active"]
    pattern_counts = Counter(str(_pattern_event(row).get("pattern_id")) for row in active_piano)
    class_a_event_count = sum(count for pattern, count in pattern_counts.items() if "_cell_A_" in pattern)
    class_b_event_count = sum(count for pattern, count in pattern_counts.items() if "_cell_B_" in pattern)
    non_core_event_count = sum(count for pattern, count in pattern_counts.items() if pattern not in {CORE_BATIDA_PATTERN, HALF_REGION_PATTERN})
    opening_rows = [
        row
        for row in active_piano
        if int(_source_metadata(row).get("region_chorus_index", -1)) == 0
        and int(_source_metadata(row).get("region_performance_bar_index", 9999)) in {0, 1}
    ]
    opening_patterns = sorted({str(_pattern_event(row).get("pattern_id")) for row in opening_rows})

    expression_summary = dict(debug.get("expression_foundation_audit") or {})
    expression_rows = list(debug.get("expression_foundation_audit_events") or [])
    distance_rows = [row for row in expression_rows if bool((row.get("metadata") or {}).get("distance_articulation_applied"))]
    distance_branches = Counter(str((row.get("metadata") or {}).get("distance_articulation_branch")) for row in distance_rows)
    distance_profile_counts = Counter(str(row.get("profile_name")) for row in distance_rows)
    distance_short_rows = [row for row in distance_rows if (row.get("metadata") or {}).get("distance_articulation_branch") == "short"]
    distance_sustain_rows = [row for row in distance_rows if (row.get("metadata") or {}).get("distance_articulation_branch") == "sustain"]
    close_gap_short_violations = [
        row
        for row in distance_short_rows
        if float(row.get("gap_to_next_same_track") or 0.0) <= 1.0 + 1e-9 and str(row.get("articulation")) != "short"
    ]
    wide_gap_sustain_violations = [
        row
        for row in distance_sustain_rows
        if float(row.get("gap_to_next_same_track") or 999.0) > 1.0 + 1e-9 and str(row.get("articulation")) != "sustain"
    ]
    pedal_audit = dict(debug.get("pedal_realization_audit") or {})
    piano_audit = dict(debug.get("piano_musical_audit") or {})
    anticipations = [_anticipation_metadata(row) for row in active_piano if _anticipation_metadata(row).get("kind") == "next_beat1_to_previous_tail"]
    terminal_ending_anticipations = [
        row
        for row in active_piano
        if _anticipation_metadata(row).get("kind") == "next_beat1_to_previous_tail"
        and _source_metadata(row).get("region_chorus_index") == int(_source_metadata(row).get("region_total_choruses", 0) or 0) - 1
        and bool(_source_metadata(row).get("region_is_last_bar_of_chorus"))
    ]
    return {
        "ok": ok,
        "choruses": choruses,
        "seed": seed,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "title": debug.get("title"),
        "style": debug.get("style"),
        "performance_bars": debug.get("performance_bars"),
        "regions": debug.get("regions"),
        "note_events_by_track": debug.get("note_events_by_track"),
        "piano_active_events": len(active_piano),
        "piano_pattern_counts": dict(pattern_counts),
        "piano_non_core_pattern_event_count": non_core_event_count,
        "piano_class_A_event_count": class_a_event_count,
        "piano_class_B_event_count": class_b_event_count,
        "piano_class_B_ratio_of_non_core_events": round(class_b_event_count / non_core_event_count, 4) if non_core_event_count else 0.0,
        "opening_first_two_bars_patterns": opening_patterns,
        "opening_first_two_bars_core_only": bool(opening_rows) and all(pattern in {CORE_BATIDA_PATTERN, HALF_REGION_PATTERN} for pattern in opening_patterns),
        "distance_articulation_event_count": len(distance_rows),
        "distance_articulation_branch_counts": dict(distance_branches),
        "distance_articulation_profile_counts": dict(distance_profile_counts),
        "distance_close_gap_short_violation_count": len(close_gap_short_violations),
        "distance_wide_gap_sustain_violation_count": len(wide_gap_sustain_violations),
        "expression_profiles": expression_summary.get("profiles"),
        "expression_articulations": expression_summary.get("articulations"),
        "expression_pedal_modes": expression_summary.get("pedal_modes"),
        "expression_avg_velocity": expression_summary.get("avg_velocity"),
        "expression_avg_duration_beats": expression_summary.get("avg_duration_beats"),
        "expression_warning_count": expression_summary.get("warning_count"),
        "expression_missing_count": expression_summary.get("missing_expression_count"),
        "expression_cross_region_count": expression_summary.get("cross_region_count"),
        "expression_cross_next_event_count": expression_summary.get("cross_next_event_count"),
        "expression_short_overlap_count": expression_summary.get("short_overlap_count"),
        "expression_sustain_chop_risk_count": expression_summary.get("sustain_chop_risk_count"),
        "active_anticipation_count": len(anticipations),
        "terminal_ending_anticipation_count": len(terminal_ending_anticipations),
        "anticipation_timing_grids": sorted({str(item.get("timing_grid")) for item in anticipations}),
        "pedal_cc64_event_count": pedal_audit.get("cc64_event_count"),
        "piano_lower_foundation_low_register_events": piano_audit.get("lower_foundation_low_register_events"),
        "piano_lower_foundation_span_violation_events": piano_audit.get("lower_foundation_span_violation_events"),
    }


def _pattern_event(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("pattern_event") or {}
    return dict(value) if isinstance(value, dict) else {}


def _source_metadata(row: dict[str, Any]) -> dict[str, Any]:
    metadata = _pattern_event(row).get("metadata") or {}
    return dict(metadata) if isinstance(metadata, dict) else {}


def _anticipation_metadata(row: dict[str, Any]) -> dict[str, Any]:
    anticipation = _source_metadata(row).get("anticipation") or {}
    return dict(anticipation) if isinstance(anticipation, dict) else {}


def _acceptance(static_audit: dict[str, Any], runtime_audits: list[dict[str, Any]]) -> dict[str, Any]:
    runtime_ok = bool(runtime_audits) and all(_runtime_accepts(item) for item in runtime_audits)
    checks = {
        "style_and_policy_registered": static_audit.get("style_registered") is True and static_audit.get("arrangement_policy_version") == MILESTONE_ID,
        "in_place_boundaries_preserved": static_audit.get("behavior_change") is True
        and static_audit.get("no_parallel_resolver") is True
        and static_audit.get("no_style_specific_runtime") is True
        and static_audit.get("no_pattern_numeric_values") is True
        and static_audit.get("no_new_pattern_vocabulary") is True
        and static_audit.get("no_core_voicing_change") is True
        and static_audit.get("no_api_agent_harmonyos_change") is True,
        "expression_policy_declares_distance_profiles": static_audit.get("expression_policy_metadata_version") == MILESTONE_ID
        and static_audit.get("distance_sensitive_profiles") == ["cell_close_gap_short", "cell_soft_hold"]
        and static_audit.get("legacy_alias_metadata_preserved") is True,
        "runtime_blue_bossa_full_band_passes": runtime_ok,
    }
    return {"passed": all(checks.values()), "checks": checks}


def _runtime_accepts(item: dict[str, Any]) -> bool:
    note_counts = dict(item.get("note_events_by_track") or {})
    non_core = int(item.get("piano_non_core_pattern_event_count") or 0)
    class_a = int(item.get("piano_class_A_event_count") or 0)
    class_b = int(item.get("piano_class_B_event_count") or 0)
    branch_counts = dict(item.get("distance_articulation_branch_counts") or {})
    return (
        item.get("ok") is True
        and int(note_counts.get("piano", 0)) > 0
        and int(note_counts.get("bass", 0)) > 0
        and int(note_counts.get("drums", 0)) > 0
        and non_core > 0
        and class_a > class_b >= 0
        and float(item.get("piano_class_B_ratio_of_non_core_events") or 0.0) <= 0.22
        and item.get("opening_first_two_bars_core_only") is True
        and int(item.get("distance_articulation_event_count") or 0) > 0
        and int(branch_counts.get("short", 0)) > 0
        and int(branch_counts.get("sustain", 0)) > 0
        and int(item.get("distance_close_gap_short_violation_count") or 0) == 0
        and int(item.get("distance_wide_gap_sustain_violation_count") or 0) == 0
        and int(item.get("expression_warning_count") or 0) == 0
        and int(item.get("expression_missing_count") or 0) == 0
        and int(item.get("expression_cross_region_count") or 0) == 0
        and int(item.get("expression_cross_next_event_count") or 0) == 0
        and int(item.get("expression_short_overlap_count") or 0) == 0
        and int(item.get("expression_sustain_chop_risk_count") or 0) == 0
        and int(item.get("active_anticipation_count") or 0) > 0
        and int(item.get("terminal_ending_anticipation_count") or 0) == 0
        and item.get("anticipation_timing_grids") == ["straight_upbeat"]
        and int(item.get("pedal_cc64_event_count") or 0) == 0
        and int(item.get("piano_lower_foundation_low_register_events") or 0) == 0
        and int(item.get("piano_lower_foundation_span_violation_events") or 0) == 0
    )


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
        "## Static expression audit",
        "",
        f"- Arrangement policy version: `{static.get('arrangement_policy_version')}`",
        f"- Resolver hook: `{static.get('resolver_hook')}`",
        f"- Distance threshold: `{static.get('threshold_beats')}`",
        f"- Distance-sensitive profiles: `{static.get('distance_sensitive_profiles')}`",
        f"- Legacy alias metadata preserved: `{static.get('legacy_alias_metadata_preserved')}`",
        "",
        "## Runtime Blue Bossa audits",
        "",
    ]
    for item in summary.get("runtime_audits") or []:
        lines.extend(
            [
                f"### {item.get('choruses')} choruses / seed `{item.get('seed')}`",
                "",
                f"- MIDI: `{item.get('midi_path')}`",
                f"- Notes by track: `{item.get('note_events_by_track')}`",
                f"- Non-core / Class A / Class B event counts: `{item.get('piano_non_core_pattern_event_count')}` / `{item.get('piano_class_A_event_count')}` / `{item.get('piano_class_B_event_count')}`",
                f"- Distance articulation events: `{item.get('distance_articulation_event_count')}`",
                f"- Distance articulation branches: `{item.get('distance_articulation_branch_counts')}`",
                f"- Expression profiles: `{item.get('expression_profiles')}`",
                f"- Expression articulations: `{item.get('expression_articulations')}`",
                f"- Expression avg velocity / duration: `{item.get('expression_avg_velocity')}` / `{item.get('expression_avg_duration_beats')}`",
                f"- Expression warnings / missing / cross-region / cross-next-event / short-overlap / sustain-chop: `{item.get('expression_warning_count')}` / `{item.get('expression_missing_count')}` / `{item.get('expression_cross_region_count')}` / `{item.get('expression_cross_next_event_count')}` / `{item.get('expression_short_overlap_count')}` / `{item.get('expression_sustain_chop_risk_count')}`",
                f"- Active anticipations / terminal-ending anticipations: `{item.get('active_anticipation_count')}` / `{item.get('terminal_ending_anticipation_count')}`",
                f"- Pedal CC64 events: `{item.get('pedal_cc64_event_count')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Known next gap",
            "",
            str(static.get("known_next_gap")),
            "",
            f"Recommended next task: `{summary.get('recommended_next_task')}`",
            "",
            "## Acceptance",
            "",
            f"Passed: `{acceptance.get('passed')}`",
            "",
        ]
    )
    for name, ok in dict(acceptance.get("checks") or {}).items():
        lines.append(f"- `{name}`: `{ok}`")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
