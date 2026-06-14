from __future__ import annotations

from jammate_engine.styles.jazz_ballad import arrangement_policy, percussion_patterns


def _candidate(context: dict):
    return percussion_patterns.get_pattern_candidates({**context, "jazz_ballad_brush_sound_source_time_feel_active": True})[0]


def _fill_events(candidate):
    return [event for event in candidate.events if event.role in {"ballad_section_transition_hint", "ballad_classic_brush_fill"}]


def test_v2_6_137_policy_declares_timbre_and_reduced_offbeat_contract() -> None:
    policy = arrangement_policy.get_arrangement_policy()
    assert policy["jazz_ballad_brush_sound_source_time_feel_version"] == "v2_6_137"
    assert policy["jazz_ballad_brush_section_transition_hint_active"] is True
    assert policy["jazz_ballad_brush_section_transition_hint_version"] == "v2_6_137"
    assert policy["jazz_ballad_classic_brush_fill_audibility_contract"] == "section_transition_hint_lane_without_background_duck"


def test_v2_6_137_section_tail_uses_hat_and_cymbal_hint_not_explicit_fill_display() -> None:
    candidate = _candidate({
        "region_duration_beats": 4.0,
        "region_source_bar_index": 7,
        "region_chorus_index": 1,
        "region_total_choruses": 3,
        "region_is_last_bar_of_section": True,
    })
    assert candidate.metadata["brush_classic_fill_cell"] == "section_tail_4_hat_cymbal_hint"
    events = _fill_events(candidate)
    assert [event.metadata["brush_event_slot"] for event in events] == ["4", "4&"]
    assert [event.metadata["drum"] for event in events] == ["hihat_pedal", "ride"]
    assert all(event.role == "ballad_section_transition_hint" for event in events)
    assert events[0].metadata["timing_intent"] == "auto"
    assert events[1].metadata["timing_intent"] == "swing_upbeat"
    assert all(event.metadata["brush_fill_foreground_lane"] is False for event in events)


def test_v2_6_137_section_entry_uses_low_tom_bloom_on_beat_1() -> None:
    candidate = _candidate({
        "region_duration_beats": 4.0,
        "region_source_bar_index": 8,
        "region_chorus_index": 0,
        "region_total_choruses": 3,
        "region_is_first_bar_of_section": True,
    })
    assert candidate.metadata["brush_classic_fill_cell"] == "section_entry_brush_bloom"
    events = _fill_events(candidate)
    assert len(events) == 1
    assert events[0].metadata["brush_event_slot"] == "1"
    assert events[0].metadata["timing_intent"] == "auto"
    assert events[0].metadata["drum"] == "low_tom"


def test_v2_6_137_cadence_hint_uses_tom_or_v1_drag_without_long_tap_drag() -> None:
    candidate = _candidate({
        "region_duration_beats": 4.0,
        "region_source_bar_index": 3,
        "region_chorus_index": 0,
        "region_total_choruses": 3,
    })
    assert candidate.metadata["brush_classic_fill_cell"] == "v1_drag_to_4_hint"
    events = _fill_events(candidate)
    assert [event.metadata["brush_event_slot"] for event in events] == ["3&", "4"]
    assert [event.metadata["drum"] for event in events] == ["snare", "cross_stick"]
    assert all(event.role == "ballad_section_transition_hint" for event in events)



def test_v2_6_137_reduces_default_brush_offbeat_articulation() -> None:
    candidate = _candidate({
        "region_duration_beats": 4.0,
        "region_source_bar_index": 1,
        "region_chorus_index": 0,
        "region_total_choruses": 3,
    })
    offbeat_events = [event for event in candidate.events if "&" in str(event.metadata.get("brush_event_slot"))]
    assert len(offbeat_events) <= 1
    assert all(event.metadata["timing_intent"] == "swing_upbeat" for event in offbeat_events)

def test_v2_6_137_stronger_fill_cells_remain_vocabulary_but_not_default_selection() -> None:
    contexts = [
        {"region_duration_beats": 4.0, "region_source_bar_index": i, "region_chorus_index": 1, "region_total_choruses": 3}
        for i in range(8)
    ]
    selected = {_candidate(ctx).metadata["brush_classic_fill_cell"] for ctx in contexts}
    assert "tap_drag_tap_release" not in selected
    assert "single_stroke_4_to_next" not in selected
    assert "turnaround_sweep_roll" not in selected
    assert {"section_tail_4_hat_cymbal_hint", "v1_drag_to_4_hint", "turnaround_cross_stick_4_hint"} & selected
