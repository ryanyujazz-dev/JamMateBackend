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
            note = _resolve_note_for_event(event, previous_note=previous_note)
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
        "bossa_root": 1.32,
        "bossa_root_with_pickup": 1.08,
        "bossa_fifth": 1.08,
        "bossa_fifth_pickup_2and": 0.36,
        "bossa_fifth_before_next_root": 1.18,
        "bossa_split_root": 1.12,
        "bossa_short_root": 0.78,
        "bossa_next_root_anticipation": 0.36,
    }
    return mapping.get(length_profile, 0.96)


def _resolve_note_for_event(event: PatternEvent, *, previous_note: int | None) -> int:
    resolved_note = event.metadata.get("resolved_midi_note")
    if resolved_note is not None:
        return int(resolved_note)

    token = event.metadata.get("degree", "R")
    next_chord_symbol = event.metadata.get("next_chord_symbol")
    resolution = resolve_bass_degree_token(
        chord_symbol=event.chord_symbol,
        token=str(token),
        next_chord_symbol=str(next_chord_symbol) if next_chord_symbol else None,
    )
    low = int(event.metadata.get("register_low", 26))
    high = int(event.metadata.get("register_high", 48))
    prefer_floor = 38 if event.local_beat in {0.0, None} else None
    note = pitch_class_to_register_note(
        resolution.pitch_class,
        low=low,
        high=high,
        previous_note=previous_note,
        prefer_downbeat_floor=prefer_floor,
    )
    policy = str(event.metadata.get("bossa_bass_register_policy") or "")
    if not policy:
        return note

    # v2_6_109 keeps Bossa register shaping inside the existing bass realizer:
    # pattern metadata only names the policy; concrete octave choices still live
    # here.  Main fifths should stay smooth and light, and may repeat the prior
    # root when a fifth projection would cause a wide leap or muddy low-register
    # jump.  Pickups and next-root anticipations use nearest continuity instead.
    if policy == "main_fifth_nearest_with_root_repeat_fallback" and previous_note is not None:
        if abs(note - previous_note) > 7 or note < 31:
            return previous_note
    if policy == "root_stable_floor" and event.local_beat in {0.0, None} and note < 38:
        lifted = pitch_class_to_register_note(
            resolution.pitch_class,
            low=38,
            high=high,
            previous_note=None,
            prefer_downbeat_floor=38,
        )
        return lifted if low <= lifted <= high else note
    return note


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
        "bossa_root": 60,
        "bossa_root_answer": 59,
        "bossa_fifth": 54,
        "bossa_fifth_answer": 53,
        "bossa_fifth_pickup": 49,
        "bossa_fifth_pickup_lift": 51,
        "bossa_next_root_lift": 55,
        "bossa_split_root": 58,
        "bossa_short_root": 56,
        "bossa_next_root": 53,
        "bossa_root_soft": 56,
        "bossa_fifth_soft": 50,
        "bossa_split_root_soft": 54,
        "bossa_short_root_soft": 52,
        "bossa_root_release": 54,
        "bossa_fifth_release": 48,
        "bossa_split_root_release": 52,
        "bossa_short_root_release": 50,
        "bossa_root_lift": 63,
        "bossa_fifth_lift": 57,
        "bossa_split_root_lift": 61,
        "bossa_short_root_lift": 59,
    }
    return mapping.get(dynamic_profile, 68)
