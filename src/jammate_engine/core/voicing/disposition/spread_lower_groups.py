from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from itertools import product

from jammate_engine.core.harmony.chord_parser import parse_chord
from jammate_engine.core.harmony.material import (
    degree_to_semitone,
    fifth_degree_for_chord,
    seventh_degree_for_chord,
    third_degree_for_chord,
)

from .placement_utils import Degree, PlacedDegree


from .spread_contracts import SPREAD_RECIPE_CONTRACT_VERSION


LOWER_GROUP_INVENTORY_VERSION = "v2_2_38"


class LowerGroupRecipeId(str, Enum):
    """Implemented lower/foundation recipe ids for SPREAD planning."""

    ROOT = "lower_1note_root"
    ROOT_SEVENTH = "lower_2note_root_7"
    ROOT_THIRD = "lower_2note_root_3"
    ROOT_FIFTH = "lower_2note_root_5"
    THIRD_SEVENTH = "lower_2note_3_7"
    ROOT_FIFTH_UPPER_ROOT = "lower_3note_root_5_upper_root"
    ROOT_THIRD_SEVENTH = "lower_3note_root_3_7"
    ROOT_FIFTH_SEVENTH = "lower_3note_root_5_7"
    ROOT_SEVENTH_UPPER_THIRD = "lower_3note_root_7_upper3"
    ROOT_FIFTH_UPPER_THIRD = "lower_3note_root_5_upper3"


@dataclass(frozen=True)
class LowerGroupDegreeSpec:
    """One chord-quality-aware degree inside a lower/foundation group.

    ``role`` names the functional recipe slot. ``degree`` is the resolved chord
    degree token owned by Harmony, not a locally redefined pitch rule.  The
    semitone is compact by default; only ``upper_root`` deliberately uses 12 so
    duplicated root recipes can retain two distinct root notes within one octave.
    """

    role: str
    degree: str
    relative_semitone: int
    source: str = "core.harmony.material"

    def to_degree_pair(self) -> Degree:
        return (self.degree, int(self.relative_semitone))

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "degree": self.degree,
            "relative_semitone": self.relative_semitone,
            "source": self.source,
        }


@dataclass(frozen=True)
class LowerGroupRecipeInventoryItem:
    """Implemented lower/foundation inventory item for future SPREAD projection."""

    recipe_id: LowerGroupRecipeId
    note_count: int
    role_contract: tuple[str, ...]
    group_role: str = "lower/foundation"
    requires_within_octave: bool = True
    max_span_semitones: int = 12
    runtime_enabled: bool = False
    implementation_status: str = "implemented_inventory_notes_only"

    @property
    def ref_id(self) -> str:
        return self.recipe_id.value

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
            "inventory_version": LOWER_GROUP_INVENTORY_VERSION,
            "recipe_id": self.recipe_id.value,
            "note_count": self.note_count,
            "role_contract": list(self.role_contract),
            "group_role": self.group_role,
            "requires_within_octave": self.requires_within_octave,
            "max_span_semitones": self.max_span_semitones,
            "runtime_enabled": self.runtime_enabled,
            "implementation_status": self.implementation_status,
        }


@dataclass(frozen=True)
class LowerGroupRecipeInstance:
    """Chord-specific lower group degrees before register placement."""

    chord_symbol: str
    recipe: LowerGroupRecipeInventoryItem
    degree_specs: tuple[LowerGroupDegreeSpec, ...]
    is_available: bool = True
    unavailable_reason: str = ""

    @property
    def degree_names(self) -> tuple[str, ...]:
        return tuple(spec.degree for spec in self.degree_specs)

    @property
    def role_names(self) -> tuple[str, ...]:
        return tuple(spec.role for spec in self.degree_specs)

    @property
    def relative_semitones(self) -> tuple[int, ...]:
        return tuple(int(spec.relative_semitone) for spec in self.degree_specs)

    @property
    def span_semitones(self) -> int:
        if not self.degree_specs:
            return 0
        values = self.relative_semitones
        return int(max(values) - min(values))

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
            "inventory_version": LOWER_GROUP_INVENTORY_VERSION,
            "chord_symbol": self.chord_symbol,
            "recipe": self.recipe.to_debug_dict(),
            "degree_specs": [spec.to_debug_dict() for spec in self.degree_specs],
            "degree_names": list(self.degree_names),
            "role_names": list(self.role_names),
            "relative_semitones": list(self.relative_semitones),
            "span_semitones": self.span_semitones,
            "is_available": self.is_available,
            "unavailable_reason": self.unavailable_reason,
            "notes_only": True,
            "no_expression_or_pedal": True,
        }


@dataclass(frozen=True)
class LowerGroupPlacement:
    """Register-guarded lower group placement with metadata for future scorers."""

    instance: LowerGroupRecipeInstance
    placed_degrees: tuple[PlacedDegree, ...]
    low: int
    high: int
    target_low: int
    is_legal: bool
    legality_reason: str = ""

    @property
    def notes(self) -> tuple[int, ...]:
        return tuple(int(note) for _, note in self.placed_degrees)

    @property
    def span_semitones(self) -> int:
        if not self.notes:
            return 0
        return int(max(self.notes) - min(self.notes))

    @property
    def metadata(self) -> dict[str, object]:
        return {
            "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
            "inventory_version": LOWER_GROUP_INVENTORY_VERSION,
            "lower_group_recipe_id": self.instance.recipe.recipe_id.value,
            "lower_group_note_count": self.instance.recipe.note_count,
            "lower_group_roles": list(self.instance.role_names),
            "lower_group_degrees": list(self.instance.degree_names),
            "lower_group_requires_within_octave": self.instance.recipe.requires_within_octave,
            "lower_group_span_semitones": self.span_semitones,
            "lower_group_max_span_semitones": self.instance.recipe.max_span_semitones,
            "lower_group_register_low": int(self.low),
            "lower_group_register_high": int(self.high),
            "lower_group_target_low": int(self.target_low),
            "is_legal": self.is_legal,
            "legality_reason": self.legality_reason,
            "group_role": self.instance.recipe.group_role,
            "notes_only": True,
            "no_expression_or_pedal": True,
            "runtime_enabled": False,
        }

    def to_debug_dict(self) -> dict[str, object]:
        return {
            **self.metadata,
            "chord_symbol": self.instance.chord_symbol,
            "placed_degrees": [[degree, int(note)] for degree, note in self.placed_degrees],
        }



_LOWER_GROUP_RECIPE_INVENTORY: tuple[LowerGroupRecipeInventoryItem, ...] = (
    LowerGroupRecipeInventoryItem(LowerGroupRecipeId.ROOT, 1, ("root",)),
    LowerGroupRecipeInventoryItem(LowerGroupRecipeId.ROOT_SEVENTH, 2, ("root", "seventh")),
    LowerGroupRecipeInventoryItem(LowerGroupRecipeId.ROOT_THIRD, 2, ("root", "third")),
    LowerGroupRecipeInventoryItem(LowerGroupRecipeId.ROOT_FIFTH, 2, ("root", "fifth")),
    LowerGroupRecipeInventoryItem(LowerGroupRecipeId.THIRD_SEVENTH, 2, ("third", "seventh")),
    # v2_2_68: rooted 3-note lower/foundation recipes now align with
    # the 2+3 lower-foundation family.  Root+3+7 returns as the shell
    # foundation option, root+5+7 is removed, and wider upper-root/upper3
    # shapes may span up to 16 semitones after root octave anchoring.
    LowerGroupRecipeInventoryItem(
        LowerGroupRecipeId.ROOT_FIFTH_UPPER_ROOT,
        3,
        ("root", "fifth", "upper_root"),
        requires_within_octave=False,
        max_span_semitones=16,
    ),
    LowerGroupRecipeInventoryItem(
        LowerGroupRecipeId.ROOT_THIRD_SEVENTH,
        3,
        ("root", "third", "seventh"),
        requires_within_octave=False,
        max_span_semitones=16,
    ),
    LowerGroupRecipeInventoryItem(
        LowerGroupRecipeId.ROOT_SEVENTH_UPPER_THIRD,
        3,
        ("root", "seventh", "upper3"),
        requires_within_octave=False,
        max_span_semitones=16,
    ),
    LowerGroupRecipeInventoryItem(
        LowerGroupRecipeId.ROOT_FIFTH_UPPER_THIRD,
        3,
        ("root", "fifth", "upper3"),
        requires_within_octave=False,
        max_span_semitones=16,
    ),
)


def lower_group_recipe_inventory() -> tuple[LowerGroupRecipeInventoryItem, ...]:
    """Return the implemented v2_2_38 lower/foundation inventory.

    This is still notes-only.  It intentionally does not select SPREAD for any
    style runtime; it only exposes chord-quality-aware lower recipes for later
    projection and group-wise voice-leading passes.
    """

    return _LOWER_GROUP_RECIPE_INVENTORY


def lower_group_recipe_by_id(recipe_id: LowerGroupRecipeId | str) -> LowerGroupRecipeInventoryItem:
    """Look up one lower group recipe by enum or string id."""

    normalized = recipe_id if isinstance(recipe_id, LowerGroupRecipeId) else LowerGroupRecipeId(str(recipe_id))
    for recipe in _LOWER_GROUP_RECIPE_INVENTORY:
        if recipe.recipe_id == normalized:
            return recipe
    raise KeyError(f"unknown lower group recipe id: {recipe_id!r}")


def instantiate_lower_group_recipe(
    chord_symbol: str,
    recipe_id: LowerGroupRecipeId | str,
) -> LowerGroupRecipeInstance:
    """Resolve one lower recipe into chord-quality-aware degree specs.

    Harmony remains the source of truth for 3rd/5th/7th spelling.  For recipes
    that require a seventh, triads without a written seventh/sixth are marked
    unavailable rather than silently adding a color tone.
    """

    recipe = lower_group_recipe_by_id(recipe_id)
    chord = parse_chord(chord_symbol)
    specs: list[LowerGroupDegreeSpec] = []
    for role in recipe.role_contract:
        spec = _resolve_lower_group_degree_spec(chord_symbol, role)
        if spec is None:
            return LowerGroupRecipeInstance(
                chord_symbol=chord.symbol,
                recipe=recipe,
                degree_specs=tuple(specs),
                is_available=False,
                unavailable_reason=f"role {role!r} is unavailable for chord symbol {chord.symbol!r} without explicit seventh/sixth material",
            )
        specs.append(spec)
    return LowerGroupRecipeInstance(chord_symbol=chord.symbol, recipe=recipe, degree_specs=tuple(specs))


def place_lower_group_recipe(
    chord_symbol: str,
    recipe_id: LowerGroupRecipeId | str,
    low: int,
    high: int,
    *,
    target_low: int | None = None,
    min_top_note: int | None = None,
    root_bass_anchor_enabled: bool = False,
    root_bass_anchor_low: int | None = None,
    root_bass_anchor_high: int | None = None,
    allow_rooted_anchor_upper3_compression: bool = False,
    upper3_compression_root_threshold: int | None = None,
) -> LowerGroupPlacement:
    """Place an implemented lower group inside a register with an octave guard."""

    instance = instantiate_lower_group_recipe(chord_symbol, recipe_id)
    target = int(low if target_low is None else target_low)
    if not instance.is_available:
        return LowerGroupPlacement(
            instance=instance,
            placed_degrees=(),
            low=int(low),
            high=int(high),
            target_low=target,
            is_legal=False,
            legality_reason=instance.unavailable_reason,
        )
    root_pc = parse_chord(chord_symbol).root_pc
    placement = _place_lower_group_offsets(
        root_pc=root_pc,
        specs=instance.degree_specs,
        low=int(low),
        high=int(high),
        target_low=target,
        max_span=instance.recipe.max_span_semitones,
        min_top_note=min_top_note,
        root_bass_anchor_enabled=root_bass_anchor_enabled,
        root_bass_anchor_low=root_bass_anchor_low,
        root_bass_anchor_high=root_bass_anchor_high,
    )
    if (
        placement is not None
        and bool(allow_rooted_anchor_upper3_compression)
        and any(spec.role == "upper3" for spec in instance.degree_specs)
    ):
        root_notes = [int(note) for degree, note in placement if str(degree) in {"R", "1"}]
        threshold = int(upper3_compression_root_threshold) if upper3_compression_root_threshold is not None else None
        if root_notes and threshold is not None and min(root_notes) >= threshold:
            compressed = _compress_upper3_specs_within_root_octave(instance.degree_specs)
            compressed_placement = _place_lower_group_offsets(
                root_pc=root_pc,
                specs=compressed,
                low=int(low),
                high=int(high),
                target_low=target,
                max_span=instance.recipe.max_span_semitones,
                min_top_note=min_top_note,
                root_bass_anchor_enabled=root_bass_anchor_enabled,
                root_bass_anchor_low=root_bass_anchor_low,
                root_bass_anchor_high=root_bass_anchor_high,
            )
            if compressed_placement is not None:
                placement = compressed_placement
    if placement is None:
        return LowerGroupPlacement(
            instance=instance,
            placed_degrees=(),
            low=int(low),
            high=int(high),
            target_low=target,
            is_legal=False,
            legality_reason="no octave placement satisfies register and within-octave guard",
        )
    notes = [note for _, note in placement]
    span = int(max(notes) - min(notes)) if notes else 0
    is_legal = all(int(low) <= note <= int(high) for note in notes) and span <= instance.recipe.max_span_semitones
    return LowerGroupPlacement(
        instance=instance,
        placed_degrees=tuple(placement),
        low=int(low),
        high=int(high),
        target_low=target,
        is_legal=is_legal,
        legality_reason="ok" if is_legal else "placement violates register or octave guard",
    )


def lower_group_inventory_debug(chord_symbol: str = "Cmaj7", low: int = 36, high: int = 60) -> dict[str, object]:
    """Return a compact debug payload for lower group inventory audits."""

    placements = [place_lower_group_recipe(chord_symbol, recipe.recipe_id, low, high) for recipe in lower_group_recipe_inventory()]
    return {
        "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
        "inventory_version": LOWER_GROUP_INVENTORY_VERSION,
        "layer": "core.voicing.disposition.spread",
        "purpose": "SPREAD lower/foundation group recipe inventory",
        "runtime_enabled": False,
        "notes_only": True,
        "no_expression_or_pedal": True,
        "inventory": [recipe.to_debug_dict() for recipe in lower_group_recipe_inventory()],
        "placements": [placement.to_debug_dict() for placement in placements],
    }


def _compress_upper3_specs_within_root_octave(
    specs: tuple[LowerGroupDegreeSpec, ...],
) -> tuple[LowerGroupDegreeSpec, ...]:
    """Lower register rescue for 3+4 high-root cases inside A1-G5.

    The 3+4 lower recipe remains root+7+upper3/root+5+upper3 at the recipe
    level, but when the root cannot be placed below A1 (for example Ab), a
    literal upper3 leaves no legal color upper block under G5.  This contract-
    local compression keeps the third content while placing it in the root
    octave so the whole 3+4 voicing can stay inside A1-G5.
    """

    out: list[LowerGroupDegreeSpec] = []
    for spec in specs:
        if str(spec.role) == "upper3":
            out.append(replace(spec, relative_semitone=degree_to_semitone(spec.degree, stacked=False)))
        else:
            out.append(spec)
    return tuple(out)


def _resolve_lower_group_degree_spec(chord_symbol: str, role: str) -> LowerGroupDegreeSpec | None:
    chord = parse_chord(chord_symbol)
    normalized = str(role)
    if normalized == "root":
        return LowerGroupDegreeSpec(role=normalized, degree="R", relative_semitone=0)
    if normalized == "upper_root":
        return LowerGroupDegreeSpec(role=normalized, degree="R", relative_semitone=12)
    if normalized == "third":
        degree = third_degree_for_chord(chord)
        return LowerGroupDegreeSpec(role=normalized, degree=degree, relative_semitone=degree_to_semitone(degree, stacked=False))
    if normalized == "upper3":
        degree = third_degree_for_chord(chord)
        return LowerGroupDegreeSpec(role=normalized, degree=degree, relative_semitone=12 + degree_to_semitone(degree, stacked=False))
    if normalized == "fifth":
        degree = fifth_degree_for_chord(chord)
        return LowerGroupDegreeSpec(role=normalized, degree=degree, relative_semitone=degree_to_semitone(degree, stacked=False))
    if normalized == "seventh":
        degree = seventh_degree_for_chord(chord)
        if degree is None and chord.has_sixth:
            degree = "6"
        if degree is None:
            return None
        return LowerGroupDegreeSpec(role=normalized, degree=degree, relative_semitone=degree_to_semitone(degree, stacked=False))
    raise ValueError(f"unsupported lower group role: {role!r}")


def _place_lower_group_offsets(
    *,
    root_pc: int,
    specs: tuple[LowerGroupDegreeSpec, ...],
    low: int,
    high: int,
    target_low: int,
    max_span: int,
    min_top_note: int | None = None,
    root_bass_anchor_enabled: bool = False,
    root_bass_anchor_low: int | None = None,
    root_bass_anchor_high: int | None = None,
) -> list[PlacedDegree] | None:
    candidates: list[tuple[int, list[PlacedDegree]]] = []
    pc = int(root_pc) % 12
    for octave in range(0, 11):
        root_note = pc + 12 * octave
        placed = [(spec.degree, root_note + int(spec.relative_semitone)) for spec in specs]
        notes = [note for _, note in placed]
        if not notes:
            continue
        if root_bass_anchor_enabled:
            root_notes = [int(note) for degree, note in placed if str(degree) in {"R", "1"}]
            if not root_notes:
                continue
            root_note = min(root_notes)
            if root_bass_anchor_low is not None and root_note < int(root_bass_anchor_low):
                continue
            if root_bass_anchor_high is not None and root_note > int(root_bass_anchor_high):
                continue
            if root_note != min(notes):
                continue
        span = max(notes) - min(notes)
        if span > int(max_span):
            continue
        if any(note < int(low) or note > int(high) for note in notes):
            continue
        if min_top_note is not None and max(notes) < int(min_top_note):
            continue
        # Prefer root anchor near target_low, then compact lower placement.
        score = abs(root_note - int(target_low)) * 10 + min(notes)
        candidates.append((score, sorted(placed, key=lambda item: item[1])))
    if candidates:
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    if root_bass_anchor_enabled:
        return None

    # v2_2_60: the Ballad SPREAD 2+3 lower band is E2-E3. For some
    # roots, e.g. Ebmaj7, a literal root-at-bottom placement cannot fit
    # root+3/root+5/root+7 entirely inside that one-octave band.  Keep the
    # same functional content, but allow the two-note lower/foundation group
    # to invert within the band so rooted and rootless modes do not get mixed
    # merely because of register geometry.
    inversion_candidates: list[tuple[int, int, list[PlacedDegree]]] = []
    note_choices: list[list[tuple[str, int]]] = []
    for spec in specs:
        spec_pc = (pc + int(spec.relative_semitone)) % 12
        choices: list[tuple[str, int]] = []
        for octave in range(0, 11):
            note = spec_pc + 12 * octave
            if int(low) <= note <= int(high):
                choices.append((spec.degree, note))
        if not choices:
            return None
        note_choices.append(choices)

    from itertools import product

    for combo in product(*note_choices):
        notes = [int(note) for _, note in combo]
        if len(set(notes)) != len(notes):
            continue
        span = max(notes) - min(notes)
        if span > int(max_span):
            continue
        if min_top_note is not None and max(notes) < int(min_top_note):
            continue
        placed = sorted([(str(degree), int(note)) for degree, note in combo], key=lambda item: item[1])
        lower_center = sum(notes) / len(notes)
        target_center = int(target_low) + min(7, max(0, int(high) - int(target_low)) / 2)
        root_degrees = {"R", "1"}
        root_notes = [note for degree, note in placed if str(degree) in root_degrees]
        root_cost = min(abs(note - int(target_low)) for note in root_notes) if root_notes else 0
        center_cost = int(abs(lower_center - target_center) * 10)
        score = center_cost + root_cost + span
        inversion_candidates.append((score, span, placed))
    if not inversion_candidates:
        return None
    inversion_candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    return inversion_candidates[0][2]

