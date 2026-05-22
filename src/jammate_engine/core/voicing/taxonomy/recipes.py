from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..policy import ContentFamily, FunctionalGrouping, RootSupportPolicy, VoicingGroupRole


VOICING_TAXONOMY_RETIRED_4NOTE_GROUPING_METADATA_VERSION = "v2_6_103"
RETIRED_ORDINARY_4NOTE_GROUPINGS = (FunctionalGrouping.ONE_PLUS_THREE, FunctionalGrouping.TWO_PLUS_TWO)


@dataclass(frozen=True)
class VoicingRecipe:
    """Minimal density + functional grouping recipe contract.

    This object is metadata-first. It names the density and grouping shape that
    a selected candidate already exhibits; it must not retune voicing selection
    or change register placement by itself.
    """

    recipe_id: str
    density: int
    functional_grouping: FunctionalGrouping | None
    group_roles: tuple[VoicingGroupRole, ...] = ()
    content_family: ContentFamily | None = None
    root_support: RootSupportPolicy | None = None

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "density": self.density,
            "functional_grouping": self.functional_grouping.value if self.functional_grouping else None,
            "group_roles": [role.value for role in self.group_roles],
            "content_family": self.content_family.value if self.content_family else None,
            "root_support": self.root_support.value if self.root_support else None,
        }


def describe_density_recipe(
    degrees: list[str] | tuple[str, ...],
    content_family: ContentFamily | None = None,
    root_support: RootSupportPolicy | None = None,
) -> VoicingRecipe:
    """Describe the density/grouping identity of an already chosen degree stack.

    The current runtime still chooses degrees with the existing content planner.
    This helper only assigns stable metadata so future content/disposition/gesture
    work can refer to density recipes without re-parsing arbitrary degree lists.
    """

    degree_list = [str(degree) for degree in degrees]
    density = len(degree_list)
    grouping = infer_functional_grouping(degree_list, content_family, root_support)
    roles = group_roles_for_grouping(grouping, degree_list, content_family)
    recipe_id = build_recipe_id(density, grouping, content_family, root_support)
    return VoicingRecipe(
        recipe_id=recipe_id,
        density=density,
        functional_grouping=grouping,
        group_roles=roles,
        content_family=content_family,
        root_support=root_support,
    )


def infer_functional_grouping(
    degrees: list[str] | tuple[str, ...],
    content_family: ContentFamily | None = None,
    root_support: RootSupportPolicy | None = None,
) -> FunctionalGrouping | None:
    """Infer the V2 grouping shape from density and coarse content context.

    v2_6_103 retires the old ordinary 4-note ``1+3`` / ``2+2``
    functional-grouping metadata.  In the current architecture those grouped
    names are reserved for lower/upper SPREAD-style projection contracts, while
    ordinary 4-note CLOSED/OPEN stacks are compact/open voicings, not grouped
    voicings.  Therefore density-4 recipes intentionally return ``None`` for
    ``functional_grouping`` and use an ``unGrouped`` recipe id.
    """

    degree_list = [str(degree) for degree in degrees]
    density = len(degree_list)
    if density == 2:
        return FunctionalGrouping.TWO
    if density == 3:
        return FunctionalGrouping.THREE
    if density == 4:
        return None
    if density == 5:
        return FunctionalGrouping.TWO_PLUS_THREE
    if density == 6:
        if _looks_like_foundation_3block(degree_list):
            return FunctionalGrouping.THREE_PLUS_THREE
        return FunctionalGrouping.TWO_PLUS_FOUR
    if density >= 7:
        return FunctionalGrouping.THREE_PLUS_FOUR
    return None


def group_roles_for_grouping(
    grouping: FunctionalGrouping | None,
    degrees: list[str] | tuple[str, ...] = (),
    content_family: ContentFamily | None = None,
) -> tuple[VoicingGroupRole, ...]:
    """Return abstract group roles for a grouping shape.

    The role tuple describes groups, not individual notes. Detailed per-note
    group assignment belongs to the later projection-map foundation pass.
    """

    if grouping is None:
        return ()
    if grouping == FunctionalGrouping.TWO:
        if content_family in {ContentFamily.GUIDE_TONE, ContentFamily.SHELL}:
            return (VoicingGroupRole.SUPPORT,)
        return (VoicingGroupRole.PROJECTION,)
    if grouping == FunctionalGrouping.THREE:
        if content_family in {ContentFamily.SHELL_PLUS_5, ContentFamily.SHELL_PLUS_COLOR}:
            return (VoicingGroupRole.SUPPORT, VoicingGroupRole.COLOR)
        if _looks_like_foundation_3block(list(degrees)):
            return (VoicingGroupRole.FOUNDATION,)
        return (VoicingGroupRole.PROJECTION,)
    if grouping == FunctionalGrouping.ONE_PLUS_THREE:
        return (VoicingGroupRole.ANCHOR, VoicingGroupRole.PROJECTION)
    if grouping == FunctionalGrouping.ONE_PLUS_FOUR:
        return (VoicingGroupRole.FOUNDATION, VoicingGroupRole.PROJECTION)
    if grouping == FunctionalGrouping.TWO_PLUS_TWO:
        return (VoicingGroupRole.SUPPORT, VoicingGroupRole.COLOR)
    if grouping in {FunctionalGrouping.TWO_PLUS_THREE, FunctionalGrouping.TWO_PLUS_FOUR}:
        return (VoicingGroupRole.SUPPORT, VoicingGroupRole.PROJECTION)
    if grouping in {FunctionalGrouping.THREE_PLUS_THREE, FunctionalGrouping.THREE_PLUS_FOUR}:
        return (VoicingGroupRole.FOUNDATION, VoicingGroupRole.PROJECTION)
    return ()


def build_recipe_id(
    density: int,
    grouping: FunctionalGrouping | None,
    content_family: ContentFamily | None = None,
    root_support: RootSupportPolicy | None = None,
) -> str:
    grouping_token = _safe_token(grouping.value if grouping else "unGrouped")
    family_token = _safe_token(content_family.value if content_family else "generic")
    root_token = _safe_token(root_support.value if root_support else "root_unspecified")
    return f"d{int(density)}__{grouping_token}__{family_token}__{root_token}"


def _looks_like_anchor_plus_projection(
    degrees: list[str],
    content_family: ContentFamily | None,
    root_support: RootSupportPolicy | None,
) -> bool:
    """Legacy helper retained for compatibility audits; not used for density-4 grouping emission."""
    if not degrees:
        return False
    if degrees[0] == "R" and root_support in {
        RootSupportPolicy.ROOT_REQUIRED,
        RootSupportPolicy.BASS_ROOT_REQUIRED,
        RootSupportPolicy.ROOT_PREFERRED,
    }:
        return True
    if content_family in {ContentFamily.ROOTED_COLOR, ContentFamily.SEVENTH_BASIC} and degrees[0] == "R":
        return True
    return False


def _looks_like_foundation_3block(degrees: list[str]) -> bool:
    return len(degrees) >= 3 and degrees[0:3] in (["R", "5", "R"], ["R", "5", "8"], ["R", "5", "root_octave"])


def _safe_token(value: str) -> str:
    return value.replace("+", "plus").replace("/", "_").replace(" ", "_").replace("-", "_")
