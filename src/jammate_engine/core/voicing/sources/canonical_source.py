from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jammate_engine.core.harmony.material import degree_to_semitone


@dataclass(frozen=True)
class CanonicalClosedSource:
    """Canonical compact source before disposition transforms.

    This is a debug/architecture contract first: higher-density voicings should
    define a stable compact source, then derive orientation/inversion/drop/open
    candidates under a VoicingTexturePlan.  The current rootless A/B pass keeps
    compact-rootless as the active family and does not yet enable broad drop2
    generation.
    """

    degree_order: tuple[str, ...]
    semitone_order: tuple[int, ...]
    source_kind: str = "canonical_closed_position_source"
    derives_disposition_candidates: bool = True

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "source_kind": self.source_kind,
            "degree_order": list(self.degree_order),
            "semitone_order": list(self.semitone_order),
            "derives_disposition_candidates": bool(self.derives_disposition_candidates),
            "not_a_final_random_disposition": True,
        }


def canonical_closed_source_from_degrees(degrees: list[tuple[str, int]] | tuple[tuple[str, int], ...]) -> CanonicalClosedSource:
    """Return a compact source seed preserving the content recipe order.

    The content recipe order is the tuned musical source order for the current
    family.  For rootless A/B, that means A or B orientation order; future drop2
    or open variants must derive from this source under texture-plan control.
    """

    degree_order = tuple(str(degree) for degree, _ in degrees)
    semitone_order: list[int] = []
    previous: int | None = None
    for degree, fallback in degrees:
        try:
            offset = int(degree_to_semitone(str(degree), stacked=False))
        except Exception:
            offset = int(fallback)
        while previous is not None and offset <= previous:
            offset += 12
        semitone_order.append(offset)
        previous = offset
    return CanonicalClosedSource(degree_order=degree_order, semitone_order=tuple(semitone_order))
