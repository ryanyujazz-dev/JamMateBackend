from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.midi.render_pipeline import PEDAL_REALIZER_VERSION, realize_pedal_events, render_midi_with_audit
from jammate_engine.realization.note_event_builder import NoteEvent


def _note(*, pedal: str, start: float = 0.0, event_id: str = "evt") -> NoteEvent:
    return NoteEvent(
        track="piano",
        channel=0,
        note=60,
        velocity=64,
        start_beat=start,
        duration_beats=1.0,
        expression_event_id=event_id,
        pedal=pedal,
    )


def test_version_tag_updated_for_v2_3_9() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"


def test_ballad_light_and_sustain_pedal_intent_materializes_as_cc64_spans() -> None:
    events = [
        _note(pedal="light", event_id="light_evt"),
        _note(pedal="light", event_id="light_evt"),  # duplicate voicing note, same expression event
        _note(pedal="sustain", start=2.0, event_id="sustain_evt"),
    ]
    pedal_events, audit = realize_pedal_events(
        events,
        {"metadata": {"style": "jazz_ballad"}, "feel": "straight"},
    )

    assert audit["pedal_realizer_version"] == PEDAL_REALIZER_VERSION
    assert audit["allowed_modes"] == ["light", "sustain"]
    assert audit["realized_span_counts_by_mode"] == {"light": 1, "sustain": 1}
    assert audit["cc64_event_count"] == 4
    assert [(event.value, round(event.beat, 3)) for event in pedal_events] == [(64, 0.02), (0, 1.0), (96, 2.02), (0, 3.0)]
    assert audit["repedal_offset_enabled"] is True
    assert audit["repedal_adjusted_span_count"] == 2


def test_bossa_and_swing_suppress_cc64_even_when_expression_profile_carries_light_pedal() -> None:
    for style in ("bossa_nova", "medium_swing"):
        pedal_events, audit = realize_pedal_events(
            [_note(pedal="light", event_id=f"{style}_evt")],
            {"metadata": {"style": style}, "feel": "swing" if style == "medium_swing" else "straight"},
        )
        assert pedal_events == []
        assert audit["allowed_modes"] == []
        assert audit["cc64_event_count"] == 0
        assert audit["suppressed_note_counts_by_reason"] == {"light:style_boundary": 1}


def test_midi_writer_serializes_realized_cc64_boundary(tmp_path: Path) -> None:
    midi_path = tmp_path / "pedal_boundary.mid"
    _path, debug = render_midi_with_audit(
        [_note(pedal="light", event_id="light_evt")],
        midi_path,
        tempo_bpm=72,
        timing_policy={"metadata": {"style": "jazz_ballad"}, "feel": "straight"},
    )
    data = midi_path.read_bytes()

    assert debug["pedal_realization"]["cc64_event_count"] == 2
    assert b"\xB0\x40\x40" in data  # CC64 light pedal on, channel 0
    assert b"\xB0\x40\x00" in data  # CC64 pedal off, channel 0
