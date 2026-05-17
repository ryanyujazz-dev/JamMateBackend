from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class HarmonicRegion:
    region_id: str
    chord_symbol: str
    next_chord_symbol: str | None
    chorus_index: int
    bar_index: int
    chord_index: int
    start_beat: float
    duration_beats: float
    total_choruses: int = 1
    bar_local_start_beat: float | None = None
    bar_local_end_beat: float | None = None
    section_id: str | None = None
    section_label: str | None = None
    phrase: str | None = None
    section_role: str | None = None
    source_bar_index: int | None = None
    written_bar_index: int | None = None
    performance_bar_index: int | None = None
    form_index: int | None = None
    is_first_region_of_bar: bool = False
    is_last_region_of_bar: bool = False
    is_first_bar_of_section: bool = False
    is_last_bar_of_section: bool = False
    is_first_bar_of_chorus: bool = False
    is_last_bar_of_chorus: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
