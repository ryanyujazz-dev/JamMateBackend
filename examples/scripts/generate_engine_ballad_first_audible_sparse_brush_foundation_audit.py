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
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad import arrangement_policy, percussion_patterns

DEMOS_DIR = PROJECT_ROOT / "demos"
LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
MILESTONE_ID = "v2_6_128"
MILESTONE_LABEL = "v2_6_128 — Engine Ballad First Audible Sparse Brush Foundation"


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static = _static_audit()
    runtime = _generate_misty_runtime_audit()
    acceptance = _acceptance(static, runtime)
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": (
            "Consume the v2_6_127 Jazz Ballad brush semantic policy and add the first very sparse audible brush texture. "
            "The change stays inside the existing Jazz Ballad percussion owner plus shared percussion voice mapping; it does not add a fixed loop, "
            "swing ride, rock backbeat, new drum engine, piano/bass/voicing change, API, Agent, or HarmonyOS change."
        ),
        "static_audit": static,
        "runtime_audit": runtime,
        "acceptance": acceptance,
        "recommended_next_task": "v2_6_129_engine_ballad_phrase_breath_brush_markers",
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_ballad_first_audible_sparse_brush_foundation_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_ballad_first_audible_sparse_brush_foundation_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def _candidate_debug(context: dict[str, Any]) -> dict[str, Any]:
    context = {**dict(context), "jazz_ballad_first_audible_sparse_brush_foundation_active": True}
    candidates = percussion_patterns.get_pattern_candidates(context)
    if not candidates:
        return {"candidate_count": 0, "events": [], "metadata": {}}
    candidate = candidates[0]
    return {
        "candidate_count": len(candidates),
        "name": candidate.name,
        "category": candidate.category,
        "events": [
            {
                "beat": float(event.local_beat),
                "role": event.role,
                "drum": event.metadata.get("drum"),
                "dynamic_profile": event.metadata.get("dynamic_profile"),
                "stroke_profile": event.metadata.get("stroke_profile"),
                "slot": event.metadata.get("jazz_ballad_brush_event_slot"),
            }
            for event in candidate.events
        ],
        "metadata": dict(candidate.metadata),
    }


def _static_audit() -> dict[str, Any]:
    ordinary_context = {"region_duration_beats": 4.0, "region_source_bar_index": 4, "region_chorus_index": 0, "region_total_choruses": 3}
    phrase_tail_context = {"region_duration_beats": 4.0, "region_source_bar_index": 7, "region_chorus_index": 0, "region_total_choruses": 3}
    short_context = {"region_duration_beats": 2.0, "region_source_bar_index": 1, "region_chorus_index": 0, "region_total_choruses": 3}
    final_context = {"region_duration_beats": 4.0, "region_source_bar_index": 31, "region_chorus_index": 2, "region_total_choruses": 3, "region_is_last_bar_of_chorus": True}
    policy = arrangement_policy.get_arrangement_policy()
    return {
        "semantic_policy_version": percussion_patterns.JAZZ_BALLAD_BRUSH_SEMANTIC_POLICY_VERSION,
        "audible_foundation_version": percussion_patterns.JAZZ_BALLAD_FIRST_AUDIBLE_SPARSE_BRUSH_VERSION,
        "arrangement_policy_active": policy.get("jazz_ballad_first_audible_sparse_brush_foundation_active"),
        "arrangement_policy_version": policy.get("jazz_ballad_first_audible_sparse_brush_foundation_version"),
        "ordinary_candidate": _candidate_debug(ordinary_context),
        "phrase_tail_candidate": _candidate_debug(phrase_tail_context),
        "short_region_candidate": _candidate_debug(short_context),
        "final_release_candidate": _candidate_debug(final_context),
        "no_fixed_loop": policy.get("jazz_ballad_brush_semantic_policy_no_fixed_loop"),
        "no_swing_ride": policy.get("jazz_ballad_brush_semantic_policy_no_swing_ride"),
        "no_rock_backbeat": policy.get("jazz_ballad_brush_semantic_policy_no_rock_backbeat"),
    }


def _generate_misty_runtime_audit() -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / "misty.json").read_text(encoding="utf-8"))
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_misty_jazz_ballad_first_audible_sparse_brush_foundation_demo.mid"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "jazz_ballad",
            "tempo": int(score.get("tempo", 72)),
            "choruses": 3,
            "seed": 1260,
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
        }
    )
    debug = dict(result.debug)
    rows = debug.get("piano_musical_audit_events") or []
    region_contexts = _region_contexts_from_piano_rows(rows)
    decisions = [percussion_patterns.build_brush_semantic_policy_decision(context) for context in region_contexts]
    candidate_debugs = [_candidate_debug(context) for context in region_contexts]
    audible_candidates = [item for item in candidate_debugs if int(item.get("candidate_count") or 0) > 0]
    event_rows = [event for item in audible_candidates for event in item.get("events", [])]
    return {
        "ok": bool(result.ok),
        "title": debug.get("title"),
        "style": debug.get("style"),
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "performance_choruses": debug.get("performance_choruses"),
        "performance_bars": debug.get("performance_bars"),
        "regions": debug.get("regions"),
        "audited_region_count": len(decisions),
        "note_events_by_track": dict(debug.get("note_events_by_track") or {}),
        "drum_note_events": int((debug.get("note_events_by_track") or {}).get("drums", 0) or 0),
        "expected_brush_pattern_event_count": len(event_rows),
        "audible_candidate_count": len(audible_candidates),
        "brush_texture_counts": dict(Counter(str(item.get("brush_texture_intent")) for item in decisions)),
        "brush_phrase_breath_counts": dict(Counter(str(item.get("brush_phrase_breath_intent")) for item in decisions)),
        "brush_candidate_texture_counts": dict(Counter(str(item.get("metadata", {}).get("brush_texture_intent")) for item in audible_candidates)),
        "brush_event_drum_counts": dict(Counter(str(item.get("drum")) for item in event_rows)),
        "brush_event_dynamic_counts": dict(Counter(str(item.get("dynamic_profile")) for item in event_rows)),
        "sample_candidates": audible_candidates[:8],
    }


def _region_contexts_from_piano_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_region: dict[str, dict[str, Any]] = {}
    for row in rows:
        event = row.get("pattern_event") if isinstance(row, dict) else None
        if not isinstance(event, dict):
            continue
        metadata = event.get("metadata") if isinstance(event.get("metadata"), dict) else {}
        region_id = str(event.get("region_id") or "")
        if not region_id or region_id in by_region:
            continue
        by_region[region_id] = {
            "region_duration_beats": metadata.get("region_duration_beats"),
            "region_source_bar_index": metadata.get("region_source_bar_index"),
            "region_performance_bar_index": metadata.get("region_performance_bar_index"),
            "region_chorus_index": metadata.get("region_chorus_index"),
            "region_total_choruses": metadata.get("region_total_choruses"),
            "region_is_first_bar_of_section": metadata.get("region_is_first_bar_of_section"),
            "region_is_last_bar_of_section": metadata.get("region_is_last_bar_of_section"),
            "region_is_last_bar_of_chorus": metadata.get("region_is_last_bar_of_chorus"),
            "phrase_role": metadata.get("region_phrase"),
        }
    return list(by_region.values())


def _acceptance(static: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
    ordinary = static.get("ordinary_candidate") or {}
    phrase_tail = static.get("phrase_tail_candidate") or {}
    short_region = static.get("short_region_candidate") or {}
    final_release = static.get("final_release_candidate") or {}
    note_counts = runtime.get("note_events_by_track") or {}
    checks = {
        "versions_declared": static.get("semantic_policy_version") == "v2_6_127" and static.get("audible_foundation_version") == MILESTONE_ID and static.get("arrangement_policy_version") == MILESTONE_ID,
        "ordinary_sparse_brush_audible": ordinary.get("candidate_count") == 1 and len(ordinary.get("events") or []) == 2 and (ordinary.get("metadata") or {}).get("brush_texture_intent") == "circular_sparse",
        "short_regions_still_silent": short_region.get("candidate_count") == 0,
        "phrase_and_release_are_contextual": phrase_tail.get("candidate_count") == 1 and final_release.get("candidate_count") == 1,
        "misty_generates_sparse_drums": runtime.get("ok") is True and 20 <= int(runtime.get("drum_note_events") or 0) <= 90,
        "piano_and_bass_unchanged_present": int(note_counts.get("piano", 0) or 0) > 0 and int(note_counts.get("bass", 0) or 0) > 0,
        "expected_and_runtime_drum_counts_match": int(runtime.get("expected_brush_pattern_event_count") or -1) == int(runtime.get("drum_note_events") or -2),
        "no_generic_loop_contract": static.get("no_fixed_loop") is True and static.get("no_swing_ride") is True and static.get("no_rock_backbeat") is True,
    }
    return {"passed": all(checks.values()), "checks": checks}


def _render_report(summary: dict[str, Any]) -> str:
    static = summary["static_audit"]
    runtime = summary["runtime_audit"]
    acceptance = summary["acceptance"]
    lines = [
        f"# {MILESTONE_LABEL}",
        "",
        f"Engine version tag: `{summary['contract_version']}`",
        "",
        "## Scope",
        "",
        str(summary["scope"]),
        "",
        "## Static audit",
        "",
        f"- Semantic policy version: `{static.get('semantic_policy_version')}`",
        f"- Audible foundation version: `{static.get('audible_foundation_version')}`",
        f"- Arrangement policy active/version: `{static.get('arrangement_policy_active')}` / `{static.get('arrangement_policy_version')}`",
        f"- Ordinary candidate: `{static.get('ordinary_candidate')}`",
        f"- Phrase-tail candidate: `{static.get('phrase_tail_candidate')}`",
        f"- Final-release candidate: `{static.get('final_release_candidate')}`",
        "",
        "## Misty runtime audit",
        "",
        f"- MIDI: `{runtime.get('midi_path')}`",
        f"- Note events by track: `{runtime.get('note_events_by_track')}`",
        f"- Audible candidate count: `{runtime.get('audible_candidate_count')}`",
        f"- Expected brush pattern events: `{runtime.get('expected_brush_pattern_event_count')}`",
        f"- Brush candidate texture counts: `{runtime.get('brush_candidate_texture_counts')}`",
        f"- Brush event drum counts: `{runtime.get('brush_event_drum_counts')}`",
        f"- Brush event dynamic counts: `{runtime.get('brush_event_dynamic_counts')}`",
        "",
        "## Acceptance",
        "",
        f"Passed: `{acceptance.get('passed')}`",
        "",
        "```json",
        json.dumps(acceptance.get("checks"), indent=2, ensure_ascii=False),
        "```",
        "",
        f"Recommended next task: `{summary.get('recommended_next_task')}`",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
