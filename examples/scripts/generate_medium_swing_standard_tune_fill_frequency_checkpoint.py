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

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_74"
MILESTONE_LABEL = "v2_6_74 — Medium Swing Standard-Tune Fill Frequency Checkpoint"
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
REQUIRED_POLICY_KEYS = {
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
    "piano_comping_ending_specific_subset_policy_version": "v2_6_70",
    "piano_comping_optional_fill_variation_vocabulary_policy_version": "v2_6_71",
    "piano_comping_optional_fill_variation_listening_refinement_policy_version": "v2_6_72",
    "piano_comping_phrase_end_fill_context_precision_policy_version": "v2_6_73",
    "piano_comping_standard_tune_fill_frequency_checkpoint_version": "v2_6_74",
}

SPECS: tuple[dict[str, Any], ...] = (
    {"slug": "all_the_things_you_are", "leadsheet": "all_the_things_you_are.json", "seed": 3710},
    {"slug": "autumn_leaves", "leadsheet": "autumn_leaves.json", "seed": 3711},
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    outputs = [_generate_and_audit(spec) for spec in SPECS]
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": (
            "Behavior-preserving Medium Swing standard-tune fill frequency checkpoint. "
            "v2_6_74 measures how often the v2_6_71 optional variation/fill vocabulary is actually selected "
            "after v2_6_72 listening refinement and v2_6_73 phrase-end precision, while checking continuity, "
            "pattern/expression/voicing boundaries, and standard-tune 3-chorus demo safety. No candidate weight, "
            "vocabulary, fill selector, voicing, expression numeric, API, Agent, or HarmonyOS behavior is changed."
        ),
        "static_audit": static_audit,
        "outputs": outputs,
        "aggregate_frequency_summary": _aggregate_frequency_summary(outputs),
        "acceptance": _acceptance(static_audit, outputs),
        "recommended_next_tasks": [
            "v2_6_75_engine_medium_swing_optional_fill_density_macro_gate_only_if_frequency_rises",
            "v2_6_76_engine_medium_swing_piano_comping_checkpoint_or_return_to_voicing_line",
        ],
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_standard_tune_fill_frequency_checkpoint_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_standard_tune_fill_frequency_checkpoint_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": summary["acceptance"]}, indent=2, ensure_ascii=False))


def build_static_audit() -> dict[str, Any]:
    policy = arrangement_policy.get_arrangement_policy()
    candidate_rows = _candidate_rows()
    optional_rows = [row for row in candidate_rows if row["optional_candidate"]]
    unique_optional = {str(row["name"]): row for row in optional_rows}
    return {
        "checkpoint_version": MILESTONE_ID,
        "checkpoint_policy_enabled": bool(policy.get("piano_comping_standard_tune_fill_frequency_checkpoint")),
        "checkpoint_policy_version": str(policy.get("piano_comping_standard_tune_fill_frequency_checkpoint_version")),
        "checkpoint_policy_contract": str(policy.get("piano_comping_standard_tune_fill_frequency_checkpoint_contract")),
        "phrase_end_precision_policy_version": str(policy.get("piano_comping_phrase_end_fill_context_precision_policy_version")),
        "optional_policy_version": str(policy.get("piano_comping_optional_fill_variation_vocabulary_policy_version")),
        "optional_refinement_policy_version": str(policy.get("piano_comping_optional_fill_variation_listening_refinement_policy_version")),
        "required_policy_versions": {key: policy.get(key) for key in REQUIRED_POLICY_KEYS},
        "missing_or_mismatched_policy_versions": {
            key: {"expected": expected, "actual": policy.get(key)}
            for key, expected in REQUIRED_POLICY_KEYS.items()
            if policy.get(key) != expected
        },
        "pattern_candidate_count": len(candidate_rows),
        "optional_candidate_count": len(unique_optional),
        "optional_candidate_names": sorted(unique_optional),
        "optional_candidate_roles": dict(Counter(str(row["optional_role"]) for row in unique_optional.values())),
        "optional_candidate_weights": {name: row["weight"] for name, row in unique_optional.items()},
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
                    "optional_candidate": bool(candidate.metadata.get("optional_fill_variation_vocabulary_candidate")),
                    "optional_version": candidate.metadata.get("optional_fill_variation_vocabulary_version"),
                    "optional_role": candidate.metadata.get("optional_fill_variation_role"),
                    "weight": candidate.weight,
                    "forbidden_pattern_expression_keys": tuple(sorted(forbidden_expression | (FORBIDDEN_PATTERN_EXPRESSION_KEYS & set(candidate.metadata)))),
                    "forbidden_pattern_voicing_keys": tuple(sorted(forbidden_voicing | (FORBIDDEN_PATTERN_VOICING_KEYS & set(candidate.metadata)))),
                    "has_bar_first_two_chord_bar_marker": "two_chord_bar" in text_blob or "split_bar" in text_blob,
                }
            )
    return rows


def _generate_and_audit(spec: Mapping[str, Any]) -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / str(spec["leadsheet"])).read_text(encoding="utf-8"))
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_medium_swing_standard_tune_fill_frequency_checkpoint_demo.mid"
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
    optional_selected = [row for row in selected_rows if row.get("optional_fill_variation_candidate")]
    transition_fill_selected = [row for row in optional_selected if row.get("optional_fill_variation_role_runtime") == "transition_fill"]
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
        "optional_selected_region_patterns": len(optional_selected),
        "optional_selected_ratio": round(len(optional_selected) / max(1, len(selected_rows)), 4),
        "transition_fill_selected_region_patterns": len(transition_fill_selected),
        "transition_fill_phrase_end_hit_count": sum(1 for row in transition_fill_selected if row.get("optional_fill_variation_phrase_end_context")),
        "optional_summary": _optional_summary(optional_selected),
        "history_summary": _history_summary(selected_rows),
        "pattern_summary": _pattern_summary(pattern_rows),
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
                "history_candidate_is_active": bool(metadata.get("history_candidate_is_active")),
                "history_candidate_is_fill": bool(metadata.get("history_candidate_is_fill")),
                "history_candidate_is_busy": bool(metadata.get("history_candidate_is_busy")),
                "history_candidate_is_tail_push": bool(metadata.get("history_candidate_is_tail_push")),
                "history_policy_version": metadata.get("medium_swing_active_fill_busy_history_policy_version"),
                "optional_fill_variation_policy_version": metadata.get("optional_fill_variation_policy_version"),
                "optional_fill_variation_listening_refinement_policy_version": metadata.get("optional_fill_variation_listening_refinement_policy_version"),
                "phrase_end_precision_policy_version": metadata.get("phrase_end_fill_context_precision_policy_version"),
                "fill_frequency_checkpoint_version": metadata.get("standard_tune_fill_frequency_checkpoint_version"),
                "fill_frequency_checkpoint_applied": bool(metadata.get("standard_tune_fill_frequency_checkpoint_applied")),
                "fill_frequency_checkpoint_scope": metadata.get("standard_tune_fill_frequency_checkpoint_scope"),
                "optional_fill_variation_phrase_end_context": bool(metadata.get("optional_fill_variation_phrase_end_context")),
                "optional_fill_variation_precise_transition_fill_context": bool(metadata.get("optional_fill_variation_precise_transition_fill_context")),
                "optional_fill_variation_harmonic_transition_context": bool(metadata.get("optional_fill_variation_harmonic_transition_context")),
                "optional_fill_variation_phrase_precision_status": metadata.get("optional_fill_variation_phrase_precision_status"),
                "optional_fill_variation_candidate": bool(metadata.get("optional_fill_variation_candidate")),
                "optional_fill_variation_role_runtime": metadata.get("optional_fill_variation_role_runtime"),
                "optional_fill_variation_status": metadata.get("optional_fill_variation_status"),
                "optional_fill_variation_context_label": metadata.get("optional_fill_variation_context_label"),
                "optional_fill_variation_multiplier": metadata.get("optional_fill_variation_multiplier"),
                "optional_fill_variation_reasons": tuple(metadata.get("optional_fill_variation_reasons") or ()),
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
        "optional_metadata_events": sum(1 for row in pattern_rows if row.get("optional_fill_variation_policy_version") == "v2_6_71"),
        "optional_refinement_metadata_events": sum(1 for row in pattern_rows if row.get("optional_fill_variation_listening_refinement_policy_version") == "v2_6_72"),
        "phrase_end_precision_metadata_events": sum(1 for row in pattern_rows if row.get("phrase_end_precision_policy_version") == "v2_6_73"),
        "fill_frequency_checkpoint_metadata_events": sum(1 for row in pattern_rows if row.get("fill_frequency_checkpoint_version") == MILESTONE_ID),
        "forbidden_pattern_expression_events": sum(1 for row in pattern_rows if row["forbidden_pattern_expression_keys"]),
        "forbidden_pattern_voicing_events": sum(1 for row in pattern_rows if row["forbidden_pattern_voicing_keys"]),
        "bar_first_marker_events": sum(1 for row in pattern_rows if row["has_bar_first_two_chord_bar_marker"]),
    }


def _optional_summary(optional_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "selected_count": len(optional_rows),
        "phrase_end_context_count": sum(1 for row in optional_rows if row.get("optional_fill_variation_phrase_end_context")),
        "precise_transition_fill_context_count": sum(1 for row in optional_rows if row.get("optional_fill_variation_precise_transition_fill_context")),
        "phrase_precision_status_counts": dict(Counter(str(row.get("optional_fill_variation_phrase_precision_status")) for row in optional_rows)),
        "status_counts": dict(Counter(str(row.get("optional_fill_variation_status")) for row in optional_rows)),
        "role_counts": dict(Counter(str(row.get("optional_fill_variation_role_runtime")) for row in optional_rows)),
        "context_counts": dict(Counter(str(row.get("optional_fill_variation_context_label")) for row in optional_rows)),
        "selected_rows": optional_rows[:12],
    }


def _history_summary(selected_rows: list[dict[str, Any]]) -> dict[str, Any]:
    classes = [str(row.get("history_activity_class") or row.get("weight_calibration_class")) for row in selected_rows]
    active_flags = [bool(row.get("history_candidate_is_active")) for row in selected_rows]
    fill_flags = [bool(row.get("history_candidate_is_fill")) for row in selected_rows]
    busy_flags = [bool(row.get("history_candidate_is_busy")) for row in selected_rows]
    tail_push_flags = [bool(row.get("history_candidate_is_tail_push")) for row in selected_rows]
    return {
        "activity_class_counts": dict(Counter(classes)),
        "consecutive_active_count": _consecutive_bool_count(active_flags),
        "consecutive_busy_count": _consecutive_bool_count(busy_flags),
        "consecutive_fill_count": _consecutive_bool_count(fill_flags),
        "consecutive_tail_push_count": _consecutive_bool_count(tail_push_flags),
    }


def _expression_summary(rows: list[dict[str, Any]], debug: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "piano_expression_events": len(rows),
        "calibrated_events": sum(1 for row in rows if row.get("calibration_version") == "v2_6_68"),
        "cross_region_hold_guard_events": debug.get("hold_cross_region_boundary_guard_events", 0),
    }


def _consecutive_bool_count(values: list[bool]) -> int:
    return sum(1 for prev, cur in zip(values, values[1:]) if prev and cur)


def _aggregate_frequency_summary(outputs: list[Mapping[str, Any]]) -> dict[str, Any]:
    selected_total = sum(int(output.get("selected_region_patterns") or 0) for output in outputs)
    optional_total = sum(int(output.get("optional_selected_region_patterns") or 0) for output in outputs)
    transition_fill_total = sum(int(output.get("transition_fill_selected_region_patterns") or 0) for output in outputs)
    transition_fill_phrase_hits = sum(int(output.get("transition_fill_phrase_end_hit_count") or 0) for output in outputs)
    ratio = optional_total / max(1, selected_total)
    return {
        "standard_tune_count": len(outputs),
        "selected_region_patterns_total": selected_total,
        "optional_selected_total": optional_total,
        "optional_selected_ratio": round(ratio, 4),
        "transition_fill_selected_total": transition_fill_total,
        "transition_fill_phrase_end_hit_count": transition_fill_phrase_hits,
        "frequency_band": _frequency_band(ratio),
        "macro_density_gate_needed_now": ratio > 0.06 or any(output.get("history_summary", {}).get("consecutive_fill_count", 0) > 0 for output in outputs),
    }


def _frequency_band(ratio: float) -> str:
    if ratio <= 0.02:
        return "very_low_intrusion"
    if ratio <= 0.05:
        return "controlled_low_frequency"
    if ratio <= 0.08:
        return "watch_density"
    return "needs_macro_density_gate"


def _acceptance(static: Mapping[str, Any], outputs: list[Mapping[str, Any]]) -> dict[str, Any]:
    checks: dict[str, bool] = {
        "static_checkpoint_policy_enabled": static.get("checkpoint_policy_enabled") is True,
        "static_checkpoint_policy_version": static.get("checkpoint_policy_version") == MILESTONE_ID,
        "static_optional_policy_version": static.get("optional_policy_version") == "v2_6_71",
        "static_optional_refinement_policy_version": static.get("optional_refinement_policy_version") == "v2_6_72",
        "static_phrase_end_precision_policy_version": static.get("phrase_end_precision_policy_version") == "v2_6_73",
        "optional_candidate_count_is_small": static.get("optional_candidate_count") == 3,
        "prior_versions_match": not static.get("missing_or_mismatched_policy_versions"),
        "no_pattern_expression_leakage": not static.get("pattern_forbidden_expression_candidates"),
        "no_pattern_voicing_leakage": not static.get("pattern_forbidden_voicing_candidates"),
        "no_bar_first_markers": not static.get("bar_first_two_chord_bar_candidates"),
    }
    if outputs:
        aggregate = _aggregate_frequency_summary(outputs)
        checks.update(
            {
                "all_outputs_ok": all(bool(output.get("ok")) for output in outputs),
                "fill_frequency_checkpoint_metadata_present": all(output.get("pattern_summary", {}).get("fill_frequency_checkpoint_metadata_events", 0) > 0 for output in outputs),
                "optional_metadata_present": all(output.get("pattern_summary", {}).get("optional_metadata_events", 0) > 0 for output in outputs),
                "phrase_end_precision_metadata_present": all(output.get("pattern_summary", {}).get("phrase_end_precision_metadata_events", 0) > 0 for output in outputs),
                "history_metadata_present": all(output.get("pattern_summary", {}).get("history_metadata_events", 0) > 0 for output in outputs),
                "optional_frequency_stays_low": aggregate.get("optional_selected_ratio", 1.0) <= 0.05,
                "no_consecutive_active": all(output.get("history_summary", {}).get("consecutive_active_count", 0) == 0 for output in outputs),
                "no_consecutive_fill": all(output.get("history_summary", {}).get("consecutive_fill_count", 0) == 0 for output in outputs),
                "no_consecutive_busy": all(output.get("history_summary", {}).get("consecutive_busy_count", 0) == 0 for output in outputs),
                "no_consecutive_tail_push": all(output.get("history_summary", {}).get("consecutive_tail_push_count", 0) == 0 for output in outputs),
                "no_runtime_pattern_expression_leakage": all(output.get("pattern_summary", {}).get("forbidden_pattern_expression_events", 0) == 0 for output in outputs),
                "no_runtime_pattern_voicing_leakage": all(output.get("pattern_summary", {}).get("forbidden_pattern_voicing_events", 0) == 0 for output in outputs),
                "no_runtime_bar_first_markers": all(output.get("pattern_summary", {}).get("bar_first_marker_events", 0) == 0 for output in outputs),
                "voice_leading_safe": all(output.get("voicing_summary", {}).get("voice_leading_warning_events", 0) == 0 for output in outputs),
                "top_register_safe": all((output.get("voicing_summary", {}).get("top_note_max") or 0) <= 76 for output in outputs),
            }
        )
    return {"passed": all(checks.values()), "checks": checks}


def _render_report(summary: Mapping[str, Any]) -> str:
    lines = [f"# {summary['milestone']}", "", f"Contract version: `{summary['contract_version']}`", "", summary["scope"], ""]
    lines.append(f"Acceptance Passed: **{summary['acceptance']['passed']}**")
    lines.append("")
    static = summary["static_audit"]
    lines.append("## Static Audit")
    lines.append(f"- Checkpoint policy: `{static['checkpoint_policy_version']}` enabled={static['checkpoint_policy_enabled']}")
    lines.append(f"- Optional vocabulary/refinement/precision: `{static['optional_policy_version']}` / `{static['optional_refinement_policy_version']}` / `{static['phrase_end_precision_policy_version']}`")
    lines.append(f"- Optional candidate count: `{static['optional_candidate_count']}`")
    lines.append(f"- Optional roles: `{static['optional_candidate_roles']}`")
    lines.append(f"- Optional weights: `{static['optional_candidate_weights']}`")
    lines.append(f"- Policy mismatches: `{static['missing_or_mismatched_policy_versions']}`")
    lines.append(f"- Pattern expression leakage candidates: `{len(static['pattern_forbidden_expression_candidates'])}`")
    lines.append(f"- Pattern voicing leakage candidates: `{len(static['pattern_forbidden_voicing_candidates'])}`")
    lines.append(f"- Bar-first/two_chord_bar markers: `{len(static['bar_first_two_chord_bar_candidates'])}`")
    lines.append("")
    aggregate = summary["aggregate_frequency_summary"]
    lines.append("## Aggregate Fill Frequency")
    lines.append(f"- Selected region patterns total: `{aggregate['selected_region_patterns_total']}`")
    lines.append(f"- Optional selected total: `{aggregate['optional_selected_total']}`")
    lines.append(f"- Optional selected ratio: `{aggregate['optional_selected_ratio']}`")
    lines.append(f"- Frequency band: `{aggregate['frequency_band']}`")
    lines.append(f"- Transition fill selected total: `{aggregate['transition_fill_selected_total']}`")
    lines.append(f"- Macro density gate needed now: `{aggregate['macro_density_gate_needed_now']}`")
    lines.append("")
    lines.append("## Demo Outputs")
    for output in summary["outputs"]:
        lines.append(f"### {output['title']}")
        lines.append(f"- MIDI: `{output['midi_path']}`")
        lines.append(f"- Piano pattern events: `{output['piano_pattern_events']}`")
        lines.append(f"- Selected region patterns: `{output['selected_region_patterns']}`")
        lines.append(f"- Optional selected region patterns: `{output['optional_selected_region_patterns']}`")
        lines.append(f"- Optional selected ratio: `{output['optional_selected_ratio']}`")
        lines.append(f"- Optional role counts: `{output['optional_summary']['role_counts']}`")
        lines.append(f"- Optional status counts: `{output['optional_summary']['status_counts']}`")
        lines.append(f"- Phrase precision status counts: `{output['optional_summary']['phrase_precision_status_counts']}`")
        lines.append(f"- History summary: `{output['history_summary']}`")
        lines.append(f"- Voicing summary: `{output['voicing_summary']}`")
        lines.append("")
    lines.append("## Recommended Next Tasks")
    for item in summary["recommended_next_tasks"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
