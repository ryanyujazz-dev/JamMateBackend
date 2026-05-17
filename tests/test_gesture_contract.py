from __future__ import annotations

import pytest

from jammate_engine.core.expression.expression_plan import EventExpression
from jammate_engine.core.gestures import GestureKind, rolled_onset, simultaneous_onset
from jammate_engine.core.gestures.gesture import GestureRequest
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime import PatternCandidate, event_spec
from jammate_engine.realization.gesture_realizer import GestureRealizer
from jammate_engine.core.voicing.runtime.plan import VoicedNote, VoicingPlan
from jammate_engine.styles.registry import get_style


def test_simultaneous_onset_is_the_official_chordal_gesture_name() -> None:
    values = {kind.value for kind in GestureKind}
    assert "simultaneous_onset" in values
    assert "block_chord" not in values


def test_style_pattern_instantiates_pitchless_gesture_request() -> None:
    style = get_style("bossa_nova")
    region = HarmonicRegion(
        region_id="r1",
        chord_symbol="Dm7",
        next_chord_symbol="G7",
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=0.0,
        duration_beats=4.0,
    )
    plan = style.plan_region(region, context={})
    piano_events = [event for event in plan.events if event.track == "piano"]
    assert piano_events
    assert all(event.gesture.kind == GestureKind.SIMULTANEOUS_ONSET for event in piano_events)
    assert all(event.gesture_type == "simultaneous_onset" for event in piano_events)


def test_gesture_request_rejects_concrete_midi_and_expression_keys() -> None:
    with pytest.raises(ValueError):
        GestureRequest(kind=GestureKind.FILL, metadata={"midi_note": 60})

    with pytest.raises(ValueError):
        GestureRequest(kind=GestureKind.INNER_MOVEMENT, metadata={"duration_beats": 1.0})


def test_pattern_event_spec_can_request_rolled_onset_without_pitch() -> None:
    candidate = PatternCandidate(
        name="rolled_demo",
        weight=1.0,
        category="test",
        events=(
            event_spec(
                track="piano",
                beat=0.0,
                role="harmonic",
                gesture=rolled_onset(onset_offsets_beats=(0.0, 0.1, 0.2)),
            ),
        ),
    )
    region = HarmonicRegion(
        region_id="r2",
        chord_symbol="Cmaj7",
        next_chord_symbol="Fmaj7",
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=4.0,
        duration_beats=4.0,
    )
    event = candidate.instantiate(region).events[0]
    assert event.gesture.kind == GestureKind.ROLLED_ONSET
    assert event.gesture_type == "rolled_onset"
    assert not hasattr(event, "midi_note")


def test_gesture_realizer_projects_voice_order_after_voicing() -> None:
    event = PatternCandidate(
        name="rolled_demo",
        weight=1.0,
        category="test",
        events=(
            event_spec(
                track="piano",
                beat=0.0,
                role="harmonic",
                gesture=rolled_onset(
                    voice_order=("lowest", "top", "inner"),
                    onset_offsets_beats=(0.0, 0.1, 0.2),
                ),
            ),
        ),
    ).instantiate(
        HarmonicRegion(
            region_id="r3",
            chord_symbol="Cmaj7",
            next_chord_symbol="Fmaj7",
            chorus_index=0,
            bar_index=0,
            chord_index=0,
            start_beat=8.0,
            duration_beats=4.0,
        )
    ).events[0]

    voicing = VoicingPlan(
        event_id=event.event_id,
        chord_symbol="Cmaj7",
        notes=[
            VoicedNote(midi_note=48, degree="R", voice_role="lowest"),
            VoicedNote(midi_note=55, degree="5", voice_role="inner_1"),
            VoicedNote(midi_note=64, degree="3", voice_role="top"),
        ],
    )
    expr = EventExpression(
        event_id=event.event_id,
        duration_beats=1.0,
        velocity=64,
        articulation="short",
        pedal="none",
    )

    notes = GestureRealizer().realize_harmonic_event(event, voicing, expr)
    assert [note.note for note in notes] == [48, 64, 55]
    assert [note.start_beat for note in notes] == [8.0, 8.1, 8.2]
