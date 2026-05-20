from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.form.form_expander import expand_form_to_regions
from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_62"
MILESTONE_LABEL = "v2_6_62 — Medium Swing CoverageGuard Region-First Cleanup"

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
        "scope": "Audit that Medium Swing CoverageGuard is ChordRegion-first and backup-only after the region-length piano comping work. The guard should stamp coverage metadata on already selected region-local piano events, insert no fallback anchors in normal standard-tune generation, and leave top-register / voice-leading checkpoints calm.",
        "outputs": outputs,
        "acceptance": _acceptance(outputs),
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_region_first_coverage_guard_audit_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_region_first_coverage_guard_audit_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_format_report(summary), encoding="utf-8")
    print({"ok": summary["acceptance"]["passed"], "summary_path": str(summary_path), "report_path": str(report_path), "outputs": outputs})
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def _generate_and_audit(spec: Mapping[str, Any]) -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / str(spec["leadsheet"])).read_text(encoding="utf-8"))
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_medium_swing_region_first_coverage_guard_demo.mid"
    choruses = 3
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": int(score.get("tempo", 132)),
            "choruses": choruses,
            "seed": int(spec["seed"]),
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
        }
    )
    piano_audit = build_piano_musical_audit(result.debug)
    timeline = expand_form_to_regions(normalize_leadsheet(parse_leadsheet(score)), choruses)
    expected_regions = {region.region_id: region for region in timeline.regions}
    rows = _piano_pattern_rows(result.debug)
    rows_by_region: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_region[str(row["region_id"])].append(row)
    uncovered_regions = [region_id for region_id in expected_regions if region_id not in rows_by_region]
    inserted_rows = [row for row in rows if row.get("coverage_inserted")]
    missing_version_rows = [row for row in rows if row.get("coverage_version") != "v2_6_62"]
    region_event_counts = [len(rows_by_region[region_id]) for region_id in expected_regions if region_id in rows_by_region]
    short_uncovered = [region_id for region_id in uncovered_regions if expected_regions[region_id].duration_beats <= 2.25]
    metadata_summary = _metadata_summary(rows)
    return {
        "ok": bool(result.ok),
        "title": score.get("title"),
        "slug": slug,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "expected_region_count": len(expected_regions),
        "covered_region_count": len(expected_regions) - len(uncovered_regions),
        "uncovered_region_count": len(uncovered_regions),
        "short_uncovered_region_count": len(short_uncovered),
        "uncovered_regions_preview": uncovered_regions[:12],
        "short_uncovered_regions_preview": short_uncovered[:12],
        "piano_events": len(rows),
        "max_piano_events_per_region": max(region_event_counts) if region_event_counts else 0,
        "coverage_inserted_events": len(inserted_rows),
        "coverage_inserted_preview": inserted_rows[:8],
        "coverage_missing_version_events": len(missing_version_rows),
        "coverage_missing_version_preview": missing_version_rows[:8],
        "metadata": metadata_summary,
        "region_length_counts": dict(Counter(str(row.get("coverage_region_length_family") or "missing") for row in rows)),
        "coverage_outcome_counts": dict(Counter(str(row.get("coverage_outcome") or "missing") for row in rows)),
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
                "status": event.get("status"),
                "region_id": event.get("region_id"),
                "onset_beat": float(event.get("onset_beat") or 0.0),
                "local_beat": float(event.get("local_beat") or 0.0),
                "pattern_id": event.get("pattern_id"),
                "rhythmic_cell": metadata.get("rhythmic_cell"),
                "rhythm_family": metadata.get("rhythm_family"),
                "coverage_version": metadata.get("piano_region_first_coverage_guard_version"),
                "coverage_checked": bool(metadata.get("piano_region_first_coverage_guard_checked", False)),
                "coverage_inserted": bool(metadata.get("piano_region_first_coverage_guard_inserted", False)),
                "coverage_outcome": metadata.get("piano_region_first_coverage_guard_outcome"),
                "coverage_scope": metadata.get("piano_region_first_coverage_guard_scope"),
                "coverage_region_duration_beats": metadata.get("coverage_region_duration_beats"),
                "coverage_region_length_family": metadata.get("coverage_region_length_family"),
                "coverage_backup_only": bool(metadata.get("coverage_guard_is_backup_only", False)),
                "coverage_time_reference": metadata.get("coverage_time_reference"),
                "candidate": metadata.get("candidate"),
                "category": metadata.get("category"),
            }
        )
    return sorted(rows, key=lambda item: (float(item["onset_beat"]), str(item["event_id"])))


def _metadata_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "coverage_version_counts": dict(Counter(str(row.get("coverage_version") or "missing") for row in rows)),
        "coverage_checked_events": sum(1 for row in rows if row.get("coverage_checked")),
        "coverage_backup_only_events": sum(1 for row in rows if row.get("coverage_backup_only")),
        "coverage_region_first_scope_events": sum(1 for row in rows if row.get("coverage_scope") == "ChordRegion"),
        "coverage_region_local_time_events": sum(1 for row in rows if row.get("coverage_time_reference") == "region_local_beats"),
    }


def _acceptance(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for output in outputs:
        metadata = dict(output.get("metadata") or {})
        checks.extend(
            [
                {"name": f"{output['slug']}: generation ok", "passed": bool(output.get("ok"))},
                {"name": f"{output['slug']}: all ChordRegions have piano harmonic presence", "passed": output.get("uncovered_region_count") == 0},
                {"name": f"{output['slug']}: no short ChordRegion uncovered", "passed": output.get("short_uncovered_region_count") == 0},
                {"name": f"{output['slug']}: all piano events carry v2_6_62 coverage metadata", "passed": metadata.get("coverage_checked_events") == output.get("piano_events") and output.get("coverage_missing_version_events") == 0},
                {"name": f"{output['slug']}: normal generation does not need fallback insertion", "passed": output.get("coverage_inserted_events") == 0},
                {"name": f"{output['slug']}: guard remains backup-only", "passed": metadata.get("coverage_backup_only_events") == output.get("piano_events")},
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
                f"- Covered regions: `{output['covered_region_count']}` / `{output['expected_region_count']}`",
                f"- Uncovered regions / short uncovered: `{output['uncovered_region_count']}` / `{output['short_uncovered_region_count']}`",
                f"- Piano events: `{output['piano_events']}`",
                f"- Coverage inserted events: `{output['coverage_inserted_events']}`",
                f"- Max piano events per region: `{output['max_piano_events_per_region']}`",
                f"- Coverage metadata: `{output['metadata']}`",
                f"- Region length counts: `{output['region_length_counts']}`",
                f"- Coverage outcome counts: `{output['coverage_outcome_counts']}`",
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
