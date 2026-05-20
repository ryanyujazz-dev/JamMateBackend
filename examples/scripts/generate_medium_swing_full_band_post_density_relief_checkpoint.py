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
from jammate_engine.styles.medium_swing import arrangement_policy, comping_patterns, voicing_policy

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_81"
MILESTONE_LABEL = "v2_6_81 — Medium Swing Full-Band Post-Density-Relief Checkpoint"

FORBIDDEN_PATTERN_EXPRESSION_KEYS = {"velocity", "duration", "duration_beats", "pedal", "release_beats", "accent", "midi_note"}
FORBIDDEN_PATTERN_VOICING_KEYS = {
    "midi_notes",
    "notes",
    "degrees",
    "chord_tones",
    "voicing",
    "voicing_degrees",
    "content_family",
    "disposition",
    "projection_method",
}

SPECS: tuple[dict[str, Any], ...] = (
    {"slug": "all_the_things_you_are", "leadsheet": "all_the_things_you_are.json", "seed": 3790},
    {"slug": "autumn_leaves", "leadsheet": "autumn_leaves.json", "seed": 3791},
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    outputs = [_generate_and_audit(spec) for spec in SPECS]
    aggregate = _aggregate(outputs)
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": (
            "Behavior-preserving full-band checkpoint after v2_6_80. It checks that the two-beat density relief works in a "
            "piano+bass+drums setting: Autumn Leaves should no longer be over-dense in consecutive 2-beat ChordRegions, "
            "All The Things You Are should not be over-thinned, generic region-first anticipation must remain active, and "
            "the v2_6_78 low-register clarity guard plus explicit-only 5/6-note grouped SPREAD usage stay intact. No pattern, "
            "voicing internals, expression numbers, API, Agent, or HarmonyOS behavior are changed."
        ),
        "static_audit": static_audit,
        "outputs": outputs,
        "aggregate": aggregate,
        "acceptance": _acceptance(static_audit, outputs, aggregate),
        "recommended_next_task": "medium_swing_bass_piano_interaction_audit_if_full_band_checkpoint_passes",
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_full_band_post_density_relief_checkpoint_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_full_band_post_density_relief_checkpoint_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": summary["acceptance"]}, indent=2, ensure_ascii=False))
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    arrangement = arrangement_policy.get_arrangement_policy()
    policy = voicing_policy.get_voicing_policy()
    nested = dict(policy.metadata.get("medium_swing_existing_voicing_capability_usage_policy") or {})
    candidate_rows = _candidate_rows()
    return {
        "checkpoint_version": MILESTONE_ID,
        "checkpoint_policy_enabled": bool(arrangement.get("medium_swing_full_band_post_density_relief_checkpoint")),
        "checkpoint_policy_version": arrangement.get("medium_swing_full_band_post_density_relief_checkpoint_version"),
        "checkpoint_policy_contract": arrangement.get("medium_swing_full_band_post_density_relief_checkpoint_contract"),
        "two_beat_density_relief_policy_version": arrangement.get("piano_comping_two_beat_region_density_relief_policy_version"),
        "two_beat_density_relief_policy_enabled": bool(arrangement.get("piano_comping_two_beat_region_density_relief_policy")),
        "full_band_checkpoint_previous_version": arrangement.get("medium_swing_full_band_listening_checkpoint_version"),
        "anticipation_checkpoint_version": arrangement.get("piano_region_first_anticipation_compatibility_checkpoint_version"),
        "low_register_clarity_guard_version": arrangement.get("medium_swing_existing_voicing_capability_low_register_clarity_guard_version"),
        "low_register_clarity_guard_enabled": bool(arrangement.get("medium_swing_existing_voicing_capability_low_register_clarity_guard")),
        "existing_voicing_capability_policy_version": arrangement.get("medium_swing_existing_voicing_capability_usage_policy_version"),
        "existing_voicing_capability_available": bool(nested.get("available")),
        "existing_voicing_capability_default_enabled": bool(nested.get("enabled")),
        "existing_voicing_capability_ordinary_runtime_default": bool(nested.get("ordinary_runtime_default")),
        "existing_voicing_capability_no_core_voicing_change": bool(nested.get("no_core_voicing_change")),
        "base_preferred_density": policy.preferred_density,
        "base_preferred_disposition": policy.preferred_disposition.value,
        "pattern_forbidden_expression_candidates": [row for row in candidate_rows if row["forbidden_pattern_expression_keys"]],
        "pattern_forbidden_voicing_candidates": [row for row in candidate_rows if row["forbidden_pattern_voicing_keys"]],
        "bar_first_two_chord_bar_candidates": [row for row in candidate_rows if row["has_bar_first_two_chord_bar_marker"]],
        "two_beat_candidate_count": len(comping_patterns.get_pattern_candidates({"region_duration_beats": 2.0})),
    }


def _candidate_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for duration in (1.0, 2.0, 3.0, 4.0, 5.0):
        for candidate in comping_patterns.get_pattern_candidates({"region_duration_beats": duration}):
            forbidden_expression: set[str] = set(FORBIDDEN_PATTERN_EXPRESSION_KEYS & set(candidate.metadata))
            forbidden_voicing: set[str] = set(FORBIDDEN_PATTERN_VOICING_KEYS & set(candidate.metadata))
            for event in candidate.events:
                forbidden_expression.update(FORBIDDEN_PATTERN_EXPRESSION_KEYS & set(event.metadata))
                forbidden_voicing.update(FORBIDDEN_PATTERN_VOICING_KEYS & set(event.metadata))
            text_blob = " ".join([candidate.name, candidate.category, str(candidate.metadata), " ".join(candidate.tags)])
            rows.append(
                {
                    "name": candidate.name,
                    "duration_probe": duration,
                    "forbidden_pattern_expression_keys": tuple(sorted(forbidden_expression)),
                    "forbidden_pattern_voicing_keys": tuple(sorted(forbidden_voicing)),
                    "has_bar_first_two_chord_bar_marker": "two_chord_bar" in text_blob or "split_bar" in text_blob,
                }
            )
    return rows


def _explicit_voicing_capability_usage_override() -> dict[str, Any]:
    return {
        "enabled": True,
        "metadata": {
            "medium_swing_existing_voicing_capability_usage_policy": {
                "version": MILESTONE_ID,
                "available": True,
                "enabled": True,
                "activation": "explicit_v2_6_81_full_band_post_density_relief_checkpoint_demo",
                "scope": "event_scoped_style_policy_only",
                "ordinary_body": "keep_open_drop_4note",
                "authorized_scenes": ["final_chorus_section_tail_support", "final_ending_climax"],
                "requested_existing_contracts": [
                    "spread_2plus3_contract",
                    "spread_2plus4_contract",
                    "spread_3plus3_contract",
                ],
                "no_core_voicing_change": True,
                "ordinary_runtime_default": False,
            },
        },
    }


def _generate_and_audit(spec: Mapping[str, Any]) -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / str(spec["leadsheet"])).read_text(encoding="utf-8"))
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_medium_swing_full_band_post_density_relief_checkpoint_demo.mid"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": int(score.get("tempo", 132)),
            "choruses": 3,
            "seed": int(spec["seed"]),
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True, "drums_present": True, "piano_present": True},
            "voicing_override": _explicit_voicing_capability_usage_override(),
        }
    )
    debug = dict(result.debug)
    piano_voicing_rows = _piano_voicing_rows(debug)
    piano_pattern_rows = _piano_pattern_rows(debug)
    bass = dict(debug.get("bass_foundation_audit") or {})
    expression = dict(debug.get("expression_foundation_audit") or {})
    pedal = dict(debug.get("pedal_realization_audit") or {})
    note_counts = dict(debug.get("note_events_by_track") or {})
    two_beat_rows = [row for row in piano_pattern_rows if row.get("region_length_family") == "two_beat_region" and row.get("status") != "suppressed"]
    two_beat_relief_rows = [row for row in two_beat_rows if row.get("two_beat_relief_applied")]
    multi_touch_two_beat_rows = [row for row in two_beat_relief_rows if int(row.get("two_beat_relief_event_count") or 0) > 1]
    start_anchor_two_beat_rows = [row for row in two_beat_relief_rows if row.get("two_beat_relief_status") == "simple_anchor_preferred"]
    anticipation_rows = [row for row in piano_pattern_rows if row.get("anticipation_kind") == "next_beat1_to_previous_tail"]
    two_beat_anticipations = [row for row in anticipation_rows if row.get("anticipation_previous_region_duration_beats") == 2.0]
    invalid_anticipations = [row for row in anticipation_rows if not _valid_region_first_anticipation(row)]
    density_counts = Counter(str(row["density"]) for row in piano_voicing_rows)
    recipe_counts = Counter(str(row["recipe_id"]) for row in piano_voicing_rows)
    optional_rows = [row for row in piano_pattern_rows if row.get("optional_selected")]
    five_six = [row for row in piano_voicing_rows if int(row.get("density") or 0) in {5, 6}]
    bar_88_rows = [row for row in piano_voicing_rows if slug == "all_the_things_you_are" and int(row.get("region_performance_bar_index") or -1) == 87]
    return {
        "ok": bool(result.ok),
        "title": score.get("title"),
        "slug": slug,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "written_bars": debug.get("written_bars"),
        "performance_choruses": debug.get("performance_choruses"),
        "performance_bars": debug.get("performance_bars"),
        "note_events_by_track": note_counts,
        "track_presence_ok": all(int(note_counts.get(track) or 0) > 0 for track in ("piano", "bass", "drums")),
        "piano_note_events": int(note_counts.get("piano") or 0),
        "bass_note_events": int(note_counts.get("bass") or 0),
        "drum_note_events": int(note_counts.get("drums") or 0),
        "piano_active_pattern_events": len([row for row in piano_pattern_rows if row.get("status") != "suppressed"]),
        "piano_two_beat_active_events": len(two_beat_rows),
        "two_beat_density_relief_applied_events": len(two_beat_relief_rows),
        "two_beat_start_anchor_events": len(start_anchor_two_beat_rows),
        "two_beat_multi_touch_events": len(multi_touch_two_beat_rows),
        "two_beat_anchor_ratio": round(len(start_anchor_two_beat_rows) / max(1, len(two_beat_relief_rows)), 4),
        "two_beat_multi_touch_ratio": round(len(multi_touch_two_beat_rows) / max(1, len(two_beat_relief_rows)), 4),
        "two_beat_pattern_counts": dict(Counter(str(row.get("pattern_id")) for row in two_beat_rows)),
        "two_beat_relief_status_counts": dict(Counter(str(row.get("two_beat_relief_status")) for row in two_beat_relief_rows)),
        "active_anticipation_count": len(anticipation_rows),
        "two_beat_previous_tail_anticipation_count": len(two_beat_anticipations),
        "invalid_region_first_anticipations": invalid_anticipations[:10],
        "sample_anticipations": anticipation_rows[:8],
        "piano_voicing_events": len(piano_voicing_rows),
        "density_counts": dict(density_counts),
        "recipe_counts": dict(recipe_counts),
        "grouped_spread_events": sum(1 for row in piano_voicing_rows if str(row.get("recipe_id") or "").startswith("spread_")),
        "five_note_events": sum(1 for row in piano_voicing_rows if int(row.get("density") or 0) == 5),
        "six_note_events": sum(1 for row in piano_voicing_rows if int(row.get("density") or 0) == 6),
        "ordinary_body_5_6_events": sum(1 for row in five_six if not row.get("authorized_5_6_scene")),
        "max_top_note": max((int(row.get("top_note") or 0) for row in piano_voicing_rows), default=0),
        "min_piano_low_note": min((int(row.get("low_note") or 128) for row in piano_voicing_rows if row.get("low_note") is not None), default=128),
        "voice_leading_warning_events": sum(1 for row in piano_voicing_rows if row.get("top_voice_leap_exceeds_max")),
        "low_register_dense_events": sum(1 for row in piano_voicing_rows if int(row.get("notes_below_c3") or 0) > 1),
        "bar_88_rows": bar_88_rows,
        "bar_88_low_register_dense_events": sum(1 for row in bar_88_rows if int(row.get("notes_below_c3") or 0) > 1),
        "optional_selected_events": len(optional_rows),
        "optional_selected_ratio": round(len(optional_rows) / max(1, len(piano_pattern_rows)), 4),
        "consecutive_optional_events": _count_consecutive(optional_rows, key="region_performance_bar_index"),
        "bass_span_violations": int(bass.get("span_violations") or 0),
        "bass_target_continuity_mismatches": int(bass.get("target_continuity_mismatches") or 0),
        "bass_repeated_root_violations": int(bass.get("repeated_root_violations") or 0),
        "bass_root_echo_bad_same": int(bass.get("root_echo_bad_same") or 0),
        "bass_root_echo_bad_timing": int(bass.get("root_echo_bad_timing") or 0),
        "pedal_cc64_event_count": int(pedal.get("cc64_event_count") or 0),
        "pedal_warning_count": int(pedal.get("repedal_warning_count") or 0),
        "expression_warning_count": int(expression.get("warning_count") or 0),
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
                "status": event.get("status"),
                "pattern_id": event.get("pattern_id"),
                "rhythm_family": metadata.get("rhythm_family"),
                "region_length_family": metadata.get("region_length_family"),
                "region_performance_bar_index": metadata.get("region_performance_bar_index"),
                "two_beat_relief_applied": bool(metadata.get("two_beat_region_density_relief_policy_applied")),
                "two_beat_relief_status": metadata.get("two_beat_region_density_relief_status"),
                "two_beat_relief_event_count": metadata.get("two_beat_region_density_relief_event_count"),
                "optional_selected": bool(metadata.get("optional_fill_variation_selected")),
                "optional_type": metadata.get("optional_fill_variation_type"),
                "anticipation_kind": anticipation.get("kind"),
                "anticipation_policy": anticipation.get("policy"),
                "anticipation_previous_region_duration_beats": _to_float(anticipation.get("previous_region_duration_beats")),
                "anticipation_current_region_duration_beats": _to_float(anticipation.get("current_region_duration_beats")),
                "anticipation_target_local_beat_in_previous": _to_float(anticipation.get("target_local_beat_in_previous")),
                "anticipation_previous_region_last_beat_local": _to_float(anticipation.get("previous_region_last_beat_local")),
                "anticipation_previous_region_last_upbeat_local": _to_float(anticipation.get("previous_region_last_upbeat_local")),
                "anticipation_tail_checked_local_beats": tuple(anticipation.get("tail_checked_local_beats") or ()),
                "anticipation_region_first_version": anticipation.get("region_first_anticipation_compatibility_checkpoint_version"),
                "anticipation_bar_first_4and_assumption": anticipation.get("bar_first_4and_assumption"),
            }
        )
    return sorted(rows, key=lambda row: (int(row.get("region_performance_bar_index") or 0), str(row.get("event_id"))))


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
        is_last_chorus = int(event_metadata.get("region_chorus_index") or 0) == int(event_metadata.get("region_total_choruses") or -1) - 1
        authorized_5_6_scene = bool(
            density in {5, 6}
            and is_last_chorus
            and (event_metadata.get("region_is_last_bar_of_section") or event_metadata.get("region_is_last_bar_of_chorus"))
        )
        rows.append(
            {
                "event_id": event.get("event_id"),
                "region_id": event.get("region_id"),
                "chord_symbol": event.get("chord_symbol"),
                "pattern_id": event.get("pattern_id"),
                "density": density,
                "disposition": voicing.get("disposition"),
                "recipe_id": voicing.get("recipe_id"),
                "functional_grouping": voicing.get("functional_grouping"),
                "midi_notes": notes,
                "notes_below_c3": sum(1 for note in notes if int(note) < 48),
                "low_note": min(notes) if notes else None,
                "top_note": max(notes) if notes else None,
                "region_chorus_index": event_metadata.get("region_chorus_index"),
                "region_total_choruses": event_metadata.get("region_total_choruses"),
                "region_is_last_bar_of_section": bool(event_metadata.get("region_is_last_bar_of_section")),
                "region_is_last_bar_of_chorus": bool(event_metadata.get("region_is_last_bar_of_chorus")),
                "region_performance_bar_index": event_metadata.get("region_performance_bar_index"),
                "authorized_5_6_scene": authorized_5_6_scene,
                "top_voice_leap_exceeds_max": bool(voice_leading.get("top_voice_leap_exceeds_max")),
                "top_voice_abs_motion": voice_leading.get("top_voice_abs_motion"),
            }
        )
    return rows


def _valid_region_first_anticipation(row: Mapping[str, Any]) -> bool:
    if row.get("anticipation_region_first_version") != "v2_6_61":
        return False
    if row.get("anticipation_bar_first_4and_assumption") is not False:
        return False
    previous_duration = row.get("anticipation_previous_region_duration_beats")
    target = row.get("anticipation_target_local_beat_in_previous")
    last_beat = row.get("anticipation_previous_region_last_beat_local")
    last_upbeat = row.get("anticipation_previous_region_last_upbeat_local")
    checked = tuple(row.get("anticipation_tail_checked_local_beats") or ())
    if previous_duration is None or target is None:
        return False
    expected_last_beat = round(max(0.0, float(previous_duration) - 1.0), 6)
    expected_last_upbeat = round(max(0.0, float(previous_duration) - 0.5), 6)
    return (
        round(float(target), 6) == expected_last_upbeat
        and round(float(last_beat or 0.0), 6) == expected_last_beat
        and round(float(last_upbeat or 0.0), 6) == expected_last_upbeat
        and tuple(round(float(item), 6) for item in checked) == (expected_last_beat, expected_last_upbeat)
    )


def _aggregate(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    total_piano_voicing = sum(int(out.get("piano_voicing_events") or 0) for out in outputs)
    total_piano_patterns = sum(int(out.get("piano_active_pattern_events") or 0) for out in outputs)
    total_two = sum(int(out.get("piano_two_beat_active_events") or 0) for out in outputs)
    total_two_multi = sum(int(out.get("two_beat_multi_touch_events") or 0) for out in outputs)
    total_two_anchor = sum(int(out.get("two_beat_start_anchor_events") or 0) for out in outputs)
    five_note = sum(int(out.get("five_note_events") or 0) for out in outputs)
    six_note = sum(int(out.get("six_note_events") or 0) for out in outputs)
    optional = sum(int(out.get("optional_selected_events") or 0) for out in outputs)
    return {
        "tracks_with_events_all_tunes": all(bool(out.get("track_presence_ok")) for out in outputs),
        "piano_note_events": sum(int(out.get("piano_note_events") or 0) for out in outputs),
        "bass_note_events": sum(int(out.get("bass_note_events") or 0) for out in outputs),
        "drum_note_events": sum(int(out.get("drum_note_events") or 0) for out in outputs),
        "piano_active_pattern_events": total_piano_patterns,
        "piano_voicing_events": total_piano_voicing,
        "piano_two_beat_active_events": total_two,
        "two_beat_multi_touch_events": total_two_multi,
        "two_beat_start_anchor_events": total_two_anchor,
        "two_beat_multi_touch_ratio": round(total_two_multi / max(1, total_two), 4),
        "two_beat_anchor_ratio": round(total_two_anchor / max(1, total_two), 4),
        "active_anticipation_count": sum(int(out.get("active_anticipation_count") or 0) for out in outputs),
        "two_beat_previous_tail_anticipation_count": sum(int(out.get("two_beat_previous_tail_anticipation_count") or 0) for out in outputs),
        "grouped_spread_events": sum(int(out.get("grouped_spread_events") or 0) for out in outputs),
        "five_note_events": five_note,
        "six_note_events": six_note,
        "five_six_ratio": round((five_note + six_note) / max(1, total_piano_voicing), 4),
        "ordinary_body_5_6_events": sum(int(out.get("ordinary_body_5_6_events") or 0) for out in outputs),
        "optional_selected_events": optional,
        "optional_selected_ratio": round(optional / max(1, total_piano_patterns), 4),
        "consecutive_optional_events": sum(int(out.get("consecutive_optional_events") or 0) for out in outputs),
        "voice_leading_warning_events": sum(int(out.get("voice_leading_warning_events") or 0) for out in outputs),
        "low_register_dense_events": sum(int(out.get("low_register_dense_events") or 0) for out in outputs),
        "bar_88_low_register_dense_events": sum(int(out.get("bar_88_low_register_dense_events") or 0) for out in outputs),
        "max_top_note": max((int(out.get("max_top_note") or 0) for out in outputs), default=0),
        "min_piano_low_note": min((int(out.get("min_piano_low_note") or 128) for out in outputs), default=128),
        "bass_span_violations": sum(int(out.get("bass_span_violations") or 0) for out in outputs),
        "bass_target_continuity_mismatches": sum(int(out.get("bass_target_continuity_mismatches") or 0) for out in outputs),
        "bass_repeated_root_violations": sum(int(out.get("bass_repeated_root_violations") or 0) for out in outputs),
        "bass_root_echo_bad_same": sum(int(out.get("bass_root_echo_bad_same") or 0) for out in outputs),
        "bass_root_echo_bad_timing": sum(int(out.get("bass_root_echo_bad_timing") or 0) for out in outputs),
        "pedal_cc64_event_count": sum(int(out.get("pedal_cc64_event_count") or 0) for out in outputs),
        "pedal_warning_count": sum(int(out.get("pedal_warning_count") or 0) for out in outputs),
        "expression_warning_count": sum(int(out.get("expression_warning_count") or 0) for out in outputs),
    }


def _acceptance(static: Mapping[str, Any], outputs: list[dict[str, Any]], aggregate: Mapping[str, Any]) -> dict[str, Any]:
    by_slug = {str(output.get("slug")): output for output in outputs}
    autumn = by_slug.get("autumn_leaves", {})
    all_things = by_slug.get("all_the_things_you_are", {})
    checks = [
        {"name": "v2_6_81 checkpoint declared", "passed": static.get("checkpoint_policy_version") == MILESTONE_ID and bool(static.get("checkpoint_policy_enabled"))},
        {"name": "v2_6_80 density relief still declared", "passed": static.get("two_beat_density_relief_policy_version") == "v2_6_80" and bool(static.get("two_beat_density_relief_policy_enabled"))},
        {"name": "generic region-first anticipation checkpoint retained", "passed": static.get("anticipation_checkpoint_version") == "v2_6_61"},
        {"name": "low-register clarity guard retained", "passed": static.get("low_register_clarity_guard_version") == "v2_6_78" and bool(static.get("low_register_clarity_guard_enabled"))},
        {"name": "existing 5/6-note capability remains explicit opt-in", "passed": static.get("existing_voicing_capability_policy_version") == "v2_6_77" and bool(static.get("existing_voicing_capability_available")) and not bool(static.get("existing_voicing_capability_default_enabled")) and not bool(static.get("existing_voicing_capability_ordinary_runtime_default"))},
        {"name": "no core voicing change declared", "passed": bool(static.get("existing_voicing_capability_no_core_voicing_change"))},
        {"name": "base policy still open/drop 4-note", "passed": static.get("base_preferred_density") == 4 and static.get("base_preferred_disposition") == "open"},
        {"name": "patterns still no expression/voicing leakage", "passed": not static.get("pattern_forbidden_expression_candidates") and not static.get("pattern_forbidden_voicing_candidates")},
        {"name": "patterns remain ChordRegion-first", "passed": not static.get("bar_first_two_chord_bar_candidates")},
        {"name": "all tracks present", "passed": bool(aggregate.get("tracks_with_events_all_tunes"))},
        {"name": "All The Things not over-thinned", "passed": int(all_things.get("piano_active_pattern_events") or 0) >= 175 and int(all_things.get("piano_two_beat_active_events") or 0) >= 20},
        {"name": "Autumn Leaves relieved but not sparse", "passed": 175 <= int(autumn.get("piano_active_pattern_events") or 0) <= 205},
        {"name": "Autumn Leaves two-beat multi-touch remains rare", "passed": int(autumn.get("two_beat_multi_touch_events", 999)) <= 8},
        {"name": "Autumn Leaves simple anchors dominate two-beat regions", "passed": float(autumn.get("two_beat_anchor_ratio") or 0.0) >= 0.70},
        {"name": "All The Things two-beat remains relaxed", "passed": int(all_things.get("two_beat_multi_touch_events", 999)) <= 4},
        {"name": "generic anticipation active on both tunes", "passed": int(all_things.get("active_anticipation_count") or 0) > 0 and int(autumn.get("active_anticipation_count") or 0) > 0},
        {"name": "2-beat previous-tail anticipation observed", "passed": int(aggregate.get("two_beat_previous_tail_anticipation_count") or 0) > 0},
        {"name": "no invalid region-first anticipations", "passed": all(not output.get("invalid_region_first_anticipations") for output in outputs)},
        {"name": "explicit 5/6-note usage remains low intrusion", "passed": 0 < float(aggregate.get("five_six_ratio") or 0.0) <= 0.06},
        {"name": "ordinary body not thickened", "passed": int(aggregate.get("ordinary_body_5_6_events") or 0) == 0},
        {"name": "optional fill/variation remains low intrusion", "passed": float(aggregate.get("optional_selected_ratio") or 0.0) <= 0.03},
        {"name": "no consecutive optional events", "passed": int(aggregate.get("consecutive_optional_events") or 0) == 0},
        {"name": "voice-leading guard ok", "passed": int(aggregate.get("voice_leading_warning_events") or 0) == 0},
        {"name": "low-register clarity guard ok", "passed": int(aggregate.get("low_register_dense_events") or 0) == 0 and int(aggregate.get("bar_88_low_register_dense_events") or 0) == 0},
        {"name": "top register ok", "passed": int(aggregate.get("max_top_note", 999)) <= 74},
        {"name": "bass foundation audit ok", "passed": int(aggregate.get("bass_span_violations") or 0) == 0 and int(aggregate.get("bass_target_continuity_mismatches") or 0) == 0 and int(aggregate.get("bass_repeated_root_violations") or 0) == 0},
        {"name": "root echo audit ok", "passed": int(aggregate.get("bass_root_echo_bad_same") or 0) == 0 and int(aggregate.get("bass_root_echo_bad_timing") or 0) == 0},
        {"name": "dry Medium Swing pedal", "passed": int(aggregate.get("pedal_cc64_event_count") or 0) == 0 and int(aggregate.get("pedal_warning_count") or 0) == 0},
    ]
    return {"passed": all(item["passed"] for item in checks), "checks": checks}


def _render_report(summary: Mapping[str, Any]) -> str:
    acc = summary["acceptance"]
    agg = summary["aggregate"]
    lines = [
        f"# {MILESTONE_LABEL}",
        "",
        f"Acceptance Passed: **{acc['passed']}**",
        "",
        "## Scope",
        str(summary["scope"]),
        "",
        "## Aggregate Full-Band Audit",
        f"- Tracks present in all tunes: {agg['tracks_with_events_all_tunes']}",
        f"- Note events by track: piano={agg['piano_note_events']}, bass={agg['bass_note_events']}, drums={agg['drum_note_events']}",
        f"- Piano active pattern events: {agg['piano_active_pattern_events']}",
        f"- Piano 2-beat active / multi-touch / anchor: {agg['piano_two_beat_active_events']} / {agg['two_beat_multi_touch_events']} / {agg['two_beat_start_anchor_events']}",
        f"- 2-beat anchor ratio / multi-touch ratio: {agg['two_beat_anchor_ratio']} / {agg['two_beat_multi_touch_ratio']}",
        f"- Active anticipations / 2-beat previous-tail anticipations: {agg['active_anticipation_count']} / {agg['two_beat_previous_tail_anticipation_count']}",
        f"- Piano voicing events: {agg['piano_voicing_events']}",
        f"- Grouped SPREAD events: {agg['grouped_spread_events']}",
        f"- 5-note / 6-note events: {agg['five_note_events']} / {agg['six_note_events']}",
        f"- 5/6 ratio: {agg['five_six_ratio']}",
        f"- Ordinary-body 5/6 events: {agg['ordinary_body_5_6_events']}",
        f"- Optional selected events / ratio: {agg['optional_selected_events']} / {agg['optional_selected_ratio']}",
        f"- Consecutive optional events: {agg['consecutive_optional_events']}",
        f"- Voice-leading warnings: {agg['voice_leading_warning_events']}",
        f"- Low-register dense events (>1 piano note below C3): {agg['low_register_dense_events']}",
        f"- Bar 88 low-register dense events: {agg['bar_88_low_register_dense_events']}",
        f"- Piano low/top note range: {agg['min_piano_low_note']}–{agg['max_top_note']}",
        f"- Bass span / continuity / repeated-root violations: {agg['bass_span_violations']} / {agg['bass_target_continuity_mismatches']} / {agg['bass_repeated_root_violations']}",
        f"- Bass root-echo bad same/timing: {agg['bass_root_echo_bad_same']} / {agg['bass_root_echo_bad_timing']}",
        f"- Pedal CC64 / warnings: {agg['pedal_cc64_event_count']} / {agg['pedal_warning_count']}",
        "",
        "## Per Tune",
    ]
    for out in summary["outputs"]:
        lines.extend(
            [
                f"### {out['title']}",
                f"- MIDI: `{out['midi_path']}`",
                f"- Performance: {out['performance_choruses']} choruses, {out['performance_bars']} bars",
                f"- Note events by track: `{out['note_events_by_track']}`",
                f"- Piano active / 2-beat active: {out['piano_active_pattern_events']} / {out['piano_two_beat_active_events']}",
                f"- 2-beat start anchors / multi-touch: {out['two_beat_start_anchor_events']} / {out['two_beat_multi_touch_events']}",
                f"- 2-beat pattern counts: `{out['two_beat_pattern_counts']}`",
                f"- 2-beat relief status counts: `{out['two_beat_relief_status_counts']}`",
                f"- Active anticipations / 2-beat previous-tail: {out['active_anticipation_count']} / {out['two_beat_previous_tail_anticipation_count']}",
                f"- Piano density counts: `{out['density_counts']}`",
                f"- Piano recipe counts: `{out['recipe_counts']}`",
                f"- 5-note / 6-note: {out['five_note_events']} / {out['six_note_events']}",
                f"- Optional selected events / ratio: {out['optional_selected_events']} / {out['optional_selected_ratio']}",
                f"- Low-register dense events: {out['low_register_dense_events']}",
                f"- Bar 88 rows: `{out.get('bar_88_rows')}`",
                "",
            ]
        )
    lines.extend(["## Acceptance Checks", ""])
    for check in acc["checks"]:
        mark = "✅" if check["passed"] else "❌"
        lines.append(f"- {mark} {check['name']}")
    lines.append("")
    return "\n".join(lines)


def _count_consecutive(rows: list[Mapping[str, Any]], *, key: str) -> int:
    values = sorted(int(row.get(key) or -1000) for row in rows)
    return sum(1 for previous, current in zip(values, values[1:]) if current == previous or current == previous + 1)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    main()
