from __future__ import annotations

from jammate_engine.core.anticipation import AnticipationPolicy


BOSSA_NOVA_ANTICIPATION_TAIL_POLICY_VERSION = "v2_6_93"


def get_anticipation_policy() -> AnticipationPolicy:
    return AnticipationPolicy(
        enabled=True,
        probability=0.30,
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
        min_previous_region_duration_beats=3.75,
        suppress_original=True,
        tie_from_previous=True,
        debug_name="bossa_next_bar_beat1_to_previous_4and_when_tail_free",
        metadata={
            "style": "bossa_nova",
            "purpose": "subtle_crossbar_syncopation",
            "bossa_nova_anticipation_tail_policy_active": True,
            "bossa_nova_anticipation_tail_policy_version": BOSSA_NOVA_ANTICIPATION_TAIL_POLICY_VERSION,
            "bossa_nova_anticipation_tail_policy_milestone": "v2_6_93_engine_bossa_nova_anticipation_tail_policy_and_native_4and_audit",
            "requires_previous_beat4_empty": True,
            "requires_previous_4and_empty": True,
            "preserve_native_4and_current_chord_events": True,
            "native_4and_is_not_anticipation_slot": True,
            "min_previous_region_duration_beats": 3.75,
            "no_parallel_anticipation_engine": True,
            "no_pattern_embedded_anticipation": True,
            "no_bar_first_pattern_restore": True,
            "contract": (
                "Bossa anticipation uses the shared pitchless AnticipationResolver. It may move a next-region beat-1 harmonic event "
                "to the previous full-region 4& only when the previous region tail has no eligible piano harmonic event on beat 4 or 4&. "
                "Native 4& cells remain current-chord events and therefore occupy the 4& tail slot rather than being overwritten."
            ),
        },
    )
