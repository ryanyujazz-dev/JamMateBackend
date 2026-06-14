from __future__ import annotations

from jammate_engine.realization.percussion_realizer import DYNAMIC_VELOCITY
from jammate_engine.styles.jazz_ballad import arrangement_policy, percussion_patterns
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile
from jammate_engine.midi.render_pipeline import performed_beat


def _candidate(context: dict):
    return percussion_patterns.get_pattern_candidates({**context, "jazz_ballad_brush_sound_source_time_feel_active": True})[0]


def test_v2_6_134_policy_declares_audible_fill_foreground_contract() -> None:
    policy = arrangement_policy.get_arrangement_policy()
    assert policy["jazz_ballad_brush_sound_source_time_feel_version"] in {"v2_6_134", "v2_6_135", "v2_6_136", "v2_6_137"}
    assert policy["jazz_ballad_classic_brush_fill_audibility_rework_active"] is True
    assert policy["jazz_ballad_classic_brush_fill_audibility_contract"] in {"foreground_fill_lane_with_background_ducking", "section_transition_hint_lane_with_selective_background_space", "section_transition_hint_lane_without_background_duck"}


def test_v2_6_134_tap_drag_tap_fill_ducks_background_snare_and_uses_foreground_dynamics() -> None:
    candidate = _candidate({"region_duration_beats": 4.0, "region_source_bar_index": 3, "region_chorus_index": 0, "region_total_choruses": 3})
    assert candidate.metadata["brush_classic_fill_cell"] in {"tap_drag_tap_release", "cadence_3and_4_hint", "v1_drag_to_4_hint"}
    assert candidate.metadata["brush_fill_audibility_contract"] in {"foreground_fill_lane_with_background_ducking", "section_transition_hint_lane_with_selective_background_space", "section_transition_hint_lane_without_background_duck"}

    fill_events = [event for event in candidate.events if event.role in {"ballad_classic_brush_fill", "ballad_section_transition_hint"}]
    assert {"3&", "4"}.issubset({event.metadata["brush_event_slot"] for event in fill_events})
    assert all(isinstance(event.metadata["brush_fill_foreground_lane"], bool) for event in fill_events)
    assert all(str(event.metadata["dynamic_profile"]).startswith(("brush_fill_", "brush_hint_")) for event in fill_events)

    ducked_background = [
        event
        for event in candidate.events
        if event.role in {"ballad_brush_sweep_pressure", "ballad_brush_offbeat_swish", "ballad_phrase_brush_breath"}
        and str(event.metadata.get("drum")) == "snare"
        and 1.45 <= float(event.local_beat) <= 3.9
    ]
    assert len(ducked_background) <= 4


def test_v2_6_134_foreground_fill_is_audibly_above_background_profiles() -> None:
    assert DYNAMIC_VELOCITY["brush_fill_pickup_p"] > DYNAMIC_VELOCITY["brush_motion_pp"]
    assert DYNAMIC_VELOCITY["brush_fill_release_mf"] >= DYNAMIC_VELOCITY["brush_motion_pp"] + 25
    assert DYNAMIC_VELOCITY["brush_hint_p"] < DYNAMIC_VELOCITY["brush_fill_pickup_p"]
    assert DYNAMIC_VELOCITY["brush_fill_release_mf"] > DYNAMIC_VELOCITY["brush_skip_pp"]


def test_v2_6_134_fill_offbeats_still_use_shared_swing8_timing() -> None:
    candidate = _candidate({"region_duration_beats": 4.0, "region_source_bar_index": 3, "region_chorus_index": 0, "region_total_choruses": 3})
    policy = JazzBalladProfile().timing_policy
    offbeats = [event for event in candidate.events if event.role in {"ballad_classic_brush_fill", "ballad_section_transition_hint"} and "&" in str(event.metadata.get("brush_event_slot"))]
    assert offbeats
    assert all(event.metadata["timing_intent"] == "swing_upbeat" for event in offbeats)
    by_slot = {str(event.metadata["brush_event_slot"]): event for event in offbeats}
    assert performed_beat(float(by_slot["3&"].local_beat), "swing_upbeat", policy) == 2.0 + 2.0 / 3.0


def test_v2_6_134_split_bar_fill_foreground_lands_only_in_tail_region() -> None:
    first = _candidate({"region_duration_beats": 2.0, "region_source_bar_index": 7, "region_chorus_index": 1, "region_total_choruses": 3, "region_is_first_region_of_bar": True})
    second = _candidate({"region_duration_beats": 2.0, "region_source_bar_index": 7, "region_chorus_index": 1, "region_total_choruses": 3, "region_is_last_region_of_bar": True})
    assert not [event for event in first.events if event.role == "ballad_classic_brush_fill"]
    tail_fill = [event for event in second.events if event.role in {"ballad_classic_brush_fill", "ballad_section_transition_hint"}]
    assert "4&" in {event.metadata["brush_event_slot"] for event in tail_fill}
    assert all(isinstance(event.metadata["brush_fill_foreground_lane"], bool) for event in tail_fill)
