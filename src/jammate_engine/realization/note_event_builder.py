from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NoteEvent:
    track: str
    channel: int
    note: int
    velocity: int
    start_beat: float
    duration_beats: float
    # Logical timing intent is interpreted by midi/render_pipeline.py before
    # midi_writer.py receives concrete performed beat positions. Keep this out
    # of style pattern libraries: patterns write musical grid, timing policy
    # decides how the grid is performed.
    timing_intent: str = "auto"
    # Projection metadata is diagnostic only.  It lets later gesture/expression
    # passes inspect which already-resolved voicing voice/group produced this
    # event without reselecting pitch content.  MIDI rendering intentionally
    # ignores these fields.
    voice_role: str | None = None
    group_id: str | None = None
    projection_ref: str | None = None
    voicing_event_id: str | None = None
    # Timing metadata is diagnostic only. Renderer timing may populate these
    # fields after applying style timing/humanization policy. MIDI writer only
    # consumes the final start_beat, duration_beats, velocity, note, channel.
    logical_start_beat: float | None = None
    timing_grid_offset_beats: float = 0.0
    humanization_offset_beats: float = 0.0
    timing_policy_version: str | None = None
    timing_profile: str | None = None
    timing_debug: dict[str, Any] = field(default_factory=dict)
    # Expression/pedal metadata is carried to the MIDI boundary for audit and
    # optional CC64 realization. It remains diagnostic for note pitch/timing;
    # note rendering still consumes only track/channel/note/velocity/start/duration.
    expression_event_id: str | None = None
    pedal: str = "none"
    release_beats: float = 0.0
    pedal_debug: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PedalEvent:
    track: str
    channel: int
    value: int
    beat: float
    timing_intent: str = "auto"
