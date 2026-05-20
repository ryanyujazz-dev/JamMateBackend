from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.medium_swing import arrangement_policy, comping_patterns
from jammate_engine.styles.medium_swing.expression_policy import get_expression_policy

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_70"
MILESTONE_LABEL = "v2_6_70 — Medium Swing Ending-Specific Region Context Candidate Subset Policy"
FORBIDDEN_PATTERN_EXPRESSION_KEYS = {"velocity", "duration", "duration_beats", "pedal", "release_beats", "accent", "midi_note"}
FORBIDDEN_PATTERN_VOICING_KEYS = {
    "midi_notes",
    "notes",
    "degrees",
    "chord_tones",
    "voicing",
    "voicing_degrees",
    "content_family",
    "disposition",
    "projection_method",
}
REQUIRED_PRIOR_POLICY_KEYS = {
    "piano_region_length_pattern_vocabulary_version": "v2_6_56",
    "piano_region_length_candidate_lookup_policy_version": "v2_6_57",
    "piano_region_length_weight_calibration_policy_version": "v2_6_58",
    "piano_comping_history_continuity_scorer_version": "v2_6_59",
    "piano_comping_harmonic_function_policy_version": "v2_6_60",
    "piano_region_first_anticipation_compatibility_checkpoint_version": "v2_6_61",
    "piano_region_first_coverage_guard_version": "v2_6_62",
    "piano_comping_progression_specific_subset_policy_version": "v2_6_65",
    "piano_comping_no_4and_delayed_tail_idiom_policy_version": "v2_6_66",
    "piano_comping_active_fill_busy_multi_region_history_scorer_version": "v2_6_67",
    "piano_expression_policy_v1_numeric_calibration_version": "v2_6_68",
    "piano_standard_tune_listening_checkpoint_version": "v2_6_69",
}

SPECS: tuple[dict[str, Any], ...] = (
    {"slug": "all_the_things_you_are", "leadsheet": "all_the_things_you_are.json", "seed": 3700},
    {"slug": "autumn_leaves", "leadsheet": "autumn_leaves.json", "seed": 3701},
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    outputs = [_generate_and_audit(spec) for spec in SPECS]
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": (
            "Medium Swing piano ending-specific candidate subset policy. Final-bar ChordRegions are reweighted inside "
            "the existing region-length pool toward stable region-start settling and away from active/4& push. This "
            "does not add an ending selector, new vocabulary, voicing logic, or final expression values."
        ),
        "static_audit": static_audit,
        "outputs": outputs,
        "acceptance": _acceptance(static_audit, outputs),
        "recommended_next_tasks": [
            "v2_6_71_engine_medium_swing_optional_fill_variation_vocabulary_activation",
            "v2_6_72_engine_medium_swing_ending_listening_refinement_after_user_review",
        ],
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_ending_specific_subset_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_ending_specific_subset_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_format_report(summary), encoding="utf-8")
    print({"ok": summary["acceptance"]["passed"], "summary_path": str(summary_path), "report_path": str(report_path), "outputs": outputs})
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    arrangement = arrangement_policy.get_arrangement_policy()
    expression = get_expression_policy()
    candidate_rows = _candidate_rows()
    return {
        "checkpoint_version": MILESTONE_ID,
        "ending_specific_policy_enabled": bool(arrangement.get("piano_comping_ending_specific_subset_policy")),
        "ending_specific_policy_version": str(arrangement.get("piano_comping_ending_specific_subset_policy_version")),
        "ending_specific_policy_contract": str(arrangement.get("piano_comping_ending_specific_subset_contract")),
        "arrangement_milestone": str(arrangement.get("milestone")),
        "required_prior_policy_versions": {key: arrangement.get(key) for key in REQUIRED_PRIOR_POLICY_KEYS},
        "missing_or_mismatched_prior_policy_versions": {
            key: {"expected": expected, "actual": arrangement.get(key)}
            for key, expected in REQUIRED_PRIOR_POLICY_KEYS.items()
            if arrangement.get(key) != expected
        },
        "expression_policy_version": str(expression.metadata.get("medium_swing_expression_policy_v1_numeric_calibration_version")),
        "pattern_candidate_count": len(candidate_rows),
        "pattern_forbidden_expression_candidates": [row for row in candidate_rows if row["forbidden_pattern_expression_keys"]],
        "pattern_forbidden_voicing_candidates": [row for row in candidate_rows if row["forbidden_pattern_voicing_keys"]],
        "bar_first_two_chord_bar_candidates": [row for row in candidate_rows if row["has_bar_first_two_chord_bar_marker"]],
    }


def _candidate_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for duration in (1.0, 2.0, 3.0, 4.0, 5.0):
        for candidate in comping_patterns.get_pattern_candidates({"region_duration_beats": duration}):
            forbidden_expression: set[str] = set()
            forbidden_voicing: set[str] = set()
            for event in candidate.events:
                event_metadata = dict(event.metadata)
                forbidden_expression.update(FORBIDDEN_PATTERN_EXPRESSION_KEYS & set(event_metadata))
                forbidden_voicing.update(FORBIDDEN_PATTERN_VOICING_KEYS & set(event_metadata))
            text_blob = " ".join([candidate.name, candidate.category, str(candidate.metadata), " ".join(candidate.tags)])
            rows.append(
                {
                    "name": candidate.name,
                    "duration_probe": duration,
                    "region_length_family": candidate.metadata.get("region_length_family"),
                    "forbidden_pattern_expression_keys": tuple(sorted(forbidden_expression)),
                    "forbidden_pattern_voicing_keys": tuple(sorted(forbidden_voicing)),
                    "has_bar_first_two_chord_bar_marker": "two_chord_bar" in text_blob or "split_bar" in text_blob,
                }
            )
    return rows


def _generate_and_audit(spec: Mapping[str, Any]) -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / str(spec["leadsheet"])).read_text(encoding="utf-8"))
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_medium_swing_ending_specific_subset_demo.mid"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": int(score.get("tempo", 132)),
            "choruses": 3,
            "seed": int(spec["seed"]),
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
        }
    )
    debug = dict(result.debug)
    piano_audit = build_piano_musical_audit(debug)
    pattern_rows = _piano_pattern_rows(debug)
    selected_rows = _selected_region_rows(pattern_rows)
    ending_rows = [row for row in selected_rows if row.get("ending_specific_policy_applied")]
    expression_rows = _expression_rows(debug)
    return {
        "ok": bool(result.ok),
        "title": score.get("title"),
        "slug": slug,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "written_bars": debug.get("written_bars"),
        "performance_choruses": debug.get("performance_choruses"),
        "performance_bars": debug.get("performance_bars"),
        "regions": debug.get("regions"),
        "note_events_by_track": debug.get("note_events_by_track"),
        "piano_pattern_events": len(pattern_rows),
        "selected_region_patterns": len(selected_rows),
        "ending_selected_region_patterns": len(ending_rows),
        "pattern_summary": _pattern_summary(pattern_rows),
        "ending_summary": _ending_summary(ending_rows),
        "history_summary": _history_summary(selected_rows),
        "expression_summary": _expression_summary(expression_rows, debug),
        "voicing_summary": {
            "top_note_max": piano_audit.summary.get("medium_swing_open_drop_top_note_max"),
            "top_note_ge_75_events": piano_audit.summary.get("medium_swing_open_drop_top_note_ge_75_events"),
            "voice_leading_warning_events": piano_audit.summary.get("medium_swing_open_drop_voice_leading_warning_events"),
            "register_guard_failed_events": piano_audit.summary.get("medium_swing_open_drop_register_guard_failed_events"),
            "method_counts": piano_audit.summary.get("medium_swing_open_drop_method_lock_calibration_method_counts"),
        },
    }


def _piano_pattern_rows(debug: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in debug.get("piano_musical_audit_events") or []:
        event = dict((raw or {}).get("pattern_event") or {})
        if event.get("track") != "piano":
            continue
        metadata = dict(event.get("metadata") or {})
        text_blob = " ".join([str(event.get("pattern_id") or ""), str(event.get("category") or ""), str(metadata)])
        rows.append(
            {
                "event_id": event.get("event_id"),
                "region_id": event.get("region_id"),
                "pattern_id": event.get("pattern_id"),
                "onset_beat": float(event.get("onset_beat") or 0.0),
                "local_beat": event.get("local_beat"),
                "chord_symbol": event.get("chord_symbol"),
                "region_length_family": metadata.get("region_length_family"),
                "rhythmic_cell": metadata.get("rhythmic_cell"),
                "weight_calibration_class": metadata.get("weight_calibration_class"),
                "history_activity_class": metadata.get("history_activity_class"),
                "history_candidate_is_busy": bool(metadata.get("history_candidate_is_busy")),
                "history_candidate_is_tail_push": bool(metadata.get("history_candidate_is_tail_push")),
                "history_policy_version": metadata.get("medium_swing_active_fill_busy_history_policy_version"),
                "expression_hint_handoff_version": metadata.get("expression_hint_handoff_policy_version"),
                "progression_subset_version": metadata.get("progression_specific_subset_policy_version"),
                "ending_specific_subset_version": metadata.get("ending_specific_subset_policy_version"),
                "ending_specific_policy_applied": bool(metadata.get("ending_specific_subset_policy_applied")),
                "ending_specific_context_label": metadata.get("ending_specific_context_label"),
                "ending_specific_subset_status": metadata.get("ending_specific_subset_status"),
                "ending_specific_subset_multiplier": metadata.get("ending_specific_subset_multiplier"),
                "ending_specific_subset_reasons": tuple(metadata.get("ending_specific_subset_reasons") or ()),
                "ending_specific_is_push": bool(metadata.get("ending_specific_is_push")),
                "ending_specific_is_active": bool(metadata.get("ending_specific_is_active")),
                "ending_specific_has_region_start": bool(metadata.get("ending_specific_has_region_start")),
                "no_4and_delayed_tail_version": metadata.get("no_4and_delayed_tail_policy_version"),
                "forbidden_pattern_expression_keys": tuple(sorted(FORBIDDEN_PATTERN_EXPRESSION_KEYS & set(metadata))),
                "forbidden_pattern_voicing_keys": tuple(sorted(FORBIDDEN_PATTERN_VOICING_KEYS & set(metadata))),
                "has_bar_first_two_chord_bar_marker": "two_chord_bar" in text_blob or "split_bar" in text_blob,
            }
        )
    return rows


def _selected_region_rows(pattern_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[tuple[Any, Any]] = set()
    for row in sorted(pattern_rows, key=lambda item: (float(item.get("onset_beat") or 0.0), str(item.get("event_id") or ""))):
        key = (row.get("region_id"), row.get("pattern_id"))
        if key in seen:
            continue
        seen.add(key)
        selected.append(row)
    return selected


def _expression_rows(debug: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in debug.get("expression_foundation_audit_events") or []:
        if raw.get("track") != "piano":
            continue
        metadata = dict(raw.get("metadata") or {})
        rows.append(
            {
                "event_id": raw.get("event_id"),
                "profile_name": raw.get("profile_name"),
                "calibration_version": metadata.get("medium_swing_expression_policy_v1_numeric_calibration_version"),
                "duration_next_touch_hold_version": metadata.get("duration_next_touch_hold_version"),
                "duration_next_touch_hold_reason": metadata.get("duration_next_touch_hold_reason"),
            }
        )
    return rows


def _pattern_summary(pattern_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "region_length_counts": dict(Counter(str(row.get("region_length_family")) for row in pattern_rows)),
        "rhythmic_cell_counts": dict(Counter(str(row.get("rhythmic_cell")) for row in pattern_rows)),
        "history_metadata_events": sum(1 for row in pattern_rows if row.get("history_policy_version") == "v2_6_67"),
        "ending_specific_metadata_events": sum(1 for row in pattern_rows if row.get("ending_specific_subset_version") == MILESTONE_ID),
        "ending_specific_applied_events": sum(1 for row in pattern_rows if row.get("ending_specific_policy_applied")),
        "expression_hint_handoff_events": sum(1 for row in pattern_rows if row.get("expression_hint_handoff_version") == "v2_6_63"),
        "progression_subset_events": sum(1 for row in pattern_rows if row.get("progression_subset_version") == "v2_6_65"),
        "no_4and_delayed_tail_policy_events": sum(1 for row in pattern_rows if row.get("no_4and_delayed_tail_version") == "v2_6_66"),
        "forbidden_expression_key_events": sum(1 for row in pattern_rows if row.get("forbidden_pattern_expression_keys")),
        "forbidden_voicing_key_events": sum(1 for row in pattern_rows if row.get("forbidden_pattern_voicing_keys")),
        "bar_first_two_chord_bar_events": sum(1 for row in pattern_rows if row.get("has_bar_first_two_chord_bar_marker")),
    }


def _ending_summary(ending_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "ending_selected_region_patterns": len(ending_rows),
        "status_counts": dict(Counter(str(row.get("ending_specific_subset_status")) for row in ending_rows)),
        "cell_counts": dict(Counter(str(row.get("rhythmic_cell")) for row in ending_rows)),
        "push_count": sum(1 for row in ending_rows if row.get("ending_specific_is_push")),
        "active_count": sum(1 for row in ending_rows if row.get("ending_specific_is_active")),
        "region_start_count": sum(1 for row in ending_rows if row.get("ending_specific_has_region_start")),
        "average_multiplier": round(sum(float(row.get("ending_specific_subset_multiplier") or 1.0) for row in ending_rows) / max(1, len(ending_rows)), 4),
    }


def _history_summary(selected_rows: list[dict[str, Any]]) -> dict[str, Any]:
    consecutive: Counter[str] = Counter()
    previous: dict[str, bool] | None = None
    for row in selected_rows:
        row_flags = {
            "busy": bool(row.get("history_candidate_is_busy")),
            "tail_push": bool(row.get("history_candidate_is_tail_push")),
        }
        if previous:
            for flag, value in row_flags.items():
                if value and previous[flag]:
                    consecutive[flag] += 1
        previous = row_flags
    return {"selected_region_patterns": len(selected_rows), "consecutive_flag_counts": dict(consecutive)}


def _expression_summary(expression_rows: list[dict[str, Any]], debug: Mapping[str, Any]) -> dict[str, Any]:
    expression_audit = dict(debug.get("expression_foundation_audit") or {})
    return {
        "piano_expression_events": len(expression_rows),
        "calibrated_expression_events": sum(1 for row in expression_rows if row.get("calibration_version") == "v2_6_68"),
        "profile_counts": dict(Counter(str(row.get("profile_name") or "missing") for row in expression_rows)),
        "hold_boundary_guard_events": sum(1 for row in expression_rows if row.get("duration_next_touch_hold_version") == "v2_6_66"),
        "cross_region_count": int(expression_audit.get("cross_region_count") or 0),
        "cross_next_event_count": int(expression_audit.get("cross_next_event_count") or 0),
        "warning_count": int(expression_audit.get("warning_count") or 0),
    }


def _acceptance(static_audit: Mapping[str, Any], outputs: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = [
        {"name": "static: arrangement declares v2_6_70 ending-specific subset policy", "passed": static_audit.get("ending_specific_policy_enabled") is True and static_audit.get("ending_specific_policy_version") == MILESTONE_ID},
        {"name": "static: all prior Medium Swing piano milestones still declared", "passed": len(static_audit.get("missing_or_mismatched_prior_policy_versions") or {}) == 0},
        {"name": "static: ExpressionPolicy remains v2_6_68 calibrated", "passed": static_audit.get("expression_policy_version") == "v2_6_68"},
        {"name": "static: no pattern candidate writes final expression values", "passed": len(static_audit.get("pattern_forbidden_expression_candidates") or []) == 0},
        {"name": "static: no pattern candidate writes voicing output", "passed": len(static_audit.get("pattern_forbidden_voicing_candidates") or []) == 0},
        {"name": "static: no bar-first/two-chord-bar markers remain", "passed": len(static_audit.get("bar_first_two_chord_bar_candidates") or []) == 0},
    ]
    for output in outputs:
        pattern = dict(output.get("pattern_summary") or {})
        ending = dict(output.get("ending_summary") or {})
        history = dict(output.get("history_summary") or {})
        expression = dict(output.get("expression_summary") or {})
        voicing = dict(output.get("voicing_summary") or {})
        checks.extend(
            [
                {"name": f"{output['slug']}: generation ok", "passed": bool(output.get("ok"))},
                {"name": f"{output['slug']}: three-chorus listening loop", "passed": output.get("performance_choruses") == 3},
                {"name": f"{output['slug']}: piano comping events present", "passed": output.get("piano_pattern_events", 0) >= 100},
                {"name": f"{output['slug']}: v2_6_70 metadata reaches runtime piano events", "passed": pattern.get("ending_specific_metadata_events") == output.get("piano_pattern_events")},
                {"name": f"{output['slug']}: ending policy applies to at least final regions", "passed": ending.get("ending_selected_region_patterns", 0) >= int(output.get("performance_choruses") or 0)},
                {"name": f"{output['slug']}: ending push selected count remains controlled", "passed": ending.get("push_count", 0) == 0},
                {"name": f"{output['slug']}: v2_6_67 history metadata still covers piano events", "passed": pattern.get("history_metadata_events") == output.get("piano_pattern_events")},
                {"name": f"{output['slug']}: v2_6_68 calibrated expression covers piano events", "passed": expression.get("calibrated_expression_events") == expression.get("piano_expression_events")},
                {"name": f"{output['slug']}: no expression cross-region sustain", "passed": expression.get("cross_region_count") == 0},
                {"name": f"{output['slug']}: no pattern events contain concrete expression values", "passed": pattern.get("forbidden_expression_key_events") == 0},
                {"name": f"{output['slug']}: no pattern events contain voicing output", "passed": pattern.get("forbidden_voicing_key_events") == 0},
                {"name": f"{output['slug']}: no bar-first two_chord_bar runtime events", "passed": pattern.get("bar_first_two_chord_bar_events") == 0},
                {"name": f"{output['slug']}: busy does not repeat", "passed": int((history.get("consecutive_flag_counts") or {}).get("busy") or 0) == 0},
                {"name": f"{output['slug']}: tail-push does not repeat", "passed": int((history.get("consecutive_flag_counts") or {}).get("tail_push") or 0) == 0},
                {"name": f"{output['slug']}: top register calm", "passed": (voicing.get("top_note_ge_75_events") or 0) == 0},
                {"name": f"{output['slug']}: voice-leading warnings calm", "passed": (voicing.get("voice_leading_warning_events") or 0) == 0},
            ]
        )
    return {"passed": all(check["passed"] for check in checks), "checks": checks}


def _format_report(summary: Mapping[str, Any]) -> str:
    lines = [
        f"# {summary['milestone']}",
        "",
        f"Contract version: `{summary['contract_version']}`",
        "",
        str(summary["scope"]),
        "",
        f"Acceptance Passed: `{summary['acceptance']['passed']}`",
        "",
        "## Static audit",
        "",
        f"- Ending policy version: `{summary['static_audit']['ending_specific_policy_version']}`",
        f"- Missing prior policy versions: `{len(summary['static_audit']['missing_or_mismatched_prior_policy_versions'])}`",
        f"- Pattern candidates: `{summary['static_audit']['pattern_candidate_count']}`",
        f"- Forbidden expression candidates: `{len(summary['static_audit']['pattern_forbidden_expression_candidates'])}`",
        f"- Forbidden voicing candidates: `{len(summary['static_audit']['pattern_forbidden_voicing_candidates'])}`",
        f"- Bar-first/two-chord-bar candidates: `{len(summary['static_audit']['bar_first_two_chord_bar_candidates'])}`",
        "",
        "## Listening outputs",
    ]
    for output in summary["outputs"]:
        pattern = output["pattern_summary"]
        ending = output["ending_summary"]
        expression = output["expression_summary"]
        voicing = output["voicing_summary"]
        lines.extend(
            [
                "",
                f"### {output['title']} / `{output['slug']}`",
                "",
                f"- MIDI: `{output['midi_path']}`",
                f"- Choruses: `{output['performance_choruses']}`; regions: `{output['regions']}`; piano pattern events: `{output['piano_pattern_events']}`",
                f"- Pattern region lengths: `{pattern['region_length_counts']}`",
                f"- Ending selected region patterns: `{ending['ending_selected_region_patterns']}`",
                f"- Ending status counts: `{ending['status_counts']}`",
                f"- Ending cell counts: `{ending['cell_counts']}`",
                f"- Ending push / active / region-start counts: `{ending['push_count']}` / `{ending['active_count']}` / `{ending['region_start_count']}`",
                f"- Calibrated expression events: `{expression['calibrated_expression_events']}/{expression['piano_expression_events']}`",
                f"- Expression cross-region: `{expression['cross_region_count']}`; cross-next warning signal: `{expression['cross_next_event_count']}`",
                f"- Top note max: `{voicing['top_note_max']}`; voice-leading warnings: `{voicing['voice_leading_warning_events']}`",
                f"- Open-drop method counts: `{voicing['method_counts']}`",
            ]
        )
    lines.extend(["", "## Acceptance checks", ""])
    for check in summary["acceptance"]["checks"]:
        marker = "PASS" if check["passed"] else "FAIL"
        lines.append(f"- `{marker}` — {check['name']}")
    lines.extend(["", "## Recommended next tasks", ""])
    for task in summary.get("recommended_next_tasks") or []:
        lines.append(f"- `{task}`")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
