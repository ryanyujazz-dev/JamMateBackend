from __future__ import annotations

from typing import Any

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.harmony.harmonic_context import HarmonicContext
from jammate_engine.core.pattern_runtime import Beat1Movability, PatternCandidate, TailPolicy, event_spec

from .gesture_policy import inner_movement_request, validate_gesture_request

STYLE_ID = "jazz_ballad"
PATTERN_LIBRARY_ID = "jazz_ballad.piano_comping"
PATTERN_LIBRARY_VERSION = "v2_5_9"
PHRASE_INTENT_VERSION = "v2_5_9"
PATTERN_DOMAIN = "comping"
TRACK_ROLE = "piano_harmonic_comping"
DEFAULT_ONSET_MODE = "simultaneous_onset"
BOUNDARY_NOTES = (
    "pitchless",
    "style_owned",
    "phrase_intent_foundation",
    "gesture_request_slots_only",
    "ballad_space_means_light_touch_not_full_bar_silence",
    "no_voicing_logic",
    "no_final_expression_values",
    "no_v1_texture_binding",
)


def _comping_metadata(
    *,
    density: str,
    cell: str,
    function: str,
    region_shape: str = "four_beat_region",
    phrase_family: str = "temporary_low_level_fallback",
    phrase_function: str | None = None,
    context_gate: str = "generic_ballad",
    gesture_intent: str = DEFAULT_ONSET_MODE,
) -> dict[str, Any]:
    return {
        "density": density,
        "style_id": STYLE_ID,
        "pattern_domain": PATTERN_DOMAIN,
        "pattern_library_id": PATTERN_LIBRARY_ID,
        "pattern_library_version": PATTERN_LIBRARY_VERSION,
        "phrase_intent_version": PHRASE_INTENT_VERSION,
        "track_role": TRACK_ROLE,
        "region_shape": region_shape,
        "rhythmic_cell": cell,
        "pattern_function": function,
        "phrase_family": phrase_family,
        "phrase_function": phrase_function or function,
        "context_gate": context_gate,
        "gesture_intent": gesture_intent,
        "onset_mode": DEFAULT_ONSET_MODE,
        "voicing_boundary": "pattern_is_pitchless",
        "gesture_boundary": "pattern_may_request_pitchless_gesture_slots_only",
        "expression_boundary": "expression_policy_owns_duration_velocity_touch_pedal",
        "v1_absorption_boundary": "learn_phrase_behavior_not_v1_code_or_texture_bundles",
        "music_pass": "v2_5_9_ballad_default_swing8_timing_patch",
    }


def _event_metadata(
    *,
    phrase_family: str,
    phrase_function: str,
    phrase_slot: str,
    gesture_intent: str = DEFAULT_ONSET_MODE,
    context_gate: str = "generic_ballad",
    timing_intent: str | None = None,
) -> dict[str, Any]:
    metadata = {
        "phrase_intent_version": PHRASE_INTENT_VERSION,
        "phrase_family": phrase_family,
        "phrase_function": phrase_function,
        "phrase_slot": phrase_slot,
        "gesture_intent": gesture_intent,
        "context_gate": context_gate,
        "voicing_boundary": "event_is_pitchless_no_texture_or_source_choice",
        "gesture_boundary": "gesture_request_is_projection_motion_contract_only",
    }
    if timing_intent:
        metadata["timing_intent"] = timing_intent
        metadata["timing_boundary"] = "logical_half_beat_upbeat_rendered_by_timing_policy_not_pattern_math"
    return metadata


def _harmonic_motion_from_context(context: dict | None):
    context = context or {}
    region = context.get("region")
    chord_symbol = str(context.get("chord_symbol") or getattr(region, "chord_symbol", "Cmaj7"))
    next_symbol = context.get("next_chord_symbol") or getattr(region, "next_chord_symbol", None)
    previous_symbol = None
    if region is not None:
        previous_symbol = getattr(region, "metadata", {}).get("previous_chord_symbol")
    previous_symbol = context.get("previous_chord_symbol") or previous_symbol
    return HarmonicContext.from_symbols(
        chord_symbol=chord_symbol,
        next_chord_symbol=str(next_symbol) if next_symbol else None,
        previous_chord_symbol=str(previous_symbol) if previous_symbol else None,
    ).functional_motion


def describe_pattern_library(context: dict | None = None) -> dict[str, Any]:
    candidates = tuple(get_pattern_candidates(context))
    motion = _harmonic_motion_from_context(context)
    return {
        "style_id": STYLE_ID,
        "library_id": PATTERN_LIBRARY_ID,
        "version": PATTERN_LIBRARY_VERSION,
        "phrase_intent_version": PHRASE_INTENT_VERSION,
        "domain": PATTERN_DOMAIN,
        "track_role": TRACK_ROLE,
        "default_onset_mode": DEFAULT_ONSET_MODE,
        "boundary_notes": list(BOUNDARY_NOTES),
        "functional_motion": {
            "previous_to_current_type": motion.previous_to_current_type,
            "current_to_next_type": motion.current_to_next_type,
            "window_type": motion.window_type,
            "tags": list(motion.tags),
        },
        "candidate_count": len(candidates),
        "phrase_families": sorted({str(candidate.metadata.get("phrase_family")) for candidate in candidates}),
        "candidates": [candidate.to_debug_dict() for candidate in candidates],
    }


def get_pattern_candidates(context: dict | None = None) -> tuple[PatternCandidate, ...]:
    """Jazz Ballad piano comping candidates.

    v2_5_4 starts the phrase-intent layer without creating a V1-style phrase
    engine.  Candidates remain ordinary V2 PatternCandidates: they define
    pitchless timing, phrase function, and optional GestureRequest slots only.
    They do not choose concrete notes, voicing textures, source degrees,
    durations, velocities, pedal values, or MIDI repair behavior.
    """

    duration = float((context or {}).get("region_duration_beats", 4.0))
    if duration <= 2.0:
        return _two_beat_region_candidates()
    motion = _harmonic_motion_from_context(context)
    return _four_beat_region_candidates(motion)


def _four_beat_region_candidates(motion) -> tuple[PatternCandidate, ...]:
    candidates: list[PatternCandidate] = [
        PatternCandidate(
            name="ballad_piano_soft_downbeat_sustain",
            weight=2.8,
            category="phrase_warm_pad_anchor",
            events=(
                event_spec(
                    track="piano",
                    beat=0.0,
                    role="harmonic",
                    gesture=simultaneous_onset(),
                    expression_hint="soft_sustain",
                    metadata=_event_metadata(
                        phrase_family="warm_pad",
                        phrase_function="minimum_harmonic_presence",
                        phrase_slot="anchor",
                    ),
                ),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0,)),
            beat1_movability=Beat1Movability(movable=True, reason="ballad_downbeat_touch_can_be_anticipated_when_previous_tail_free"),
            metadata=_comping_metadata(density="sparse", cell="1", function="minimum_harmonic_touch", phrase_family="warm_pad"),
            tags=("ballad", "piano", "sustain", "comping", "phrase_intent"),
        ),
        PatternCandidate(
            name="ballad_phrase_breath_answer_inner_motion",
            weight=0.52,
            category="phrase_breath_answer",
            events=(
                event_spec(
                    track="piano",
                    beat=0.0,
                    role="harmonic",
                    gesture=simultaneous_onset(),
                    expression_hint="soft_sustain",
                    metadata=_event_metadata(
                        phrase_family="breath_answer",
                        phrase_function="anchor_then_inner_voice_breath",
                        phrase_slot="anchor",
                    ),
                ),
                event_spec(
                    track="piano",
                    beat=2.5,
                    role="harmonic_motion",
                    gesture=inner_movement_request(
                        motion_shape="inner_voice_breath",
                        target_voice_class="inner",
                        phrase_function="anchor_then_inner_voice_breath",
                    ),
                    expression_hint="soft_answer",
                    metadata=_event_metadata(
                        phrase_family="breath_answer",
                        phrase_function="anchor_then_inner_voice_breath",
                        phrase_slot="inner_motion_answer",
                        gesture_intent="inner_movement",
                    ),
                ),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0, 2.5)),
            beat1_movability=Beat1Movability(movable=True, reason="phrase_anchor_can_move_initial_touch_when_tail_free"),
            metadata=_comping_metadata(
                density="medium",
                cell="1_3and_motion",
                function="anchor_then_inner_voice_breath",
                phrase_family="breath_answer",
                phrase_function="anchor_then_inner_voice_breath",
                gesture_intent="inner_movement",
            ),
            tags=("ballad", "piano", "phrase", "breath_answer", "inner_movement"),
        ),
        PatternCandidate(
            name="ballad_piano_downbeat_midbar_retouch",
            weight=0.58,
            category="fallback_soft_retouch",
            events=(
                event_spec(
                    track="piano",
                    beat=0.0,
                    role="harmonic",
                    gesture=simultaneous_onset(),
                    expression_hint="soft_sustain",
                    metadata=_event_metadata(
                        phrase_family="temporary_low_level_fallback",
                        phrase_function="anchored_midbar_retouch",
                        phrase_slot="anchor",
                    ),
                ),
                event_spec(
                    track="piano",
                    beat=2.0,
                    role="harmonic",
                    gesture=simultaneous_onset(),
                    expression_hint="soft_retouch",
                    metadata=_event_metadata(
                        phrase_family="temporary_low_level_fallback",
                        phrase_function="anchored_midbar_retouch",
                        phrase_slot="fallback_retouch",
                    ),
                ),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0, 2.0)),
            beat1_movability=Beat1Movability(movable=True, reason="anchored_ballad_cell_can_move_initial_touch_when_tail_free"),
            metadata=_comping_metadata(density="medium", cell="1_3", function="anchored_midbar_retouch"),
            tags=("ballad", "piano", "retouch", "comping", "temporary_fallback"),
        ),
        PatternCandidate(
            name="ballad_piano_downbeat_3and_answer",
            weight=0.32,
            category="fallback_soft_answer",
            events=(
                event_spec(
                    track="piano",
                    beat=0.0,
                    role="harmonic",
                    gesture=simultaneous_onset(),
                    expression_hint="soft_sustain",
                    metadata=_event_metadata(
                        phrase_family="temporary_low_level_fallback",
                        phrase_function="gentle_late_answer",
                        phrase_slot="anchor",
                    ),
                ),
                event_spec(
                    track="piano",
                    beat=2.5,
                    role="harmonic",
                    gesture=simultaneous_onset(),
                    expression_hint="soft_answer",
                    metadata=_event_metadata(
                        phrase_family="temporary_low_level_fallback",
                        phrase_function="gentle_late_answer",
                        phrase_slot="fallback_answer",
                    ),
                ),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0, 2.5)),
            beat1_movability=Beat1Movability(movable=True, reason="anchored_ballad_cell_can_move_initial_touch_when_tail_free"),
            metadata=_comping_metadata(density="medium", cell="1_3and", function="gentle_late_answer"),
            tags=("ballad", "piano", "3and", "answer", "comping", "temporary_fallback"),
        ),
        PatternCandidate(
            name="ballad_piano_downbeat_1and_whisper",
            weight=0.22,
            category="fallback_near_downbeat_whisper",
            events=(
                event_spec(
                    track="piano",
                    beat=0.0,
                    role="harmonic",
                    gesture=simultaneous_onset(),
                    expression_hint="soft_sustain",
                    metadata=_event_metadata(
                        phrase_family="temporary_low_level_fallback",
                        phrase_function="near_downbeat_whisper_not_delayed_whisper",
                        phrase_slot="anchor",
                    ),
                ),
                event_spec(
                    track="piano",
                    beat=0.5,
                    role="harmonic_motion",
                    gesture=inner_movement_request(
                        motion_shape="near_downbeat_upper_whisper",
                        target_voice_class="projection_group",
                        phrase_function="near_downbeat_whisper_not_delayed_whisper",
                    ),
                    expression_hint="soft_whisper",
                    metadata=_event_metadata(
                        phrase_family="temporary_low_level_fallback",
                        phrase_function="near_downbeat_whisper_not_delayed_whisper",
                        phrase_slot="fallback_whisper",
                        timing_intent="swing_upbeat",
                        gesture_intent="inner_movement",
                    ),
                ),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0, 0.5)),
            beat1_movability=Beat1Movability(movable=True, reason="anchored_ballad_cell_can_move_initial_touch_when_tail_free"),
            metadata=_comping_metadata(density="medium", cell="1_1and", function="near_downbeat_whisper_not_delayed_whisper"),
            tags=("ballad", "piano", "1and", "whisper", "comping", "temporary_fallback"),
        ),
    ]

    if motion.window_type == "major_ii_v_i":
        candidates.append(_major_251_stable_cadence_candidate())
    return tuple(candidates)


def _major_251_stable_cadence_candidate() -> PatternCandidate:
    phrase_family = "major_251_stable_cadence"
    phrase_function = "predominant_dominant_tonic_cadence_mark"
    context_gate = "major_ii_v_i_window_current_dominant_region"
    return PatternCandidate(
        name="ballad_phrase_major_251_stable_cadence",
        weight=0.48,
        category="phrase_major_251_stable_cadence",
        events=(
            event_spec(
                track="piano",
                beat=0.0,
                role="harmonic",
                gesture=simultaneous_onset(),
                expression_hint="soft_sustain",
                metadata=_event_metadata(
                    phrase_family=phrase_family,
                    phrase_function=phrase_function,
                    phrase_slot="dominant_anchor",
                    context_gate=context_gate,
                ),
            ),
            event_spec(
                track="piano",
                beat=2.5,
                role="harmonic_motion",
                gesture=inner_movement_request(
                    motion_shape="stable_cadence_inner_resolution",
                    target_voice_class="color_group",
                    phrase_function=phrase_function,
                ),
                expression_hint="soft_answer",
                metadata=_event_metadata(
                    phrase_family=phrase_family,
                    phrase_function=phrase_function,
                    phrase_slot="cadence_inner_motion",
                    gesture_intent="inner_movement",
                    context_gate=context_gate,
                ),
            ),
        ),
        tail_policy=TailPolicy.from_local_beats((0.0, 2.5)),
        beat1_movability=Beat1Movability(movable=True, reason="ballad_251_anchor_can_be_anticipated_when_previous_tail_free"),
        metadata=_comping_metadata(
            density="medium",
            cell="1_3and_cadence_motion",
            function=phrase_function,
            phrase_family=phrase_family,
            phrase_function=phrase_function,
            context_gate=context_gate,
            gesture_intent="inner_movement",
        ),
        tags=("ballad", "piano", "phrase", "major_251", "cadence", "inner_movement"),
    )


def _two_beat_region_candidates() -> tuple[PatternCandidate, ...]:
    return (
        PatternCandidate(
            name="ballad_piano_two_beat_soft_anchor",
            weight=2.4,
            category="two_beat_phrase_warm_pad_anchor",
            events=(
                event_spec(
                    track="piano",
                    beat=0.0,
                    role="harmonic",
                    gesture=simultaneous_onset(),
                    expression_hint="soft_sustain",
                    metadata=_event_metadata(
                        phrase_family="warm_pad",
                        phrase_function="two_beat_minimum_touch",
                        phrase_slot="anchor",
                        context_gate="two_beat_region",
                    ),
                ),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0,)),
            beat1_movability=Beat1Movability(movable=True, reason="two_beat_ballad_anchor_can_be_anticipated_when_previous_tail_free"),
            metadata=_comping_metadata(
                density="sparse",
                cell="region_start",
                function="two_beat_minimum_touch",
                region_shape="two_beat_region",
                phrase_family="warm_pad",
                context_gate="two_beat_region",
            ),
            tags=("ballad", "piano", "two_chord_bar", "sustain", "comping", "phrase_intent"),
        ),
        PatternCandidate(
            name="ballad_phrase_two_chord_soft_marks",
            weight=0.74,
            category="phrase_two_chord_soft_marks",
            events=(
                event_spec(
                    track="piano",
                    beat=0.0,
                    role="harmonic",
                    gesture=simultaneous_onset(),
                    expression_hint="soft_sustain",
                    metadata=_event_metadata(
                        phrase_family="two_chord_soft_marks",
                        phrase_function="two_chord_region_anchor_and_mark",
                        phrase_slot="anchor",
                        context_gate="two_beat_region",
                    ),
                ),
                event_spec(
                    track="piano",
                    beat=0.5,
                    role="harmonic_motion",
                    gesture=inner_movement_request(
                        motion_shape="two_chord_upper_soft_mark",
                        target_voice_class="projection_group",
                        phrase_function="two_chord_region_anchor_and_mark",
                    ),
                    expression_hint="soft_retouch",
                    metadata=_event_metadata(
                        phrase_family="two_chord_soft_marks",
                        phrase_function="two_chord_region_anchor_and_mark",
                        phrase_slot="soft_mark",
                        context_gate="two_beat_region",
                        timing_intent="swing_upbeat",
                        gesture_intent="inner_movement",
                    ),
                ),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0, 0.5)),
            beat1_movability=Beat1Movability(movable=True, reason="two_beat_ballad_anchor_can_be_anticipated_when_previous_tail_free"),
            metadata=_comping_metadata(
                density="medium",
                cell="region_start_1and",
                function="two_chord_region_anchor_and_mark",
                region_shape="two_beat_region",
                phrase_family="two_chord_soft_marks",
                phrase_function="two_chord_region_anchor_and_mark",
                context_gate="two_beat_region",
            ),
            tags=("ballad", "piano", "two_chord_bar", "phrase", "soft_marks"),
        ),
        PatternCandidate(
            name="ballad_piano_two_beat_light_retouch",
            weight=0.32,
            category="fallback_two_beat_soft_retouch",
            events=(
                event_spec(
                    track="piano",
                    beat=0.0,
                    role="harmonic",
                    gesture=simultaneous_onset(),
                    expression_hint="soft_sustain",
                    metadata=_event_metadata(
                        phrase_family="temporary_low_level_fallback",
                        phrase_function="two_beat_light_retouch",
                        phrase_slot="anchor",
                        context_gate="two_beat_region",
                    ),
                ),
                event_spec(
                    track="piano",
                    beat=0.5,
                    role="harmonic_motion",
                    gesture=inner_movement_request(
                        motion_shape="two_beat_upper_light_retouch",
                        target_voice_class="projection_group",
                        phrase_function="two_beat_light_retouch",
                    ),
                    expression_hint="soft_retouch",
                    metadata=_event_metadata(
                        phrase_family="temporary_low_level_fallback",
                        phrase_function="two_beat_light_retouch",
                        phrase_slot="fallback_retouch",
                        context_gate="two_beat_region",
                        timing_intent="swing_upbeat",
                        gesture_intent="inner_movement",
                    ),
                ),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0, 0.5)),
            beat1_movability=Beat1Movability(movable=True, reason="two_beat_ballad_anchor_can_be_anticipated_when_previous_tail_free"),
            metadata=_comping_metadata(
                density="medium",
                cell="region_start_1and",
                function="two_beat_light_retouch",
                region_shape="two_beat_region",
            ),
            tags=("ballad", "piano", "two_chord_bar", "retouch", "temporary_fallback"),
        ),
    )


# Import-time guard: the phrase candidates may request gestures, but those
# requests must stay inside the style-approved pitchless contract.
for _candidate in (*_four_beat_region_candidates(_harmonic_motion_from_context({})), *_two_beat_region_candidates()):
    for _spec in _candidate.events:
        if _spec.gesture is not None:
            validate_gesture_request(_spec.gesture)
