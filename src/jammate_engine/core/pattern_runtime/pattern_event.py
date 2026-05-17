from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jammate_engine.core.gestures.gesture import GestureRequest, simultaneous_onset


@dataclass(frozen=True)
class PatternEvent:
    """A pitchless event produced by style-owned pattern planning.

    PatternEvent intentionally contains no MIDI pitch, final duration, final
    velocity, pedal value, or concrete voicing notes. It may carry a
    GestureRequest, but that request is still pitchless and only describes how
    later core stages should project voiced material.
    """

    event_id: str
    track: str
    region_id: str
    chord_symbol: str
    onset_beat: float
    role: str
    gesture_type: str = "simultaneous_onset"
    gesture: GestureRequest = field(default_factory=simultaneous_onset)
    expression_hint: str | None = None
    status: str = "active"
    source_event_id: str | None = None
    pattern_id: str | None = None
    local_beat: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.gesture_type != self.gesture.gesture_type:
            object.__setattr__(self, "gesture_type", self.gesture.gesture_type)


PitchlessEvent = PatternEvent
