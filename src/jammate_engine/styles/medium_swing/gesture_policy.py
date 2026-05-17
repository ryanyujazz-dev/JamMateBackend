from __future__ import annotations

STYLE_ID = "medium_swing"
GESTURE_POLICY_VERSION = "v2_0_42"


def get_gesture_policy() -> dict:
    """Pitchless gesture policy for Medium Swing comping.

    This policy declares which abstract gesture/projection contracts the style
    currently uses. It does not choose pitches, voicings, durations, velocities,
    or pedal values.
    """

    return {
        "style_id": STYLE_ID,
        "version": GESTURE_POLICY_VERSION,
        "default_onset_mode": "simultaneous_onset",
        "allowed_gesture_kinds": ("simultaneous_onset",),
        "allowed_projection_refs": (
            "all_voices",
            "lowest",
            "inner",
            "inner_1",
            "inner_2",
            "top",
            "support_group",
            "foundation_group",
            "projection_group",
            "color_group",
        ),
        "boundary": "gesture_policy_is_pitchless_and_projection_only",
    }
