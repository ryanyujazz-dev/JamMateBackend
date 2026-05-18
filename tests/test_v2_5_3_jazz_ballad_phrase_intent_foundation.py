from __future__ import annotations

from jammate_engine.core.gestures import GestureKind
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles.jazz_ballad import comping_patterns, gesture_policy
from jammate_engine.styles.registry import get_style


def test_v2_5_4_ballad_phrase_intent_library_exposes_v2_native_families() -> None:
    description = comping_patterns.describe_pattern_library({"region_duration_beats": 4.0})

    assert description["version"] == "v2_5_9"
    assert description["phrase_intent_version"] == "v2_5_9"
    assert "gesture_request_slots_only" in description["boundary_notes"]
    assert {"warm_pad", "breath_answer", "temporary_low_level_fallback"}.issubset(set(description["phrase_families"]))

    names = {candidate.name for candidate in comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})}
    assert "ballad_phrase_breath_answer_inner_motion" in names
    assert "ballad_piano_soft_downbeat_sustain" in names


def test_v2_5_4_breath_answer_candidate_requests_inner_movement_without_notes_or_texture() -> None:
    candidate = next(c for c in comping_patterns.get_pattern_candidates({}) if c.name == "ballad_phrase_breath_answer_inner_motion")
    assert candidate.metadata["phrase_family"] == "breath_answer"
    assert candidate.metadata["gesture_intent"] == "inner_movement"

    motion_spec = candidate.events[1]
    assert motion_spec.gesture is not None
    assert motion_spec.gesture.kind == GestureKind.INNER_MOVEMENT
    assert motion_spec.gesture.projection_refs == ("inner",)
    assert motion_spec.metadata["phrase_slot"] == "inner_motion_answer"

    forbidden = {"midi_note", "notes", "pitch", "velocity", "duration_beats", "pedal", "voicing_texture", "source_degrees"}
    assert forbidden.isdisjoint(candidate.metadata)
    assert forbidden.isdisjoint(motion_spec.metadata)
    assert forbidden.isdisjoint(motion_spec.gesture.metadata)
    gesture_policy.validate_gesture_request(motion_spec.gesture)


def test_v2_5_4_two_beat_regions_expose_two_chord_soft_marks_only_inside_region() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 2.0})
    by_name = {candidate.name: candidate for candidate in candidates}

    assert "ballad_phrase_two_chord_soft_marks" in by_name
    candidate = by_name["ballad_phrase_two_chord_soft_marks"]
    assert candidate.metadata["phrase_family"] == "two_chord_soft_marks"
    assert all(max(c.rhythm_beats) < 2.0 for c in candidates)
    assert candidate.rhythm_beats == (0.0, 0.5)
    assert candidate.events[1].metadata["phrase_slot"] == "soft_mark"


def test_v2_5_4_major_251_stable_cadence_candidate_is_context_gated_and_pitchless() -> None:
    region = HarmonicRegion(
        region_id="r_ballad_251_v253",
        chord_symbol="G7",
        next_chord_symbol="Cmaj7",
        chorus_index=0,
        bar_index=0,
        chord_index=1,
        start_beat=4.0,
        duration_beats=4.0,
        metadata={"previous_chord_symbol": "Dm7", "home_key": "C"},
    )
    candidates = comping_patterns.get_pattern_candidates({"region": region, "region_duration_beats": 4.0})
    candidate = next(c for c in candidates if c.name == "ballad_phrase_major_251_stable_cadence")

    assert candidate.metadata["phrase_family"] == "major_251_stable_cadence"
    assert candidate.metadata["context_gate"] == "major_ii_v_i_window_current_dominant_region"
    assert candidate.events[1].gesture is not None
    assert candidate.events[1].gesture.kind == GestureKind.INNER_MOVEMENT
    assert candidate.events[1].gesture.projection_refs == ("color_group",)

    generic = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "chord_symbol": "Cmaj7", "next_chord_symbol": "Fmaj7"})
    assert "ballad_phrase_major_251_stable_cadence" not in {c.name for c in generic}


def test_v2_5_4_default_ballad_runtime_still_uses_warm_pad_anchor_without_rng() -> None:
    style = get_style("jazz_ballad")
    region = HarmonicRegion(
        region_id="r_ballad_default_v253",
        chord_symbol="Cmaj7",
        next_chord_symbol="Fmaj7",
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=0.0,
        duration_beats=4.0,
    )

    plan = style.plan_region(region, context={})
    assert plan.selected_candidate == "ballad_piano_soft_downbeat_sustain + ballad_bass_root_anchor"
    piano_events = [event for event in plan.events if event.track == "piano"]
    assert piano_events[0].metadata["phrase_family"] == "warm_pad"
    assert [event.gesture_type for event in piano_events] == ["simultaneous_onset"]
