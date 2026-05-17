from __future__ import annotations

from jammate_engine.core.pattern_runtime import PatternCandidate, TailPolicy, event_spec


def get_pattern_candidates(context: dict | None = None) -> tuple[PatternCandidate, ...]:
    """Bossa Nova drum placeholder candidates."""

    return (
        PatternCandidate(
            name="bossa_drums_hihat_2_4_placeholder",
            weight=1.0,
            category="light_time_placeholder",
            events=(
                event_spec(track="drums", beat=1.0, role="drum", metadata={"drum": "hihat"}),
                event_spec(track="drums", beat=3.0, role="drum", metadata={"drum": "hihat"}),
            ),
            tail_policy=TailPolicy.from_local_beats((1.0, 3.0), can_receive_next_chord_anticipation=False),
            tags=("bossa", "drums", "placeholder"),
        ),
    )
