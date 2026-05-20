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
MILESTONE_ID = "v2_6_59"
MILESTONE_LABEL = "v2_6_59 — Medium Swing Piano Comping History Continuity Scorer"

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
        "scope": "Audit the v2_6_59 Medium Swing piano comping history scorer. The scorer reweights the existing ChordRegion-length candidate pool only; it does not introduce a parallel selector, new pattern source, voicing rule, expression parameter, or gesture.",
        "outputs": outputs,
        "acceptance": _acceptance(outputs),
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_piano_history_continuity_audit_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_piano_history_continuity_audit_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_format_report(summary), encoding="utf-8")
    print({"ok": summary["acceptance"]["passed"], "summary_path": str(summary_path), "report_path": str(report_path), "outputs": outputs})
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def _generate_and_audit(spec: Mapping[str, Any]) -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / str(spec["leadsheet"])).read_text(encoding="utf-8"))
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_medium_swing_piano_history_continuity_demo.mid"
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
    rows = _piano_pattern_rows(result.debug)
    region_rows = _region_level_rows(rows)
    continuity = _continuity_summary(region_rows)
    metadata_summary = _metadata_summary(rows)
    pattern_counts = Counter(row["pattern_id"] for row in region_rows)
    class_counts = Counter(row["continuity_class"] for row in region_rows)
    region_length_counts = Counter(row["region_length_family"] for row in region_rows)
    return {
        "ok": bool(result.ok),
        "title": score.get("title"),
        "slug": slug,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "piano_events": len(rows),
        "piano_regions": len(region_rows),
        "pattern_counts": dict(pattern_counts),
        "continuity_class_counts": dict(class_counts),
        "region_length_counts": dict(region_length_counts),
        "metadata": metadata_summary,
        "continuity": continuity,
        "top_note_max": piano_audit.summary.get("medium_swing_open_drop_top_note_max"),
        "top_note_ge_75_events": piano_audit.summary.get("medium_swing_open_drop_top_note_ge_75_events"),
        "voice_leading_warning_events": piano_audit.summary.get("medium_swing_open_drop_voice_leading_warning_events"),
    }


def _piano_pattern_rows(debug: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in debug.get("piano_musical_audit_events") or []:
        event = dict((raw or {}).get("pattern_event") or {})
        if event.get("track") != "piano":
            continue
        metadata = dict(event.get("metadata") or {})
        rows.append(
            {
                "event_id": event.get("event_id"),
                "region_id": event.get("region_id"),
                "onset_beat": float(event.get("onset_beat") or 0.0),
                "local_beat": float(event.get("local_beat") or 0.0),
                "pattern_id": event.get("pattern_id"),
                "rhythmic_cell": metadata.get("rhythmic_cell"),
                "rhythm_family": metadata.get("rhythm_family"),
                "continuity_class": metadata.get("history_continuity_class") or metadata.get("weight_calibration_class"),
                "region_length_family": metadata.get("region_length_family"),
                "history_version": metadata.get("history_continuity_scorer_version"),
                "history_applied": bool(metadata.get("history_continuity_scorer_applied", False)),
                "history_multiplier": float(metadata.get("history_continuity_multiplier") or 1.0),
                "history_reasons": list(metadata.get("history_continuity_reasons") or []),
            }
        )
    return sorted(rows, key=lambda item: (float(item["onset_beat"]), str(item["event_id"])))


def _region_level_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_region: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_region.setdefault(str(row["region_id"]), []).append(row)
    result: list[dict[str, Any]] = []
    for region_id, region_events in by_region.items():
        ordered = sorted(region_events, key=lambda item: float(item["onset_beat"]))
        first = dict(ordered[0])
        first["region_event_count"] = len(ordered)
        result.append(first)
    return sorted(result, key=lambda item: float(item["onset_beat"]))


def _metadata_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    versions = Counter(str(row.get("history_version") or "missing") for row in rows)
    reasons = Counter(reason for row in rows for reason in row.get("history_reasons") or [])
    penalized = [row for row in rows if float(row.get("history_multiplier") or 1.0) < 1.0]
    bonus = [row for row in rows if float(row.get("history_multiplier") or 1.0) > 1.0]
    return {
        "history_version_counts": dict(versions),
        "history_applied_events": sum(1 for row in rows if row.get("history_applied")),
        "penalized_events": len(penalized),
        "bonus_events": len(bonus),
        "reason_counts": dict(reasons),
    }


def _continuity_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    exact_repeats = 0
    same_family_repeats = 0
    consecutive_offbeat = 0
    consecutive_active = 0
    consecutive_tail_push = 0
    pairs: list[dict[str, Any]] = []
    for previous, current in zip(rows, rows[1:]):
        previous_class = str(previous.get("continuity_class") or "")
        current_class = str(current.get("continuity_class") or "")
        exact = previous.get("pattern_id") == current.get("pattern_id")
        same_family = previous.get("rhythm_family") == current.get("rhythm_family")
        if exact:
            exact_repeats += 1
        if same_family:
            same_family_repeats += 1
        if previous_class == current_class == "offbeat":
            consecutive_offbeat += 1
        if previous_class == current_class == "active":
            consecutive_active += 1
        if previous_class == current_class == "tail_push":
            consecutive_tail_push += 1
        if exact or same_family or previous_class == current_class:
            pairs.append(
                {
                    "previous_region_id": previous.get("region_id"),
                    "region_id": current.get("region_id"),
                    "previous_pattern": previous.get("pattern_id"),
                    "pattern": current.get("pattern_id"),
                    "previous_class": previous_class,
                    "class": current_class,
                    "same_family": bool(same_family),
                    "exact_repeat": bool(exact),
                }
            )
    return {
        "region_transition_count": max(0, len(rows) - 1),
        "exact_repeat_count": exact_repeats,
        "same_family_repeat_count": same_family_repeats,
        "consecutive_offbeat_count": consecutive_offbeat,
        "consecutive_active_count": consecutive_active,
        "consecutive_tail_push_count": consecutive_tail_push,
        "flagged_pairs_preview": pairs[:20],
        "checkpoint_passed": bool(exact_repeats == 0 and consecutive_active == 0 and consecutive_tail_push == 0),
    }


def _acceptance(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for output in outputs:
        metadata = dict(output.get("metadata") or {})
        continuity = dict(output.get("continuity") or {})
        checks.extend(
            [
                {"name": f"{output['slug']}: generation ok", "passed": bool(output.get("ok"))},
                {"name": f"{output['slug']}: history metadata applied", "passed": metadata.get("history_applied_events", 0) == output.get("piano_events", -1)},
                {"name": f"{output['slug']}: no exact consecutive pattern repeat", "passed": continuity.get("exact_repeat_count") == 0},
                {"name": f"{output['slug']}: no consecutive active", "passed": continuity.get("consecutive_active_count") == 0},
                {"name": f"{output['slug']}: no consecutive tail-push", "passed": continuity.get("consecutive_tail_push_count") == 0},
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
                f"- Piano events / regions: `{output['piano_events']}` / `{output['piano_regions']}`",
                f"- Pattern counts: `{output['pattern_counts']}`",
                f"- Continuity class counts: `{output['continuity_class_counts']}`",
                f"- Metadata: `{output['metadata']}`",
                f"- Continuity: `{output['continuity']}`",
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
