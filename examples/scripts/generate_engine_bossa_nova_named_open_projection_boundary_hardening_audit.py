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
MILESTONE_ID = "v2_6_111"
MILESTONE_LABEL = "v2_6_111 — Engine Bossa Nova Drop-Family Closed-Parent Projection Fix"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 23110, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 23111, "slug": "blue_bossa_5x"},
)
INSPECTED_BARS = (14, 19, 29)
INSPECTED_SYMBOLS = ("G7b9", "Fm7", "Dm7b5", "Cm7")


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    runtime_audits = [_generate_runtime_audit(spec) for spec in DEMO_SPECS]
    summary = {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "scope": (
            "Fix named OPEN drop-family projection wiring so DROP2/DROP3/DROP2&4 project from true compact CLOSED parents, "
            "not from already-open runtime closed variants. This retires the low-cluster/top-gap artifact heard in Bossa bars such as 14/19/29 without adding a new voicing ability."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
    }
    summary["acceptance"] = _acceptance(static_audit, runtime_audits)
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_named_open_projection_boundary_hardening_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_named_open_projection_boundary_hardening_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    policy = voicing_policy.get_voicing_policy()
    candidate_rows: list[dict[str, Any]] = []
    bad_parent_rows: list[dict[str, Any]] = []
    bad_low_cluster_rows: list[dict[str, Any]] = []
    method_counts: Counter[str] = Counter()
    for symbol in INSPECTED_SYMBOLS:
        for candidate in generate_candidates(symbol, policy):
            if candidate.disposition != Disposition.OPEN:
                continue
            metadata = dict(candidate.metadata or {})
            method = str(metadata.get("disposition_projection_method") or "unknown")
            method_counts[method] += 1
            notes = [int(note) for note in candidate.notes]
            intervals = _intervals(notes)
            parent_notes = [int(note) for note in metadata.get("open_named_projection_parent_closed_notes") or []]
            parent_span = int(metadata.get("open_named_projection_parent_closed_span") or 0)
            row = {
                "symbol": symbol,
                "method": method,
                "notes": notes,
                "intervals": intervals,
                "parent_closed_notes": parent_notes,
                "parent_closed_span": parent_span,
                "parent_source": metadata.get("open_named_projection_parent_source"),
                "noncompact_parent_fallback_used": bool(metadata.get("open_named_projection_noncompact_parent_fallback_used")),
                "legacy_parent_fallback_used": bool(metadata.get("open_named_projection_legacy_parent_fallback_used")),
                "silent_fallback_allowed": bool(metadata.get("open_named_projection_silent_fallback_allowed")),
                "content_family": str(candidate.content_family.value if hasattr(candidate.content_family, "value") else candidate.content_family),
                "recipe_id": candidate.recipe_id,
            }
            candidate_rows.append(row)
            if parent_span > 12:
                bad_parent_rows.append(row)
            if _is_low_cluster_top_gap(notes):
                bad_low_cluster_rows.append(row)
    fallback_rows = [row for row in candidate_rows if row.get("noncompact_parent_fallback_used") or row.get("legacy_parent_fallback_used")]
    wrong_parent_source_rows = [row for row in candidate_rows if row.get("parent_source") != "compact_closed_parent_candidates_for_projection"]
    silent_fallback_rows = [row for row in candidate_rows if row.get("silent_fallback_allowed")]
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "policy_preferred_disposition": policy.preferred_disposition.value,
        "policy_open_projection_methods": list((policy.metadata or {}).get("open_projection_methods") or []),
        "method_counts": dict(method_counts),
        "candidate_count": len(candidate_rows),
        "bad_parent_span_count": len(bad_parent_rows),
        "bad_low_cluster_candidate_count": len(bad_low_cluster_rows),
        "fallback_parent_count": len(fallback_rows),
        "wrong_parent_source_count": len(wrong_parent_source_rows),
        "silent_fallback_allowed_count": len(silent_fallback_rows),
        "bad_parent_examples": bad_parent_rows[:5],
        "bad_low_cluster_examples": bad_low_cluster_rows[:5],
        "fallback_parent_examples": fallback_rows[:5],
        "wrong_parent_source_examples": wrong_parent_source_rows[:5],
        "inspected_symbols": list(INSPECTED_SYMBOLS),
        "no_new_voicing_ability": True,
        "hardening_location": "core/voicing/selection/candidate_generator.py::_project_closed_parent_candidates_for_named_open_projection",
        "hardening_contract": "named OPEN methods use only compact_closed_parent_candidates_for_projection; non-compact legacy parent fallback is disabled by default and must not appear silently in ordinary runtime",
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_named_open_projection_boundary_hardening_demo.mid"
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
    rows = list(debug.get("piano_musical_audit_events") or [])
    piano_rows = [_piano_row(row) for row in rows if _piano_row(row)]
    bad_rows = [row for row in piano_rows if _is_low_cluster_top_gap(row["notes"])]
    inspected_rows = [row for row in piano_rows if row["bar"] in INSPECTED_BARS]
    inspected_bad_rows = [row for row in inspected_rows if _is_low_cluster_top_gap(row["notes"])]
    method_counts = Counter(row.get("method") or "unknown" for row in piano_rows)
    parent_spans = [int(row.get("parent_closed_span") or 0) for row in piano_rows if row.get("parent_closed_span") is not None]
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
        "piano_harmonic_event_count": len(piano_rows),
        "open_method_counts": dict(method_counts),
        "generic_open_event_count": int(method_counts.get("generic_open", 0)),
        "low_cluster_top_gap_event_count": len(bad_rows),
        "inspected_bars": list(INSPECTED_BARS),
        "inspected_bar_event_count": len(inspected_rows),
        "inspected_bar_bad_event_count": len(inspected_bad_rows),
        "inspected_bar_examples": inspected_rows[:12],
        "bad_examples": bad_rows[:5],
        "max_parent_closed_span": max(parent_spans or [0]),
        "parent_closed_span_over_12_count": sum(1 for value in parent_spans if value > 12),
        "fallback_parent_event_count": sum(1 for row in piano_rows if row.get("noncompact_parent_fallback_used") or row.get("legacy_parent_fallback_used")),
        "wrong_parent_source_event_count": sum(1 for row in piano_rows if row.get("parent_source") != "compact_closed_parent_candidates_for_projection"),
        "silent_fallback_allowed_event_count": sum(1 for row in piano_rows if row.get("silent_fallback_allowed")),
    }


def _piano_row(row: dict[str, Any]) -> dict[str, Any] | None:
    realized = list(row.get("realized_notes") or [])
    if not realized:
        return None
    notes = [int(note.get("note")) for note in realized]
    start = float(realized[0].get("start_beat") or 0.0)
    voicing = dict(row.get("voicing") or {})
    metadata = dict(voicing.get("metadata") or {})
    pattern_event = dict(row.get("pattern_event") or {})
    return {
        "bar": int(start // 4) + 1,
        "start_beat": round(start, 3),
        "chord": pattern_event.get("chord_symbol"),
        "pattern_id": pattern_event.get("pattern_id"),
        "notes": notes,
        "intervals": _intervals(notes),
        "span": max(notes) - min(notes) if notes else 0,
        "method": metadata.get("active_open_projection_method") or metadata.get("disposition_projection_method"),
        "parent_closed_notes": metadata.get("open_named_projection_parent_closed_notes"),
        "parent_closed_span": metadata.get("open_named_projection_parent_closed_span"),
        "parent_source": metadata.get("open_named_projection_parent_source"),
        "noncompact_parent_fallback_used": bool(metadata.get("open_named_projection_noncompact_parent_fallback_used")),
        "legacy_parent_fallback_used": bool(metadata.get("open_named_projection_legacy_parent_fallback_used")),
        "silent_fallback_allowed": bool(metadata.get("open_named_projection_silent_fallback_allowed")),
        "degrees": voicing.get("degrees"),
        "content_family": voicing.get("content_family"),
        "disposition": voicing.get("disposition"),
    }


def _intervals(notes: list[int]) -> list[int]:
    return [notes[index + 1] - notes[index] for index in range(len(notes) - 1)]


def _is_low_cluster_top_gap(notes: list[int]) -> bool:
    if len(notes) != 4:
        return False
    intervals = _intervals(notes)
    # Captures the audible artifact reported by the user: three low notes packed
    # into adjacent/near-adjacent semitones plus one high top note.
    return intervals[0] <= 2 and intervals[1] <= 2 and intervals[2] >= 10


def _acceptance(static: dict[str, Any], runtime_audits: list[dict[str, Any]]) -> dict[str, Any]:
    checks = {
        "static_drop_parents_are_compact": int(static.get("bad_parent_span_count") or 0) == 0,
        "static_no_low_cluster_candidates": int(static.get("bad_low_cluster_candidate_count") or 0) == 0,
        "runtime_demos_ok": bool(runtime_audits) and all(audit.get("ok") is True for audit in runtime_audits),
        "runtime_no_low_cluster_top_gap": bool(runtime_audits) and all(int(audit.get("low_cluster_top_gap_event_count") or 0) == 0 for audit in runtime_audits),
        "runtime_inspected_bars_clean": bool(runtime_audits) and all(int(audit.get("inspected_bar_bad_event_count") or 0) == 0 for audit in runtime_audits),
        "runtime_no_generic_open": bool(runtime_audits) and all(int(audit.get("generic_open_event_count") or 0) == 0 for audit in runtime_audits),
        "runtime_parent_spans_compact": bool(runtime_audits) and all(int(audit.get("parent_closed_span_over_12_count") or 0) == 0 for audit in runtime_audits),
        "static_no_fallback_parent_candidates": int(static.get("fallback_parent_count") or 0) == 0,
        "static_parent_sources_are_compact_helper": int(static.get("wrong_parent_source_count") or 0) == 0,
        "static_no_silent_fallback_allowed": int(static.get("silent_fallback_allowed_count") or 0) == 0,
        "runtime_no_fallback_parent_candidates": bool(runtime_audits) and all(int(audit.get("fallback_parent_event_count") or 0) == 0 for audit in runtime_audits),
        "runtime_parent_sources_are_compact_helper": bool(runtime_audits) and all(int(audit.get("wrong_parent_source_event_count") or 0) == 0 for audit in runtime_audits),
        "runtime_no_silent_fallback_allowed": bool(runtime_audits) and all(int(audit.get("silent_fallback_allowed_event_count") or 0) == 0 for audit in runtime_audits),
    }
    return {"passed": all(checks.values()), "checks": checks}


def _render_report(summary: dict[str, Any]) -> str:
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
        f"- Candidate count: `{summary['static_audit'].get('candidate_count')}`",
        f"- Method counts: `{summary['static_audit'].get('method_counts')}`",
        f"- Bad parent span count: `{summary['static_audit'].get('bad_parent_span_count')}`",
        f"- Bad low-cluster candidate count: `{summary['static_audit'].get('bad_low_cluster_candidate_count')}`",
        f"- Fallback parent count: `{summary['static_audit'].get('fallback_parent_count')}`",
        f"- Wrong parent-source count: `{summary['static_audit'].get('wrong_parent_source_count')}`",
        "",
        "## Runtime audits",
        "",
    ]
    for audit in summary.get("runtime_audits", []):
        lines.extend(
            [
                f"### Blue Bossa {audit.get('choruses')}x",
                "",
                f"- MIDI: `{audit.get('midi_path')}`",
                f"- Piano / bass / drums notes: `{audit.get('piano_notes')} / {audit.get('bass_notes')} / {audit.get('drums_notes')}`",
                f"- Open methods: `{audit.get('open_method_counts')}`",
                f"- Generic open events: `{audit.get('generic_open_event_count')}`",
                f"- Low-cluster/top-gap events: `{audit.get('low_cluster_top_gap_event_count')}`",
                f"- Inspected bar bad events: `{audit.get('inspected_bar_bad_event_count')}`",
                f"- Max parent closed span: `{audit.get('max_parent_closed_span')}`",
                f"- Fallback parent events: `{audit.get('fallback_parent_event_count')}`",
                f"- Wrong parent-source events: `{audit.get('wrong_parent_source_event_count')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Acceptance checks",
            "",
            "```json",
            json.dumps(summary.get("acceptance"), indent=2, ensure_ascii=False),
            "```",
            "",
            "Recommended next task: `v2_6_112_engine_bossa_nova_voicing_listening_checkpoint_or_continue_bass_drums`." ,
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
