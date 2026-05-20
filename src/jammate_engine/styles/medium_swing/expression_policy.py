from __future__ import annotations

from jammate_engine.core.expression import (
    ArticulationKind,
    ExpressionPolicyBundle,
    ExpressionProfile,
    PedalMode,
    TouchKind,
)

MEDIUM_SWING_EXPRESSION_POLICY_VERSION = "v2_6_68"
V1_REFERENCE_TICKS_PER_BEAT = 120


def _v1_reference(
    semantic_hint: str,
    *,
    velocity_range: tuple[int, int],
    duration_ticks_range: tuple[int, int],
    usage: str,
    resolved_as: str,
) -> dict:
    low, high = duration_ticks_range
    return {
        "medium_swing_expression_policy_v1_numeric_calibration_version": MEDIUM_SWING_EXPRESSION_POLICY_VERSION,
        "v1_reference_semantic_hint": semantic_hint,
        "v1_reference_velocity_range": tuple(velocity_range),
        "v1_reference_duration_ticks_range": tuple(duration_ticks_range),
        "v1_reference_ticks_per_beat": V1_REFERENCE_TICKS_PER_BEAT,
        "v1_reference_duration_beats_range": (round(low / V1_REFERENCE_TICKS_PER_BEAT, 6), round(high / V1_REFERENCE_TICKS_PER_BEAT, 6)),
        "v1_reference_usage": usage,
        "v2_resolution_owner": resolved_as,
        "calibration_contract": "Profile values are V1-informed expression defaults; pattern events still carry only semantic hints and never final velocity/duration/pedal values.",
    }


def _hold_reference(
    semantic_hint: str,
    *,
    velocity_range: tuple[int, int],
    duration_ticks_range: tuple[int, int],
    usage: str,
) -> dict:
    return {
        **_v1_reference(
            semantic_hint,
            velocity_range=velocity_range,
            duration_ticks_range=duration_ticks_range,
            usage=usage,
            resolved_as="ExpressionResolver hold_until_next_touch clamped to current ChordRegion boundary",
        ),
        "duration_semantics": "hold_until_next_touch",
        "duration_semantics_version": "v2_6_63",
        "duration_boundary_guard_version": "v2_6_66",
    }


def get_expression_policy() -> ExpressionPolicyBundle:
    """Medium swing performance-expression defaults.

    This file is style-owned, but it only declares expression policy. It does
    not define patterns, voicings, chord tones, or concrete MIDI events. v2_6_68
    calibrates the piano comping profile values against the V1 touch ranges while
    preserving V2 separation: pattern emits semantic hints only; this policy maps
    those hints to expression defaults; the core resolver still applies region
    boundary and next-touch guards.
    """

    soft_hold_ref = _hold_reference(
        "soft_hold",
        velocity_range=(48, 59),
        duration_ticks_range=(84, 140),
        usage="main support, beat-1/3 anchors, cadence release",
    )
    light_stab_ref = _v1_reference(
        "light_stab",
        velocity_range=(48, 65),
        duration_ticks_range=(62, 88),
        usage="Charleston answer and light offbeat response",
        resolved_as="fixed short profile, region/next-event clamped by core resolver when needed",
    )
    accent_stab_ref = _v1_reference(
        "accent_stab",
        velocity_range=(60, 70),
        duration_ticks_range=(58, 72),
        usage="push, 4& pickup, dominant approach, busy fill",
        resolved_as="fixed accented short profile, dry release",
    )
    backbeat_hold_ref = _hold_reference(
        "backbeat_hold",
        velocity_range=(51, 64),
        duration_ticks_range=(76, 108),
        usage="2&/3& support, longer than stab",
    )
    final_hold_ref = _hold_reference(
        "final_hold",
        velocity_range=(44, 45),
        duration_ticks_range=(220, 240),
        usage="ending final sustain",
    )
    accent_hold_ref = {
        **backbeat_hold_ref,
        "v1_reference_semantic_hint": "accent_hold_from_accent_stab_plus_hold_semantics",
        "v1_reference_velocity_range": (60, 70),
        "v1_reference_duration_ticks_range": (76, 108),
        "v1_reference_duration_beats_range": (round(76 / V1_REFERENCE_TICKS_PER_BEAT, 6), round(108 / V1_REFERENCE_TICKS_PER_BEAT, 6)),
        "v1_reference_usage": "accented anchor held until next comping touch; V2-specific combination of accent_stab velocity and backbeat/soft hold duration semantics",
    }

    return ExpressionPolicyBundle(
        profiles={
            "short": ExpressionProfile(
                name="short",
                duration_beats=0.55,
                velocity=56,
                articulation=ArticulationKind.SHORT,
                touch=TouchKind.CLEAR,
                pedal=PedalMode.NONE,
                release_beats=0.025,
                metadata={**light_stab_ref, "purpose": "generic short swing touch aligned to light_stab reference"},
            ),
            "sustain": ExpressionProfile(
                name="sustain",
                duration_beats=0.95,
                velocity=54,
                articulation=ArticulationKind.SUSTAIN,
                touch=TouchKind.WARM,
                pedal=PedalMode.NONE,
                release_beats=0.045,
                metadata={**soft_hold_ref, "purpose": "generic medium swing sustain aligned to soft_hold reference"},
            ),
            "comp_short": ExpressionProfile(
                name="comp_short",
                duration_beats=0.62,
                velocity=56,
                articulation=ArticulationKind.SHORT,
                touch=TouchKind.CLEAR,
                pedal=PedalMode.NONE,
                release_beats=0.025,
                metadata={**light_stab_ref, "purpose": "short swing comp answer"},
            ),
            "comp_medium": ExpressionProfile(
                name="comp_medium",
                duration_beats=0.95,
                velocity=54,
                articulation=ArticulationKind.SUSTAIN,
                touch=TouchKind.CLEAR,
                pedal=PedalMode.NONE,
                release_beats=0.045,
                metadata={
                    **soft_hold_ref,
                    "purpose": "medium swing chordal anchor",
                    "semantic_expression_hint": "soft_hold",
                },
            ),
            "comp_backbeat_hold": ExpressionProfile(
                name="comp_backbeat_hold",
                duration_beats=0.78,
                velocity=58,
                articulation=ArticulationKind.SUSTAIN,
                touch=TouchKind.CLEAR,
                pedal=PedalMode.NONE,
                release_beats=0.03,
                metadata={
                    **backbeat_hold_ref,
                    "purpose": "medium swing backbeat/tail hold",
                    "semantic_expression_hint": "backbeat_hold",
                },
            ),
            "comp_accent_hold": ExpressionProfile(
                name="comp_accent_hold",
                duration_beats=0.78,
                velocity=64,
                articulation=ArticulationKind.ACCENT,
                touch=TouchKind.ACCENTED,
                pedal=PedalMode.NONE,
                release_beats=0.03,
                accent=0.22,
                metadata={
                    **accent_hold_ref,
                    "purpose": "accented medium swing anchor held until next touch",
                    "semantic_expression_hint": "accent_hold",
                },
            ),
            "comp_final_hold": ExpressionProfile(
                name="comp_final_hold",
                duration_beats=1.92,
                velocity=45,
                articulation=ArticulationKind.SUSTAIN,
                touch=TouchKind.WARM,
                pedal=PedalMode.NONE,
                release_beats=0.055,
                metadata={
                    **final_hold_ref,
                    "purpose": "medium swing final/release hold",
                    "semantic_expression_hint": "final_hold",
                },
            ),
            "comp_accent": ExpressionProfile(
                name="comp_accent",
                duration_beats=0.54,
                velocity=66,
                articulation=ArticulationKind.ACCENT,
                touch=TouchKind.ACCENTED,
                pedal=PedalMode.NONE,
                release_beats=0.025,
                accent=0.22,
                metadata={**accent_stab_ref, "purpose": "clear Charleston-style anchor or rare push"},
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
        metadata={
            "style": "medium_swing",
            "milestone": "v2_6_68_medium_swing_expression_policy_v1_numeric_calibration",
            "piano_expression_hint_handoff_version": "v2_6_63",
            "hold_duration_semantics": "hold_until_next_touch",
            "medium_swing_expression_policy_v1_numeric_calibration": True,
            "medium_swing_expression_policy_v1_numeric_calibration_version": MEDIUM_SWING_EXPRESSION_POLICY_VERSION,
            "medium_swing_expression_policy_v1_reference_ticks_per_beat": V1_REFERENCE_TICKS_PER_BEAT,
            "medium_swing_expression_policy_v1_numeric_calibration_contract": "V1 numeric ranges calibrate style-owned ExpressionProfile defaults only; patterns keep semantic_expression_hint metadata and never write velocity/duration/pedal.",
        },
    )
