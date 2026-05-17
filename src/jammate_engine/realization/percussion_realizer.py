from __future__ import annotations

from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from .note_event_builder import NoteEvent

DRUM_NOTES = {
    "ride": 51,
    "ride_bell": 53,
    "hihat": 42,
    "hihat_pedal": 44,
    "kick": 36,
    "snare": 38,
}

DYNAMIC_VELOCITY = {
    "medium": 58,
    "soft": 54,
    "ghost": 45,
    "hat": 50,
    "accent": 70,
}

STROKE_DURATION = {
    "swing_time": 0.08,
    "short": 0.08,
    "choked": 0.05,
}


class PercussionRealizer:
    def realize(self, events: list[PatternEvent]) -> list[NoteEvent]:
        out: list[NoteEvent] = []
        for event in events:
            if event.status != "active" or event.track != "drums":
                continue
            drum = event.metadata.get("drum", "ride")
            dynamic_profile = str(event.metadata.get("dynamic_profile", "medium"))
            stroke_profile = str(event.metadata.get("stroke_profile", "short"))
            out.append(
                NoteEvent(
                    track="drums",
                    channel=9,
                    note=DRUM_NOTES.get(drum, 51),
                    velocity=DYNAMIC_VELOCITY.get(dynamic_profile, 55),
                    start_beat=event.onset_beat,
                    duration_beats=STROKE_DURATION.get(stroke_profile, 0.1),
                    timing_intent=str(event.metadata.get("timing_intent", "auto")),
                )
            )
        return out
