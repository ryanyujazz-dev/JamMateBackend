from __future__ import annotations

from jammate_engine.core.pattern_runtime import PatternCandidate, TailPolicy, event_spec


def _drum(name: str, dynamic: str) -> dict:
    return {"drum": name, "dynamic_profile": dynamic, "stroke_profile": "swing_time"}


def get_pattern_candidates(context: dict | None = None) -> tuple[PatternCandidate, ...]:
    """Medium swing drum ride candidates.

    Drum voice names are style/percussion roles, not MIDI note numbers. v2_0_9
    trims the event cell to the current harmonic-region duration so two-chord
    bars keep time without spilling events into the following region.
    """

    duration = float((context or {}).get("region_duration_beats", 4.0))
    if duration <= 2.0:
        return _two_beat_region_candidates()
    return _four_beat_region_candidates()


def _four_beat_region_candidates() -> tuple[PatternCandidate, ...]:
    return (
        PatternCandidate(
            name="medium_swing_drums_spang_a_lang_hat_2_4",
            weight=1.0,
            category="ride_time_foundation",
            events=(
                event_spec(track="drums", beat=0.0, role="drum", metadata=_drum("ride", "medium")),
                event_spec(track="drums", beat=1.0, role="drum", metadata=_drum("ride", "soft")),
                event_spec(track="drums", beat=1.6667, role="drum", metadata=_drum("ride", "ghost")),
                event_spec(track="drums", beat=2.0, role="drum", metadata=_drum("ride", "medium")),
                event_spec(track="drums", beat=3.0, role="drum", metadata=_drum("ride", "soft")),
                event_spec(track="drums", beat=3.6667, role="drum", metadata=_drum("ride", "ghost")),
                event_spec(track="drums", beat=1.0, role="drum", metadata=_drum("hihat_pedal", "hat")),
                event_spec(track="drums", beat=3.0, role="drum", metadata=_drum("hihat_pedal", "hat")),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0, 1.0, 1.6667, 2.0, 3.0, 3.6667), can_receive_next_chord_anticipation=False),
            tags=("swing", "drums", "ride", "spang_a_lang", "audible_v208"),
        ),
    )


def _two_beat_region_candidates() -> tuple[PatternCandidate, ...]:
    return (
        PatternCandidate(
            name="medium_swing_drums_two_beat_spang_fragment",
            weight=1.0,
            category="ride_time_two_chord_fragment",
            events=(
                event_spec(track="drums", beat=0.0, role="drum", metadata=_drum("ride", "medium")),
                event_spec(track="drums", beat=1.0, role="drum", metadata=_drum("ride", "soft")),
                event_spec(track="drums", beat=1.6667, role="drum", metadata=_drum("ride", "ghost")),
                event_spec(track="drums", beat=1.0, role="drum", metadata=_drum("hihat_pedal", "hat")),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0, 1.0, 1.6667), can_receive_next_chord_anticipation=False),
            tags=("swing", "drums", "ride", "two_chord_bar", "audible_v208"),
        ),
    )
