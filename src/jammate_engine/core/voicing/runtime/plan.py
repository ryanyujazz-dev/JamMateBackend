from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VoicedNote:
    midi_note: int
    degree: str
    voice_role: str
    hand: str | None = None
    group_id: str | None = None

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "midi_note": int(self.midi_note),
            "degree": self.degree,
            "voice_role": self.voice_role,
            "hand": self.hand,
            "group_id": self.group_id,
        }


@dataclass(frozen=True)
class VoicingPlan:
    event_id: str
    chord_symbol: str
    notes: list[VoicedNote]
    projection_map: dict[str, list[int]] = field(default_factory=dict)
    groups: dict[str, list[int]] = field(default_factory=dict)
    content_family: str | None = None
    disposition: str | None = None
    root_support: str | None = None
    bass_relation: str | None = None
    interval_structure: str | None = None
    root_included: bool = False
    density: int | None = None
    functional_grouping: str | None = None
    recipe_id: str | None = None
    group_roles: list[str] = field(default_factory=list)
    root_support_decision: dict[str, Any] = field(default_factory=dict)
    disposition_guard: dict[str, Any] = field(default_factory=dict)
    register_guard: dict[str, Any] = field(default_factory=dict)
    voice_leading_profile: dict[str, Any] = field(default_factory=dict)
    selector_decision: dict[str, Any] = field(default_factory=dict)
    ensemble_role: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.density is None:
            object.__setattr__(self, "density", len(self.notes))

    @property
    def midi_notes(self) -> list[int]:
        return [note.midi_note for note in self.notes]

    @property
    def degrees(self) -> list[str]:
        return [note.degree for note in self.notes]

    @property
    def voice_roles(self) -> list[str]:
        return [note.voice_role for note in self.notes]

    def to_debug_dict(self) -> dict[str, Any]:
        """Return the public voicing result contract for diagnostics.

        VoicingPlan is the boundary object returned by core/voicing. Downstream
        realization may project these voices over time, but should not re-decide
        vertical note content or voice-leading.
        """

        return {
            "event_id": self.event_id,
            "chord_symbol": self.chord_symbol,
            "notes": [note.to_debug_dict() for note in self.notes],
            "midi_notes": self.midi_notes,
            "degrees": self.degrees,
            "voice_roles": self.voice_roles,
            "projection_map": {key: list(value) for key, value in self.projection_map.items()},
            "groups": {key: list(value) for key, value in self.groups.items()},
            "content_family": self.content_family,
            "disposition": self.disposition,
            "root_support": self.root_support,
            "bass_relation": self.bass_relation,
            "interval_structure": self.interval_structure,
            "root_included": self.root_included,
            "density": self.density,
            "functional_grouping": self.functional_grouping,
            "recipe_id": self.recipe_id,
            "group_roles": list(self.group_roles),
            "root_support_decision": dict(self.root_support_decision),
            "disposition_guard": dict(self.disposition_guard),
            "register_guard": dict(self.register_guard),
            "voice_leading_profile": dict(self.voice_leading_profile),
            "selector_decision": dict(self.selector_decision),
            "ensemble_role": self.ensemble_role,
            "metadata": dict(self.metadata),
        }
