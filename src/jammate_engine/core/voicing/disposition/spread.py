from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any

from jammate_engine.core.harmony.chord_parser import parse_chord
from .closed import compact_closed_parent_candidates_for_projection
from .models import OpenProjectionMethod
from .open import named_open_projection_metadata, place_named_open_projection_from_closed_parents
from .placement_utils import Degree, PlacedDegree, dedupe_by_note, degree_to_note, place_stack


from .spread_contracts import (
    SPREAD_ACTIVE_CONTRACT_IDS,
    SPREAD_RECIPE_CONTRACT_VERSION,
    SPREAD_RETIRED_FOUR_NOTE_CONTRACT_IDS,
    SpreadGrouping,
    SpreadReuseStatus,
    SpreadUpperSourceKind,
)
from .spread_lower_groups import (
    LOWER_GROUP_INVENTORY_VERSION,
    LowerGroupDegreeSpec,
    LowerGroupPlacement,
    LowerGroupRecipeId,
    LowerGroupRecipeInstance,
    LowerGroupRecipeInventoryItem,
    lower_group_inventory_debug,
    lower_group_recipe_by_id,
    lower_group_recipe_inventory,
    instantiate_lower_group_recipe,
    place_lower_group_recipe,
)

from .spread_upper_sources import (
    UPPER_SOURCE_ADAPTER_VERSION,
    SpreadUpperSourceAdapterResult,
    SpreadUpperSourceOption,
    UpperSourceRef,
    _is_upper_structure_source,
    _spread_allowed_upper_4note_projection_methods,
    _upper_structure_enabled_for_policy,
    _upper_structure_lower_gate_enabled,
    _upper_structure_lower_mode,
    _upper_structure_source_id,
    adapt_spread_upper_source_from_ref,
)

from .spread_register_guards import (
    BASIC_SPREAD_PROJECTION_VERSION,
    LOW_REGISTER_DENSITY_GUARD_VERSION,
    SPREAD_REGISTER_GUARD_SPLIT_VERSION,
    UPPER_STRUCTURE_SPREAD_PILOT_VERSION,
    SpreadProjectionRegisterPolicy,
    basic_spread_projection_legality as _basic_spread_projection_legality,
    basic_spread_register_policy,
    is_spread_1plus4_contract as _is_spread_1plus4_contract,
    is_spread_3plus4_contract as _is_spread_3plus4_contract,
    low_register_density_guard_passed as _low_register_density_guard_passed,
    lower_group_register_window as _lower_group_register_window,
    root_anchor_tail_span_guard_enabled as _root_anchor_tail_span_guard_enabled,
    root_anchor_tail_span_guard_passed as _root_anchor_tail_span_guard_passed,
    root_bass_note_from_lower as _root_bass_note_from_lower,
    rooted_bass_anchor_passed as _rooted_bass_anchor_passed,
    spread_register_guard_debug,
    spread_register_policy_for_contract as _spread_register_policy_for_contract,
    upper_structure_root_shell_tail_gate_passed as _upper_structure_root_shell_tail_gate_passed,
)

from .spread_voice_leading import (
    GROUPWISE_SPREAD_VOICE_LEADING_VERSION,
    SPREAD_GROUPWISE_VOICE_LEADING_SPLIT_VERSION,
    SpreadGroupwiseVoiceLeadingScore,
    SpreadGroupwiseVoiceLeadingWeights,
    compute_groupwise_motion_score,
    lower_group_motion_distance,
    rank_spread_candidates_by_group_motion,
    rank_spread_candidates_by_groupwise_voice_leading,
    score_spread_groupwise_voice_leading,
    select_spread_candidate_by_groupwise_voice_leading,
    spread_groupwise_voice_leading_path_debug,
    spread_voice_leading_debug,
    top_voice_continuity_distance,
    upper_group_motion_distance,
)


from .spread_runtime_gate import (
    SPREAD_RUNTIME_GATE_ADAPTER_CLEANUP_VERSION,
    SpreadRuntimeGateDecision,
    SpreadCandidateSelectorRequest,
    SpreadCandidateSelectorResult,
    spread_runtime_gate_from_policy,
    select_spread_candidate_with_runtime_gate,
    spread_candidate_selector_contract_debug,
)

from .spread_runtime_adapter import (
    SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION,
    SpreadRuntimeAdapterStatus,
    SpreadRuntimeAdapterFieldMapping,
    SpreadRuntimeAdapterResult,
    _spread_runtime_adapter_field_mappings,
    _spread_runtime_adapter_values,
    _spread_runtime_adapter_conversion_requested,
    _spread_runtime_content_family,
    _spread_runtime_root_support,
    _spread_runtime_bass_relation,
    _spread_runtime_interval_structure,
    _spread_runtime_root_support_decision,
    spread_projection_candidate_to_voicing_candidate_adapter,
    spread_runtime_adapter_owner_debug,
)

@dataclass(frozen=True)
class SpreadReuseAuditItem:
    """One reusable or forbidden resource discovered for SPREAD planning.

    The contract is intentionally metadata-first.  It records what SPREAD may
    reuse in future passes and what it must not reuse; it does not project notes
    or retune any style runtime by itself.
    """

    resource_id: str
    owner_path: str
    reusable_level: str
    status: SpreadReuseStatus
    reason: str
    final_placed_result_reuse_allowed: bool = False

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
            "resource_id": self.resource_id,
            "owner_path": self.owner_path,
            "reusable_level": self.reusable_level,
            "status": self.status.value,
            "reason": self.reason,
            "final_placed_result_reuse_allowed": self.final_placed_result_reuse_allowed,
        }


@dataclass(frozen=True)
class LowerGroupRecipeContract:
    """Skeleton reference to a future lower/foundation recipe inventory."""

    ref_id: str
    note_count: int
    degree_role_contract: tuple[str, ...]
    group_role: str = "lower/foundation"
    requires_within_octave: bool = True
    inventory_owner_path: str = "core.voicing.disposition.spread"
    implementation_status: str = "inventory_contract_skeleton_only"

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
            "ref_id": self.ref_id,
            "note_count": self.note_count,
            "degree_role_contract": list(self.degree_role_contract),
            "group_role": self.group_role,
            "requires_within_octave": self.requires_within_octave,
            "inventory_owner_path": self.inventory_owner_path,
            "implementation_status": self.implementation_status,
        }



@dataclass(frozen=True)
class SpreadRecipeContract:
    """Skeleton contract for one lower+upper SPREAD recipe shape."""

    recipe_id: str
    grouping: SpreadGrouping
    density: int
    lower_group: LowerGroupRecipeContract
    upper_source: UpperSourceRef
    notes_only: bool = True
    owns_group_register_gap_span: bool = True
    owns_groupwise_voice_leading: bool = True
    expression_allowed_in_this_layer: bool = False
    runtime_enabled: bool = False

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
            "recipe_id": self.recipe_id,
            "grouping": self.grouping.value,
            "density": self.density,
            "lower_group": self.lower_group.to_debug_dict(),
            "upper_source": self.upper_source.to_debug_dict(),
            "notes_only": self.notes_only,
            "owns_group_register_gap_span": self.owns_group_register_gap_span,
            "owns_groupwise_voice_leading": self.owns_groupwise_voice_leading,
            "expression_allowed_in_this_layer": self.expression_allowed_in_this_layer,
            "runtime_enabled": self.runtime_enabled,
        }


SPREAD_SELECTOR_RUNTIME_GATE_VERSION = "v2_2_42"
SPREAD_1PLUS4_UPPER_COMPACT_CLOSED_PARENT_ALIGNMENT_VERSION = "v2_2_53"
SPREAD_UPPER_4NOTE_DROP2_DROP3_ONLY_VERSION = "v2_2_55"
BALLAD_SPREAD_1PLUS3_PILOT_VERSION = "v2_2_56"
BALLAD_SPREAD_2PLUS3_PILOT_VERSION = "v2_2_73"
BALLAD_SPREAD_2PLUS3_LOWER_UPPER_FIX_VERSION = "v2_2_73"
BALLAD_SPREAD_2PLUS3_CLOSED_UPPER_GROUPWISE_VL_VERSION = "v2_2_73"
BALLAD_SPREAD_2PLUS3_ROOTED_BASS_ANCHOR_VERSION = "v2_2_73"
BALLAD_SPREAD_2PLUS4_PILOT_VERSION = "v2_2_73"
BALLAD_SPREAD_3PLUS3_PILOT_VERSION = "v2_2_73"
BALLAD_SPREAD_3PLUS3_LOWER_RECIPE_REGISTER_FIX_VERSION = "v2_2_73"
BALLAD_SPREAD_3PLUS3_LOWER_SPAN_OVERLAP_FIX_VERSION = "v2_2_73"
SPREAD_LOWER_FOUNDATION_QUALITY_GATE_VERSION = "v2_2_73"
BALLAD_SPREAD_3PLUS4_PILOT_VERSION = "v2_2_76"
BALLAD_SPREAD_3PLUS4_COLOR_UPPER_VERSION = "v2_2_76"
BALLAD_SPREAD_3PLUS4_MUSICAL_CLOSURE_VERSION = "v2_2_76"
BALLAD_SPREAD_GROUPING_MIX_POLICY_VERSION = "v2_2_84"
BALLAD_SPREAD_TEXTURE_STATE_MIX_VERSION = "v2_2_84"


@dataclass(frozen=True)
class SpreadProjectionCandidate:
    """One lower+upper SPREAD candidate after register placement.

    This is a notes/projection candidate, not a runtime ``VoicingCandidate``.
    It intentionally carries enough metadata for later scorer/selector work
    while remaining disconnected from expression, pedal, and style retuning.
    """

    chord_symbol: str
    recipe_contract: SpreadRecipeContract
    lower: LowerGroupPlacement
    upper_source: SpreadUpperSourceOption
    upper_placed: tuple[PlacedDegree, ...]
    upper_projection_method: str
    upper_projection_metadata: dict[str, object]
    register_policy: SpreadProjectionRegisterPolicy
    is_legal: bool
    legality_reason: str = ""
    runtime_enabled: bool = False

    @property
    def lower_placed(self) -> tuple[PlacedDegree, ...]:
        return self.lower.placed_degrees

    @property
    def lower_notes(self) -> tuple[int, ...]:
        return self.lower.notes

    @property
    def upper_notes(self) -> tuple[int, ...]:
        return tuple(int(note) for _, note in self.upper_placed)

    @property
    def placed_degrees(self) -> tuple[PlacedDegree, ...]:
        combined = [(str(degree), int(note)) for degree, note in (*self.lower_placed, *self.upper_placed)]
        return tuple(sorted(dedupe_by_note(combined), key=lambda item: item[1]))

    @property
    def notes(self) -> tuple[int, ...]:
        return tuple(int(note) for _, note in self.placed_degrees)

    @property
    def degrees(self) -> tuple[str, ...]:
        return tuple(str(degree) for degree, _ in self.placed_degrees)

    @property
    def group_gap_semitones(self) -> int | None:
        if not self.lower_notes or not self.upper_notes:
            return None
        return int(min(self.upper_notes) - max(self.lower_notes))

    @property
    def overall_span_semitones(self) -> int:
        if not self.notes:
            return 0
        return int(max(self.notes) - min(self.notes))

    @property
    def density(self) -> int:
        return len(self.notes)

    @property
    def metadata(self) -> dict[str, object]:
        return {
            "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
            "basic_spread_projection_version": BASIC_SPREAD_PROJECTION_VERSION,
            "layer": "core.voicing.disposition.spread",
            "chord_symbol": self.chord_symbol,
            "recipe_id": self.recipe_contract.recipe_id,
            "grouping": self.recipe_contract.grouping.value,
            "density": self.density,
            "expected_density": int(self.recipe_contract.density),
            "lower_group_recipe_id": self.lower.instance.recipe.recipe_id.value,
            "lower_group_roles": list(self.lower.instance.role_names),
            "lower_group_degrees": list(self.lower.instance.degree_names),
            "lower_group_notes": list(self.lower_notes),
            "lower_group_placed_degrees": [[str(degree), int(note)] for degree, note in self.lower_placed],
            "lower_group_max_note": max(self.lower_notes) if self.lower_notes else None,
            "lower_2note_fixed_register_version": BALLAD_SPREAD_2PLUS3_LOWER_UPPER_FIX_VERSION if self.recipe_contract.lower_group.note_count == 2 else None,
            "lower_2note_foundation_mode": self.register_policy.to_debug_dict().get("lower_2note_foundation_mode"),
            "rooted_bass_anchor_version": BALLAD_SPREAD_2PLUS3_ROOTED_BASS_ANCHOR_VERSION if int(self.recipe_contract.lower_group.note_count) in {2, 3} and bool(self.register_policy.rooted_bass_anchor_enabled) else None,
            "rooted_bass_anchor_enabled": bool(self.register_policy.rooted_bass_anchor_enabled),
            "rooted_bass_anchor_passed": _rooted_bass_anchor_passed(self.lower, self.upper_placed) if bool(self.register_policy.rooted_bass_anchor_enabled) else None,
            "root_bass_anchor_note": _root_bass_note_from_lower(self.lower),
            "root_bass_anchor_low": int(self.register_policy.root_bass_anchor_low),
            "root_bass_anchor_high": int(self.register_policy.root_bass_anchor_high),
            "root_bass_anchor_target": int(self.register_policy.root_bass_anchor_target),
            "whole_register_low": int(self.register_policy.whole_register_low),
            "whole_register_high": int(self.register_policy.whole_register_high),
            "root_bass_anchor_high_tail_semitones": int(self.register_policy.root_bass_anchor_high_tail_semitones),
            "root_bass_anchor_high_tail_max_lower_span": int(self.register_policy.root_bass_anchor_high_tail_max_lower_span),
            "root_bass_anchor_high_tail_start": int(self.register_policy.root_bass_anchor_high) - int(self.register_policy.root_bass_anchor_high_tail_semitones),
            "root_bass_anchor_high_tail_span_guard_enabled": _root_anchor_tail_span_guard_enabled(self.recipe_contract),
            "lower_group_anchor_tail_span_guard_passed": (_root_anchor_tail_span_guard_passed(self.lower, self.register_policy) if _root_anchor_tail_span_guard_enabled(self.recipe_contract) else None) if bool(self.register_policy.rooted_bass_anchor_enabled) else None,
            "upper_source_ref_id": self.upper_source.ref_id,
            "upper_source_family": self.upper_source.source_family,
            "upper_source_degrees": list(self.upper_source.degree_names),
            "upper_source_metadata": list(getattr(self.upper_source, "source_metadata", ()) or ()),
            "upper_structure_spread_pilot_version": UPPER_STRUCTURE_SPREAD_PILOT_VERSION if _is_upper_structure_source(self.upper_source) else None,
            "upper_structure_source_enabled": _is_upper_structure_source(self.upper_source),
            "upper_structure_density": int(self.upper_source.note_count) if _is_upper_structure_source(self.upper_source) else None,
            "upper_structure_source_id": _upper_structure_source_id(self.upper_source),
            "upper_structure_lower_mode": _upper_structure_lower_mode(self.lower.instance.recipe.recipe_id) if _is_upper_structure_source(self.upper_source) else None,
            "upper_structure_lower_root_shell_tail_gate_passed": _upper_structure_root_shell_tail_gate_passed(self.lower, self.register_policy) if _is_upper_structure_source(self.upper_source) and self.lower.instance.recipe.recipe_id == LowerGroupRecipeId.ROOT_THIRD_SEVENTH else None,
            "upper_source_degrees": list(self.upper_source.degree_names),
            "spread_3plus4_upper_4note_color_only_version": BALLAD_SPREAD_3PLUS4_COLOR_UPPER_VERSION if self.recipe_contract.recipe_id == "spread_3plus4_contract" else None,
            "spread_3plus4_upper_4note_color_only_enabled": self.recipe_contract.recipe_id == "spread_3plus4_contract",
            "spread_3plus4_upper_source_color_passed": (_is_expanded_upper_4note_color(self.upper_source) if self.recipe_contract.recipe_id == "spread_3plus4_contract" else None),
            "spread_3plus4_a1_g5_register_version": "v2_2_76" if self.recipe_contract.recipe_id == "spread_3plus4_contract" else None,
            "spread_3plus4_musical_closure_version": BALLAD_SPREAD_3PLUS4_MUSICAL_CLOSURE_VERSION if self.recipe_contract.recipe_id == "spread_3plus4_contract" else None,
            "spread_3plus4_register_aware_lower_compression_enabled": self.recipe_contract.recipe_id == "spread_3plus4_contract",
            "spread_3plus4_lower_upper3_compressed_within_root_octave": (self.recipe_contract.recipe_id == "spread_3plus4_contract" and "upper3" in self.lower.instance.role_names and self.lower.span_semitones <= 12),
            "spread_3plus4_upper_rootless_color_preferred": self.recipe_contract.recipe_id == "spread_3plus4_contract",
            "spread_3plus4_upper_rootless_color_passed": (self.recipe_contract.recipe_id == "spread_3plus4_contract" and _is_rootless_upper_4note_color(self.upper_source)),
            "upper_source_contains_root_degree": any(str(degree) in {"R", "1"} for degree in self.upper_source.degree_names),
            "upper_group_notes": list(self.upper_notes),
            "upper_group_degrees": [str(degree) for degree, _note in self.upper_placed],
            "upper_group_min_note": min(self.upper_notes) if self.upper_notes else None,
            "upper_3note_closed_groupwise_vl_version": BALLAD_SPREAD_2PLUS3_CLOSED_UPPER_GROUPWISE_VL_VERSION if self.recipe_contract.upper_source.note_count == 3 else None,
            "upper_projection_method": self.upper_projection_method,
            "upper_projection_metadata": dict(self.upper_projection_metadata),
            "source_integrity_notes": list(_spread_candidate_source_integrity_notes(self.chord_symbol, self.degrees)),
            "source_preserves_seventh_chord_identity": _spread_candidate_preserves_seventh_chord_identity(self.chord_symbol, self.degrees),
            "ballad_spread_1plus3_pilot_version": BALLAD_SPREAD_1PLUS3_PILOT_VERSION if self.recipe_contract.recipe_id == "spread_1plus3_contract" else None,
            "ballad_spread_2plus3_pilot_version": BALLAD_SPREAD_2PLUS3_PILOT_VERSION if self.recipe_contract.recipe_id == "spread_2plus3_contract" else None,
            "ballad_spread_2plus4_pilot_version": BALLAD_SPREAD_2PLUS4_PILOT_VERSION if self.recipe_contract.recipe_id == "spread_2plus4_contract" else None,
            "ballad_spread_3plus3_pilot_version": BALLAD_SPREAD_3PLUS3_PILOT_VERSION if self.recipe_contract.recipe_id == "spread_3plus3_contract" else None,
            "ballad_spread_3plus4_pilot_version": BALLAD_SPREAD_3PLUS4_PILOT_VERSION if self.recipe_contract.recipe_id == "spread_3plus4_contract" else None,
            "ballad_spread_3plus3_lower_recipe_register_fix_version": BALLAD_SPREAD_3PLUS3_LOWER_RECIPE_REGISTER_FIX_VERSION if self.recipe_contract.recipe_id in {"spread_3plus3_contract", "spread_3plus4_contract"} else None,
            "ballad_spread_3plus3_lower_span_overlap_fix_version": BALLAD_SPREAD_3PLUS3_LOWER_SPAN_OVERLAP_FIX_VERSION if self.recipe_contract.recipe_id in {"spread_3plus3_contract", "spread_3plus4_contract"} else None,
            "spread_lower_foundation_quality_gate_version": SPREAD_LOWER_FOUNDATION_QUALITY_GATE_VERSION if int(self.recipe_contract.lower_group.note_count) in {2, 3} else None,
            "lower_foundation_quality_family": _lower_foundation_quality_family(self.chord_symbol),
            "lower_foundation_recipe_family": _lower_recipe_quality_family(self.lower.instance.recipe.recipe_id),
            "upper_lower_note_overlap_guard_enabled": self.recipe_contract.recipe_id in {"spread_3plus3_contract", "spread_3plus4_contract"},
            "group_gap_semitones": self.group_gap_semitones,
            "overall_span_semitones": self.overall_span_semitones,
            "group_gap_guard": {
                "min_group_gap": int(self.register_policy.min_group_gap),
                "max_group_gap": int(self.register_policy.max_group_gap),
                "actual_group_gap": self.group_gap_semitones,
            },
            "span_guard": {
                "max_overall_span": int(self.register_policy.max_overall_span),
                "actual_overall_span": self.overall_span_semitones,
            },
            "low_register_density_guard": {
                "enabled": bool(self.register_policy.low_register_density_guard_enabled),
                "threshold": int(self.register_policy.low_register_density_threshold),
                "max_notes_below": int(self.register_policy.low_register_density_max_notes_below),
                "actual_notes_below": sum(1 for note in self.notes if int(note) < int(self.register_policy.low_register_density_threshold)),
                "version": LOW_REGISTER_DENSITY_GUARD_VERSION if self.register_policy.low_register_density_guard_enabled else None,
            },
            "register_policy": self.register_policy.to_debug_dict(),
            "is_legal": self.is_legal,
            "legality_reason": self.legality_reason,
            "spread_projection_placed": True,
            "source_oriented_not_placed": False,
            "final_placed_closed_open_result_reuse_allowed": False,
            "notes_only": True,
            "runtime_enabled": self.runtime_enabled,
            "no_expression_or_pedal": True,
        }

    def to_debug_dict(self) -> dict[str, object]:
        return {
            **self.metadata,
            "placed_degrees": [[degree, int(note)] for degree, note in self.placed_degrees],
            "notes": list(self.notes),
            "degrees": list(self.degrees),
        }


@dataclass(frozen=True)
class SpreadProjectionResult:
    """Basic SPREAD projection result for one contract and chord symbol."""

    chord_symbol: str
    recipe_contract: SpreadRecipeContract
    candidates: tuple[SpreadProjectionCandidate, ...]
    register_policy: SpreadProjectionRegisterPolicy
    runtime_enabled: bool = False

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)

    @property
    def legal_candidate_count(self) -> int:
        return sum(1 for candidate in self.candidates if candidate.is_legal)

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
            "basic_spread_projection_version": BASIC_SPREAD_PROJECTION_VERSION,
            "chord_symbol": self.chord_symbol,
            "recipe_contract": self.recipe_contract.to_debug_dict(),
            "candidate_count": self.candidate_count,
            "legal_candidate_count": self.legal_candidate_count,
            "register_policy": self.register_policy.to_debug_dict(),
            "candidates": [candidate.to_debug_dict() for candidate in self.candidates],
            "runtime_enabled": self.runtime_enabled,
            "notes_only": True,
            "no_expression_or_pedal": True,
        }


@dataclass(frozen=True)


class BalladSpreadGroupingMixScene(str, Enum):
    """Scene buckets for the explicit Ballad SPREAD grouping mix policy.

    The scene only chooses a SPREAD contract id.  It does not create notes,
    change expression, or enable default Jazz Ballad runtime by itself.
    """

    NORMAL_COMPING = "normal_comping"
    CHORUS_LIFT = "chorus_lift"
    ENDING_CLIMAX = "ending_climax"


BALLAD_SPREAD_GROUPING_MIX_DEFAULT_WEIGHTS: dict[str, dict[str, int]] = {
    BalladSpreadGroupingMixScene.NORMAL_COMPING.value: {
        # v2_6_10: ordinary Ballad comping should no longer collapse to old
        # 4-note SPREAD, but it also should not become constantly huge.  The
        # 5-note 2+3 contract is the default grouped-spread body; 2+4/3+3 are
        # reserved for lift/climax or occasional fuller support.
        # v2_6_30: 1+4 returns as a low-frequency upper4-color lane.
        # The stable 5-note body remains 2+3; 6-note support still comes from
        # 2+4/3+3, so 1+4 must not become the default comping body.
        "spread_1plus4_contract": 4,
        "spread_2plus3_contract": 70,
        "spread_2plus4_contract": 22,
        "spread_3plus3_contract": 4,
        "spread_3plus4_contract": 0,
    },
    BalladSpreadGroupingMixScene.CHORUS_LIFT.value: {
        "spread_1plus4_contract": 3,
        "spread_2plus3_contract": 45,
        "spread_2plus4_contract": 36,
        "spread_3plus3_contract": 14,
        "spread_3plus4_contract": 2,
    },
    BalladSpreadGroupingMixScene.ENDING_CLIMAX.value: {
        "spread_1plus4_contract": 0,
        "spread_2plus3_contract": 17,
        "spread_2plus4_contract": 35,
        "spread_3plus3_contract": 35,
        "spread_3plus4_contract": 13,
    },
}


@dataclass(frozen=True)
class BalladSpreadGroupingMixDecision:
    """One explicit, event-scoped grouping-mix decision.

    This object is a policy/audit decision: it selects which existing SPREAD
    contract to request for a dry-run/listening pilot.  Candidate conversion and
    default style runtime remain opt-in and closed by default.
    """

    enabled: bool
    scene: BalladSpreadGroupingMixScene
    selected_contract_id: str | None
    weights: dict[str, int]
    slot: int
    total_weight: int
    reason: str
    texture_state_id: str = ""
    texture_family: str = ""
    compatible_contract_ids: tuple[str, ...] = ()
    texture_primary_contract_id: str | None = None
    texture_state_enabled: bool = True
    source: str = "policy_metadata"
    style_runtime_default_enabled: bool = False
    runtime_enabled: bool = False

    @property
    def selected_grouping(self) -> str | None:
        mapping = {
            "spread_1plus4_contract": "1+4",
            "spread_2plus3_contract": "2+3",
            "spread_2plus4_contract": "2+4",
            "spread_3plus3_contract": "3+3",
            "spread_3plus4_contract": "3+4",
        }
        return mapping.get(str(self.selected_contract_id)) if self.selected_contract_id else None

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "ballad_spread_grouping_mix_policy_version": BALLAD_SPREAD_GROUPING_MIX_POLICY_VERSION,
            "enabled": bool(self.enabled),
            "scene": self.scene.value,
            "selected_contract_id": self.selected_contract_id,
            "selected_grouping": self.selected_grouping,
            "weights": dict(self.weights),
            "slot": int(self.slot),
            "total_weight": int(self.total_weight),
            "reason": self.reason,
            "texture_state_id": self.texture_state_id,
            "texture_family": self.texture_family,
            "compatible_contract_ids": list(self.compatible_contract_ids),
            "texture_primary_contract_id": self.texture_primary_contract_id,
            "texture_state_enabled": bool(self.texture_state_enabled),
            "source": self.source,
            "style_runtime_default_enabled": bool(self.style_runtime_default_enabled),
            "runtime_enabled": bool(self.runtime_enabled),
            "candidate_conversion_allowed": False,
            "notes_only": True,
            "no_expression_or_pedal": True,
            "does_not_change_medium_swing_or_bossa": True,
        }


def resolve_ballad_spread_grouping_mix_policy(
    policy: Any | None = None,
    *,
    event_context: dict[str, object] | None = None,
    explicit_enable: bool | None = None,
) -> BalladSpreadGroupingMixDecision:
    """Resolve the v2_2_82 Ballad SPREAD grouping mix policy.

    The default is disabled.  Enabling this helper only returns a selected
    existing SPREAD contract id; callers must still explicitly open the existing
    SPREAD dry-run/listening guard.
    """

    values = _ballad_spread_grouping_mix_values(policy)
    if explicit_enable is not None:
        values["explicit_enable_argument"] = bool(explicit_enable)
    enabled = _spread_bool_any(
        values,
        (
            "explicit_enable_argument",
            "enabled",
            "dry_run_enabled",
            "grouping_mix_enabled",
            "ballad_spread_grouping_mix_enabled",
        ),
        default=False,
    )
    scene = _ballad_spread_grouping_mix_scene(values, event_context or {})
    base_weights = _ballad_spread_grouping_mix_weights(values, scene)
    texture = _ballad_spread_grouping_texture_state(values, event_context or {}, scene, base_weights)
    weights = dict(texture["weights"])
    slot = _ballad_spread_grouping_mix_slot(event_context or {}, values, scene=scene)
    total = sum(max(0, int(value)) for value in weights.values())
    selected = _select_ballad_spread_grouping_contract(weights, slot) if enabled else None
    reason = "selected_existing_spread_contract_from_texture_state_mix" if selected else (
        "ballad_spread_grouping_mix_policy_disabled" if not enabled else "no_positive_texture_state_grouping_weights"
    )
    return BalladSpreadGroupingMixDecision(
        enabled=bool(enabled),
        scene=scene,
        selected_contract_id=selected,
        weights=weights,
        slot=int(slot),
        total_weight=int(total),
        reason=reason,
        texture_state_id=str(texture["texture_state_id"]),
        texture_family=str(texture["texture_family"]),
        compatible_contract_ids=tuple(str(item) for item in texture["compatible_contract_ids"]),
        texture_primary_contract_id=str(texture["primary_contract_id"]) if texture.get("primary_contract_id") else None,
        texture_state_enabled=True,
        source="explicit_argument" if explicit_enable is not None else "policy_metadata",
        style_runtime_default_enabled=False,
        runtime_enabled=False,
    )


def ballad_spread_grouping_mix_policy_debug(
    policy: Any | None = None,
    *,
    event_context: dict[str, object] | None = None,
    explicit_enable: bool | None = None,
) -> dict[str, object]:
    decision = resolve_ballad_spread_grouping_mix_policy(
        policy,
        event_context=event_context,
        explicit_enable=explicit_enable,
    )
    return {
        "ballad_spread_grouping_mix_policy_version": BALLAD_SPREAD_GROUPING_MIX_POLICY_VERSION,
        "layer": "core.voicing.disposition.spread",
        "purpose": "Ballad SPREAD grouping mix policy draft / dry-run audit",
        "decision": decision.to_debug_dict(),
        "style_runtime_default_enabled": False,
        "candidate_conversion_allowed": False,
        "runtime_enabled": False,
        "notes_only": True,
        "no_expression_or_pedal": True,
    }


def _ballad_spread_grouping_mix_values(policy: Any | None) -> dict[str, object]:
    try:
        metadata = dict(getattr(policy, "metadata", None) or {})
    except Exception:
        metadata = {}
    if not metadata and isinstance(policy, dict):
        metadata = dict(policy.get("metadata") or policy)
    nested = (
        metadata.get("ballad_spread_grouping_mix_policy")
        or metadata.get("ballad_spread_grouping_mix")
        or {}
    )
    if not isinstance(nested, dict):
        nested = {"enabled": nested}
    return {**metadata, **nested}


def _ballad_spread_grouping_mix_scene(
    values: dict[str, object],
    event_context: dict[str, object],
) -> BalladSpreadGroupingMixScene:
    explicit = event_context.get("ballad_spread_grouping_mix_scene") or values.get("scene") or values.get("mix_scene")
    if explicit:
        text = str(getattr(explicit, "value", explicit)).strip().lower().replace("-", "_")
        aliases = {
            "normal": BalladSpreadGroupingMixScene.NORMAL_COMPING,
            "normal_comping": BalladSpreadGroupingMixScene.NORMAL_COMPING,
            "ordinary": BalladSpreadGroupingMixScene.NORMAL_COMPING,
            "lift": BalladSpreadGroupingMixScene.CHORUS_LIFT,
            "chorus_lift": BalladSpreadGroupingMixScene.CHORUS_LIFT,
            "medium_high": BalladSpreadGroupingMixScene.CHORUS_LIFT,
            "ending": BalladSpreadGroupingMixScene.ENDING_CLIMAX,
            "climax": BalladSpreadGroupingMixScene.ENDING_CLIMAX,
            "ending_climax": BalladSpreadGroupingMixScene.ENDING_CLIMAX,
            "final_cadence": BalladSpreadGroupingMixScene.ENDING_CLIMAX,
        }
        if text in aliases:
            return aliases[text]
        try:
            return BalladSpreadGroupingMixScene(text)
        except ValueError:
            return BalladSpreadGroupingMixScene.NORMAL_COMPING

    chorus = _spread_safe_int(event_context.get("region_chorus_index"), default=0)
    total = _spread_safe_int(event_context.get("region_total_choruses"), default=0)
    bar = _spread_safe_int(event_context.get("region_bar_index"), default=-1)
    section_role = str(event_context.get("region_section_role") or "").lower()
    phrase = str(event_context.get("region_phrase") or "").upper()
    if total > 0 and chorus >= total - 1 and (bar >= 28 or section_role in {"ending", "final"}):
        return BalladSpreadGroupingMixScene.ENDING_CLIMAX
    if total > 0 and chorus >= 1:
        return BalladSpreadGroupingMixScene.CHORUS_LIFT
    if phrase in {"B", "BRIDGE"}:
        return BalladSpreadGroupingMixScene.CHORUS_LIFT
    return BalladSpreadGroupingMixScene.NORMAL_COMPING


def _ballad_spread_grouping_texture_state(
    values: dict[str, object],
    event_context: dict[str, object],
    scene: BalladSpreadGroupingMixScene,
    base_weights: dict[str, int],
) -> dict[str, object]:
    """Resolve a phrase/scene-level grouping palette before event selection.

    v2_2_82 deliberately avoids free event-by-event random switching across all
    SPREAD groupings. A texture state chooses a compatible contract palette for
    a phrase/block; individual events may still vary inside that palette, but
    note-count changes are limited to musical neighbors such as 1+4 <-> 2+4 or
    2+4 <-> 3+3/3+4.
    """

    if _spread_bool_any(values, ("disable_texture_state", "event_level_random_grouping"), default=False):
        return {
            "texture_state_id": "disabled_event_level_weights",
            "texture_family": "legacy_event_weighted",
            "primary_contract_id": None,
            "compatible_contract_ids": tuple(base_weights.keys()),
            "weights": dict(base_weights),
        }

    chorus = _spread_safe_int(event_context.get("region_chorus_index"), default=0)
    bar = _spread_safe_int(event_context.get("region_bar_index"), default=0)
    phrase = str(event_context.get("region_phrase") or "").upper() or f"BLOCK{max(0, bar) // 8}"
    block = max(0, bar) // 8
    scope_key = f"c{chorus}_{phrase}_b{block}_{scene.value}"
    seed = sum(ord(ch) for ch in scope_key) % 100

    if scene == BalladSpreadGroupingMixScene.NORMAL_COMPING:
        # v2_6_10: choose a phrase-level density lane first.  Normal Ballad
        # comping is centered on 5-note 2+3 SPREAD; 6-note lanes are controlled
        # lift options, not the default fix for retiring 4-note 1+3/2+2.
        if seed < 70:
            family = "rooted_5note_phrase"
            compatible = ("spread_2plus3_contract", "spread_1plus4_contract")
            primary = "spread_2plus3_contract"
        elif seed < 92:
            family = "rooted_5_to_6_support_phrase"
            compatible = ("spread_2plus3_contract", "spread_2plus4_contract")
            primary = "spread_2plus3_contract"
        else:
            family = "controlled_full_phrase"
            compatible = ("spread_2plus4_contract", "spread_3plus3_contract")
            primary = "spread_2plus4_contract"
    elif scene == BalladSpreadGroupingMixScene.CHORUS_LIFT:
        if seed < 45:
            family = "lift_5_to_6_phrase"
            compatible = ("spread_2plus3_contract", "spread_2plus4_contract")
            primary = "spread_2plus3_contract"
        elif seed < 85:
            family = "lift_6note_support_phrase"
            compatible = ("spread_2plus4_contract", "spread_3plus3_contract")
            primary = "spread_2plus4_contract"
        else:
            family = "lift_upper4_climax_hint"
            compatible = ("spread_1plus4_contract", "spread_2plus4_contract", "spread_3plus4_contract")
            primary = "spread_2plus4_contract"
    else:
        family = "ending_climax_phrase"
        compatible = ("spread_2plus4_contract", "spread_3plus3_contract", "spread_3plus4_contract")
        primary = "spread_3plus3_contract"

    weights = {contract: 0 for contract in base_weights}
    for contract in compatible:
        if int(base_weights.get(contract, 0)) > 0:
            weights[contract] = int(base_weights.get(contract, 0))
    if primary in weights and weights[primary] > 0:
        weights[primary] = max(int(weights[primary]), int(sum(weights.values()) * 0.55) or int(weights[primary]))
    if not any(int(value) > 0 for value in weights.values()):
        weights = dict(base_weights)
    # v2_6_30: a contract with zero weight is not part of the ordinary
    # compatible runtime pool.  1+4 now enters only when its explicit
    # low-frequency weight is positive; it must not leak in as a zero-weight
    # neighbor.
    active_compatible = tuple(contract for contract in compatible if int(weights.get(contract, 0)) > 0)
    if not active_compatible:
        active_compatible = tuple(contract for contract, value in weights.items() if int(value) > 0)
    active_primary = primary if primary in active_compatible else (active_compatible[0] if active_compatible else primary)
    return {
        "texture_state_id": scope_key,
        "texture_family": family,
        "primary_contract_id": active_primary,
        "compatible_contract_ids": active_compatible,
        "weights": weights,
    }


def _ballad_spread_grouping_mix_weights(
    values: dict[str, object],
    scene: BalladSpreadGroupingMixScene,
) -> dict[str, int]:
    default = BALLAD_SPREAD_GROUPING_MIX_DEFAULT_WEIGHTS[scene.value]
    raw_by_scene = values.get("weights_by_scene") or values.get("grouping_weights_by_scene") or {}
    raw = {}
    if isinstance(raw_by_scene, dict):
        raw = raw_by_scene.get(scene.value) or raw_by_scene.get(scene.name) or {}
    if not isinstance(raw, dict):
        raw = {}
    allowed = set().union(*(set(weights.keys()) for weights in BALLAD_SPREAD_GROUPING_MIX_DEFAULT_WEIGHTS.values()))
    out: dict[str, int] = {}
    for contract_id, value in {**default, **raw}.items():
        if str(contract_id) not in allowed:
            continue
        out[str(contract_id)] = max(0, _spread_safe_int(value, default=0))
    return out


def _ballad_spread_grouping_mix_slot(
    event_context: dict[str, object],
    values: dict[str, object],
    *,
    scene: BalladSpreadGroupingMixScene | None = None,
) -> int:
    cycle = max(1, _spread_safe_int(values.get("weight_cycle"), default=100))
    region_id = str(event_context.get("region_id") or "")
    import re as _re

    match = _re.search(r"c(\d+)_b(\d+)_ch(\d+)", region_id)
    if match:
        chorus, bar, chord_index = (int(item) for item in match.groups())
    else:
        chorus = _spread_safe_int(event_context.get("region_chorus_index"), default=0)
        bar = _spread_safe_int(event_context.get("region_bar_index"), default=0)
        chord_index = _spread_safe_int(event_context.get("region_chord_index"), default=0)

    # Use a stable lightweight hash instead of raw sequential bar order.  This
    # gives the dry-run audit a representative weighted mix across small scene
    # samples while remaining deterministic and independent of Python's hash seed.
    return int((chorus * 53 + bar * 31 + chord_index * 17) % cycle)


def _select_ballad_spread_grouping_contract(weights: dict[str, int], slot: int) -> str | None:
    positive = [(contract, int(weight)) for contract, weight in weights.items() if int(weight) > 0]
    total = sum(weight for _, weight in positive)
    if total <= 0:
        return None
    pointer = int(slot) % total
    running = 0
    for contract, weight in positive:
        running += weight
        if pointer < running:
            return contract
    return positive[-1][0] if positive else None


def _spread_safe_int(value: object, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def spread_upper_source_refs() -> tuple[UpperSourceRef, ...]:
    """Return the reusable upper-source refs declared by the SPREAD contracts."""

    refs: list[UpperSourceRef] = []
    seen: set[str] = set()
    for contract in spread_recipe_contract_skeleton():
        ref = contract.upper_source
        if ref.ref_id in seen:
            continue
        seen.add(ref.ref_id)
        refs.append(ref)
    return tuple(refs)


def spread_upper_source_ref_by_id(ref_id: str) -> UpperSourceRef:
    """Look up a SPREAD upper source reference by contract id."""

    for ref in spread_upper_source_refs():
        if ref.ref_id == ref_id:
            return ref
    raise KeyError(f"unknown SPREAD upper source ref id: {ref_id!r}")


def adapt_spread_upper_source(
    chord_symbol: str,
    upper_source_ref: UpperSourceRef | str,
    policy: Any | None = None,
) -> SpreadUpperSourceAdapterResult:
    """Adapt existing voicing source/orientation resources for a SPREAD upper group."""

    ref = spread_upper_source_ref_by_id(upper_source_ref) if isinstance(upper_source_ref, str) else upper_source_ref
    return adapt_spread_upper_source_from_ref(chord_symbol, ref, policy)


def adapt_spread_upper_sources_for_contracts(
    chord_symbol: str,
    policy: Any | None = None,
) -> tuple[SpreadUpperSourceAdapterResult, ...]:
    """Adapt all upper-source refs referenced by the current SPREAD contracts."""

    return tuple(adapt_spread_upper_source(chord_symbol, ref, policy) for ref in spread_upper_source_refs())


def spread_upper_source_adapter_debug(chord_symbol: str = "Cmaj7", policy: Any | None = None) -> dict[str, object]:
    """Return debug payload for the v2_2_39 SPREAD upper-source adapter."""

    results = adapt_spread_upper_sources_for_contracts(chord_symbol, policy)
    return {
        "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
        "upper_source_adapter_version": UPPER_SOURCE_ADAPTER_VERSION,
        "layer": "core.voicing.disposition.spread",
        "implementation_owner": "core.voicing.disposition.spread_upper_sources",
        "purpose": "SPREAD upper source adapter using existing source/orientation/color/drop resources",
        "runtime_enabled": False,
        "notes_only": True,
        "no_expression_or_pedal": True,
        "source_oriented_not_placed": True,
        "final_placed_result_reuse_allowed": False,
        "results": [result.to_debug_dict() for result in results],
    }


from .spread_projection_core import (
    SPREAD_PROJECTION_CORE_SPLIT_VERSION,
    basic_spread_projection_debug,
    project_basic_spread_candidates,
    project_basic_spread_contract,
)


def _spread_float_value(values: dict[str, object], key: str, *, default: float) -> float:
    try:
        return float(values.get(key, default))
    except (TypeError, ValueError):
        return float(default)


def _spread_bool_any(values: dict[str, object], keys: tuple[str, ...], *, default: bool = False) -> bool:
    for key in keys:
        if key in values:
            return _spread_coerce_bool(values.get(key), default=default)
    return bool(default)


def _spread_coerce_bool(value: object, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return bool(default)
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on", "enabled", "enable", "open"}:
        return True
    if text in {"0", "false", "no", "n", "off", "disabled", "disable", "closed"}:
        return False
    return bool(default)


def _normalize_style_name(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def spread_recipe_contract_by_id(recipe_id: str) -> SpreadRecipeContract:
    """Look up a SPREAD contract by id without creating a second inventory."""

    for contract in spread_recipe_contract_skeleton():
        if contract.recipe_id == str(recipe_id):
            return contract
    raise KeyError(f"unknown SPREAD recipe contract id: {recipe_id!r}")



def _lower_recipe_ids_for_contract(
    contract: SpreadRecipeContract,
    policy: Any | None = None,
    *,
    chord_symbol: str | None = None,
) -> tuple[LowerGroupRecipeId, ...]:
    count = int(contract.lower_group.note_count)
    recipes = tuple(recipe.recipe_id for recipe in lower_group_recipe_inventory() if recipe.note_count == count)
    metadata = _spread_policy_metadata(policy)
    quality_gate_enabled = bool(metadata.get("spread_lower_foundation_quality_gate_enabled", True))
    quality_family = _lower_foundation_quality_family(chord_symbol) if chord_symbol else "unknown"

    if _upper_structure_lower_gate_enabled(metadata):
        # v2_2_83: upper-structure SPREAD sources are allowed only over a
        # clear shell or root+shell lower/foundation group. Keep this gate in
        # the lower recipe selector; upper structure remains a source family,
        # not a new projection system.
        if quality_gate_enabled and quality_family != "seventh_or_above":
            return ()
        if count == 2:
            return (LowerGroupRecipeId.THIRD_SEVENTH,) if LowerGroupRecipeId.THIRD_SEVENTH in recipes else ()
        if count == 3:
            allowed = (LowerGroupRecipeId.ROOT_SEVENTH_UPPER_THIRD, LowerGroupRecipeId.ROOT_THIRD_SEVENTH)
            return tuple(recipe for recipe in allowed if recipe in recipes)

    if count == 3:
        # v2_2_73: 3+4 is intentionally the thickest regular SPREAD pilot.
        # Its lower foundation should be more unified than 3+3: seventh-or-above
        # chords use root+7+upper3 only, while triad-family chords use
        # root+5+upper3 only. 3+3 keeps the broader quality-aware lower pool.
        is_3plus4 = str(contract.recipe_id) == "spread_3plus4_contract"
        if is_3plus4:
            seventh_family = (LowerGroupRecipeId.ROOT_SEVENTH_UPPER_THIRD,)
            triad_family = (LowerGroupRecipeId.ROOT_FIFTH_UPPER_THIRD,)
        else:
            # v2_2_73: 3-note lower foundations are not one homogeneous pool.
            # Seventh-or-above chords use shell-bearing lower foundations; triad
            # family chords use root+5 based lower foundations. Root+5+7 remains
            # outside the rooted 3-note SPREAD pool.
            seventh_family = (LowerGroupRecipeId.ROOT_THIRD_SEVENTH, LowerGroupRecipeId.ROOT_SEVENTH_UPPER_THIRD)
            triad_family = (LowerGroupRecipeId.ROOT_FIFTH_UPPER_ROOT, LowerGroupRecipeId.ROOT_FIFTH_UPPER_THIRD)
        if not quality_gate_enabled or quality_family == "unknown":
            allowed = (*seventh_family, *triad_family)
        elif quality_family == "seventh_or_above":
            allowed = seventh_family
        else:
            allowed = triad_family
        return tuple(recipe for recipe in allowed if recipe in recipes)
    if count != 2:
        return recipes

    mode = str(metadata.get("spread_lower_2note_foundation_mode", "rooted")).strip().lower()
    rootless = (LowerGroupRecipeId.THIRD_SEVENTH,)
    if mode in {"rootless", "guide", "guide_tones", "3+7", "third_seventh"}:
        allowed = rootless
    elif mode in {"all", "mixed", "legacy"}:
        allowed = (LowerGroupRecipeId.ROOT_THIRD, LowerGroupRecipeId.ROOT_FIFTH, LowerGroupRecipeId.ROOT_SEVENTH, *rootless)
    else:
        # v2_2_73: rooted 2-note lower foundations are also quality-aware.
        # root+5 is a triad/root-fifth foundation color; root+3/root+7 are
        # the seventh-family shell anchors.  Triad-family chords keep root+3
        # and root+5 available because no written seventh is present.
        if quality_gate_enabled and quality_family == "seventh_or_above":
            allowed = (LowerGroupRecipeId.ROOT_THIRD, LowerGroupRecipeId.ROOT_SEVENTH)
        elif quality_gate_enabled and quality_family == "triad_family":
            allowed = (LowerGroupRecipeId.ROOT_THIRD, LowerGroupRecipeId.ROOT_FIFTH)
        else:
            allowed = (LowerGroupRecipeId.ROOT_THIRD, LowerGroupRecipeId.ROOT_FIFTH, LowerGroupRecipeId.ROOT_SEVENTH)

    preferred = metadata.get("spread_lower_2note_preferred_recipe_id")
    strict = bool(metadata.get("spread_lower_2note_preferred_recipe_strict", False))
    if preferred:
        try:
            preferred_id = LowerGroupRecipeId(str(preferred))
        except ValueError:
            preferred_id = None
        if preferred_id in allowed:
            if strict:
                return (preferred_id,)
            return (preferred_id, *(item for item in allowed if item != preferred_id))
    return tuple(item for item in allowed if item in recipes)


def _lower_foundation_quality_family(chord_symbol: str | None) -> str:
    if not chord_symbol:
        return "unknown"
    try:
        chord = parse_chord(chord_symbol)
    except Exception:
        return "unknown"
    if chord.has_seventh or chord.extensions or chord.alterations or chord.is_dominant or chord.is_half_diminished or chord.is_fully_diminished:
        return "seventh_or_above"
    return "triad_family"


def _lower_recipe_quality_family(recipe_id: LowerGroupRecipeId | str) -> str:
    try:
        normalized = recipe_id if isinstance(recipe_id, LowerGroupRecipeId) else LowerGroupRecipeId(str(recipe_id))
    except ValueError:
        return "unknown"
    if normalized in {LowerGroupRecipeId.ROOT_THIRD_SEVENTH, LowerGroupRecipeId.ROOT_SEVENTH_UPPER_THIRD, LowerGroupRecipeId.ROOT_THIRD, LowerGroupRecipeId.ROOT_SEVENTH}:
        return "seventh_shell_family"
    if normalized in {LowerGroupRecipeId.ROOT_FIFTH_UPPER_ROOT, LowerGroupRecipeId.ROOT_FIFTH_UPPER_THIRD, LowerGroupRecipeId.ROOT_FIFTH}:
        return "triad_root_fifth_family"
    if normalized == LowerGroupRecipeId.THIRD_SEVENTH:
        return "rootless_guide_family"
    return "neutral"


def _preferred_lower_recipe_id_from_policy(
    contract: SpreadRecipeContract,
    policy: Any | None = None,
) -> LowerGroupRecipeId | None:
    if int(contract.lower_group.note_count) != 2:
        return None
    metadata = _spread_policy_metadata(policy)
    preferred = metadata.get("spread_lower_2note_preferred_recipe_id")
    if not preferred:
        return None
    try:
        preferred_id = LowerGroupRecipeId(str(preferred))
    except ValueError:
        return None
    allowed = set(_lower_recipe_ids_for_contract(contract, policy))
    return preferred_id if preferred_id in allowed else None


def _spread_policy_metadata(policy: Any | None) -> dict[str, object]:
    try:
        return dict(getattr(policy, "metadata", None) or {})
    except Exception:
        return dict(policy or {}) if isinstance(policy, dict) else {}



def _spread_runtime_policy_for_contract(contract: SpreadRecipeContract, policy: Any | None) -> Any | None:
    from dataclasses import replace

    from jammate_engine.core.voicing.policy import ColorPolicyMode, VoicingPolicy

    if isinstance(policy, VoicingPolicy):
        base = policy
    elif policy is None:
        base = VoicingPolicy()
    else:
        base = VoicingPolicy.from_legacy_dict(dict(policy or {}))

    base_metadata = dict(getattr(base, "metadata", None) or {})
    upper_structure_enabled = _upper_structure_enabled_for_policy(base)
    if not _is_spread_3plus4_contract(contract) and not upper_structure_enabled:
        return policy

    metadata = {**base_metadata}
    harmonic_expansion_enabled = bool(getattr(base, "harmonic_expansion_enabled", False))
    color_policy_mode = getattr(base, "color_policy_mode", ColorPolicyMode.CHORD_SYMBOL_ONLY)

    if _is_spread_3plus4_contract(contract):
        metadata.update({
            "spread_3plus4_upper_4note_color_only_enabled": True,
            "spread_3plus4_upper_4note_color_only_version": BALLAD_SPREAD_3PLUS4_COLOR_UPPER_VERSION,
            "spread_3plus4_local_harmonic_expansion_for_color_upper": True,
            "spread_upper_4note_prefer_expanded_color": True,
            "spread_upper_4note_expanded_color_only": True,
            "spread_3plus4_upper_rootless_color_preferred": True,
            "harmonic_expansion_enabled": True,
            "color_policy_mode": ColorPolicyMode.STYLE_SAFE_EXTENSIONS.value,
            "harmonic_expansion_target_families": [
                "rootless_A",
                "rootless_B",
                "rooted_color",
            ],
        })
        harmonic_expansion_enabled = True
        color_policy_mode = ColorPolicyMode.STYLE_SAFE_EXTENSIONS

    if upper_structure_enabled:
        # v2_2_84: Upper Structure entry does not itself authorize harmonic
        # expansion. It only opens the source-family door; sources.upper_structure
        # then gates actual color by harmonic_expansion + altered_dominant policy.
        # The low-register and lower-mode guards remain contract-local here.
        metadata.update({
            "spread_upper_structure_enabled": True,
            "spread_upper_structure_pilot_version": UPPER_STRUCTURE_SPREAD_PILOT_VERSION,
            "spread_upper_structure_policy_gate_version": UPPER_STRUCTURE_SPREAD_PILOT_VERSION,
            "spread_upper_structure_lower_gate_enabled": True,
            "spread_low_register_density_guard_enabled": True,
            "spread_low_register_density_guard_version": LOW_REGISTER_DENSITY_GUARD_VERSION,
            "spread_low_register_density_threshold": int(metadata.get("spread_low_register_density_threshold", 40)),
            "spread_low_register_density_max_notes_below": int(metadata.get("spread_low_register_density_max_notes_below", 1)),
        })

    return replace(
        base,
        harmonic_expansion_enabled=bool(harmonic_expansion_enabled),
        color_policy_mode=color_policy_mode,
        metadata=metadata,
    )


def _filter_upper_options_for_spread_contract(
    options: tuple[SpreadUpperSourceOption, ...] | list[SpreadUpperSourceOption],
    contract: SpreadRecipeContract,
    policy: Any | None = None,
) -> tuple[SpreadUpperSourceOption, ...]:
    metadata = _spread_policy_metadata(policy)
    upper_structure_options = tuple(option for option in options if _is_upper_structure_source(option))
    if upper_structure_options:
        if bool(metadata.get("spread_upper_structure_only", False)):
            return upper_structure_options
        if bool(metadata.get("spread_upper_structure_prefer", True)):
            options = (*upper_structure_options, *(option for option in options if not _is_upper_structure_source(option)))
    if _is_spread_3plus4_contract(contract) and int(contract.upper_source.note_count) == 4:
        # v2_2_76: 3+4 is the thick/climax SPREAD texture, not a normal
        # root/third/fifth/seventh 7-note stack.  Its upper 4-note projection
        # must therefore come from color-bearing 4-note sources only.  This
        # remains contract-local so 1+4 / 2+4 can keep the broader upper
        # 4-note logic. Upper-structure 4-note sources are color-bearing by
        # construction and are therefore valid here too.
        color_options = tuple(
            option for option in options
            if _is_expanded_upper_4note_color(option) or _is_upper_structure_source(option)
        )
        return _prioritize_spread_3plus4_upper_color_options(color_options)
    allow_shell_plus_one = bool(metadata.get("spread_upper_3note_shell_plus_1_allowed", False))
    if int(contract.upper_source.note_count) != 3 or allow_shell_plus_one:
        return tuple(options)
    filtered = tuple(option for option in options if not _is_upper_3note_shell_plus_one(option))
    return filtered


def _is_expanded_upper_3note_color(option: SpreadUpperSourceOption) -> bool:
    if _is_upper_structure_source(option) and int(option.note_count) == 3:
        return True
    if option.kind != SpreadUpperSourceKind.THREE_NOTE_CONTENT_SOURCE:
        return False
    if option.source_family != "shell_plus_color":
        return False
    if "shell_expansion_component_root" in option.source_metadata or "shell_expansion_component_5" in option.source_metadata:
        return False
    return any(str(note).startswith("shell_expansion_component_") for note in option.source_metadata)


def _is_expanded_upper_4note_color(option: SpreadUpperSourceOption) -> bool:
    if _is_upper_structure_source(option) and int(option.note_count) == 4:
        return True
    if option.kind != SpreadUpperSourceKind.DROP_FAMILY_DERIVED_PROJECTION_BLOCK:
        return False
    if int(option.note_count) != 4:
        return False

    family = str(option.source_family)
    metadata = set(str(item) for item in option.source_metadata)
    if family in {"rootless_A", "rootless_B"}:
        return any(
            marker in metadata
            for marker in (
                "harmonic_expansion_color_used",
                "rootless_ab_harmonic_expansion_enabled",
                "rootless_ab_explicit_chord_symbol_color_used",
            )
        )
    if family == "rooted_color":
        return any(
            marker in metadata
            for marker in (
                "harmonic_expansion_color_used",
                "explicit_chord_symbol_color_used",
                "rooted_color_4note_explicit_9_source_family",
                "rooted_color_4note_explicit_13_source_family",
                "rooted_color_4note_explicit_eleventh_source_family",
                "rooted_color_4note_altered_dominant_rooted_source",
                "rooted_color_4note_6_9_source_family",
                "rooted_color_4note_add9_source_family",
                "rooted_color_4note_harmonic_expansion_source_family",
                "rooted_color_4note_1_3_7_9_alias",
                "rooted_color_4note_1_3_7_13_alias",
            )
        )
    if family in {"major_triad", "minor_triad", "diminished_triad", "augmented_triad", "sus2_triad", "sus4_triad"}:
        return any(str(marker).startswith("triad_harmonic_expansion_low_order_") for marker in metadata)
    return False


def _is_rootless_upper_4note_color(option: SpreadUpperSourceOption) -> bool:
    return bool(_is_expanded_upper_4note_color(option) and str(option.source_family) in {"rootless_A", "rootless_B"})


def _prioritize_spread_3plus4_upper_color_options(
    options: tuple[SpreadUpperSourceOption, ...] | list[SpreadUpperSourceOption],
) -> tuple[SpreadUpperSourceOption, ...]:
    # v2_2_76: give rootless A/B color blocks priority before max_upper_options
    # slicing happens.  Interleaving keeps the isolation audit from collapsing
    # into a single rooted/rootless orientation family while preserving rooted
    # color or triad/add fallback when rootless color is unavailable.
    rootless_a = [option for option in options if str(option.source_family) == "rootless_A"]
    rootless_b = [option for option in options if str(option.source_family) == "rootless_B"]
    rooted = [option for option in options if str(option.source_family) == "rooted_color"]
    fallback = [
        option for option in options
        if str(option.source_family) not in {"rootless_A", "rootless_B", "rooted_color"}
    ]
    interleaved: list[SpreadUpperSourceOption] = []
    max_len = max(len(rootless_a), len(rootless_b), 0)
    for index in range(max_len):
        if index < len(rootless_a):
            interleaved.append(rootless_a[index])
        if index < len(rootless_b):
            interleaved.append(rootless_b[index])
    return tuple([*interleaved, *rooted, *fallback])


def _prefer_rootless_upper_color_for_spread_3plus4(
    candidates: list[SpreadProjectionCandidate],
    contract: SpreadRecipeContract,
) -> list[SpreadProjectionCandidate]:
    if not _is_spread_3plus4_contract(contract):
        return candidates
    # v2_2_76: 3+4 already carries root + seventh + upper-third in the lower
    # foundation.  For seventh-family chords, keep the upper 4-note block as a
    # color/projection block rather than another rooted R-3-7-9 stack.  Triad
    # chords may still fall back to triad/add/6 color sources because no rootless
    # A/B source exists for plain triads.
    rootless = [
        candidate for candidate in candidates
        if candidate.is_legal and _is_rootless_upper_4note_color(candidate.upper_source)
    ]
    return rootless or candidates


def _is_upper_3note_shell_plus_one(option: SpreadUpperSourceOption) -> bool:
    family = str(option.source_family)
    # SPREAD upper 3-note blocks should not carry a duplicated root/1 in this
    # 2+3 pilot, regardless of whether it came from shell+1 or a triad source.
    if any(str(degree) in {"R", "1"} for degree in option.degree_names):
        return True
    if family not in {"shell_plus_5", "shell_plus_color"}:
        return False
    root_markers = {
        "shell_plus_1or5_component_root_low_weight",
        "shell_expansion_component_root",
        "three_note_source_component_root_low_weight",
    }
    return any(note in root_markers for note in option.source_metadata)


def _place_upper_source_for_spread(
    root_pc: int,
    upper_option: SpreadUpperSourceOption,
    register_policy: SpreadProjectionRegisterPolicy,
    runtime_policy: Any | None,
) -> tuple[tuple[list[PlacedDegree], str, dict[str, object]], ...]:
    degrees = [(str(degree), int(semitone)) for degree, semitone in upper_option.degrees]
    if not degrees:
        return ()
    if upper_option.kind == SpreadUpperSourceKind.DROP_FAMILY_DERIVED_PROJECTION_BLOCK and len(degrees) == 4:
        projection_policy = _spread_drop_projection_policy(register_policy, runtime_policy)
        parent_candidates = compact_closed_parent_candidates_for_projection(root_pc, degrees, projection_policy)
        if not parent_candidates:
            return ()
        parent_candidate_spans = [
            max(note for _, note in parent) - min(note for _, note in parent)
            for parent in parent_candidates
            if parent
        ]
        results: list[tuple[list[PlacedDegree], str, dict[str, object]]] = []
        emit_all_parent_projections = bool(
            _spread_policy_metadata(runtime_policy).get("spread_upper_4note_emit_all_parent_projections", False)
        )
        for method_name in upper_option.projection_methods or (OpenProjectionMethod.DROP2.value, OpenProjectionMethod.DROP3.value):
            method = _coerce_drop_family_method(method_name)
            if method is None:
                continue
            selections = []
            if emit_all_parent_projections:
                for parent_index, parent in enumerate(parent_candidates):
                    selection = place_named_open_projection_from_closed_parents(
                        [parent],
                        projection_policy,
                        method,
                    )
                    if selection.placed:
                        selections.append((parent_index, selection))
            else:
                selection = place_named_open_projection_from_closed_parents(
                    parent_candidates,
                    projection_policy,
                    method,
                )
                if selection.placed:
                    selections.append((selection.parent_index, selection))
            allow_octave_shift_candidates = bool(
                _spread_policy_metadata(runtime_policy).get("spread_upper_4note_allow_octave_shift_candidates", False)
            )
            for parent_index, selection in selections:
                placed = selection.placed
                if not placed:
                    continue
                shift_values = (0, 12, 24) if allow_octave_shift_candidates else (0,)
                for octave_shift in shift_values:
                    shifted_placed = [(str(degree), int(note) + int(octave_shift)) for degree, note in placed]
                    shifted_notes = [int(note) for _, note in shifted_placed]
                    if any(note < int(register_policy.upper_low) or note > int(register_policy.upper_high) for note in shifted_notes):
                        continue
                    metadata = named_open_projection_metadata(
                        shifted_placed,
                        method,
                        [(str(degree), int(note) + int(octave_shift)) for degree, note in selection.parent_closed],
                        parent_index=parent_index,
                        parent_candidate_count=len(parent_candidates),
                        projected_candidate_count=selection.projected_candidate_count,
                        legal_candidate_count=selection.legal_candidate_count,
                        policy=projection_policy,
                    )
                    metadata.update(
                        {
                            "spread_1plus4_upper_compact_closed_parent_alignment_version": SPREAD_1PLUS4_UPPER_COMPACT_CLOSED_PARENT_ALIGNMENT_VERSION,
                            "spread_upper_4note_drop2_drop3_only_version": SPREAD_UPPER_4NOTE_DROP2_DROP3_ONLY_VERSION,
                            "spread_upper_4note_allowed_projection_methods": [OpenProjectionMethod.DROP2.value, OpenProjectionMethod.DROP3.value],
                            "spread_upper_4note_drop2_and_4_allowed": False,
                            "spread_upper_4note_emit_all_parent_projections": bool(emit_all_parent_projections),
                            "spread_upper_4note_allow_octave_shift_candidates": bool(allow_octave_shift_candidates),
                            "spread_upper_4note_octave_shift": int(octave_shift),
                            "spread_upper_projection_uses_drop_family_resource": True,
                            "spread_upper_projection_resource_owner": "core.voicing.disposition.open",
                            "spread_upper_parent_construction_owner": "core.voicing.disposition.closed.compact_closed_parent_candidates_for_projection",
                            "spread_upper_uses_compact_closed_parent_candidates": True,
                            "spread_upper_compact_parent_candidate_count": len(parent_candidates),
                            "spread_upper_compact_parent_candidate_spans": parent_candidate_spans,
                            "spread_upper_compact_parent_max_span": max(parent_candidate_spans) if parent_candidate_spans else 0,
                            "spread_upper_projection_parent_closed": [[degree, int(note)] for degree, note in selection.parent_closed],
                            "spread_upper_oriented_stack_parent_reuse_allowed": False,
                            "final_placed_closed_open_result_reuse_allowed": False,
                        }
                    )
                    results.append(([(str(degree), int(note)) for degree, note in shifted_placed], method.value, metadata))
        return tuple(results)

    placed_options = _place_closed_upper_stack_candidates(root_pc, degrees, register_policy)
    if not placed_options:
        return ()
    results: list[tuple[list[PlacedDegree], str, dict[str, object]]] = []
    for placed in placed_options:
        notes = [int(note) for _, note in placed]
        results.append((placed, "closed_upper_stack", {
            "spread_upper_projection_uses_drop_family_resource": False,
            "spread_upper_projection_resource_owner": "core.voicing.disposition.spread",
            "spread_upper_3note_closed_stack_version": BALLAD_SPREAD_2PLUS3_CLOSED_UPPER_GROUPWISE_VL_VERSION,
            "spread_upper_3note_min_note_floor": int(register_policy.upper_low),
            "spread_upper_3note_closed_span": (max(notes) - min(notes)) if notes else 0,
            "source_oriented_not_placed": False,
            "final_placed_closed_open_result_reuse_allowed": False,
        }))
    return tuple(results)


def _place_closed_upper_stack_candidates(
    root_pc: int,
    degrees: list[Degree],
    register_policy: SpreadProjectionRegisterPolicy,
) -> tuple[list[PlacedDegree], ...]:
    """Place upper source material as compact closed stacks.

    Upper 3-note SPREAD blocks reuse source *content* but not source order as a
    physical layout.  This prevents shapes like 3-7-5 from being stretched into
    a pseudo-open voicing.  Multiple closed inversions are returned so the final
    selector can choose the nearest lower/upper-group continuation.
    """

    if not degrees:
        return ()
    normalized_source = [(str(degree), int(semitone)) for degree, semitone in degrees]
    ordered = sorted(enumerate(normalized_source), key=lambda item: (item[1][1] % 12, item[0]))
    ordered_degrees = [(degree, semitone % 12) for _, (degree, semitone) in ordered]
    rotations: list[list[tuple[str, int]]] = []
    for start in range(len(ordered_degrees)):
        rotated = ordered_degrees[start:] + ordered_degrees[:start]
        offsets: list[tuple[str, int]] = []
        previous: int | None = None
        for degree, pc_offset in rotated:
            value = int(pc_offset)
            if previous is not None:
                while value <= previous:
                    value += 12
            offsets.append((degree, value))
            previous = value
        if offsets and (offsets[-1][1] - offsets[0][1]) <= 12:
            rotations.append(offsets)

    candidates: list[tuple[int, list[PlacedDegree]]] = []
    seen: set[tuple[int, ...]] = set()
    for offsets in rotations:
        for octave in range(0, 11):
            root_note = int(root_pc) % 12 + 12 * octave
            placed = [(degree, root_note + int(offset)) for degree, offset in offsets]
            placed = sorted(dedupe_by_note(placed), key=lambda item: item[1])
            notes = [int(note) for _, note in placed]
            if len(notes) != len(degrees):
                continue
            if tuple(notes) in seen:
                continue
            if any(note < int(register_policy.upper_low) or note > int(register_policy.upper_high) for note in notes):
                continue
            span = max(notes) - min(notes)
            if span > 12:
                continue
            score = abs(min(notes) - int(register_policy.upper_target_low)) * 10 + span
            seen.add(tuple(notes))
            candidates.append((score, placed))
    candidates.sort(key=lambda item: (item[0], item[1]))
    return tuple(placed for _, placed in candidates)


def _normalize_oriented_offsets(semitones: list[int]) -> list[int]:
    out: list[int] = []
    previous: int | None = None
    for semitone in semitones:
        value = int(semitone)
        if previous is not None:
            while value <= previous:
                value += 12
        out.append(value)
        previous = value
    return out


def _coerce_drop_family_method(method_name: object) -> OpenProjectionMethod | None:
    text = str(getattr(method_name, "value", method_name)).strip().lower().replace("-", "_")
    if text in {"drop2", "drop_2"}:
        return OpenProjectionMethod.DROP2
    if text in {"drop3", "drop_3"}:
        return OpenProjectionMethod.DROP3
    return None


def _spread_drop_projection_policy(register_policy: SpreadProjectionRegisterPolicy, runtime_policy: Any | None) -> Any:
    from dataclasses import replace

    from jammate_engine.core.voicing.policy import VoicingPolicy

    base = runtime_policy if isinstance(runtime_policy, VoicingPolicy) else VoicingPolicy()
    metadata = {
        **dict(getattr(base, "metadata", None) or {}),
        "drop_family_register_low": int(register_policy.upper_low),
        "drop_family_max_span": max(24, int(register_policy.max_overall_span)),
        "strict_closed_compact_pitch_class_layout": True,
        "strict_closed_max_span": 12,
        "spread_upper_drop_projection_resource_adapter": True,
        "spread_1plus4_upper_compact_closed_parent_alignment_version": SPREAD_1PLUS4_UPPER_COMPACT_CLOSED_PARENT_ALIGNMENT_VERSION,
        "spread_upper_uses_compact_closed_parent_candidates": True,
        "final_placed_closed_open_result_reuse_allowed": False,
    }
    return replace(
        base,
        register_low=int(register_policy.upper_low),
        register_high=int(register_policy.upper_high),
        comfort_register_low=int(register_policy.upper_low),
        comfort_register_high=int(register_policy.upper_high),
        top_voice_low=int(register_policy.upper_low),
        top_voice_high=int(register_policy.upper_high),
        max_voicing_span=max(24, int(register_policy.max_overall_span)),
        metadata=metadata,
    )


def _spread_candidate_preserves_seventh_chord_identity(chord_symbol: str, degree_names: tuple[str, ...]) -> bool:
    from jammate_engine.core.voicing.sources.content_planner import source_preserves_seventh_chord_identity

    return bool(source_preserves_seventh_chord_identity(chord_symbol, degree_names))


def _spread_candidate_source_integrity_notes(chord_symbol: str, degree_names: tuple[str, ...]) -> tuple[str, ...]:
    from jammate_engine.core.voicing.sources.content_planner import seventh_chord_source_integrity_notes

    return tuple(seventh_chord_source_integrity_notes(chord_symbol, degree_names))


def _dedupe_spread_projection_candidates(candidates: list[SpreadProjectionCandidate]) -> list[SpreadProjectionCandidate]:
    out: list[SpreadProjectionCandidate] = []
    seen: set[tuple[str, tuple[int, ...], str, str]] = set()
    for candidate in candidates:
        key = (
            candidate.recipe_contract.recipe_id,
            candidate.notes,
            candidate.lower.instance.recipe.recipe_id.value,
            candidate.upper_projection_method,
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(candidate)
    out.sort(
        key=lambda candidate: (
            not candidate.is_legal,
            candidate.group_gap_semitones if candidate.group_gap_semitones is not None else 999,
            candidate.overall_span_semitones,
            candidate.notes,
        )
    )
    return out


def spread_recipe_reuse_audit() -> tuple[SpreadReuseAuditItem, ...]:
    """Return the v2_2_38 reuse audit for SPREAD recipe planning."""

    return (
        SpreadReuseAuditItem(
            resource_id="three_note_content_source_inventory",
            owner_path="core.voicing.content_planner + core.voicing.chord_tone_resolver",
            reusable_level="source/orientation/color_policy",
            status=SpreadReuseStatus.ADAPTER_REQUIRED,
            reason="Upper 3-note SPREAD blocks should adapt existing triad, shell, shell+color, guide+color source logic instead of inventing a parallel source list.",
        ),
        SpreadReuseAuditItem(
            resource_id="four_note_source_orientation_inventory",
            owner_path="core.voicing.content_planner + core.voicing.four_note_sources",
            reusable_level="source/orientation/canonical_rotation_metadata",
            status=SpreadReuseStatus.ADAPTER_REQUIRED,
            reason="Upper 4-note SPREAD blocks should reuse canonical source rotations and color gates, including seventh/basic, rooted color, triad-aware, and rootless A/B resources.",
        ),
        SpreadReuseAuditItem(
            resource_id="drop_family_projection_resource",
            owner_path="core.voicing.disposition.open.place_named_open_projection_from_closed_parents",
            reusable_level="projection_resource_only",
            status=SpreadReuseStatus.ADAPTER_REQUIRED,
            reason="SPREAD 1+4 / 2+4 / 3+4 may derive an upper block from DROP2/DROP3 resources, but SPREAD still owns lower register, upper register, gap, span, and group-wise continuity.",
        ),
        SpreadReuseAuditItem(
            resource_id="color_permission_policy",
            owner_path="core.voicing.color_permission",
            reusable_level="permission_gate",
            status=SpreadReuseStatus.REUSE_READY,
            reason="SPREAD must obey the same chord-symbol-only vs harmonic-expansion color policy as 3-note and 4-note voicings.",
        ),
        SpreadReuseAuditItem(
            resource_id="final_closed_or_open_voicing_candidate",
            owner_path="core.voicing.candidate_generator.VoicingCandidate",
            reusable_level="final_placed_result",
            status=SpreadReuseStatus.NOT_REUSABLE,
            reason="A completed closed/open voicing already owns a register placement; SPREAD must not reuse it as a final placement.",
            final_placed_result_reuse_allowed=False,
        ),
    )


def spread_recipe_contract_skeleton(*, include_retired_four_note: bool = False) -> tuple[SpreadRecipeContract, ...]:
    """Return the active SPREAD grouping/source contract skeleton.

    v2_6_10 retires the old 4-note 1+3 / 2+2 SPREAD contracts from the
    default skeleton.  Explicit legacy audits may request them with
    ``include_retired_four_note=True``, but ordinary runtime SPREAD now starts
    at 5-note grouped contracts.
    """

    lower_1 = LowerGroupRecipeContract(
        ref_id="lower_1note_root_only",
        note_count=1,
        degree_role_contract=("root",),
    )
    lower_2 = LowerGroupRecipeContract(
        ref_id="lower_2note_inventory_root7_root3_root5_3and7",
        note_count=2,
        degree_role_contract=("root+7", "root+3", "root+5", "3+7"),
    )
    lower_3 = LowerGroupRecipeContract(
        ref_id="lower_3note_inventory_root5upperroot_root37_root7upper3_root5upper3",
        note_count=3,
        degree_role_contract=("root+5+upper_root", "root+3+7", "root+7+upper3", "root+5+upper3"),
    )
    upper_2 = UpperSourceRef(
        ref_id="upper_2note_existing_guide_shell_source_ref",
        note_count=2,
        kind=SpreadUpperSourceKind.TWO_NOTE_CONTENT_SOURCE,
        reusable_owner_paths=("core.voicing.content_planner", "core.voicing.chord_tone_resolver", "core.voicing.color_permission"),
    )
    upper_3 = UpperSourceRef(
        ref_id="upper_3note_existing_content_source_ref",
        note_count=3,
        kind=SpreadUpperSourceKind.THREE_NOTE_CONTENT_SOURCE,
        reusable_owner_paths=("core.voicing.content_planner", "core.voicing.chord_tone_resolver", "core.voicing.color_permission"),
    )
    upper_4 = UpperSourceRef(
        ref_id="upper_4note_drop2_drop3_derived_source_ref",
        note_count=4,
        kind=SpreadUpperSourceKind.DROP_FAMILY_DERIVED_PROJECTION_BLOCK,
        reusable_owner_paths=("core.voicing.content_planner", "core.voicing.four_note_sources", "core.voicing.disposition.open"),
        projection_methods=("DROP2", "DROP3"),
    )
    active = (
        SpreadRecipeContract("spread_1plus4_contract", SpreadGrouping.ONE_PLUS_FOUR, 5, lower_1, upper_4),
        SpreadRecipeContract("spread_2plus3_contract", SpreadGrouping.TWO_PLUS_THREE, 5, lower_2, upper_3),
        SpreadRecipeContract("spread_2plus4_contract", SpreadGrouping.TWO_PLUS_FOUR, 6, lower_2, upper_4),
        SpreadRecipeContract("spread_3plus3_contract", SpreadGrouping.THREE_PLUS_THREE, 6, lower_3, upper_3),
        SpreadRecipeContract("spread_3plus4_contract", SpreadGrouping.THREE_PLUS_FOUR, 7, lower_3, upper_4),
    )
    if not include_retired_four_note:
        return active
    retired = (
        SpreadRecipeContract("spread_1plus3_contract", SpreadGrouping.ONE_PLUS_THREE, 4, lower_1, upper_3),
        SpreadRecipeContract("spread_2plus2_contract", SpreadGrouping.TWO_PLUS_TWO, 4, lower_2, upper_2),
    )
    return (*retired, *active)


def spread_recipe_contract_debug() -> dict[str, object]:
    """Return a compact debug payload for docs, audits, and regression tests."""

    return {
        "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
        "layer": "core.voicing.disposition.spread",
        "purpose": "SPREAD notes/projection foundation contract skeleton",
        "runtime_enabled": False,
        "notes_only": True,
        "no_expression_or_pedal": True,
        "reuse_audit": [item.to_debug_dict() for item in spread_recipe_reuse_audit()],
        "lower_group_inventory": [recipe.to_debug_dict() for recipe in lower_group_recipe_inventory()],
        "upper_source_adapter_version": UPPER_SOURCE_ADAPTER_VERSION,
        "upper_source_refs": [ref.to_debug_dict() for ref in spread_upper_source_refs()],
        "active_contract_ids": list(SPREAD_ACTIVE_CONTRACT_IDS),
        "retired_four_note_contract_ids": list(SPREAD_RETIRED_FOUR_NOTE_CONTRACT_IDS),
        "four_note_spread_groupings_retired": True,
        "recipe_contracts": [contract.to_debug_dict() for contract in spread_recipe_contract_skeleton()],
    }


def place_lower_upper_grouped_projection(
    root_pc: int,
    degrees: list[Degree],
    low: int,
    high: int,
    policy: Any,
) -> list[PlacedDegree]:
    """Project a source as an abstract lower/upper grouped spread."""

    if len(degrees) <= 2:
        return place_stack(root_pc, degrees, low, high, target_low=max(int(low), 48), spread_upper_voices=True)
    low_part = degrees[:1]
    high_part = degrees[1:]
    placed = place_stack(
        root_pc,
        low_part,
        max(int(low), int(getattr(policy, "left_hand_low"))),
        min(int(high), int(getattr(policy, "left_hand_high"))),
        target_low=max(int(low), int(getattr(policy, "left_hand_low"))),
        spread_upper_voices=False,
    )
    placed.extend(
        place_stack(
            root_pc,
            high_part,
            max(int(low), int(getattr(policy, "right_hand_low"))),
            min(int(high), int(getattr(policy, "right_hand_high"))),
            target_low=max(int(low), int(getattr(policy, "right_hand_low"))),
            spread_upper_voices=False,
        )
    )
    return sorted(dedupe_by_note(placed), key=lambda item: item[1])


def place_foundation_projection(
    root_pc: int,
    degrees: list[Degree],
    policy: Any,
) -> list[PlacedDegree]:
    """Project root/foundation support below an upper chord/color group."""

    root = degree_to_note(root_pc, 0, int(getattr(policy, "left_hand_low")), int(getattr(policy, "left_hand_high")))
    while root > 48:
        root -= 12
    right_degrees = [degree for degree in degrees if str(degree[0]) != "R"] or degrees
    right = place_stack(
        root_pc,
        right_degrees,
        int(getattr(policy, "right_hand_low")),
        int(getattr(policy, "right_hand_high")),
        target_low=int(getattr(policy, "right_hand_low")),
        spread_upper_voices=False,
    )
    return sorted(dedupe_by_note([("R", root), *right]), key=lambda item: item[1])


def place_root_10th_projection(
    root_pc: int,
    degrees: list[Degree],
    policy: Any,
) -> list[PlacedDegree]:
    """Project root + upper material using the legacy root-10th register band."""

    root = degree_to_note(root_pc, 0, int(getattr(policy, "left_hand_low")), int(getattr(policy, "left_hand_high")))
    while root > 45:
        root -= 12
    others = [degree for degree in degrees if str(degree[0]) != "R"]
    right = place_stack(
        root_pc,
        others,
        int(getattr(policy, "right_hand_low")),
        int(getattr(policy, "right_hand_high")),
        target_low=int(getattr(policy, "right_hand_low")),
        spread_upper_voices=False,
    )
    return sorted(dedupe_by_note([("R", root), *right]), key=lambda item: item[1])
