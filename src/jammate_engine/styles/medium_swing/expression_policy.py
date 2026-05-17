from __future__ import annotations

from jammate_engine.core.expression import (
    ArticulationKind,
    ExpressionPolicyBundle,
    ExpressionProfile,
    PedalMode,
    TouchKind,
)


def get_expression_policy() -> ExpressionPolicyBundle:
    """Medium swing performance-expression defaults.

    This file is style-owned, but it only declares expression policy. It does
    not define patterns, voicings, chord tones, or concrete MIDI events. v2_0_9
    keeps the comping profiles so the first audible swing demo has contrast
    between anchor hits, short answers, and light sustained comping.
    """

    return ExpressionPolicyBundle(
        profiles={
            "short": ExpressionProfile(
                name="short",
                duration_beats=0.55,
                velocity=62,
                articulation=ArticulationKind.SHORT,
                touch=TouchKind.CLEAR,
                pedal=PedalMode.NONE,
                release_beats=0.03,
            ),
            "sustain": ExpressionProfile(
                name="sustain",
                duration_beats=1.65,
                velocity=58,
                articulation=ArticulationKind.SUSTAIN,
                touch=TouchKind.WARM,
                pedal=PedalMode.NONE,
                release_beats=0.06,
            ),
            "comp_short": ExpressionProfile(
                name="comp_short",
                duration_beats=0.42,
                velocity=60,
                articulation=ArticulationKind.SHORT,
                touch=TouchKind.CLEAR,
                pedal=PedalMode.NONE,
                release_beats=0.03,
                metadata={"purpose": "short swing comp answer"},
            ),
            "comp_medium": ExpressionProfile(
                name="comp_medium",
                duration_beats=0.85,
                velocity=61,
                articulation=ArticulationKind.SHORT,
                touch=TouchKind.CLEAR,
                pedal=PedalMode.NONE,
                release_beats=0.04,
                metadata={"purpose": "medium swing chordal anchor"},
            ),
            "comp_accent": ExpressionProfile(
                name="comp_accent",
                duration_beats=0.62,
                velocity=66,
                articulation=ArticulationKind.ACCENT,
                touch=TouchKind.ACCENTED,
                pedal=PedalMode.NONE,
                release_beats=0.03,
                accent=0.25,
                metadata={"purpose": "clear Charleston-style anchor"},
            ),

            "bass_foundation_root_echo": ExpressionProfile(
                name="bass_foundation_root_echo",
                duration_beats=0.55,
                velocity=62,
                articulation=ArticulationKind.SHORT,
                touch=TouchKind.CLEAR,
                pedal=PedalMode.NONE,
                release_beats=0.03,
                metadata={"purpose": "current-root upbeat echo ornament after BassFoundation walking"},
            ),
            "bass_foundation_classic_fill": ExpressionProfile(
                name="bass_foundation_classic_fill",
                duration_beats=0.88,
                velocity=70,
                articulation=ArticulationKind.SUSTAIN,
                touch=TouchKind.WARM,
                pedal=PedalMode.NONE,
                release_beats=0.04,
                metadata={"purpose": "scene-triggered classic BassFoundation fill body"},
            ),
            "bass_foundation_classic_fill_upbeat": ExpressionProfile(
                name="bass_foundation_classic_fill_upbeat",
                duration_beats=0.48,
                velocity=62,
                articulation=ArticulationKind.SHORT,
                touch=TouchKind.CLEAR,
                pedal=PedalMode.NONE,
                release_beats=0.03,
                metadata={"purpose": "classic BassFoundation fill upbeat note"},
            ),
        },
        default_profile="comp_short",
        track_default_profiles={"piano": "comp_short", "bass": "sustain", "drums": "short"},
        metadata={"style": "medium_swing", "milestone": "v2_0_20_swing_timing_grid_resolver"},
    )
