from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TailPolicy:
    """Pitchless tail-space contract for anticipation and continuation layers.

    Beat numbers are local to a 4/4 region/bar convention used by the current
    v2 skeleton:
      - beat 4   -> local beat 3.0
      - beat 4&  -> local beat 3.5
    Future versions can generalize this for other meters without changing style
    pattern ownership.
    """

    beat4_available: bool = True
    beat4_and_available: bool = True
    can_receive_next_chord_anticipation: bool = True
    beat1_movable_by_previous_anticipation: bool = True
    occupied_local_beats: tuple[float, ...] = field(default_factory=tuple)
    notes: str = ""

    @staticmethod
    def from_local_beats(local_beats: tuple[float, ...], *, can_receive_next_chord_anticipation: bool = True) -> "TailPolicy":
        occupied = tuple(sorted(float(b) for b in local_beats))
        return TailPolicy(
            beat4_available=3.0 not in occupied,
            beat4_and_available=3.5 not in occupied,
            can_receive_next_chord_anticipation=can_receive_next_chord_anticipation,
            beat1_movable_by_previous_anticipation=0.0 in occupied,
            occupied_local_beats=occupied,
        )
