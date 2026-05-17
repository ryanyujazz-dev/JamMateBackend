from __future__ import annotations


def get_arrangement_policy() -> dict:
    """Medium swing arrangement-level guards.

    The policy remains style-owned, but it only declares guard preferences. The
    default StyleProfile planner applies the guards without letting style files
    emit notes, velocities, durations, or voicings.
    """

    return {
        "default_feel": "medium_swing",
        "avoid_immediate_pattern_repeat": True,
        "avoid_immediate_pattern_category_repeat": True,
        "piano_comping_density_guard": True,
        "milestone": "v2_0_12_comping_history_review",
    }
