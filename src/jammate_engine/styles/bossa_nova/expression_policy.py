from __future__ import annotations

from jammate_engine.core.expression import (
    ArticulationKind,
    ExpressionPolicyBundle,
    ExpressionProfile,
    PedalMode,
    TouchKind,
)


def get_expression_policy() -> ExpressionPolicyBundle:
    """Bossa Nova expression policy.

    The core batida identity remains short-short-sustain through named
    expression profiles referenced by the bossa piano pattern library.
    """

    return ExpressionPolicyBundle(
        profiles={
            "core_short": ExpressionProfile(
                name="core_short",
                duration_beats=0.45,
                velocity=56,
                articulation=ArticulationKind.SHORT,
                touch=TouchKind.CLEAR,
                pedal=PedalMode.NONE,
                release_beats=0.03,
                metadata={"role": "bossa_core_batida_short"},
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
        },
        default_profile="core_short",
        track_default_profiles={"piano": "core_short", "bass": "core_sustain", "drums": "core_short"},
        metadata={"style": "bossa_nova"},
    )
