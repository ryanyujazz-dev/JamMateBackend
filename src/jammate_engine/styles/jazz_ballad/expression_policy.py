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
    silence. v2_5_0 adds lighter re-touch / answer profiles so pattern cells can
    add motion without turning into hard stabs or Agent/LLM-specific behavior.
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
            ),
            "soft_retouch": ExpressionProfile(
                name="soft_retouch",
                duration_beats=1.35,
                velocity=43,
                articulation=ArticulationKind.SUSTAIN,
                touch=TouchKind.LIGHT,
                pedal=PedalMode.LIGHT,
                release_beats=0.08,
                metadata={"role": "ballad_light_retouch"},
            ),
            "soft_answer": ExpressionProfile(
                name="soft_answer",
                duration_beats=1.05,
                velocity=42,
                articulation=ArticulationKind.SUSTAIN,
                touch=TouchKind.LIGHT,
                pedal=PedalMode.LIGHT,
                release_beats=0.07,
                metadata={"role": "ballad_soft_answer"},
            ),
            "soft_whisper": ExpressionProfile(
                name="soft_whisper",
                duration_beats=1.0,
                velocity=39,
                articulation=ArticulationKind.SUSTAIN,
                touch=TouchKind.LIGHT,
                pedal=PedalMode.LIGHT,
                release_beats=0.07,
                metadata={"role": "ballad_near_downbeat_sustained_whisper"},
            ),
        },
        default_profile="soft_sustain",
        track_default_profiles={"piano": "soft_sustain", "bass": "soft_sustain"},
        metadata={"style": "jazz_ballad", "avoid_full_bar_silence": True, "music_pass": "v2_5_0_ballad_comping_motion"},
    )
