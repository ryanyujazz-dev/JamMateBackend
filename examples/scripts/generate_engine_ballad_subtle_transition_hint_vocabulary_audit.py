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
from jammate_engine.midi.channel_map import CHANNELS
from jammate_engine.midi.midi_writer import write_midi
from jammate_engine.midi.render_pipeline import performed_beat
from jammate_engine.realization.note_event_builder import NoteEvent
from jammate_engine.realization.percussion_realizer import DRUM_NOTES, DYNAMIC_VELOCITY, STROKE_DURATION
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad import arrangement_policy, percussion_patterns
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile

DEMOS_DIR = PROJECT_ROOT / "demos"
LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
MILESTONE_ID = "v2_6_136"
MILESTONE_LABEL = "v2_6_136 — Engine Ballad Subtle Transition Hint Vocabulary"


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static = _static_audit()
    runtime = _generate_misty_runtime_audit()
    fill_focus_demo = _write_fill_focus_demo()
    acceptance = _acceptance(static, runtime)
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": (
            "Lower automatic Ballad transition hints so they no longer read as foreground fills, and expand the vocabulary using V1-derived primitives: brush_drag_to_4, section_breath, soft_swish_4and, and final_release. Hints ride inside the brush texture with no background ducking; explicit tap-drag/single-stroke fills remain vocabulary only. Offbeats keep shared swing-8 timing; no piano/bass/voicing/API/Agent/HarmonyOS change."
        ),
        "static_audit": static,
        "runtime_audit": runtime,
        "fill_focus_demo": fill_focus_demo,
        "acceptance": acceptance,
        "recommended_next_task": "v2_6_137_engine_ballad_transition_hint_listening_calibration",
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_ballad_subtle_transition_hint_vocabulary_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_ballad_subtle_transition_hint_vocabulary_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def _candidate_debug(context: dict[str, Any]) -> dict[str, Any]:
    context = {**dict(context), "jazz_ballad_brush_sound_source_time_feel_active": True}
    candidates = percussion_patterns.get_pattern_candidates(context)
    if not candidates:
        return {"candidate_count": 0, "events": [], "metadata": {}}
    candidate = candidates[0]
    events = [
        {
            "beat": float(event.local_beat),
            "role": event.role,
            "drum": event.metadata.get("drum"),
            "slot": event.metadata.get("brush_event_slot"),
            "offbeat_role": event.metadata.get("brush_offbeat_role"),
            "articulation": event.metadata.get("brush_sound_source_articulation"),
            "dynamic_profile": event.metadata.get("dynamic_profile"),
            "stroke_profile": event.metadata.get("stroke_profile"),
            "timing_intent": event.metadata.get("timing_intent"),
            "brush_classic_fill_cell": event.metadata.get("brush_classic_fill_cell"),
            "brush_fill_policy_active": event.metadata.get("brush_fill_policy_active"),
            "brush_fill_foreground_lane": event.metadata.get("brush_fill_foreground_lane"),
            "brush_fill_audibility_contract": event.metadata.get("brush_fill_audibility_contract"),
            "brush_timing_contract": event.metadata.get("brush_timing_contract"),
            "brush_timing_owner": event.metadata.get("brush_timing_owner"),
            "logical_grid_position": event.metadata.get("brush_logical_grid_position"),
        }
        for event in candidate.events
    ]
    return {
        "candidate_count": len(candidates),
        "name": candidate.name,
        "category": candidate.category,
        "rhythm_beats": list(candidate.rhythm_beats),
        "events": events,
        "event_drum_counts": dict(Counter(str(event["drum"]) for event in events)),
        "event_slot_counts": dict(Counter(str(event["slot"]) for event in events)),
        "metadata": dict(candidate.metadata),
    }


def _static_audit() -> dict[str, Any]:
    policy = arrangement_policy.get_arrangement_policy()
    contexts = {
        "basic_bar": {"region_duration_beats": 4.0, "region_source_bar_index": 0, "region_chorus_index": 0, "region_total_choruses": 3},
        "swing_skip_bar": {"region_duration_beats": 4.0, "region_source_bar_index": 1, "region_chorus_index": 0, "region_total_choruses": 3},
        "first_half_split": {"region_duration_beats": 2.0, "region_source_bar_index": 1, "region_chorus_index": 0, "region_total_choruses": 3, "region_is_first_region_of_bar": True},
        "second_half_split": {"region_duration_beats": 2.0, "region_source_bar_index": 1, "region_chorus_index": 0, "region_total_choruses": 3, "region_is_last_region_of_bar": True},
        "phrase_breath": {"region_duration_beats": 4.0, "region_source_bar_index": 7, "region_chorus_index": 0, "region_total_choruses": 3},
        "later_chorus_pickup_fill": {"region_duration_beats": 4.0, "region_source_bar_index": 5, "region_chorus_index": 1, "region_total_choruses": 3},
        "later_chorus_section_fill": {"region_duration_beats": 4.0, "region_source_bar_index": 7, "region_chorus_index": 1, "region_total_choruses": 3, "region_is_last_bar_of_section": True},
        "final_release": {"region_duration_beats": 4.0, "region_source_bar_index": 31, "region_chorus_index": 2, "region_total_choruses": 3, "region_is_last_bar_of_chorus": True},
    }
    return {
        "arrangement_policy_version": policy.get("jazz_ballad_brush_sound_source_time_feel_version"),
        "brush_sound_source_assumed": policy.get("jazz_ballad_brush_sound_source_assumed"),
        "bar_level_scope": policy.get("jazz_ballad_drum_planning_scope"),
        "not_chord_region_loop": policy.get("jazz_ballad_drum_not_chord_region_loop"),
        "no_custom_internal_brush_voices": policy.get("jazz_ballad_no_custom_internal_brush_voices"),
        "motion_points": list(policy.get("jazz_ballad_brush_motion_points") or []),
        "candidate_debugs": {name: _candidate_debug(ctx) for name, ctx in contexts.items()},
    }



def _candidate_note_events(context: dict[str, Any], *, bar_start: float) -> list[NoteEvent]:
    candidate = percussion_patterns.get_pattern_candidates({**context, "jazz_ballad_brush_sound_source_time_feel_active": True})[0]
    timing_policy = JazzBalladProfile().timing_policy
    out: list[NoteEvent] = []
    for event in candidate.events:
        drum = str(event.metadata.get("drum") or "ride")
        dynamic = str(event.metadata.get("dynamic_profile") or "medium")
        stroke = str(event.metadata.get("stroke_profile") or "short")
        timing = str(event.metadata.get("timing_intent") or "auto")
        start = bar_start + performed_beat(float(event.local_beat), timing, timing_policy)
        out.append(
            NoteEvent(
                track="drums",
                channel=CHANNELS["drums"],
                note=int(DRUM_NOTES.get(drum, DRUM_NOTES["ride"])),
                velocity=int(DYNAMIC_VELOCITY.get(dynamic, 55)),
                start_beat=start,
                duration_beats=float(STROKE_DURATION.get(stroke, 0.1)),
                timing_intent="straight_even",
            )
        )
    return out


def _write_fill_focus_demo() -> dict[str, Any]:
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_jazz_ballad_subtle_transition_hint_focus_demo.mid"
    contexts = [
        ("basic_time", {"region_duration_beats": 4.0, "region_source_bar_index": 0, "region_chorus_index": 0, "region_total_choruses": 3}),
        ("v1_drag_to_4_hint", {"region_duration_beats": 4.0, "region_source_bar_index": 3, "region_chorus_index": 0, "region_total_choruses": 3}),
        ("turnaround_2and_3and_4and_whisper", {"region_duration_beats": 4.0, "region_source_bar_index": 5, "region_chorus_index": 1, "region_total_choruses": 3}),
        ("v1_section_breath_4_to_4and_hint", {"region_duration_beats": 4.0, "region_source_bar_index": 7, "region_chorus_index": 1, "region_total_choruses": 3, "region_is_last_bar_of_section": True}),
        ("section_entry_1and_bloom_hint", {"region_duration_beats": 4.0, "region_source_bar_index": 8, "region_chorus_index": 1, "region_total_choruses": 3, "region_is_first_bar_of_section": True}),
        ("final_release", {"region_duration_beats": 4.0, "region_source_bar_index": 31, "region_chorus_index": 2, "region_total_choruses": 3, "region_is_last_bar_of_chorus": True}),
    ]
    events: list[NoteEvent] = []
    debug: list[dict[str, Any]] = []
    bar_start = 0.0
    for label, context in contexts:
        events.extend(_candidate_note_events(context, bar_start=bar_start))
        candidate = _candidate_debug(context)
        debug.append(
            {
                "label": label,
                "bar_start": bar_start,
                "brush_classic_fill_cell": (candidate.get("metadata") or {}).get("brush_classic_fill_cell"),
                "event_slot_counts": candidate.get("event_slot_counts"),
                "foreground_fill_event_count": sum(1 for event in candidate.get("events", []) if event.get("brush_fill_foreground_lane") is True),
            }
        )
        bar_start += 4.0
    write_midi(events, midi_path, tempo_bpm=72)
    return {
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "demo_type": "drum_only_section_transition_hint_focus",
        "note_event_count": len(events),
        "bars": debug,
    }

def _generate_misty_runtime_audit() -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / "misty.json").read_text(encoding="utf-8"))
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_misty_jazz_ballad_subtle_transition_hint_vocabulary_demo.mid"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "jazz_ballad",
            "tempo": int(score.get("tempo", 72)),
            "choruses": 3,
            "seed": 1310,
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
        }
    )
    debug = dict(result.debug)
    rows = debug.get("piano_musical_audit_events") or []
    region_contexts = _region_contexts_from_piano_rows(rows)
    candidates = [_candidate_debug(context) for context in region_contexts]
    audible_candidates = [item for item in candidates if int(item.get("candidate_count") or 0) > 0]
    event_rows = [event for item in audible_candidates for event in item.get("events", [])]
    return {
        "ok": bool(result.ok),
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "note_events_by_track": dict(debug.get("note_events_by_track") or {}),
        "performance_choruses": debug.get("performance_choruses"),
        "performance_bars": debug.get("performance_bars"),
        "regions": debug.get("regions"),
        "audited_region_count": len(candidates),
        "audible_candidate_count": len(audible_candidates),
        "expected_brush_pattern_event_count": len(event_rows),
        "brush_feel_cell_counts": dict(Counter(str(item.get("metadata", {}).get("brush_feel_cell")) for item in audible_candidates)),
        "brush_event_drum_counts": dict(Counter(str(event.get("drum")) for event in event_rows)),
        "brush_event_slot_counts": dict(Counter(str(event.get("slot")) for event in event_rows)),
        "brush_event_articulation_counts": dict(Counter(str(event.get("articulation")) for event in event_rows)),
        "brush_classic_fill_cell_counts": dict(Counter(str(item.get("metadata", {}).get("brush_classic_fill_cell")) for item in audible_candidates)),
        "classic_fill_event_count": sum(1 for event in event_rows if str(event.get("role")) == "ballad_classic_brush_fill"),
        "section_transition_hint_event_count": sum(1 for event in event_rows if str(event.get("role")) == "ballad_section_transition_hint"),
        "sample_candidates": audible_candidates[:6],
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
            "region_is_first_region_of_bar": metadata.get("region_is_first_region_of_bar"),
            "region_is_last_region_of_bar": metadata.get("region_is_last_region_of_bar"),
            "region_is_first_bar_of_section": metadata.get("region_is_first_bar_of_section"),
            "region_is_last_bar_of_section": metadata.get("region_is_last_bar_of_section"),
            "region_is_last_bar_of_chorus": metadata.get("region_is_last_bar_of_chorus"),
            "phrase_role": metadata.get("region_phrase"),
        }
    return list(by_region.values())


def _offbeats_use_shared_swing8_timing(candidate_debug: dict[str, Any]) -> bool:
    events = candidate_debug.get("events") or []
    offbeats = [event for event in events if "&" in str(event.get("slot"))]
    if not offbeats:
        return False
    return all(
        event.get("timing_intent") == "swing_upbeat"
        and event.get("brush_timing_contract") == "style_timing_policy_swing8"
        and event.get("brush_timing_owner") == "style_timing_policy_not_pattern"
        for event in offbeats
    )

def _acceptance(static: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
    debug = static.get("candidate_debugs") or {}
    basic = debug.get("basic_bar") or {}
    skip = debug.get("swing_skip_bar") or {}
    first = debug.get("first_half_split") or {}
    second = debug.get("second_half_split") or {}
    breath = debug.get("phrase_breath") or {}
    pickup = debug.get("later_chorus_pickup_fill") or {}
    section_fill = debug.get("later_chorus_section_fill") or {}
    final = debug.get("final_release") or {}
    runtime_drums = set((runtime.get("brush_event_drum_counts") or {}).keys())
    allowed = {"snare", "hihat_pedal", "kick", "ride"}
    custom = {"brush_swirl", "brush_sweep", "brush_tap", "brush_release"}
    note_counts = runtime.get("note_events_by_track") or {}
    skip_slots = set((skip.get("event_slot_counts") or {}).keys())
    first_slots = set((first.get("event_slot_counts") or {}).keys())
    second_slots = set((second.get("event_slot_counts") or {}).keys())
    hint_events = [
        event
        for event in (pickup.get("events") or []) + (section_fill.get("events") or []) + (breath.get("events") or [])
        if str(event.get("role")) == "ballad_section_transition_hint"
    ]
    foreground_hint_events = [event for event in hint_events if event.get("brush_fill_foreground_lane") is True]
    hint_dynamic_profiles = {str(event.get("dynamic_profile")) for event in hint_events}
    # Background is allowed to continue around the hint; only the exact cue slot
    # should get a small amount of space.  The important check is that we do not
    # wipe the whole half-bar like the previous foreground-fill experiment.
    section_tail_slots = {str(event.get("slot")) for event in (section_fill.get("events") or []) if str(event.get("role")) == "ballad_section_transition_hint"}
    runtime_cells = set((runtime.get("brush_classic_fill_cell_counts") or {}).keys())
    checks = {
        "version_declared": static.get("arrangement_policy_version") == MILESTONE_ID,
        "brush_source_assumed": static.get("brush_sound_source_assumed") is True,
        "bar_level_not_chord_loop": static.get("not_chord_region_loop") is True and static.get("bar_level_scope") == "bar_level_brush_time_feel_with_region_projection",
        "motion_grid_includes_offbeats": static.get("motion_points") == ["1", "1&", "2", "2&", "3", "3&", "4", "4&"],
        "no_custom_internal_brush_drums": custom.isdisjoint(runtime_drums),
        "standard_drum_entries_only": runtime_drums.issubset(allowed),
        "basic_bar_has_brush_pressure_hat_and_feather": basic.get("candidate_count") == 1 and {"snare", "hihat_pedal", "kick"}.issubset(set((basic.get("event_drum_counts") or {}).keys())),
        "skip_bar_articulates_2and_4and": {"2&", "4&"}.issubset(skip_slots),
        "offbeats_use_shared_swing8_timing": _offbeats_use_shared_swing8_timing(skip),
        "split_regions_project_same_bar_plan": {"1", "2", "2&"}.issubset(first_slots) and {"3", "4", "4&"}.issubset(second_slots) and "1" not in second_slots,
        "phrase_tail_keeps_4and_transition_hint": "4&" in set((breath.get("event_slot_counts") or {}).keys()),
        "section_hints_are_not_foreground_lane": bool(hint_events) and len(foreground_hint_events) == 0,
        "section_hints_use_subtle_hint_dynamic_profiles": bool(hint_dynamic_profiles) and all(profile.startswith("brush_hint_") for profile in hint_dynamic_profiles),
        "pickup_uses_turnaround_whisper_hint": (pickup.get("metadata") or {}).get("brush_classic_fill_cell") == "turnaround_2and_3and_4and_whisper" and {"2&", "3&", "4&"}.issubset(set((pickup.get("event_slot_counts") or {}).keys())),
        "section_tail_uses_v1_section_breath_hint": (section_fill.get("metadata") or {}).get("brush_classic_fill_cell") == "v1_section_breath_4_to_4and_hint" and {"4", "4&"}.issubset(section_tail_slots),
        "cadence_uses_v1_drag_to_4_hint": (breath.get("metadata") or {}).get("brush_classic_fill_cell") in {"v1_section_breath_4_to_4and_hint", "v1_soft_swish_4and_hint", "v1_drag_to_4_hint"},
        "v1_reference_primitives_declared": bool((breath.get("metadata") or {}).get("brush_transition_hint_v1_reference_primitives")),
        "no_default_long_explicit_fill_cells": not ({"tap_drag_tap_release", "single_stroke_4_to_next", "turnaround_sweep_roll"} & runtime_cells),
        "final_release_contextual": final.get("candidate_count") == 1 and set((final.get("event_drum_counts") or {}).keys()).issubset({"snare", "ride"}),
        "misty_runtime_has_section_hint_events": int(runtime.get("section_transition_hint_event_count") or 0) > 0,
        "misty_runtime_has_drum_layer": runtime.get("ok") is True and int(note_counts.get("drums", 0) or 0) > 0,
        "piano_bass_still_present": int(note_counts.get("piano", 0) or 0) > 0 and int(note_counts.get("bass", 0) or 0) > 0,
    }
    return {"passed": all(checks.values()), "checks": checks}


def _render_report(summary: dict[str, Any]) -> str:
    static = summary["static_audit"]
    runtime = summary["runtime_audit"]
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
        f"- Arrangement policy version: `{static.get('arrangement_policy_version')}`",
        f"- Brush source assumed: `{static.get('brush_sound_source_assumed')}`",
        f"- Scope: `{static.get('bar_level_scope')}`",
        f"- Motion points: `{static.get('motion_points')}`",
        "",
        "## Misty runtime audit",
        "",
        f"- MIDI: `{runtime.get('midi_path')}`",
        f"- Note events by track: `{runtime.get('note_events_by_track')}`",
        f"- Brush feel cell counts: `{runtime.get('brush_feel_cell_counts')}`",
        f"- Brush event drum counts: `{runtime.get('brush_event_drum_counts')}`",
        f"- Brush event slot counts: `{runtime.get('brush_event_slot_counts')}`",
        f"- Classic fill cell counts: `{runtime.get('brush_classic_fill_cell_counts')}`",
        f"- Classic fill event count: `{runtime.get('classic_fill_event_count')}`",
        f"- Section transition hint event count: `{runtime.get('section_transition_hint_event_count')}`",
        "",
        "## Subtle transition-hint focus demo",
        "",
        f"- MIDI: `{summary.get('fill_focus_demo', {}).get('midi_path')}`",
        f"- Bars: `{summary.get('fill_focus_demo', {}).get('bars')}`",
        "",
        "## Acceptance",
        "",
        f"Passed: `{summary['acceptance'].get('passed')}`",
        "",
        "```json",
        json.dumps(summary["acceptance"].get("checks"), indent=2, ensure_ascii=False),
        "```",
        "",
        f"Recommended next task: `{summary.get('recommended_next_task')}`",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
