from __future__ import annotations

from pathlib import Path

from jammate_engine.midi.render_pipeline import apply_timing_policy, performed_beat, render_midi
from jammate_engine.midi.midi_writer import TPQ
from jammate_engine.realization.note_event_builder import NoteEvent
from jammate_engine.styles.medium_swing.profile import MediumSwingProfile


def _read_vlq(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    while True:
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if byte < 0x80:
            return value, pos


def _track_payloads(data: bytes) -> list[bytes]:
    header_len = int.from_bytes(data[4:8], "big")
    pos = 8 + header_len
    payloads: list[bytes] = []
    while pos < len(data):
        length = int.from_bytes(data[pos + 4 : pos + 8], "big")
        start = pos + 8
        payloads.append(data[start : start + length])
        pos = start + length
    return payloads


def _absolute_note_on_ticks(track: bytes) -> list[int]:
    pos = 0
    tick = 0
    running_status: int | None = None
    out: list[int] = []
    while pos < len(track):
        delta, pos = _read_vlq(track, pos)
        tick += delta
        status = track[pos]
        if status == 0xFF:
            pos += 1
            meta_type = track[pos]
            pos += 1
            length, pos = _read_vlq(track, pos)
            if meta_type == 0x2F:
                break
            pos += length
            running_status = None
            continue
        if status >= 0x80:
            pos += 1
            running_status = status
        elif running_status is None:
            raise AssertionError("bad running status")
        else:
            status = running_status
        command = status & 0xF0
        if command in (0xC0, 0xD0):
            pos += 1
            continue
        data1 = track[pos]
        data2 = track[pos + 1]
        pos += 2
        if command == 0x90 and data2 > 0:
            out.append(tick)
    return out


def test_medium_swing_timing_policy_swings_logical_half_beats() -> None:
    policy = MediumSwingProfile().timing_policy
    assert performed_beat(0.5, "auto", policy) == 2.0 / 3.0
    assert performed_beat(2.5, "swing_upbeat", policy) == 2.0 + 2.0 / 3.0
    assert performed_beat(0.5, "straight_even", policy) == 0.5
    assert performed_beat(0.5, "literal", policy) == 0.5


def test_apply_timing_policy_preserves_logical_events_but_outputs_performed_starts() -> None:
    policy = MediumSwingProfile().timing_policy
    events = [
        NoteEvent(track="bass", channel=1, note=36, velocity=70, start_beat=0.5, duration_beats=0.25),
        NoteEvent(track="bass", channel=1, note=38, velocity=70, start_beat=1.5, duration_beats=0.25, timing_intent="straight_even"),
    ]
    performed = apply_timing_policy(events, policy)
    assert events[0].start_beat == 0.5
    assert abs(performed[0].start_beat - (2.0 / 3.0)) < 1e-9
    assert performed[0].duration_beats == events[0].duration_beats
    assert performed[1].start_beat == 1.5


def test_render_pipeline_writes_swing_upbeat_to_midi_ticks(tmp_path: Path) -> None:
    midi_path = tmp_path / "swing_grid.mid"
    render_midi(
        [NoteEvent(track="piano", channel=0, note=60, velocity=80, start_beat=0.5, duration_beats=0.1)],
        midi_path,
        tempo_bpm=132,
        timing_policy=MediumSwingProfile().timing_policy,
    )
    piano_track = _track_payloads(midi_path.read_bytes())[1]
    assert _absolute_note_on_ticks(piano_track) == [round((2.0 / 3.0) * TPQ)]
