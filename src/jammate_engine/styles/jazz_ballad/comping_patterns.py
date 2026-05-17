from __future__ import annotations

from typing import Any

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.pattern_runtime import Beat1Movability, PatternCandidate, TailPolicy, event_spec

STYLE_ID = "jazz_ballad"
PATTERN_LIBRARY_ID = "jazz_ballad.piano_comping"
PATTERN_LIBRARY_VERSION = "v2_0_42"
PATTERN_DOMAIN = "comping"
TRACK_ROLE = "piano_harmonic_comping"
DEFAULT_ONSET_MODE = "simultaneous_onset"
BOUNDARY_NOTES = (
    "pitchless",
    "style_owned",
    "minimum_harmonic_touch",
    "no_voicing_logic",
    "no_final_expression_values",
)


def _comping_metadata(*, density: str, cell: str, function: str) -> dict[str, Any]:
    return {
        "density": density,
        "style_id": STYLE_ID,
        "pattern_domain": PATTERN_DOMAIN,
        "pattern_library_id": PATTERN_LIBRARY_ID,
        "pattern_library_version": PATTERN_LIBRARY_VERSION,
        "track_role": TRACK_ROLE,
        "region_shape": "four_beat_region",
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
    """Jazz ballad piano pattern candidates.

    The V2 foundation preserves the minimal every-region harmonic touch so ballad does not
    become full-bar silence by default.
    """

    return (
        PatternCandidate(
            name="ballad_piano_soft_downbeat_sustain",
            weight=1.0,
            category="soft_sustain_anchor",
            events=(
                event_spec(track="piano", beat=0.0, role="harmonic", gesture=simultaneous_onset(), expression_hint="soft_sustain"),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0,)),
            beat1_movability=Beat1Movability(movable=True, reason="ballad_downbeat_touch_can_be_anticipated_when_previous_tail_free"),
            metadata=_comping_metadata(density="sparse", cell="1", function="minimum_harmonic_touch"),
            tags=("ballad", "piano", "sustain", "comping"),
        ),
    )
