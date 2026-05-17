from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.midi.render_pipeline import PEDAL_REALIZER_VERSION, REPEDAL_POLICY_VERSION, realize_pedal_events, render_midi_with_audit
from jammate_engine.realization.note_event_builder import NoteEvent


def _note(*, pedal: str, start: float = 0.0, duration: float = 1.0, event_id: str = "evt") -> NoteEvent:
    return NoteEvent(
        track="piano",
        channel=0,
        note=60,
        velocity=64,
        start_beat=start,
        duration_beats=duration,
        expression_event_id=event_id,
        pedal=pedal,
    )


def test_version_tag_updated_for_v2_3_9() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert PEDAL_REALIZER_VERSION == "v2_3_9"
    assert REPEDAL_POLICY_VERSION == "v2_3_9"


def test_ballad_repedal_offsets_lift_before_next_chord_and_repress_after_attack() -> None:
    events = [
        _note(pedal="sustain", start=0.0, duration=2.0, event_id="old_harmony"),
        _note(pedal="sustain", start=1.0, duration=1.0, event_id="new_harmony"),
    ]
    pedal_events, audit = realize_pedal_events(events, {"metadata": {"style": "jazz_ballad"}, "feel": "straight"})

    assert audit["repedal_policy_version"] == "v2_3_9"
    assert audit["repedal_offset_enabled"] is True
    assert audit["repedal_adjusted_span_count"] == 2
    assert audit["repedal_gap_count"] == 1
    assert audit["repedal_gap_beats_min"] >= 0.02
    assert audit["repedal_warning_count"] == 0

    # Human-like re-pedal: down shortly after the first attack, lift before the
    # next chord, down again shortly after the next attack.
    assert [(event.value, round(event.beat, 3)) for event in pedal_events] == [
        (96, 0.02),
        (0, 0.965),
        (96, 1.02),
        (0, 2.0),
    ]


def test_dry_styles_still_do_not_realize_cc64_or_repedal() -> None:
    for style in ("bossa_nova", "medium_swing"):
        pedal_events, audit = realize_pedal_events(
            [_note(pedal="sustain", start=0.0, duration=2.0, event_id=f"{style}_evt")],
            {"metadata": {"style": style}, "feel": "swing" if style == "medium_swing" else "straight"},
        )
        assert pedal_events == []
        assert audit["cc64_event_count"] == 0
        assert audit["repedal_offset_enabled"] is False
        assert audit["repedal_adjusted_span_count"] == 0
        assert audit["repedal_gap_count"] == 0


def test_midi_writer_serializes_repedal_offset_cc64_boundary(tmp_path: Path) -> None:
    midi_path = tmp_path / "repedal_boundary.mid"
    _path, debug = render_midi_with_audit(
        [_note(pedal="sustain", start=0.0, duration=2.0, event_id="old"), _note(pedal="sustain", start=1.0, duration=1.0, event_id="new")],
        midi_path,
        tempo_bpm=72,
        timing_policy={"metadata": {"style": "jazz_ballad"}, "feel": "straight"},
    )
    data = midi_path.read_bytes()

    pedal = debug["pedal_realization"]
    assert pedal["cc64_event_count"] == 4
    assert pedal["repedal_gap_count"] == 1
    assert b"\xB0\x40\x60" in data  # CC64 sustain pedal on, channel 0
    assert b"\xB0\x40\x00" in data  # CC64 pedal off, channel 0
