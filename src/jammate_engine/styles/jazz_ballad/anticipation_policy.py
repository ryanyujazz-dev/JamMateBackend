from __future__ import annotations

from jammate_engine.core.anticipation import AnticipationPolicy


def get_anticipation_policy() -> AnticipationPolicy:
    return AnticipationPolicy(
        enabled=True,
        probability=0.12,
        target_offset_beats=-0.5,
        timing_grid="straight_upbeat",
        target_timing_intent="straight_even",
        performed_lead_in_beats=0.5,
        expected_upbeat_fraction=0.5,
        eligible_tracks=("piano",),
        eligible_roles=("harmonic",),
        require_previous_tail_space=True,
        require_previous_last_beat_empty=True,
        require_previous_last_upbeat_empty=True,
        suppress_original=True,
        tie_from_previous=True,
        debug_name="ballad_gentle_4and_anticipation",
        metadata={"style": "jazz_ballad", "purpose": "occasional_soft_approach"},
    )
