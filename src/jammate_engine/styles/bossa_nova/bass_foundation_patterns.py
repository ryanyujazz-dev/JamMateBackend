from __future__ import annotations

from jammate_engine.core.pattern_runtime import PatternCandidate, TailPolicy, event_spec


def get_pattern_candidates(context: dict | None = None) -> tuple[PatternCandidate, ...]:
    """Bossa Nova bass foundation candidates.

    Relative degree metadata remains pitchless and is resolved by core later.
    """

    return (
        PatternCandidate(
            name="bossa_bass_root_fifth_half_note_foundation",
            weight=1.0,
            category="root_fifth_foundation",
            events=(
                event_spec(track="bass", beat=0.0, role="bass_note", metadata={"degree": "root"}),
                event_spec(track="bass", beat=2.0, role="bass_note", metadata={"degree": "fifth"}),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0, 2.0)),
            tags=("bossa", "bass", "root_fifth"),
        ),
    )
