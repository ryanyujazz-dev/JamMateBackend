from __future__ import annotations

from typing import Any

from jammate_engine.core.pattern_runtime import PatternCandidate, TailPolicy, event_spec
from jammate_engine.styles.bossa_nova import arrangement_policy, fill_policy


BOSSA_BASS_AND_DRUMS_IDENTITY_AUDIT_VERSION = "v2_6_96"
BOSSA_FULL_BAND_ARRANGEMENT_ARC_LISTENING_REFINEMENT_VERSION = "v2_6_98"
BOSSA_STYLE_BASELINE_PHASE_COMPLETION_CHECKPOINT_VERSION = "v2_6_99"
BOSSA_DRUM_SHAKER_MICRODYNAMICS_AND_PULSE_SHAPE_VERSION = "v2_6_100"
BOSSA_DRUM_CROSS_STICK_PHRASE_LOCAL_CONTOUR_VERSION = "v2_6_101"
BOSSA_KICK_BASS_LOCK_AND_LOW_FREQUENCY_SHADOW_VERSION = "v2_6_105"
BOSSA_LIGHT_MARKER_FILL_POLICY_VERSION = "v2_6_106"
BOSSA_DRUM_BASELINE_CHECKPOINT_VERSION = "v2_6_107"


def _duration_family(duration: float) -> str:
    if duration <= 1.25:
        return "very_short_region"
    if duration <= 2.25:
        return "split_region"
    return "full_region"


def _region_local_bar_index(context: dict[str, Any]) -> int:
    raw = context.get("region_source_bar_index")
    if raw is None:
        raw = context.get("bar_index")
    region = context.get("region")
    if raw is None and region is not None:
        raw = getattr(region, "source_bar_index", None) or getattr(region, "bar_index", None)
    try:
        return int(raw or 0)
    except (TypeError, ValueError):
        return 0


def _phrase_local_bar_index(context: dict[str, Any]) -> int:
    # Keep this ChordRegion-first: we only use source/performance bar metadata
    # as phrase-position metadata for the region-local drum event shape.  This
    # is not a bar-first pattern template or a separate phrase engine.
    raw = context.get("region_source_bar_index")
    if raw is None:
        raw = context.get("region_performance_bar_index")
    if raw is None:
        raw = context.get("bar_index")
    region = context.get("region")
    if raw is None and region is not None:
        raw = (
            getattr(region, "source_bar_index", None)
            if getattr(region, "source_bar_index", None) is not None
            else getattr(region, "performance_bar_index", None)
        )
    try:
        return int(raw or 0) % 8
    except (TypeError, ValueError):
        return 0


def _cross_stick_phrase_pattern(context: dict[str, Any]) -> str:
    return "B" if _phrase_local_bar_index(context) % 2 else "A"


def _arc_refinement(context: dict[str, Any]) -> dict[str, Any]:
    return arrangement_policy.resolve_full_band_arrangement_arc_listening_refinement(
        context.get("bossa_nova_arrangement_arc_intent")
    )


def _shaker_pulse_slot(local_beat: float) -> str:
    beat = round(float(local_beat) % 4.0, 3)
    if beat in {0.0, 2.0}:
        return "primary_clear"
    if beat in {1.0, 3.0}:
        return "secondary_mid"
    if beat in {0.5, 2.5}:
        return "offbeat_light"
    return "offbeat_feather"


def _shaker_pulse_role(local_beat: float) -> str:
    beat = round(float(local_beat) % 4.0, 3)
    return {
        0.0: "shaker_beat_1_clear",
        0.5: "shaker_1and_light",
        1.0: "shaker_beat_2_mid",
        1.5: "shaker_2and_feather",
        2.0: "shaker_beat_3_clear",
        2.5: "shaker_3and_light",
        3.0: "shaker_beat_4_mid",
        3.5: "shaker_4and_feather",
    }.get(beat, "shaker_time")


def _meta(context: dict[str, Any], *, family: str, pattern_function: str, cross_pattern: str) -> dict[str, Any]:
    arc = _arc_refinement(context)
    return {
        "style_id": "bossa_nova",
        "pattern_domain": "percussion_foundation",
        "pattern_library_id": "bossa_nova.percussion_foundation",
        "pattern_library_version": BOSSA_BASS_AND_DRUMS_IDENTITY_AUDIT_VERSION,
        "bossa_bass_and_drums_identity_audit_active": True,
        "bossa_bass_and_drums_identity_audit_version": BOSSA_BASS_AND_DRUMS_IDENTITY_AUDIT_VERSION,
        "drum_identity": "shaker_cross_stick_light_kick",
        "drum_region_duration_family": family,
        "cross_stick_phrase_pattern": cross_pattern,
        "pattern_function": pattern_function,
        "chord_region_first": True,
        "bar_first": False,
        "swing_ride_pattern": False,
        "rock_backbeat_pattern": False,
        "timing_intent": "straight_even",
        "region_duration_beats_at_selection": float(context.get("region_duration_beats", 4.0)),
        "bossa_full_band_arrangement_arc_listening_refinement_active": bool(arc.get("active")),
        "bossa_full_band_arrangement_arc_listening_refinement_version": BOSSA_FULL_BAND_ARRANGEMENT_ARC_LISTENING_REFINEMENT_VERSION,
        "bossa_full_band_arrangement_arc_phase": arc.get("phase"),
        "bossa_full_band_arrangement_arc_runtime_intent": arc.get("runtime_intent"),
        "bossa_full_band_arrangement_arc_band": arc.get("full_band_arc_band"),
        "bossa_full_band_arrangement_arc_boundary": arc.get("boundary"),
        "bossa_style_baseline_phase_completion_checkpoint": True,
        "bossa_style_baseline_phase_completion_checkpoint_version": BOSSA_STYLE_BASELINE_PHASE_COMPLETION_CHECKPOINT_VERSION,
        "bossa_style_baseline_phase_completion_checkpoint_behavior_change": False,
        "bossa_style_baseline_phase_completion_checkpoint_boundary": "style_identity_metadata_only_no_pattern_or_realizer_change",
        "bossa_drum_shaker_microdynamics_and_pulse_shape_active": True,
        "bossa_drum_shaker_microdynamics_and_pulse_shape_version": BOSSA_DRUM_SHAKER_MICRODYNAMICS_AND_PULSE_SHAPE_VERSION,
        "bossa_drum_shaker_microdynamics_and_pulse_shape_scope": "semantic_shaker_pulse_slots_and_shared_percussion_realizer_velocity_shape",
        "bossa_drum_shaker_microdynamics_and_pulse_shape_no_parallel_selector": True,
        "bossa_drum_shaker_microdynamics_and_pulse_shape_no_new_pattern_vocabulary": True,
        "bossa_drum_shaker_microdynamics_and_pulse_shape_no_api_agent_harmonyos_change": True,
        "bossa_drum_cross_stick_phrase_local_contour_active": True,
        "bossa_drum_cross_stick_phrase_local_contour_version": BOSSA_DRUM_CROSS_STICK_PHRASE_LOCAL_CONTOUR_VERSION,
        "bossa_drum_cross_stick_phrase_local_contour_scope": "phrase-local cross-stick A/B slots plus arc-aware light subtraction inside the existing percussion candidate",
        "bossa_drum_cross_stick_phrase_local_contour_no_parallel_selector": True,
        "bossa_drum_cross_stick_phrase_local_contour_no_new_pattern_vocabulary": True,
        "bossa_drum_cross_stick_phrase_local_contour_no_api_agent_harmonyos_change": True,
        "bossa_kick_bass_lock_and_low_frequency_shadow_active": True,
        "bossa_kick_bass_lock_and_low_frequency_shadow_version": BOSSA_KICK_BASS_LOCK_AND_LOW_FREQUENCY_SHADOW_VERSION,
        "bossa_kick_bass_lock_and_low_frequency_shadow_scope": "semantic kick/bass root-fifth locking and low-frequency shadow shaping inside the existing percussion candidate",
        "bossa_kick_bass_lock_and_low_frequency_shadow_no_parallel_selector": True,
        "bossa_kick_bass_lock_and_low_frequency_shadow_no_new_pattern_vocabulary": True,
        "bossa_kick_bass_lock_and_low_frequency_shadow_no_api_agent_harmonyos_change": True,
        "bossa_light_marker_fill_policy_active": True,
        "bossa_light_marker_fill_policy_version": BOSSA_LIGHT_MARKER_FILL_POLICY_VERSION,
        "bossa_light_marker_fill_policy_scope": "sparse phrase-end / turnaround / ending cross-stick markers inside the existing percussion candidate",
        "bossa_light_marker_fill_policy_no_parallel_selector": True,
        "bossa_light_marker_fill_policy_no_bar_first_restore": True,
        "bossa_light_marker_fill_policy_no_tom_crash_roll_fill": True,
        "bossa_light_marker_fill_policy_no_swing_or_rock_fill": True,
        "bossa_light_marker_fill_policy_no_api_agent_harmonyos_change": True,
        "bossa_drum_baseline_checkpoint_active": True,
        "bossa_drum_baseline_checkpoint_version": BOSSA_DRUM_BASELINE_CHECKPOINT_VERSION,
        "bossa_drum_baseline_checkpoint_behavior_change": False,
        "bossa_drum_baseline_checkpoint_scope": "metadata/audit checkpoint for shaker microdynamics, cross-stick contour, kick/bass lock, and light marker fill policy",
        "bossa_drum_baseline_checkpoint_completed_versions": (
            BOSSA_DRUM_SHAKER_MICRODYNAMICS_AND_PULSE_SHAPE_VERSION,
            BOSSA_DRUM_CROSS_STICK_PHRASE_LOCAL_CONTOUR_VERSION,
            BOSSA_KICK_BASS_LOCK_AND_LOW_FREQUENCY_SHADOW_VERSION,
            BOSSA_LIGHT_MARKER_FILL_POLICY_VERSION,
        ),
        "bossa_drum_baseline_checkpoint_no_parallel_selector": True,
        "bossa_drum_baseline_checkpoint_no_new_pattern_vocabulary": True,
        "bossa_drum_baseline_checkpoint_no_piano_bass_voicing_change": True,
        "bossa_drum_baseline_checkpoint_no_api_agent_harmonyos_change": True,
    }


def _drum_event(
    beat: float,
    *,
    drum: str,
    role: str,
    dynamic: str,
    stroke: str = "short",
    arc: dict[str, Any] | None = None,
    extra_metadata: dict[str, Any] | None = None,
):
    arc = dict(arc or {})
    metadata = {
        "drum": drum,
        "bossa_drum_voice": role,
        "dynamic_profile": dynamic,
        "stroke_profile": stroke,
        "timing_intent": "straight_even",
        "bossa_bass_and_drums_identity_audit_version": BOSSA_BASS_AND_DRUMS_IDENTITY_AUDIT_VERSION,
        "bossa_full_band_arrangement_arc_listening_refinement_active": bool(arc.get("active")),
        "bossa_full_band_arrangement_arc_listening_refinement_version": BOSSA_FULL_BAND_ARRANGEMENT_ARC_LISTENING_REFINEMENT_VERSION,
        "bossa_full_band_arrangement_arc_phase": arc.get("phase"),
        "bossa_full_band_arrangement_arc_runtime_intent": arc.get("runtime_intent"),
        "bossa_full_band_arrangement_arc_band": arc.get("full_band_arc_band"),
        "bossa_full_band_arrangement_arc_boundary": arc.get("boundary"),
        "drum_identity": "shaker_cross_stick_light_kick",
        "swing_ride_pattern": False,
        "rock_backbeat_pattern": False,
        "bossa_style_baseline_phase_completion_checkpoint": True,
        "bossa_style_baseline_phase_completion_checkpoint_version": BOSSA_STYLE_BASELINE_PHASE_COMPLETION_CHECKPOINT_VERSION,
        "bossa_style_baseline_phase_completion_checkpoint_behavior_change": False,
        "bossa_style_baseline_phase_completion_checkpoint_boundary": "drum_event_metadata_only_no_pattern_or_realizer_change",
        "bossa_drum_baseline_checkpoint_active": True,
        "bossa_drum_baseline_checkpoint_version": BOSSA_DRUM_BASELINE_CHECKPOINT_VERSION,
        "bossa_drum_baseline_checkpoint_behavior_change": False,
        "bossa_drum_baseline_checkpoint_boundary": "drum_event_metadata_only_no_pattern_or_realizer_change",
        "bossa_drum_baseline_checkpoint_completed_versions": (
            BOSSA_DRUM_SHAKER_MICRODYNAMICS_AND_PULSE_SHAPE_VERSION,
            BOSSA_DRUM_CROSS_STICK_PHRASE_LOCAL_CONTOUR_VERSION,
            BOSSA_KICK_BASS_LOCK_AND_LOW_FREQUENCY_SHADOW_VERSION,
            BOSSA_LIGHT_MARKER_FILL_POLICY_VERSION,
        ),
        "bossa_drum_baseline_checkpoint_no_parallel_selector": True,
        "bossa_drum_baseline_checkpoint_no_new_pattern_vocabulary": True,
        "bossa_drum_baseline_checkpoint_no_piano_bass_voicing_change": True,
        "bossa_drum_baseline_checkpoint_no_api_agent_harmonyos_change": True,
    }
    metadata.update(dict(extra_metadata or {}))
    return event_spec(
        track="drums",
        beat=beat,
        role="drum",
        metadata=metadata,
    )


def _shaker_events(duration: float, *, arc: dict[str, Any]) -> tuple[Any, ...]:
    beats = []
    beat = 0.0
    # Keep the shaker region-local so split ChordRegions do not duplicate or spill.
    while beat < max(0.25, duration) - 1e-9 and beat <= 3.5 + 1e-9:
        beats.append(round(beat, 3))
        beat += 0.5
    dynamic = str(arc.get("drum_shaker_dynamic_profile") or "shaker_light")
    return tuple(
        _drum_event(
            beat,
            drum="shaker",
            role="shaker_time",
            dynamic=dynamic,
            arc=arc,
            extra_metadata={
                "bossa_drum_voice_family": "shaker_time",
                "shaker_pulse_slot": _shaker_pulse_slot(beat),
                "shaker_pulse_position": _shaker_pulse_role(beat),
                "shaker_microdynamic_profile": "bossa_shaker_straight_8th_pulse_shape",
                "shaker_microdynamic_enabled": True,
                "shaker_microdynamic_timing_intent": "straight_even_not_swing",
                "bossa_drum_shaker_microdynamics_and_pulse_shape_active": True,
                "bossa_drum_shaker_microdynamics_and_pulse_shape_version": BOSSA_DRUM_SHAKER_MICRODYNAMICS_AND_PULSE_SHAPE_VERSION,
                "bossa_drum_shaker_microdynamics_and_pulse_shape_boundary": "semantic_slot_only_no_pattern_velocity",
            },
        )
        for beat in beats
    )


def _kick_lock_extra_metadata(*, slot: str, bass_degree: str, family: str, arc: dict[str, Any]) -> dict[str, Any]:
    return {
        "bossa_drum_voice_family": "kick_bass_locked_low_frequency_shadow",
        "kick_bass_lock_slot": slot,
        "kick_locked_to_bass_degree": bass_degree,
        "kick_locked_to_bass_event_role": f"bass_{bass_degree}",
        "kick_low_frequency_role": "shadow_not_driver",
        "kick_shadow_strength": "root_shadow" if bass_degree == "root" else "fifth_shadow_lighter",
        "kick_region_duration_family": family,
        "kick_bass_lock_arc_band": arc.get("full_band_arc_band"),
        "kick_bass_lock_arc_phase": arc.get("phase"),
        "kick_bass_lock_timing_intent": "straight_even_not_swing",
        "kick_four_on_floor_driver": False,
        "kick_rock_backbeat_driver": False,
        "bossa_kick_bass_lock_and_low_frequency_shadow_active": True,
        "bossa_kick_bass_lock_and_low_frequency_shadow_version": BOSSA_KICK_BASS_LOCK_AND_LOW_FREQUENCY_SHADOW_VERSION,
        "bossa_kick_bass_lock_and_low_frequency_shadow_boundary": "semantic_lock_slot_and_shadow_role_only_no_pattern_velocity",
    }


def _kick_event(beat: float, *, role: str, dynamic: str, slot: str, bass_degree: str, family: str, arc: dict[str, Any]):
    return _drum_event(
        beat,
        drum="kick",
        role=role,
        dynamic=dynamic,
        arc=arc,
        extra_metadata=_kick_lock_extra_metadata(slot=slot, bass_degree=bass_degree, family=family, arc=arc),
    )


def _kick_events(duration: float, *, family: str, arc: dict[str, Any]) -> tuple[Any, ...]:
    root_dynamic = str(arc.get("drum_kick_root_dynamic_profile") or "bossa_kick_root")
    fifth_dynamic = str(arc.get("drum_kick_fifth_dynamic_profile") or "bossa_kick_fifth")
    events = [
        _kick_event(
            0.0,
            role="soft_kick_root_shadow",
            dynamic=root_dynamic,
            slot="root_on_1_locked_shadow",
            bass_degree="root",
            family=family,
            arc=arc,
        )
    ]
    if duration > 2.25:
        events.append(
            _kick_event(
                2.0,
                role="soft_kick_fifth_shadow",
                dynamic=fifth_dynamic,
                slot="fifth_on_3_locked_shadow",
                bass_degree="fifth",
                family=family,
                arc=arc,
            )
        )
    return tuple(events)


def _cross_contour_density(arc: dict[str, Any]) -> str:
    band = str(arc.get("full_band_arc_band") or "warm_flow")
    phase = str(arc.get("phase") or "")
    if band == "soft_release" or "release" in phase:
        return "settled_release_sparse"
    if band == "breath_space" or "breath" in phase:
        return "breath_space_reduced"
    if band == "gentle_lift" or "lift" in phase:
        return "gentle_lift_clear"
    if band == "clear_identity":
        return "identity_clear"
    return "warm_flow_full"


def _cross_extra_metadata(*, pattern: str, phrase_local_index: int, phrase_slot: str, contour_density: str, arc: dict[str, Any]) -> dict[str, Any]:
    return {
        "bossa_drum_voice_family": "cross_stick_phrase_local_contour",
        "cross_stick_phrase_pattern": pattern,
        "cross_stick_phrase_local_bar_index": int(phrase_local_index),
        "cross_stick_phrase_pair_index": int(phrase_local_index) // 2,
        "cross_stick_phrase_slot": phrase_slot,
        "cross_stick_contour_density": contour_density,
        "cross_stick_arc_band": arc.get("full_band_arc_band"),
        "cross_stick_arc_phase": arc.get("phase"),
        "cross_stick_contour_timing_intent": "straight_even_not_swing",
        "bossa_drum_cross_stick_phrase_local_contour_active": True,
        "bossa_drum_cross_stick_phrase_local_contour_version": BOSSA_DRUM_CROSS_STICK_PHRASE_LOCAL_CONTOUR_VERSION,
        "bossa_drum_cross_stick_phrase_local_contour_boundary": "semantic_slot_and_arc_density_only_no_pattern_velocity",
    }


def _cross_event(beat: float, *, role: str, dynamic: str, phrase_slot: str, pattern: str, phrase_local_index: int, contour_density: str, arc: dict[str, Any]):
    return _drum_event(
        beat,
        drum="cross_stick",
        role=role,
        dynamic=dynamic,
        arc=arc,
        extra_metadata=_cross_extra_metadata(
            pattern=pattern,
            phrase_local_index=phrase_local_index,
            phrase_slot=phrase_slot,
            contour_density=contour_density,
            arc=arc,
        ),
    )


def _cross_stick_events(duration: float, *, cross_pattern: str, arc: dict[str, Any], phrase_local_index: int) -> tuple[Any, ...]:
    main_dynamic = str(arc.get("drum_cross_main_dynamic_profile") or "bossa_cross_main")
    light_dynamic = str(arc.get("drum_cross_light_dynamic_profile") or "bossa_cross_light")
    contour_density = _cross_contour_density(arc)
    if duration <= 1.25:
        return ()
    if duration <= 2.25:
        return (
            _cross_event(
                1.0,
                role="cross_stick_split_mark",
                dynamic=light_dynamic,
                phrase_slot="split_region_light_mark",
                pattern="split",
                phrase_local_index=phrase_local_index,
                contour_density="split_region_single_mark",
                arc=arc,
            ),
        )

    if cross_pattern == "B":
        events = [
            _cross_event(1.0, role="cross_stick_B_2", dynamic=main_dynamic, phrase_slot="B_beat2_response_anchor", pattern="B", phrase_local_index=phrase_local_index, contour_density=contour_density, arc=arc),
        ]
        if contour_density not in {"settled_release_sparse"}:
            events.append(_cross_event(2.5, role="cross_stick_B_3and", dynamic=light_dynamic, phrase_slot="B_3and_light_answer", pattern="B", phrase_local_index=phrase_local_index, contour_density=contour_density, arc=arc))
        return tuple(events)

    events = [
        _cross_event(0.0, role="cross_stick_A_1", dynamic=main_dynamic, phrase_slot="A_beat1_phrase_anchor", pattern="A", phrase_local_index=phrase_local_index, contour_density=contour_density, arc=arc),
        _cross_event(1.5, role="cross_stick_A_2and", dynamic=light_dynamic, phrase_slot="A_2and_syncopated_answer", pattern="A", phrase_local_index=phrase_local_index, contour_density=contour_density, arc=arc),
    ]
    if contour_density not in {"breath_space_reduced", "settled_release_sparse"}:
        events.append(_cross_event(3.0, role="cross_stick_A_4", dynamic=main_dynamic, phrase_slot="A_beat4_phrase_tail", pattern="A", phrase_local_index=phrase_local_index, contour_density=contour_density, arc=arc))
    return tuple(events)


def _marker_policy(context: dict[str, Any], *, duration: float, arc: dict[str, Any]) -> dict[str, Any]:
    return fill_policy.classify_light_marker_context(context, arc, duration_beats=duration)


def _marker_slot_metadata(*, kind: str, slot: str, policy: dict[str, Any], arc: dict[str, Any]) -> dict[str, Any]:
    return {
        "bossa_drum_voice_family": "light_marker_fill_policy",
        "bossa_light_marker_fill_policy_active": True,
        "bossa_light_marker_fill_policy_version": BOSSA_LIGHT_MARKER_FILL_POLICY_VERSION,
        "bossa_light_marker_fill_policy_kind": kind,
        "bossa_light_marker_fill_policy_slot": slot,
        "bossa_light_marker_fill_policy_reason": policy.get("reason"),
        "bossa_light_marker_fill_policy_scope": "rim_click_marker_not_tom_crash_roll_fill",
        "bossa_light_marker_fill_policy_no_parallel_selector": True,
        "bossa_light_marker_fill_policy_no_bar_first_restore": True,
        "bossa_light_marker_fill_policy_no_tom_crash_roll_fill": True,
        "bossa_light_marker_fill_policy_no_swing_or_rock_fill": True,
        "bossa_light_marker_fill_policy_pattern_layer_numeric_values": False,
        "bossa_light_marker_fill_policy_arc_band": arc.get("full_band_arc_band"),
        "bossa_light_marker_fill_policy_arc_phase": arc.get("phase"),
        "bossa_drum_cross_stick_phrase_local_contour_active": True,
        "bossa_drum_cross_stick_phrase_local_contour_version": BOSSA_DRUM_CROSS_STICK_PHRASE_LOCAL_CONTOUR_VERSION,
        "cross_stick_phrase_pattern": "split",
        "cross_stick_phrase_local_bar_index": -1,
        "cross_stick_phrase_pair_index": -1,
        "cross_stick_phrase_slot": slot,
        "cross_stick_contour_density": "light_marker_fill_policy",
        "cross_stick_arc_band": arc.get("full_band_arc_band"),
        "cross_stick_arc_phase": arc.get("phase"),
        "cross_stick_contour_timing_intent": "straight_even_not_swing",
        "timing_intent": "straight_even_not_swing",
        "swing_ride_pattern": False,
        "rock_backbeat_pattern": False,
        "tom_fill_pattern": False,
        "crash_fill_pattern": False,
        "snare_roll_fill_pattern": False,
    }


def _marker_event(beat: float, *, kind: str, role: str, dynamic: str, slot: str, policy: dict[str, Any], arc: dict[str, Any]):
    return _drum_event(
        beat,
        drum="cross_stick",
        role=role,
        dynamic=dynamic,
        arc=arc,
        extra_metadata=_marker_slot_metadata(kind=kind, slot=slot, policy=policy, arc=arc),
    )


def _light_marker_events(duration: float, *, arc: dict[str, Any], context: dict[str, Any], existing_cross_beats: tuple[float, ...]) -> tuple[Any, ...]:
    policy = _marker_policy(context, duration=duration, arc=arc)
    if policy.get("enabled") is not True:
        return ()
    kind = str(policy.get("marker_kind") or "none")
    occupied = {round(float(beat), 3) for beat in existing_cross_beats}
    if kind == "phrase_end_micro":
        candidates = ((3.5, "phrase_end_micro_4and", "bossa_marker_micro", "micro_4and"),)
    elif kind == "turnaround_light":
        candidates = (
            (2.5, "turnaround_light_3and", "bossa_marker_turnaround_light", "turnaround_3and"),
            (3.5, "turnaround_light_4and", "bossa_marker_turnaround_light", "turnaround_4and"),
        )
    elif kind == "ending_soft":
        if duration <= 2.25:
            candidates = (
                (1.0, "ending_soft_short_region_4", "bossa_marker_ending_soft", "ending_short_region_4"),
                (1.5, "ending_soft_short_region_4and", "bossa_marker_ending_soft", "ending_short_region_4and"),
            )
        else:
            candidates = (
                (2.5, "ending_soft_3and", "bossa_marker_ending_soft", "ending_3and"),
                (3.0, "ending_soft_4", "bossa_marker_ending_soft", "ending_4"),
                (3.5, "ending_soft_4and", "bossa_marker_ending_soft", "ending_4and"),
            )
    else:
        return ()

    events = []
    for beat, role, dynamic, slot in candidates:
        if round(float(beat), 3) in occupied:
            continue
        if beat < max(0.25, duration) - 1e-9 and beat <= 3.5 + 1e-9:
            events.append(_marker_event(beat, kind=kind, role=role, dynamic=dynamic, slot=slot, policy=policy, arc=arc))
    return tuple(events)


def get_pattern_candidates(context: dict | None = None) -> tuple[PatternCandidate, ...]:
    """Bossa percussion identity candidate.

    v2_6_96 replaces the old hihat placeholder in place with a region-local
    shaker/cross-stick/light-kick identity layer. v2_6_100 keeps that candidate
    shape and refines the shaker by annotating semantic pulse slots; v2_6_101
    refines the existing cross-stick layer with phrase-local A/B slots; v2_6_105
    refines the low-frequency layer so kick remains a semantic shadow locked to
    the Bossa bass root/fifth support instead of becoming a dance/rock driver.
    v2_6_106 adds sparse phrase-end/turnaround/ending cross-stick markers inside
    the same candidate; it does not add tom/crash/roll fills or a selector.
    v2_6_107 is a drum-baseline checkpoint only: it stamps audit metadata and
    freezes the current Bossa drum baseline without adding new drum behavior.
    """

    context = dict(context or {})
    duration = float(context.get("region_duration_beats", 4.0))
    family = _duration_family(duration)
    phrase_local_index = _phrase_local_bar_index(context)
    cross_pattern = _cross_stick_phrase_pattern(context)
    arc = _arc_refinement(context)
    shaker_events = _shaker_events(duration, arc=arc)
    cross_events = _cross_stick_events(duration, cross_pattern=cross_pattern, arc=arc, phrase_local_index=phrase_local_index)
    marker_events = _light_marker_events(
        duration,
        arc=arc,
        context=context,
        existing_cross_beats=tuple(float(event.local_beat) for event in cross_events),
    )
    events = shaker_events + cross_events + marker_events + _kick_events(duration, family=family, arc=arc)
    occupied = tuple(float(spec.local_beat) for spec in events)
    return (
        PatternCandidate(
            name=f"bossa_drums_shaker_cross_stick_kick_{family}_{cross_pattern}",
            weight=1.0,
            category="bossa_shaker_cross_stick_light_kick_identity",
            events=events,
            tail_policy=TailPolicy.from_local_beats(occupied, can_receive_next_chord_anticipation=False),
            tags=("bossa", "drums", "shaker", "cross_stick", "light_kick", "light_marker", "drum_baseline_checkpoint", "not_swing_ride", "not_rock_backbeat", "chord_region_first"),
            metadata=_meta(context, family=family, pattern_function="shaker_cross_stick_light_kick_identity", cross_pattern=cross_pattern),
        ),
    )
