from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


VOICING_STATE_ADVANCE_ANCHOR_HELPER_VERSION = "v2_6_37"


def _int_tuple(values: Sequence[Any] | None) -> tuple[int, ...]:
    return tuple(int(value) for value in (values or ()))


def _str_tuple(values: Sequence[Any] | None) -> tuple[str, ...]:
    return tuple(str(value) for value in (values or ()))


@dataclass(frozen=True)
class VoicingStateAdvanceAnchor:
    """Separate the realized notes from the phrase-state continuity anchor.

    Most voicing events should advance continuity state from their realized notes.
    A small class of phrase-scope repairs, such as the Ballad SPREAD wide-gap
    fix, intentionally realizes a safer current voicing while keeping the
    original phrase anchor for the next event's voice-leading state.  This helper
    centralizes that contract so selector code only declares the anchor and the
    resolver consumes one stable runtime surface.
    """

    notes: tuple[int, ...]
    degrees: tuple[str, ...] = ()
    lower_group_notes: tuple[int, ...] = ()
    upper_group_notes: tuple[int, ...] = ()
    upper_group_degrees: tuple[str, ...] = ()
    lower_group_placed_degrees: tuple[str, ...] = ()
    group_gap_semitones: int | float | None = None
    reason: str = ""

    @classmethod
    def from_metadata(cls, metadata: Mapping[str, Any]) -> "VoicingStateAdvanceAnchor | None":
        data = dict(metadata or {})
        notes = data.get("voicing_state_advance_anchor_notes") or data.get("voicing_state_advance_override_notes")
        if not notes:
            return None
        return cls(
            notes=_int_tuple(notes),
            degrees=_str_tuple(data.get("voicing_state_advance_anchor_degrees") or data.get("voicing_state_advance_override_degrees")),
            lower_group_notes=_int_tuple(data.get("voicing_state_advance_anchor_lower_group_notes") or data.get("voicing_state_advance_override_lower_group_notes")),
            upper_group_notes=_int_tuple(data.get("voicing_state_advance_anchor_upper_group_notes") or data.get("voicing_state_advance_override_upper_group_notes")),
            upper_group_degrees=_str_tuple(data.get("voicing_state_advance_anchor_upper_group_degrees") or data.get("voicing_state_advance_override_upper_group_degrees")),
            lower_group_placed_degrees=_str_tuple(data.get("voicing_state_advance_anchor_lower_group_placed_degrees") or data.get("voicing_state_advance_override_lower_group_placed_degrees")),
            group_gap_semitones=data.get("voicing_state_advance_anchor_group_gap_semitones", data.get("voicing_state_advance_override_group_gap_semitones")),
            reason=str(data.get("voicing_state_advance_anchor_reason") or data.get("spread_phrase_scope_wide_gap_reason") or ""),
        )

    def to_metadata(self) -> dict[str, Any]:
        """Return new v2_6_37 fields plus legacy aliases for older audits/tests."""

        data: dict[str, Any] = {
            "voicing_state_advance_anchor_helper_version": VOICING_STATE_ADVANCE_ANCHOR_HELPER_VERSION,
            "voicing_state_advance_anchor_enabled": True,
            "voicing_state_advance_anchor_notes": list(self.notes),
            "voicing_state_advance_anchor_degrees": list(self.degrees),
            "voicing_state_advance_anchor_reason": self.reason,
            # Legacy aliases retained so existing audit rows and focused tests do
            # not need to understand the new helper name immediately.
            "voicing_state_advance_override_notes": list(self.notes),
            "voicing_state_advance_override_degrees": list(self.degrees),
        }
        if self.lower_group_notes:
            data["voicing_state_advance_anchor_lower_group_notes"] = list(self.lower_group_notes)
            data["voicing_state_advance_override_lower_group_notes"] = list(self.lower_group_notes)
        if self.upper_group_notes:
            data["voicing_state_advance_anchor_upper_group_notes"] = list(self.upper_group_notes)
            data["voicing_state_advance_override_upper_group_notes"] = list(self.upper_group_notes)
        if self.upper_group_degrees:
            data["voicing_state_advance_anchor_upper_group_degrees"] = list(self.upper_group_degrees)
            data["voicing_state_advance_override_upper_group_degrees"] = list(self.upper_group_degrees)
        if self.lower_group_placed_degrees:
            data["voicing_state_advance_anchor_lower_group_placed_degrees"] = list(self.lower_group_placed_degrees)
            data["voicing_state_advance_override_lower_group_placed_degrees"] = list(self.lower_group_placed_degrees)
        if self.group_gap_semitones is not None:
            data["voicing_state_advance_anchor_group_gap_semitones"] = self.group_gap_semitones
            data["voicing_state_advance_override_group_gap_semitones"] = self.group_gap_semitones
        return data

    def to_state_metadata(self, fallback: Mapping[str, Any]) -> dict[str, Any]:
        """Overlay anchor group state onto the resolver's state metadata."""

        data = dict(fallback or {})
        if self.lower_group_notes:
            data["lower_group_notes"] = list(self.lower_group_notes)
        if self.upper_group_notes:
            data["upper_group_notes"] = list(self.upper_group_notes)
        if self.upper_group_degrees:
            data["upper_group_degrees"] = list(self.upper_group_degrees)
        if self.lower_group_placed_degrees:
            data["lower_group_placed_degrees"] = list(self.lower_group_placed_degrees)
        if self.group_gap_semitones is not None:
            data["group_gap_semitones"] = self.group_gap_semitones
        data["state_advance_anchor_helper_version"] = VOICING_STATE_ADVANCE_ANCHOR_HELPER_VERSION
        data["state_advance_anchor_enabled"] = True
        data["state_advance_anchor_notes"] = list(self.notes)
        data["state_advance_anchor_reason"] = self.reason
        return data


def state_advance_anchor_from_candidate_metadata(metadata: Mapping[str, Any]) -> VoicingStateAdvanceAnchor | None:
    return VoicingStateAdvanceAnchor.from_metadata(metadata)


def state_advance_notes_and_degrees(
    *,
    metadata: Mapping[str, Any],
    realized_notes: Sequence[int],
    realized_degrees: Sequence[str],
) -> tuple[tuple[int, ...], tuple[str, ...], VoicingStateAdvanceAnchor | None]:
    anchor = state_advance_anchor_from_candidate_metadata(metadata)
    if anchor is None:
        return _int_tuple(realized_notes), _str_tuple(realized_degrees), None
    return anchor.notes, (anchor.degrees or _str_tuple(realized_degrees)), anchor


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
