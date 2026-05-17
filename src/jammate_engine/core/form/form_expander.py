from __future__ import annotations

from jammate_engine.core.leadsheet.models import ExpandedBar, Leadsheet
from jammate_engine.core.timeline.chord_region_timeline import ChordRegionTimeline, build_chord_region_timeline


def expand_leadsheet_to_written_bars(leadsheet: Leadsheet) -> list[ExpandedBar]:
    """Return written-form bars before GenerationRequest chorus repetition."""

    return leadsheet.expanded_bars()


def expand_form_to_regions(leadsheet: Leadsheet, choruses: int) -> ChordRegionTimeline:
    return build_chord_region_timeline(leadsheet, choruses=choruses)
