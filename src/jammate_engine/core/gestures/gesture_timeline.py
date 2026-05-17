from __future__ import annotations

from dataclasses import dataclass

from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent


@dataclass(frozen=True)
class GestureTimeline:
    events: list[PatternEvent]
