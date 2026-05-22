from __future__ import annotations

from jammate_engine.midi.render_pipeline import performed_beat
from jammate_engine.realization.percussion_realizer import DRUM_NOTES, DYNAMIC_VELOCITY, STROKE_DURATION
from jammate_engine.styles.jazz_ballad import arrangement_policy, percussion_patterns
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile

CUSTOM_BRUSH_DRUM_VOICES = {"brush_swirl", "brush_sweep", "brush_tap", "brush_release"}


def _candidate(context: dict):
    return percussion_patterns.get_pattern_candidates({**context, "jazz_ballad_brush_sound_source_time_feel_active": True})[0]


def test_v2_6_132_policy_keeps_brush_source_on_shared_swing8_contract() -> None:
    policy = arrangement_policy.get_arrangement_policy()
    assert policy["jazz_ballad_brush_sound_source_time_feel_version"] == "v2_6_133"
    assert policy["jazz_ballad_brush_sound_source_assumed"] is True
    assert policy["jazz_ballad_drum_planning_scope"] == "bar_level_brush_time_feel_with_region_projection"
    assert policy["jazz_ballad_drum_not_chord_region_loop"] is True
    assert policy["jazz_ballad_no_custom_internal_brush_voices"] is True
    assert policy["jazz_ballad_brush_motion_points"] == ("1", "1&", "2", "2&", "3", "3&", "4", "4&")


def test_v2_6_132_offbeat_brush_events_use_existing_swing_upbeat_timing() -> None:
    candidate = _candidate({"region_duration_beats": 4.0, "region_source_bar_index": 1, "region_chorus_index": 0, "region_total_choruses": 3})
    policy = JazzBalladProfile().timing_policy
    offbeats = [event for event in candidate.events if "&" in str(event.metadata.get("brush_event_slot"))]
    downbeats = [event for event in candidate.events if "&" not in str(event.metadata.get("brush_event_slot"))]

    assert offbeats
    assert all(event.metadata["timing_intent"] == "swing_upbeat" for event in offbeats)
    assert all(event.metadata["brush_timing_contract"] == "style_timing_policy_swing8" for event in offbeats)
    assert all(event.metadata["brush_timing_owner"] == "style_timing_policy_not_pattern" for event in offbeats)
    assert all(event.metadata["timing_intent"] == "auto" for event in downbeats)

    logical_by_slot = {str(event.metadata["brush_event_slot"]): event.local_beat for event in candidate.events}
    assert logical_by_slot["2&"] == 1.5
    assert logical_by_slot["4&"] == 3.5
    assert performed_beat(logical_by_slot["2&"], "swing_upbeat", policy) == 1.0 + 2.0 / 3.0
    assert performed_beat(logical_by_slot["4&"], "swing_upbeat", policy) == 3.0 + 2.0 / 3.0


def test_v2_6_132_candidate_contains_offbeat_brush_skip_not_private_timing_or_ride_pattern() -> None:
    candidate = _candidate({"region_duration_beats": 4.0, "region_source_bar_index": 1, "region_chorus_index": 0, "region_total_choruses": 3})
    assert candidate.metadata["brush_feel_cell"] == "brush_swing_skip"
    assert candidate.metadata["brush_motion_lane"] == "logical_eighth_sweep_path_resolved_by_style_swing8_timing"
    assert candidate.metadata["brush_offbeat_policy"]["2&"] == "swing_skip_lift"
    assert candidate.metadata["brush_offbeat_policy"]["4&"] == "pickup_or_breath_to_next_bar"
    drums = {event.metadata["drum"] for event in candidate.events}
    assert drums <= {"snare", "hihat_pedal", "kick", "ride"}
    assert CUSTOM_BRUSH_DRUM_VOICES.isdisjoint(drums)
    assert not any(event.metadata.get("timing_intent") == "ballad_brush_sound_source_swing_time" for event in candidate.events)
    assert not any(event.metadata.get("drum") == "ride" for event in candidate.events if event.metadata.get("brush_feel_cell") != "final_release")


def test_v2_6_132_split_regions_project_one_bar_plan_without_restarting_loop() -> None:
    first = _candidate({"region_duration_beats": 2.0, "region_source_bar_index": 1, "region_chorus_index": 0, "region_total_choruses": 3, "region_is_first_region_of_bar": True})
    second = _candidate({"region_duration_beats": 2.0, "region_source_bar_index": 1, "region_chorus_index": 0, "region_total_choruses": 3, "region_is_last_region_of_bar": True})
    assert first.metadata["bar_region_projection"]["region_role"] == "first_half"
    assert second.metadata["bar_region_projection"]["region_role"] == "second_half"
    first_slots = {event.metadata.get("brush_event_slot") for event in first.events}
    second_slots = {event.metadata.get("brush_event_slot") for event in second.events}
    assert {"1", "2", "2&"}.issubset(first_slots)
    assert {"3", "4", "4&"}.issubset(second_slots)
    assert "1" not in second_slots
    assert "4&" not in first_slots


def test_v2_6_132_phrase_breath_uses_3and_to_4and_shared_swing8_motion() -> None:
    candidate = _candidate({"region_duration_beats": 4.0, "region_source_bar_index": 7, "region_chorus_index": 0, "region_total_choruses": 3})
    assert candidate.metadata["brush_feel_cell"] == "phrase_breath_release"
    breath_events = [event for event in candidate.events if event.role in {"ballad_phrase_brush_breath", "ballad_classic_brush_fill"}]
    breath_slots = [event.metadata.get("brush_event_slot") for event in breath_events]
    assert "3&" in breath_slots
    assert "4&" in breath_slots
    assert all(event.metadata["timing_intent"] == "swing_upbeat" for event in breath_events if "&" in str(event.metadata.get("brush_event_slot")))


def test_v2_6_132_percussion_realizer_has_brush_source_profiles_without_custom_drums() -> None:
    assert CUSTOM_BRUSH_DRUM_VOICES.isdisjoint(DRUM_NOTES)
    for profile in ("brush_motion_pp", "brush_skip_pp", "brush_breath_pp", "brush_hat_p", "brush_feather"):
        assert profile in DYNAMIC_VELOCITY
    for stroke in ("brush_sweep", "brush_swish", "brush_foot", "feather"):
        assert stroke in STROKE_DURATION
