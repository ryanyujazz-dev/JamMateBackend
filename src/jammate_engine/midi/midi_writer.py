from __future__ import annotations

from pathlib import Path
from typing import Iterable

from jammate_engine.midi.channel_map import CHANNELS
from jammate_engine.midi.instrument_map import INSTRUMENT_PROGRAMS
from jammate_engine.realization.note_event_builder import NoteEvent, PedalEvent

TPQ = 480

# Event priorities at the same tick.  This keeps repedaling deterministic:
# previous notes release, pedal comes up, pedal goes down, then the new notes hit.
_MIDI_PRIORITY_PROGRAM = -100
_MIDI_PRIORITY_NOTE_OFF = -20
_MIDI_PRIORITY_PEDAL_OFF = -10
_MIDI_PRIORITY_PEDAL_ON = -5
_MIDI_PRIORITY_NOTE_ON = 0


def _vlq(value: int) -> bytes:
    """Encode a MIDI variable-length quantity."""

    if value < 0:
        raise ValueError("VLQ value must be non-negative")

    buffer = [value & 0x7F]
    value >>= 7
    while value:
        buffer.insert(0, (value & 0x7F) | 0x80)
        value >>= 7
    return bytes(buffer)


def _normalize_event(event: tuple) -> tuple[int, int, bytes]:
    if len(event) == 2:
        tick, payload = event
        return int(tick), 0, bytes(payload)
    tick, priority, payload = event
    return int(tick), int(priority), bytes(payload)


def _track_chunk(events: list[tuple[int, bytes]] | list[tuple[int, int, bytes]]) -> bytes:
    normalized = [_normalize_event(event) for event in events]
    normalized = sorted(normalized, key=lambda x: (x[0], x[1], x[2]))
    data = bytearray()
    last_tick = 0
    for tick, _priority, payload in normalized:
        delta = max(0, tick - last_tick)
        data.extend(_vlq(delta))
        data.extend(payload)
        last_tick = tick
    data.extend(_vlq(0))
    data.extend(b"\xFF\x2F\x00")
    return b"MTrk" + len(data).to_bytes(4, "big") + bytes(data)


def _program_change(channel: int, program: int) -> tuple[int, int, bytes]:
    return (0, _MIDI_PRIORITY_PROGRAM, bytes([0xC0 | channel, max(0, min(127, int(program)))]))


def _control_change(channel: int, controller: int, value: int) -> bytes:
    return bytes([0xB0 | channel, max(0, min(127, int(controller))), max(0, min(127, int(value)))])


def write_midi(
    note_events: list[NoteEvent],
    output_path: Path,
    tempo_bpm: int = 120,
    pedal_events: Iterable[PedalEvent] | None = None,
) -> Path:
    """Write a small type-1 MIDI file with explicit per-track instruments.

    v2_3_9 keeps note rendering simple while adding an optional, explicit CC64
    boundary: expression pedal intent may be converted to ``PedalEvent`` objects
    before this writer is called.  The writer itself only serializes those
    already-decided events as MIDI controller 64 messages and does not infer
    pedal from articulation, duration, style, or track names.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)
    header = b"MThd" + (6).to_bytes(4, "big") + (1).to_bytes(2, "big") + (4).to_bytes(2, "big") + TPQ.to_bytes(2, "big")

    tempo_us = int(60_000_000 / tempo_bpm)
    meta_events: list[tuple[int, int, bytes]] = [
        (0, -100, b"\xFF\x51\x03" + tempo_us.to_bytes(3, "big")),
        (0, -90, b"\xFF\x58\x04\x04\x02\x18\x08"),
    ]

    piano_channel = CHANNELS["piano"]
    bass_channel = CHANNELS["bass"]
    drum_channel = CHANNELS["drums"]
    track_events: dict[int, list[tuple[int, int, bytes]]] = {
        piano_channel: [_program_change(piano_channel, INSTRUMENT_PROGRAMS["piano"])],
        bass_channel: [_program_change(bass_channel, INSTRUMENT_PROGRAMS["bass"])],
        drum_channel: [],
    }

    for pedal in pedal_events or []:
        tick = int(round(float(pedal.beat) * TPQ))
        channel = int(pedal.channel)
        priority = _MIDI_PRIORITY_PEDAL_ON if int(pedal.value) >= 64 else _MIDI_PRIORITY_PEDAL_OFF
        track_events.setdefault(channel, [])
        track_events[channel].append((tick, priority, _control_change(channel, 64, int(pedal.value))))

    for ev in note_events:
        start = int(round(ev.start_beat * TPQ))
        end = int(round((ev.start_beat + ev.duration_beats) * TPQ))
        channel = ev.channel
        track_events.setdefault(channel, [])
        track_events[channel].append((start, _MIDI_PRIORITY_NOTE_ON, bytes([0x90 | channel, ev.note, ev.velocity])))
        track_events[channel].append((end, _MIDI_PRIORITY_NOTE_OFF, bytes([0x80 | channel, ev.note, 0])))

    chunks = [_track_chunk(meta_events)]
    chunks.append(_track_chunk(track_events.get(piano_channel, [])))
    chunks.append(_track_chunk(track_events.get(bass_channel, [])))
    chunks.append(_track_chunk(track_events.get(drum_channel, [])))
    output_path.write_bytes(header + b"".join(chunks))
    return output_path
