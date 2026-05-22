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
MILESTONE_ID = "v2_6_127"
MILESTONE_LABEL = "v2_6_127 — Engine Ballad Brush Semantic Policy Skeleton"


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static = _static_audit()
    runtime = _generate_misty_runtime_audit()
    acceptance = _acceptance(static, runtime)
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": (
            "Introduce a Jazz Ballad brush semantic policy skeleton in the existing jazz_ballad percussion owner. "
            "The milestone exposes per-region brush texture/time-anchor/kick/phrase-breath/density intent for audit, "
            "but intentionally keeps default Ballad drums silent and emits no MIDI drum notes."
        ),
        "static_audit": static,
        "runtime_audit": runtime,
        "acceptance": acceptance,
        "recommended_next_task": "v2_6_128_engine_ballad_first_audible_sparse_brush_foundation",
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_ballad_brush_semantic_policy_skeleton_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_ballad_brush_semantic_policy_skeleton_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def _static_audit() -> dict[str, Any]:
    ordinary = percussion_patterns.build_brush_semantic_policy_decision(
        {"region_duration_beats": 4.0, "region_source_bar_index": 4, "region_chorus_index": 1, "region_total_choruses": 3}
    )
    phrase_tail = percussion_patterns.build_brush_semantic_policy_decision(
        {"region_duration_beats": 4.0, "region_source_bar_index": 7, "region_chorus_index": 0, "region_total_choruses": 3}
    )
    final_release = percussion_patterns.build_brush_semantic_policy_decision(
        {"region_duration_beats": 4.0, "region_source_bar_index": 31, "region_chorus_index": 2, "region_total_choruses": 3, "region_is_last_bar_of_chorus": True}
    )
    candidates = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    policy = arrangement_policy.get_arrangement_policy()
    return {
        "policy_version": percussion_patterns.JAZZ_BALLAD_BRUSH_SEMANTIC_POLICY_VERSION,
        "arrangement_policy_active": policy.get("jazz_ballad_brush_semantic_policy_active"),
        "arrangement_policy_version": policy.get("jazz_ballad_brush_semantic_policy_version"),
        "declared_texture_intents": list(percussion_patterns.BRUSH_TEXTURE_INTENTS),
        "declared_time_anchor_intents": list(percussion_patterns.BRUSH_TIME_ANCHOR_INTENTS),
        "declared_kick_policy_intents": list(percussion_patterns.BRUSH_KICK_POLICY_INTENTS),
        "declared_phrase_breath_intents": list(percussion_patterns.BRUSH_PHRASE_BREATH_INTENTS),
        "declared_density_bands": list(percussion_patterns.BRUSH_DENSITY_BANDS),
        "default_candidate_count": len(candidates),
        "ordinary_decision": _compact_decision(ordinary),
        "phrase_tail_decision": _compact_decision(phrase_tail),
        "final_release_decision": _compact_decision(final_release),
        "boundary": ordinary.get("jazz_ballad_brush_semantic_policy_boundary"),
        "no_fixed_loop": ordinary.get("brush_no_fixed_loop"),
        "no_swing_ride": ordinary.get("brush_no_swing_ride"),
        "no_rock_backbeat": ordinary.get("brush_no_rock_backbeat"),
    }


def _generate_misty_runtime_audit() -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / "misty.json").read_text(encoding="utf-8"))
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_misty_jazz_ballad_brush_semantic_policy_skeleton_demo.mid"
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
        "brush_texture_counts": dict(Counter(str(item.get("brush_texture_intent")) for item in decisions)),
        "brush_time_anchor_counts": dict(Counter(str(item.get("brush_time_anchor_intent")) for item in decisions)),
        "brush_kick_policy_counts": dict(Counter(str(item.get("brush_kick_policy_intent")) for item in decisions)),
        "brush_phrase_breath_counts": dict(Counter(str(item.get("brush_phrase_breath_intent")) for item in decisions)),
        "brush_density_counts": dict(Counter(str(item.get("brush_density_band")) for item in decisions)),
        "sample_decisions": [_compact_decision(item) for item in decisions[:12]],
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


def _compact_decision(decision: dict[str, Any]) -> dict[str, Any]:
    context = dict(decision.get("brush_phrase_context") or {})
    return {
        "texture": decision.get("brush_texture_intent"),
        "time_anchor": decision.get("brush_time_anchor_intent"),
        "kick_policy": decision.get("brush_kick_policy_intent"),
        "phrase_breath": decision.get("brush_phrase_breath_intent"),
        "density": decision.get("brush_density_band"),
        "audible": decision.get("brush_runtime_audible"),
        "source_bar_index": context.get("source_bar_index"),
        "chorus_index": context.get("chorus_index"),
        "phrase_tail": context.get("phrase_tail"),
        "final_release_context": context.get("final_release_context"),
    }


def _acceptance(static: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "version_declared": static.get("policy_version") == MILESTONE_ID and static.get("arrangement_policy_version") == MILESTONE_ID and static.get("arrangement_policy_active") is True,
        "default_runtime_still_silent": static.get("default_candidate_count") == 0 and runtime.get("drum_note_events") == 0,
        "misty_still_generates_piano_and_bass": runtime.get("ok") is True and int((runtime.get("note_events_by_track") or {}).get("piano", 0)) > 0 and int((runtime.get("note_events_by_track") or {}).get("bass", 0)) > 0,
        "semantic_dimensions_present": all(static.get(key) for key in ("declared_texture_intents", "declared_time_anchor_intents", "declared_kick_policy_intents", "declared_phrase_breath_intents", "declared_density_bands")),
        "ordinary_and_boundary_decisions_present": static.get("ordinary_decision", {}).get("texture") == "circular_sparse" and static.get("phrase_tail_decision", {}).get("phrase_breath") == "soft_swish_4and" and static.get("final_release_decision", {}).get("phrase_breath") == "final_release",
        "runtime_region_decisions_exposed": int(runtime.get("audited_region_count") or 0) >= 90 and bool(runtime.get("brush_texture_counts")) and bool(runtime.get("brush_phrase_breath_counts")),
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
        "## Static brush semantic policy",
        "",
        f"- Policy version: `{static.get('policy_version')}`",
        f"- Arrangement policy active: `{static.get('arrangement_policy_active')}` / `{static.get('arrangement_policy_version')}`",
        f"- Default candidate count: `{static.get('default_candidate_count')}`",
        f"- Boundary: `{static.get('boundary')}`",
        f"- Texture intents: `{static.get('declared_texture_intents')}`",
        f"- Time anchor intents: `{static.get('declared_time_anchor_intents')}`",
        f"- Kick policy intents: `{static.get('declared_kick_policy_intents')}`",
        f"- Phrase breath intents: `{static.get('declared_phrase_breath_intents')}`",
        f"- Density bands: `{static.get('declared_density_bands')}`",
        "",
        "## Misty runtime audit",
        "",
        f"- MIDI: `{runtime.get('midi_path')}`",
        f"- Note events by track: `{runtime.get('note_events_by_track')}`",
        f"- Audited region count: `{runtime.get('audited_region_count')}`",
        f"- Brush texture counts: `{runtime.get('brush_texture_counts')}`",
        f"- Brush time anchor counts: `{runtime.get('brush_time_anchor_counts')}`",
        f"- Brush kick policy counts: `{runtime.get('brush_kick_policy_counts')}`",
        f"- Brush phrase breath counts: `{runtime.get('brush_phrase_breath_counts')}`",
        f"- Brush density counts: `{runtime.get('brush_density_counts')}`",
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
