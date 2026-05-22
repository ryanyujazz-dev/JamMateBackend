from __future__ import annotations

from jammate_engine.midi.render_pipeline import performed_beat
from jammate_engine.styles.jazz_ballad import arrangement_policy, percussion_patterns
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile

CUSTOM_BRUSH_DRUM_VOICES = {"brush_swirl", "brush_sweep", "brush_tap", "brush_release"}


def _candidate(context: dict):
    return percussion_patterns.get_pattern_candidates({**context, "jazz_ballad_brush_sound_source_time_feel_active": True})[0]


def _fill_slots(candidate) -> set[str]:
    return {str(event.metadata.get("brush_event_slot")) for event in candidate.events if event.role == "ballad_classic_brush_fill"}


def test_v2_6_133_policy_declares_classic_brush_fill_overlay_contract() -> None:
    policy = arrangement_policy.get_arrangement_policy()
    assert policy["jazz_ballad_brush_sound_source_time_feel_version"] == "v2_6_133"
    assert policy["jazz_ballad_classic_brush_fill_policy_active"] is True
    assert policy["jazz_ballad_classic_brush_fill_policy_version"] == "v2_6_133"
    assert "single_stroke_4_to_next" in policy["jazz_ballad_classic_brush_fill_cells"]
    assert policy["jazz_ballad_drum_not_chord_region_loop"] is True


def test_v2_6_133_plain_bar_has_no_classic_fill_overlay() -> None:
    candidate = _candidate({"region_duration_beats": 4.0, "region_source_bar_index": 0, "region_chorus_index": 0, "region_total_choruses": 3})
    assert candidate.metadata["brush_classic_fill_cell"] == "none"
    assert not [event for event in candidate.events if event.role == "ballad_classic_brush_fill"]


def test_v2_6_133_phrase_tail_uses_tap_drag_tap_with_shared_swing8_offbeats() -> None:
    candidate = _candidate({"region_duration_beats": 4.0, "region_source_bar_index": 3, "region_chorus_index": 0, "region_total_choruses": 3})
    assert candidate.metadata["brush_feel_cell"] == "phrase_breath_release"
    assert candidate.metadata["brush_classic_fill_cell"] == "tap_drag_tap_release"
    assert {"2&", "3&", "4", "4&"}.issubset(_fill_slots(candidate))
    policy = JazzBalladProfile().timing_policy
    offbeat_events = [event for event in candidate.events if event.role == "ballad_classic_brush_fill" and "&" in str(event.metadata.get("brush_event_slot"))]
    assert offbeat_events
    assert all(event.metadata["timing_intent"] == "swing_upbeat" for event in offbeat_events)
    logical_by_slot = {str(event.metadata["brush_event_slot"]): event.local_beat for event in offbeat_events}
    assert performed_beat(logical_by_slot["3&"], "swing_upbeat", policy) == 2.0 + 2.0 / 3.0


def test_v2_6_133_later_chorus_section_tail_uses_single_stroke_4_to_next() -> None:
    candidate = _candidate({"region_duration_beats": 4.0, "region_source_bar_index": 7, "region_chorus_index": 1, "region_total_choruses": 3})
    assert candidate.metadata["brush_classic_fill_cell"] == "single_stroke_4_to_next"
    assert {"3", "3&", "4", "4&"}.issubset(_fill_slots(candidate))
    assert all(event.metadata["drum"] == "snare" for event in candidate.events if event.role == "ballad_classic_brush_fill")


def test_v2_6_133_split_regions_project_fill_without_restarting_bar_loop() -> None:
    first = _candidate({"region_duration_beats": 2.0, "region_source_bar_index": 7, "region_chorus_index": 1, "region_total_choruses": 3, "region_is_first_region_of_bar": True})
    second = _candidate({"region_duration_beats": 2.0, "region_source_bar_index": 7, "region_chorus_index": 1, "region_total_choruses": 3, "region_is_last_region_of_bar": True})
    assert first.metadata["brush_classic_fill_cell"] == "single_stroke_4_to_next"
    assert second.metadata["brush_classic_fill_cell"] == "single_stroke_4_to_next"
    assert _fill_slots(first) == set()
    assert {"3", "3&", "4", "4&"}.issubset(_fill_slots(second))
    assert "1" not in {event.metadata.get("brush_event_slot") for event in second.events}


def test_v2_6_133_final_release_uses_release_fill_not_dense_loop_or_custom_drums() -> None:
    candidate = _candidate({"region_duration_beats": 4.0, "region_source_bar_index": 31, "region_chorus_index": 2, "region_total_choruses": 3, "region_is_last_bar_of_chorus": True})
    assert candidate.metadata["brush_classic_fill_cell"] == "final_brush_release"
    drums = {event.metadata["drum"] for event in candidate.events}
    assert drums <= {"snare", "ride"}
    assert CUSTOM_BRUSH_DRUM_VOICES.isdisjoint(drums)
