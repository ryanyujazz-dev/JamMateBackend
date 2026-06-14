from __future__ import annotations

from .percussion_patterns import (
    JAZZ_BALLAD_BRUSH_SEMANTIC_POLICY_VERSION,
    JAZZ_BALLAD_BRUSH_SOUND_SOURCE_TIME_FEEL_VERSION,
    JAZZ_BALLAD_BRUSH_SECTION_HINT_VERSION,
)


def get_arrangement_policy() -> dict:
    """Return Jazz Ballad style-level arrangement defaults.

    v2_6_137 keeps Ballad percussion on the shared swing-8 timing contract while turning classic brush fills into quieter phrase/section transition hints with expanded vocabulary on top of the real brush-sound-source
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
            "section_tail_4and_hint",
            "section_tail_4and_whisper",
            "section_tail_3and_4and_feather_hint",
            "v1_soft_swish_4and_hint",
            "v1_section_breath_4_to_4and_hint",
            "section_entry_brush_bloom",
            "section_entry_1and_bloom_hint",
            "section_entry_soft_1_to_1and_hint",
            "cadence_3and_4_hint",
            "cadence_3and_4and_whisper",
            "cadence_4_hat_brush_hint",
            "cadence_3_to_4_tom_hat_hint",
            "v1_drag_to_4_hint",
            "turnaround_soft_2and_4and_hint",
            "turnaround_2and_3and_4and_whisper",
            "turnaround_2and_4_hat_hint",
            "turnaround_cross_stick_4_hint",
            "bridge_entry_soft_1_2and_hint",
            "bridge_entry_low_tom_bloom_hint",
            "section_tail_4_hat_cymbal_hint",
            "final_brush_release",
        ),
        "jazz_ballad_classic_brush_fill_audibility_rework_active": True,
        "jazz_ballad_classic_brush_fill_audibility_contract": "section_transition_hint_lane_without_background_duck",
        "jazz_ballad_transition_hint_vocabulary_expanded": True,
        "jazz_ballad_transition_hint_dynamic_contract": "subtle_hint_overlay_not_foreground_fill",
        "jazz_ballad_transition_hint_v1_reference_primitives": (
            "brush_drag_to_4",
            "section_breath",
            "soft_swish_4and",
            "final_release",
        ),
        "jazz_ballad_brush_section_transition_hint_active": True,
        "jazz_ballad_brush_section_transition_hint_version": JAZZ_BALLAD_BRUSH_SECTION_HINT_VERSION,
        "recommended_next_task": "v2_6_138_engine_ballad_hint_timbre_and_offbeat_density_listening_calibration",
    }
