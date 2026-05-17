from __future__ import annotations

from dataclasses import dataclass, field

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime import PatternEvent


@dataclass(frozen=True)
class BassTarget:
    region_id: str
    chord_symbol: str
    next_chord_symbol: str | None
    start_beat: float
    duration_beats: float

    @classmethod
    def from_region(cls, region: HarmonicRegion) -> "BassTarget":
        return cls(
            region_id=region.region_id,
            chord_symbol=region.chord_symbol,
            next_chord_symbol=region.next_chord_symbol,
            start_beat=region.start_beat,
            duration_beats=region.duration_beats,
        )


@dataclass(frozen=True)
class Beat4Choice:
    note: int
    kind: str
    weight: float
    description: str


@dataclass(frozen=True)
class BassFoundationPlan:
    events: list[PatternEvent]
    selected_candidates: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

