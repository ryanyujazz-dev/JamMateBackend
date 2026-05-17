from __future__ import annotations

from jammate_engine.core.expression import (
    ArticulationKind,
    ExpressionPolicyBundle,
    ExpressionProfile,
    PedalMode,
    TouchKind,
)


def get_expression_policy() -> ExpressionPolicyBundle:
    """Jazz ballad expression policy.

    Ballad space is represented as soft sustained expression, not full-bar
    silence. Pattern still owns the onset; core expression owns sustain and
    touch behavior.
    """

    return ExpressionPolicyBundle(
        profiles={
            "soft_sustain": ExpressionProfile(
                name="soft_sustain",
                duration_beats=3.5,
                velocity=48,
                articulation=ArticulationKind.SUSTAIN,
                touch=TouchKind.WARM,
                pedal=PedalMode.SUSTAIN,
                release_beats=0.12,
                metadata={"role": "ballad_soft_sustain_anchor"},
            )
        },
        default_profile="soft_sustain",
        track_default_profiles={"piano": "soft_sustain", "bass": "soft_sustain"},
        metadata={"style": "jazz_ballad", "avoid_full_bar_silence": True},
    )
