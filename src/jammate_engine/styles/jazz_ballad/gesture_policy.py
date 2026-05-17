from __future__ import annotations

STYLE_ID = "jazz_ballad"
GESTURE_POLICY_VERSION = "v2_0_42"


def get_gesture_policy() -> dict:
    """Pitchless gesture policy for Jazz Ballad comping."""

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
            "motion_group",
        ),
        "boundary": "gesture_policy_is_pitchless_and_projection_only",
    }
