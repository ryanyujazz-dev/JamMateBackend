from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jammate_engine.core.pattern_runtime import PatternCandidate, TailPolicy, event_spec


JAZZ_BALLAD_BRUSH_SEMANTIC_POLICY_VERSION = "v2_6_127"
JAZZ_BALLAD_FIRST_AUDIBLE_SPARSE_BRUSH_VERSION = "v2_6_128"
JAZZ_BALLAD_COMPLETE_BRUSH_DRUM_SYSTEM_VERSION = "v2_6_131"
JAZZ_BALLAD_BRUSH_SOUND_SOURCE_TIME_FEEL_VERSION = "v2_6_137"
JAZZ_BALLAD_BRUSH_SECTION_HINT_VERSION = "v2_6_137"

BRUSH_FEEL_CELLS = (
    "pure_legato_brush",
    "basic_brush_time",
    "brush_swing_skip",
    "brush_two_feel",
    "brush_four_feel_development",
    "phrase_breath_release",
    "final_release",
)
BRUSH_CLASSIC_FILL_CELLS = (
    "none",
    # Explicit foreground fills remain available for future explicit requests,
    # but the automatic Ballad planner defaults to subtle transition hints.
    "soft_pickup_to_4",
    "tap_drag_tap_release",
    "single_stroke_4_to_next",
    "turnaround_sweep_roll",
    # Subtle section/phrase transition hint vocabulary.
    "section_tail_4and_hint",
    "section_tail_4and_whisper",
    "section_tail_3and_4and_feather_hint",
    "v1_soft_swish_4and_hint",
    "v1_section_breath_4_to_4and_hint",
    "section_entry_brush_bloom",
    "section_entry_1and_bloom_hint",
    "section_entry_soft_1_to_1and_hint",
    "cadence_3and_4_hint",
    "cadence_3and_4and_whisper",
    "cadence_4_hat_brush_hint",
    "cadence_3_to_4_tom_hat_hint",
    "v1_drag_to_4_hint",
    "turnaround_soft_2and_4and_hint",
    "turnaround_2and_3and_4and_whisper",
    "turnaround_2and_4_hat_hint",
    "turnaround_cross_stick_4_hint",
    "bridge_entry_soft_1_2and_hint",
    "bridge_entry_low_tom_bloom_hint",
    "section_tail_4_hat_cymbal_hint",
    "final_brush_release",
)
BRUSH_OFFBEAT_ROLES = {
    "1&": "continuation_motion",
    "2&": "swing_skip_lift",
    "3&": "pickup_to_4",
    "4&": "pickup_or_breath_to_next_bar",
}
BRUSH_TIME_ANCHOR_INTENTS = ("none", "hat_4_only", "hat_2_4_soft")
BRUSH_KICK_POLICY_INTENTS = ("none", "beat1_feather", "one_three_feather", "all_four_feather")
BRUSH_DENSITY_BANDS = ("very_low", "low", "medium")


@dataclass(frozen=True)
class _BarPosition:
    start: float
    end: float
    region_role: str


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "end", "ending", "phrase_end", "section_end"}


def _region_value(context: dict[str, Any], attr: str, fallback_key: str | None = None, default: Any = None) -> Any:
    region = context.get("region")
    if region is not None and hasattr(region, attr):
        value = getattr(region, attr)
        if value is not None:
            return value
    if fallback_key and fallback_key in context:
        return context.get(fallback_key)
    return default


def _bar_mod(value: Any, mod: int) -> int | None:
    try:
        return int(value) % mod
    except (TypeError, ValueError):
        return None


def _bar_position(context: dict[str, Any], region_span: float) -> _BarPosition:
    first = _coerce_bool(_region_value(context, "is_first_region_of_bar", "region_is_first_region_of_bar", False))
    last = _coerce_bool(_region_value(context, "is_last_region_of_bar", "region_is_last_region_of_bar", False))
    if region_span >= 3.75:
        return _BarPosition(0.0, min(4.0, region_span), "whole_bar")
    if first and not last:
        return _BarPosition(0.0, min(2.0, region_span), "first_half")
    if last and not first:
        return _BarPosition(2.0, min(4.0, 2.0 + region_span), "second_half")
    if last:
        return _BarPosition(max(0.0, 4.0 - region_span), 4.0, "bar_tail")
    return _BarPosition(0.0, min(4.0, region_span), "short_region")


def _phrase_flags(context: dict[str, Any], *, region_span: float) -> dict[str, bool]:
    source_bar_index = _region_value(context, "source_bar_index", "region_source_bar_index", None)
    source_mod4 = _bar_mod(source_bar_index, 4)
    source_mod8 = _bar_mod(source_bar_index, 8)
    last_region = _coerce_bool(_region_value(context, "is_last_region_of_bar", "region_is_last_region_of_bar", region_span >= 3.75))
    last_bar_of_section = _coerce_bool(_region_value(context, "is_last_bar_of_section", "region_is_last_bar_of_section", False))
    last_bar_of_chorus = _coerce_bool(_region_value(context, "is_last_bar_of_chorus", "region_is_last_bar_of_chorus", False))
    chorus_index = int(_region_value(context, "chorus_index", "region_chorus_index", 0) or 0)
    total_choruses = int(_region_value(context, "total_choruses", "region_total_choruses", 1) or 1)
    phrase_role = str(context.get("phrase_role") or context.get("phrase_position") or "").strip().lower()
    explicit_tail = phrase_role in {"end", "ending", "last", "tail", "cadence", "phrase_end", "section_end"} or any(
        _coerce_bool(context.get(key)) for key in ("phrase_end", "is_phrase_end", "phrase_boundary", "section_end", "is_section_end")
    )
    phrase_tail = bool(last_region and (last_bar_of_section or source_mod8 == 7 or source_mod4 == 3 or explicit_tail))
    final_release = bool(last_region and last_bar_of_chorus and total_choruses > 0 and chorus_index >= total_choruses - 1)
    return {
        "phrase_tail": phrase_tail,
        "section_tail": bool(last_region and last_bar_of_section),
        "final_release": final_release,
        "last_region_of_bar": last_region,
    }




def _select_classic_fill_cell(
    *,
    feel_cell: str,
    source_mod4: int | None,
    source_mod8: int | None,
    chorus_index: int,
    flags: dict[str, bool],
    first_bar_of_section: bool,
    density: str,
) -> str:
    """Select a subtle section/phrase transition hint cell.

    v2_6_137 keeps the v2_6_135 idea that automatic Ballad fills should be
    phrase/section hints rather than foreground drum-fill displays.  After
    re-reading the V1 Ballad brush implementation, the automatic V2 cells are
    mapped from V1's useful primitives: brush_drag_to_4, section_breath,
    soft_swish_4and, and final_release.  They remain quieter, shorter, and
    resolved by the shared swing-8 timing layer instead of foreground fill
    displays.  Stronger tap-drag/single-stroke cells remain vocabulary only
    for future explicit requests.
    """

    if feel_cell == "final_release" or flags.get("final_release"):
        return "final_brush_release"
    if first_bar_of_section:
        # Prefer a downbeat bloom on a different brush-kit lane; 1& blooms are
        # retained in the vocabulary but no longer the default transition cue.
        return "bridge_entry_low_tom_bloom_hint" if chorus_index >= 1 else "section_entry_brush_bloom"
    if flags.get("section_tail") or source_mod8 == 7:
        if chorus_index >= 1:
            return "section_tail_4_hat_cymbal_hint"
        return "v1_soft_swish_4and_hint"
    if flags.get("phrase_tail") or source_mod4 == 3:
        if chorus_index >= 1 and density in {"low", "medium"}:
            return "cadence_3_to_4_tom_hat_hint"
        return "v1_drag_to_4_hint"
    if chorus_index >= 1 and source_mod8 == 5 and density in {"low", "medium"}:
        return "turnaround_cross_stick_4_hint"
    if chorus_index >= 1 and source_mod8 == 6 and density in {"low", "medium"}:
        return "turnaround_2and_4_hat_hint"
    if chorus_index >= 1 and source_mod8 == 4 and density in {"low", "medium"}:
        return "bridge_entry_low_tom_bloom_hint"
    return "none"

def build_brush_semantic_policy_decision(context: dict | None = None) -> dict[str, Any]:
    """Return a bar-level Jazz Ballad brush time-feel decision.

    The contract assumes the playback environment has a brush-capable drum
    source.  V2 therefore plans brush motion/offbeat/time-anchor intent instead
    of approximating brushes with dense ordinary snare hits or custom internal
    brush voices.
    """

    context = dict(context or {})
    region_span = float(_region_value(context, "duration_beats", "region_duration_beats", 4.0) or 4.0)
    bar_pos = _bar_position(context, region_span)
    source_bar_index = _region_value(context, "source_bar_index", "region_source_bar_index", None)
    performance_bar_index = _region_value(context, "performance_bar_index", "region_performance_bar_index", None)
    chorus_index = int(_region_value(context, "chorus_index", "region_chorus_index", 0) or 0)
    total_choruses = int(_region_value(context, "total_choruses", "region_total_choruses", 1) or 1)
    first_bar_of_section = _coerce_bool(_region_value(context, "is_first_bar_of_section", "region_is_first_bar_of_section", False))
    flags = _phrase_flags(context, region_span=region_span)
    source_mod4 = _bar_mod(source_bar_index, 4)
    source_mod8 = _bar_mod(source_bar_index, 8)
    energy = str(context.get("energy") or context.get("comping_energy") or "").lower()
    requested_density = str(context.get("drum_density") or context.get("brush_density") or "").lower()

    if flags["final_release"]:
        feel_cell = "final_release"
        time_anchor = "none"
        kick_policy = "none"
        density = "very_low"
    elif flags["phrase_tail"]:
        feel_cell = "phrase_breath_release"
        time_anchor = "hat_4_only"
        kick_policy = "none"
        density = "very_low"
    elif first_bar_of_section or energy in {"low", "sparse", "quiet"} or requested_density in {"very_low", "low", "sparse"}:
        feel_cell = "pure_legato_brush"
        time_anchor = "hat_4_only" if flags["last_region_of_bar"] else "none"
        kick_policy = "none" if chorus_index == 0 else "beat1_feather"
        density = "very_low"
    elif chorus_index >= 1 and requested_density in {"medium", "active"}:
        feel_cell = "brush_four_feel_development"
        time_anchor = "hat_2_4_soft"
        kick_policy = "all_four_feather"
        density = "medium"
    elif chorus_index >= 1 and source_mod8 in {4, 5, 6}:
        feel_cell = "brush_two_feel"
        time_anchor = "hat_2_4_soft"
        kick_policy = "one_three_feather"
        density = "low"
    elif source_mod4 in {1, 2}:
        feel_cell = "brush_swing_skip"
        time_anchor = "hat_2_4_soft"
        kick_policy = "beat1_feather"
        density = "low"
    else:
        feel_cell = "basic_brush_time"
        time_anchor = "hat_2_4_soft"
        kick_policy = "beat1_feather"
        density = "low"

    return {
        "jazz_ballad_brush_semantic_policy_active": True,
        "jazz_ballad_brush_semantic_policy_version": JAZZ_BALLAD_BRUSH_SEMANTIC_POLICY_VERSION,
        "jazz_ballad_brush_sound_source_time_feel_active": True,
        "jazz_ballad_brush_sound_source_time_feel_version": JAZZ_BALLAD_BRUSH_SOUND_SOURCE_TIME_FEEL_VERSION,
        "jazz_ballad_brush_sound_source_assumed": True,
        "jazz_ballad_drum_planning_scope": "bar_level_brush_time_feel_with_region_projection",
        "jazz_ballad_drum_not_chord_region_loop": True,
        "jazz_ballad_no_custom_internal_brush_voices": True,
        "jazz_ballad_brush_timbre_delegated_to_sound_source": True,
        "brush_feel_cell": feel_cell,
        "brush_motion_lane": "logical_eighth_sweep_path_resolved_by_style_swing8_timing",
        "brush_motion_points": ("1", "1&", "2", "2&", "3", "3&", "4", "4&"),
        "brush_audible_motion_policy": "logical_quarter_pressure_plus_contextual_swing8_offbeat_articulation",
        "brush_offbeat_policy": dict(BRUSH_OFFBEAT_ROLES),
        "brush_time_anchor_intent": time_anchor,
        "brush_kick_policy_intent": kick_policy,
        "brush_density_band": density,
        "bar_region_projection": {
            "bar_start": bar_pos.start,
            "bar_end": bar_pos.end,
            "region_role": bar_pos.region_role,
        },
        "brush_classic_fill_cell": _select_classic_fill_cell(
            feel_cell=feel_cell,
            source_mod4=source_mod4,
            source_mod8=source_mod8,
            chorus_index=chorus_index,
            flags=flags,
            first_bar_of_section=first_bar_of_section,
            density=density,
        ),
        "brush_fill_policy_active": True,
        "brush_fill_policy_version": JAZZ_BALLAD_BRUSH_SOUND_SOURCE_TIME_FEEL_VERSION,
        "brush_transition_hint_vocabulary_expanded": True,
        "brush_transition_hint_dynamic_contract": "subtle_hint_overlay_not_foreground_fill",
        "brush_transition_hint_timbre_variation_active": True,
        "brush_offbeat_articulation_density_contract": "reduced_contextual_offbeats",
        "brush_transition_hint_v1_reference_primitives": (
            "brush_drag_to_4",
            "section_breath",
            "soft_swish_4and",
            "final_release",
        ),
        "brush_fill_scope": "section_or_phrase_transition_hint_not_chord_region_loop",
        "brush_fill_timing_contract": "style_timing_policy_swing8",
        "brush_phrase_context": {
            "region_span_beats": region_span,
            "source_bar_index": source_bar_index,
            "performance_bar_index": performance_bar_index,
            "source_bar_mod4": source_mod4,
            "source_bar_mod8": source_mod8,
            "chorus_index": chorus_index,
            "total_choruses": total_choruses,
            "first_bar_of_section": first_bar_of_section,
            **flags,
        },
        "brush_no_swing_ride": True,
        "brush_no_rock_backbeat": True,
        "brush_no_piano_bass_voicing_change": True,
        "recommended_next_task": "v2_6_138_engine_ballad_hint_timbre_and_offbeat_density_listening_calibration",
    }


def _candidate_metadata(decision: dict[str, Any], *, event_count: int) -> dict[str, Any]:
    return {
        "style_id": "jazz_ballad",
        "pattern_domain": "percussion_foundation",
        "pattern_library_id": "jazz_ballad.brush_sound_source_time_feel",
        "pattern_library_version": JAZZ_BALLAD_BRUSH_SOUND_SOURCE_TIME_FEEL_VERSION,
        "brush_fill_audibility_rework_active": True,
        "brush_section_transition_hint_active": True,
        "brush_section_transition_hint_version": JAZZ_BALLAD_BRUSH_SECTION_HINT_VERSION,
        "jazz_ballad_brush_sound_source_time_feel_active": True,
        "jazz_ballad_brush_sound_source_time_feel_version": JAZZ_BALLAD_BRUSH_SOUND_SOURCE_TIME_FEEL_VERSION,
        "jazz_ballad_brush_sound_source_assumed": True,
        "jazz_ballad_drum_planning_scope": decision["jazz_ballad_drum_planning_scope"],
        "jazz_ballad_drum_not_chord_region_loop": True,
        "jazz_ballad_no_custom_internal_brush_voices": True,
        "jazz_ballad_brush_timbre_delegated_to_sound_source": True,
        "brush_feel_cell": decision["brush_feel_cell"],
        "brush_motion_lane": decision["brush_motion_lane"],
        "brush_motion_points": decision["brush_motion_points"],
        "brush_audible_motion_policy": decision["brush_audible_motion_policy"],
        "brush_offbeat_policy": decision["brush_offbeat_policy"],
        "brush_time_anchor_intent": decision["brush_time_anchor_intent"],
        "brush_kick_policy_intent": decision["brush_kick_policy_intent"],
        "brush_density_band": decision["brush_density_band"],
        "brush_classic_fill_cell": decision.get("brush_classic_fill_cell", "none"),
        "brush_fill_policy_active": decision.get("brush_fill_policy_active") is True,
        "brush_fill_policy_version": decision.get("brush_fill_policy_version"),
        "brush_fill_scope": decision.get("brush_fill_scope"),
        "brush_fill_timing_contract": decision.get("brush_fill_timing_contract"),
        "bar_region_projection": decision["bar_region_projection"],
        "brush_runtime_audible": event_count > 0,
        "brush_runtime_note_event_count": int(event_count),
        "brush_fill_audibility_rework_active": True,
        "brush_transition_hint_vocabulary_expanded": True,
        "brush_transition_hint_dynamic_contract": "subtle_hint_overlay_not_foreground_fill",
        "brush_transition_hint_timbre_variation_active": True,
        "brush_offbeat_articulation_density_contract": "reduced_contextual_offbeats",
        "brush_transition_hint_v1_reference_primitives": decision.get("brush_transition_hint_v1_reference_primitives"),
        "brush_fill_audibility_contract": "section_transition_hint_lane_without_background_duck",
        "brush_transition_hint_timbre_variation_active": True,
        "brush_offbeat_articulation_density_contract": "reduced_contextual_offbeats",
        "allowed_drum_voices": ("snare", "cross_stick", "hihat_pedal", "kick", "ride", "low_tom", "mid_tom"),
        "brush_no_swing_ride": True,
        "brush_no_rock_backbeat": True,
        "brush_no_piano_bass_voicing_change": True,
    }


def _timing_intent_for_slot(slot: str) -> str:
    """Return the shared V2 timing intent for a brush slot.

    Ballad brush patterns own the written logical grid only.  Written eighth
    offbeats stay at `.5` positions and are performed by the style-level
    swing-8 timing policy, matching the existing Jazz Ballad v2_5_8/v2_5_9
    contract.  The drum pattern must not invent a private timing intent or
    write performed `2/3` offsets directly.
    """

    return "swing_upbeat" if "&" in str(slot) else "auto"

def _event(beat: float, *, role: str, drum: str, dynamic: str, stroke: str, articulation: str, decision: dict[str, Any], slot: str) -> Any:
    # Section transition hints are intentionally not foreground fills in
    # v2_6_137.  They ride inside the brush texture; only explicit fills and
    # final releases own foreground space.
    fill_foreground = role in {"ballad_classic_brush_fill", "ballad_final_brush_release", "ballad_final_soft_cymbal_release"}
    return event_spec(
        track="drums",
        beat=beat,
        role=role,
        metadata={
            "drum": drum,
            "dynamic_profile": dynamic,
            "stroke_profile": stroke,
            "timing_intent": _timing_intent_for_slot(slot),
            "brush_sound_source_articulation": articulation,
            "brush_timing_contract": "style_timing_policy_swing8",
            "brush_timing_owner": "style_timing_policy_not_pattern",
            "brush_logical_grid_position": beat,
            "brush_feel_cell": decision["brush_feel_cell"],
            "brush_motion_lane": decision["brush_motion_lane"],
            "brush_event_slot": slot,
            "brush_event_bar_position": beat,
            "brush_event_role": role,
            "brush_offbeat_role": BRUSH_OFFBEAT_ROLES.get(slot, "downbeat_pressure"),
            "brush_fill_policy_active": decision.get("brush_fill_policy_active") is True,
            "brush_fill_audibility_rework_active": True,
            "brush_section_transition_hint_active": True,
            "brush_section_transition_hint_version": JAZZ_BALLAD_BRUSH_SECTION_HINT_VERSION,
            "brush_transition_hint_vocabulary_expanded": True,
            "brush_transition_hint_dynamic_contract": "subtle_hint_overlay_not_foreground_fill",
        "brush_transition_hint_timbre_variation_active": True,
        "brush_offbeat_articulation_density_contract": "reduced_contextual_offbeats",
            "brush_fill_audibility_contract": "section_transition_hint_lane_without_background_duck",
        "brush_transition_hint_timbre_variation_active": True,
        "brush_offbeat_articulation_density_contract": "reduced_contextual_offbeats",
            "brush_fill_foreground_lane": fill_foreground,
            "brush_classic_fill_cell": decision.get("brush_classic_fill_cell", "none"),
            "jazz_ballad_no_custom_internal_brush_voices": True,
            "jazz_ballad_brush_timbre_delegated_to_sound_source": True,
        },
    )


def _bar_to_local(bar_beat: float, decision: dict[str, Any]) -> float | None:
    projection = dict(decision.get("bar_region_projection") or {})
    start = float(projection.get("bar_start", 0.0))
    end = float(projection.get("bar_end", 4.0))
    if start - 1e-9 <= bar_beat < end - 1e-9:
        return round(bar_beat - start, 4)
    return None


def _append_if_in_region(events: list[Any], bar_beat: float, *, role: str, drum: str, dynamic: str, stroke: str, articulation: str, decision: dict[str, Any], slot: str) -> None:
    local = _bar_to_local(bar_beat, decision)
    if local is None:
        return
    events.append(_event(local, role=role, drum=drum, dynamic=dynamic, stroke=stroke, articulation=articulation, decision=decision, slot=slot))


def _render_transition_hint_entry(fill_cell: str, articulation: str, role: str, dynamic: str, stroke: str) -> tuple[str, str, str]:
    """Map subtle Ballad transition hints across brush-kit sound entries.

    These are still standard drum entries; the brush sound source is expected
    to interpret them as brush/timbre articulations.  The goal is to avoid every
    phrase hint speaking as the same snare-brush color while keeping dynamics
    subtle and avoiding foreground drum fills.
    """

    if role != "ballad_section_transition_hint":
        return "snare", dynamic, stroke
    art = str(articulation)
    text = f"{fill_cell} {art}"
    if "cymbal" in art or "ride_" in art:
        return "ride", dynamic, "brush_cymbal"
    if "hat" in art:
        return "hihat_pedal", "brush_hat_pp" if dynamic == "brush_hint_pp" else "brush_hat_p", "brush_foot"
    if "cross_stick" in art:
        return "cross_stick", dynamic, "brush_hint_tap"
    if "low_tom" in art:
        return "low_tom", dynamic, "brush_hint_swish"
    if "mid_tom" in art:
        return "mid_tom", dynamic, "brush_hint_swish"
    if "entry" in text or "bloom" in text:
        return "low_tom", dynamic, "brush_hint_swish"
    if "turnaround" in text:
        if "4and" in art:
            return "ride", dynamic, "brush_cymbal"
        if "3and" in art:
            return "mid_tom", dynamic, "brush_hint_swish"
        if "2and" in art:
            return "cross_stick", dynamic, "brush_hint_tap"
        return "cross_stick", dynamic, "brush_hint_tap"
    if "cadence" in text:
        if "4and" in art:
            return "ride", dynamic, "brush_cymbal"
        if "3and" in art or "3_hint" in art:
            return "low_tom", dynamic, "brush_hint_swish"
        return "cross_stick", dynamic, "brush_hint_tap"
    if "drag_to_4" in text and "soft_whisper" in art:
        return "cross_stick", dynamic, "brush_hint_tap"
    return "snare", dynamic, stroke



def _append_brush_motion(events: list[Any], decision: dict[str, Any]) -> None:
    cell = str(decision.get("brush_feel_cell"))
    density = str(decision.get("brush_density_band"))
    phrase_context = dict(decision.get("brush_phrase_context") or {})
    source_mod4 = phrase_context.get("source_bar_mod4")
    phrase_tail = bool(phrase_context.get("phrase_tail"))
    section_tail = bool(phrase_context.get("section_tail"))
    # Quarter pressure pulses are the audible part of a continuous brush path.
    for beat, slot in ((0.0, "1"), (1.0, "2"), (2.0, "3"), (3.0, "4")):
        _append_if_in_region(
            events,
            beat,
            role="ballad_brush_sweep_pressure",
            drum="snare",
            dynamic="brush_motion_pp",
            stroke="brush_sweep",
            articulation="snare_brush_continuous_sweep_pressure",
            decision=decision,
            slot=slot,
        )
    # v2_6_137: the written brush path still passes through swing-8 offbeats,
    # but audible offbeat articulation is intentionally reduced.  The shared
    # swing-8 timing layer owns performed placement; this layer only decides
    # whether an offbeat should speak as a brush-source articulation.
    offbeats: tuple[tuple[float, str, str], ...]
    if cell == "pure_legato_brush":
        offbeats = ()
    elif cell == "basic_brush_time":
        offbeats = ((3.5, "4&", "snare_brush_soft_4and_breath"),) if (phrase_tail or section_tail or source_mod4 == 3) else ()
    elif cell == "brush_swing_skip":
        offbeats = ((1.5, "2&", "snare_brush_swing_skip"),) if source_mod4 == 1 else ((3.5, "4&", "snare_brush_swing_skip_to_next"),)
    elif cell == "brush_two_feel":
        offbeats = ((2.5, "3&", "snare_brush_pickup_to_4"),) if source_mod4 in {1, 2} else ((3.5, "4&", "snare_brush_soft_4and_breath"),)
    elif cell == "brush_four_feel_development":
        offbeats = ((1.5, "2&", "snare_brush_swing_skip"), (3.5, "4&", "snare_brush_swing_skip_to_next"))
    else:
        offbeats = ()
    if density == "very_low":
        offbeats = tuple(item for item in offbeats if item[1] == "4&" and (phrase_tail or section_tail))
    for beat, slot, articulation in offbeats:
        _append_if_in_region(
            events,
            beat,
            role="ballad_brush_offbeat_swish",
            drum="snare",
            dynamic="brush_skip_pp",
            stroke="brush_swish",
            articulation=articulation,
            decision=decision,
            slot=slot,
        )

def _append_anchor(events: list[Any], decision: dict[str, Any]) -> None:
    intent = str(decision.get("brush_time_anchor_intent"))
    if intent == "hat_2_4_soft":
        for beat, slot in ((1.0, "2"), (3.0, "4")):
            _append_if_in_region(events, beat, role="ballad_brush_foot_hat_anchor", drum="hihat_pedal", dynamic="brush_hat_p", stroke="brush_foot", articulation="soft_foot_hat_anchor", decision=decision, slot=slot)
    elif intent == "hat_4_only":
        _append_if_in_region(events, 3.0, role="ballad_brush_foot_hat_anchor", drum="hihat_pedal", dynamic="brush_hat_pp", stroke="brush_foot", articulation="soft_foot_hat_4_only", decision=decision, slot="4")


def _append_feather_kick(events: list[Any], decision: dict[str, Any]) -> None:
    policy = str(decision.get("brush_kick_policy_intent"))
    if policy == "beat1_feather":
        beats = (0.0,)
    elif policy == "one_three_feather":
        beats = (0.0, 2.0)
    elif policy == "all_four_feather":
        beats = (0.0, 1.0, 2.0, 3.0)
    else:
        beats = ()
    for beat in beats:
        _append_if_in_region(events, beat, role="ballad_feather_kick", drum="kick", dynamic="brush_feather", stroke="feather", articulation="felt_not_heard_feather_kick", decision=decision, slot=f"{int(beat)+1}")


def _classic_fill_window(decision: dict[str, Any]) -> tuple[float, float] | None:
    fill_cell = str(decision.get("brush_classic_fill_cell") or "none")
    if fill_cell == "none":
        return None
    # Automatic section hints are not foreground fills in v2_6_137: they should
    # sit inside the brush texture instead of carving space out of it.  Keep
    # ducking only for explicit stronger fill cells and final release.
    subtle_hint_cells = {
        "section_tail_4and_hint",
        "section_tail_4and_whisper",
        "section_tail_3and_4and_feather_hint",
        "v1_soft_swish_4and_hint",
        "v1_section_breath_4_to_4and_hint",
        "section_entry_brush_bloom",
        "section_entry_1and_bloom_hint",
        "section_entry_soft_1_to_1and_hint",
        "cadence_3and_4_hint",
        "cadence_3and_4and_whisper",
        "cadence_4_hat_brush_hint",
        "cadence_3_to_4_tom_hat_hint",
        "v1_drag_to_4_hint",
        "turnaround_soft_2and_4and_hint",
        "turnaround_2and_3and_4and_whisper",
        "turnaround_2and_4_hat_hint",
        "turnaround_cross_stick_4_hint",
        "bridge_entry_soft_1_2and_hint",
        "bridge_entry_low_tom_bloom_hint",
        "section_tail_4_hat_cymbal_hint",
    }
    if fill_cell in subtle_hint_cells:
        return None
    if fill_cell == "soft_pickup_to_4":
        return (2.45, 3.05)
    if fill_cell == "tap_drag_tap_release":
        return (1.45, 3.9)
    if fill_cell == "single_stroke_4_to_next":
        return (1.95, 3.9)
    if fill_cell == "turnaround_sweep_roll":
        return (1.45, 3.9)
    if fill_cell == "final_brush_release":
        return (0.0, 4.0)
    return None

def _duck_background_for_classic_fill(events: list[Any], decision: dict[str, Any]) -> None:
    """Let the foreground brush fill speak by clearing overlapping background sweep.

    v2_6_134 proved that foreground ducking makes fills audible, but the result
    was too explicit for ordinary Ballad transitions.  v2_6_135 keeps only a
    tiny selective space around transition-hint cues; background brush time
    should still feel continuous.
    """

    window = _classic_fill_window(decision)
    if window is None:
        return
    start, end = window
    background_roles = {
        "ballad_brush_sweep_pressure",
        "ballad_brush_offbeat_swish",
        "ballad_phrase_brush_breath",
    }
    events[:] = [
        event
        for event in events
        if not (
            event.role in background_roles
            and str(event.metadata.get("drum")) == "snare"
            and start - 1e-9 <= float(event.local_beat) <= end + 1e-9
        )
    ]


def _append_classic_fill_overlay(events: list[Any], decision: dict[str, Any]) -> None:
    fill_cell = str(decision.get("brush_classic_fill_cell") or "none")
    if fill_cell == "none":
        return
    if fill_cell == "final_brush_release":
        events.clear()
        _append_if_in_region(
            events,
            0.0,
            role="ballad_final_brush_release",
            drum="snare",
            dynamic="brush_fill_release_mf",
            stroke="brush_fill_release",
            articulation="snare_brush_final_release_sweep_foreground",
            decision=decision,
            slot="1",
        )
        _append_if_in_region(
            events,
            1.5,
            role="ballad_final_soft_cymbal_release",
            drum="ride",
            dynamic="brush_fill_cymbal_p",
            stroke="brush_cymbal",
            articulation="soft_cymbal_decay_from_brush_source_foreground",
            decision=decision,
            slot="2&",
        )
        return

    # Each tuple: bar beat, logical slot, role, articulation, dynamic profile, stroke profile.
    # These remain brush-source intents on standard drum entries; they are not custom drum voices.
    gestures: tuple[tuple[float, str, str, str, str, str], ...]
    if fill_cell == "section_tail_4and_hint":
        gestures = (
            (3.5, "4&", "ballad_section_transition_hint", "snare_brush_section_tail_soft_4and_hint_to_next", "brush_hint_p", "brush_hint_release"),
        )
    elif fill_cell == "section_tail_4and_whisper":
        gestures = (
            (3.5, "4&", "ballad_section_transition_hint", "snare_brush_section_tail_4and_whisper_to_next", "brush_hint_pp", "brush_hint_swish"),
        )
    elif fill_cell == "section_tail_3and_4and_feather_hint":
        gestures = (
            (2.5, "3&", "ballad_section_transition_hint", "snare_brush_section_tail_3and_feather_lift", "brush_hint_pp", "brush_hint_swish"),
            (3.5, "4&", "ballad_section_transition_hint", "snare_brush_section_tail_4and_feather_to_next", "brush_hint_p", "brush_hint_release"),
        )
    elif fill_cell == "v1_soft_swish_4and_hint":
        gestures = (
            (3.5, "4&", "ballad_section_transition_hint", "v1_soft_swish_4and_mapped_to_shared_swing8", "brush_hint_pp", "brush_hint_swish"),
        )
    elif fill_cell == "v1_section_breath_4_to_4and_hint":
        gestures = (
            (3.0, "4", "ballad_section_transition_hint", "v1_section_breath_soft_4_sweep", "brush_hint_pp", "brush_hint_swish"),
            (3.5, "4&", "ballad_section_transition_hint", "v1_section_breath_soft_4and_cymbal_or_sweep_hint", "brush_hint_p", "brush_hint_release"),
        )
    elif fill_cell == "section_entry_brush_bloom":
        gestures = (
            (0.0, "1", "ballad_section_transition_hint", "snare_brush_section_entry_soft_bloom_on_1", "brush_hint_p", "brush_hint_swish"),
        )
    elif fill_cell == "section_entry_1and_bloom_hint":
        gestures = (
            (0.5, "1&", "ballad_section_transition_hint", "snare_brush_section_entry_1and_bloom_hint", "brush_hint_pp", "brush_hint_swish"),
        )
    elif fill_cell == "section_entry_soft_1_to_1and_hint":
        gestures = (
            (0.0, "1", "ballad_section_transition_hint", "snare_brush_section_entry_soft_1_bloom", "brush_hint_pp", "brush_hint_swish"),
            (0.5, "1&", "ballad_section_transition_hint", "snare_brush_section_entry_soft_1and_bloom", "brush_hint_p", "brush_hint_release"),
        )
    elif fill_cell == "cadence_3and_4_hint":
        gestures = (
            (2.5, "3&", "ballad_section_transition_hint", "snare_brush_cadence_pickup_3and", "brush_hint_pp", "brush_hint_swish"),
            (3.0, "4", "ballad_section_transition_hint", "snare_brush_cadence_soft_answer_4", "brush_hint_p", "brush_hint_tap"),
        )
    elif fill_cell == "cadence_3and_4and_whisper":
        gestures = (
            (2.5, "3&", "ballad_section_transition_hint", "snare_brush_cadence_3and_whisper", "brush_hint_pp", "brush_hint_swish"),
            (3.5, "4&", "ballad_section_transition_hint", "snare_brush_cadence_4and_whisper_to_next", "brush_hint_p", "brush_hint_release"),
        )
    elif fill_cell == "cadence_4_hat_brush_hint":
        gestures = (
            (3.0, "4", "ballad_section_transition_hint", "snare_brush_cadence_beat4_hint_inside_hat", "brush_hint_p", "brush_hint_tap"),
        )
    elif fill_cell == "cadence_3_to_4_tom_hat_hint":
        gestures = (
            (2.0, "3", "ballad_section_transition_hint", "low_tom_brush_cadence_beat3_hint", "brush_hint_pp", "brush_hint_swish"),
            (3.0, "4", "ballad_section_transition_hint", "hat_cadence_beat4_soft_close_hint", "brush_hint_p", "brush_hint_tap"),
        )
    elif fill_cell == "v1_drag_to_4_hint":
        gestures = (
            (2.5, "3&", "ballad_section_transition_hint", "v1_brush_drag_to_4_pickup_mapped_to_shared_swing8", "brush_hint_pp", "brush_hint_swish"),
            (3.0, "4", "ballad_section_transition_hint", "v1_brush_drag_to_4_soft_whisper", "brush_hint_p", "brush_hint_tap"),
        )
    elif fill_cell == "turnaround_soft_2and_4and_hint":
        gestures = (
            (1.5, "2&", "ballad_section_transition_hint", "snare_brush_turnaround_soft_2and_lift", "brush_hint_pp", "brush_hint_swish"),
            (3.5, "4&", "ballad_section_transition_hint", "snare_brush_turnaround_soft_4and_to_next", "brush_hint_p", "brush_hint_release"),
        )
    elif fill_cell == "turnaround_2and_3and_4and_whisper":
        gestures = (
            (1.5, "2&", "ballad_section_transition_hint", "snare_brush_turnaround_2and_whisper_lift", "brush_hint_pp", "brush_hint_swish"),
            (2.5, "3&", "ballad_section_transition_hint", "snare_brush_turnaround_3and_whisper_pickup", "brush_hint_pp", "brush_hint_swish"),
            (3.5, "4&", "ballad_section_transition_hint", "snare_brush_turnaround_4and_whisper_to_next", "brush_hint_p", "brush_hint_release"),
        )
    elif fill_cell == "turnaround_2and_4_hat_hint":
        gestures = (
            (1.5, "2&", "ballad_section_transition_hint", "snare_brush_turnaround_2and_hint", "brush_hint_pp", "brush_hint_swish"),
            (3.0, "4", "ballad_section_transition_hint", "snare_brush_turnaround_4_hat_inside_brush_hint", "brush_hint_p", "brush_hint_tap"),
        )
    elif fill_cell == "turnaround_cross_stick_4_hint":
        gestures = (
            (3.0, "4", "ballad_section_transition_hint", "cross_stick_turnaround_beat4_hint", "brush_hint_p", "brush_hint_tap"),
        )
    elif fill_cell == "bridge_entry_soft_1_2and_hint":
        gestures = (
            (0.0, "1", "ballad_section_transition_hint", "snare_brush_bridge_entry_soft_1_hint", "brush_hint_pp", "brush_hint_swish"),
            (1.5, "2&", "ballad_section_transition_hint", "snare_brush_bridge_entry_soft_2and_lift", "brush_hint_p", "brush_hint_swish"),
        )
    elif fill_cell == "bridge_entry_low_tom_bloom_hint":
        gestures = (
            (0.0, "1", "ballad_section_transition_hint", "low_tom_brush_bridge_or_section_entry_bloom", "brush_hint_p", "brush_hint_swish"),
        )
    elif fill_cell == "section_tail_4_hat_cymbal_hint":
        gestures = (
            (3.0, "4", "ballad_section_transition_hint", "hat_section_tail_soft_4_hint", "brush_hint_pp", "brush_hint_tap"),
            (3.5, "4&", "ballad_section_transition_hint", "ride_cymbal_section_tail_4and_breath_hint", "brush_hint_pp", "brush_hint_release"),
        )
    elif fill_cell == "soft_pickup_to_4":
        gestures = (
            (2.5, "3&", "ballad_classic_brush_fill", "snare_brush_foreground_pickup_to_4", "brush_fill_pickup_p", "brush_fill_swish"),
            (3.0, "4", "ballad_classic_brush_fill", "snare_brush_foreground_answer_on_4", "brush_fill_release_mp", "brush_fill_tap"),
        )
    elif fill_cell == "tap_drag_tap_release":
        gestures = (
            (1.5, "2&", "ballad_classic_brush_fill", "snare_brush_foreground_tap_drag_start", "brush_fill_pickup_p", "brush_fill_tap"),
            (2.5, "3&", "ballad_classic_brush_fill", "snare_brush_foreground_drag_through_3and", "brush_fill_drag_mp", "brush_fill_drag"),
            (3.0, "4", "ballad_classic_brush_fill", "snare_brush_foreground_tap_release_on_4", "brush_fill_release_mf", "brush_fill_tap"),
            (3.5, "4&", "ballad_classic_brush_fill", "snare_brush_foreground_soft_release_to_next", "brush_fill_release_mp", "brush_fill_release"),
        )
    elif fill_cell == "single_stroke_4_to_next":
        gestures = (
            (2.0, "3", "ballad_classic_brush_fill", "snare_brush_foreground_single_stroke_4_1", "brush_fill_pickup_p", "brush_fill_tap"),
            (2.5, "3&", "ballad_classic_brush_fill", "snare_brush_foreground_single_stroke_4_2", "brush_fill_drag_mp", "brush_fill_tap"),
            (3.0, "4", "ballad_classic_brush_fill", "snare_brush_foreground_single_stroke_4_3", "brush_fill_release_mf", "brush_fill_tap"),
            (3.5, "4&", "ballad_classic_brush_fill", "snare_brush_foreground_single_stroke_4_to_next", "brush_fill_release_mp", "brush_fill_release"),
        )
    elif fill_cell == "turnaround_sweep_roll":
        gestures = (
            (1.5, "2&", "ballad_classic_brush_fill", "snare_brush_foreground_turnaround_roll_start", "brush_fill_pickup_p", "brush_fill_tap"),
            (2.0, "3", "ballad_classic_brush_fill", "snare_brush_foreground_turnaround_roll_mid", "brush_fill_drag_mp", "brush_fill_swish"),
            (2.5, "3&", "ballad_classic_brush_fill", "snare_brush_foreground_turnaround_roll_lift", "brush_fill_release_mp", "brush_fill_swish"),
            (3.5, "4&", "ballad_classic_brush_fill", "snare_brush_foreground_turnaround_roll_to_next", "brush_fill_release_mf", "brush_fill_release"),
        )
    else:
        return

    for beat, slot, role, articulation, dynamic, stroke in gestures:
        drum, resolved_dynamic, resolved_stroke = _render_transition_hint_entry(fill_cell, articulation, role, dynamic, stroke)
        _append_if_in_region(
            events,
            beat,
            role=role,
            drum=drum,
            dynamic=resolved_dynamic,
            stroke=resolved_stroke,
            articulation=articulation,
            decision=decision,
            slot=slot,
        )


def _append_phrase_release(events: list[Any], decision: dict[str, Any]) -> None:
    cell = str(decision.get("brush_feel_cell"))
    if cell == "final_release":
        # The final release is owned by the classic fill overlay.
        _append_classic_fill_overlay(events, decision)
        return
    fill_cell = str(decision.get("brush_classic_fill_cell") or "none")
    if cell == "phrase_breath_release" and fill_cell == "none":
        # Preserve the underlying pulse but add the 3& -> 4 -> 4& breath gesture.
        for beat, slot, articulation in ((2.5, "3&", "snare_brush_drag_into_4"), (3.5, "4&", "snare_brush_soft_release_to_next")):
            _append_if_in_region(events, beat, role="ballad_phrase_brush_breath", drum="snare", dynamic="brush_breath_pp", stroke="brush_swish", articulation=articulation, decision=decision, slot=slot)
    _append_classic_fill_overlay(events, decision)


def _events_for_decision(decision: dict[str, Any]) -> tuple[Any, ...]:
    events: list[Any] = []
    _append_brush_motion(events, decision)
    _append_anchor(events, decision)
    _append_feather_kick(events, decision)
    # Foreground fill gestures need audible space; duck only the overlapping
    # snare brush background while keeping quiet time anchors/feather intact.
    _duck_background_for_classic_fill(events, decision)
    _append_phrase_release(events, decision)
    # Keep order stable after combining layers.
    events.sort(key=lambda item: (float(item.local_beat), str(item.role), str(item.metadata.get("drum"))))
    return tuple(events)


def _normal_generation_runtime_context(context: dict[str, Any]) -> bool:
    return any(key in context for key in ("tempo", "ensemble", "ensemble_context", "rng"))


def get_pattern_candidates(context: dict | None = None) -> tuple[PatternCandidate, ...]:
    """Return Jazz Ballad bar-level brush time-feel candidates.

    v2_6_131 assumes a brush-capable drum sound source.  The pattern layer
    therefore describes brush sweep/offbeat/anchor/feather intent and projects a
    single bar-level time-feel plan into the current region.  It does not create
    internal brush drum voices, and it does not treat each chord region as a new
    independent drum loop.
    """

    context = dict(context or {})
    if not (_normal_generation_runtime_context(context) or context.get("jazz_ballad_brush_sound_source_time_feel_active") is True):
        return ()
    decision = build_brush_semantic_policy_decision(context)
    events = _events_for_decision(decision)
    if not events:
        return ()
    beats = tuple(float(event.local_beat) for event in events)
    metadata = _candidate_metadata(decision, event_count=len(events))
    return (
        PatternCandidate(
            name=f"jazz_ballad_brush_source_{metadata['brush_feel_cell']}_{metadata['bar_region_projection']['region_role']}",
            weight=1.0,
            category="jazz_ballad_bar_level_brush_sound_source_time_feel",
            events=events,
            tail_policy=TailPolicy.from_local_beats(beats, can_receive_next_chord_anticipation=False),
            tags=("jazz_ballad", "drums", "brush_source", "bar_level", "offbeat_policy", "feather_kick", "not_chord_region_loop", "audible_v2_6_137"),
            metadata=metadata,
        ),
    )
