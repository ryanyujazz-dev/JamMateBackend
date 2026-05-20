from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

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
MILESTONE_ID = "v2_6_67"
MILESTONE_LABEL = "v2_6_67 — Medium Swing Active/Fill/Busy Multi-Region History Scorer"

SPECS: tuple[dict[str, Any], ...] = (
    {"slug": "all_the_things_you_are", "leadsheet": "all_the_things_you_are.json", "seed": 3600},
    {"slug": "autumn_leaves", "leadsheet": "autumn_leaves.json", "seed": 3601},
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    outputs = [_generate_and_audit(spec) for spec in SPECS]
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": "v2_6_67 upgrades the existing Medium Swing piano history scorer in-place with multi-region active/fill/busy/push/tail-push memory. It remains ChordRegion-first and does not write voicing, final expression values, MIDI pitch, duration, velocity, or pedal into the pattern layer.",
        "static_audit": static_audit,
        "outputs": outputs,
        "acceptance": _acceptance(static_audit, outputs),
        "recommended_next_tasks": [
            "v2_6_68_engine_medium_swing_expression_policy_v1_numeric_calibration",
            "v2_6_69_engine_medium_swing_piano_standard_tune_listening_checkpoint",
        ],
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_piano_active_fill_busy_history_audit_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_piano_active_fill_busy_history_audit_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_format_report(summary), encoding="utf-8")
    print({"ok": summary["acceptance"]["passed"], "summary_path": str(summary_path), "report_path": str(report_path), "outputs": outputs})
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    policy = arrangement_policy.get_arrangement_policy()
    rows = _candidate_rows()
    active_rows = [row for row in rows if row["weight"] > 0]
    return {
        "checkpoint_version": MILESTONE_ID,
        "pattern_library_version": comping_patterns.PATTERN_LIBRARY_VERSION,
        "candidate_lookup_policy_version": comping_patterns.CANDIDATE_LOOKUP_POLICY_VERSION,
        "weight_calibration_policy_version": comping_patterns.WEIGHT_CALIBRATION_POLICY_VERSION,
        "history_continuity_scorer_version": str(policy.get("piano_comping_history_continuity_scorer_version")),
        "active_fill_busy_history_enabled": bool(policy.get("piano_comping_active_fill_busy_multi_region_history_scorer")),
        "active_fill_busy_history_version": str(policy.get("piano_comping_active_fill_busy_multi_region_history_scorer_version")),
        "active_fill_busy_history_contract": str(policy.get("piano_comping_active_fill_busy_multi_region_history_contract")),
        "candidate_count_total": len(rows),
        "candidate_count_active": len(active_rows),
        "active_by_region_length_family": dict(_counter_by(active_rows, "region_length_family")),
        "active_by_weight_calibration_class": dict(_counter_by(active_rows, "weight_calibration_class")),
        "active_by_rhythm_family": dict(_counter_by(active_rows, "rhythm_family")),
        "forbidden_pattern_expression_key_candidates": [row for row in rows if row["forbidden_pattern_expression_keys"]],
        "bar_first_two_chord_bar_candidates": [row for row in rows if row["has_bar_first_two_chord_bar_marker"]],
    }


def _candidate_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for duration in (1.0, 2.0, 3.0, 4.0, 5.0):
        for candidate in comping_patterns.get_pattern_candidates({"region_duration_beats": duration}):
            metadata = dict(candidate.metadata)
            forbidden: list[str] = []
            for event in candidate.events:
                event_metadata = dict(event.metadata)
                forbidden.extend([key for key in ("velocity", "duration", "duration_beats", "pedal", "midi_note") if key in event_metadata])
            text_blob = " ".join([candidate.name, candidate.category, str(metadata), " ".join(candidate.tags)])
            rows.append(
                {
                    "name": candidate.name,
                    "duration_probe": duration,
                    "weight": float(candidate.weight),
                    "category": candidate.category,
                    "region_length_family": str(metadata.get("region_length_family") or "missing"),
                    "rhythmic_cell": str(metadata.get("rhythmic_cell") or "missing"),
                    "rhythm_family": str(metadata.get("rhythm_family") or "missing"),
                    "weight_calibration_class": str(metadata.get("weight_calibration_class") or "missing"),
                    "tail_push_risk": str(metadata.get("tail_push_risk") or "none"),
                    "no_4and_delayed_tail_idiom": bool(metadata.get("no_4and_delayed_tail_idiom", False)),
                    "forbidden_pattern_expression_keys": tuple(sorted(set(forbidden))),
                    "has_bar_first_two_chord_bar_marker": "two_chord_bar" in text_blob or "split_bar" in text_blob,
                    "is_region_first": metadata.get("candidate_lookup_policy") == "region_length_aware" and metadata.get("time_reference") == "region_local_beats",
                }
            )
    return rows


def _generate_and_audit(spec: Mapping[str, Any]) -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / str(spec["leadsheet"])).read_text(encoding="utf-8"))
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_medium_swing_active_fill_busy_history_demo.mid"
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
    piano_audit = build_piano_musical_audit(result.debug)
    rows = _piano_rows(result.debug)
    reason_counter: Counter[str] = Counter()
    for row in rows:
        for reason in row.get("history_continuity_reasons") or ():
            reason_counter[str(reason)] += 1
    class_counts = Counter(str(row.get("history_continuity_class") or "missing") for row in rows)
    return {
        "ok": bool(result.ok),
        "title": score.get("title"),
        "slug": slug,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "piano_events": len(rows),
        "history_policy_events": sum(1 for row in rows if row.get("active_fill_busy_multi_region_history_policy_version") == MILESTONE_ID),
        "history_class_counts": dict(class_counts),
        "history_reason_counts": dict(reason_counter),
        "active_events": sum(1 for row in rows if row.get("history_candidate_is_active")),
        "fill_like_events": sum(1 for row in rows if row.get("history_candidate_is_fill")),
        "busy_events": sum(1 for row in rows if row.get("history_candidate_is_busy")),
        "push_events": sum(1 for row in rows if row.get("history_candidate_is_push")),
        "tail_push_events": sum(1 for row in rows if row.get("history_candidate_is_tail_push")),
        "history_penalty_events": sum(1 for row in rows if float(row.get("history_continuity_multiplier") or 1.0) < 1.0),
        "history_bonus_events": sum(1 for row in rows if float(row.get("history_continuity_multiplier") or 1.0) > 1.0),
        "stable_reset_after_active_count": reason_counter.get("stable_reset_after_active_bonus", 0),
        "stable_reset_after_fill_count": reason_counter.get("stable_reset_after_fill_bonus", 0),
        "stable_reset_after_busy_count": reason_counter.get("stable_reset_after_busy_bonus", 0),
        "no_4and_after_push_bonus_count": reason_counter.get("no_4and_delayed_tail_after_recent_push_bonus", 0),
        "active_after_active_penalty_count": reason_counter.get("active_after_active_medium_penalty", 0),
        "busy_near_block_count": reason_counter.get("busy_after_busy_near_block", 0) + reason_counter.get("recent_busy_near_block", 0),
        "tail_push_cluster_penalty_count": reason_counter.get("recent_tail_push_penalty", 0),
        "pattern_forbidden_expression_key_events": sum(1 for row in rows if row.get("pattern_forbidden_expression_keys")),
        "bar_first_two_chord_bar_events": sum(1 for row in rows if row.get("has_bar_first_two_chord_bar_marker")),
        "top_note_max": piano_audit.summary.get("medium_swing_open_drop_top_note_max"),
        "top_note_ge_75_events": piano_audit.summary.get("medium_swing_open_drop_top_note_ge_75_events"),
        "voice_leading_warning_events": piano_audit.summary.get("medium_swing_open_drop_voice_leading_warning_events"),
    }


def _piano_rows(debug: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in debug.get("piano_musical_audit_events") or []:
        event = dict((raw or {}).get("pattern_event") or {})
        if event.get("track") != "piano":
            continue
        pattern_metadata = dict(event.get("metadata") or {})
        text_blob = " ".join([str(event.get("pattern_id") or ""), str(event.get("category") or ""), str(pattern_metadata)])
        forbidden = [key for key in {"velocity", "duration", "duration_beats", "pedal", "midi_note"} if key in pattern_metadata]
        rows.append(
            {
                "event_id": event.get("event_id"),
                "pattern_id": event.get("pattern_id"),
                "onset_beat": event.get("onset_beat"),
                "region_length_family": pattern_metadata.get("region_length_family") or pattern_metadata.get("coverage_region_length_family"),
                "rhythm_family": pattern_metadata.get("rhythm_family"),
                "history_continuity_class": pattern_metadata.get("history_continuity_class"),
                "history_continuity_reasons": tuple(pattern_metadata.get("history_continuity_reasons") or ()),
                "history_continuity_multiplier": pattern_metadata.get("history_continuity_multiplier"),
                "active_fill_busy_multi_region_history_policy_version": pattern_metadata.get("active_fill_busy_multi_region_history_policy_version"),
                "history_candidate_is_active": bool(pattern_metadata.get("history_candidate_is_active")),
                "history_candidate_is_fill": bool(pattern_metadata.get("history_candidate_is_fill")),
                "history_candidate_is_busy": bool(pattern_metadata.get("history_candidate_is_busy")),
                "history_candidate_is_push": bool(pattern_metadata.get("history_candidate_is_push")),
                "history_candidate_is_tail_push": bool(pattern_metadata.get("history_candidate_is_tail_push")),
                "pattern_forbidden_expression_keys": tuple(forbidden),
                "has_bar_first_two_chord_bar_marker": "two_chord_bar" in text_blob or "split_bar" in text_blob,
            }
        )
    return sorted(rows, key=lambda row: (float(row.get("onset_beat") or 0.0), str(row.get("event_id"))))


def _counter_by(rows: Iterable[Mapping[str, Any]], key: str) -> Counter:
    return Counter(str(row.get(key) or "missing") for row in rows)


def _acceptance(static_audit: Mapping[str, Any], outputs: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = [
        {"name": "static: active/fill/busy history policy enabled", "passed": bool(static_audit.get("active_fill_busy_history_enabled"))},
        {"name": "static: active/fill/busy history policy version", "passed": static_audit.get("active_fill_busy_history_version") == MILESTONE_ID},
        {"name": "static: no pattern candidate writes final expression values", "passed": len(static_audit.get("forbidden_pattern_expression_key_candidates") or []) == 0},
        {"name": "static: no bar-first/two-chord-bar markers remain", "passed": len(static_audit.get("bar_first_two_chord_bar_candidates") or []) == 0},
    ]
    for output in outputs:
        checks.extend(
            [
                {"name": f"{output['slug']}: generation ok", "passed": bool(output.get("ok"))},
                {"name": f"{output['slug']}: v2_6_67 metadata present", "passed": output.get("history_policy_events", 0) > 0},
                {"name": f"{output['slug']}: history penalties present", "passed": output.get("history_penalty_events", 0) > 0},
                {"name": f"{output['slug']}: no pattern events contain concrete expression values", "passed": output.get("pattern_forbidden_expression_key_events") == 0},
                {"name": f"{output['slug']}: no bar-first two_chord_bar runtime events", "passed": output.get("bar_first_two_chord_bar_events") == 0},
                {"name": f"{output['slug']}: top register calm", "passed": (output.get("top_note_ge_75_events") or 0) == 0},
                {"name": f"{output['slug']}: voice-leading warnings calm", "passed": (output.get("voice_leading_warning_events") or 0) == 0},
            ]
        )
    return {"passed": all(check["passed"] for check in checks), "checks": checks}


def _format_report(summary: Mapping[str, Any]) -> str:
    lines = [f"# {summary['milestone']}", "", str(summary.get("scope", "")), ""]
    static = summary["static_audit"]
    lines.extend(
        [
            "## Static V2 policy audit",
            "",
            f"- Pattern / lookup / weight versions: `{static['pattern_library_version']}` / `{static['candidate_lookup_policy_version']}` / `{static['weight_calibration_policy_version']}`",
            f"- History scorer compatibility/new version: `{static['history_continuity_scorer_version']}` / `{static['active_fill_busy_history_version']}`",
            f"- Candidate counts total/active: `{static['candidate_count_total']}` / `{static['candidate_count_active']}`",
            f"- Active by region length: `{static['active_by_region_length_family']}`",
            f"- Active by weight class: `{static['active_by_weight_calibration_class']}`",
            f"- Forbidden expression candidates: `{len(static['forbidden_pattern_expression_key_candidates'])}`",
            f"- Bar-first two_chord_bar candidates: `{len(static['bar_first_two_chord_bar_candidates'])}`",
            "",
            "## Runtime standard-tune audit",
            "",
        ]
    )
    for output in summary.get("outputs", []):
        lines.extend(
            [
                f"### {output['title']}",
                "",
                f"- MIDI: `{output['midi_path']}`",
                f"- Piano events: `{output['piano_events']}`",
                f"- v2_6_67 metadata events: `{output['history_policy_events']}`",
                f"- History class counts: `{output['history_class_counts']}`",
                f"- Active/fill/busy/push/tail-push events: `{output['active_events']}` / `{output['fill_like_events']}` / `{output['busy_events']}` / `{output['push_events']}` / `{output['tail_push_events']}`",
                f"- History penalty/bonus events: `{output['history_penalty_events']}` / `{output['history_bonus_events']}`",
                f"- Active-after-active / busy-near-block / tail-push-cluster penalties: `{output['active_after_active_penalty_count']}` / `{output['busy_near_block_count']}` / `{output['tail_push_cluster_penalty_count']}`",
                f"- Stable reset after active/fill/busy: `{output['stable_reset_after_active_count']}` / `{output['stable_reset_after_fill_count']}` / `{output['stable_reset_after_busy_count']}`",
                f"- No-4& recovery after push bonuses: `{output['no_4and_after_push_bonus_count']}`",
                f"- Forbidden expression / bar-first events: `{output['pattern_forbidden_expression_key_events']}` / `{output['bar_first_two_chord_bar_events']}`",
                f"- Top note max / >=75 / voice-leading warnings: `{output['top_note_max']}` / `{output['top_note_ge_75_events']}` / `{output['voice_leading_warning_events']}`",
                "",
            ]
        )
    lines.extend(["## Acceptance", "", f"Passed: `{summary['acceptance']['passed']}`", ""])
    for check in summary["acceptance"]["checks"]:
        lines.append(f"- `{check['name']}`: `{check['passed']}`")
    lines.extend(["", "## Recommended next tasks", ""])
    for task in summary.get("recommended_next_tasks", []):
        lines.append(f"- `{task}`")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
