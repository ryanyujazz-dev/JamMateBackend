from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from jammate_engine.core.harmony.chord_parser import parse_chord

from .models import OpenProjectionMethod
from .spread_contracts import SPREAD_RECIPE_CONTRACT_VERSION, SpreadUpperSourceKind
from .spread_lower_groups import LowerGroupRecipeId


UPPER_SOURCE_ADAPTER_VERSION = "v2_2_39"


@dataclass(frozen=True)
class UpperSourceRef:
    """Reference to existing upper source/orientation/projection resources.

    SPREAD may reuse source definitions, orientation metadata, color permission,
    and drop-family projection resources. It may not reuse an already-finalized
    closed/open candidate as the SPREAD placement.
    """

    ref_id: str
    note_count: int
    kind: SpreadUpperSourceKind
    reusable_owner_paths: tuple[str, ...]
    projection_methods: tuple[str, ...] = ()
    reusable_level: str = "source/orientation/projection_resource"
    final_placed_result_reuse_allowed: bool = False
    adapter_required: bool = True
    color_policy_owner_path: str = "core.voicing.color_permission"

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
            "ref_id": self.ref_id,
            "note_count": self.note_count,
            "kind": self.kind.value,
            "reusable_owner_paths": list(self.reusable_owner_paths),
            "projection_methods": list(self.projection_methods),
            "reusable_level": self.reusable_level,
            "final_placed_result_reuse_allowed": self.final_placed_result_reuse_allowed,
            "adapter_required": self.adapter_required,
            "color_policy_owner_path": self.color_policy_owner_path,
        }


@dataclass(frozen=True)
class SpreadUpperSourceOption:
    """Source/orientation-level upper material adapted for SPREAD projection.

    This object deliberately carries degrees and metadata only. It is not a
    closed/open placement and must not be treated as a final voicing candidate.
    The source data comes from the existing content planner, color gate, and
    canonical orientation metadata so SPREAD does not grow a parallel source
    inventory.
    """

    chord_symbol: str
    ref_id: str
    kind: SpreadUpperSourceKind
    source_family: str
    degrees: tuple[tuple[str, int], ...]
    source_metadata: tuple[str, ...]
    functional_source_type: str
    orientation_token: str
    reusable_owner_paths: tuple[str, ...]
    projection_methods: tuple[str, ...] = ()
    adapter_owner_path: str = "core.voicing.disposition.spread"
    final_placed_result_reuse_allowed: bool = False
    notes_only: bool = True
    runtime_enabled: bool = False

    @property
    def note_count(self) -> int:
        return len(self.degrees)

    @property
    def degree_names(self) -> tuple[str, ...]:
        return tuple(str(degree) for degree, _ in self.degrees)

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
            "upper_source_adapter_version": UPPER_SOURCE_ADAPTER_VERSION,
            "chord_symbol": self.chord_symbol,
            "ref_id": self.ref_id,
            "kind": self.kind.value,
            "note_count": self.note_count,
            "degree_names": list(self.degree_names),
            "degrees": [[degree, int(semitone)] for degree, semitone in self.degrees],
            "source_family": self.source_family,
            "functional_source_type": self.functional_source_type,
            "orientation_token": self.orientation_token,
            "source_metadata": list(self.source_metadata),
            "reusable_owner_paths": list(self.reusable_owner_paths),
            "projection_methods": list(self.projection_methods),
            "adapter_owner_path": self.adapter_owner_path,
            "source_oriented_not_placed": True,
            "final_placed_result_reuse_allowed": self.final_placed_result_reuse_allowed,
            "notes_only": self.notes_only,
            "runtime_enabled": self.runtime_enabled,
            "no_expression_or_pedal": True,
        }


@dataclass(frozen=True)
class SpreadUpperSourceAdapterResult:
    """Adapter result for one ``UpperSourceRef`` and chord symbol."""

    chord_symbol: str
    upper_source_ref: UpperSourceRef
    options: tuple[SpreadUpperSourceOption, ...]
    policy_metadata: dict[str, object]
    adapter_owner_path: str = "core.voicing.disposition.spread"
    runtime_enabled: bool = False

    @property
    def option_count(self) -> int:
        return len(self.options)

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
            "upper_source_adapter_version": UPPER_SOURCE_ADAPTER_VERSION,
            "chord_symbol": self.chord_symbol,
            "upper_source_ref": self.upper_source_ref.to_debug_dict(),
            "option_count": self.option_count,
            "options": [option.to_debug_dict() for option in self.options],
            "policy_metadata": dict(self.policy_metadata),
            "adapter_owner_path": self.adapter_owner_path,
            "source_oriented_not_placed": True,
            "final_placed_result_reuse_allowed": False,
            "notes_only": True,
            "runtime_enabled": self.runtime_enabled,
            "no_expression_or_pedal": True,
        }


def adapt_spread_upper_source_from_ref(
    chord_symbol: str,
    upper_source_ref: UpperSourceRef,
    policy: Any | None = None,
) -> SpreadUpperSourceAdapterResult:
    """Adapt core source/orientation resources for one SPREAD upper group.

    This is notes-only and source-oriented. It reuses the core content planner,
    color gates, canonical source metadata, and optional upper-structure source
    planner; it never calls the final candidate generator and never reuses a
    completed CLOSED/OPEN ``VoicingCandidate`` placement.
    """

    ref = upper_source_ref
    voicing_policy = _spread_upper_adapter_policy(ref, policy)
    source_recipes = _plan_upper_source_content_recipes(chord_symbol, ref, voicing_policy)
    options: list[SpreadUpperSourceOption] = []
    seen: set[tuple[str, tuple[str, ...], tuple[str, ...]]] = set()
    for upper_structure in _plan_upper_structure_sources_for_spread(chord_symbol, ref, voicing_policy):
        degrees = tuple((str(degree), int(semitone)) for degree, semitone in upper_structure.degrees)
        source_metadata = tuple(str(note) for note in upper_structure.source_notes)
        source_family = str(upper_structure.structure_kind)
        key = (source_family, tuple(degree for degree, _ in degrees), source_metadata)
        if key in seen:
            continue
        seen.add(key)
        options.append(
            SpreadUpperSourceOption(
                chord_symbol=str(upper_structure.symbol),
                ref_id=ref.ref_id,
                kind=ref.kind,
                source_family=source_family,
                degrees=degrees,
                source_metadata=source_metadata,
                functional_source_type=str(upper_structure.source_id),
                orientation_token="upper_structure_source_family",
                reusable_owner_paths=(*ref.reusable_owner_paths, "core.voicing.sources.upper_structure"),
                projection_methods=_normalized_upper_projection_methods(ref),
            )
        )
    for recipe in source_recipes:
        degrees = tuple((str(degree), int(semitone)) for degree, semitone in getattr(recipe, "degrees", ()))
        if len(degrees) != ref.note_count:
            continue
        source_metadata = tuple(str(note) for note in getattr(recipe, "validity_notes", ()) or ())
        source_family = getattr(getattr(recipe, "family", None), "value", str(getattr(recipe, "family", "unknown")))
        functional_type = _extract_upper_functional_source_type(source_metadata, source_family)
        orientation_token = _extract_upper_orientation_token(source_metadata)
        key = (source_family, tuple(degree for degree, _ in degrees), source_metadata)
        if key in seen:
            continue
        seen.add(key)
        options.append(
            SpreadUpperSourceOption(
                chord_symbol=str(getattr(recipe, "symbol", chord_symbol)),
                ref_id=ref.ref_id,
                kind=ref.kind,
                source_family=source_family,
                degrees=degrees,
                source_metadata=source_metadata,
                functional_source_type=functional_type,
                orientation_token=orientation_token,
                reusable_owner_paths=ref.reusable_owner_paths,
                projection_methods=_normalized_upper_projection_methods(ref),
            )
        )
    if not bool(_spread_policy_metadata(voicing_policy).get("spread_upper_structure_prefer", True)):
        options.sort(
            key=lambda option: (
                1 if _is_upper_structure_source(option) else 0,
                str(option.source_family),
                option.degree_names,
                option.source_metadata,
            )
        )
    return SpreadUpperSourceAdapterResult(
        chord_symbol=parse_chord(chord_symbol).symbol,
        upper_source_ref=ref,
        options=tuple(options),
        policy_metadata=_spread_upper_adapter_policy_metadata(voicing_policy, ref),
    )


def _spread_policy_metadata(policy: Any | None) -> dict[str, object]:
    try:
        return dict(getattr(policy, "metadata", None) or {})
    except Exception:
        return dict(policy or {}) if isinstance(policy, dict) else {}


def _upper_structure_enabled_for_policy(policy: Any | None) -> bool:
    metadata = _spread_policy_metadata(policy)
    if metadata.get("spread_upper_structure_force_enabled") is True:
        return True
    if metadata.get("spread_upper_structure_enabled") is False:
        return False
    if metadata.get("spread_upper_structure_enabled") is True:
        return True
    nested = metadata.get("upper_structure")
    if isinstance(nested, dict) and nested.get("enabled") is True:
        return True
    return False


def _upper_structure_lower_gate_enabled(metadata: dict[str, object]) -> bool:
    return bool(
        metadata.get("spread_upper_structure_lower_gate_enabled", False)
        or metadata.get("spread_upper_structure_enabled", False)
        or metadata.get("spread_upper_structure_force_enabled", False)
    )


def _plan_upper_structure_sources_for_spread(
    chord_symbol: str,
    ref: UpperSourceRef,
    policy: Any | None,
) -> tuple[Any, ...]:
    if int(ref.note_count) not in {3, 4}:
        return ()
    if not _upper_structure_enabled_for_policy(policy):
        return ()
    try:
        from jammate_engine.core.voicing.sources.upper_structure import plan_upper_structure_sources
    except Exception:  # pragma: no cover - defensive optional boundary
        return ()
    return tuple(plan_upper_structure_sources(chord_symbol, density=int(ref.note_count), policy=policy))


def _is_upper_structure_source(option: SpreadUpperSourceOption) -> bool:
    family = str(getattr(option, "source_family", ""))
    return family in {"upper_structure_triad", "upper_structure_4note"} or any(
        str(note) == "upper_structure_source_family" for note in getattr(option, "source_metadata", ())
    )


def _upper_structure_source_id(option: SpreadUpperSourceOption) -> str | None:
    if not _is_upper_structure_source(option):
        return None
    prefix = "upper_structure_source_id_"
    for note in getattr(option, "source_metadata", ()):  # source metadata is tuple[str, ...]
        text = str(note)
        if text.startswith(prefix):
            return text.removeprefix(prefix)
    return str(getattr(option, "functional_source_type", "upper_structure"))


def _upper_structure_lower_mode(recipe_id: LowerGroupRecipeId | str) -> str:
    try:
        normalized = recipe_id if isinstance(recipe_id, LowerGroupRecipeId) else LowerGroupRecipeId(str(recipe_id))
    except ValueError:
        return "unknown"
    if normalized == LowerGroupRecipeId.THIRD_SEVENTH:
        return "shell"
    if normalized in {LowerGroupRecipeId.ROOT_SEVENTH_UPPER_THIRD, LowerGroupRecipeId.ROOT_THIRD_SEVENTH}:
        return "root_plus_shell"
    return "not_upper_structure_lower_mode"


def _plan_upper_source_content_recipes(chord_symbol: str, ref: UpperSourceRef, policy: Any) -> list[Any]:
    from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes

    return list(plan_content_recipes(chord_symbol, policy))


def _spread_upper_adapter_policy(ref: UpperSourceRef, policy: Any | None) -> Any:
    from jammate_engine.core.voicing.policy import ContentFamily, RootSupportPolicy, VoicingPolicy

    base = policy if policy is not None else VoicingPolicy()
    if not isinstance(base, VoicingPolicy):
        base = VoicingPolicy.from_legacy_dict(dict(base or {}))
    note_count = int(ref.note_count)
    allowed_content: tuple[ContentFamily, ...]
    metadata_source = dict(getattr(base, "metadata", None) or {})
    prefer_expanded_3note_color = bool(metadata_source.get("spread_upper_3note_prefer_expanded_color"))
    prefer_expanded_4note_color = bool(metadata_source.get("spread_upper_4note_prefer_expanded_color"))
    if note_count == 2:
        allowed_content = (ContentFamily.GUIDE_TONE, ContentFamily.SHELL)
    elif note_count == 3:
        if prefer_expanded_3note_color:
            allowed_content = (
                ContentFamily.SHELL_PLUS_COLOR,
                ContentFamily.SHELL_PLUS_5,
                ContentFamily.MAJOR_TRIAD,
                ContentFamily.MINOR_TRIAD,
                ContentFamily.DIMINISHED_TRIAD,
                ContentFamily.AUGMENTED_TRIAD,
                ContentFamily.SUS2_TRIAD,
                ContentFamily.SUS4_TRIAD,
                ContentFamily.POWER_CHORD_5TH,
            )
        else:
            allowed_content = (
                ContentFamily.SHELL_PLUS_5,
                ContentFamily.SHELL_PLUS_COLOR,
                ContentFamily.MAJOR_TRIAD,
                ContentFamily.MINOR_TRIAD,
                ContentFamily.DIMINISHED_TRIAD,
                ContentFamily.AUGMENTED_TRIAD,
                ContentFamily.SUS2_TRIAD,
                ContentFamily.SUS4_TRIAD,
                ContentFamily.POWER_CHORD_5TH,
            )
    elif note_count == 4:
        if prefer_expanded_4note_color:
            allowed_content = (
                ContentFamily.ROOTED_COLOR,
                ContentFamily.ROOTLESS_A,
                ContentFamily.ROOTLESS_B,
                ContentFamily.SEVENTH_BASIC,
                ContentFamily.MAJOR_TRIAD,
                ContentFamily.MINOR_TRIAD,
                ContentFamily.DIMINISHED_TRIAD,
                ContentFamily.AUGMENTED_TRIAD,
                ContentFamily.SUS2_TRIAD,
                ContentFamily.SUS4_TRIAD,
                ContentFamily.POWER_CHORD_5TH,
            )
        else:
            allowed_content = (
                ContentFamily.SEVENTH_BASIC,
                ContentFamily.ROOTED_COLOR,
                ContentFamily.ROOTLESS_A,
                ContentFamily.ROOTLESS_B,
                ContentFamily.MAJOR_TRIAD,
                ContentFamily.MINOR_TRIAD,
                ContentFamily.DIMINISHED_TRIAD,
                ContentFamily.AUGMENTED_TRIAD,
                ContentFamily.SUS2_TRIAD,
                ContentFamily.SUS4_TRIAD,
                ContentFamily.POWER_CHORD_5TH,
            )
    else:
        allowed_content = tuple(getattr(base, "allowed_content", ()) or ())
    metadata = {
        **metadata_source,
        "spread_upper_source_adapter": True,
        "spread_upper_3note_prefer_expanded_color": prefer_expanded_3note_color,
        "spread_upper_4note_prefer_expanded_color": prefer_expanded_4note_color,
        "spread_upper_source_ref_id": ref.ref_id,
        "spread_upper_source_note_count": note_count,
        "spread_upper_reuse_level": ref.reusable_level,
        "spread_upper_final_placed_result_reuse_allowed": False,
    }
    return replace(
        base,
        allowed_content=allowed_content,
        preferred_content=None,
        root_support=RootSupportPolicy.ROOT_OPTIONAL,
        preferred_density=note_count,
        min_density=min(note_count, max(1, int(getattr(base, "min_density", note_count)))),
        max_density=note_count,
        metadata=metadata,
    )


def _spread_upper_adapter_policy_metadata(policy: Any, ref: UpperSourceRef) -> dict[str, object]:
    return {
        "upper_source_ref_id": ref.ref_id,
        "upper_source_note_count": int(ref.note_count),
        "upper_source_kind": ref.kind.value,
        "allowed_content": [getattr(item, "value", str(item)) for item in getattr(policy, "allowed_content", ())],
        "preferred_density": int(getattr(policy, "preferred_density", 0)),
        "min_density": int(getattr(policy, "min_density", 0)),
        "max_density": int(getattr(policy, "max_density", 0)),
        "harmonic_expansion_enabled": bool(getattr(policy, "harmonic_expansion_enabled", False)),
        "color_policy_mode": getattr(getattr(policy, "color_policy_mode", ""), "value", str(getattr(policy, "color_policy_mode", ""))),
        "reuses_core_content_planner": True,
        "reuses_core_color_permission": True,
        "reuses_drop_family_projection_resource": ref.kind == SpreadUpperSourceKind.DROP_FAMILY_DERIVED_PROJECTION_BLOCK,
        "final_placed_result_reuse_allowed": False,
    }


def _normalized_upper_projection_methods(ref: UpperSourceRef) -> tuple[str, ...]:
    if ref.kind == SpreadUpperSourceKind.DROP_FAMILY_DERIVED_PROJECTION_BLOCK:
        return _spread_allowed_upper_4note_projection_methods(ref.projection_methods)
    if ref.projection_methods:
        return tuple(_normalize_projection_method_name(method) for method in ref.projection_methods)
    return ()


def _spread_allowed_upper_4note_projection_methods(methods: tuple[str, ...] | list[str] | None = None) -> tuple[str, ...]:
    """Return the only OPEN projection resources SPREAD may reuse for upper 4-note blocks."""

    requested = methods or (OpenProjectionMethod.DROP2.value, OpenProjectionMethod.DROP3.value)
    allowed = {OpenProjectionMethod.DROP2.value, OpenProjectionMethod.DROP3.value}
    out: list[str] = []
    for method in requested:
        normalized = _normalize_projection_method_name(method)
        if normalized in allowed and normalized not in out:
            out.append(normalized)
    return tuple(out) or (OpenProjectionMethod.DROP2.value, OpenProjectionMethod.DROP3.value)


def _normalize_projection_method_name(method: object) -> str:
    value = getattr(method, "value", str(method))
    text = str(value).strip().lower().replace("-", "_")
    aliases = {
        "drop2": "drop2",
        "drop_2": "drop2",
        "drop3": "drop3",
        "drop_3": "drop3",
        "drop2_and_4": "drop2_and_4",
        "drop_2_and_4": "drop2_and_4",
        "drop24": "drop2_and_4",
        "drop_2_4": "drop2_and_4",
        "drop2&4": "drop2_and_4",
        "drop_2&4": "drop2_and_4",
    }
    return aliases.get(text, text)


def _extract_upper_functional_source_type(metadata: tuple[str, ...], source_family: str) -> str:
    prefixes = (
        "three_note_functional_source_type_",
        "rootless_ab_functional_source_type_",
        "basic_4note_functional_content_type_",
        "triad_4note_functional_content_type_",
        "rooted_color_4note_functional_source_type_",
    )
    for note in metadata:
        for prefix in prefixes:
            if note.startswith(prefix):
                return note.removeprefix(prefix)
    return str(source_family)


def _extract_upper_orientation_token(metadata: tuple[str, ...]) -> str:
    for prefix in (
        "rootless_ab_orientation_",
        "rootless_ab_inversion_index_",
        "basic_4note_inversion_index_",
        "triad_4note_inversion_index_",
        "rooted_color_4note_inversion_index_",
    ):
        for note in metadata:
            if note.startswith(prefix):
                return note
    for note in metadata:
        if "degree_order_" in note or "source_order_" in note:
            return note
    return "source_order_as_emitted_by_content_planner"
