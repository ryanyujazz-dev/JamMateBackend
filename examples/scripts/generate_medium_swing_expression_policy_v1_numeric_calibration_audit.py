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
from jammate_engine.styles.medium_swing.expression_policy import get_expression_policy

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_68"
MILESTONE_LABEL = "v2_6_68 — Medium Swing ExpressionPolicy V1 Numeric Calibration"
FORBIDDEN_PATTERN_EXPRESSION_KEYS = {"velocity", "duration", "duration_beats", "pedal", "release_beats", "accent", "midi_note"}

SPECS: tuple[dict[str, Any], ...] = (
    {"slug": "all_the_things_you_are", "leadsheet": "all_the_things_you_are.json", "seed": 3680},
    {"slug": "autumn_leaves", "leadsheet": "autumn_leaves.json", "seed": 3681},
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    outputs = [_generate_and_audit(spec) for spec in SPECS]
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": "v2_6_68 calibrates Medium Swing piano comping ExpressionProfile defaults against V1 soft_hold/light_stab/accent_stab/backbeat_hold/final_hold numeric ranges. It changes expression policy only; pattern candidates remain semantic-only and ChordRegion-first.",
        "static_audit": static_audit,
        "outputs": outputs,
        "acceptance": _acceptance(static_audit, outputs),
        "recommended_next_tasks": [
            "v2_6_69_engine_medium_swing_piano_standard_tune_listening_checkpoint",
            "v2_6_70_engine_medium_swing_ending_specific_region_context_candidate_subset_policy",
        ],
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_expression_policy_v1_numeric_calibration_audit_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_expression_policy_v1_numeric_calibration_audit_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_format_report(summary), encoding="utf-8")
    print({"ok": summary["acceptance"]["passed"], "summary_path": str(summary_path), "report_path": str(report_path), "outputs": outputs})
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    arrangement = arrangement_policy.get_arrangement_policy()
    expression = get_expression_policy()
    profile_rows = _profile_rows(expression)
    candidate_rows = _candidate_rows()
    return {
        "checkpoint_version": MILESTONE_ID,
        "arrangement_policy_enabled": bool(arrangement.get("piano_expression_policy_v1_numeric_calibration")),
        "arrangement_policy_version": str(arrangement.get("piano_expression_policy_v1_numeric_calibration_version")),
        "arrangement_policy_contract": str(arrangement.get("piano_expression_policy_v1_numeric_calibration_contract")),
        "expression_policy_enabled": bool(expression.metadata.get("medium_swing_expression_policy_v1_numeric_calibration")),
        "expression_policy_version": str(expression.metadata.get("medium_swing_expression_policy_v1_numeric_calibration_version")),
        "ticks_per_beat": expression.metadata.get("medium_swing_expression_policy_v1_reference_ticks_per_beat"),
        "profile_rows": profile_rows,
        "profiles_outside_v1_reference_ranges": [row for row in profile_rows if not (row["velocity_in_v1_range"] and row["duration_in_v1_range"])],
        "pattern_candidate_count": len(candidate_rows),
        "pattern_forbidden_expression_candidates": [row for row in candidate_rows if row["forbidden_pattern_expression_keys"]],
        "bar_first_two_chord_bar_candidates": [row for row in candidate_rows if row["has_bar_first_two_chord_bar_marker"]],
    }


def _profile_rows(expression) -> list[dict[str, Any]]:
    rows = []
    for profile_name in ("comp_medium", "comp_short", "comp_accent", "comp_backbeat_hold", "comp_accent_hold", "comp_final_hold"):
        profile = expression.profiles[profile_name]
        metadata = dict(profile.metadata)
        velocity_range = tuple(metadata.get("v1_reference_velocity_range") or (0, 127))
        duration_range = tuple(metadata.get("v1_reference_duration_beats_range") or (0.0, 99.0))
        rows.append(
            {
                "profile_name": profile_name,
                "semantic_hint": metadata.get("v1_reference_semantic_hint"),
                "velocity": profile.velocity,
                "velocity_range": velocity_range,
                "velocity_in_v1_range": _in_range(profile.velocity, velocity_range),
                "duration_beats": profile.duration_beats,
                "duration_range": duration_range,
                "duration_in_v1_range": _in_range(profile.duration_beats, duration_range),
                "release_beats": profile.release_beats,
                "pedal": profile.pedal.value,
                "articulation": profile.articulation.value,
                "touch": profile.touch.value,
                "duration_semantics": metadata.get("duration_semantics"),
                "calibration_version": metadata.get("medium_swing_expression_policy_v1_numeric_calibration_version"),
            }
        )
    return rows


def _candidate_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for duration in (1.0, 2.0, 3.0, 4.0, 5.0):
        for candidate in comping_patterns.get_pattern_candidates({"region_duration_beats": duration}):
            forbidden: list[str] = []
            for event in candidate.events:
                event_metadata = dict(event.metadata)
                forbidden.extend(sorted(FORBIDDEN_PATTERN_EXPRESSION_KEYS & set(event_metadata)))
            text_blob = " ".join([candidate.name, candidate.category, str(candidate.metadata), " ".join(candidate.tags)])
            rows.append(
                {
                    "name": candidate.name,
                    "duration_probe": duration,
                    "region_length_family": candidate.metadata.get("region_length_family"),
                    "forbidden_pattern_expression_keys": tuple(sorted(set(forbidden))),
                    "has_bar_first_two_chord_bar_marker": "two_chord_bar" in text_blob or "split_bar" in text_blob,
                }
            )
    return rows


def _generate_and_audit(spec: Mapping[str, Any]) -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / str(spec["leadsheet"])).read_text(encoding="utf-8"))
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_medium_swing_expression_policy_v1_numeric_calibration_demo.mid"
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
    rows = _expression_rows(result.debug)
    pattern_rows = _piano_pattern_rows(result.debug)
    profile_counter = Counter(str(row.get("profile_name") or "missing") for row in rows)
    velocity_by_profile: dict[str, list[int]] = {}
    duration_by_profile: dict[str, list[float]] = {}
    for row in rows:
        profile = str(row.get("profile_name") or "missing")
        velocity_by_profile.setdefault(profile, []).append(int(row.get("velocity") or 0))
        duration_by_profile.setdefault(profile, []).append(float(row.get("duration_beats") or 0.0))
    return {
        "ok": bool(result.ok),
        "title": score.get("title"),
        "slug": slug,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "piano_expression_events": len(rows),
        "calibrated_expression_events": sum(1 for row in rows if row.get("calibration_version") == MILESTONE_ID),
        "profile_counts": dict(profile_counter),
        "profile_velocity_ranges_realized": {profile: [min(values), max(values)] for profile, values in velocity_by_profile.items() if values},
        "profile_duration_ranges_realized": {profile: [round(min(values), 6), round(max(values), 6)] for profile, values in duration_by_profile.items() if values},
        "duration_hold_boundary_guard_events": sum(1 for row in rows if row.get("duration_next_touch_hold_version") == "v2_6_66"),
        "duration_hold_boundary_clamped_events": sum(1 for row in rows if row.get("duration_next_touch_hold_reason") == "next_same_track_touch_beyond_region_clamped_to_region_end"),
        "final_hold_events": profile_counter.get("comp_final_hold", 0),
        "pattern_forbidden_expression_key_events": sum(1 for row in pattern_rows if row.get("pattern_forbidden_expression_keys")),
        "bar_first_two_chord_bar_events": sum(1 for row in pattern_rows if row.get("has_bar_first_two_chord_bar_marker")),
        "top_note_max": piano_audit.summary.get("medium_swing_open_drop_top_note_max"),
        "top_note_ge_75_events": piano_audit.summary.get("medium_swing_open_drop_top_note_ge_75_events"),
        "voice_leading_warning_events": piano_audit.summary.get("medium_swing_open_drop_voice_leading_warning_events"),
    }


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
                "velocity": raw.get("velocity"),
                "duration_beats": raw.get("duration_beats"),
                "pedal": raw.get("pedal"),
                "touch": raw.get("touch"),
                "articulation": raw.get("articulation"),
                "calibration_version": metadata.get("medium_swing_expression_policy_v1_numeric_calibration_version"),
                "duration_next_touch_hold_version": metadata.get("duration_next_touch_hold_version"),
                "duration_next_touch_hold_reason": metadata.get("duration_next_touch_hold_reason"),
            }
        )
    return rows


def _piano_pattern_rows(debug: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in debug.get("piano_musical_audit_events") or []:
        event = dict((raw or {}).get("pattern_event") or {})
        if event.get("track") != "piano":
            continue
        pattern_metadata = dict(event.get("metadata") or {})
        text_blob = " ".join([str(event.get("pattern_id") or ""), str(event.get("category") or ""), str(pattern_metadata)])
        rows.append(
            {
                "event_id": event.get("event_id"),
                "pattern_forbidden_expression_keys": tuple(sorted(FORBIDDEN_PATTERN_EXPRESSION_KEYS & set(pattern_metadata))),
                "has_bar_first_two_chord_bar_marker": "two_chord_bar" in text_blob or "split_bar" in text_blob,
            }
        )
    return rows


def _in_range(value: float, bounds: Iterable[float]) -> bool:
    low, high = tuple(bounds)
    return float(low) - 1e-9 <= float(value) <= float(high) + 1e-9


def _acceptance(static_audit: Mapping[str, Any], outputs: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = [
        {"name": "static: arrangement declares v2_6_68 expression calibration", "passed": static_audit.get("arrangement_policy_enabled") is True and static_audit.get("arrangement_policy_version") == MILESTONE_ID},
        {"name": "static: expression policy declares v2_6_68 calibration", "passed": static_audit.get("expression_policy_enabled") is True and static_audit.get("expression_policy_version") == MILESTONE_ID},
        {"name": "static: all calibrated profiles inside V1 reference ranges", "passed": len(static_audit.get("profiles_outside_v1_reference_ranges") or []) == 0},
        {"name": "static: no pattern candidate writes final expression values", "passed": len(static_audit.get("pattern_forbidden_expression_candidates") or []) == 0},
        {"name": "static: no bar-first/two-chord-bar markers remain", "passed": len(static_audit.get("bar_first_two_chord_bar_candidates") or []) == 0},
    ]
    for output in outputs:
        checks.extend(
            [
                {"name": f"{output['slug']}: generation ok", "passed": bool(output.get("ok"))},
                {"name": f"{output['slug']}: calibrated expression metadata present", "passed": output.get("calibrated_expression_events", 0) > 0},
                {"name": f"{output['slug']}: hold boundary guard still active", "passed": output.get("duration_hold_boundary_guard_events", 0) > 0},
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
            "## Static expression policy audit",
            "",
            f"- Arrangement / expression versions: `{static['arrangement_policy_version']}` / `{static['expression_policy_version']}`",
            f"- V1 ticks per beat: `{static['ticks_per_beat']}`",
            f"- Profiles outside V1 ranges: `{len(static['profiles_outside_v1_reference_ranges'])}`",
            f"- Forbidden pattern expression candidates: `{len(static['pattern_forbidden_expression_candidates'])}`",
            f"- Bar-first two_chord_bar candidates: `{len(static['bar_first_two_chord_bar_candidates'])}`",
            "",
            "### Calibrated profiles",
            "",
            "| profile | semantic hint | velocity | velocity range | duration | duration range | articulation | touch |",
            "|---|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in static["profile_rows"]:
        lines.append(
            f"| `{row['profile_name']}` | `{row['semantic_hint']}` | `{row['velocity']}` | `{row['velocity_range']}` | `{row['duration_beats']}` | `{row['duration_range']}` | `{row['articulation']}` | `{row['touch']}` |"
        )
    lines.extend(["", "## Runtime standard-tune audit", ""])
    for output in summary.get("outputs", []):
        lines.extend(
            [
                f"### {output['title']}",
                "",
                f"- MIDI: `{output['midi_path']}`",
                f"- Piano expression events / calibrated metadata events: `{output['piano_expression_events']}` / `{output['calibrated_expression_events']}`",
                f"- Profile counts: `{output['profile_counts']}`",
                f"- Realized velocity ranges by profile: `{output['profile_velocity_ranges_realized']}`",
                f"- Realized duration ranges by profile: `{output['profile_duration_ranges_realized']}`",
                f"- Hold boundary guard / clamped-to-region events: `{output['duration_hold_boundary_guard_events']}` / `{output['duration_hold_boundary_clamped_events']}`",
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
