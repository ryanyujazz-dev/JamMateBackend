from __future__ import annotations

from jammate_engine.core.expression import (
    ArticulationKind,
    ExpressionPolicyBundle,
    ExpressionProfile,
    PedalMode,
    TouchKind,
)


BOSSA_DISTANCE_AWARE_EXPRESSION_VERSION = "v2_6_94"
BOSSA_CORE_BATIDA_FRONT_VELOCITY_CALIBRATION_VERSION = "v2_6_122"


def get_expression_policy() -> ExpressionPolicyBundle:
    """Bossa Nova expression policy.

    The core batida identity remains short-short-sustain through named
    expression profiles referenced by the Bossa piano pattern library. v2_6_94
    replaces the earlier v2_6_91 alias-only non-core cell touch with
    policy-driven distance articulation consumed by the shared core
    ExpressionResolver after anticipation has rewritten the pitchless timeline.
    """

    return ExpressionPolicyBundle(
        profiles={
            "core_short": ExpressionProfile(
                name="core_short",
                duration_beats=0.45,
                velocity=48,
                articulation=ArticulationKind.SHORT,
                touch=TouchKind.CLEAR,
                pedal=PedalMode.NONE,
                release_beats=0.03,
                metadata={
                    "role": "bossa_core_batida_short",
                    "bossa_core_batida_front_velocity_calibration_version": BOSSA_CORE_BATIDA_FRONT_VELOCITY_CALIBRATION_VERSION,
                    "core_batida_front_two_hits_velocity": 48,
                },
            ),
            "core_sustain": ExpressionProfile(
                name="core_sustain",
                duration_beats=1.3,
                velocity=52,
                articulation=ArticulationKind.SUSTAIN,
                touch=TouchKind.LIGHT,
                pedal=PedalMode.LIGHT,
                release_beats=0.08,
                metadata={"role": "bossa_core_batida_sustain"},
            ),
            "cell_close_gap_short": ExpressionProfile(
                name="cell_close_gap_short",
                duration_beats=0.42,
                velocity=47,
                articulation=ArticulationKind.SHORT,
                touch=TouchKind.LIGHT,
                pedal=PedalMode.NONE,
                release_beats=0.025,
                metadata={
                    "role": "bossa_non_core_close_gap_short",
                    "bossa_distance_aware_expression_version": BOSSA_DISTANCE_AWARE_EXPRESSION_VERSION,
                    "bossa_non_core_expression_alias_version": "v2_6_91",
                    "numeric_source_profile": "core_short",
                    "distance_articulation": "short_if_close_else_sustain",
                    "distance_threshold_beats": 1.0,
                    "distance_short_duration_beats": 0.42,
                    "distance_short_velocity": 47,
                    "distance_short_articulation": "short",
                    "distance_short_touch": "light",
                    "distance_short_pedal": "none",
                    "distance_short_release_beats": 0.025,
                    "distance_sustain_duration_beats": 1.18,
                    "distance_sustain_velocity": 46,
                    "distance_sustain_articulation": "sustain",
                    "distance_sustain_touch": "warm",
                    "distance_sustain_pedal": "light",
                    "distance_sustain_release_beats": 0.06,
                    "expression_policy_contract": "Bossa non-core cell articulation is resolved from final event distance after anticipation; the pattern supplies only semantic hints.",
                },
            ),
            "cell_soft_hold": ExpressionProfile(
                name="cell_soft_hold",
                duration_beats=1.18,
                velocity=46,
                articulation=ArticulationKind.SUSTAIN,
                touch=TouchKind.WARM,
                pedal=PedalMode.LIGHT,
                release_beats=0.06,
                metadata={
                    "role": "bossa_non_core_distance_sensitive_hold",
                    "bossa_distance_aware_expression_version": BOSSA_DISTANCE_AWARE_EXPRESSION_VERSION,
                    "bossa_non_core_expression_alias_version": "v2_6_91",
                    "numeric_source_profile": "core_sustain",
                    "distance_articulation": "short_if_close_else_sustain",
                    "distance_threshold_beats": 1.0,
                    "distance_short_duration_beats": 0.42,
                    "distance_short_velocity": 47,
                    "distance_short_articulation": "short",
                    "distance_short_touch": "light",
                    "distance_short_pedal": "none",
                    "distance_short_release_beats": 0.025,
                    "distance_sustain_duration_beats": 1.18,
                    "distance_sustain_velocity": 46,
                    "distance_sustain_articulation": "sustain",
                    "distance_sustain_touch": "warm",
                    "distance_sustain_pedal": "light",
                    "distance_sustain_release_beats": 0.06,
                    "expression_policy_contract": "Bossa non-core cell articulation is resolved from final event distance after anticipation; the pattern supplies only semantic hints.",
                },
            ),
            "anticipation_light": ExpressionProfile(
                name="anticipation_light",
                duration_beats=0.88,
                velocity=44,
                articulation=ArticulationKind.SUSTAIN,
                touch=TouchKind.LIGHT,
                pedal=PedalMode.NONE,
                release_beats=0.035,
                metadata={
                    "role": "bossa_light_barline_anticipation",
                    "bossa_distance_aware_expression_version": BOSSA_DISTANCE_AWARE_EXPRESSION_VERSION,
                    "expression_policy_contract": "Anticipation stays dry and light; AnticipationResolver owns timing movement, ExpressionResolver owns release.",
                },
            ),
            "dense_light_mark": ExpressionProfile(
                name="dense_light_mark",
                duration_beats=0.72,
                velocity=43,
                articulation=ArticulationKind.SUSTAIN,
                touch=TouchKind.LIGHT,
                pedal=PedalMode.NONE,
                release_beats=0.035,
                metadata={
                    "role": "bossa_dense_harmonic_light_mark",
                    "bossa_distance_aware_expression_version": BOSSA_DISTANCE_AWARE_EXPRESSION_VERSION,
                    "expression_policy_contract": "Dense harmonic marks stay light and region-clamped; pattern remains pitchless.",
                },
            ),
            "release_soft": ExpressionProfile(
                name="release_soft",
                duration_beats=1.45,
                velocity=43,
                articulation=ArticulationKind.SUSTAIN,
                touch=TouchKind.WARM,
                pedal=PedalMode.LIGHT,
                release_beats=0.075,
                metadata={
                    "role": "bossa_soft_release",
                    "bossa_distance_aware_expression_version": BOSSA_DISTANCE_AWARE_EXPRESSION_VERSION,
                    "expression_policy_contract": "Soft Bossa release is style expression only and does not alter pattern/voicing logic.",
                },
            ),
        },
        default_profile="core_short",
        track_default_profiles={"piano": "core_short", "bass": "core_sustain", "drums": "core_short"},
        metadata={
            "style": "bossa_nova",
            "bossa_distance_aware_expression_active": True,
            "bossa_distance_aware_expression_version": BOSSA_DISTANCE_AWARE_EXPRESSION_VERSION,
            "bossa_distance_aware_expression_no_parallel_resolver": True,
            "bossa_distance_aware_expression_contract": "Style policy declares Bossa distance articulation profiles; shared core ExpressionResolver applies them after anticipation and clamps durations to next event / ChordRegion boundaries.",
        },
    )
