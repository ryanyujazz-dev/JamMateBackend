from __future__ import annotations

from jammate_engine.core.anticipation import AnticipationPolicy


def get_anticipation_policy() -> AnticipationPolicy:
    return AnticipationPolicy(
        enabled=True,
        probability=0.10,
        target_offset_beats=-0.5,
        timing_grid="swing_triplet_upbeat",
        target_timing_intent="swing_upbeat",
        performed_lead_in_beats=1.0 / 3.0,
        expected_upbeat_fraction=2.0 / 3.0,
        eligible_tracks=("piano",),
        eligible_roles=("harmonic",),
        require_previous_tail_space=True,
        require_previous_last_beat_empty=True,
        require_previous_last_upbeat_empty=True,
        suppress_original=True,
        tie_from_previous=True,
        debug_name="medium_swing_light_region_tail_push",
        metadata={
            "style": "medium_swing",
            "purpose": "rare_comping_push",
            "region_first_anticipation_compatibility_checkpoint_version": "v2_6_61",
            "region_first_anticipation_contract": "Medium Swing anticipation moves the next region-start harmonic event to the previous ChordRegion tail slot, computed from previous_region.duration_beats - 0.5; this is local 4& only for a 4-beat region and local 2& for a 2-beat region.",
            "no_bar_first_4and_assumption": True,
        },
    )
