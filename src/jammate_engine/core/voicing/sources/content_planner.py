from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jammate_engine.core.harmony.material import ChordMaterial, chord_material
from jammate_engine.core.harmony.chord_parser import parse_chord

from .content_family_router import choose_content_families as _route_content_families
from .content_source_inventory import (
    content_degree_options,
    content_validity_notes,
    seventh_chord_source_integrity_notes as _inventory_seventh_chord_source_integrity_notes,
    source_preserves_seventh_chord_identity as _inventory_source_preserves_seventh_chord_identity,
    trim_content_degrees as _inventory_trim_content_degrees,
)
from ..policy import ContentFamily, RootSupportPolicy, VoicingPolicy
from ..taxonomy.recipes import VoicingRecipe, describe_density_recipe


GLOBAL_SEVENTH_CHORD_EXPANSION_SOURCE_INTEGRITY_GATE_VERSION = "v2_2_54"


@dataclass(frozen=True)
class VoicingContentRecipe:
    """Content-family degree recipe selected before disposition/register.

    The content planner is now a public compatibility facade and orchestration
    layer.  Family routing lives in ``content_family_router.py`` and family ->
    degree source inventory lives in ``content_source_inventory.py``.
    """

    symbol: str
    family: ContentFamily
    root_support: RootSupportPolicy
    degrees: tuple[tuple[str, int], ...]
    density_recipe: VoicingRecipe
    material: ChordMaterial
    validity_notes: tuple[str, ...] = ()

    @property
    def degree_names(self) -> tuple[str, ...]:
        return tuple(degree for degree, _ in self.degrees)

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "family": self.family.value,
            "root_support": self.root_support.value,
            "degree_names": list(self.degree_names),
            "degrees": [{"degree": degree, "semitone": semitone} for degree, semitone in self.degrees],
            "density_recipe": self.density_recipe.to_debug_dict(),
            "validity_notes": list(self.validity_notes),
            "harmony_material": {
                "quality": self.material.quality,
                "triad_degrees": list(self.material.triad_degrees),
                "seventh_degree": self.material.seventh_degree,
                "chord_tone_degrees": list(self.material.chord_tone_degrees),
                "available_tensions": list(self.material.available_tensions),
                "avoid_degrees": list(self.material.avoid_degrees),
            },
        }


def trim_content_degrees(degrees: list[tuple[str, int]], policy: VoicingPolicy) -> list[tuple[str, int]]:
    """Compatibility wrapper for content-source inventory density trimming."""

    return _inventory_trim_content_degrees(degrees, policy)


def source_preserves_seventh_chord_identity(chord, degree_names: tuple[str, ...] | list[str]) -> bool:
    """Compatibility wrapper for the global seventh-chord source integrity gate."""

    return _inventory_source_preserves_seventh_chord_identity(chord, degree_names)


def seventh_chord_source_integrity_notes(chord, degree_names: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Compatibility wrapper for global seventh-chord source integrity audit notes."""

    return _inventory_seventh_chord_source_integrity_notes(chord, degree_names)


def choose_content_families(symbol: str, policy: VoicingPolicy) -> list[ContentFamily]:
    """Compatibility facade for content-family routing.

    The implementation owner is ``content_family_router.py``.  Keep this
    wrapper so historical imports from ``content_planner`` remain stable while
    family-choice / chord-quality normalization no longer lives in the source
    inventory planner.
    """

    return _route_content_families(symbol, policy)


def plan_content_recipes(symbol: str, policy: VoicingPolicy) -> list[VoicingContentRecipe]:
    """Return content recipes with density and validity metadata."""

    material = chord_material(symbol)
    chord = parse_chord(symbol)
    recipes: list[VoicingContentRecipe] = []
    for family in choose_content_families(symbol, policy):
        for raw_degrees, variant_notes in content_degree_options(symbol, chord, material, family, policy):
            degrees = trim_content_degrees(raw_degrees, policy)
            density = describe_density_recipe([degree for degree, _ in degrees], family, policy.root_support)
            validity_notes = content_validity_notes(chord, family, tuple(degree for degree, _ in degrees), policy)
            validity_notes = tuple(dict.fromkeys([*validity_notes, *variant_notes]))
            recipes.append(
                VoicingContentRecipe(
                    symbol=symbol,
                    family=family,
                    root_support=policy.root_support,
                    degrees=tuple(degrees),
                    density_recipe=density,
                    material=material,
                    validity_notes=validity_notes,
                )
            )
    return recipes


def choose_degrees(symbol: str, policy: VoicingPolicy) -> list[tuple[str, int]]:
    """Compatibility helper returning the first valid content recipe."""

    recipes = plan_content_recipes(symbol, policy)
    return list(recipes[0].degrees) if recipes else []
