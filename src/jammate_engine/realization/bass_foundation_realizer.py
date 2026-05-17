from __future__ import annotations

from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from .bass_degree_resolver import pitch_class_to_register_note, resolve_bass_degree_token
from .note_event_builder import NoteEvent


class BassFoundationRealizer:
    """Resolve pitchless bass-foundation degree events into a basic acoustic bass line.

    Styles may provide abstract degree tokens only. This core realizer maps
    those tokens to chord/next-root pitch classes, chooses a bass-register
    octave, and applies modest continuity. It intentionally does not own style
    pattern selection.
    """

    def realize(self, events: list[PatternEvent]) -> list[NoteEvent]:
        out: list[NoteEvent] = []
        previous_note: int | None = None
        for event in sorted(events, key=lambda e: (e.onset_beat, e.event_id)):
            if event.status != "active" or event.track != "bass":
                continue
            resolved_note = event.metadata.get("resolved_midi_note")
            if resolved_note is not None:
                note = int(resolved_note)
            else:
                token = event.metadata.get("degree", "R")
                next_chord_symbol = event.metadata.get("next_chord_symbol")
                resolution = resolve_bass_degree_token(
                    chord_symbol=event.chord_symbol,
                    token=str(token),
                    next_chord_symbol=str(next_chord_symbol) if next_chord_symbol else None,
                )
                prefer_floor = 38 if event.local_beat in {0.0, None} else None
                note = pitch_class_to_register_note(
                    resolution.pitch_class,
                    low=int(event.metadata.get("register_low", 26)),
                    high=int(event.metadata.get("register_high", 48)),
                    previous_note=previous_note,
                    prefer_downbeat_floor=prefer_floor,
                )
            previous_note = note
            length_profile = str(event.metadata.get("length_profile", "walking_quarter"))
            dynamic_profile = str(event.metadata.get("dynamic_profile", "downbeat" if event.local_beat == 0.0 else "walk"))
            out.append(
                NoteEvent(
                    track="bass",
                    channel=1,
                    note=note,
                    velocity=_velocity_for(dynamic_profile),
                    start_beat=event.onset_beat,
                    duration_beats=_duration_for(length_profile),
                    timing_intent=str(event.metadata.get("timing_intent", "auto")),
                )
            )
        return out


def _duration_for(length_profile: str) -> float:
    mapping = {
        "walking_quarter": 0.92,
        "two_feel_half": 1.72,
        "short_pickup": 0.55,
        "classic_fill_quarter": 0.88,
        "classic_fill_syncopated_sustain": 1.45,
        "classic_fill_upbeat": 0.48,
        "classic_fill_connector": 0.82,
    }
    return mapping.get(length_profile, 0.96)


def _velocity_for(dynamic_profile: str) -> int:
    mapping = {
        "downbeat": 74,
        "walk": 68,
        "connector": 67,
        "light": 62,
        "accent": 78,
        "classic_fill": 70,
        "classic_fill_accent": 76,
        "classic_fill_chromatic": 69,
    }
    return mapping.get(dynamic_profile, 68)
