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

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_82"
MILESTONE_LABEL = "v2_6_82 — Medium Swing Bass–Piano Interaction Audit"

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
            "Full-band bass–piano interaction audit after v2_6_80/v2_6_81. It checks piano/bass low-register overlap, "
            "exact low unisons, two-beat region density sharing, bass continuity, optional 5/6-note SPREAD intrusion, "
            "and dry Medium Swing pedal behavior. For explicitly enabled optional 5/6-note grouped SPREAD demos, v2_6_82 "
            "requests stricter C3+ foundation-register metadata through the existing style/event policy adapter so piano does "
            "not duplicate the bass walking foundation in the low register. Core voicing internals, pattern rhythm, expression "
            "numbers, API, Agent, and HarmonyOS are unchanged."
        ),
        "static_audit": static_audit,
        "outputs": outputs,
        "aggregate": aggregate,
        "acceptance": _acceptance(static_audit, outputs, aggregate),
        "recommended_next_task": "medium_swing_drum_piano_interaction_audit_or_phase_baseline_checkpoint",
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_bass_piano_interaction_audit_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_bass_piano_interaction_audit_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": summary["acceptance"]}, indent=2, ensure_ascii=False))
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    arrangement = arrangement_policy.get_arrangement_policy()
    policy = voicing_policy.get_voicing_policy()
    nested = dict(policy.metadata.get("medium_swing_existing_voicing_capability_usage_policy") or {})
    return {
        "checkpoint_version": MILESTONE_ID,
        "bass_piano_interaction_audit_enabled": bool(arrangement.get("medium_swing_bass_piano_interaction_audit")),
        "bass_piano_interaction_audit_version": arrangement.get("medium_swing_bass_piano_interaction_audit_version"),
        "bass_piano_interaction_audit_contract": arrangement.get("medium_swing_bass_piano_interaction_audit_contract"),
        "previous_full_band_checkpoint_version": arrangement.get("medium_swing_full_band_post_density_relief_checkpoint_version"),
        "two_beat_density_relief_policy_version": arrangement.get("piano_comping_two_beat_region_density_relief_policy_version"),
        "existing_voicing_capability_policy_version": arrangement.get("medium_swing_existing_voicing_capability_usage_policy_version"),
        "low_register_clarity_guard_version": arrangement.get("medium_swing_existing_voicing_capability_low_register_clarity_guard_version"),
        "bass_piano_interaction_guard_version": nested.get("bass_piano_interaction_guard_version"),
        "bass_piano_interaction_guard_enabled": bool(nested.get("bass_piano_interaction_guard_enabled")),
        "bass_piano_interaction_register_floor": nested.get("bass_piano_interaction_register_floor"),
        "bass_piano_interaction_spread_root_bass_anchor_low": nested.get("bass_piano_interaction_spread_root_bass_anchor_low"),
        "bass_piano_interaction_spread_root_bass_anchor_high": nested.get("bass_piano_interaction_spread_root_bass_anchor_high"),
        "bass_piano_interaction_spread_root_bass_anchor_target": nested.get("bass_piano_interaction_spread_root_bass_anchor_target"),
        "existing_voicing_capability_available": bool(nested.get("available")),
        "existing_voicing_capability_default_enabled": bool(nested.get("enabled")),
        "existing_voicing_capability_ordinary_runtime_default": bool(nested.get("ordinary_runtime_default")),
        "existing_voicing_capability_no_core_voicing_change": bool(nested.get("no_core_voicing_change")),
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
                "activation": "explicit_v2_6_82_bass_piano_interaction_audit_demo",
                "scope": "event_scoped_style_policy_only",
                "ordinary_body": "keep_open_drop_4note",
                "authorized_scenes": ["final_chorus_section_tail_support", "final_ending_climax"],
                "requested_existing_contracts": [
                    "spread_2plus3_contract",
                    "spread_2plus4_contract",
                    "spread_3plus3_contract",
                ],
                "low_register_clarity_guard_version": "v2_6_78",
                "low_register_clarity_guard_enabled": True,
                "low_register_clarity_threshold": 48,
                "low_register_clarity_max_notes_below": 1,
                "bass_piano_interaction_guard_version": MILESTONE_ID,
                "bass_piano_interaction_guard_enabled": True,
                "bass_piano_interaction_register_floor": 48,
                "bass_piano_interaction_spread_root_bass_anchor_low": 48,
                "bass_piano_interaction_spread_root_bass_anchor_high": 60,
                "bass_piano_interaction_spread_root_bass_anchor_target": 54,
                "bass_piano_interaction_guard_contract": "request existing grouped-SPREAD candidates from C3+ foundation registers in bass-present full-band demos; event-scoped style metadata only",
                "no_core_voicing_change": True,
                "ordinary_runtime_default": False,
            },
        },
    }


def _generate_and_audit(spec: Mapping[str, Any]) -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / str(spec["leadsheet"])).read_text(encoding="utf-8"))
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_medium_swing_bass_piano_interaction_audit_demo.mid"
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
    bass_rows = _bass_segment_rows(debug)
    bass_by_region = {str(row["region_id"]): row for row in bass_rows}
    interaction = _bass_piano_interaction_metrics(piano_voicing_rows, piano_pattern_rows, bass_by_region)
    bass = dict(debug.get("bass_foundation_audit") or {})
    pedal = dict(debug.get("pedal_realization_audit") or {})
    note_counts = dict(debug.get("note_events_by_track") or {})
    two_beat_rows = [row for row in piano_pattern_rows if row.get("region_length_family") == "two_beat_region" and row.get("status") != "suppressed"]
    two_beat_anchor_rows = [row for row in two_beat_rows if row.get("two_beat_relief_status") == "simple_anchor_preferred"]
    anticipation_rows = [row for row in piano_pattern_rows if row.get("anticipation_kind") == "next_beat1_to_previous_tail"]
    two_beat_anticipations = [row for row in anticipation_rows if row.get("anticipation_previous_region_duration_beats") == 2.0]
    five_six = [row for row in piano_voicing_rows if int(row.get("density") or 0) in {5, 6}]
    optional_rows = [row for row in piano_pattern_rows if row.get("optional_selected")]
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
        "two_beat_start_anchor_events": len(two_beat_anchor_rows),
        "two_beat_anchor_ratio": round(len(two_beat_anchor_rows) / max(1, len(two_beat_rows)), 4),
        "two_beat_multi_touch_events": len([row for row in two_beat_rows if int(row.get("two_beat_relief_event_count") or 0) > 1]),
        "active_anticipation_count": len(anticipation_rows),
        "two_beat_previous_tail_anticipation_count": len(two_beat_anticipations),
        "piano_voicing_events": len(piano_voicing_rows),
        "density_counts": dict(Counter(str(row.get("density")) for row in piano_voicing_rows)),
        "recipe_counts": dict(Counter(str(row.get("recipe_id")) for row in piano_voicing_rows)),
        "grouped_spread_events": sum(1 for row in piano_voicing_rows if str(row.get("recipe_id") or "").startswith("spread_")),
        "five_note_events": sum(1 for row in piano_voicing_rows if int(row.get("density") or 0) == 5),
        "six_note_events": sum(1 for row in piano_voicing_rows if int(row.get("density") or 0) == 6),
        "ordinary_body_5_6_events": sum(1 for row in five_six if not row.get("authorized_5_6_scene")),
        "five_six_low_below_c3_events": sum(1 for row in five_six if int(row.get("low_note") or 128) < 48),
        "max_top_note": max((int(row.get("top_note") or 0) for row in piano_voicing_rows), default=0),
        "min_piano_low_note": min((int(row.get("low_note") or 128) for row in piano_voicing_rows if row.get("low_note") is not None), default=128),
        "voice_leading_warning_events": sum(1 for row in piano_voicing_rows if row.get("top_voice_leap_exceeds_max")),
        "low_register_dense_events": sum(1 for row in piano_voicing_rows if int(row.get("notes_below_c3") or 0) > 1),
        "bar_88_rows": bar_88_rows,
        "bar_88_low_register_dense_events": sum(1 for row in bar_88_rows if int(row.get("notes_below_c3") or 0) > 1),
        "bar_88_bass_piano_exact_low_unison_events": interaction["bar_88_bass_piano_exact_low_unison_events"],
        "optional_selected_events": len(optional_rows),
        "optional_selected_ratio": round(len(optional_rows) / max(1, len(piano_pattern_rows)), 4),
        "bass_segments": len(bass_rows),
        "bass_span_violations": int(bass.get("span_violations") or 0),
        "bass_target_continuity_mismatches": int(bass.get("target_continuity_mismatches") or 0),
        "bass_repeated_root_violations": int(bass.get("repeated_root_violations") or 0),
        "bass_root_echo_bad_same": int(bass.get("root_echo_bad_same") or 0),
        "bass_root_echo_bad_timing": int(bass.get("root_echo_bad_timing") or 0),
        "pedal_cc64_event_count": int(pedal.get("cc64_event_count") or 0),
        "pedal_warning_count": int(pedal.get("repedal_warning_count") or 0),
        **interaction,
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
                "region_id": event.get("region_id"),
                "pattern_id": event.get("pattern_id"),
                "rhythm_family": metadata.get("rhythm_family"),
                "region_length_family": metadata.get("region_length_family"),
                "region_performance_bar_index": metadata.get("region_performance_bar_index"),
                "two_beat_relief_status": metadata.get("two_beat_region_density_relief_status"),
                "two_beat_relief_event_count": metadata.get("two_beat_region_density_relief_event_count"),
                "optional_selected": bool(metadata.get("optional_fill_variation_selected")),
                "anticipation_kind": anticipation.get("kind"),
                "anticipation_previous_region_duration_beats": _to_float(anticipation.get("previous_region_duration_beats")),
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
                "recipe_id": voicing.get("recipe_id"),
                "midi_notes": notes,
                "notes_below_c3": sum(1 for note in notes if int(note) < 48),
                "low_note": min(notes) if notes else None,
                "top_note": max(notes) if notes else None,
                "region_performance_bar_index": event_metadata.get("region_performance_bar_index"),
                "region_length_family": event_metadata.get("region_length_family"),
                "authorized_5_6_scene": authorized_5_6_scene,
                "top_voice_leap_exceeds_max": bool(voice_leading.get("top_voice_leap_exceeds_max")),
            }
        )
    return rows


def _bass_segment_rows(debug: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in (dict(debug.get("bass_foundation_plan") or {}).get("segments") or []):
        if not isinstance(raw, Mapping):
            continue
        notes = [int(note) for note in raw.get("notes") or [] if note is not None]
        if not notes:
            continue
        rows.append(
            {
                "region_id": raw.get("region_id"),
                "chord_symbol": raw.get("chord_symbol"),
                "candidate": raw.get("candidate"),
                "notes": notes,
                "low_note": min(notes),
                "high_note": max(notes),
                "selected_lane": raw.get("selected_lane"),
                "beat4_connector_kind": raw.get("beat4_connector_kind"),
            }
        )
    return rows


def _bass_piano_interaction_metrics(
    piano_rows: list[Mapping[str, Any]],
    pattern_rows: list[Mapping[str, Any]],
    bass_by_region: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    pattern_by_event = {str(row.get("event_id")): row for row in pattern_rows}
    joined = []
    exact_low_unison = []
    close_low_spacing = []
    foundation_gap_too_tight = []
    five_six_exact_low_unison = []
    five_six_low_below_c3 = []
    bar_88_exact_low_unison = []
    two_beat_non_anchor = []
    two_beat_with_bass_compact = []
    for row in piano_rows:
        region_id = str(row.get("region_id"))
        bass = bass_by_region.get(region_id)
        if not bass:
            continue
        notes = [int(note) for note in row.get("midi_notes") or []]
        bass_notes = [int(note) for note in bass.get("notes") or []]
        if not notes or not bass_notes:
            continue
        low = min(notes)
        bass_high = max(bass_notes)
        min_low_distance = min(abs(low - bass_note) for bass_note in bass_notes)
        pattern = pattern_by_event.get(str(row.get("event_id")), {})
        joined_row = {
            "event_id": row.get("event_id"),
            "region_id": region_id,
            "bar": row.get("region_performance_bar_index"),
            "pattern_id": row.get("pattern_id"),
            "region_length_family": pattern.get("region_length_family") or row.get("region_length_family"),
            "piano_low_note": low,
            "piano_notes": notes,
            "bass_notes": bass_notes,
            "bass_high_note": bass_high,
            "piano_low_to_bass_high_gap": low - bass_high,
            "min_piano_low_to_bass_note_distance": min_low_distance,
            "density": row.get("density"),
            "recipe_id": row.get("recipe_id"),
        }
        joined.append(joined_row)
        if low < 52 and low in bass_notes:
            exact_low_unison.append(joined_row)
            if int(row.get("region_performance_bar_index") or -1) == 87:
                bar_88_exact_low_unison.append(joined_row)
        if low < 52 and min_low_distance <= 2:
            close_low_spacing.append(joined_row)
        if low < 55 and (low - bass_high) <= 2:
            foundation_gap_too_tight.append(joined_row)
        if int(row.get("density") or 0) in {5, 6}:
            if low < 48:
                five_six_low_below_c3.append(joined_row)
            if low < 52 and low in bass_notes:
                five_six_exact_low_unison.append(joined_row)
        if joined_row["region_length_family"] == "two_beat_region":
            if len(bass_notes) <= 2:
                two_beat_with_bass_compact.append(joined_row)
            if row.get("pattern_id") != "medium_swing_piano_two_beat_region_start_anchor":
                two_beat_non_anchor.append(joined_row)
    return {
        "bass_piano_joined_events": len(joined),
        "bass_piano_exact_low_unison_events": len(exact_low_unison),
        "bass_piano_close_low_spacing_events": len(close_low_spacing),
        "bass_piano_foundation_gap_too_tight_events": len(foundation_gap_too_tight),
        "five_six_exact_low_unison_events": len(five_six_exact_low_unison),
        "five_six_low_below_c3_interaction_events": len(five_six_low_below_c3),
        "bar_88_bass_piano_exact_low_unison_events": len(bar_88_exact_low_unison),
        "two_beat_bass_compact_joined_events": len(two_beat_with_bass_compact),
        "two_beat_piano_non_anchor_with_bass_events": len(two_beat_non_anchor),
        "bass_piano_exact_low_unison_samples": exact_low_unison[:8],
        "bass_piano_close_low_spacing_samples": close_low_spacing[:8],
        "bass_piano_foundation_gap_too_tight_samples": foundation_gap_too_tight[:8],
    }


def _aggregate(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    total_piano_voicing = sum(int(out.get("piano_voicing_events") or 0) for out in outputs)
    total_piano_patterns = sum(int(out.get("piano_active_pattern_events") or 0) for out in outputs)
    five_note = sum(int(out.get("five_note_events") or 0) for out in outputs)
    six_note = sum(int(out.get("six_note_events") or 0) for out in outputs)
    total_two = sum(int(out.get("piano_two_beat_active_events") or 0) for out in outputs)
    total_two_anchor = sum(int(out.get("two_beat_start_anchor_events") or 0) for out in outputs)
    return {
        "tracks_with_events_all_tunes": all(bool(out.get("track_presence_ok")) for out in outputs),
        "piano_note_events": sum(int(out.get("piano_note_events") or 0) for out in outputs),
        "bass_note_events": sum(int(out.get("bass_note_events") or 0) for out in outputs),
        "drum_note_events": sum(int(out.get("drum_note_events") or 0) for out in outputs),
        "piano_active_pattern_events": total_piano_patterns,
        "piano_voicing_events": total_piano_voicing,
        "piano_two_beat_active_events": total_two,
        "two_beat_start_anchor_events": total_two_anchor,
        "two_beat_anchor_ratio": round(total_two_anchor / max(1, total_two), 4),
        "active_anticipation_count": sum(int(out.get("active_anticipation_count") or 0) for out in outputs),
        "two_beat_previous_tail_anticipation_count": sum(int(out.get("two_beat_previous_tail_anticipation_count") or 0) for out in outputs),
        "grouped_spread_events": sum(int(out.get("grouped_spread_events") or 0) for out in outputs),
        "five_note_events": five_note,
        "six_note_events": six_note,
        "five_six_ratio": round((five_note + six_note) / max(1, total_piano_voicing), 4),
        "ordinary_body_5_6_events": sum(int(out.get("ordinary_body_5_6_events") or 0) for out in outputs),
        "five_six_low_below_c3_events": sum(int(out.get("five_six_low_below_c3_events") or 0) for out in outputs),
        "five_six_low_below_c3_interaction_events": sum(int(out.get("five_six_low_below_c3_interaction_events") or 0) for out in outputs),
        "five_six_exact_low_unison_events": sum(int(out.get("five_six_exact_low_unison_events") or 0) for out in outputs),
        "bass_piano_joined_events": sum(int(out.get("bass_piano_joined_events") or 0) for out in outputs),
        "bass_piano_exact_low_unison_events": sum(int(out.get("bass_piano_exact_low_unison_events") or 0) for out in outputs),
        "bass_piano_close_low_spacing_events": sum(int(out.get("bass_piano_close_low_spacing_events") or 0) for out in outputs),
        "bass_piano_foundation_gap_too_tight_events": sum(int(out.get("bass_piano_foundation_gap_too_tight_events") or 0) for out in outputs),
        "bar_88_bass_piano_exact_low_unison_events": sum(int(out.get("bar_88_bass_piano_exact_low_unison_events") or 0) for out in outputs),
        "two_beat_bass_compact_joined_events": sum(int(out.get("two_beat_bass_compact_joined_events") or 0) for out in outputs),
        "two_beat_piano_non_anchor_with_bass_events": sum(int(out.get("two_beat_piano_non_anchor_with_bass_events") or 0) for out in outputs),
        "low_register_dense_events": sum(int(out.get("low_register_dense_events") or 0) for out in outputs),
        "voice_leading_warning_events": sum(int(out.get("voice_leading_warning_events") or 0) for out in outputs),
        "max_top_note": max((int(out.get("max_top_note") or 0) for out in outputs), default=0),
        "min_piano_low_note": min((int(out.get("min_piano_low_note") or 128) for out in outputs), default=128),
        "bass_span_violations": sum(int(out.get("bass_span_violations") or 0) for out in outputs),
        "bass_target_continuity_mismatches": sum(int(out.get("bass_target_continuity_mismatches") or 0) for out in outputs),
        "bass_repeated_root_violations": sum(int(out.get("bass_repeated_root_violations") or 0) for out in outputs),
        "bass_root_echo_bad_same": sum(int(out.get("bass_root_echo_bad_same") or 0) for out in outputs),
        "bass_root_echo_bad_timing": sum(int(out.get("bass_root_echo_bad_timing") or 0) for out in outputs),
        "pedal_cc64_event_count": sum(int(out.get("pedal_cc64_event_count") or 0) for out in outputs),
        "pedal_warning_count": sum(int(out.get("pedal_warning_count") or 0) for out in outputs),
    }


def _acceptance(static: Mapping[str, Any], outputs: list[dict[str, Any]], aggregate: Mapping[str, Any]) -> dict[str, Any]:
    by_slug = {str(output.get("slug")): output for output in outputs}
    autumn = by_slug.get("autumn_leaves", {})
    all_things = by_slug.get("all_the_things_you_are", {})
    checks = [
        {"name": "v2_6_82 bass-piano interaction audit declared", "passed": static.get("bass_piano_interaction_audit_version") == MILESTONE_ID and bool(static.get("bass_piano_interaction_audit_enabled"))},
        {"name": "post-density full-band checkpoint retained", "passed": static.get("previous_full_band_checkpoint_version") == "v2_6_81"},
        {"name": "two-beat density relief retained", "passed": static.get("two_beat_density_relief_policy_version") == "v2_6_80"},
        {"name": "existing 5/6-note capability remains explicit opt-in", "passed": static.get("existing_voicing_capability_policy_version") == "v2_6_77" and bool(static.get("existing_voicing_capability_available")) and not bool(static.get("existing_voicing_capability_default_enabled")) and not bool(static.get("existing_voicing_capability_ordinary_runtime_default"))},
        {"name": "low-register clarity guard retained", "passed": static.get("low_register_clarity_guard_version") == "v2_6_78"},
        {"name": "bass-piano interaction guard declared", "passed": static.get("bass_piano_interaction_guard_version") == MILESTONE_ID and bool(static.get("bass_piano_interaction_guard_enabled")) and int(static.get("bass_piano_interaction_register_floor") or 0) == 48},
        {"name": "no core voicing change declared", "passed": bool(static.get("existing_voicing_capability_no_core_voicing_change")) and static.get("base_preferred_density") == 4 and static.get("base_preferred_disposition") == "open"},
        {"name": "all full-band tracks present", "passed": bool(aggregate.get("tracks_with_events_all_tunes"))},
        {"name": "2-beat piano remains relieved", "passed": float(aggregate.get("two_beat_anchor_ratio") or 0.0) >= 0.80 and int(autumn.get("two_beat_multi_touch_events") or 0) <= 8},
        {"name": "All The Things not over-thinned", "passed": int(all_things.get("piano_active_pattern_events") or 0) >= 175},
        {"name": "generic anticipation still active", "passed": int(aggregate.get("active_anticipation_count") or 0) > 0 and int(aggregate.get("two_beat_previous_tail_anticipation_count") or 0) > 0},
        {"name": "explicit 5/6-note usage remains low intrusion", "passed": 0 < float(aggregate.get("five_six_ratio") or 0.0) <= 0.06 and int(aggregate.get("ordinary_body_5_6_events") or 0) == 0},
        {"name": "optional 5/6-note no longer lives below C3", "passed": int(aggregate.get("five_six_low_below_c3_events") or 0) == 0 and int(aggregate.get("five_six_low_below_c3_interaction_events") or 0) == 0},
        {"name": "optional 5/6-note avoids low bass unison", "passed": int(aggregate.get("five_six_exact_low_unison_events") or 0) == 0},
        {"name": "low-register dense piano guard ok", "passed": int(aggregate.get("low_register_dense_events") or 0) == 0},
        {"name": "bar 88 bass-piano low unison cleared", "passed": int(aggregate.get("bar_88_bass_piano_exact_low_unison_events") or 0) == 0},
        {"name": "close low spacing stays rare", "passed": int(aggregate.get("bass_piano_close_low_spacing_events") or 0) <= 6},
        {"name": "voice-leading and top register ok", "passed": int(aggregate.get("voice_leading_warning_events") or 0) == 0 and int(aggregate.get("max_top_note") or 999) <= 74},
        {"name": "bass foundation audit ok", "passed": int(aggregate.get("bass_span_violations") or 0) == 0 and int(aggregate.get("bass_target_continuity_mismatches") or 0) == 0 and int(aggregate.get("bass_repeated_root_violations") or 0) == 0},
        {"name": "root echo and dry pedal ok", "passed": int(aggregate.get("bass_root_echo_bad_same") or 0) == 0 and int(aggregate.get("bass_root_echo_bad_timing") or 0) == 0 and int(aggregate.get("pedal_cc64_event_count") or 0) == 0 and int(aggregate.get("pedal_warning_count") or 0) == 0},
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
        "## Aggregate Bass–Piano Interaction Audit",
        f"- Tracks present in all tunes: {agg['tracks_with_events_all_tunes']}",
        f"- Note events by track: piano={agg['piano_note_events']}, bass={agg['bass_note_events']}, drums={agg['drum_note_events']}",
        f"- Piano active pattern events / voicing events: {agg['piano_active_pattern_events']} / {agg['piano_voicing_events']}",
        f"- Piano 2-beat active / start anchors / anchor ratio: {agg['piano_two_beat_active_events']} / {agg['two_beat_start_anchor_events']} / {agg['two_beat_anchor_ratio']}",
        f"- Active anticipations / 2-beat previous-tail anticipations: {agg['active_anticipation_count']} / {agg['two_beat_previous_tail_anticipation_count']}",
        f"- 5-note / 6-note events / ratio: {agg['five_note_events']} / {agg['six_note_events']} / {agg['five_six_ratio']}",
        f"- 5/6 low below C3 / low unison with bass: {agg['five_six_low_below_c3_events']} / {agg['five_six_exact_low_unison_events']}",
        f"- Bass–piano joined events: {agg['bass_piano_joined_events']}",
        f"- Bass–piano exact low unisons / close low spacing: {agg['bass_piano_exact_low_unison_events']} / {agg['bass_piano_close_low_spacing_events']}",
        f"- Bass–piano foundation gap too tight events: {agg['bass_piano_foundation_gap_too_tight_events']}",
        f"- Bar 88 bass–piano exact low unisons: {agg['bar_88_bass_piano_exact_low_unison_events']}",
        f"- Piano low/top note range: {agg['min_piano_low_note']}–{agg['max_top_note']}",
        f"- Voice-leading warnings / low-register dense events: {agg['voice_leading_warning_events']} / {agg['low_register_dense_events']}",
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
                f"- Piano active / 2-beat active / 2-beat anchor ratio: {out['piano_active_pattern_events']} / {out['piano_two_beat_active_events']} / {out['two_beat_anchor_ratio']}",
                f"- Active anticipations / 2-beat previous-tail: {out['active_anticipation_count']} / {out['two_beat_previous_tail_anticipation_count']}",
                f"- Piano density counts: `{out['density_counts']}`",
                f"- Piano recipe counts: `{out['recipe_counts']}`",
                f"- 5-note / 6-note: {out['five_note_events']} / {out['six_note_events']}",
                f"- 5/6 low below C3 / low unison with bass: {out['five_six_low_below_c3_events']} / {out['five_six_exact_low_unison_events']}",
                f"- Bass–piano exact low unisons / close low spacing / tight foundation gap: {out['bass_piano_exact_low_unison_events']} / {out['bass_piano_close_low_spacing_events']} / {out['bass_piano_foundation_gap_too_tight_events']}",
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


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    main()
