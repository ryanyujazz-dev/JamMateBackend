from __future__ import annotations

import json
import math
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
from jammate_engine.styles.medium_swing import arrangement_policy, percussion_patterns, voicing_policy

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_83"
MILESTONE_LABEL = "v2_6_83 — Medium Swing Drum–Piano Interaction Audit"

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
            "Full-band drum–piano interaction checkpoint after v2_6_82. This audit reconstructs the existing "
            "Medium Swing region-local ride/hi-hat time grid for analysis only, then checks whether piano comping is "
            "overlapping too aggressively with ride accents, hi-hat 2/4, ride-skip ghosts, optional fill/variation cells, "
            "and dense 2-beat ChordRegions. No drum fills, drum patterns, piano patterns, voicing internals, expression "
            "numbers, API, Agent, or HarmonyOS behavior are changed."
        ),
        "static_audit": static_audit,
        "outputs": outputs,
        "aggregate": aggregate,
        "acceptance": _acceptance(static_audit, outputs, aggregate),
        "recommended_next_task": "medium_swing_chorus_level_arrangement_arc_checkpoint_if_drum_piano_audit_passes",
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_drum_piano_interaction_audit_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_drum_piano_interaction_audit_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": summary["acceptance"]}, indent=2, ensure_ascii=False))
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    arrangement = arrangement_policy.get_arrangement_policy()
    voicing = voicing_policy.get_voicing_policy()
    nested = dict(voicing.metadata.get("medium_swing_existing_voicing_capability_usage_policy") or {})
    four = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    two = percussion_patterns.get_pattern_candidates({"region_duration_beats": 2.0})
    return {
        "checkpoint_version": MILESTONE_ID,
        "drum_piano_interaction_audit_enabled": bool(arrangement.get("medium_swing_drum_piano_interaction_audit")),
        "drum_piano_interaction_audit_version": arrangement.get("medium_swing_drum_piano_interaction_audit_version"),
        "drum_piano_interaction_audit_contract": arrangement.get("medium_swing_drum_piano_interaction_audit_contract"),
        "previous_bass_piano_interaction_audit_version": arrangement.get("medium_swing_bass_piano_interaction_audit_version"),
        "post_density_checkpoint_version": arrangement.get("medium_swing_full_band_post_density_relief_checkpoint_version"),
        "two_beat_density_relief_policy_version": arrangement.get("piano_comping_two_beat_region_density_relief_policy_version"),
        "existing_voicing_capability_policy_version": arrangement.get("medium_swing_existing_voicing_capability_usage_policy_version"),
        "bass_piano_interaction_guard_version": nested.get("bass_piano_interaction_guard_version"),
        "existing_voicing_capability_default_enabled": bool(nested.get("enabled")),
        "existing_voicing_capability_ordinary_runtime_default": bool(nested.get("ordinary_runtime_default")),
        "no_core_voicing_change": bool(nested.get("no_core_voicing_change")),
        "four_beat_drum_candidate_names": [candidate.name for candidate in four],
        "two_beat_drum_candidate_names": [candidate.name for candidate in two],
        "four_beat_drum_event_count": sum(len(candidate.events) for candidate in four),
        "two_beat_drum_event_count": sum(len(candidate.events) for candidate in two),
        "drum_candidates_do_not_receive_next_chord_anticipation": all(not candidate.tail_policy.can_receive_next_chord_anticipation for candidate in (*four, *two)),
        "drum_candidates_are_existing_ride_time_only": all(candidate.category.startswith("ride_time") for candidate in (*four, *two)),
        "base_preferred_density": voicing.preferred_density,
        "base_preferred_disposition": voicing.preferred_disposition.value,
    }


def _explicit_voicing_capability_usage_override() -> dict[str, Any]:
    return {
        "enabled": True,
        "metadata": {
            "medium_swing_existing_voicing_capability_usage_policy": {
                "version": MILESTONE_ID,
                "available": True,
                "enabled": True,
                "activation": "explicit_v2_6_83_drum_piano_interaction_audit_demo",
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
                "drum_piano_interaction_audit_version": MILESTONE_ID,
                "drum_piano_interaction_audit_scope": "audit_only_no_behavior_change",
                "no_core_voicing_change": True,
                "ordinary_runtime_default": False,
            }
        },
    }


def _generate_and_audit(spec: Mapping[str, Any]) -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / str(spec["leadsheet"])).read_text(encoding="utf-8"))
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_medium_swing_drum_piano_interaction_audit_demo.mid"
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
    piano_pattern_rows = _piano_pattern_rows(debug)
    piano_voicing_rows = _piano_voicing_rows(debug)
    drum_piano = _drum_piano_interaction_metrics(piano_pattern_rows)
    note_counts = dict(debug.get("note_events_by_track") or {})
    bass = dict(debug.get("bass_foundation_audit") or {})
    pedal = dict(debug.get("pedal_realization_audit") or {})
    two_beat_rows = [row for row in piano_pattern_rows if row.get("region_length_family") == "two_beat_region"]
    two_beat_anchor_rows = [row for row in two_beat_rows if row.get("two_beat_relief_status") == "simple_anchor_preferred"]
    anticipation_rows = [row for row in piano_pattern_rows if row.get("anticipation_kind") == "next_beat1_to_previous_tail"]
    two_beat_anticipations = [row for row in anticipation_rows if row.get("anticipation_previous_region_duration_beats") == 2.0]
    five_six = [row for row in piano_voicing_rows if int(row.get("density") or 0) in {5, 6}]
    return {
        "ok": bool(result.ok),
        "title": score.get("title"),
        "slug": slug,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "performance_choruses": debug.get("performance_choruses"),
        "performance_bars": debug.get("performance_bars"),
        "note_events_by_track": note_counts,
        "track_presence_ok": all(int(note_counts.get(track) or 0) > 0 for track in ("piano", "bass", "drums")),
        "piano_note_events": int(note_counts.get("piano") or 0),
        "bass_note_events": int(note_counts.get("bass") or 0),
        "drum_note_events": int(note_counts.get("drums") or 0),
        "piano_active_pattern_events": len(piano_pattern_rows),
        "piano_two_beat_active_events": len(two_beat_rows),
        "two_beat_start_anchor_events": len(two_beat_anchor_rows),
        "two_beat_anchor_ratio": round(len(two_beat_anchor_rows) / max(1, len(two_beat_rows)), 4),
        "two_beat_multi_touch_events": len([row for row in two_beat_rows if int(row.get("two_beat_relief_event_count") or 0) > 1]),
        "active_anticipation_count": len(anticipation_rows),
        "two_beat_previous_tail_anticipation_count": len(two_beat_anticipations),
        "piano_voicing_events": len(piano_voicing_rows),
        "density_counts": dict(Counter(str(row.get("density")) for row in piano_voicing_rows)),
        "recipe_counts": dict(Counter(str(row.get("recipe_id")) for row in piano_voicing_rows)),
        "five_note_events": sum(1 for row in piano_voicing_rows if int(row.get("density") or 0) == 5),
        "six_note_events": sum(1 for row in piano_voicing_rows if int(row.get("density") or 0) == 6),
        "ordinary_body_5_6_events": sum(1 for row in five_six if not row.get("authorized_5_6_scene")),
        "low_register_dense_events": sum(1 for row in piano_voicing_rows if int(row.get("notes_below_c3") or 0) > 1),
        "voice_leading_warning_events": sum(1 for row in piano_voicing_rows if row.get("top_voice_leap_exceeds_max")),
        "max_top_note": max((int(row.get("top_note") or 0) for row in piano_voicing_rows), default=0),
        "bass_span_violations": int(bass.get("span_violations") or 0),
        "bass_target_continuity_mismatches": int(bass.get("target_continuity_mismatches") or 0),
        "bass_repeated_root_violations": int(bass.get("repeated_root_violations") or 0),
        "pedal_cc64_event_count": int(pedal.get("cc64_event_count") or 0),
        "pedal_warning_count": int(pedal.get("repedal_warning_count") or 0),
        **drum_piano,
    }


def _piano_pattern_rows(debug: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in debug.get("piano_musical_audit_events") or []:
        event = dict((raw or {}).get("pattern_event") or {})
        if event.get("track") != "piano" or event.get("status") == "suppressed":
            continue
        metadata = dict(event.get("metadata") or {})
        anticipation = dict(metadata.get("anticipation") or {})
        rows.append(
            {
                "event_id": event.get("event_id"),
                "region_id": event.get("region_id"),
                "pattern_id": event.get("pattern_id"),
                "expression_hint": event.get("expression_hint"),
                "local_beat": _to_float(event.get("local_beat")),
                "onset_beat": _to_float(event.get("onset_beat")),
                "region_length_family": metadata.get("region_length_family"),
                "region_performance_bar_index": metadata.get("region_performance_bar_index"),
                "two_beat_relief_status": metadata.get("two_beat_region_density_relief_status"),
                "two_beat_relief_event_count": metadata.get("two_beat_region_density_relief_event_count"),
                "optional_selected": bool(metadata.get("optional_fill_variation_selected")),
                "optional_type": metadata.get("optional_fill_variation_type"),
                "rhythm_family": metadata.get("rhythm_family"),
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
        rows.append(
            {
                "event_id": event.get("event_id"),
                "density": density,
                "recipe_id": voicing.get("recipe_id"),
                "notes_below_c3": sum(1 for note in notes if int(note) < 48),
                "top_note": max(notes) if notes else None,
                "authorized_5_6_scene": bool(density in {5, 6} and is_last_chorus and (event_metadata.get("region_is_last_bar_of_section") or event_metadata.get("region_is_last_bar_of_chorus"))),
                "top_voice_leap_exceeds_max": bool(voice_leading.get("top_voice_leap_exceeds_max")),
            }
        )
    return rows


def _drum_piano_interaction_metrics(piano_rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    joined: list[dict[str, Any]] = []
    two_beat_non_anchor: list[dict[str, Any]] = []
    hihat_rows: list[dict[str, Any]] = []
    ride_skip_rows: list[dict[str, Any]] = []
    optional_rows: list[dict[str, Any]] = []
    accent_hihat: list[dict[str, Any]] = []
    for row in piano_rows:
        roles = _drum_roles_for_piano_hit(str(row.get("region_length_family") or ""), _to_float(row.get("local_beat")) or 0.0)
        if not roles:
            continue
        joined_row = {
            "event_id": row.get("event_id"),
            "region_id": row.get("region_id"),
            "bar": row.get("region_performance_bar_index"),
            "pattern_id": row.get("pattern_id"),
            "local_beat": row.get("local_beat"),
            "swing_local_beat": _swing_local_beat(_to_float(row.get("local_beat")) or 0.0),
            "expression_hint": row.get("expression_hint"),
            "region_length_family": row.get("region_length_family"),
            "drum_roles": roles,
            "optional_selected": row.get("optional_selected"),
        }
        joined.append(joined_row)
        if "hihat_pedal" in roles:
            hihat_rows.append(joined_row)
            if str(row.get("expression_hint") or "").startswith("comp_accent"):
                accent_hihat.append(joined_row)
        if "ride_skip_ghost" in roles:
            ride_skip_rows.append(joined_row)
        if row.get("optional_selected"):
            optional_rows.append(joined_row)
        if row.get("region_length_family") == "two_beat_region" and row.get("pattern_id") != "medium_swing_piano_two_beat_region_start_anchor":
            two_beat_non_anchor.append(joined_row)
    role_counts = Counter(role for row in joined for role in row["drum_roles"])
    risk_events = {str(row["event_id"]): row for row in (*two_beat_non_anchor, *optional_rows, *accent_hihat)}
    return {
        "piano_drum_joined_events": len(joined),
        "piano_drum_role_counts": dict(role_counts),
        "piano_on_ride_medium_events": int(role_counts.get("ride_medium") or 0),
        "piano_on_hihat_events": len(hihat_rows),
        "piano_on_ride_skip_ghost_events": len(ride_skip_rows),
        "two_beat_piano_non_anchor_with_drums_events": len(two_beat_non_anchor),
        "optional_piano_with_drums_events": len(optional_rows),
        "accented_piano_on_hihat_events": len(accent_hihat),
        "drum_piano_interaction_risk_events": len(risk_events),
        "piano_drum_interaction_samples": joined[:8],
        "two_beat_piano_non_anchor_with_drums_samples": two_beat_non_anchor[:8],
    }


def _drum_roles_for_piano_hit(region_length_family: str, local_beat: float) -> list[str]:
    beat = _swing_local_beat(local_beat)
    roles: list[str] = []
    if _near(beat, 0.0) or (region_length_family == "four_beat_region" and _near(beat, 2.0)):
        roles.append("ride_medium")
    if _near(beat, 1.0) or (region_length_family == "four_beat_region" and _near(beat, 3.0)):
        roles.extend(["ride_soft", "hihat_pedal"])
    if _near(beat, 1.6667) or (region_length_family == "four_beat_region" and _near(beat, 3.6667)):
        roles.append("ride_skip_ghost")
    return roles


def _swing_local_beat(local_beat: float) -> float:
    whole = math.floor(local_beat)
    fraction = local_beat - whole
    if abs(fraction - 0.5) <= 0.0001:
        return round(whole + (2.0 / 3.0), 4)
    return round(local_beat, 4)


def _near(a: float, b: float, tolerance: float = 0.02) -> bool:
    return abs(a - b) <= tolerance


def _aggregate(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    total_piano_voicing = sum(int(out.get("piano_voicing_events") or 0) for out in outputs)
    total_two = sum(int(out.get("piano_two_beat_active_events") or 0) for out in outputs)
    total_two_anchor = sum(int(out.get("two_beat_start_anchor_events") or 0) for out in outputs)
    five_note = sum(int(out.get("five_note_events") or 0) for out in outputs)
    six_note = sum(int(out.get("six_note_events") or 0) for out in outputs)
    return {
        "tracks_with_events_all_tunes": all(bool(out.get("track_presence_ok")) for out in outputs),
        "piano_note_events": sum(int(out.get("piano_note_events") or 0) for out in outputs),
        "bass_note_events": sum(int(out.get("bass_note_events") or 0) for out in outputs),
        "drum_note_events": sum(int(out.get("drum_note_events") or 0) for out in outputs),
        "piano_active_pattern_events": sum(int(out.get("piano_active_pattern_events") or 0) for out in outputs),
        "piano_voicing_events": total_piano_voicing,
        "piano_two_beat_active_events": total_two,
        "two_beat_start_anchor_events": total_two_anchor,
        "two_beat_anchor_ratio": round(total_two_anchor / max(1, total_two), 4),
        "active_anticipation_count": sum(int(out.get("active_anticipation_count") or 0) for out in outputs),
        "two_beat_previous_tail_anticipation_count": sum(int(out.get("two_beat_previous_tail_anticipation_count") or 0) for out in outputs),
        "five_note_events": five_note,
        "six_note_events": six_note,
        "five_six_ratio": round((five_note + six_note) / max(1, total_piano_voicing), 4),
        "ordinary_body_5_6_events": sum(int(out.get("ordinary_body_5_6_events") or 0) for out in outputs),
        "low_register_dense_events": sum(int(out.get("low_register_dense_events") or 0) for out in outputs),
        "voice_leading_warning_events": sum(int(out.get("voice_leading_warning_events") or 0) for out in outputs),
        "max_top_note": max((int(out.get("max_top_note") or 0) for out in outputs), default=0),
        "bass_span_violations": sum(int(out.get("bass_span_violations") or 0) for out in outputs),
        "bass_target_continuity_mismatches": sum(int(out.get("bass_target_continuity_mismatches") or 0) for out in outputs),
        "bass_repeated_root_violations": sum(int(out.get("bass_repeated_root_violations") or 0) for out in outputs),
        "pedal_cc64_event_count": sum(int(out.get("pedal_cc64_event_count") or 0) for out in outputs),
        "pedal_warning_count": sum(int(out.get("pedal_warning_count") or 0) for out in outputs),
        "piano_drum_joined_events": sum(int(out.get("piano_drum_joined_events") or 0) for out in outputs),
        "piano_on_ride_medium_events": sum(int(out.get("piano_on_ride_medium_events") or 0) for out in outputs),
        "piano_on_hihat_events": sum(int(out.get("piano_on_hihat_events") or 0) for out in outputs),
        "piano_on_ride_skip_ghost_events": sum(int(out.get("piano_on_ride_skip_ghost_events") or 0) for out in outputs),
        "two_beat_piano_non_anchor_with_drums_events": sum(int(out.get("two_beat_piano_non_anchor_with_drums_events") or 0) for out in outputs),
        "optional_piano_with_drums_events": sum(int(out.get("optional_piano_with_drums_events") or 0) for out in outputs),
        "accented_piano_on_hihat_events": sum(int(out.get("accented_piano_on_hihat_events") or 0) for out in outputs),
        "drum_piano_interaction_risk_events": sum(int(out.get("drum_piano_interaction_risk_events") or 0) for out in outputs),
    }


def _acceptance(static: Mapping[str, Any], outputs: list[dict[str, Any]], aggregate: Mapping[str, Any]) -> dict[str, Any]:
    by_slug = {str(output.get("slug")): output for output in outputs}
    autumn = by_slug.get("autumn_leaves", {})
    all_things = by_slug.get("all_the_things_you_are", {})
    checks = [
        {"name": "v2_6_83 drum-piano audit declared", "passed": static.get("drum_piano_interaction_audit_version") == MILESTONE_ID and bool(static.get("drum_piano_interaction_audit_enabled"))},
        {"name": "previous bass-piano checkpoint retained", "passed": static.get("previous_bass_piano_interaction_audit_version") == "v2_6_82"},
        {"name": "no music behavior change declared", "passed": bool(static.get("no_core_voicing_change")) and static.get("base_preferred_density") == 4 and static.get("base_preferred_disposition") == "open"},
        {"name": "existing drum ride candidates retained", "passed": static.get("four_beat_drum_candidate_names") == ["medium_swing_drums_spang_a_lang_hat_2_4"] and static.get("two_beat_drum_candidate_names") == ["medium_swing_drums_two_beat_spang_fragment"]},
        {"name": "drum grid remains ride-time only and not anticipation receiver", "passed": bool(static.get("drum_candidates_are_existing_ride_time_only")) and bool(static.get("drum_candidates_do_not_receive_next_chord_anticipation"))},
        {"name": "all full-band tracks present", "passed": bool(aggregate.get("tracks_with_events_all_tunes"))},
        {"name": "2-beat piano remains relieved", "passed": float(aggregate.get("two_beat_anchor_ratio") or 0.0) >= 0.80 and int(autumn.get("two_beat_multi_touch_events") or 0) <= 8},
        {"name": "All The Things not over-thinned", "passed": int(all_things.get("piano_active_pattern_events") or 0) >= 175},
        {"name": "anticipation remains active", "passed": int(aggregate.get("active_anticipation_count") or 0) > 0 and int(aggregate.get("two_beat_previous_tail_anticipation_count") or 0) > 0},
        {"name": "piano does not accent hi-hat 2/4", "passed": int(aggregate.get("accented_piano_on_hihat_events") or 0) == 0},
        {"name": "2-beat piano non-anchor with drums stays controlled", "passed": int(aggregate.get("two_beat_piano_non_anchor_with_drums_events") or 0) <= 20},
        {"name": "optional fill/variation does not collide with drums", "passed": int(aggregate.get("optional_piano_with_drums_events") or 0) <= 4},
        {"name": "drum-piano risk events stay low", "passed": int(aggregate.get("drum_piano_interaction_risk_events") or 0) <= 24},
        {"name": "explicit 5/6-note usage remains low intrusion", "passed": 0 <= float(aggregate.get("five_six_ratio") or 0.0) <= 0.06 and int(aggregate.get("ordinary_body_5_6_events") or 0) == 0},
        {"name": "low register, voice-leading, and dry pedal remain safe", "passed": int(aggregate.get("low_register_dense_events") or 0) == 0 and int(aggregate.get("voice_leading_warning_events") or 0) == 0 and int(aggregate.get("max_top_note") or 999) <= 74 and int(aggregate.get("pedal_cc64_event_count") or 0) == 0},
        {"name": "bass foundation remains safe", "passed": int(aggregate.get("bass_span_violations") or 0) == 0 and int(aggregate.get("bass_target_continuity_mismatches") or 0) == 0 and int(aggregate.get("bass_repeated_root_violations") or 0) == 0},
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
        "## Aggregate Drum–Piano Interaction Audit",
        f"- Tracks present in all tunes: {agg['tracks_with_events_all_tunes']}",
        f"- Note events by track: piano={agg['piano_note_events']}, bass={agg['bass_note_events']}, drums={agg['drum_note_events']}",
        f"- Piano active pattern events / voicing events: {agg['piano_active_pattern_events']} / {agg['piano_voicing_events']}",
        f"- Piano 2-beat active / start anchors / anchor ratio: {agg['piano_two_beat_active_events']} / {agg['two_beat_start_anchor_events']} / {agg['two_beat_anchor_ratio']}",
        f"- Active anticipations / 2-beat previous-tail anticipations: {agg['active_anticipation_count']} / {agg['two_beat_previous_tail_anticipation_count']}",
        f"- 5-note / 6-note events / ratio: {agg['five_note_events']} / {agg['six_note_events']} / {agg['five_six_ratio']}",
        f"- Piano–drum joined events: {agg['piano_drum_joined_events']}",
        f"- Piano on ride medium / hi-hat / ride-skip ghost: {agg['piano_on_ride_medium_events']} / {agg['piano_on_hihat_events']} / {agg['piano_on_ride_skip_ghost_events']}",
        f"- 2-beat non-anchor with drums / optional with drums / accented hi-hat: {agg['two_beat_piano_non_anchor_with_drums_events']} / {agg['optional_piano_with_drums_events']} / {agg['accented_piano_on_hihat_events']}",
        f"- Drum–piano risk events: {agg['drum_piano_interaction_risk_events']}",
        f"- Voice-leading warnings / low-register dense events: {agg['voice_leading_warning_events']} / {agg['low_register_dense_events']}",
        f"- Bass span / continuity / repeated-root violations: {agg['bass_span_violations']} / {agg['bass_target_continuity_mismatches']} / {agg['bass_repeated_root_violations']}",
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
                f"- Piano–drum roles: `{out['piano_drum_role_counts']}`",
                f"- 2-beat non-anchor with drums / optional with drums / accented hi-hat: {out['two_beat_piano_non_anchor_with_drums_events']} / {out['optional_piano_with_drums_events']} / {out['accented_piano_on_hihat_events']}",
                f"- Samples: `{out['piano_drum_interaction_samples'][:3]}`",
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
