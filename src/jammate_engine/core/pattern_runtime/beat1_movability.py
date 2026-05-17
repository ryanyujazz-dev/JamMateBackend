from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Beat1Movability:
    """Contract for whether a region's first event may be anticipated by the previous region.

    This stays pitchless. It only tells the AnticipationResolver whether the first
    harmonic event can be moved earlier, and under what timeline conditions.
    """

    movable: bool = True
    requires_previous_tail_space: bool = True
    target_offset_beats: float = -0.5
    suppress_original: bool = True
    tie_from_previous: bool = True
    reason: str = "default_movable_beat1"
