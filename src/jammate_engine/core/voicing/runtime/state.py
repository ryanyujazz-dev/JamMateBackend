from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VoicingState:
    """Runtime memory for sequential voicing selection.

    V2 keeps voicing as a core concern. A style may express a preference for
    register and density, but continuity from one harmonic event to the next is
    scored here in core/voicing, not in style pattern files.
    """

    previous_notes: tuple[int, ...] = ()
    previous_degrees: tuple[str, ...] = ()
    previous_top_note: int | None = None
    previous_low_note: int | None = None
    previous_chord_symbol: str | None = None
    previous_event_id: str | None = None
    previous_onset_beat: float | None = None
    previous_score_breakdown: dict[str, Any] = field(default_factory=dict)
    previous_selector_decision: dict[str, Any] = field(default_factory=dict)
    previous_recipe_id: str | None = None
    previous_functional_grouping: str | None = None
    previous_content_family: str | None = None
    recent_top_notes: tuple[int, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> "VoicingState":
        return cls()

    @property
    def has_previous(self) -> bool:
        return bool(self.previous_notes)

    def advance(
        self,
        *,
        event_id: str,
        chord_symbol: str,
        notes: list[int] | tuple[int, ...],
        degrees: list[str] | tuple[str, ...],
        onset_beat: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "VoicingState":
        ordered = tuple(sorted(int(note) for note in notes))
        top = max(ordered) if ordered else None
        low = min(ordered) if ordered else None
        event_metadata = dict(metadata or {})
        recent_top_notes = self.recent_top_notes
        if top is not None:
            recent_top_notes = (*recent_top_notes, top)[-8:]
        return VoicingState(
            previous_notes=ordered,
            previous_degrees=tuple(degrees),
            previous_top_note=top,
            previous_low_note=low,
            previous_chord_symbol=chord_symbol,
            previous_event_id=event_id,
            previous_onset_beat=onset_beat,
            previous_score_breakdown=dict(event_metadata.get("score_breakdown", {})),
            previous_selector_decision=dict(event_metadata.get("selector_decision", {})),
            previous_recipe_id=event_metadata.get("recipe_id"),
            previous_functional_grouping=event_metadata.get("functional_grouping"),
            previous_content_family=event_metadata.get("content_family"),
            recent_top_notes=recent_top_notes,
            metadata=event_metadata,
        )

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "previous_notes": list(self.previous_notes),
            "previous_degrees": list(self.previous_degrees),
            "previous_top_note": self.previous_top_note,
            "previous_low_note": self.previous_low_note,
            "previous_chord_symbol": self.previous_chord_symbol,
            "previous_event_id": self.previous_event_id,
            "previous_onset_beat": self.previous_onset_beat,
            "previous_score_breakdown": dict(self.previous_score_breakdown),
            "previous_selector_decision": dict(self.previous_selector_decision),
            "previous_recipe_id": self.previous_recipe_id,
            "previous_functional_grouping": self.previous_functional_grouping,
            "previous_content_family": self.previous_content_family,
            "recent_top_notes": list(self.recent_top_notes),
            "metadata": dict(self.metadata),
        }
