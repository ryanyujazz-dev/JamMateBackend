from __future__ import annotations

# harness token: test_v2_6_127_engine_ballad_brush_semantic_policy_skeleton

import json
from jammate_engine.styles.jazz_ballad import arrangement_policy, percussion_patterns


def test_v2_6_127_ballad_percussion_remains_silent_by_default() -> None:
    candidates = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    assert candidates == ()


def test_v2_6_127_arrangement_policy_declares_brush_semantic_skeleton() -> None:
    policy = arrangement_policy.get_arrangement_policy()
    assert policy["default_feel"] == "jazz_ballad"
    assert policy["avoid_full_bar_silence"] is True
    assert policy["jazz_ballad_brush_semantic_policy_active"] is True
    assert policy["jazz_ballad_brush_semantic_policy_version"] == "v2_6_127"
    assert policy["jazz_ballad_brush_semantic_policy_no_fixed_loop"] is True
    assert policy["jazz_ballad_brush_semantic_policy_no_swing_ride"] is True
    assert policy["jazz_ballad_brush_semantic_policy_no_rock_backbeat"] is True


def test_v2_6_127_brush_semantic_dimensions_are_declared_without_midi_values() -> None:
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
    assert decision["jazz_ballad_brush_semantic_policy_boundary"] == "semantic_intent_only_no_concrete_midi_notes_or_velocities"
    assert decision["brush_texture_intent"] == "circular_standard"
    assert decision["brush_time_anchor_intent"] == "2_4_soft"
    assert decision["brush_kick_policy_intent"] == "one_three"
    assert decision["brush_phrase_breath_intent"] == "none"
    assert decision["brush_density_band"] == "medium"
    assert decision["brush_runtime_audible"] is False
    assert decision["brush_runtime_note_event_count"] == 0
    assert decision["brush_no_fixed_loop"] is True
    assert decision["brush_no_swing_ride"] is True
    assert decision["brush_no_rock_backbeat"] is True
    assert "drum_events" not in decision
    assert "pattern_events" not in decision
    assert "\"concrete_midi_note\":" not in json.dumps(decision, ensure_ascii=False)


def test_v2_6_127_brush_phrase_context_classifies_tail_and_final_release() -> None:
    phrase_tail = percussion_patterns.build_brush_semantic_policy_decision(
        {
            "region_duration_beats": 4.0,
            "region_source_bar_index": 7,
            "region_chorus_index": 0,
            "region_total_choruses": 3,
        }
    )
    assert phrase_tail["brush_texture_intent"] == "half_bar_breath_sweep"
    assert phrase_tail["brush_time_anchor_intent"] == "4_only"
    assert phrase_tail["brush_phrase_breath_intent"] == "soft_swish_4and"
    assert phrase_tail["brush_density_band"] == "very_low"

    final = percussion_patterns.build_brush_semantic_policy_decision(
        {
            "region_duration_beats": 4.0,
            "region_source_bar_index": 31,
            "region_chorus_index": 2,
            "region_total_choruses": 3,
            "region_is_last_bar_of_chorus": True,
        }
    )
    assert final["brush_texture_intent"] == "release_sweep"
    assert final["brush_time_anchor_intent"] == "none"
    assert final["brush_kick_policy_intent"] == "none"
    assert final["brush_phrase_breath_intent"] == "final_release"
    assert final["brush_phrase_context"]["final_release_context"] is True


def test_v2_6_127_static_skeleton_can_be_consumed_by_v2_6_128_candidate_opt_in() -> None:
    # v2_6_127's bare semantic helper remains metadata-only. v2_6_128 can
    # explicitly consume the same context to create a sparse brush candidate.
    assert percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0}) == ()
    candidates = percussion_patterns.get_pattern_candidates(
        {
            "region_duration_beats": 4.0,
            "region_source_bar_index": 4,
            "region_chorus_index": 0,
            "region_total_choruses": 3,
            "jazz_ballad_first_audible_sparse_brush_foundation_active": True,
        }
    )
    assert len(candidates) == 1
    assert candidates[0].metadata["jazz_ballad_brush_semantic_policy_version"] == "v2_6_127"
    assert candidates[0].metadata["jazz_ballad_first_audible_sparse_brush_foundation_version"] == "v2_6_128"
