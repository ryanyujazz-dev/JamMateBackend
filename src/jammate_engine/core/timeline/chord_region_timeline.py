from __future__ import annotations

from dataclasses import dataclass

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.leadsheet.models import Leadsheet


@dataclass(frozen=True)
class ChordRegionTimeline:
    regions: list[HarmonicRegion]
    total_beats: float
    written_bars: int = 0
    performance_bars: int = 0
    choruses: int = 1


def build_chord_region_timeline(leadsheet: Leadsheet, choruses: int) -> ChordRegionTimeline:
    """Compile a V2 leadsheet into the chord-region-first runtime timeline."""

    bars = list(leadsheet.bars)
    flat: list[tuple[int, int, str, float, float]] = []
    for bar_i, bar in enumerate(bars):
        for chord_i, chord in enumerate(bar.chords):
            flat.append((bar_i, chord_i, chord.symbol, float(chord.beats), float(chord.beat)))

    beats_per_chorus = sum(float(bar.total_beats) for bar in bars)
    bar_offsets: list[float] = []
    running = 0.0
    for bar in bars:
        bar_offsets.append(running)
        running += float(bar.total_beats)

    section_last_bar_index: dict[str, int] = {}
    for bar_i, bar in enumerate(bars):
        if bar.section_id is not None:
            section_last_bar_index[str(bar.section_id)] = bar_i

    regions: list[HarmonicRegion] = []
    choruses = max(1, int(choruses))
    for chorus_i in range(choruses):
        chorus_offset = chorus_i * beats_per_chorus
        for idx, (bar_i, chord_i, symbol, beats, local_beat) in enumerate(flat):
            bar = bars[bar_i]
            previous_symbol = flat[(idx - 1) % len(flat)][2] if flat else None
            next_symbol = flat[(idx + 1) % len(flat)][2] if flat else None
            absolute_start = chorus_offset + bar_offsets[bar_i] + (local_beat - 1.0)
            section_id = str(bar.section_id) if bar.section_id is not None else None
            regions.append(
                HarmonicRegion(
                    region_id=f"c{chorus_i}_b{bar_i}_ch{chord_i}",
                    chord_symbol=symbol,
                    next_chord_symbol=next_symbol,
                    chorus_index=chorus_i,
                    total_choruses=choruses,
                    bar_index=bar_i,
                    chord_index=chord_i,
                    start_beat=absolute_start,
                    duration_beats=beats,
                    bar_local_start_beat=local_beat,
                    bar_local_end_beat=local_beat + beats,
                    section_id=section_id,
                    section_label=bar.section_label,
                    phrase=bar.phrase,
                    section_role=bar.role,
                    source_bar_index=bar.source_bar_index,
                    written_bar_index=bar.written_bar_index if bar.written_bar_index is not None else bar_i,
                    performance_bar_index=chorus_i * len(bars) + bar_i,
                    form_index=bar.form_index,
                    is_first_region_of_bar=chord_i == 0,
                    is_last_region_of_bar=chord_i == len(bar.chords) - 1,
                    is_first_bar_of_section=(bar.source_bar_index == 0),
                    is_last_bar_of_section=(section_id is not None and section_last_bar_index.get(section_id) == bar_i),
                    is_first_bar_of_chorus=bar_i == 0,
                    is_last_bar_of_chorus=bar_i == len(bars) - 1,
                    metadata={
                        **dict(bar.metadata),
                        "schema_version": leadsheet.schema_version,
                        "source_shape": leadsheet.metadata.get("source_shape"),
                        "home_key": leadsheet.key,
                        "key": leadsheet.key,
                        "previous_chord_symbol": previous_symbol,
                        "next_chord_symbol": next_symbol,
                        "performance_repetitions_live_in_request": True,
                    },
                )
            )
    return ChordRegionTimeline(
        regions=regions,
        total_beats=beats_per_chorus * choruses,
        written_bars=len(bars),
        performance_bars=len(bars) * choruses,
        choruses=choruses,
    )
