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
from jammate_engine.core.voicing import Disposition, generate_candidates
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.bossa_nova import voicing_policy

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_112"
MILESTONE_LABEL = "v2_6_112 — Engine Bossa Nova Voicing Listening Checkpoint"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 23112, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 23113, "slug": "blue_bossa_5x"},
)
INSPECTED_BARS = (14, 19, 29)
INSPECTED_SYMBOLS = ("Cm7", "Fm7", "Dm7b5", "G7b9", "Ab7", "Dbmaj7")
EXPECTED_PARENT_SOURCE = "compact_closed_parent_candidates_for_projection"
ALLOWED_METHODS = {"drop2", "drop3", "drop2_and_4"}
RETIRED_GROUPINGS = {"1+3", "2+2", "one_plus_three", "two_plus_two"}


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    runtime_audits = [_generate_runtime_audit(spec) for spec in DEMO_SPECS]
    summary = {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "scope": (
            "Checkpoint the Bossa OPEN-main voicing baseline after v2_6_102 through v2_6_111. "
            "This verifies ordinary runtime uses normal 4-to-5-note drop-family OPEN voicing, excludes generic_open, "
            "does not revive 2/3-note forced density or retired 1+3/2+2 grouped metadata, and has no low-cluster/top-gap artifact."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
    }
    summary["acceptance"] = _acceptance(static_audit, runtime_audits)
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_voicing_listening_checkpoint_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_voicing_listening_checkpoint_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    policy = voicing_policy.get_voicing_policy()
    metadata = dict(policy.metadata or {})
    checkpoint = dict(metadata.get("bossa_voicing_listening_checkpoint") or {})
    rows: list[dict[str, Any]] = []
    method_counts: Counter[str] = Counter()
    density_counts: Counter[str] = Counter()
    content_counts: Counter[str] = Counter()
    bad_low_cluster_rows: list[dict[str, Any]] = []
    retired_grouping_rows: list[dict[str, Any]] = []
    for symbol in INSPECTED_SYMBOLS:
        for candidate in generate_candidates(symbol, policy):
            if candidate.disposition != Disposition.OPEN:
                continue
            row = _candidate_row(symbol, candidate)
            rows.append(row)
            method_counts[row["method"]] += 1
            density_counts[str(row["density"])] += 1
            content_counts[str(row["content_family"])] += 1
            if _is_low_cluster_top_gap(row["notes"]):
                bad_low_cluster_rows.append(row)
            if _has_retired_grouping(row):
                retired_grouping_rows.append(row)
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "policy_preferred_disposition": getattr(policy.preferred_disposition, "value", str(policy.preferred_disposition)),
        "policy_allowed_dispositions": [getattr(value, "value", str(value)) for value in policy.allowed_dispositions],
        "policy_density_range": [policy.min_density, policy.max_density],
        "policy_open_projection_methods": list(metadata.get("open_projection_methods") or []),
        "checkpoint_metadata": checkpoint,
        "candidate_count": len(rows),
        "method_counts": dict(method_counts),
        "density_counts": dict(density_counts),
        "content_counts": dict(content_counts),
        "generic_open_candidate_count": int(method_counts.get("generic_open", 0)),
        "low_density_candidate_count": sum(int(count) for density, count in density_counts.items() if density in {"2", "3"}),
        "fallback_parent_candidate_count": sum(1 for row in rows if row["noncompact_parent_fallback_used"] or row["legacy_parent_fallback_used"]),
        "wrong_parent_source_candidate_count": sum(1 for row in rows if row["parent_source"] != EXPECTED_PARENT_SOURCE),
        "silent_fallback_allowed_candidate_count": sum(1 for row in rows if row["silent_fallback_allowed"]),
        "parent_closed_span_over_12_candidate_count": sum(1 for row in rows if int(row.get("parent_closed_span") or 0) > 12),
        "low_cluster_top_gap_candidate_count": len(bad_low_cluster_rows),
        "retired_4note_grouping_candidate_count": len(retired_grouping_rows),
        "bad_low_cluster_examples": bad_low_cluster_rows[:5],
        "retired_grouping_examples": retired_grouping_rows[:5],
        "inspected_symbols": list(INSPECTED_SYMBOLS),
    }


def _candidate_row(symbol: str, candidate: Any) -> dict[str, Any]:
    metadata = dict(candidate.metadata or {})
    density_recipe = dict(metadata.get("density_recipe") or {})
    notes = [int(note) for note in candidate.notes]
    return {
        "symbol": symbol,
        "notes": notes,
        "intervals": _intervals(notes),
        "density": int(candidate.density or 0),
        "content_family": str(candidate.content_family.value if hasattr(candidate.content_family, "value") else candidate.content_family),
        "disposition": str(candidate.disposition.value if hasattr(candidate.disposition, "value") else candidate.disposition),
        "recipe_id": candidate.recipe_id,
        "functional_grouping": getattr(candidate.functional_grouping, "value", candidate.functional_grouping),
        "density_recipe_functional_grouping": density_recipe.get("functional_grouping"),
        "method": str(metadata.get("active_open_projection_method") or metadata.get("disposition_projection_method") or "unknown"),
        "parent_source": metadata.get("open_named_projection_parent_source"),
        "parent_closed_notes": metadata.get("open_named_projection_parent_closed_notes"),
        "parent_closed_span": metadata.get("open_named_projection_parent_closed_span"),
        "noncompact_parent_fallback_used": bool(metadata.get("open_named_projection_noncompact_parent_fallback_used")),
        "legacy_parent_fallback_used": bool(metadata.get("open_named_projection_legacy_parent_fallback_used")),
        "silent_fallback_allowed": bool(metadata.get("open_named_projection_silent_fallback_allowed")),
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_voicing_listening_checkpoint_demo.mid"
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
    note_counts = dict(debug.get("note_events_by_track") or {})
    rows = [_piano_row(row) for row in list(debug.get("piano_musical_audit_events") or [])]
    rows = [row for row in rows if row]
    method_counts = Counter(row["method"] for row in rows)
    density_counts = Counter(str(row["density"]) for row in rows)
    disposition_counts = Counter(str(row["disposition"]) for row in rows)
    content_counts = Counter(str(row["content_family"]) for row in rows)
    bad_rows = [row for row in rows if _is_low_cluster_top_gap(row["notes"])]
    inspected_rows = [row for row in rows if row["bar"] in INSPECTED_BARS]
    inspected_bad_rows = [row for row in inspected_rows if _is_low_cluster_top_gap(row["notes"])]
    return {
        "ok": bool(result.ok),
        "choruses": choruses,
        "seed": seed,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "title": debug.get("title"),
        "style": debug.get("style"),
        "performance_bars": debug.get("performance_bars"),
        "regions": debug.get("regions"),
        "note_events_by_track": note_counts,
        "piano_notes": int(note_counts.get("piano", 0)),
        "bass_notes": int(note_counts.get("bass", 0)),
        "drums_notes": int(note_counts.get("drums", 0)),
        "piano_harmonic_event_count": len(rows),
        "density_counts": dict(density_counts),
        "disposition_counts": dict(disposition_counts),
        "content_family_counts": dict(content_counts),
        "open_method_counts": dict(method_counts),
        "generic_open_event_count": int(method_counts.get("generic_open", 0)),
        "low_density_event_count": sum(int(count) for density, count in density_counts.items() if density in {"2", "3"}),
        "non_open_event_count": sum(1 for row in rows if row["disposition"] != "open"),
        "retired_4note_grouping_event_count": sum(1 for row in rows if _has_retired_grouping(row)),
        "fallback_parent_event_count": sum(1 for row in rows if row["noncompact_parent_fallback_used"] or row["legacy_parent_fallback_used"]),
        "wrong_parent_source_event_count": sum(1 for row in rows if row["parent_source"] != EXPECTED_PARENT_SOURCE),
        "silent_fallback_allowed_event_count": sum(1 for row in rows if row["silent_fallback_allowed"]),
        "parent_closed_span_over_12_count": sum(1 for row in rows if int(row.get("parent_closed_span") or 0) > 12),
        "low_cluster_top_gap_event_count": len(bad_rows),
        "inspected_bars": list(INSPECTED_BARS),
        "inspected_bar_event_count": len(inspected_rows),
        "inspected_bar_bad_event_count": len(inspected_bad_rows),
        "inspected_bar_examples": inspected_rows[:12],
        "bad_examples": bad_rows[:5],
    }


def _piano_row(row: dict[str, Any]) -> dict[str, Any] | None:
    voicing = dict(row.get("voicing") or {})
    realized = list(row.get("realized_notes") or [])
    if not voicing or not realized:
        return None
    notes = [int(note.get("note")) for note in realized]
    start = float(realized[0].get("start_beat") or 0.0)
    metadata = dict(voicing.get("metadata") or {})
    density_recipe = dict(metadata.get("density_recipe") or {})
    pattern_event = dict(row.get("pattern_event") or {})
    return {
        "bar": int(start // 4) + 1,
        "start_beat": round(start, 3),
        "chord": pattern_event.get("chord_symbol"),
        "pattern_id": pattern_event.get("pattern_id"),
        "notes": notes,
        "intervals": _intervals(notes),
        "span": max(notes) - min(notes) if notes else 0,
        "density": int(voicing.get("density") or 0),
        "content_family": voicing.get("content_family"),
        "disposition": voicing.get("disposition"),
        "recipe_id": voicing.get("recipe_id"),
        "functional_grouping": voicing.get("functional_grouping"),
        "density_recipe_functional_grouping": density_recipe.get("functional_grouping"),
        "method": str(metadata.get("active_open_projection_method") or metadata.get("disposition_projection_method") or "unknown"),
        "parent_source": metadata.get("open_named_projection_parent_source"),
        "parent_closed_notes": metadata.get("open_named_projection_parent_closed_notes"),
        "parent_closed_span": metadata.get("open_named_projection_parent_closed_span"),
        "noncompact_parent_fallback_used": bool(metadata.get("open_named_projection_noncompact_parent_fallback_used")),
        "legacy_parent_fallback_used": bool(metadata.get("open_named_projection_legacy_parent_fallback_used")),
        "silent_fallback_allowed": bool(metadata.get("open_named_projection_silent_fallback_allowed")),
    }


def _intervals(notes: list[int]) -> list[int]:
    return [notes[index + 1] - notes[index] for index in range(len(notes) - 1)]


def _is_low_cluster_top_gap(notes: list[int]) -> bool:
    if len(notes) != 4:
        return False
    intervals = _intervals(notes)
    return intervals[0] <= 2 and intervals[1] <= 2 and intervals[2] >= 10


def _has_retired_grouping(row: dict[str, Any]) -> bool:
    values = {str(row.get("functional_grouping")), str(row.get("density_recipe_functional_grouping"))}
    recipe = str(row.get("recipe_id") or "")
    return bool(values & RETIRED_GROUPINGS) or "1plus3" in recipe or "2plus2" in recipe


def _acceptance(static: dict[str, Any], runtime_audits: list[dict[str, Any]]) -> dict[str, Any]:
    checkpoint = dict(static.get("checkpoint_metadata") or {})
    checks = {
        "policy_declares_checkpoint": checkpoint.get("version") == MILESTONE_ID and checkpoint.get("enabled") is True,
        "checkpoint_is_metadata_only": checkpoint.get("behavior_change") is False and checkpoint.get("no_new_voicing_ability") is True,
        "policy_open_main_drop_family_only": static.get("policy_preferred_disposition") == "open" and static.get("policy_open_projection_methods") == ["drop2", "drop3", "drop2_and_4"],
        "policy_density_4_to_5": static.get("policy_density_range") == [4, 5],
        "static_no_generic_open": int(static.get("generic_open_candidate_count") or 0) == 0,
        "static_no_low_density_candidates": int(static.get("low_density_candidate_count") or 0) == 0,
        "static_no_fallback_or_wrong_parent": int(static.get("fallback_parent_candidate_count") or 0) == 0 and int(static.get("wrong_parent_source_candidate_count") or 0) == 0,
        "static_no_silent_fallback": int(static.get("silent_fallback_allowed_candidate_count") or 0) == 0,
        "static_parent_spans_compact": int(static.get("parent_closed_span_over_12_candidate_count") or 0) == 0,
        "static_no_low_cluster_artifact": int(static.get("low_cluster_top_gap_candidate_count") or 0) == 0,
        "static_no_retired_grouping": int(static.get("retired_4note_grouping_candidate_count") or 0) == 0,
        "runtime_demos_ok": bool(runtime_audits) and all(audit.get("ok") is True for audit in runtime_audits),
        "runtime_open_only": bool(runtime_audits) and all(int(audit.get("non_open_event_count") or 0) == 0 for audit in runtime_audits),
        "runtime_no_generic_open": bool(runtime_audits) and all(int(audit.get("generic_open_event_count") or 0) == 0 for audit in runtime_audits),
        "runtime_no_low_density": bool(runtime_audits) and all(int(audit.get("low_density_event_count") or 0) == 0 for audit in runtime_audits),
        "runtime_no_retired_grouping": bool(runtime_audits) and all(int(audit.get("retired_4note_grouping_event_count") or 0) == 0 for audit in runtime_audits),
        "runtime_no_fallback_or_wrong_parent": bool(runtime_audits) and all(int(audit.get("fallback_parent_event_count") or 0) == 0 and int(audit.get("wrong_parent_source_event_count") or 0) == 0 for audit in runtime_audits),
        "runtime_parent_spans_compact": bool(runtime_audits) and all(int(audit.get("parent_closed_span_over_12_count") or 0) == 0 for audit in runtime_audits),
        "runtime_no_low_cluster_artifact": bool(runtime_audits) and all(int(audit.get("low_cluster_top_gap_event_count") or 0) == 0 and int(audit.get("inspected_bar_bad_event_count") or 0) == 0 for audit in runtime_audits),
    }
    return {"passed": all(checks.values()), "checks": checks}


def _render_report(summary: dict[str, Any]) -> str:
    static = summary["static_audit"]
    lines = [
        f"# {MILESTONE_LABEL}",
        "",
        f"- Engine version tag: `{summary.get('engine_version_tag')}`",
        f"- Acceptance passed: `{summary['acceptance']['passed']}`",
        "",
        "## Scope",
        "",
        str(summary.get("scope")),
        "",
        "## Static audit",
        "",
        f"- Policy disposition: `{static.get('policy_preferred_disposition')}`",
        f"- Policy density range: `{static.get('policy_density_range')}`",
        f"- Policy open methods: `{static.get('policy_open_projection_methods')}`",
        f"- Candidate count: `{static.get('candidate_count')}`",
        f"- Method counts: `{static.get('method_counts')}`",
        f"- Density counts: `{static.get('density_counts')}`",
        f"- Generic-open candidates: `{static.get('generic_open_candidate_count')}`",
        f"- Low-density candidates: `{static.get('low_density_candidate_count')}`",
        f"- Fallback/wrong-parent candidates: `{static.get('fallback_parent_candidate_count')}` / `{static.get('wrong_parent_source_candidate_count')}`",
        f"- Low-cluster/top-gap candidates: `{static.get('low_cluster_top_gap_candidate_count')}`",
        f"- Retired grouping candidates: `{static.get('retired_4note_grouping_candidate_count')}`",
        "",
        "## Runtime audits",
        "",
    ]
    for audit in summary.get("runtime_audits", []):
        lines.extend(
            [
                f"### {audit.get('choruses')}x — seed {audit.get('seed')}",
                "",
                f"- MIDI: `{audit.get('midi_path')}`",
                f"- Notes piano/bass/drums: `{audit.get('piano_notes')}` / `{audit.get('bass_notes')}` / `{audit.get('drums_notes')}`",
                f"- Piano harmonic events: `{audit.get('piano_harmonic_event_count')}`",
                f"- Dispositions: `{audit.get('disposition_counts')}`",
                f"- Open methods: `{audit.get('open_method_counts')}`",
                f"- Densities: `{audit.get('density_counts')}`",
                f"- Content families: `{audit.get('content_family_counts')}`",
                f"- Generic-open events: `{audit.get('generic_open_event_count')}`",
                f"- Low-density events: `{audit.get('low_density_event_count')}`",
                f"- Retired grouping events: `{audit.get('retired_4note_grouping_event_count')}`",
                f"- Fallback/wrong-parent events: `{audit.get('fallback_parent_event_count')}` / `{audit.get('wrong_parent_source_event_count')}`",
                f"- Low-cluster/top-gap events: `{audit.get('low_cluster_top_gap_event_count')}`",
                f"- Inspected bars bad events: `{audit.get('inspected_bar_bad_event_count')}`",
                "",
            ]
        )
    lines.extend([
        "## Acceptance",
        "",
        "```json",
        json.dumps(summary.get("acceptance"), indent=2, ensure_ascii=False),
        "```",
        "",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    main()
