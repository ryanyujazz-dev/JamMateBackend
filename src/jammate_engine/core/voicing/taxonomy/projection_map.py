from __future__ import annotations

from enum import Enum
from typing import Iterable

from ..policy import FunctionalGrouping, VoicingGroupRole


_GROUP_KEY_BY_ROLE = {
    VoicingGroupRole.ANCHOR: "anchor_group",
    VoicingGroupRole.FOUNDATION: "foundation_group",
    VoicingGroupRole.SUPPORT: "support_group",
    VoicingGroupRole.PROJECTION: "projection_group",
    VoicingGroupRole.COLOR: "color_group",
    VoicingGroupRole.MOTION: "motion_group",
    VoicingGroupRole.EXTENSION: "extension_group",
}


ABSTRACT_GROUP_KEYS = tuple(_GROUP_KEY_BY_ROLE.values())


def build_projection_map(
    notes: list[int],
    functional_grouping: FunctionalGrouping | str | None = None,
    group_roles: Iterable[VoicingGroupRole | str] | None = None,
) -> dict[str, list[int]]:
    """Build stable voice-reference keys for realization and future gestures.

    The core semantic keys are abstract group references such as
    ``support_group`` and ``projection_group``.  The older ``left_hand`` /
    ``right_hand`` keys remain compatibility hints for existing piano
    realization; they are not the canonical grouping model.
    """

    if not notes:
        return {}

    mapping = _build_positional_projection_map(notes)
    grouping = _coerce_grouping(functional_grouping)
    roles = _coerce_group_roles(group_roles)
    if grouping and roles:
        mapping.update(_build_abstract_group_map(len(notes), grouping, roles))
    return mapping


def group_indices_for_projection(
    note_count: int,
    functional_grouping: FunctionalGrouping | str | None,
    group_roles: Iterable[VoicingGroupRole | str] | None,
) -> dict[str, list[int]]:
    """Return only abstract group projection indices.

    This helper is useful for tests, audit scripts, and VoicingPlan group
    metadata.  It intentionally avoids hand-based naming.
    """

    if note_count <= 0:
        return {}
    grouping = _coerce_grouping(functional_grouping)
    roles = _coerce_group_roles(group_roles)
    if not grouping or not roles:
        return {}
    return _build_abstract_group_map(note_count, grouping, roles)


def _build_positional_projection_map(notes: list[int]) -> dict[str, list[int]]:
    mapping = {
        "all_voices": list(range(len(notes))),
        "lowest": [0],
        "top": [len(notes) - 1],
    }
    if len(notes) > 2:
        inner_indices = list(range(1, len(notes) - 1))
        mapping["inner"] = inner_indices
        for offset, index in enumerate(inner_indices, start=1):
            mapping[f"inner_{offset}"] = [index]
    if len(notes) >= 2:
        # Compatibility hints only.  Core grouping semantics use abstract group
        # keys such as foundation_group / projection_group, not LH/RH labels.
        mapping["left_hand"] = [idx for idx, note in enumerate(notes) if note <= 54] or [0]
        mapping["right_hand"] = [idx for idx, note in enumerate(notes) if note > 54] or list(range(1, len(notes))) or [0]
    return mapping


def _build_abstract_group_map(
    note_count: int,
    grouping: FunctionalGrouping,
    roles: tuple[VoicingGroupRole, ...],
) -> dict[str, list[int]]:
    partitions = _partition_indices(note_count, grouping, len(roles))
    if not partitions:
        return {}

    out: dict[str, list[int]] = {}
    for role, indices in zip(roles, partitions):
        key = _GROUP_KEY_BY_ROLE.get(role)
        if not key or not indices:
            continue
        out.setdefault(key, [])
        out[key].extend(indices)

    # Convenience aliases used by future gestures.  They remain abstract and do
    # not imply physical hands.
    if "anchor_group" in out and "foundation_group" not in out:
        out["foundation_group"] = list(out["anchor_group"])
    if "color_group" in out and "projection_group" not in out:
        out["projection_group"] = list(out["color_group"])
    if "extension_group" in out and "projection_group" not in out:
        out["projection_group"] = list(out["extension_group"])
    return {key: _dedupe_sorted_indices(value, note_count) for key, value in out.items()}


def _partition_indices(note_count: int, grouping: FunctionalGrouping, role_count: int) -> list[list[int]]:
    if note_count <= 0 or role_count <= 0:
        return []

    if grouping in {FunctionalGrouping.TWO, FunctionalGrouping.THREE} or role_count == 1:
        return [list(range(note_count))]

    first_size = {
        FunctionalGrouping.ONE_PLUS_THREE: 1,
        FunctionalGrouping.TWO_PLUS_TWO: 2,
        FunctionalGrouping.ONE_PLUS_FOUR: 1,
        FunctionalGrouping.TWO_PLUS_THREE: 2,
        FunctionalGrouping.TWO_PLUS_FOUR: 2,
        FunctionalGrouping.THREE_PLUS_THREE: 3,
        FunctionalGrouping.THREE_PLUS_FOUR: 3,
    }.get(grouping)
    if first_size is None:
        return [list(range(note_count))]

    first_size = max(1, min(first_size, note_count - 1)) if note_count > 1 else 1
    partitions = [list(range(0, first_size)), list(range(first_size, note_count))]

    if role_count <= 2:
        return partitions

    # Future-proof fallback: split the upper partition into additional adjacent
    # chunks if a later recipe exposes more than two abstract groups.
    while len(partitions) < role_count and len(partitions[-1]) > 1:
        tail = partitions.pop()
        partitions.append([tail[0]])
        partitions.append(tail[1:])
    return partitions[:role_count]


def _coerce_grouping(value: FunctionalGrouping | str | None) -> FunctionalGrouping | None:
    if isinstance(value, FunctionalGrouping):
        return value
    if value is None:
        return None
    try:
        return FunctionalGrouping(str(value))
    except ValueError:
        return None


def _coerce_group_roles(values: Iterable[VoicingGroupRole | str] | None) -> tuple[VoicingGroupRole, ...]:
    if values is None:
        return ()
    out: list[VoicingGroupRole] = []
    for value in values:
        if isinstance(value, VoicingGroupRole):
            out.append(value)
            continue
        if isinstance(value, Enum):
            value = value.value
        try:
            out.append(VoicingGroupRole(str(value)))
        except ValueError:
            continue
    return tuple(out)


def _dedupe_sorted_indices(values: list[int], note_count: int) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for value in values:
        index = int(value)
        if index < 0 or index >= note_count or index in seen:
            continue
        seen.add(index)
        out.append(index)
    return out
