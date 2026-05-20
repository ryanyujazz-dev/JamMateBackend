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
MILESTONE_ID = "v2_6_61"
MILESTONE_LABEL = "v2_6_61 — Medium Swing Region-First Anticipation Compatibility Checkpoint"

SPECS: tuple[dict[str, Any], ...] = (
    {"slug": "all_the_things_you_are", "leadsheet": "all_the_things_you_are.json", "seed": 3300},
    {"slug": "autumn_leaves", "leadsheet": "autumn_leaves.json", "seed": 3301},
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    outputs = [_generate_and_audit(spec) for spec in SPECS]
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": "Audit that Medium Swing anticipation remains ChordRegion-first after the region-length piano comping work: anticipated next-region starts are placed at previous_region.duration_beats - 0.5, so 4-beat regions use local 3.5 and 2-beat regions use local 1.5. This checkpoint does not add new patterns, voicings, gestures, expression parameters, or bar-first/two-chord-bar routing.",
        "outputs": outputs,
        "acceptance": _acceptance(outputs),
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_region_first_anticipation_audit_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_region_first_anticipation_audit_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_format_report(summary), encoding="utf-8")
    print({"ok": summary["acceptance"]["passed"], "summary_path": str(summary_path), "report_path": str(report_path), "outputs": outputs})
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def _generate_and_audit(spec: Mapping[str, Any]) -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / str(spec["leadsheet"])).read_text(encoding="utf-8"))
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_medium_swing_region_first_anticipation_demo.mid"
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
    anticipation_rows = _anticipation_rows(result.debug)
    active_rows = [row for row in anticipation_rows if row["kind"] == "next_beat1_to_previous_tail"]
    suppressed_rows = [row for row in anticipation_rows if row["kind"] == "suppressed_original_beat1"]
    target_local_counts = Counter(str(row.get("target_local_beat_in_previous")) for row in active_rows)
    previous_duration_counts = Counter(str(row.get("previous_region_duration_beats")) for row in active_rows)
    current_duration_counts = Counter(str(row.get("current_region_duration_beats")) for row in active_rows)
    version_counts = Counter(str(row.get("region_first_version") or "missing") for row in active_rows)
    invalid_rows = [row for row in active_rows if not _row_is_region_first_valid(row)]
    return {
        "ok": bool(result.ok),
        "title": score.get("title"),
        "slug": slug,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "anticipation_event_count": len(anticipation_rows),
        "active_anticipation_count": len(active_rows),
        "suppressed_original_count": len(suppressed_rows),
        "target_local_counts": dict(target_local_counts),
        "previous_region_duration_counts": dict(previous_duration_counts),
        "current_region_duration_counts": dict(current_duration_counts),
        "region_first_version_counts": dict(version_counts),
        "two_beat_previous_tail_anticipations": sum(1 for row in active_rows if row.get("previous_region_duration_beats") == 2.0 and row.get("target_local_beat_in_previous") == 1.5),
        "four_beat_previous_tail_anticipations": sum(1 for row in active_rows if row.get("previous_region_duration_beats") == 4.0 and row.get("target_local_beat_in_previous") == 3.5),
        "invalid_region_first_rows": invalid_rows[:10],
        "valid_region_first_rows": len(active_rows) - len(invalid_rows),
        "preview": active_rows[:8],
        "top_note_max": piano_audit.summary.get("medium_swing_open_drop_top_note_max"),
        "top_note_ge_75_events": piano_audit.summary.get("medium_swing_open_drop_top_note_ge_75_events"),
        "voice_leading_warning_events": piano_audit.summary.get("medium_swing_open_drop_voice_leading_warning_events"),
    }


def _anticipation_rows(debug: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in debug.get("piano_musical_audit_events") or []:
        event = dict((raw or {}).get("pattern_event") or {})
        if event.get("track") != "piano":
            continue
        metadata = dict(event.get("metadata") or {})
        anticipation = dict(metadata.get("anticipation") or {})
        if not anticipation:
            continue
        rows.append(
            {
                "event_id": event.get("event_id"),
                "status": event.get("status"),
                "region_id": event.get("region_id"),
                "pattern_id": event.get("pattern_id"),
                "onset_beat": _to_float(event.get("onset_beat")),
                "local_beat": _to_float(event.get("local_beat")),
                "kind": anticipation.get("kind"),
                "policy": anticipation.get("policy"),
                "source_region_id": anticipation.get("source_region_id"),
                "placed_in_region_id": anticipation.get("placed_in_region_id"),
                "target_local_beat_in_previous": _to_float(anticipation.get("target_local_beat_in_previous")),
                "previous_region_duration_beats": _to_float(anticipation.get("previous_region_duration_beats")),
                "current_region_duration_beats": _to_float(anticipation.get("current_region_duration_beats")),
                "previous_region_last_beat_local": _to_float(anticipation.get("previous_region_last_beat_local")),
                "previous_region_last_upbeat_local": _to_float(anticipation.get("previous_region_last_upbeat_local")),
                "tail_checked_local_beats": tuple(anticipation.get("tail_checked_local_beats") or ()),
                "tail_availability_reason": anticipation.get("tail_availability_reason"),
                "region_first_version": anticipation.get("region_first_anticipation_compatibility_checkpoint_version"),
                "bar_first_4and_assumption": anticipation.get("bar_first_4and_assumption"),
                "timing_grid": anticipation.get("timing_grid"),
                "target_timing_intent": anticipation.get("target_timing_intent"),
                "expected_upbeat_fraction": anticipation.get("expected_upbeat_fraction"),
            }
        )
    return sorted(rows, key=lambda item: (float(item.get("onset_beat") or 0.0), str(item.get("event_id"))))


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _row_is_region_first_valid(row: Mapping[str, Any]) -> bool:
    previous_duration = row.get("previous_region_duration_beats")
    target_local = row.get("target_local_beat_in_previous")
    last_beat = row.get("previous_region_last_beat_local")
    last_upbeat = row.get("previous_region_last_upbeat_local")
    checked = tuple(row.get("tail_checked_local_beats") or ())
    if row.get("region_first_version") != "v2_6_61":
        return False
    if row.get("bar_first_4and_assumption") is not False:
        return False
    if previous_duration is None or target_local is None:
        return False
    expected_last_beat = round(max(0.0, float(previous_duration) - 1.0), 6)
    expected_last_upbeat = round(max(0.0, float(previous_duration) - 0.5), 6)
    return (
        round(float(target_local), 6) == expected_last_upbeat
        and round(float(last_beat or 0.0), 6) == expected_last_beat
        and round(float(last_upbeat or 0.0), 6) == expected_last_upbeat
        and tuple(round(float(item), 6) for item in checked) == (expected_last_beat, expected_last_upbeat)
    )


def _acceptance(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    total_two_beat_tail = sum(int(output.get("two_beat_previous_tail_anticipations") or 0) for output in outputs)
    for output in outputs:
        checks.extend(
            [
                {"name": f"{output['slug']}: generation ok", "passed": bool(output.get("ok"))},
                {"name": f"{output['slug']}: active anticipations have region-first metadata", "passed": output.get("active_anticipation_count", 0) == output.get("valid_region_first_rows", -1)},
                {"name": f"{output['slug']}: no invalid region-first anticipation rows", "passed": len(output.get("invalid_region_first_rows") or []) == 0},
                {"name": f"{output['slug']}: top register calm", "passed": (output.get("top_note_ge_75_events") or 0) == 0},
                {"name": f"{output['slug']}: voice-leading warnings calm", "passed": (output.get("voice_leading_warning_events") or 0) == 0},
            ]
        )
    checks.append({"name": "combined: observed at least one 2-beat previous-region local 2& anticipation", "passed": total_two_beat_tail > 0})
    return {"passed": all(check["passed"] for check in checks), "checks": checks}


def _format_report(summary: Mapping[str, Any]) -> str:
    lines = [f"# {summary['milestone']}", "", str(summary.get("scope", "")), ""]
    for output in summary.get("outputs", []):
        lines.extend(
            [
                f"## {output['title']}",
                "",
                f"- MIDI: `{output['midi_path']}`",
                f"- Anticipation events / active / suppressed: `{output['anticipation_event_count']}` / `{output['active_anticipation_count']}` / `{output['suppressed_original_count']}`",
                f"- Target local counts: `{output['target_local_counts']}`",
                f"- Previous-region duration counts: `{output['previous_region_duration_counts']}`",
                f"- 2-beat previous-tail anticipations: `{output['two_beat_previous_tail_anticipations']}`",
                f"- 4-beat previous-tail anticipations: `{output['four_beat_previous_tail_anticipations']}`",
                f"- Region-first version counts: `{output['region_first_version_counts']}`",
                f"- Invalid rows: `{output['invalid_region_first_rows']}`",
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
