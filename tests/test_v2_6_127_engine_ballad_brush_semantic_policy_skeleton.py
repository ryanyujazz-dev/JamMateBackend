from __future__ import annotations

# harness token: test_v2_6_127_engine_ballad_brush_semantic_policy_skeleton

import json
from jammate_engine.styles.jazz_ballad import arrangement_policy, percussion_patterns


def _active_context(**kwargs):
    return {**kwargs, "jazz_ballad_brush_sound_source_time_feel_active": True}


def test_v2_6_127_ballad_percussion_remains_silent_by_default() -> None:
    # Current contract: the old bare semantic skeleton still does not emit a
    # candidate unless normal generation/runtime context or the current brush
    # sound-source flag opts in.
    candidates = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    assert candidates == ()


def test_v2_6_127_arrangement_policy_declares_current_brush_contract() -> None:
    policy = arrangement_policy.get_arrangement_policy()
    assert policy["default_feel"] == "jazz_ballad"
    assert policy["avoid_full_bar_silence"] is True
    assert policy["jazz_ballad_brush_semantic_policy_active"] is True
    assert policy["jazz_ballad_brush_semantic_policy_version"] == "v2_6_127"
    assert policy["jazz_ballad_brush_sound_source_time_feel_active"] is True
    assert policy["jazz_ballad_brush_sound_source_time_feel_version"] == "v2_6_137"
    assert policy["jazz_ballad_drum_not_chord_region_loop"] is True
    assert policy["jazz_ballad_no_custom_internal_brush_voices"] is True
    assert policy["jazz_ballad_brush_timbre_delegated_to_sound_source"] is True
    assert policy["jazz_ballad_brush_semantic_policy_no_swing_ride"] is True
    assert policy["jazz_ballad_brush_semantic_policy_no_rock_backbeat"] is True


def test_v2_6_127_brush_semantic_dimensions_are_now_bar_level_sound_source_intent() -> None:
    decision = percussion_patterns.build_brush_semantic_policy_decision(
        {
            "region_duration_beats": 4.0,
            "region_source_bar_index": 4,
            "region_chorus_index": 1,
            "region_total_choruses": 3,
            "energy": "medium",
        }
    )

    assert decision["jazz_ballad_brush_semantic_policy_version"] == "v2_6_127"
    assert decision["jazz_ballad_brush_sound_source_time_feel_version"] == "v2_6_137"
    assert decision["jazz_ballad_drum_planning_scope"] == "bar_level_brush_time_feel_with_region_projection"
    assert decision["jazz_ballad_drum_not_chord_region_loop"] is True
    assert decision["jazz_ballad_no_custom_internal_brush_voices"] is True
    assert decision["jazz_ballad_brush_timbre_delegated_to_sound_source"] is True
    assert decision["brush_motion_points"] == ("1", "1&", "2", "2&", "3", "3&", "4", "4&")
    assert decision["brush_time_anchor_intent"] == "hat_2_4_soft"
    assert decision["brush_kick_policy_intent"] == "one_three_feather"
    assert decision["brush_density_band"] == "low"
    assert decision["brush_classic_fill_cell"] == "bridge_entry_low_tom_bloom_hint"
    assert decision["brush_no_swing_ride"] is True
    assert decision["brush_no_rock_backbeat"] is True
    debug_text = json.dumps(decision, ensure_ascii=False)
    assert "midi_note" not in debug_text
    assert "velocity" not in debug_text


def test_v2_6_127_brush_phrase_context_classifies_tail_and_final_release_under_current_contract() -> None:
    phrase_tail = percussion_patterns.build_brush_semantic_policy_decision(
        {
            "region_duration_beats": 4.0,
            "region_source_bar_index": 7,
            "region_chorus_index": 0,
            "region_total_choruses": 3,
        }
    )
    assert phrase_tail["brush_feel_cell"] == "phrase_breath_release"
    assert phrase_tail["brush_time_anchor_intent"] == "hat_4_only"
    assert phrase_tail["brush_kick_policy_intent"] == "none"
    assert phrase_tail["brush_classic_fill_cell"] == "v1_soft_swish_4and_hint"
    assert phrase_tail["brush_density_band"] == "very_low"
    assert phrase_tail["brush_phrase_context"]["phrase_tail"] is True

    final = percussion_patterns.build_brush_semantic_policy_decision(
        {
            "region_duration_beats": 4.0,
            "region_source_bar_index": 31,
            "region_chorus_index": 2,
            "region_total_choruses": 3,
            "region_is_last_bar_of_chorus": True,
        }
    )
    assert final["brush_feel_cell"] == "final_release"
    assert final["brush_time_anchor_intent"] == "none"
    assert final["brush_kick_policy_intent"] == "none"
    assert final["brush_classic_fill_cell"] == "final_brush_release"
    assert final["brush_phrase_context"]["final_release"] is True


def test_v2_6_127_static_skeleton_can_be_consumed_by_current_sound_source_candidate_opt_in() -> None:
    assert percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0}) == ()
    candidates = percussion_patterns.get_pattern_candidates(
        _active_context(
            region_duration_beats=4.0,
            region_source_bar_index=4,
            region_chorus_index=0,
            region_total_choruses=3,
        )
    )
    assert len(candidates) == 1
    assert candidates[0].category == "jazz_ballad_bar_level_brush_sound_source_time_feel"
    assert candidates[0].metadata["jazz_ballad_brush_sound_source_time_feel_version"] == "v2_6_137"
    assert candidates[0].metadata["pattern_library_version"] == "v2_6_137"
