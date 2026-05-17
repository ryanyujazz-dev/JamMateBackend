from __future__ import annotations

from pathlib import Path

import pytest

from jammate_engine.midi.midi_writer import _vlq, write_midi
from jammate_engine.realization.note_event_builder import NoteEvent


def _read_vlq(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    while True:
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if byte < 0x80:
            return value, pos


def _track_payloads(data: bytes) -> list[bytes]:
    assert data[:4] == b"MThd"
    header_len = int.from_bytes(data[4:8], "big")
    pos = 8 + header_len
    payloads: list[bytes] = []
    while pos < len(data):
        assert data[pos : pos + 4] == b"MTrk"
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
            raise AssertionError(f"MIDI data byte without running status at {pos}: {status:#x}")
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


def test_vlq_encoding_for_common_midi_deltas() -> None:
    assert _vlq(0) == b"\x00"
    assert _vlq(127) == b"\x7f"
    assert _vlq(128) == b"\x81\x00"
    assert _vlq(240) == b"\x81\x70"
    assert _vlq(480) == b"\x83\x60"
    assert _vlq(960) == b"\x87\x40"
    with pytest.raises(ValueError):
        _vlq(-1)


def test_midi_writer_preserves_note_timeline_after_127_ticks(tmp_path: Path) -> None:
    midi_path = tmp_path / "timeline.mid"
    write_midi(
        [
            NoteEvent(track="piano", channel=0, note=60, velocity=80, start_beat=0.0, duration_beats=0.5),
            NoteEvent(track="piano", channel=0, note=64, velocity=80, start_beat=1.0, duration_beats=0.5),
            NoteEvent(track="piano", channel=0, note=67, velocity=80, start_beat=4.0, duration_beats=0.5),
        ],
        midi_path,
        tempo_bpm=132,
    )
    tracks = _track_payloads(midi_path.read_bytes())
    piano_track = tracks[1]
    assert _absolute_note_on_ticks(piano_track) == [0, 480, 1920]
