from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..policy import BassRelation, ContentFamily, Disposition, FunctionalGrouping, IntervalStructure, RootSupportPolicy, VoicingGroupRole


@dataclass(frozen=True)
class VoicingCandidate:
    notes: list[int]
    degrees: list[str]
    score: float = 0.0
    content_family: ContentFamily | None = None
    root_support: RootSupportPolicy = RootSupportPolicy.ROOT_OPTIONAL
    bass_relation: BassRelation = BassRelation.ROOT_POSITION
    disposition: Disposition = Disposition.OPEN
    interval_structure: IntervalStructure = IntervalStructure.TERTIAN
    root_included: bool = False
    density: int = 0
    functional_grouping: FunctionalGrouping | None = None
    recipe_id: str | None = None
    group_roles: tuple[VoicingGroupRole, ...] = ()
    root_support_decision: dict[str, Any] = field(default_factory=dict)
    disposition_guard: dict[str, Any] = field(default_factory=dict)
    register_guard: dict[str, Any] = field(default_factory=dict)
    voice_leading_profile: dict[str, Any] = field(default_factory=dict)
    selector_decision: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "notes", [int(note) for note in self.notes])
        object.__setattr__(self, "degrees", [str(degree) for degree in self.degrees])
        object.__setattr__(self, "density", len(self.notes))
        object.__setattr__(self, "root_included", "R" in self.degrees)
        object.__setattr__(self, "group_roles", tuple(self.group_roles))

    def to_debug_dict(self) -> dict[str, Any]:
        """Return a stable, JSON-friendly view of the candidate contract.

        This is intentionally metadata-only. It does not change selection or
        realization behavior; it gives tests, audit scripts, and future LLM
        tooling one public way to inspect the vertical voicing axes.
        """

        return {
            "notes": list(self.notes),
            "degrees": list(self.degrees),
            "score": float(self.score),
            "content_family": self.content_family.value if self.content_family else None,
            "root_support": self.root_support.value,
            "bass_relation": self.bass_relation.value,
            "disposition": self.disposition.value,
            "interval_structure": self.interval_structure.value,
            "root_included": self.root_included,
            "density": self.density,
            "functional_grouping": self.functional_grouping.value if self.functional_grouping else None,
            "recipe_id": self.recipe_id,
            "group_roles": [role.value if isinstance(role, VoicingGroupRole) else str(role) for role in self.group_roles],
            "root_support_decision": dict(self.root_support_decision),
            "disposition_guard": dict(self.disposition_guard),
            "register_guard": dict(self.register_guard),
            "voice_leading_profile": dict(self.voice_leading_profile),
            "selector_decision": dict(self.selector_decision),
            "metadata": dict(self.metadata),
        }
