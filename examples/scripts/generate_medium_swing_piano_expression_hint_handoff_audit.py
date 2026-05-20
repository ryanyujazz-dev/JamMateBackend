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

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_63"
MILESTONE_LABEL = "v2_6_63 — Medium Swing Piano Expression-Hint Handoff Checkpoint"

SPECS: tuple[dict[str, Any], ...] = (
    {"slug": "all_the_things_you_are", "leadsheet": "all_the_things_you_are.json", "seed": 3300},
    {"slug": "autumn_leaves", "leadsheet": "autumn_leaves.json", "seed": 3301},
)

HOLD_HINTS = {"soft_hold", "accent_hold", "backbeat_hold", "final_hold", "anticipated_hold"}
ALLOWED_HINTS = {"soft_hold", "light_stab", "accent_stab", "accent_hold", "backbeat_hold", "final_hold"}


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    outputs = [_generate_and_audit(spec) for spec in SPECS]
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": "Audit that Medium Swing piano patterns carry semantic expression hints only, include accent_hold, and that hold-style hints are resolved by ExpressionResolver as hold-until-next-touch durations rather than fixed pattern durations.",
        "outputs": outputs,
        "acceptance": _acceptance(outputs),
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_piano_expression_hint_handoff_audit_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_piano_expression_hint_handoff_audit_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_format_report(summary), encoding="utf-8")
    print({"ok": summary["acceptance"]["passed"], "summary_path": str(summary_path), "report_path": str(report_path), "outputs": outputs})
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def _generate_and_audit(spec: Mapping[str, Any]) -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / str(spec["leadsheet"])).read_text(encoding="utf-8"))
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_medium_swing_piano_expression_hint_handoff_demo.mid"
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
    rows = _piano_expression_rows(result.debug)
    hold_rows = [row for row in rows if row.get("semantic_expression_hint") in HOLD_HINTS]
    non_hold_rows = [row for row in rows if row.get("semantic_expression_hint") not in HOLD_HINTS]
    forbidden_pattern_rows = [row for row in rows if row.get("pattern_forbidden_expression_keys")]
    missing_handoff_rows = [row for row in rows if row.get("expression_hint_handoff_policy_version") != "v2_6_63"]
    invalid_hint_rows = [row for row in rows if row.get("semantic_expression_hint") not in ALLOWED_HINTS]
    return {
        "ok": bool(result.ok),
        "title": score.get("title"),
        "slug": slug,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "piano_events": len(rows),
        "semantic_hint_counts": dict(Counter(str(row.get("semantic_expression_hint") or "missing") for row in rows)),
        "profile_counts": dict(Counter(str(row.get("profile_name") or "missing") for row in rows)),
        "hold_hint_events": len(hold_rows),
        "hold_until_next_touch_applied_events": sum(1 for row in hold_rows if row.get("duration_next_touch_hold_applied")),
        "hold_until_next_touch_missing_events": sum(1 for row in hold_rows if not row.get("duration_next_touch_hold_applied")),
        "hold_reason_counts": dict(Counter(str(row.get("duration_next_touch_hold_reason") or "missing") for row in hold_rows)),
        "accent_hold_events": sum(1 for row in rows if row.get("semantic_expression_hint") == "accent_hold"),
        "accent_hold_profile_events": sum(1 for row in rows if row.get("profile_name") == "comp_accent_hold"),
        "accent_hold_duration_min": _min_duration(row for row in rows if row.get("semantic_expression_hint") == "accent_hold"),
        "accent_hold_duration_max": _max_duration(row for row in rows if row.get("semantic_expression_hint") == "accent_hold"),
        "non_hold_next_touch_applied_events": sum(1 for row in non_hold_rows if row.get("duration_next_touch_hold_applied")),
        "missing_handoff_events": len(missing_handoff_rows),
        "invalid_semantic_hint_events": len(invalid_hint_rows),
        "pattern_forbidden_expression_key_events": len(forbidden_pattern_rows),
        "duration_min": _min_duration(rows),
        "duration_max": _max_duration(rows),
        "top_note_max": piano_audit.summary.get("medium_swing_open_drop_top_note_max"),
        "top_note_ge_75_events": piano_audit.summary.get("medium_swing_open_drop_top_note_ge_75_events"),
        "voice_leading_warning_events": piano_audit.summary.get("medium_swing_open_drop_voice_leading_warning_events"),
    }


def _piano_expression_rows(debug: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in debug.get("piano_musical_audit_events") or []:
        event = dict((raw or {}).get("pattern_event") or {})
        if event.get("track") != "piano":
            continue
        expression = dict((raw or {}).get("expression") or {})
        pattern_metadata = dict(event.get("metadata") or {})
        expression_metadata = dict(expression.get("metadata") or {})
        forbidden = [key for key in {"velocity", "duration", "duration_beats", "pedal"} if key in pattern_metadata]
        rows.append(
            {
                "event_id": event.get("event_id"),
                "pattern_id": event.get("pattern_id"),
                "onset_beat": event.get("onset_beat"),
                "local_beat": event.get("local_beat"),
                "semantic_expression_hint": pattern_metadata.get("semantic_expression_hint"),
                "expression_hint": event.get("expression_hint"),
                "expression_hint_handoff_policy_version": pattern_metadata.get("expression_hint_handoff_policy_version") or pattern_metadata.get("expression_hint_handoff_policy"),
                "profile_name": expression.get("profile_name"),
                "duration_beats": expression.get("duration_beats"),
                "articulation": expression.get("articulation"),
                "touch": expression.get("touch"),
                "accent": expression.get("accent"),
                "duration_next_touch_hold_applied": bool(expression_metadata.get("duration_next_touch_hold_applied", False)),
                "duration_next_touch_hold_reason": expression_metadata.get("duration_next_touch_hold_reason"),
                "duration_next_touch_hold_gap_beats": expression_metadata.get("duration_next_touch_hold_gap_beats"),
                "pattern_forbidden_expression_keys": forbidden,
            }
        )
    return sorted(rows, key=lambda row: (float(row.get("onset_beat") or 0.0), str(row.get("event_id"))))


def _min_duration(rows) -> float | None:
    values = [float(row.get("duration_beats") or 0.0) for row in rows]
    return min(values) if values else None


def _max_duration(rows) -> float | None:
    values = [float(row.get("duration_beats") or 0.0) for row in rows]
    return max(values) if values else None


def _acceptance(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for output in outputs:
        checks.extend(
            [
                {"name": f"{output['slug']}: generation ok", "passed": bool(output.get("ok"))},
                {"name": f"{output['slug']}: all piano events carry v2_6_63 handoff metadata", "passed": output.get("missing_handoff_events") == 0},
                {"name": f"{output['slug']}: semantic hints stay in approved set", "passed": output.get("invalid_semantic_hint_events") == 0},
                {"name": f"{output['slug']}: patterns still contain no final expression values", "passed": output.get("pattern_forbidden_expression_key_events") == 0},
                {"name": f"{output['slug']}: hold hints use next-touch duration semantics", "passed": output.get("hold_until_next_touch_missing_events") == 0},
                {"name": f"{output['slug']}: non-hold hints do not accidentally use hold semantics", "passed": output.get("non_hold_next_touch_applied_events") == 0},
                {"name": f"{output['slug']}: accent_hold is available and routed", "passed": output.get("accent_hold_events", 0) >= 1 and output.get("accent_hold_profile_events", 0) == output.get("accent_hold_events", -1)},
                {"name": f"{output['slug']}: top register calm", "passed": (output.get("top_note_ge_75_events") or 0) == 0},
                {"name": f"{output['slug']}: voice-leading warnings calm", "passed": (output.get("voice_leading_warning_events") or 0) == 0},
            ]
        )
    return {"passed": all(check["passed"] for check in checks), "checks": checks}


def _format_report(summary: Mapping[str, Any]) -> str:
    lines = [f"# {summary['milestone']}", "", str(summary.get("scope", "")), ""]
    for output in summary.get("outputs", []):
        lines.extend(
            [
                f"## {output['title']}",
                "",
                f"- MIDI: `{output['midi_path']}`",
                f"- Piano events: `{output['piano_events']}`",
                f"- Semantic hint counts: `{output['semantic_hint_counts']}`",
                f"- Profile counts: `{output['profile_counts']}`",
                f"- Hold events / next-touch applied / missing: `{output['hold_hint_events']}` / `{output['hold_until_next_touch_applied_events']}` / `{output['hold_until_next_touch_missing_events']}`",
                f"- Hold reasons: `{output['hold_reason_counts']}`",
                f"- Accent-hold events/profile events/duration range: `{output['accent_hold_events']}` / `{output['accent_hold_profile_events']}` / `{output['accent_hold_duration_min']}`–`{output['accent_hold_duration_max']}`",
                f"- Missing handoff / invalid hints / forbidden pattern keys: `{output['missing_handoff_events']}` / `{output['invalid_semantic_hint_events']}` / `{output['pattern_forbidden_expression_key_events']}`",
                f"- Duration min/max: `{output['duration_min']}` / `{output['duration_max']}`",
                f"- Top note max / >=75 / voice-leading warnings: `{output['top_note_max']}` / `{output['top_note_ge_75_events']}` / `{output['voice_leading_warning_events']}`",
                "",
            ]
        )
    lines.extend(["## Acceptance", "", f"Passed: `{summary['acceptance']['passed']}`", ""])
    for check in summary["acceptance"]["checks"]:
        lines.append(f"- `{check['name']}`: `{check['passed']}`")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
