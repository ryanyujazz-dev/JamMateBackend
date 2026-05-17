from __future__ import annotations

from typing import Any

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.pattern_runtime import Beat1Movability, PatternCandidate, TailPolicy, event_spec

STYLE_ID = "bossa_nova"
PATTERN_LIBRARY_ID = "bossa_nova.piano_comping"
PATTERN_LIBRARY_VERSION = "v2_0_42"
PATTERN_DOMAIN = "comping"
TRACK_ROLE = "piano_harmonic_comping"
DEFAULT_ONSET_MODE = "simultaneous_onset"
BOUNDARY_NOTES = (
    "pitchless",
    "style_owned",
    "identity_anchor_only_for_current_runtime",
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
    """Bossa Nova piano pattern candidates.

    The V2 foundation currently keeps only the identity anchor: core_batida
    1, 2, 3& with short-short-sustain expression hints. The hints are not final
    durations/velocities; the core ExpressionResolver owns those decisions.
    """

    duration = float((context or {}).get("region_duration_beats", 4.0))
    if duration <= 2.0:
        return (
            PatternCandidate(
                name="bossa_piano_half_region_1_2",
                weight=1.0,
                category="core_batida_half_region_adaptation",
                events=(
                    event_spec(track="piano", beat=0.0, role="harmonic", gesture=simultaneous_onset(), expression_hint="core_short"),
                    event_spec(track="piano", beat=1.0, role="harmonic", gesture=simultaneous_onset(), expression_hint="core_sustain"),
                ),
                tail_policy=TailPolicy.from_local_beats((0.0, 1.0)),
                beat1_movability=Beat1Movability(movable=True, reason="half_region_start_can_move_when_previous_tail_free"),
                metadata=_comping_metadata(
                    density="identity",
                    cell="half_region_1_2",
                    function="core_batida_harmonic_rhythm_adaptation",
                    region_shape="two_beat_region",
                ),
                tags=("bossa", "piano", "core_batida", "two_chord_bar", "comping"),
            ),
        )

    return (
        PatternCandidate(
            name="bossa_piano_core_batida_1_2_3and",
            weight=1.0,
            category="core_batida_identity_anchor",
            events=(
                event_spec(track="piano", beat=0.0, role="harmonic", gesture=simultaneous_onset(), expression_hint="core_short"),
                event_spec(track="piano", beat=1.0, role="harmonic", gesture=simultaneous_onset(), expression_hint="core_short"),
                event_spec(track="piano", beat=2.5, role="harmonic", gesture=simultaneous_onset(), expression_hint="core_sustain"),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0, 1.0, 2.5)),
            beat1_movability=Beat1Movability(movable=True, reason="core_batida_beat1_can_move_to_previous_4and_when_tail_free"),
            metadata=_comping_metadata(density="identity", cell="1_2_3and", function="core_batida_identity_anchor"),
            tags=("bossa", "piano", "core_batida", "identity_anchor", "comping"),
        ),
    )
