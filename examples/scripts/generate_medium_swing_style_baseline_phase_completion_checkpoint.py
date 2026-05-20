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
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.medium_swing import arrangement_policy, voicing_policy
from jammate_engine.styles.medium_swing.arrangement_policy import simulate_repeat_count_arrangement_arc

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_88"
MILESTONE_LABEL = "v2_6_88 — Medium Swing Style Baseline Phase Completion Checkpoint"

REPEAT_POLICY_CASES = (1, 2, 3, 5, 6, 8, 9, 10, 50)
RUNTIME_SPECS: tuple[dict[str, Any], ...] = (
    {"slug": "all_the_things_you_are", "leadsheet": "all_the_things_you_are.json", "choruses": 3, "seed": 3870},
    {"slug": "autumn_leaves", "leadsheet": "autumn_leaves.json", "choruses": 3, "seed": 3871},
    {"slug": "all_the_things_you_are", "leadsheet": "all_the_things_you_are.json", "choruses": 5, "seed": 3872},
    {"slug": "autumn_leaves", "leadsheet": "autumn_leaves.json", "choruses": 5, "seed": 3873},
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    outputs = [_generate_and_audit(spec) for spec in RUNTIME_SPECS]
    aggregate = _aggregate(outputs)
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": (
            "Medium Swing style baseline phase-completion checkpoint after v2_6_56-v2_6_87.  "
            "It summarizes the full-band baseline: ChordRegion-first piano comping, semantic expression hints, "
            "generic anticipation, 2-beat density relief, explicit low-intrusion 5/6-note voicing intent, "
            "bass-piano and drum-piano interaction, repeat-count-aware arrangement arcs, dry swing behavior, and "
            "full-band ending realization.  It is audit-oriented and does not add patterns, change multipliers, "
            "modify core voicing, write expression numbers, or touch API/Agent/HarmonyOS."
        ),
        "static_audit": static_audit,
        "outputs": outputs,
        "aggregate": aggregate,
        "acceptance": _acceptance(static_audit, outputs, aggregate),
        "recommended_next_task": "v2_6_89_engine_medium_swing_baseline_handoff_or_next_style_selection",
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_style_baseline_phase_completion_checkpoint_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_style_baseline_phase_completion_checkpoint_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": summary["acceptance"]}, indent=2, ensure_ascii=False))
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    arrangement = arrangement_policy.get_arrangement_policy()
    policy = voicing_policy.get_voicing_policy()
    nested = dict(policy.metadata.get("medium_swing_existing_voicing_capability_usage_policy") or {})
    repeat_arcs = {str(count): simulate_repeat_count_arrangement_arc(count) for count in REPEAT_POLICY_CASES}
    phase_counts = {str(count): dict(Counter(item["phase"] for item in arc)) for count, arc in repeat_arcs.items()}
    long_arc = repeat_arcs["50"]
    return {
        "checkpoint_version": MILESTONE_ID,
        "ending_realization_checkpoint_enabled": bool(arrangement.get("medium_swing_full_band_ending_realization_checkpoint")),
        "ending_realization_checkpoint_version": arrangement.get("medium_swing_full_band_ending_realization_checkpoint_version"),
        "ending_realization_checkpoint_contract": arrangement.get("medium_swing_full_band_ending_realization_checkpoint_contract"),
        "style_baseline_phase_completion_checkpoint_enabled": bool(arrangement.get("medium_swing_style_baseline_phase_completion_checkpoint")),
        "style_baseline_phase_completion_checkpoint_version": arrangement.get("medium_swing_style_baseline_phase_completion_checkpoint_version"),
        "style_baseline_phase_completion_checkpoint_contract": arrangement.get("medium_swing_style_baseline_phase_completion_checkpoint_contract"),
        "arrangement_arc_runtime_listening_refinement_version": arrangement.get("medium_swing_arrangement_arc_runtime_listening_refinement_version"),
        "arrangement_arc_runtime_intent_usage_version": arrangement.get("medium_swing_arrangement_arc_runtime_intent_usage_version"),
        "repeat_count_aware_arrangement_arc_version": arrangement.get("medium_swing_repeat_count_aware_arrangement_arc_checkpoint_version"),
        "previous_drum_piano_interaction_audit_version": arrangement.get("medium_swing_drum_piano_interaction_audit_version"),
        "previous_bass_piano_interaction_audit_version": arrangement.get("medium_swing_bass_piano_interaction_audit_version"),
        "two_beat_density_relief_policy_version": arrangement.get("piano_comping_two_beat_region_density_relief_policy_version"),
        "existing_voicing_capability_default_enabled": bool(nested.get("enabled")),
        "existing_voicing_capability_ordinary_runtime_default": bool(nested.get("ordinary_runtime_default")),
        "no_core_voicing_change": bool(nested.get("no_core_voicing_change")),
        "repeat_policy_cases": list(REPEAT_POLICY_CASES),
        "repeat_policy_phase_counts": phase_counts,
        "long_loop_50x_has_wave_reset": any(item["phase"] == "loop_wave_reset" for item in long_arc),
        "long_loop_50x_has_wave_peak": any(item["phase"] == "loop_wave_peak" for item in long_arc),
        "long_loop_50x_final_phase": long_arc[-1]["phase"],
        "long_loop_50x_monotonic_ramp_allowed": any(item.get("monotonic_ramp_allowed") for item in long_arc),
        "long_loop_50x_all_long_loop_safe": all(bool(item.get("long_loop_safe")) for item in long_arc),
        "base_preferred_density": policy.preferred_density,
        "base_preferred_disposition": policy.preferred_disposition.value,
    }


def _explicit_voicing_capability_usage_override() -> dict[str, Any]:
    return {
        "enabled": True,
        "metadata": {
            "medium_swing_existing_voicing_capability_usage_policy": {
                "version": MILESTONE_ID,
                "available": True,
                "enabled": True,
                "activation": "explicit_v2_6_88_style_baseline_phase_completion_checkpoint_demo",
                "scope": "event_scoped_style_policy_only",
                "ordinary_body": "keep_open_drop_4note",
                "authorized_scenes": ["final_chorus_section_tail_support", "final_ending_climax"],
                "requested_existing_contracts": ["spread_2plus3_contract", "spread_2plus4_contract", "spread_3plus3_contract"],
                "low_register_clarity_guard_version": "v2_6_78",
                "low_register_clarity_guard_enabled": True,
                "low_register_clarity_threshold": 48,
                "low_register_clarity_max_notes_below": 1,
                "bass_piano_interaction_guard_version": "v2_6_82",
                "bass_piano_interaction_guard_enabled": True,
                "bass_piano_interaction_register_floor": 48,
                "bass_piano_interaction_spread_root_bass_anchor_low": 48,
                "bass_piano_interaction_spread_root_bass_anchor_high": 60,
                "bass_piano_interaction_spread_root_bass_anchor_target": 54,
                "arrangement_arc_runtime_intent_usage_version": "v2_6_85",
                "arrangement_arc_runtime_listening_refinement_version": "v2_6_86",
                "full_band_ending_realization_checkpoint_version": "v2_6_87",
                "style_baseline_phase_completion_checkpoint_version": MILESTONE_ID,
                "arrangement_arc_runtime_intent_usage_scope": "style_baseline_phase_completion_checkpoint",
                "no_core_voicing_change": True,
                "ordinary_runtime_default": False,
            }
        },
    }


def _generate_and_audit(spec: Mapping[str, Any]) -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / str(spec["leadsheet"])).read_text(encoding="utf-8"))
    slug = str(spec["slug"])
    choruses = int(spec["choruses"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_{choruses}x_medium_swing_style_baseline_phase_completion_checkpoint_demo.mid"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": int(score.get("tempo", 132)),
            "choruses": choruses,
            "seed": int(spec["seed"]),
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True, "drums_present": True, "piano_present": True},
            "voicing_override": _explicit_voicing_capability_usage_override(),
        }
    )
    debug = dict(result.debug)
    piano_pattern_rows = _piano_pattern_rows(debug)
    piano_voicing_rows = _piano_voicing_rows(debug)
    ending_pattern_rows = _ending_rows(piano_pattern_rows, choruses)
    ending_voicing_rows = _ending_rows(piano_voicing_rows, choruses)
    note_counts = dict(debug.get("note_events_by_track") or {})
    bass = dict(debug.get("bass_foundation_audit") or {})
    pedal = dict(debug.get("pedal_realization_audit") or {})
    five_six = [row for row in piano_voicing_rows if int(row.get("density") or 0) in {5, 6}]
    ending_five_six = [row for row in ending_voicing_rows if int(row.get("density") or 0) in {5, 6}]
    ending_stable_rows = [row for row in ending_pattern_rows if row.get("ending_specific_subset_status") == "ending_settle_anchor_preferred" or row.get("rhythm_family") in {"stable", "short_region_anchor"}]
    ending_push_or_active_rows = [row for row in ending_pattern_rows if bool(row.get("ending_specific_is_push")) or row.get("weight_calibration_class") in {"active", "fill", "busy"} or row.get("optional_selected")]
    ending_checkpoint_rows = [row for row in piano_pattern_rows if row.get("ending_checkpoint_version") == "v2_6_87"]
    baseline_completion_rows = [row for row in piano_pattern_rows if row.get("style_baseline_phase_completion_version") == MILESTONE_ID]
    arrangement_arc_rows = [row for row in piano_pattern_rows if row.get("arrangement_arc_runtime_intent_usage_version") == "v2_6_85"]
    listening_rows = [row for row in piano_pattern_rows if row.get("arrangement_arc_runtime_listening_refinement_version") == "v2_6_86"]
    anticipation_rows = [row for row in piano_pattern_rows if row.get("anticipation_kind") == "next_beat1_to_previous_tail"]
    ending_anticipations = [row for row in ending_pattern_rows if row.get("anticipation_kind") == "next_beat1_to_previous_tail"]
    two_beat_rows = [row for row in piano_pattern_rows if row.get("region_length_family") == "two_beat_region"]
    two_beat_anchor_rows = [row for row in two_beat_rows if row.get("two_beat_relief_status") == "simple_anchor_preferred"]
    return {
        "ok": bool(result.ok),
        "title": score.get("title"),
        "slug": slug,
        "requested_choruses": choruses,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "performance_choruses": debug.get("performance_choruses"),
        "performance_bars": debug.get("performance_bars"),
        "repeat_arc_plan": simulate_repeat_count_arrangement_arc(choruses),
        "note_events_by_track": note_counts,
        "track_presence_ok": all(int(note_counts.get(track) or 0) > 0 for track in ("piano", "bass", "drums")),
        "piano_note_events": int(note_counts.get("piano") or 0),
        "bass_note_events": int(note_counts.get("bass") or 0),
        "drum_note_events": int(note_counts.get("drums") or 0),
        "piano_active_pattern_events": len(piano_pattern_rows),
        "piano_two_beat_active_events": len(two_beat_rows),
        "two_beat_anchor_ratio": round(len(two_beat_anchor_rows) / max(1, len(two_beat_rows)), 4),
        "active_anticipation_count": len(anticipation_rows),
        "ending_anticipation_count": len(ending_anticipations),
        "arrangement_arc_runtime_intent_event_count": len(arrangement_arc_rows),
        "arrangement_arc_runtime_intent_coverage_ratio": round(len(arrangement_arc_rows) / max(1, len(piano_pattern_rows)), 4),
        "arrangement_arc_runtime_listening_refinement_event_count": len(listening_rows),
        "arrangement_arc_runtime_listening_refinement_coverage_ratio": round(len(listening_rows) / max(1, len(piano_pattern_rows)), 4),
        "ending_checkpoint_event_count": len(ending_checkpoint_rows),
        "ending_checkpoint_coverage_ratio": round(len(ending_checkpoint_rows) / max(1, len(piano_pattern_rows)), 4),
        "ending_checkpoint_behavior_change_events": len([row for row in piano_pattern_rows if row.get("ending_checkpoint_behavior_change") is not False]),
        "style_baseline_phase_completion_event_count": len(baseline_completion_rows),
        "style_baseline_phase_completion_coverage_ratio": round(len(baseline_completion_rows) / max(1, len(piano_pattern_rows)), 4),
        "style_baseline_phase_completion_behavior_change_events": len([row for row in piano_pattern_rows if row.get("style_baseline_phase_completion_behavior_change") is not False]),
        "ending_pattern_events": len(ending_pattern_rows),
        "ending_stable_settle_events": len(ending_stable_rows),
        "ending_stable_settle_ratio": round(len(ending_stable_rows) / max(1, len(ending_pattern_rows)), 4),
        "ending_push_or_active_events": len(ending_push_or_active_rows),
        "ending_arc_final_release_events": len([row for row in ending_pattern_rows if row.get("arrangement_arc_phase") == "final_head_out_release"]),
        "ending_arc_final_release_ratio": round(len([row for row in ending_pattern_rows if row.get("arrangement_arc_phase") == "final_head_out_release"]) / max(1, len(ending_pattern_rows)), 4),
        "piano_voicing_events": len(piano_voicing_rows),
        "five_note_events": len([row for row in piano_voicing_rows if int(row.get("density") or 0) == 5]),
        "six_note_events": len([row for row in piano_voicing_rows if int(row.get("density") or 0) == 6]),
        "five_six_ratio": round(len(five_six) / max(1, len(piano_voicing_rows)), 4),
        "ordinary_body_5_6_events": len([row for row in five_six if not row.get("authorized_5_6_scene")]),
        "ending_five_six_events": len(ending_five_six),
        "low_register_dense_events": len([row for row in piano_voicing_rows if int(row.get("notes_below_c3") or 0) > 1]),
        "ending_low_register_dense_events": len([row for row in ending_voicing_rows if int(row.get("notes_below_c3") or 0) > 1]),
        "voice_leading_warning_events": len([row for row in piano_voicing_rows if row.get("top_voice_leap_exceeds_max")]),
        "ending_voice_leading_warning_events": len([row for row in ending_voicing_rows if row.get("top_voice_leap_exceeds_max")]),
        "max_top_note": max((int(row.get("top_note")) for row in piano_voicing_rows if row.get("top_note") is not None), default=0),
        "bass_span_violations": int(bass.get("span_violations") or 0),
        "bass_target_continuity_mismatches": int(bass.get("target_continuity_mismatches") or 0),
        "bass_repeated_root_violations": int(bass.get("repeated_root_same_pitch_violations") or 0),
        "pedal_cc64_event_count": int(pedal.get("cc64_event_count") or 0),
        "pedal_warning_count": int(pedal.get("warning_count") or 0),
    }


def _piano_pattern_rows(debug: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in debug.get("piano_musical_audit_events") or []:
        event = dict((raw or {}).get("pattern_event") or {})
        if event.get("track") != "piano":
            continue
        metadata = dict(event.get("metadata") or {})
        anticipation = dict(metadata.get("anticipation") or {})
        rows.append(
            {
                "event_id": event.get("event_id"),
                "region_chorus_index": _to_int(metadata.get("region_chorus_index"), default=0),
                "region_total_choruses": _to_int(metadata.get("region_total_choruses"), default=1),
                "region_performance_bar_index": _to_int(metadata.get("region_performance_bar_index"), default=-1),
                "region_is_last_bar_of_chorus": bool(metadata.get("region_is_last_bar_of_chorus")),
                "region_is_last_bar_of_section": bool(metadata.get("region_is_last_bar_of_section")),
                "region_length_family": metadata.get("region_length_family"),
                "two_beat_relief_status": metadata.get("two_beat_region_density_relief_status"),
                "optional_selected": bool(metadata.get("optional_fill_variation_selected")),
                "rhythm_family": metadata.get("rhythm_family"),
                "weight_calibration_class": metadata.get("weight_calibration_class"),
                "semantic_expression_hint": metadata.get("semantic_expression_hint"),
                "anticipation_kind": anticipation.get("kind"),
                "ending_specific_subset_status": metadata.get("ending_specific_subset_status"),
                "ending_specific_is_push": metadata.get("ending_specific_is_push"),
                "ending_specific_subset_policy_applied": bool(metadata.get("ending_specific_subset_policy_applied")),
                "arrangement_arc_runtime_intent_usage_version": metadata.get("medium_swing_arrangement_arc_runtime_intent_usage_version"),
                "arrangement_arc_phase": metadata.get("medium_swing_arrangement_arc_runtime_intent_phase"),
                "arrangement_arc_runtime_listening_refinement_version": metadata.get("medium_swing_arrangement_arc_runtime_listening_refinement_version"),
                "ending_checkpoint_version": metadata.get("medium_swing_full_band_ending_realization_checkpoint_version"),
                "ending_checkpoint_behavior_change": metadata.get("medium_swing_full_band_ending_realization_checkpoint_behavior_change"),
                "style_baseline_phase_completion_version": metadata.get("medium_swing_style_baseline_phase_completion_checkpoint_version"),
                "style_baseline_phase_completion_behavior_change": metadata.get("medium_swing_style_baseline_phase_completion_checkpoint_behavior_change"),
            }
        )
    return rows


def _piano_voicing_rows(debug: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in debug.get("piano_musical_audit_events") or []:
        event = dict((raw or {}).get("pattern_event") or {})
        if event.get("track") != "piano":
            continue
        event_metadata = dict(event.get("metadata") or {})
        voicing = dict((raw or {}).get("voicing") or {})
        notes = [int(note.get("midi_note")) for note in voicing.get("notes") or [] if note.get("midi_note") is not None]
        voice_leading = dict(voicing.get("voice_leading_profile") or {})
        density = int(voicing.get("density") or 0)
        is_last_chorus = _to_int(event_metadata.get("region_chorus_index"), default=0) == _to_int(event_metadata.get("region_total_choruses"), default=-1) - 1
        rows.append(
            {
                "event_id": event.get("event_id"),
                "region_chorus_index": _to_int(event_metadata.get("region_chorus_index"), default=0),
                "region_total_choruses": _to_int(event_metadata.get("region_total_choruses"), default=1),
                "region_performance_bar_index": _to_int(event_metadata.get("region_performance_bar_index"), default=-1),
                "region_is_last_bar_of_chorus": bool(event_metadata.get("region_is_last_bar_of_chorus")),
                "region_is_last_bar_of_section": bool(event_metadata.get("region_is_last_bar_of_section")),
                "density": density,
                "recipe_id": voicing.get("recipe_id"),
                "notes_below_c3": sum(1 for note in notes if int(note) < 48),
                "top_note": max(notes) if notes else None,
                "authorized_5_6_scene": bool(density in {5, 6} and is_last_chorus and (event_metadata.get("region_is_last_bar_of_section") or event_metadata.get("region_is_last_bar_of_chorus"))),
                "top_voice_leap_exceeds_max": bool(voice_leading.get("top_voice_leap_exceeds_max")),
            }
        )
    return rows


def _ending_rows(rows: list[Mapping[str, Any]], choruses: int) -> list[Mapping[str, Any]]:
    final = int(choruses) - 1
    final_rows = [row for row in rows if _to_int(row.get("region_chorus_index"), default=-1) == final]
    if not final_rows:
        return []
    max_bar = max(_to_int(row.get("region_performance_bar_index"), default=-1) for row in final_rows)
    return [row for row in final_rows if bool(row.get("region_is_last_bar_of_chorus")) or _to_int(row.get("region_performance_bar_index"), default=-2) == max_bar]


def _aggregate(outputs: list[Mapping[str, Any]]) -> dict[str, Any]:
    total_voicings = sum(int(out.get("piano_voicing_events") or 0) for out in outputs)
    total_five_six = sum(int(out.get("five_note_events") or 0) + int(out.get("six_note_events") or 0) for out in outputs)
    return {
        "demo_count": len(outputs),
        "runtime_chorus_counts": sorted({int(out.get("requested_choruses") or 0) for out in outputs}),
        "all_track_presence_ok": all(bool(out.get("track_presence_ok")) for out in outputs),
        "total_piano_note_events": sum(int(out.get("piano_note_events") or 0) for out in outputs),
        "total_bass_note_events": sum(int(out.get("bass_note_events") or 0) for out in outputs),
        "total_drum_note_events": sum(int(out.get("drum_note_events") or 0) for out in outputs),
        "total_piano_active_pattern_events": sum(int(out.get("piano_active_pattern_events") or 0) for out in outputs),
        "total_active_anticipation_count": sum(int(out.get("active_anticipation_count") or 0) for out in outputs),
        "total_ending_anticipation_count": sum(int(out.get("ending_anticipation_count") or 0) for out in outputs),
        "min_arrangement_arc_runtime_intent_coverage_ratio": min((float(out.get("arrangement_arc_runtime_intent_coverage_ratio") or 0.0) for out in outputs), default=0.0),
        "min_arrangement_arc_runtime_listening_refinement_coverage_ratio": min((float(out.get("arrangement_arc_runtime_listening_refinement_coverage_ratio") or 0.0) for out in outputs), default=0.0),
        "min_ending_checkpoint_coverage_ratio": min((float(out.get("ending_checkpoint_coverage_ratio") or 0.0) for out in outputs), default=0.0),
        "min_style_baseline_phase_completion_coverage_ratio": min((float(out.get("style_baseline_phase_completion_coverage_ratio") or 0.0) for out in outputs), default=0.0),
        "style_baseline_phase_completion_behavior_change_events": sum(int(out.get("style_baseline_phase_completion_behavior_change_events") or 0) for out in outputs),
        "ending_checkpoint_behavior_change_events": sum(int(out.get("ending_checkpoint_behavior_change_events") or 0) for out in outputs),
        "total_ending_pattern_events": sum(int(out.get("ending_pattern_events") or 0) for out in outputs),
        "total_ending_stable_settle_events": sum(int(out.get("ending_stable_settle_events") or 0) for out in outputs),
        "min_ending_stable_settle_ratio": min((float(out.get("ending_stable_settle_ratio") or 0.0) for out in outputs), default=0.0),
        "total_ending_push_or_active_events": sum(int(out.get("ending_push_or_active_events") or 0) for out in outputs),
        "min_ending_arc_final_release_ratio": min((float(out.get("ending_arc_final_release_ratio") or 0.0) for out in outputs), default=0.0),
        "total_five_note_events": sum(int(out.get("five_note_events") or 0) for out in outputs),
        "total_six_note_events": sum(int(out.get("six_note_events") or 0) for out in outputs),
        "total_five_six_ratio": round(total_five_six / max(1, total_voicings), 4),
        "ordinary_body_5_6_events": sum(int(out.get("ordinary_body_5_6_events") or 0) for out in outputs),
        "ending_five_six_events": sum(int(out.get("ending_five_six_events") or 0) for out in outputs),
        "low_register_dense_events": sum(int(out.get("low_register_dense_events") or 0) for out in outputs),
        "ending_low_register_dense_events": sum(int(out.get("ending_low_register_dense_events") or 0) for out in outputs),
        "voice_leading_warning_events": sum(int(out.get("voice_leading_warning_events") or 0) for out in outputs),
        "ending_voice_leading_warning_events": sum(int(out.get("ending_voice_leading_warning_events") or 0) for out in outputs),
        "bass_span_violations": sum(int(out.get("bass_span_violations") or 0) for out in outputs),
        "bass_target_continuity_mismatches": sum(int(out.get("bass_target_continuity_mismatches") or 0) for out in outputs),
        "bass_repeated_root_violations": sum(int(out.get("bass_repeated_root_violations") or 0) for out in outputs),
        "pedal_cc64_event_count": sum(int(out.get("pedal_cc64_event_count") or 0) for out in outputs),
    }


def _acceptance(static: Mapping[str, Any], outputs: list[Mapping[str, Any]], aggregate: Mapping[str, Any]) -> dict[str, Any]:
    checks = [
        {"name": "v2_6_88 style baseline phase-completion checkpoint declared", "passed": static.get("style_baseline_phase_completion_checkpoint_version") == MILESTONE_ID and bool(static.get("style_baseline_phase_completion_checkpoint_enabled"))},
        {"name": "v2_6_87 ending checkpoint remains declared", "passed": static.get("ending_realization_checkpoint_version") == "v2_6_87" and bool(static.get("ending_realization_checkpoint_enabled"))},
        {"name": "v2_6_86 listening refinement remains declared", "passed": static.get("arrangement_arc_runtime_listening_refinement_version") == "v2_6_86"},
        {"name": "v2_6_85 runtime arc remains declared", "passed": static.get("arrangement_arc_runtime_intent_usage_version") == "v2_6_85"},
        {"name": "50x loop remains long-loop safe", "passed": bool(static.get("long_loop_50x_has_wave_reset")) and bool(static.get("long_loop_50x_has_wave_peak")) and static.get("long_loop_50x_final_phase") == "final_head_out_release" and static.get("long_loop_50x_monotonic_ramp_allowed") is False},
        {"name": "runtime demos include 3x and 5x", "passed": set(aggregate.get("runtime_chorus_counts") or []) == {3, 5}},
        {"name": "full-band tracks present", "passed": bool(aggregate.get("all_track_presence_ok"))},
        {"name": "runtime arc metadata covers piano events", "passed": float(aggregate.get("min_arrangement_arc_runtime_intent_coverage_ratio") or 0.0) >= 0.98},
        {"name": "listening refinement metadata covers piano events", "passed": float(aggregate.get("min_arrangement_arc_runtime_listening_refinement_coverage_ratio") or 0.0) >= 0.98},
        {"name": "ending checkpoint metadata covers piano events", "passed": float(aggregate.get("min_ending_checkpoint_coverage_ratio") or 0.0) >= 0.98},
        {"name": "style baseline phase-completion metadata covers piano events", "passed": float(aggregate.get("min_style_baseline_phase_completion_coverage_ratio") or 0.0) >= 0.98},
        {"name": "style baseline phase-completion metadata is behavior-preserving", "passed": int(aggregate.get("style_baseline_phase_completion_behavior_change_events") or 0) == 0},
        {"name": "ending checkpoint metadata is behavior-preserving", "passed": int(aggregate.get("ending_checkpoint_behavior_change_events") or 0) == 0},
        {"name": "ending regions favor stable settle", "passed": float(aggregate.get("min_ending_stable_settle_ratio") or 0.0) >= 0.90},
        {"name": "ending has no active/push/fill risk", "passed": int(aggregate.get("total_ending_push_or_active_events") or 0) == 0},
        {"name": "ending arc is final release", "passed": float(aggregate.get("min_ending_arc_final_release_ratio") or 0.0) >= 0.98},
        {"name": "anticipation remains active", "passed": int(aggregate.get("total_active_anticipation_count") or 0) >= 24},
        {"name": "terminal ending is not anticipated away", "passed": int(aggregate.get("total_ending_anticipation_count") or 0) == 0},
        {"name": "5/6-note remains low-intrusion", "passed": float(aggregate.get("total_five_six_ratio") or 0.0) <= 0.04},
        {"name": "5/6-note stays out of ordinary body", "passed": int(aggregate.get("ordinary_body_5_6_events") or 0) == 0},
        {"name": "ending low register remains clear", "passed": int(aggregate.get("ending_low_register_dense_events") or 0) == 0},
        {"name": "full low register remains clear", "passed": int(aggregate.get("low_register_dense_events") or 0) == 0},
        {"name": "voice leading remains safe", "passed": int(aggregate.get("voice_leading_warning_events") or 0) == 0 and int(aggregate.get("ending_voice_leading_warning_events") or 0) == 0},
        {"name": "bass continuity remains safe", "passed": int(aggregate.get("bass_span_violations") or 0) == 0 and int(aggregate.get("bass_target_continuity_mismatches") or 0) == 0 and int(aggregate.get("bass_repeated_root_violations") or 0) == 0},
        {"name": "Medium Swing remains dry", "passed": int(aggregate.get("pedal_cc64_event_count") or 0) == 0},
    ]
    return {"passed": all(bool(check["passed"]) for check in checks), "checks": checks}


def _render_report(summary: Mapping[str, Any]) -> str:
    aggregate = dict(summary.get("aggregate") or {})
    acceptance = dict(summary.get("acceptance") or {})
    lines = [
        f"# {MILESTONE_LABEL}",
        "",
        "## Scope",
        str(summary.get("scope")),
        "",
        "## Runtime full-band baseline demos",
    ]
    for out in summary.get("outputs") or []:
        lines.extend(
            [
                f"### {out['title']} — {out['requested_choruses']}x",
                f"- MIDI: `{out['midi_path']}`",
                f"- Piano/Bass/Drums notes: {out['piano_note_events']} / {out['bass_note_events']} / {out['drum_note_events']}",
                f"- Piano active patterns: {out['piano_active_pattern_events']}",
                f"- 2-beat anchor ratio: {out['two_beat_anchor_ratio']}",
                f"- Anticipations: {out['active_anticipation_count']} (ending {out['ending_anticipation_count']})",
                f"- Ending pattern events: {out['ending_pattern_events']}",
                f"- Ending stable settle ratio: {out['ending_stable_settle_ratio']}",
                f"- Ending push/active events: {out['ending_push_or_active_events']}",
                f"- Ending arc final-release ratio: {out['ending_arc_final_release_ratio']}",
                f"- Ending 5/6-note events: {out['ending_five_six_events']}",
                f"- Baseline phase-completion coverage: {out['style_baseline_phase_completion_coverage_ratio']}",
                f"- 5-note / 6-note: {out['five_note_events']} / {out['six_note_events']} (ratio {out['five_six_ratio']})",
                f"- Ending low-register dense events: {out['ending_low_register_dense_events']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Aggregate",
            f"- Runtime chorus counts: {aggregate.get('runtime_chorus_counts')}",
            f"- Total piano/bass/drums notes: {aggregate.get('total_piano_note_events')} / {aggregate.get('total_bass_note_events')} / {aggregate.get('total_drum_note_events')}",
            f"- Total anticipations: {aggregate.get('total_active_anticipation_count')}",
            f"- Ending anticipations: {aggregate.get('total_ending_anticipation_count')}",
            f"- Min ending stable settle ratio: {aggregate.get('min_ending_stable_settle_ratio')}",
            f"- Min baseline phase-completion coverage: {aggregate.get('min_style_baseline_phase_completion_coverage_ratio')}",
            f"- Ending push/active events: {aggregate.get('total_ending_push_or_active_events')}",
            f"- Ending 5/6-note events: {aggregate.get('ending_five_six_events')}",
            f"- Total 5/6 ratio: {aggregate.get('total_five_six_ratio')}",
            f"- Low-register dense events: {aggregate.get('low_register_dense_events')}",
            f"- Voice-leading warnings: {aggregate.get('voice_leading_warning_events')}",
            "",
            "## Acceptance",
        ]
    )
    for check in acceptance.get("checks") or []:
        lines.append(f"- [{'x' if check.get('passed') else ' '}] {check.get('name')}")
    lines.extend(["", f"Acceptance Passed: {acceptance.get('passed')}", ""])
    return "\n".join(lines)


def _to_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


if __name__ == "__main__":
    main()
