from __future__ import annotations

from typing import Any

from .open import place_generic_open_projection
from .placement_utils import Degree, PlacedDegree, place_stack
from .spread import (
    place_foundation_projection,
    place_lower_upper_grouped_projection,
    place_root_10th_projection,
)
from ..policy import Disposition, VoicingPolicy


def place_degree_notes(
    root_pc: int,
    degrees: list[Degree],
    low: int,
    high: int,
    disposition: Disposition = Disposition.OPEN,
    policy: VoicingPolicy | None = None,
) -> list[PlacedDegree]:
    """Disposition placement facade for existing disposition inputs.

    The implementation delegates to the family-specific disposition projection
    modules while preserving a single diagnostic entry point for tests and
    explicit placement audits. Runtime candidate generation should prefer
    ``core.voicing.disposition.projection``.
    """

    policy = policy or VoicingPolicy()
    if not degrees:
        return []
    if not isinstance(disposition, Disposition):
        disposition = Disposition(str(disposition))
    if disposition in {Disposition.LEFT_ROOT_RIGHT_CHORD, Disposition.LEFT_ROOT_RIGHT_ROOTLESS}:
        return place_foundation_projection(root_pc, degrees, policy)
    if disposition == Disposition.OPEN_ROOT_10TH:
        return place_root_10th_projection(root_pc, degrees, policy)
    if disposition == Disposition.CLOSED:
        return place_stack(root_pc, degrees, low, high, target_low=max(int(low), 56), spread_upper_voices=False)
    if disposition in {Disposition.SPREAD, Disposition.TWO_HAND_SPREAD}:
        return place_lower_upper_grouped_projection(root_pc, degrees, low, high, policy)
    return place_generic_open_projection(root_pc, degrees, low, high, policy)


def place_degrees(
    root_pc: int,
    degrees: list[Degree],
    low: int,
    high: int,
    disposition: Disposition = Disposition.OPEN,
    policy: VoicingPolicy | None = None,
) -> list[int]:
    return [note for _, note in place_degree_notes(root_pc, degrees, low, high, disposition, policy)]



def describe_disposition_placement(
    placed: list[PlacedDegree],
    disposition: Disposition,
    policy: VoicingPolicy,
) -> dict[str, Any]:
    """Return a stable debug contract for disposition/register placement.

    The core describes abstract functional groups elsewhere; the legacy hand
    ranges here are only instrument-specific register hints for the current
    piano realization path.  v2_2_4 keeps this diagnostic helper as the sole
    compatibility reason for this module.
    """

    if not isinstance(disposition, Disposition):
        disposition = Disposition(str(disposition))
    notes = [int(note) for _, note in placed]
    degrees = [str(degree) for degree, _ in placed]
    return {
        "disposition": disposition.value,
        "placed_degrees": degrees,
        "placed_notes": notes,
        "register_low": int(policy.register_low),
        "register_high": int(policy.register_high),
        "left_range_hint": [int(policy.left_hand_low), int(policy.left_hand_high)],
        "right_range_hint": [int(policy.right_hand_low), int(policy.right_hand_high)],
        "uses_split_register_hints": disposition
        in {Disposition.SPREAD, Disposition.TWO_HAND_SPREAD, Disposition.LEFT_ROOT_RIGHT_CHORD, Disposition.LEFT_ROOT_RIGHT_ROOTLESS, Disposition.OPEN_ROOT_10TH},
        "legacy_hand_hints_only": True,
        "core_grouping_is_abstract": True,
        "placement_algorithm_owner": "core.voicing.disposition",
        "disposition_planner_role": "placement_facade_and_debug_contract",
    }
