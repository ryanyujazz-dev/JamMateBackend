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
from jammate_engine.styles.bossa_nova import arrangement_policy, comping_patterns, expression_policy
from jammate_engine.styles.registry import get_style

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_90"
MILESTONE_LABEL = "v2_6_90 — Engine Bossa Nova Style Baseline Audit"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 22702, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 22752, "slug": "blue_bossa_5x"},
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
            "Bossa Nova baseline audit from the latest v2_10_28/v2_6_89 handoff baseline. "
            "This pass cleans misleading legacy Bossa metadata and audits the current Blue Bossa full-band runtime without adding rhythm vocabulary, "
            "changing expression numeric values, modifying core voicing, or touching API/Agent/HarmonyOS."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
        "acceptance": acceptance,
        "recommended_next_task": static_audit.get("recommended_next_task"),
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_style_baseline_audit_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_style_baseline_audit_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()
    full_library = comping_patterns.describe_pattern_library({"region_duration_beats": 4.0})
    half_library = comping_patterns.describe_pattern_library({"region_duration_beats": 2.0})
    full_candidates = [dict(candidate) for candidate in full_library["candidates"]]
    half_candidates = [dict(candidate) for candidate in half_library["candidates"]]
    expression_profiles = expression_policy.get_expression_policy().profiles
    all_tags = [str(tag) for candidate in [*full_candidates, *half_candidates] for tag in candidate.get("tags", [])]
    legacy_tags = sorted({tag for tag in all_tags if tag in {"two_chord_bar", "bar_first", "split_bar"}})
    core = _find_candidate(full_candidates, CORE_BATIDA_PATTERN)
    half = _find_candidate(half_candidates, HALF_REGION_PATTERN)
    arrangement_from_style = dict(style.arrangement_policy)

    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "style_registered": getattr(style, "name", None) == "bossa_nova",
        "arrangement_policy_version": arrangement_from_style.get("bossa_nova_style_baseline_audit_version"),
        "arrangement_policy_behavior_change": arrangement_from_style.get("bossa_nova_style_baseline_audit_behavior_change"),
        "no_new_pattern_vocabulary": arrangement_from_style.get("bossa_nova_style_baseline_audit_no_new_pattern_vocabulary"),
        "no_expression_numeric_change": arrangement_from_style.get("bossa_nova_style_baseline_audit_no_expression_numeric_change"),
        "no_core_voicing_change": arrangement_from_style.get("bossa_nova_style_baseline_audit_no_core_voicing_change"),
        "no_api_agent_harmonyos_change": arrangement_from_style.get("bossa_nova_style_baseline_audit_no_api_agent_harmonyos_change"),
        "opening_core_batida_bars": arrangement_from_style.get("opening_core_batida_bars"),
        "pattern_library_version": full_library.get("version"),
        "full_region_candidate_count": full_library.get("candidate_count"),
        "half_region_candidate_count": half_library.get("candidate_count"),
        "full_region_core_batida_beats": core.get("rhythm_beats") if core else [],
        "full_region_core_batida_expression_hints": [event.get("expression_hint") for event in core.get("events", [])] if core else [],
        "half_region_beats": half.get("rhythm_beats") if half else [],
        "half_region_expression_hints": [event.get("expression_hint") for event in half.get("events", [])] if half else [],
        "legacy_bar_first_tags": legacy_tags,
        "chord_region_first_half_region_tag_present": "chord_region_first" in all_tags and "two_beat_region" in all_tags,
        "pattern_boundary_notes": full_library.get("boundary_notes"),
        "expression_profiles": {
            name: {
                "duration_beats": profile.duration_beats,
                "velocity": profile.velocity,
                "articulation": str(profile.articulation.value),
                "pedal": str(profile.pedal.value),
                "touch": str(profile.touch.value),
                "release_beats": profile.release_beats,
            }
            for name, profile in expression_profiles.items()
        },
        "recommended_next_task": arrangement_from_style.get("bossa_nova_style_baseline_audit_recommended_next_task"),
        "known_next_gap": arrangement_from_style.get("bossa_nova_style_baseline_audit_known_next_gap"),
    }


def _find_candidate(candidates: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    return next((candidate for candidate in candidates if candidate.get("name") == name), None)


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_style_baseline_audit_demo.mid"
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
    debug = dict(result.debug)
    return _summarize_runtime(debug, midi_path=midi_path, ok=bool(result.ok), choruses=choruses, seed=seed)


def _summarize_runtime(debug: dict[str, Any], *, midi_path: Path, ok: bool, choruses: int, seed: int) -> dict[str, Any]:
    piano_rows = [row for row in debug.get("piano_musical_audit_events", []) if _pattern_event(row).get("track") == "piano"]
    active_piano = [row for row in piano_rows if _pattern_event(row).get("status") == "active"]
    pattern_counts = Counter(str(_pattern_event(row).get("pattern_id")) for row in active_piano)
    expression_summary = dict(debug.get("expression_foundation_audit") or {})
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
    opening_rows = [
        row
        for row in active_piano
        if int(_source_metadata(row).get("region_chorus_index", -1)) == 0
        and int(_source_metadata(row).get("region_performance_bar_index", 9999)) in {0, 1}
    ]
    opening_patterns = sorted({str(_pattern_event(row).get("pattern_id")) for row in opening_rows})
    source_durations = Counter(str(_source_metadata(row).get("region_duration_beats")) for row in active_piano)
    expected_tail_slots = Counter(
        str(_anticipation_metadata(row).get("target_local_beat_in_previous"))
        for row in active_piano
        if _anticipation_metadata(row).get("kind") == "next_beat1_to_previous_tail"
    )

    return {
        "ok": ok,
        "choruses": choruses,
        "seed": seed,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "title": debug.get("title"),
        "style": debug.get("style"),
        "performance_bars": debug.get("performance_bars"),
        "regions": debug.get("regions"),
        "pattern_events": debug.get("pattern_events"),
        "active_pattern_events": debug.get("active_pattern_events"),
        "suppressed_pattern_events": debug.get("suppressed_pattern_events"),
        "note_events_by_track": debug.get("note_events_by_track"),
        "piano_active_events": len(active_piano),
        "piano_pattern_counts": dict(pattern_counts),
        "piano_non_core_pattern_count": sum(count for pattern, count in pattern_counts.items() if pattern not in {CORE_BATIDA_PATTERN, HALF_REGION_PATTERN}),
        "opening_first_two_bars_patterns": opening_patterns,
        "opening_first_two_bars_core_only": bool(opening_rows) and all(pattern in {CORE_BATIDA_PATTERN, HALF_REGION_PATTERN} for pattern in opening_patterns),
        "region_duration_source_counts": dict(source_durations),
        "active_anticipation_count": len(anticipations),
        "anticipated_target_local_slots": dict(expected_tail_slots),
        "terminal_ending_anticipation_count": len(terminal_ending_anticipations),
        "anticipation_timing_grids": sorted({str(item.get("timing_grid")) for item in anticipations}),
        "anticipation_target_timing_intents": sorted({str(item.get("target_timing_intent")) for item in anticipations}),
        "anticipation_expected_upbeat_fractions": sorted({str(item.get("expected_upbeat_fraction")) for item in anticipations}),
        "expression_profiles": expression_summary.get("profiles"),
        "articulations": expression_summary.get("articulations"),
        "pedal_modes": expression_summary.get("pedal_modes"),
        "expression_warning_count": expression_summary.get("warning_count"),
        "expression_missing_count": expression_summary.get("missing_expression_count"),
        "expression_cross_region_count": expression_summary.get("cross_region_count"),
        "expression_cross_next_event_count": expression_summary.get("cross_next_event_count"),
        "anticipation_tie_event_count": expression_summary.get("anticipation_tie_event_count"),
        "anticipation_pedal_modes": expression_summary.get("anticipation_pedal_modes"),
        "pedal_cc64_event_count": pedal_audit.get("cc64_event_count"),
        "pedal_light_intents_suppressed_by_style": int((pedal_audit.get("suppressed_note_counts_by_reason") or {}).get("light:style_boundary", 0)),
        "piano_content_families": piano_audit.get("content_families"),
        "piano_densities": piano_audit.get("densities"),
        "piano_dispositions": piano_audit.get("dispositions"),
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
        "style_and_policy_registered": static_audit.get("style_registered") is True
        and static_audit.get("arrangement_policy_version") == MILESTONE_ID,
        "baseline_audit_is_behavior_preserving": static_audit.get("arrangement_policy_behavior_change") is False
        and static_audit.get("no_new_pattern_vocabulary") is True
        and static_audit.get("no_expression_numeric_change") is True
        and static_audit.get("no_core_voicing_change") is True
        and static_audit.get("no_api_agent_harmonyos_change") is True,
        "core_batida_identity_matches_user_rule": static_audit.get("full_region_core_batida_beats") == [0.0, 1.0, 2.5]
        and static_audit.get("full_region_core_batida_expression_hints") == ["core_short", "core_short", "core_sustain"],
        "half_region_is_chord_region_first": static_audit.get("legacy_bar_first_tags") == []
        and static_audit.get("chord_region_first_half_region_tag_present") is True,
        "runtime_blue_bossa_full_band_passes": runtime_ok,
    }
    return {"passed": all(checks.values()), "checks": checks}


def _runtime_accepts(item: dict[str, Any]) -> bool:
    note_counts = dict(item.get("note_events_by_track") or {})
    return (
        item.get("ok") is True
        and int(note_counts.get("piano", 0)) > 0
        and int(note_counts.get("bass", 0)) > 0
        and int(note_counts.get("drums", 0)) > 0
        and int(item.get("piano_non_core_pattern_count") or 0) == 0
        and item.get("opening_first_two_bars_core_only") is True
        and int(item.get("active_anticipation_count") or 0) > 0
        and int(item.get("terminal_ending_anticipation_count") or 0) == 0
        and item.get("anticipation_timing_grids") == ["straight_upbeat"]
        and item.get("anticipation_expected_upbeat_fractions") == ["0.5"]
        and int(item.get("expression_warning_count") or 0) == 0
        and int(item.get("expression_missing_count") or 0) == 0
        and int(item.get("expression_cross_region_count") or 0) == 0
        and int(item.get("expression_cross_next_event_count") or 0) == 0
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
        "## Static Bossa policy audit",
        "",
        f"- Arrangement policy version: `{static.get('arrangement_policy_version')}`",
        f"- Core batida beats: `{static.get('full_region_core_batida_beats')}`",
        f"- Core batida expression hints: `{static.get('full_region_core_batida_expression_hints')}`",
        f"- Half-region beats: `{static.get('half_region_beats')}`",
        f"- Legacy bar-first tags: `{static.get('legacy_bar_first_tags')}`",
        f"- Behavior change: `{static.get('arrangement_policy_behavior_change')}`",
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
                f"- Piano pattern counts: `{item.get('piano_pattern_counts')}`",
                f"- Opening first two bars patterns: `{item.get('opening_first_two_bars_patterns')}`",
                f"- Active anticipations: `{item.get('active_anticipation_count')}`",
                f"- Terminal-ending anticipations: `{item.get('terminal_ending_anticipation_count')}`",
                f"- Expression warnings / missing / cross-region / cross-next-event: `{item.get('expression_warning_count')}` / `{item.get('expression_missing_count')}` / `{item.get('expression_cross_region_count')}` / `{item.get('expression_cross_next_event_count')}`",
                f"- Pedal CC64 events: `{item.get('pedal_cc64_event_count')}`",
                f"- Piano content families: `{item.get('piano_content_families')}`",
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
