from __future__ import annotations

from jammate_engine.core.roles import EnsembleContext
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent

from .bass_degree_resolver import pitch_class_to_register_note, resolve_bass_degree_token
from .note_event_builder import NoteEvent


class PianoLHBassFoundationRealizer:
    """Realize bass-pattern events as piano left-hand bass foundation.

    This is the formal V2 alternative to the old shortcut of stuffing the root
    into every piano chord when no bass player is present. The source events are
    still style-owned pitchless bass foundation patterns; only the final instrument role and
    register are changed here.

    Important harness rule:
        Do not reimplement bass-degree parsing in this file. Piano LH bass uses
        the same core resolver as bass-track realization so tokens such as ``R``,
        ``root``, ``5`` and ``nextR`` stay consistent across ensemble modes.
    """

    def realize(self, events: list[PatternEvent], ensemble: EnsembleContext | dict | None = None) -> list[NoteEvent]:
        context = EnsembleContext.from_dict(ensemble)
        if not context.needs_piano_lh_bass_foundation:
            return []

        out: list[NoteEvent] = []
        previous_note: int | None = None
        active_events = [event for event in events if event.status == "active" and event.track == "bass"]

        for index, event in enumerate(active_events):
            next_chord_symbol = None
            if index + 1 < len(active_events):
                next_chord_symbol = active_events[index + 1].chord_symbol

            token = event.metadata.get("degree", "R")
            resolution = resolve_bass_degree_token(
                chord_symbol=event.chord_symbol,
                token=token,
                next_chord_symbol=next_chord_symbol,
            )
            note = pitch_class_to_register_note(
                resolution.pitch_class,
                low=context.piano_lh_low,
                high=context.piano_lh_high,
                previous_note=previous_note,
            )
            previous_note = note

            out.append(
                NoteEvent(
                    track="piano_lh_bass_foundation",
                    channel=context.piano_channel,
                    note=note,
                    velocity=68,
                    start_beat=event.onset_beat,
                    duration_beats=0.95,
                    timing_intent=str(event.metadata.get("timing_intent", "auto")),
                )
            )
        return out
