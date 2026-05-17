from __future__ import annotations

from typing import Any

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.pattern_runtime import Beat1Movability, PatternCandidate, TailPolicy, event_spec

STYLE_ID = "medium_swing"
PATTERN_LIBRARY_ID = "medium_swing.piano_comping"
PATTERN_LIBRARY_VERSION = "v2_0_42"
PATTERN_DOMAIN = "comping"
TRACK_ROLE = "piano_harmonic_comping"
DEFAULT_ONSET_MODE = "simultaneous_onset"
BOUNDARY_NOTES = (
    "pitchless",
    "style_owned",
    "no_voicing_logic",
    "no_final_expression_values",
)


def _comping_metadata(*, density: str, cell: str, function: str, region_shape: str = "four_beat_region") -> dict[str, Any]:
    return {
        "density": density,
        "style_id": STYLE_ID,
        "pattern_domain": PATTERN_DOMAIN,
        "pattern_library_id": PATTERN_LIBRARY_ID,
        "pattern_library_version": PATTERN_LIBRARY_VERSION,
        "track_role": TRACK_ROLE,
        "region_shape": region_shape,
        "rhythmic_cell": cell,
        "pattern_function": function,
        "onset_mode": DEFAULT_ONSET_MODE,
        "voicing_boundary": "pattern_is_pitchless",
    }


def describe_pattern_library(context: dict | None = None) -> dict[str, Any]:
    candidates = tuple(get_pattern_candidates(context))
    return {
        "style_id": STYLE_ID,
        "library_id": PATTERN_LIBRARY_ID,
        "version": PATTERN_LIBRARY_VERSION,
        "domain": PATTERN_DOMAIN,
        "track_role": TRACK_ROLE,
        "default_onset_mode": DEFAULT_ONSET_MODE,
        "boundary_notes": list(BOUNDARY_NOTES),
        "candidate_count": len(candidates),
        "candidates": [candidate.to_debug_dict() for candidate in candidates],
    }


def get_pattern_candidates(context: dict | None = None) -> tuple[PatternCandidate, ...]:
    """Medium swing piano comping candidates.

    These are pitchless rhythm/gesture candidates. They do not contain chord
    tones, MIDI pitches, final durations, velocities, or pedal decisions.
    v2_0_42 standardizes the library metadata so comping vocabulary can be
    audited without moving voicing or expression logic into style patterns.
    """

    duration = float((context or {}).get("region_duration_beats", 4.0))
    if duration <= 2.0:
        return _two_beat_region_candidates()
    return _four_beat_region_candidates()


def _four_beat_region_candidates() -> tuple[PatternCandidate, ...]:
    return (
        PatternCandidate(
            name="medium_swing_piano_anchor_1",
            weight=1.2,
            category="stable_comping_anchor",
            events=(
                event_spec(track="piano", beat=0.0, role="harmonic", gesture=simultaneous_onset(), expression_hint="comp_medium"),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0,)),
            beat1_movability=Beat1Movability(movable=True, reason="downbeat_harmonic_anchor_can_be_anticipated_later"),
            metadata=_comping_metadata(density="sparse", cell="1", function="anchor"),
            tags=("swing", "piano", "stable", "comping"),
        ),
        PatternCandidate(
            name="medium_swing_piano_charleston_1_2and",
            weight=3.0,
            category="swing_comping_charleston",
            events=(
                event_spec(track="piano", beat=0.0, role="harmonic", gesture=simultaneous_onset(), expression_hint="comp_accent"),
                event_spec(track="piano", beat=1.5, role="harmonic", gesture=simultaneous_onset(), expression_hint="comp_short"),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0, 1.5)),
            beat1_movability=Beat1Movability(movable=True, reason="charleston_downbeat_can_be_anticipated_later"),
            metadata=_comping_metadata(density="dense", cell="1_2and", function="charleston_answer"),
            tags=("swing", "piano", "charleston", "audible_v208", "comping"),
        ),
        PatternCandidate(
            name="medium_swing_piano_1_3and_answer",
            weight=2.3,
            category="swing_comping_answer",
            events=(
                event_spec(track="piano", beat=0.0, role="harmonic", gesture=simultaneous_onset(), expression_hint="comp_medium"),
                event_spec(track="piano", beat=2.5, role="harmonic", gesture=simultaneous_onset(), expression_hint="comp_short"),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0, 2.5)),
            beat1_movability=Beat1Movability(movable=True, reason="beat1_anchor_can_be_anticipated_later"),
            metadata=_comping_metadata(density="dense", cell="1_3and", function="answer"),
            tags=("swing", "piano", "answer", "audible_v208", "comping"),
        ),
        PatternCandidate(
            name="medium_swing_piano_backbeat_2_4",
            weight=1.1,
            category="swing_comping_backbeat",
            events=(
                event_spec(track="piano", beat=1.0, role="harmonic", gesture=simultaneous_onset(), expression_hint="comp_short"),
                event_spec(track="piano", beat=3.0, role="harmonic", gesture=simultaneous_onset(), expression_hint="comp_short"),
            ),
            tail_policy=TailPolicy.from_local_beats((1.0, 3.0)),
            beat1_movability=Beat1Movability(movable=False, reason="no_beat1_harmonic_event_in_this_cell"),
            metadata=_comping_metadata(density="dense", cell="2_4", function="backbeat_answer"),
            tags=("swing", "piano", "backbeat", "audible_v208", "comping"),
        ),
        PatternCandidate(
            name="medium_swing_piano_light_2and_only",
            weight=0.8,
            category="sparse_offbeat_answer",
            events=(
                event_spec(track="piano", beat=1.5, role="harmonic", gesture=simultaneous_onset(), expression_hint="comp_short"),
            ),
            tail_policy=TailPolicy.from_local_beats((1.5,)),
            beat1_movability=Beat1Movability(movable=False, reason="no_beat1_harmonic_event_in_this_cell"),
            metadata=_comping_metadata(density="sparse", cell="2and", function="light_offbeat_answer"),
            tags=("swing", "piano", "sparse", "audible_v208", "comping"),
        ),
    )


def _two_beat_region_candidates() -> tuple[PatternCandidate, ...]:
    return (
        PatternCandidate(
            name="medium_swing_piano_two_beat_anchor",
            weight=2.0,
            category="two_chord_bar_anchor",
            events=(
                event_spec(track="piano", beat=0.0, role="harmonic", gesture=simultaneous_onset(), expression_hint="comp_medium"),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0,)),
            beat1_movability=Beat1Movability(movable=True, reason="region_start_anchor_can_be_anticipated_later"),
            metadata=_comping_metadata(density="sparse", cell="region_start", function="two_beat_anchor", region_shape="two_beat_region"),
            tags=("swing", "piano", "two_chord_bar", "audible_v208", "comping"),
        ),
        PatternCandidate(
            name="medium_swing_piano_two_beat_offbeat_answer",
            weight=1.2,
            category="two_chord_bar_answer",
            events=(
                event_spec(track="piano", beat=0.0, role="harmonic", gesture=simultaneous_onset(), expression_hint="comp_short"),
                event_spec(track="piano", beat=1.5, role="harmonic", gesture=simultaneous_onset(), expression_hint="comp_short"),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0, 1.5)),
            beat1_movability=Beat1Movability(movable=True, reason="region_start_anchor_can_be_anticipated_later"),
            metadata=_comping_metadata(density="dense", cell="region_start_2and", function="two_beat_offbeat_answer", region_shape="two_beat_region"),
            tags=("swing", "piano", "two_chord_bar", "offbeat", "audible_v208", "comping"),
        ),
        PatternCandidate(
            name="medium_swing_piano_two_beat_push_only",
            weight=0.7,
            category="two_chord_bar_light_push",
            events=(
                event_spec(track="piano", beat=1.0, role="harmonic", gesture=simultaneous_onset(), expression_hint="comp_short"),
            ),
            tail_policy=TailPolicy.from_local_beats((1.0,)),
            beat1_movability=Beat1Movability(movable=False, reason="no_region_start_harmonic_event"),
            metadata=_comping_metadata(density="sparse", cell="beat2_push", function="two_beat_light_push", region_shape="two_beat_region"),
            tags=("swing", "piano", "two_chord_bar", "light", "audible_v208", "comping"),
        ),
    )


def get_voicing_tuning_anchor_only_candidates(context: dict | None = None) -> tuple[PatternCandidate, ...]:
    """Temporary voicing-isolation piano pattern source.

    This source intentionally emits exactly one piano harmonic event at the
    start of every harmonic region. It is used by the ``medium_swing_voicing_tuning``
    profile so voicing choices can be audited and listened to without rhythmic
    comping variation. It must not replace the normal Medium Swing comping
    vocabulary.
    """

    duration = float((context or {}).get("region_duration_beats", 4.0))
    region_shape = "two_beat_region" if duration <= 2.0 else "four_beat_region"
    return (
        PatternCandidate(
            name="medium_swing_voicing_tuning_region_start_anchor",
            weight=1.0,
            category="voicing_tuning_anchor_only",
            events=(
                event_spec(
                    track="piano",
                    beat=0.0,
                    role="harmonic",
                    gesture=simultaneous_onset(metadata={"tuning_mode": "voicing_isolation"}),
                    expression_hint="sustain",
                ),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0,)),
            beat1_movability=Beat1Movability(movable=False, reason="voicing_tuning_keeps_all_events_on_region_start"),
            metadata={
                **_comping_metadata(
                    density="voicing_isolation",
                    cell="region_start_only",
                    function="voicing_tuning_anchor",
                    region_shape=region_shape,
                ),
                "tuning_mode": "voicing_isolation",
                "normal_style_default": False,
                "purpose": "freeze_pattern_choice_to_region_start_for_voicing_audit",
            },
            tags=("swing", "piano", "voicing_tuning", "region_start", "comping"),
        ),
    )
