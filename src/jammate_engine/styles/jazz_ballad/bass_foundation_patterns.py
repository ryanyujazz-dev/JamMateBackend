from __future__ import annotations

from jammate_engine.core.pattern_runtime import PatternCandidate, TailPolicy, event_spec


def get_pattern_candidates(context: dict | None = None) -> tuple[PatternCandidate, ...]:
    """Jazz ballad bass foundation candidates."""

    return (
        PatternCandidate(
            name="ballad_bass_root_anchor",
            weight=1.0,
            category="root_anchor",
            events=(
                event_spec(track="bass", beat=0.0, role="bass_note", metadata={"degree": "root"}),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0,)),
            tags=("ballad", "bass", "root"),
        ),
    )
