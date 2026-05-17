from __future__ import annotations

from jammate_engine.core.pattern_runtime import PatternCandidate


def get_pattern_candidates(context: dict | None = None) -> tuple[PatternCandidate, ...]:
    """Jazz ballad drum placeholder candidates.

    The current clean skeleton keeps ballad drums silent rather than faking brush
    detail before the brush-expression layer exists.
    """

    return ()
