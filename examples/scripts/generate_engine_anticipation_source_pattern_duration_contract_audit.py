from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.anticipation import AnticipationPolicy, AnticipationResolver
from jammate_engine.core.expression import ArticulationKind, ExpressionPolicyBundle, ExpressionProfile, ExpressionResolver
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime import Beat1Movability, PatternCandidate, TailPolicy, event_spec
from jammate_engine.runtime.generate import generate_accompaniment

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_113"
MILESTONE_LABEL = "v2_6_113 — Anticipation Source-Pattern Duration Contract"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 23114, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 23115, "slug": "blue_bossa_5x"},
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_probe()
    runtime_audits = [_generate_runtime_audit(spec) for spec in DEMO_SPECS]
    summary = {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "scope": (
            "First-principles anticipation duration fix: a next-region beat-1 event moved to the previous tail keeps "
            "the suppressed source event's original continuation target, such as source beat 1 -> source 3&, instead of "
            "being shortened to a generic post-downbeat cap. This is a shared AnticipationResolver / ExpressionResolver contract, "
            "not a Bossa-specific patch."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
    }
    summary["acceptance"] = _acceptance(static_audit, runtime_audits)
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_anticipation_source_pattern_duration_contract_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_anticipation_source_pattern_duration_contract_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def _region(region_id: str, chord: str, start: float, duration: float) -> HarmonicRegion:
    return HarmonicRegion(
        region_id=region_id,
        chord_symbol=chord,
        next_chord_symbol=None,
        chorus_index=0,
        total_choruses=1,
        bar_index=int(start // 4),
        chord_index=0,
        start_beat=start,
        duration_beats=duration,
        source_bar_index=int(start // 4),
        performance_bar_index=int(start // 4),
    )


def _expression_policy() -> ExpressionPolicyBundle:
    return ExpressionPolicyBundle(
        profiles={
            "soft_hold": ExpressionProfile(
                name="soft_hold",
                duration_beats=0.8,
                velocity=50,
                articulation=ArticulationKind.SUSTAIN,
                metadata={"duration_semantics": "hold_until_next_touch"},
            ),
            "short": ExpressionProfile(
                name="short",
                duration_beats=0.45,
                velocity=56,
                articulation=ArticulationKind.SHORT,
            ),
        },
        default_profile="soft_hold",
        track_default_profiles={"piano": "soft_hold"},
    )


def _probe(first_hint: str) -> dict[str, Any]:
    prev_region = _region("prev", "Dm7", 0.0, 4.0)
    next_region = _region("next", "G7", 4.0, 4.0)
    previous = PatternCandidate(
        name="prev_tail_free",
        weight=1.0,
        category="test",
        events=(event_spec(track="piano", beat=0.0, role="harmonic"),),
        tail_policy=TailPolicy.from_local_beats((0.0,)),
    ).instantiate(prev_region)
    source = PatternCandidate(
        name="source_beat1_to_3and",
        weight=1.0,
        category="test",
        events=(
            event_spec(track="piano", beat=0.0, role="harmonic", expression_hint=first_hint),
            event_spec(track="piano", beat=3.5, role="harmonic", expression_hint="short"),
        ),
        beat1_movability=Beat1Movability(movable=True),
    ).instantiate(next_region)
    rewritten = AnticipationResolver().resolve(
        list(previous.events) + list(source.events),
        AnticipationPolicy(enabled=True, probability=1.0, debug_name="source_duration_probe"),
        random.Random(1),
        regions=(prev_region, next_region),
        region_plans={prev_region.region_id: previous, next_region.region_id: source},
    )
    anticipated = next(event for event in rewritten if event.event_id.endswith("__anticipated_from_previous"))
    expression = ExpressionResolver().resolve(rewritten, _expression_policy()).events[anticipated.event_id]
    anticipation = dict(anticipated.metadata.get("anticipation") or {})
    return {
        "first_hint": first_hint,
        "anticipated_onset": anticipated.onset_beat,
        "original_onset": anticipation.get("original_onset_beat"),
        "source_continuation_contract_version": anticipation.get("source_continuation_contract_version"),
        "source_continuation_target_kind": anticipation.get("source_continuation_target_kind"),
        "source_next_same_track_gap_beats": anticipation.get("source_next_same_track_gap_beats"),
        "lead_in_beats": anticipation.get("lead_in_beats"),
        "duration_beats": expression.duration_beats,
        "duration_anticipation_original_sustain_beats": expression.metadata.get("duration_anticipation_original_sustain_beats"),
        "duration_anticipation_source_continuation_applied": expression.metadata.get("duration_anticipation_source_continuation_applied"),
        "duration_anticipation_source_continuation_reason": expression.metadata.get("duration_anticipation_source_continuation_reason"),
        "duration_anticipation_micro_tuning_reason": expression.metadata.get("duration_anticipation_micro_tuning_reason"),
    }


def build_static_probe() -> dict[str, Any]:
    hold = _probe("soft_hold")
    short = _probe("short")
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "hold_probe": hold,
        "short_probe": short,
        "hold_expected_duration_beats": 4.0,
        "short_expected_duration_beats": 0.95,
        "first_principles_contract": (
            "Anticipation moves the logical event onset, not its source-pattern continuation endpoint. "
            "Hold-style source beat-1 events use lead-in + source next-touch/source-region-end gap; fixed short events keep fixed short duration."
        ),
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_anticipation_source_pattern_duration_contract_demo.mid"
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
    rows = [_anticipation_row(row) for row in list(debug.get("piano_musical_audit_events") or [])]
    rows = [row for row in rows if row]
    continuation_rows = [row for row in rows if row["source_continuation_applied"]]
    mismatch_rows = [
        row
        for row in continuation_rows
        if row["source_continuation_target_kind"] == "next_same_track_touch"
        and abs(float(row["duration_beats"]) - float(row["expected_duration_beats"])) > 1e-6
    ]
    cap_rows = [row for row in continuation_rows if str(row.get("micro_tuning_reason")) == "bossa_clean_post_downbeat_release_cap"]
    short_rows = [row for row in rows if not row["source_continuation_applied"]]
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
        "anticipated_piano_event_count": len(rows),
        "source_continuation_applied_count": len(continuation_rows),
        "source_next_touch_count": sum(1 for row in rows if row["source_continuation_target_kind"] == "next_same_track_touch"),
        "source_region_end_count": sum(1 for row in rows if row["source_continuation_target_kind"] == "source_region_end"),
        "next_touch_continuation_mismatch_count": len(mismatch_rows),
        "source_region_end_rows_may_be_next_event_clamped": sum(1 for row in continuation_rows if row["source_continuation_target_kind"] == "source_region_end"),
        "continuation_micro_cap_count": len(cap_rows),
        "non_continuation_short_or_fixed_count": len(short_rows),
        "max_source_continuation_gap_beats": max([float(row["source_continuation_gap_beats"] or 0.0) for row in rows] or [0.0]),
        "max_duration_beats": max([float(row["duration_beats"] or 0.0) for row in rows] or [0.0]),
        "examples": rows[:10],
        "mismatch_examples": mismatch_rows[:5],
        "cap_examples": cap_rows[:5],
    }


def _anticipation_row(row: dict[str, Any]) -> dict[str, Any] | None:
    pattern_event = dict(row.get("pattern_event") or {})
    metadata = dict(pattern_event.get("metadata") or {})
    anticipation = dict(metadata.get("anticipation") or {})
    if anticipation.get("kind") != "next_beat1_to_previous_tail":
        return None
    expression = dict(row.get("expression") or {})
    expression_metadata = dict(expression.get("metadata") or {})
    lead_in = float(anticipation.get("lead_in_beats") or 0.0)
    source_gap = anticipation.get("source_continuation_gap_beats")
    applied = bool(expression_metadata.get("duration_anticipation_source_continuation_applied"))
    expected = None
    if applied and source_gap is not None:
        expected = round(lead_in + float(source_gap), 6)
    return {
        "event_id": pattern_event.get("event_id"),
        "pattern_id": pattern_event.get("pattern_id"),
        "chord": pattern_event.get("chord_symbol"),
        "onset_beat": pattern_event.get("onset_beat"),
        "lead_in_beats": lead_in,
        "source_continuation_contract_version": anticipation.get("source_continuation_contract_version"),
        "source_continuation_target_kind": anticipation.get("source_continuation_target_kind"),
        "source_continuation_gap_beats": source_gap,
        "source_next_same_track_gap_beats": anticipation.get("source_next_same_track_gap_beats"),
        "source_continuation_applied": applied,
        "expected_duration_beats": expected,
        "duration_beats": expression.get("duration_beats"),
        "original_sustain_beats": expression_metadata.get("duration_anticipation_original_sustain_beats"),
        "source_continuation_reason": expression_metadata.get("duration_anticipation_source_continuation_reason"),
        "micro_tuning_reason": expression_metadata.get("duration_anticipation_micro_tuning_reason"),
        "profile_name": expression.get("profile_name"),
    }


def _acceptance(static: dict[str, Any], runtimes: list[dict[str, Any]]) -> dict[str, Any]:
    checks = {
        "static_hold_probe_preserves_source_3and_target": abs(float(static["hold_probe"]["duration_beats"]) - 4.0) <= 1e-6,
        "static_short_probe_remains_short": abs(float(static["short_probe"]["duration_beats"]) - 0.95) <= 1e-6,
        "static_contract_metadata_present": static["hold_probe"]["source_continuation_contract_version"] == MILESTONE_ID,
        "runtime_blue_bossa_generated": all(runtime["ok"] for runtime in runtimes),
        "runtime_has_anticipations": all(runtime["anticipated_piano_event_count"] > 0 for runtime in runtimes),
        "runtime_has_source_continuation_rows": all(runtime["source_continuation_applied_count"] > 0 for runtime in runtimes),
        "runtime_next_touch_continuation_matches_expected_duration": all(runtime["next_touch_continuation_mismatch_count"] == 0 for runtime in runtimes),
        "runtime_source_continuation_not_micro_capped": all(runtime["continuation_micro_cap_count"] == 0 for runtime in runtimes),
    }
    return {"checks": checks, "passed": all(checks.values())}


def _render_report(summary: dict[str, Any]) -> str:
    lines = [
        f"# {MILESTONE_LABEL}",
        "",
        f"Engine version: `{summary['engine_version_tag']}`",
        "",
        "## Scope",
        "",
        summary["scope"],
        "",
        "## Static probes",
        "",
        "```json",
        json.dumps(summary["static_audit"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Runtime audits",
        "",
    ]
    for runtime in summary["runtime_audits"]:
        lines.extend(
            [
                f"### Blue Bossa {runtime['choruses']}x",
                "",
                f"- MIDI: `{runtime['midi_path']}`",
                f"- Piano/bass/drums notes: {runtime['piano_notes']} / {runtime['bass_notes']} / {runtime['drums_notes']}",
                f"- Anticipated piano events: {runtime['anticipated_piano_event_count']}",
                f"- Source-continuation applied: {runtime['source_continuation_applied_count']}",
                f"- Next-touch continuation mismatches: {runtime['next_touch_continuation_mismatch_count']}",
                f"- Continuation micro-cap count: {runtime['continuation_micro_cap_count']}",
                "",
            ]
        )
    lines.extend(["## Acceptance", "", "```json", json.dumps(summary["acceptance"], indent=2, ensure_ascii=False), "```", ""])
    return "\n".join(lines)


if __name__ == "__main__":
    main()
