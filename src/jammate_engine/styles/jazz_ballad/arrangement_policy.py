from __future__ import annotations

from .percussion_patterns import (
    JAZZ_BALLAD_BRUSH_SEMANTIC_POLICY_VERSION,
    JAZZ_BALLAD_BRUSH_SOUND_SOURCE_TIME_FEEL_VERSION,
)


def get_arrangement_policy() -> dict:
    """Return Jazz Ballad style-level arrangement defaults.

    v2_6_133 keeps Ballad percussion on the shared swing-8 timing contract while adding phrase-level classic brush fill overlays on top of the real brush-sound-source
    assumption: the style owns bar-level brush swing time feel, offbeat brush
    motion, soft 2/4 anchors, feather kick, and phrase breath.  It does not
    create custom internal brush drum voices and it does not restart a complete
    drum loop for every chord region.
    """

    return {
        "default_feel": "jazz_ballad",
        "avoid_full_bar_silence": True,
        "jazz_ballad_brush_semantic_policy_active": True,
        "jazz_ballad_brush_semantic_policy_version": JAZZ_BALLAD_BRUSH_SEMANTIC_POLICY_VERSION,
        "jazz_ballad_brush_sound_source_time_feel_active": True,
        "jazz_ballad_brush_sound_source_time_feel_version": JAZZ_BALLAD_BRUSH_SOUND_SOURCE_TIME_FEEL_VERSION,
        "jazz_ballad_brush_sound_source_assumed": True,
        "jazz_ballad_drum_planning_scope": "bar_level_brush_time_feel_with_region_projection",
        "jazz_ballad_drum_not_chord_region_loop": True,
        "jazz_ballad_no_custom_internal_brush_voices": True,
        "jazz_ballad_brush_timbre_delegated_to_sound_source": True,
        "jazz_ballad_brush_offbeat_policy_active": True,
        "jazz_ballad_brush_motion_points": ("1", "1&", "2", "2&", "3", "3&", "4", "4&"),
        "jazz_ballad_brush_semantic_policy_no_fixed_loop": True,
        "jazz_ballad_brush_semantic_policy_no_swing_ride": True,
        "jazz_ballad_brush_semantic_policy_no_rock_backbeat": True,
        "jazz_ballad_classic_brush_fill_policy_active": True,
        "jazz_ballad_classic_brush_fill_policy_version": JAZZ_BALLAD_BRUSH_SOUND_SOURCE_TIME_FEEL_VERSION,
        "jazz_ballad_classic_brush_fill_cells": (
            "soft_pickup_to_4",
            "tap_drag_tap_release",
            "single_stroke_4_to_next",
            "turnaround_sweep_roll",
            "final_brush_release",
        ),
        "recommended_next_task": "v2_6_134_engine_ballad_brush_fill_listening_calibration",
    }
