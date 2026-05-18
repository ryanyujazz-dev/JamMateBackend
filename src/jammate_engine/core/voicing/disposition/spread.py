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
    SPREAD_RECIPE_CONTRACT_VERSION,
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


GROUPWISE_SPREAD_VOICE_LEADING_VERSION = "v2_2_41"
SPREAD_SELECTOR_RUNTIME_GATE_VERSION = "v2_2_42"
BALLAD_SPREAD_RUNTIME_ENTRY_CONTRACT_VERSION = "v2_2_43"
BALLAD_SPREAD_RUNTIME_SAFE_DRY_RUN_VERSION = "v2_2_44"
SPREAD_RUNTIME_CONVERSION_BOUNDARY_AUDIT_VERSION = "v2_2_45"
FUNCTIONAL_GROUPING_1PLUS4_CONTRACT_ALIGNMENT_VERSION = "v2_2_46"
SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION = "v2_2_47"
BALLAD_SPREAD_RUNTIME_CANDIDATE_POOL_INTEGRATION_VERSION = "v2_2_48"
BALLAD_SPREAD_PILOT_SELECTION_WEIGHT_FALLBACK_AUDIT_VERSION = "v2_2_49"
BALLAD_SPREAD_PILOT_RUNTIME_ENABLEMENT_GUARD_VERSION = "v2_2_50"
BALLAD_SPREAD_1PLUS4_TRUE_ISOLATION_FIX_VERSION = "v2_2_52"
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
class SpreadGroupwiseVoiceLeadingWeights:
    """Weights for notes-only SPREAD group-wise continuity scoring.

    Lower and upper groups are scored separately so SPREAD does not collapse
    back into a single all-notes total-motion heuristic.  Smaller penalties are
    better.  The scorer is a debug/ranking helper only in v2_2_41 and does not
    enable SPREAD in runtime selection.
    """

    lower_group_motion: float = 1.25
    upper_group_motion: float = 1.0
    top_voice_motion: float = 0.9
    group_gap_stability: float = 0.55
    span_penalty: float = 0.35
    register_penalty: float = 0.4
    legality_penalty: float = 10000.0
    runtime_enabled: bool = False

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "groupwise_spread_voice_leading_version": GROUPWISE_SPREAD_VOICE_LEADING_VERSION,
            "lower_group_motion": float(self.lower_group_motion),
            "upper_group_motion": float(self.upper_group_motion),
            "top_voice_motion": float(self.top_voice_motion),
            "group_gap_stability": float(self.group_gap_stability),
            "span_penalty": float(self.span_penalty),
            "register_penalty": float(self.register_penalty),
            "legality_penalty": float(self.legality_penalty),
            "runtime_enabled": self.runtime_enabled,
            "notes_only": True,
            "no_expression_or_pedal": True,
        }


@dataclass(frozen=True)
class SpreadGroupwiseVoiceLeadingScore:
    """A component score for one current SPREAD candidate.

    The score preserves separate lower/upper/top/gap/span/register components so
    future selectors can inspect why a candidate ranked well.  It intentionally
    references ``SpreadProjectionCandidate`` rather than converting to a runtime
    voicing candidate.
    """

    current: SpreadProjectionCandidate
    previous: SpreadProjectionCandidate | None
    lower_group_motion: int
    upper_group_motion: int
    top_voice_motion: int
    group_gap_change: int
    span_penalty: int
    register_penalty: int
    legality_penalty: float
    weighted_penalty: float
    weights: SpreadGroupwiseVoiceLeadingWeights
    runtime_enabled: bool = False

    @property
    def total_motion(self) -> int:
        return int(self.lower_group_motion + self.upper_group_motion)

    @property
    def continuity_score(self) -> float:
        return max(0.0, 1000.0 - float(self.weighted_penalty))

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
            "basic_spread_projection_version": BASIC_SPREAD_PROJECTION_VERSION,
            "groupwise_spread_voice_leading_version": GROUPWISE_SPREAD_VOICE_LEADING_VERSION,
            "layer": "core.voicing.disposition.spread",
            "current_chord_symbol": self.current.chord_symbol,
            "previous_chord_symbol": self.previous.chord_symbol if self.previous is not None else None,
            "current_recipe_id": self.current.recipe_contract.recipe_id,
            "previous_recipe_id": self.previous.recipe_contract.recipe_id if self.previous is not None else None,
            "current_grouping": self.current.recipe_contract.grouping.value,
            "previous_grouping": self.previous.recipe_contract.grouping.value if self.previous is not None else None,
            "current_lower_group_notes": list(self.current.lower_notes),
            "previous_lower_group_notes": list(self.previous.lower_notes) if self.previous is not None else [],
            "current_upper_group_notes": list(self.current.upper_notes),
            "previous_upper_group_notes": list(self.previous.upper_notes) if self.previous is not None else [],
            "current_top_voice": max(self.current.notes) if self.current.notes else None,
            "previous_top_voice": max(self.previous.notes) if self.previous is not None and self.previous.notes else None,
            "lower_group_motion": int(self.lower_group_motion),
            "upper_group_motion": int(self.upper_group_motion),
            "top_voice_motion": int(self.top_voice_motion),
            "group_gap_change": int(self.group_gap_change),
            "span_penalty": int(self.span_penalty),
            "register_penalty": int(self.register_penalty),
            "legality_penalty": float(self.legality_penalty),
            "total_motion": self.total_motion,
            "weighted_penalty": float(self.weighted_penalty),
            "continuity_score": float(self.continuity_score),
            "weights": self.weights.to_debug_dict(),
            "scored_groupwise_not_total_motion_only": True,
            "runtime_enabled": self.runtime_enabled,
            "notes_only": True,
            "no_expression_or_pedal": True,
        }



@dataclass(frozen=True)
class SpreadRuntimeGateDecision:
    """Safety gate for future SPREAD runtime use.

    The gate may be opened only by explicit policy metadata plus a SPREAD
    texture-family request.  Even when open, v2_2_42 does not wire SPREAD into
    style runtime candidate generation and does not convert a selected
    ``SpreadProjectionCandidate`` into a runtime ``VoicingCandidate``.
    """

    selector_gate_open: bool
    reason: str
    explicit_request: bool
    spread_family_requested: bool
    primary_family: str | None = None
    allowed_families: tuple[str, ...] = ()
    source: str = "policy_metadata"
    style_runtime_wiring_enabled: bool = False
    candidate_conversion_allowed: bool = False
    notes_only: bool = True
    runtime_enabled: bool = False

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "spread_selector_runtime_gate_version": SPREAD_SELECTOR_RUNTIME_GATE_VERSION,
            "selector_gate_open": bool(self.selector_gate_open),
            "reason": self.reason,
            "explicit_request": bool(self.explicit_request),
            "spread_family_requested": bool(self.spread_family_requested),
            "primary_family": self.primary_family,
            "allowed_families": list(self.allowed_families),
            "source": self.source,
            "style_runtime_wiring_enabled": bool(self.style_runtime_wiring_enabled),
            "candidate_conversion_allowed": bool(self.candidate_conversion_allowed),
            "runtime_enabled": bool(self.runtime_enabled),
            "notes_only": bool(self.notes_only),
            "no_expression_or_pedal": True,
            "does_not_change_default_style_runtime": True,
        }


@dataclass(frozen=True)
class SpreadCandidateSelectorRequest:
    """Selector request contract for notes-only SPREAD candidates.

    This is intentionally smaller than a style runtime request.  It declares
    which SPREAD contracts may be projected and ranked while leaving expression,
    pedal, duration, and final instrument realization outside this layer.
    """

    chord_symbol: str
    contract_ids: tuple[str, ...] = ()
    max_upper_options: int = 12
    legal_only: bool = True
    source: str = "explicit_policy_gate"
    runtime_enabled: bool = False

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "spread_selector_runtime_gate_version": SPREAD_SELECTOR_RUNTIME_GATE_VERSION,
            "chord_symbol": self.chord_symbol,
            "contract_ids": list(self.contract_ids),
            "max_upper_options": int(self.max_upper_options),
            "legal_only": bool(self.legal_only),
            "source": self.source,
            "runtime_enabled": bool(self.runtime_enabled),
            "notes_only": True,
            "no_expression_or_pedal": True,
        }


@dataclass(frozen=True)
class SpreadCandidateSelectorResult:
    """Result of the SPREAD selector contract / runtime gate skeleton.

    The selected object remains a notes-only ``SpreadProjectionCandidate``.
    Runtime conversion and style wiring are explicitly forbidden in v2_2_42.
    """

    request: SpreadCandidateSelectorRequest
    gate: SpreadRuntimeGateDecision
    projected_results: tuple[SpreadProjectionResult, ...]
    ranked_scores: tuple[SpreadGroupwiseVoiceLeadingScore, ...]
    selected: SpreadProjectionCandidate | None
    selected_score: SpreadGroupwiseVoiceLeadingScore | None
    runtime_enabled: bool = False

    @property
    def projected_result_count(self) -> int:
        return len(self.projected_results)

    @property
    def candidate_count(self) -> int:
        return sum(len(result.candidates) for result in self.projected_results)

    @property
    def legal_candidate_count(self) -> int:
        return sum(result.legal_candidate_count for result in self.projected_results)

    @property
    def ranked_score_count(self) -> int:
        return len(self.ranked_scores)

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
            "basic_spread_projection_version": BASIC_SPREAD_PROJECTION_VERSION,
            "groupwise_spread_voice_leading_version": GROUPWISE_SPREAD_VOICE_LEADING_VERSION,
            "spread_selector_runtime_gate_version": SPREAD_SELECTOR_RUNTIME_GATE_VERSION,
            "layer": "core.voicing.disposition.spread",
            "purpose": "SPREAD Candidate Selector Contract / Runtime Gate Skeleton",
            "request": self.request.to_debug_dict(),
            "gate": self.gate.to_debug_dict(),
            "projected_result_count": self.projected_result_count,
            "candidate_count": self.candidate_count,
            "legal_candidate_count": self.legal_candidate_count,
            "ranked_score_count": self.ranked_score_count,
            "selected_candidate": self.selected.to_debug_dict() if self.selected is not None else None,
            "selected_score": self.selected_score.to_debug_dict() if self.selected_score is not None else None,
            "selected_candidate_runtime_enabled": bool(self.selected.runtime_enabled) if self.selected is not None else False,
            "candidate_conversion_allowed": False,
            "style_runtime_wiring_enabled": False,
            "runtime_enabled": bool(self.runtime_enabled),
            "notes_only": True,
            "no_expression_or_pedal": True,
            "does_not_change_default_style_runtime": True,
        }


class BalladSpreadEntryScene(str, Enum):
    """Scene tags where a future Ballad SPREAD pilot may be explicitly requested.

    These are planning/entry-contract tags only.  They do not retune Ballad,
    change expression, or wire SPREAD candidates into runtime selection.
    """

    EXPLICIT_TEXTURE_REQUEST = "explicit_texture_request"
    WARM_SPREAD_PHRASE = "warm_spread_phrase"
    FINAL_CADENCE_LIFT = "final_cadence_lift"
    NO_BASS_FOUNDATION = "no_bass_foundation"
    SOLO_PIANO_SECTION = "solo_piano_section"
    THICK_ENDING_PREP = "thick_ending_prep"


BALLAD_SPREAD_DEPRECATED_CONTRACT_IDS: tuple[str, ...] = (
    "spread_1plus3_contract",
)


BALLAD_SPREAD_ENTRY_ALLOWED_CONTRACT_IDS: tuple[str, ...] = (
    "spread_1plus4_contract",
    "spread_2plus3_contract",
    "spread_2plus4_contract",
    "spread_3plus3_contract",
    "spread_3plus4_contract",
)

BALLAD_SPREAD_ENTRY_PREFERRED_CONTRACT_IDS: tuple[str, ...] = (
    "spread_1plus4_contract",
    "spread_2plus3_contract",
)


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
        "spread_1plus4_contract": 18,
        "spread_2plus3_contract": 56,
        "spread_2plus4_contract": 22,
        "spread_3plus3_contract": 4,
        "spread_3plus4_contract": 0,
    },
    BalladSpreadGroupingMixScene.CHORUS_LIFT.value: {
        "spread_1plus4_contract": 10,
        "spread_2plus3_contract": 38,
        "spread_2plus4_contract": 36,
        "spread_3plus3_contract": 14,
        "spread_3plus4_contract": 2,
    },
    BalladSpreadGroupingMixScene.ENDING_CLIMAX.value: {
        "spread_1plus4_contract": 5,
        "spread_2plus3_contract": 12,
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
    return {
        "texture_state_id": scope_key,
        "texture_family": family,
        "primary_contract_id": primary,
        "compatible_contract_ids": tuple(compatible),
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
    allowed = set(BALLAD_SPREAD_ENTRY_ALLOWED_CONTRACT_IDS)
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


@dataclass(frozen=True)
class BalladSpreadRuntimeEntryContract:
    """Safe entry contract for a future Jazz Ballad SPREAD runtime pilot.

    This contract declares where Ballad may ask for SPREAD later.  It remains a
    planning/debug surface: it does not convert notes-only SPREAD candidates into
    runtime voicings and it does not enable SPREAD for any default style path.
    """

    style_name: str = "jazz_ballad"
    pilot_enabled: bool = False
    scene: BalladSpreadEntryScene = BalladSpreadEntryScene.EXPLICIT_TEXTURE_REQUEST
    allowed_style_names: tuple[str, ...] = ("jazz_ballad",)
    blocked_style_names: tuple[str, ...] = ("medium_swing", "bossa_nova")
    allowed_scenes: tuple[BalladSpreadEntryScene, ...] = (
        BalladSpreadEntryScene.EXPLICIT_TEXTURE_REQUEST,
        BalladSpreadEntryScene.WARM_SPREAD_PHRASE,
        BalladSpreadEntryScene.FINAL_CADENCE_LIFT,
        BalladSpreadEntryScene.NO_BASS_FOUNDATION,
        BalladSpreadEntryScene.SOLO_PIANO_SECTION,
        BalladSpreadEntryScene.THICK_ENDING_PREP,
    )
    allowed_contract_ids: tuple[str, ...] = BALLAD_SPREAD_ENTRY_ALLOWED_CONTRACT_IDS
    preferred_contract_ids: tuple[str, ...] = BALLAD_SPREAD_ENTRY_PREFERRED_CONTRACT_IDS
    allowed_groupings: tuple[str, ...] = ("1+4", "2+3", "2+4", "3+3", "3+4")
    density_range: tuple[int, int] = (4, 6)
    fallback_path: str = "existing_non_spread_voicing_selector_or_open_fallback"
    source: str = "policy_metadata_or_default_contract"
    style_runtime_wiring_enabled: bool = False
    candidate_conversion_allowed: bool = False
    runtime_enabled: bool = False
    notes_only: bool = True

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "ballad_spread_runtime_entry_contract_version": BALLAD_SPREAD_RUNTIME_ENTRY_CONTRACT_VERSION,
            "style_name": self.style_name,
            "pilot_enabled": bool(self.pilot_enabled),
            "scene": self.scene.value,
            "allowed_style_names": list(self.allowed_style_names),
            "blocked_style_names": list(self.blocked_style_names),
            "allowed_scenes": [scene.value for scene in self.allowed_scenes],
            "allowed_contract_ids": list(self.allowed_contract_ids),
            "preferred_contract_ids": list(self.preferred_contract_ids),
            "allowed_groupings": list(self.allowed_groupings),
            "density_range": list(self.density_range),
            "fallback_path": self.fallback_path,
            "source": self.source,
            "style_runtime_wiring_enabled": bool(self.style_runtime_wiring_enabled),
            "candidate_conversion_allowed": bool(self.candidate_conversion_allowed),
            "runtime_enabled": bool(self.runtime_enabled),
            "notes_only": bool(self.notes_only),
            "no_expression_or_pedal": True,
            "does_not_change_medium_swing_or_bossa": True,
        }


@dataclass(frozen=True)
class BalladSpreadRuntimeEntryDecision:
    """Decision explaining whether a Ballad SPREAD pilot entry is allowed."""

    contract: BalladSpreadRuntimeEntryContract
    gate: SpreadRuntimeGateDecision
    entry_allowed: bool
    reason: str
    runtime_enabled: bool = False

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "ballad_spread_runtime_entry_contract_version": BALLAD_SPREAD_RUNTIME_ENTRY_CONTRACT_VERSION,
            "contract": self.contract.to_debug_dict(),
            "gate": self.gate.to_debug_dict(),
            "entry_allowed": bool(self.entry_allowed),
            "reason": self.reason,
            "style_runtime_wiring_enabled": False,
            "candidate_conversion_allowed": False,
            "runtime_enabled": bool(self.runtime_enabled),
            "notes_only": True,
            "no_expression_or_pedal": True,
            "planning_contract_only": True,
        }


@dataclass(frozen=True)
class BalladSpreadRuntimePilotResult:
    """Notes-only Ballad pilot selection result guarded by the entry contract."""

    chord_symbol: str
    decision: BalladSpreadRuntimeEntryDecision
    selector_result: SpreadCandidateSelectorResult | None
    selected: SpreadProjectionCandidate | None
    runtime_enabled: bool = False

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "ballad_spread_runtime_entry_contract_version": BALLAD_SPREAD_RUNTIME_ENTRY_CONTRACT_VERSION,
            "chord_symbol": self.chord_symbol,
            "decision": self.decision.to_debug_dict(),
            "selector_result": self.selector_result.to_debug_dict() if self.selector_result is not None else None,
            "selected_candidate": self.selected.to_debug_dict() if self.selected is not None else None,
            "selected_candidate_runtime_enabled": bool(self.selected.runtime_enabled) if self.selected is not None else False,
            "style_runtime_wiring_enabled": False,
            "candidate_conversion_allowed": False,
            "runtime_enabled": bool(self.runtime_enabled),
            "notes_only": True,
            "no_expression_or_pedal": True,
            "planning_contract_only": True,
        }

@dataclass(frozen=True)
class BalladSpreadRuntimePilotWiringPlan:
    """Safe dry-run wiring plan for a future Ballad SPREAD runtime pilot.

    The plan names the runtime boundary without crossing it.  It validates that
    Ballad can explicitly request a notes-only SPREAD candidate through the
    existing entry contract and selector gate, but keeps runtime conversion and
    style candidate-generator wiring disabled.
    """

    style_name: str = "jazz_ballad"
    dry_run_enabled: bool = False
    entry_contract_required: bool = True
    selector_gate_required: bool = True
    groupwise_ranking_required: bool = True
    output_candidate_type: str = "SpreadProjectionCandidate"
    future_conversion_target: str = "VoicingCandidate"
    fallback_path: str = "existing_non_spread_voicing_selector_or_open_fallback"
    source: str = "policy_metadata_or_explicit_argument"
    style_runtime_wiring_enabled: bool = False
    candidate_conversion_allowed: bool = False
    runtime_enabled: bool = False
    notes_only: bool = True

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "ballad_spread_runtime_safe_dry_run_version": BALLAD_SPREAD_RUNTIME_SAFE_DRY_RUN_VERSION,
            "style_name": self.style_name,
            "dry_run_enabled": bool(self.dry_run_enabled),
            "entry_contract_required": bool(self.entry_contract_required),
            "selector_gate_required": bool(self.selector_gate_required),
            "groupwise_ranking_required": bool(self.groupwise_ranking_required),
            "output_candidate_type": self.output_candidate_type,
            "future_conversion_target": self.future_conversion_target,
            "fallback_path": self.fallback_path,
            "source": self.source,
            "style_runtime_wiring_enabled": bool(self.style_runtime_wiring_enabled),
            "candidate_conversion_allowed": bool(self.candidate_conversion_allowed),
            "runtime_enabled": bool(self.runtime_enabled),
            "notes_only": bool(self.notes_only),
            "no_expression_or_pedal": True,
            "does_not_change_medium_swing_or_bossa": True,
            "safe_dry_run_only": True,
        }


@dataclass(frozen=True)
class BalladSpreadRuntimeDryRunChordTrace:
    """One chord-level trace through the safe Ballad SPREAD dry-run chain."""

    chord_symbol: str
    pilot_result: BalladSpreadRuntimePilotResult
    previous_candidate: SpreadProjectionCandidate | None = None
    conversion_boundary: str = "notes_only_candidate_not_converted_to_runtime_voicing"
    runtime_enabled: bool = False

    @property
    def selected(self) -> SpreadProjectionCandidate | None:
        return self.pilot_result.selected

    @property
    def selected_notes(self) -> tuple[int, ...]:
        return tuple(self.selected.notes) if self.selected is not None else ()

    @property
    def entry_allowed(self) -> bool:
        return bool(self.pilot_result.decision.entry_allowed)

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "ballad_spread_runtime_safe_dry_run_version": BALLAD_SPREAD_RUNTIME_SAFE_DRY_RUN_VERSION,
            "chord_symbol": self.chord_symbol,
            "entry_allowed": bool(self.entry_allowed),
            "decision_reason": self.pilot_result.decision.reason,
            "selected_candidate": self.selected.to_debug_dict() if self.selected is not None else None,
            "selected_notes": list(self.selected_notes),
            "previous_candidate_notes": list(self.previous_candidate.notes) if self.previous_candidate is not None else [],
            "selector_ranked_score_count": self.pilot_result.selector_result.ranked_score_count if self.pilot_result.selector_result is not None else 0,
            "conversion_boundary": self.conversion_boundary,
            "selected_candidate_runtime_enabled": bool(self.selected.runtime_enabled) if self.selected is not None else False,
            "style_runtime_wiring_enabled": False,
            "candidate_conversion_allowed": False,
            "runtime_enabled": bool(self.runtime_enabled),
            "notes_only": True,
            "no_expression_or_pedal": True,
            "safe_dry_run_only": True,
        }


@dataclass(frozen=True)
class BalladSpreadRuntimeSafeDryRunResult:
    """Safe dry-run result for Ballad SPREAD pilot wiring planning."""

    wiring_plan: BalladSpreadRuntimePilotWiringPlan
    chord_symbols: tuple[str, ...]
    traces: tuple[BalladSpreadRuntimeDryRunChordTrace, ...]
    blocked_reason: str = ""
    runtime_enabled: bool = False

    @property
    def selected_candidates(self) -> tuple[SpreadProjectionCandidate, ...]:
        return tuple(trace.selected for trace in self.traces if trace.selected is not None)

    @property
    def dry_run_completed(self) -> bool:
        return bool(
            self.wiring_plan.dry_run_enabled
            and not self.blocked_reason
            and self.traces
            and len(self.traces) == len(self.chord_symbols)
            and all(trace.selected is not None for trace in self.traces)
        )

    @property
    def selected_candidate_count(self) -> int:
        return len(self.selected_candidates)

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "ballad_spread_runtime_safe_dry_run_version": BALLAD_SPREAD_RUNTIME_SAFE_DRY_RUN_VERSION,
            "layer": "core.voicing.disposition.spread",
            "purpose": "Ballad SPREAD Runtime Pilot Wiring Plan + Safe Dry Run",
            "wiring_plan": self.wiring_plan.to_debug_dict(),
            "chord_symbols": list(self.chord_symbols),
            "trace_count": len(self.traces),
            "selected_candidate_count": self.selected_candidate_count,
            "dry_run_completed": bool(self.dry_run_completed),
            "blocked_reason": self.blocked_reason,
            "traces": [trace.to_debug_dict() for trace in self.traces],
            "candidate_conversion_allowed": False,
            "style_runtime_wiring_enabled": False,
            "runtime_enabled": bool(self.runtime_enabled),
            "notes_only": True,
            "no_expression_or_pedal": True,
            "safe_dry_run_only": True,
            "does_not_change_medium_swing_or_bossa": True,
        }




@dataclass(frozen=True)
class SpreadFunctionalGroupingContractAlignment:
    """Audit the SPREAD grouping string against core FunctionalGrouping.

    This is a contract-alignment surface only.  It proves that the core voicing
    taxonomy and projection-map helpers understand the same abstract grouping
    shape used by SPREAD notes/projection, without converting a notes-only
    ``SpreadProjectionCandidate`` into a runtime ``VoicingCandidate``.
    """

    spread_grouping: str
    runtime_grouping: str | None
    runtime_grouping_exists: bool
    group_roles: tuple[str, ...]
    projection_partition: tuple[tuple[int, ...], ...]
    projection_map_supported: bool
    conversion_allowed: bool = False
    candidate_generator_wiring_allowed: bool = False
    style_runtime_wiring_enabled: bool = False
    runtime_enabled: bool = False

    @property
    def functional_grouping_gap(self) -> str:
        if self.runtime_grouping_exists:
            return "runtime_functional_grouping_value_exists"
        return f"runtime_functional_grouping_missing:{self.spread_grouping}"

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "functional_grouping_1plus4_contract_alignment_version": FUNCTIONAL_GROUPING_1PLUS4_CONTRACT_ALIGNMENT_VERSION,
            "layer": "core.voicing.functional_grouping_contract",
            "purpose": "FunctionalGrouping 1+4 Contract Alignment",
            "spread_grouping": self.spread_grouping,
            "runtime_grouping": self.runtime_grouping,
            "runtime_grouping_exists": bool(self.runtime_grouping_exists),
            "functional_grouping_gap": self.functional_grouping_gap,
            "group_roles": list(self.group_roles),
            "projection_partition": [list(group) for group in self.projection_partition],
            "projection_map_supported": bool(self.projection_map_supported),
            "candidate_conversion_allowed": bool(self.conversion_allowed),
            "candidate_generator_wiring_allowed": bool(self.candidate_generator_wiring_allowed),
            "style_runtime_wiring_enabled": bool(self.style_runtime_wiring_enabled),
            "runtime_enabled": bool(self.runtime_enabled),
            "converted_now": False,
            "notes_only": True,
            "no_expression_or_pedal": True,
            "does_not_change_default_style_runtime": True,
        }


def align_spread_functional_grouping_contract(
    grouping: SpreadGrouping | str = SpreadGrouping.ONE_PLUS_FOUR,
    *,
    note_count: int | None = None,
) -> SpreadFunctionalGroupingContractAlignment:
    """Return the current SPREAD grouping alignment against core taxonomy.

    The import is intentionally local to avoid making ``spread.py`` depend on
    ``policy.py`` during module initialization.  This keeps the existing
    disposition/policy import boundary intact while still giving tests and docs
    an explicit contract surface for the v2_2_46 alignment.
    """

    grouping_value = grouping.value if isinstance(grouping, SpreadGrouping) else str(grouping)
    note_count = int(note_count if note_count is not None else _density_for_spread_grouping_value(grouping_value))
    try:
        from jammate_engine.core.voicing.policy import FunctionalGrouping, VoicingGroupRole
        from jammate_engine.core.voicing.taxonomy.projection_map import group_indices_for_projection
        from jammate_engine.core.voicing.taxonomy.recipes import group_roles_for_grouping

        runtime_grouping = FunctionalGrouping(grouping_value)
        group_roles = group_roles_for_grouping(runtime_grouping)
        projection_map = group_indices_for_projection(note_count, runtime_grouping, group_roles)
        projection_partition = tuple(tuple(indices) for indices in projection_map.values())
        return SpreadFunctionalGroupingContractAlignment(
            spread_grouping=grouping_value,
            runtime_grouping=runtime_grouping.value,
            runtime_grouping_exists=True,
            group_roles=tuple(role.value if isinstance(role, VoicingGroupRole) else str(role) for role in group_roles),
            projection_partition=projection_partition,
            projection_map_supported=bool(projection_map),
        )
    except ValueError:
        return SpreadFunctionalGroupingContractAlignment(
            spread_grouping=grouping_value,
            runtime_grouping=None,
            runtime_grouping_exists=False,
            group_roles=(),
            projection_partition=(),
            projection_map_supported=False,
        )


def functional_grouping_1plus4_contract_alignment_debug() -> dict[str, object]:
    """Debug dictionary for the v2_2_46 1+4 alignment contract."""

    return align_spread_functional_grouping_contract(SpreadGrouping.ONE_PLUS_FOUR).to_debug_dict()


def _density_for_spread_grouping_value(grouping_value: str) -> int:
    density_by_grouping = {
        "1+3": 4,
        "2+2": 4,
        "1+4": 5,
        "2+3": 5,
        "2+4": 6,
        "3+3": 6,
        "3+4": 7,
    }
    return density_by_grouping.get(str(grouping_value), 0)


class SpreadRuntimeConversionBoundaryStatus(str, Enum):
    """Audit status for each future SPREAD -> VoicingCandidate field mapping.

    The status is deliberately conservative.  v2_2_45 audits conversion edges
    but does not cross them.
    """

    MAPPABLE_NOT_CONVERTED = "mappable_not_converted"
    REQUIRES_RUNTIME_ADAPTER = "requires_runtime_adapter"
    BLOCKED_CURRENT_STAGE = "blocked_current_stage"


class SpreadRuntimeAdapterStatus(str, Enum):
    """Status for the v2_2_47 SPREAD runtime adapter skeleton.

    The adapter skeleton can prove a field mapping in an explicit dry-run, but
    it is not candidate-generator wiring and it is not a style runtime retune.
    """

    DEFAULT_BLOCKED = "default_blocked"
    POLICY_BLOCKED = "policy_blocked"
    INVALID_SOURCE_CANDIDATE = "invalid_source_candidate"
    UNSUPPORTED_GROUPING = "unsupported_grouping"
    ADAPTED_SKELETON_ONLY = "adapted_skeleton_only"


class BalladSpreadRuntimeCandidatePoolStatus(str, Enum):
    """Status for the explicit v2_2_48 Ballad SPREAD pilot candidate pool.

    This is a tightly gated candidate-source integration status, not a default
    Ballad retune.  The existing non-SPREAD runtime pool remains the fallback.
    """

    DEFAULT_DISABLED = "default_disabled"
    STYLE_BLOCKED = "style_blocked"
    ADAPTER_CONVERSION_BLOCKED = "adapter_conversion_blocked"
    CANDIDATE_POOL_MERGE_BLOCKED = "candidate_pool_merge_blocked"
    PILOT_NO_SPREAD_CANDIDATES = "pilot_no_spread_candidates"
    PILOT_CANDIDATES_INTEGRATED = "pilot_candidates_integrated"


class BalladSpreadPilotSelectionAuditStatus(str, Enum):
    """Status for the explicit v2_2_49 Ballad SPREAD pilot selection audit.

    This audit checks whether explicit SPREAD pilot candidates could dominate the
    existing fallback pool by score, count, or ordering assumptions.  It does not
    select a candidate and it does not retune Ballad runtime defaults.
    """

    DEFAULT_DISABLED = "default_disabled"
    STYLE_BLOCKED = "style_blocked"
    POOL_NOT_INTEGRATED = "pool_not_integrated"
    FALLBACK_MISSING = "fallback_missing"
    SPREAD_DOMINANCE_RISK = "spread_dominance_risk"
    FALLBACK_PROTECTED = "fallback_protected"


class BalladSpreadPilotRuntimeEnablementGuardStatus(str, Enum):
    """Status for the explicit v2_2_50 Ballad SPREAD runtime enablement guard.

    This is the first listening-isolation gate for SPREAD candidates.  It is
    intentionally stricter than the v2_2_48 candidate-pool builder: pool flags
    alone are not enough to enter runtime selection.
    """

    DEFAULT_DISABLED = "default_disabled"
    STYLE_BLOCKED = "style_blocked"
    LISTENING_ISOLATION_REQUIRED = "listening_isolation_required"
    CANDIDATE_POOL_NOT_READY = "candidate_pool_not_ready"
    FALLBACK_AUDIT_BLOCKED = "fallback_audit_blocked"
    ENABLED_FOR_LISTENING_ISOLATION = "enabled_for_listening_isolation"


@dataclass(frozen=True)
class SpreadRuntimeAdapterFieldMapping:
    """One explicit source-to-runtime field mapping for the adapter skeleton."""

    source_field: str
    target_field: str
    copied: bool
    reason: str
    source_owner_path: str = "core.voicing.disposition.spread.SpreadProjectionCandidate"
    target_owner_path: str = "core.voicing.candidate.VoicingCandidate"

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "spread_runtime_adapter_skeleton_version": SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION,
            "source_field": self.source_field,
            "target_field": self.target_field,
            "copied": bool(self.copied),
            "reason": self.reason,
            "source_owner_path": self.source_owner_path,
            "target_owner_path": self.target_owner_path,
        }


@dataclass(frozen=True)
class SpreadRuntimeAdapterResult:
    """Result of the explicit SPREAD -> VoicingCandidate adapter skeleton.

    By default this result is blocked and contains no runtime candidate.  When
    explicitly allowed for a dry-run, it may hold a ``VoicingCandidate`` object
    that preserves SPREAD metadata, but generator/style wiring still remains
    disabled.
    """

    source_candidate: SpreadProjectionCandidate | None
    adapted_candidate: Any | None
    status: SpreadRuntimeAdapterStatus
    field_mappings: tuple[SpreadRuntimeAdapterFieldMapping, ...]
    conversion_requested: bool
    conversion_allowed: bool
    reason: str
    candidate_generator_wiring_allowed: bool = False
    style_runtime_wiring_enabled: bool = False
    runtime_enabled: bool = False

    @property
    def converted(self) -> bool:
        return self.adapted_candidate is not None and self.status == SpreadRuntimeAdapterStatus.ADAPTED_SKELETON_ONLY

    def to_debug_dict(self) -> dict[str, object]:
        adapted_debug = None
        if self.adapted_candidate is not None and hasattr(self.adapted_candidate, "to_debug_dict"):
            adapted_debug = self.adapted_candidate.to_debug_dict()
        source_summary = None
        if self.source_candidate is not None:
            source_summary = {
                "chord_symbol": self.source_candidate.chord_symbol,
                "recipe_id": self.source_candidate.recipe_contract.recipe_id,
                "grouping": self.source_candidate.recipe_contract.grouping.value,
                "density": self.source_candidate.density,
                "notes": list(self.source_candidate.notes),
                "degrees": list(self.source_candidate.degrees),
                "is_legal": bool(self.source_candidate.is_legal),
                "notes_only": True,
                "runtime_enabled": bool(self.source_candidate.runtime_enabled),
            }
        return {
            "spread_runtime_adapter_skeleton_version": SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION,
            "layer": "core.voicing.disposition.spread",
            "purpose": "SPREAD Runtime Adapter Skeleton",
            "source_candidate_type": "SpreadProjectionCandidate",
            "target_candidate_type": "VoicingCandidate",
            "source_candidate_summary": source_summary,
            "adapted_candidate_debug": adapted_debug,
            "status": self.status.value,
            "converted": bool(self.converted),
            "reason": self.reason,
            "field_mapping_count": len(self.field_mappings),
            "field_mappings": [item.to_debug_dict() for item in self.field_mappings],
            "candidate_conversion_requested": bool(self.conversion_requested),
            "candidate_conversion_allowed": bool(self.conversion_allowed),
            "candidate_generator_wiring_allowed": bool(self.candidate_generator_wiring_allowed),
            "style_runtime_wiring_enabled": bool(self.style_runtime_wiring_enabled),
            "runtime_enabled": bool(self.runtime_enabled),
            "adapter_skeleton_only": True,
            "notes_only_source": True,
            "no_expression_or_pedal": True,
            "does_not_change_default_style_runtime": True,
        }


@dataclass(frozen=True)
class BalladSpreadRuntimeAdapterSkeletonResult:
    """Adapter skeleton pass over a Ballad safe dry-run trace path."""

    dry_run_result: BalladSpreadRuntimeSafeDryRunResult
    adapter_results: tuple[SpreadRuntimeAdapterResult, ...]
    conversion_requested: bool
    conversion_allowed: bool
    runtime_enabled: bool = False

    @property
    def adapted_candidate_count(self) -> int:
        return sum(1 for item in self.adapter_results if item.converted)

    @property
    def selected_candidate_count(self) -> int:
        return self.dry_run_result.selected_candidate_count

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "spread_runtime_adapter_skeleton_version": SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION,
            "layer": "core.voicing.disposition.spread",
            "purpose": "Ballad SPREAD Runtime Adapter Skeleton",
            "dry_run_completed": bool(self.dry_run_result.dry_run_completed),
            "selected_candidate_count": self.selected_candidate_count,
            "adapter_result_count": len(self.adapter_results),
            "adapted_candidate_count": self.adapted_candidate_count,
            "dry_run_result": self.dry_run_result.to_debug_dict(),
            "adapter_results": [item.to_debug_dict() for item in self.adapter_results],
            "candidate_conversion_requested": bool(self.conversion_requested),
            "candidate_conversion_allowed": bool(self.conversion_allowed),
            "candidate_generator_wiring_allowed": False,
            "style_runtime_wiring_enabled": False,
            "runtime_enabled": bool(self.runtime_enabled),
            "adapter_skeleton_only": True,
            "no_expression_or_pedal": True,
            "does_not_change_medium_swing_or_bossa": True,
        }


@dataclass(frozen=True)
class BalladSpreadRuntimeCandidatePoolPlan:
    """Explicit Ballad pilot plan for adding SPREAD candidates to a candidate pool.

    The plan is disabled by default and requires separate opt-ins for the pilot
    pool, adapter conversion, and pool merge.  This keeps the ordinary Ballad
    runtime and all non-Ballad styles unchanged unless a caller deliberately
    requests the pilot path.
    """

    style_name: str
    candidate_pool_enabled: bool
    adapter_conversion_allowed: bool
    candidate_pool_merge_allowed: bool
    reason: str
    source: str = "policy_metadata_or_explicit_arguments"
    fallback_to_existing_pool: bool = True
    default_style_runtime_unchanged: bool = True

    @property
    def integration_allowed(self) -> bool:
        return (
            self.style_name == "jazz_ballad"
            and self.candidate_pool_enabled
            and self.adapter_conversion_allowed
            and self.candidate_pool_merge_allowed
        )

    @property
    def status(self) -> BalladSpreadRuntimeCandidatePoolStatus:
        if self.style_name != "jazz_ballad":
            return BalladSpreadRuntimeCandidatePoolStatus.STYLE_BLOCKED
        if not self.candidate_pool_enabled:
            return BalladSpreadRuntimeCandidatePoolStatus.DEFAULT_DISABLED
        if not self.adapter_conversion_allowed:
            return BalladSpreadRuntimeCandidatePoolStatus.ADAPTER_CONVERSION_BLOCKED
        if not self.candidate_pool_merge_allowed:
            return BalladSpreadRuntimeCandidatePoolStatus.CANDIDATE_POOL_MERGE_BLOCKED
        return BalladSpreadRuntimeCandidatePoolStatus.PILOT_CANDIDATES_INTEGRATED

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "ballad_spread_runtime_candidate_pool_integration_version": BALLAD_SPREAD_RUNTIME_CANDIDATE_POOL_INTEGRATION_VERSION,
            "layer": "core.voicing.disposition.spread",
            "purpose": "Ballad SPREAD Runtime Pilot Candidate Pool Integration",
            "style_name": self.style_name,
            "candidate_pool_enabled": bool(self.candidate_pool_enabled),
            "adapter_conversion_allowed": bool(self.adapter_conversion_allowed),
            "candidate_pool_merge_allowed": bool(self.candidate_pool_merge_allowed),
            "candidate_generator_wiring_allowed": bool(self.integration_allowed),
            "pilot_candidate_pool_integration_allowed": bool(self.integration_allowed),
            "fallback_to_existing_pool": bool(self.fallback_to_existing_pool),
            "default_style_runtime_unchanged": bool(self.default_style_runtime_unchanged),
            "style_runtime_default_enabled": False,
            "expression_or_pedal_changed": False,
            "reason": self.reason,
            "status": self.status.value,
            "source": self.source,
        }


@dataclass(frozen=True)
class BalladSpreadRuntimeCandidatePoolResult:
    """Explicit pilot candidate-pool result for one chord symbol.

    ``merged_candidates`` always preserves the incoming ``base_candidates`` so
    the existing non-SPREAD runtime remains a fallback even when pilot SPREAD
    candidates are added.
    """

    chord_symbol: str
    plan: BalladSpreadRuntimeCandidatePoolPlan
    base_candidates: tuple[Any, ...]
    adapter_result: BalladSpreadRuntimeAdapterSkeletonResult | None
    spread_candidates: tuple[Any, ...]
    merged_candidates: tuple[Any, ...]
    status: BalladSpreadRuntimeCandidatePoolStatus
    reason: str

    @property
    def base_candidate_count(self) -> int:
        return len(self.base_candidates)

    @property
    def spread_candidate_count(self) -> int:
        return len(self.spread_candidates)

    @property
    def merged_candidate_count(self) -> int:
        return len(self.merged_candidates)

    @property
    def candidate_pool_integrated(self) -> bool:
        return self.status == BalladSpreadRuntimeCandidatePoolStatus.PILOT_CANDIDATES_INTEGRATED

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "ballad_spread_runtime_candidate_pool_integration_version": BALLAD_SPREAD_RUNTIME_CANDIDATE_POOL_INTEGRATION_VERSION,
            "layer": "core.voicing.disposition.spread",
            "purpose": "Ballad SPREAD Runtime Pilot Candidate Pool Integration",
            "chord_symbol": self.chord_symbol,
            "plan": self.plan.to_debug_dict(),
            "status": self.status.value,
            "reason": self.reason,
            "base_candidate_count": self.base_candidate_count,
            "spread_candidate_count": self.spread_candidate_count,
            "merged_candidate_count": self.merged_candidate_count,
            "candidate_pool_integrated": bool(self.candidate_pool_integrated),
            "fallback_to_existing_pool": True,
            "base_pool_retained": self.base_candidate_count <= self.merged_candidate_count,
            "spread_candidate_summaries": [
                candidate.to_debug_dict() if hasattr(candidate, "to_debug_dict") else {"repr": repr(candidate)}
                for candidate in self.spread_candidates
            ],
            "adapter_result": self.adapter_result.to_debug_dict() if self.adapter_result is not None else None,
            "candidate_generator_wiring_allowed": bool(self.plan.integration_allowed and self.candidate_pool_integrated),
            "style_runtime_default_enabled": False,
            "default_style_runtime_unchanged": True,
            "no_expression_or_pedal": True,
            "does_not_change_medium_swing_or_bossa": True,
        }


@dataclass(frozen=True)
class SpreadRuntimeConversionFieldAudit:
    """One field-level audit row for future SpreadProjectionCandidate conversion."""

    source_field: str
    target_field: str
    status: SpreadRuntimeConversionBoundaryStatus
    reason: str
    source_owner_path: str = "core.voicing.disposition.spread.SpreadProjectionCandidate"
    target_owner_path: str = "core.voicing.candidate.VoicingCandidate"
    future_adapter_required: bool = True

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "spread_runtime_conversion_boundary_audit_version": SPREAD_RUNTIME_CONVERSION_BOUNDARY_AUDIT_VERSION,
            "source_field": self.source_field,
            "target_field": self.target_field,
            "status": self.status.value,
            "reason": self.reason,
            "source_owner_path": self.source_owner_path,
            "target_owner_path": self.target_owner_path,
            "future_adapter_required": bool(self.future_adapter_required),
            "converted_now": False,
        }


@dataclass(frozen=True)
class SpreadRuntimeConversionBoundaryAudit:
    """Boundary audit for future SPREAD notes-only candidate conversion.

    This object documents how a ``SpreadProjectionCandidate`` could eventually
    become a runtime ``VoicingCandidate``.  It intentionally does not create or
    return a ``VoicingCandidate`` so v2_2_45 remains an audit/contract pass.
    """

    candidate: SpreadProjectionCandidate | None = None
    field_audits: tuple[SpreadRuntimeConversionFieldAudit, ...] = ()
    source_candidate_type: str = "SpreadProjectionCandidate"
    target_candidate_type: str = "VoicingCandidate"
    source_owner_path: str = "core.voicing.disposition.spread"
    target_owner_path: str = "core.voicing.candidate"
    candidate_generator_owner_path: str = "core.voicing.candidate_generator"
    conversion_allowed: bool = False
    candidate_generator_wiring_allowed: bool = False
    style_runtime_wiring_enabled: bool = False
    runtime_enabled: bool = False

    @property
    def candidate_present(self) -> bool:
        return self.candidate is not None

    @property
    def candidate_is_legal(self) -> bool:
        return bool(self.candidate.is_legal) if self.candidate is not None else False

    @property
    def mappable_field_count(self) -> int:
        return sum(1 for item in self.field_audits if item.status == SpreadRuntimeConversionBoundaryStatus.MAPPABLE_NOT_CONVERTED)

    @property
    def adapter_required_field_count(self) -> int:
        return sum(1 for item in self.field_audits if item.status == SpreadRuntimeConversionBoundaryStatus.REQUIRES_RUNTIME_ADAPTER)

    @property
    def blocked_field_count(self) -> int:
        return sum(1 for item in self.field_audits if item.status == SpreadRuntimeConversionBoundaryStatus.BLOCKED_CURRENT_STAGE)

    @property
    def functional_grouping_gap(self) -> str:
        if self.candidate is None:
            return "candidate_not_provided"
        grouping = self.candidate.recipe_contract.grouping.value
        known_runtime_groupings = {"2", "3", "1+3", "2+2", "1+4", "2+3", "2+4", "3+3", "3+4"}
        if grouping in known_runtime_groupings:
            return "runtime_functional_grouping_value_exists"
        return f"runtime_functional_grouping_missing:{grouping}"

    def to_debug_dict(self) -> dict[str, object]:
        candidate_summary = None
        if self.candidate is not None:
            candidate_summary = {
                "chord_symbol": self.candidate.chord_symbol,
                "recipe_id": self.candidate.recipe_contract.recipe_id,
                "grouping": self.candidate.recipe_contract.grouping.value,
                "density": self.candidate.density,
                "notes": list(self.candidate.notes),
                "degrees": list(self.candidate.degrees),
                "is_legal": bool(self.candidate.is_legal),
                "runtime_enabled": bool(self.candidate.runtime_enabled),
                "notes_only": True,
            }
        return {
            "spread_runtime_conversion_boundary_audit_version": SPREAD_RUNTIME_CONVERSION_BOUNDARY_AUDIT_VERSION,
            "layer": "core.voicing.disposition.spread",
            "purpose": "Ballad SPREAD Runtime Conversion Boundary Audit",
            "source_candidate_type": self.source_candidate_type,
            "target_candidate_type": self.target_candidate_type,
            "source_owner_path": self.source_owner_path,
            "target_owner_path": self.target_owner_path,
            "candidate_generator_owner_path": self.candidate_generator_owner_path,
            "candidate_present": bool(self.candidate_present),
            "candidate_is_legal": bool(self.candidate_is_legal),
            "candidate_summary": candidate_summary,
            "field_audit_count": len(self.field_audits),
            "mappable_field_count": self.mappable_field_count,
            "adapter_required_field_count": self.adapter_required_field_count,
            "blocked_field_count": self.blocked_field_count,
            "functional_grouping_gap": self.functional_grouping_gap,
            "field_audits": [item.to_debug_dict() for item in self.field_audits],
            "required_future_steps": [
                "define_explicit_spread_projection_candidate_to_voicing_candidate_adapter",
                "functional_grouping_1plus4_contract_aligned_before_runtime_conversion",
                "decide_content_family_root_support_bass_relation_interval_structure_mapping",
                "wire_candidate_generator_only_after_explicit_style_policy_gate",
                "preserve_fallback_to_existing_non_spread_voicing_runtime",
            ],
            "candidate_conversion_allowed": bool(self.conversion_allowed),
            "candidate_generator_wiring_allowed": bool(self.candidate_generator_wiring_allowed),
            "style_runtime_wiring_enabled": bool(self.style_runtime_wiring_enabled),
            "runtime_enabled": bool(self.runtime_enabled),
            "converted_now": False,
            "notes_only": True,
            "no_expression_or_pedal": True,
            "does_not_change_default_style_runtime": True,
        }


@dataclass(frozen=True)
class BalladSpreadRuntimeConversionBoundaryAuditResult:
    """Dry-run conversion-boundary audit over a Ballad SPREAD trace path."""

    dry_run_result: BalladSpreadRuntimeSafeDryRunResult
    candidate_audits: tuple[SpreadRuntimeConversionBoundaryAudit, ...]
    runtime_enabled: bool = False

    @property
    def audit_count(self) -> int:
        return len(self.candidate_audits)

    @property
    def selected_candidate_count(self) -> int:
        return self.dry_run_result.selected_candidate_count

    @property
    def conversion_allowed(self) -> bool:
        return False

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "spread_runtime_conversion_boundary_audit_version": SPREAD_RUNTIME_CONVERSION_BOUNDARY_AUDIT_VERSION,
            "layer": "core.voicing.disposition.spread",
            "purpose": "Ballad SPREAD Runtime Conversion Boundary Audit",
            "dry_run_completed": bool(self.dry_run_result.dry_run_completed),
            "selected_candidate_count": self.selected_candidate_count,
            "audit_count": self.audit_count,
            "dry_run_result": self.dry_run_result.to_debug_dict(),
            "candidate_audits": [audit.to_debug_dict() for audit in self.candidate_audits],
            "candidate_conversion_allowed": False,
            "candidate_generator_wiring_allowed": False,
            "style_runtime_wiring_enabled": False,
            "runtime_enabled": bool(self.runtime_enabled),
            "converted_now": False,
            "notes_only": True,
            "no_expression_or_pedal": True,
            "boundary_audit_only": True,
            "does_not_change_medium_swing_or_bossa": True,
        }


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


def score_spread_groupwise_voice_leading(
    current: SpreadProjectionCandidate,
    previous: SpreadProjectionCandidate | None = None,
    weights: SpreadGroupwiseVoiceLeadingWeights | None = None,
) -> SpreadGroupwiseVoiceLeadingScore:
    """Score one SPREAD candidate with lower/upper group-wise continuity.

    This is the v2_2_41 scorer boundary.  It works on notes-only SPREAD
    projection candidates and does not enable any style runtime path.
    """

    scoring_weights = weights or SpreadGroupwiseVoiceLeadingWeights()
    lower_motion = _paired_note_motion(previous.lower_notes if previous is not None else (), current.lower_notes)
    upper_motion = _paired_note_motion(previous.upper_notes if previous is not None else (), current.upper_notes)
    top_motion = _top_voice_motion(previous, current)
    gap_change = _group_gap_change(previous, current)
    span_penalty = _spread_span_penalty(current)
    register_penalty = _spread_register_penalty(current)
    legality_penalty = 0.0 if current.is_legal else float(scoring_weights.legality_penalty)
    weighted_penalty = (
        float(lower_motion) * float(scoring_weights.lower_group_motion)
        + float(upper_motion) * float(scoring_weights.upper_group_motion)
        + float(top_motion) * float(scoring_weights.top_voice_motion)
        + float(gap_change) * float(scoring_weights.group_gap_stability)
        + float(span_penalty) * float(scoring_weights.span_penalty)
        + float(register_penalty) * float(scoring_weights.register_penalty)
        + legality_penalty
    )
    return SpreadGroupwiseVoiceLeadingScore(
        current=current,
        previous=previous,
        lower_group_motion=int(lower_motion),
        upper_group_motion=int(upper_motion),
        top_voice_motion=int(top_motion),
        group_gap_change=int(gap_change),
        span_penalty=int(span_penalty),
        register_penalty=int(register_penalty),
        legality_penalty=float(legality_penalty),
        weighted_penalty=float(weighted_penalty),
        weights=scoring_weights,
    )


def rank_spread_candidates_by_groupwise_voice_leading(
    candidates: tuple[SpreadProjectionCandidate, ...] | list[SpreadProjectionCandidate],
    previous: SpreadProjectionCandidate | None = None,
    weights: SpreadGroupwiseVoiceLeadingWeights | None = None,
    *,
    legal_only: bool = True,
) -> tuple[SpreadGroupwiseVoiceLeadingScore, ...]:
    """Rank SPREAD projection candidates by group-wise voice-leading penalty."""

    usable = [candidate for candidate in candidates if (candidate.is_legal or not legal_only)]
    scores = [score_spread_groupwise_voice_leading(candidate, previous, weights) for candidate in usable]
    scores.sort(
        key=lambda score: (
            float(score.weighted_penalty),
            score.lower_group_motion,
            score.upper_group_motion,
            score.top_voice_motion,
            score.current.group_gap_semitones if score.current.group_gap_semitones is not None else 999,
            score.current.notes,
        )
    )
    return tuple(scores)


def select_spread_candidate_by_groupwise_voice_leading(
    candidates: tuple[SpreadProjectionCandidate, ...] | list[SpreadProjectionCandidate],
    previous: SpreadProjectionCandidate | None = None,
    weights: SpreadGroupwiseVoiceLeadingWeights | None = None,
    *,
    legal_only: bool = True,
) -> SpreadProjectionCandidate | None:
    """Return the best candidate from the notes-only group-wise scorer."""

    ranked = rank_spread_candidates_by_groupwise_voice_leading(candidates, previous, weights, legal_only=legal_only)
    return ranked[0].current if ranked else None


def spread_groupwise_voice_leading_path_debug(
    chord_symbols: tuple[str, ...] = ("Dm7", "G7", "Cmaj7"),
    *,
    contract_id: str = "spread_2plus3_contract",
    policy: Any | None = None,
    weights: SpreadGroupwiseVoiceLeadingWeights | None = None,
    max_upper_options: int = 12,
) -> dict[str, object]:
    """Greedy notes-only debug path for SPREAD group-wise voice-leading."""

    selected: list[SpreadProjectionCandidate] = []
    score_path: list[SpreadGroupwiseVoiceLeadingScore] = []
    previous: SpreadProjectionCandidate | None = None
    for symbol in chord_symbols:
        result = project_basic_spread_contract(symbol, contract_id, policy, max_upper_options=max_upper_options)
        ranked = rank_spread_candidates_by_groupwise_voice_leading(result.candidates, previous, weights)
        if not ranked:
            continue
        score = ranked[0]
        score_path.append(score)
        selected.append(score.current)
        previous = score.current
    return {
        "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
        "basic_spread_projection_version": BASIC_SPREAD_PROJECTION_VERSION,
        "groupwise_spread_voice_leading_version": GROUPWISE_SPREAD_VOICE_LEADING_VERSION,
        "layer": "core.voicing.disposition.spread",
        "purpose": "Group-wise SPREAD voice-leading scorer debug path",
        "contract_id": contract_id,
        "chord_symbols": list(chord_symbols),
        "selected_candidate_count": len(selected),
        "selected_lower_group_path": [list(candidate.lower_notes) for candidate in selected],
        "selected_upper_group_path": [list(candidate.upper_notes) for candidate in selected],
        "selected_top_voice_path": [max(candidate.notes) if candidate.notes else None for candidate in selected],
        "scores": [score.to_debug_dict() for score in score_path],
        "scored_groupwise_not_total_motion_only": True,
        "runtime_enabled": False,
        "notes_only": True,
        "no_expression_or_pedal": True,
    }


def spread_runtime_gate_from_policy(
    policy: Any | None = None,
    *,
    texture_state: Any | None = None,
    explicit_enable: bool | None = None,
) -> SpreadRuntimeGateDecision:
    """Resolve the v2_2_42 safety gate for SPREAD candidate selection.

    The default is closed.  Opening the selector gate requires an explicit
    metadata request and a SPREAD texture-family request.  This helper still
    does not wire SPREAD into the style runtime or convert candidates.
    """

    values = _spread_selector_gate_values(policy)
    if explicit_enable is not None:
        values["explicit_enable_argument"] = bool(explicit_enable)
    explicit_request = _spread_bool_any(
        values,
        (
            "explicit_enable_argument",
            "spread_candidate_selector_enabled",
            "spread_selector_enabled",
            "spread_runtime_gate_enabled",
            "spread_runtime_enabled",
            "enable_spread_runtime",
            "use_spread_voicing_runtime",
        ),
        default=False,
    )
    primary_family, allowed_families = _spread_requested_families(values, texture_state)
    family_values = {value for value in (*allowed_families, primary_family or "") if value}
    spread_family_requested = "spread" in family_values

    if not explicit_request:
        reason = "explicit_spread_runtime_gate_not_requested"
        gate_open = False
    elif not spread_family_requested:
        reason = "explicit_request_without_spread_texture_family"
        gate_open = False
    else:
        reason = "explicit_policy_requested_spread_selector_gate"
        gate_open = True

    return SpreadRuntimeGateDecision(
        selector_gate_open=gate_open,
        reason=reason,
        explicit_request=explicit_request,
        spread_family_requested=spread_family_requested,
        primary_family=primary_family,
        allowed_families=allowed_families,
        source="explicit_argument" if explicit_enable is not None else "policy_metadata",
        style_runtime_wiring_enabled=False,
        candidate_conversion_allowed=False,
        notes_only=True,
        runtime_enabled=False,
    )


def select_spread_candidate_with_runtime_gate(
    chord_symbol: str,
    policy: Any | None = None,
    *,
    previous: SpreadProjectionCandidate | None = None,
    texture_state: Any | None = None,
    contract_ids: tuple[str, ...] | list[str] | None = None,
    weights: SpreadGroupwiseVoiceLeadingWeights | None = None,
    max_upper_options: int = 12,
    legal_only: bool = True,
    explicit_enable: bool | None = None,
) -> SpreadCandidateSelectorResult:
    """Select a notes-only SPREAD candidate through the v2_2_42 gate.

    This is a selector contract, not style runtime wiring.  When the gate is
    closed, it returns no candidates.  When the gate is open, it projects and
    ranks ``SpreadProjectionCandidate`` objects only.
    """

    requested_contracts = tuple(str(item) for item in (contract_ids or ()))
    request = SpreadCandidateSelectorRequest(
        chord_symbol=str(chord_symbol),
        contract_ids=requested_contracts,
        max_upper_options=int(max_upper_options),
        legal_only=bool(legal_only),
    )
    gate = spread_runtime_gate_from_policy(policy, texture_state=texture_state, explicit_enable=explicit_enable)
    if not gate.selector_gate_open:
        return SpreadCandidateSelectorResult(
            request=request,
            gate=gate,
            projected_results=(),
            ranked_scores=(),
            selected=None,
            selected_score=None,
        )

    projected = project_basic_spread_candidates(
        chord_symbol,
        policy,
        contract_ids=requested_contracts or None,
        max_upper_options=max_upper_options,
    )
    all_candidates: list[SpreadProjectionCandidate] = []
    for result in projected:
        all_candidates.extend(result.candidates)
    ranked = rank_spread_candidates_by_groupwise_voice_leading(
        all_candidates,
        previous,
        weights,
        legal_only=legal_only,
    )
    selected_score = ranked[0] if ranked else None
    return SpreadCandidateSelectorResult(
        request=request,
        gate=gate,
        projected_results=tuple(projected),
        ranked_scores=tuple(ranked),
        selected=selected_score.current if selected_score is not None else None,
        selected_score=selected_score,
    )


def spread_candidate_selector_contract_debug(
    chord_symbol: str = "Cmaj7",
    policy: Any | None = None,
    *,
    contract_ids: tuple[str, ...] | list[str] | None = None,
    explicit_enable: bool | None = None,
) -> dict[str, object]:
    """Return v2_2_42 SPREAD selector/gate debug metadata."""

    result = select_spread_candidate_with_runtime_gate(
        chord_symbol,
        policy,
        contract_ids=contract_ids,
        explicit_enable=explicit_enable,
    )
    return {
        "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
        "basic_spread_projection_version": BASIC_SPREAD_PROJECTION_VERSION,
        "groupwise_spread_voice_leading_version": GROUPWISE_SPREAD_VOICE_LEADING_VERSION,
        "spread_selector_runtime_gate_version": SPREAD_SELECTOR_RUNTIME_GATE_VERSION,
        "layer": "core.voicing.disposition.spread",
        "purpose": "SPREAD Candidate Selector Contract / Runtime Gate Skeleton",
        "result": result.to_debug_dict(),
        "default_gate_closed_without_explicit_policy": not result.gate.selector_gate_open,
        "candidate_conversion_allowed": False,
        "style_runtime_wiring_enabled": False,
        "runtime_enabled": False,
        "notes_only": True,
        "no_expression_or_pedal": True,
    }



def ballad_spread_runtime_entry_contract(
    policy: Any | None = None,
    *,
    style_name: str | None = None,
    scene: str | BalladSpreadEntryScene | None = None,
    enabled: bool | None = None,
    contract_ids: tuple[str, ...] | list[str] | None = None,
) -> BalladSpreadRuntimeEntryContract:
    """Return the v2_2_43 Ballad SPREAD pilot entry contract.

    The default contract is disabled.  Enabling requires explicit metadata or an
    explicit function argument, and later selection still goes through the
    v2_2_42 SPREAD selector gate.
    """

    values = _ballad_spread_entry_values(policy)
    resolved_style = _normalize_style_name(style_name or values.get("style_name") or values.get("style"))
    resolved_scene = _coerce_ballad_spread_scene(scene or values.get("scene") or values.get("ballad_spread_scene"))
    pilot_enabled = bool(enabled) if enabled is not None else _spread_bool_any(
        values,
        (
            "enabled",
            "pilot_enabled",
            "ballad_spread_runtime_pilot_enabled",
            "ballad_spread_entry_enabled",
            "enable_ballad_spread_runtime_pilot",
        ),
        default=False,
    )
    requested_contract_ids = _valid_ballad_spread_contract_ids(contract_ids or values.get("contract_ids"))
    preferred_contract_ids = _valid_ballad_spread_contract_ids(values.get("preferred_contract_ids")) or tuple(
        contract_id for contract_id in BALLAD_SPREAD_ENTRY_PREFERRED_CONTRACT_IDS if contract_id in requested_contract_ids
    )
    return BalladSpreadRuntimeEntryContract(
        style_name=resolved_style or "",
        pilot_enabled=pilot_enabled,
        scene=resolved_scene,
        allowed_contract_ids=requested_contract_ids or BALLAD_SPREAD_ENTRY_ALLOWED_CONTRACT_IDS,
        preferred_contract_ids=preferred_contract_ids or BALLAD_SPREAD_ENTRY_PREFERRED_CONTRACT_IDS,
        source="explicit_argument" if enabled is not None or style_name is not None or scene is not None else "policy_metadata_or_default_contract",
    )


def resolve_ballad_spread_runtime_entry(
    policy: Any | None = None,
    *,
    texture_state: Any | None = None,
    style_name: str | None = None,
    scene: str | BalladSpreadEntryScene | None = None,
    explicit_enable: bool | None = None,
) -> BalladSpreadRuntimeEntryDecision:
    """Resolve whether a future Ballad SPREAD pilot may enter notes-only selection."""

    contract = ballad_spread_runtime_entry_contract(
        policy,
        style_name=style_name,
        scene=scene,
        enabled=explicit_enable,
    )
    gate = spread_runtime_gate_from_policy(policy, texture_state=texture_state, explicit_enable=explicit_enable)
    if contract.style_name not in contract.allowed_style_names:
        allowed = False
        reason = "style_not_allowed_for_ballad_spread_pilot"
    elif not contract.pilot_enabled:
        allowed = False
        reason = "ballad_spread_runtime_pilot_not_enabled"
    elif contract.scene not in contract.allowed_scenes:
        allowed = False
        reason = "ballad_spread_scene_not_allowed"
    elif not gate.selector_gate_open:
        allowed = False
        reason = f"spread_selector_gate_closed:{gate.reason}"
    else:
        allowed = True
        reason = "ballad_spread_pilot_entry_allowed_notes_only"
    return BalladSpreadRuntimeEntryDecision(
        contract=contract,
        gate=gate,
        entry_allowed=allowed,
        reason=reason,
    )


def select_ballad_spread_pilot_candidate(
    chord_symbol: str,
    policy: Any | None = None,
    *,
    previous: SpreadProjectionCandidate | None = None,
    texture_state: Any | None = None,
    style_name: str | None = None,
    scene: str | BalladSpreadEntryScene | None = None,
    explicit_enable: bool | None = None,
    weights: SpreadGroupwiseVoiceLeadingWeights | None = None,
    max_upper_options: int = 12,
    legal_only: bool = True,
) -> BalladSpreadRuntimePilotResult:
    """Select a notes-only SPREAD candidate for the guarded Ballad pilot contract.

    This helper is still not runtime wiring.  It delegates to the existing
    selector gate and returns ``SpreadProjectionCandidate`` only.
    """

    decision = resolve_ballad_spread_runtime_entry(
        policy,
        texture_state=texture_state,
        style_name=style_name,
        scene=scene,
        explicit_enable=explicit_enable,
    )
    if not decision.entry_allowed:
        return BalladSpreadRuntimePilotResult(
            chord_symbol=str(chord_symbol),
            decision=decision,
            selector_result=None,
            selected=None,
        )
    selector = select_spread_candidate_with_runtime_gate(
        chord_symbol,
        policy,
        previous=previous,
        texture_state=texture_state,
        contract_ids=decision.contract.preferred_contract_ids or decision.contract.allowed_contract_ids,
        weights=weights,
        max_upper_options=max_upper_options,
        legal_only=legal_only,
        explicit_enable=explicit_enable,
    )
    return BalladSpreadRuntimePilotResult(
        chord_symbol=str(chord_symbol),
        decision=decision,
        selector_result=selector,
        selected=selector.selected,
    )


def ballad_spread_runtime_entry_debug(
    chord_symbol: str = "Cmaj7",
    policy: Any | None = None,
    *,
    texture_state: Any | None = None,
    style_name: str | None = None,
    scene: str | BalladSpreadEntryScene | None = None,
    explicit_enable: bool | None = None,
) -> dict[str, object]:
    """Return v2_2_43 Ballad SPREAD pilot entry debug metadata."""

    result = select_ballad_spread_pilot_candidate(
        chord_symbol,
        policy,
        texture_state=texture_state,
        style_name=style_name,
        scene=scene,
        explicit_enable=explicit_enable,
    )
    return {
        "ballad_spread_runtime_entry_contract_version": BALLAD_SPREAD_RUNTIME_ENTRY_CONTRACT_VERSION,
        "layer": "core.voicing.disposition.spread",
        "purpose": "SPREAD Runtime Pilot Planning / Ballad Entry Contract",
        "result": result.to_debug_dict(),
        "default_entry_closed_without_explicit_ballad_pilot": not result.decision.entry_allowed,
        "style_runtime_wiring_enabled": False,
        "candidate_conversion_allowed": False,
        "runtime_enabled": False,
        "notes_only": True,
        "no_expression_or_pedal": True,
        "does_not_change_medium_swing_or_bossa": True,
    }


def ballad_spread_runtime_pilot_wiring_plan(
    policy: Any | None = None,
    *,
    style_name: str | None = None,
    enabled: bool | None = None,
) -> BalladSpreadRuntimePilotWiringPlan:
    """Return the v2_2_44 safe dry-run wiring plan for Ballad SPREAD.

    This is a contract/debug surface only.  It names how a future runtime pilot
    would flow, but keeps conversion and style runtime wiring disabled.
    """

    entry_values = _ballad_spread_entry_values(policy)
    dry_run_values = _ballad_spread_dry_run_values(policy)
    merged = {**entry_values, **dry_run_values}
    resolved_style = _normalize_style_name(style_name or merged.get("style_name") or merged.get("style")) or "jazz_ballad"
    dry_run_enabled = bool(enabled) if enabled is not None else _spread_bool_any(
        merged,
        (
            "dry_run_enabled",
            "safe_dry_run_enabled",
            "ballad_spread_runtime_safe_dry_run_enabled",
            "enable_ballad_spread_runtime_safe_dry_run",
        ),
        default=False,
    )
    return BalladSpreadRuntimePilotWiringPlan(
        style_name=resolved_style,
        dry_run_enabled=dry_run_enabled,
        source="explicit_argument" if enabled is not None or style_name is not None else "policy_metadata_or_default_contract",
    )


def run_ballad_spread_runtime_safe_dry_run(
    chord_symbols: tuple[str, ...] | list[str] = ("Dm7", "G7", "Cmaj7"),
    policy: Any | None = None,
    *,
    texture_state: Any | None = None,
    style_name: str | None = None,
    scene: str | BalladSpreadEntryScene | None = None,
    explicit_enable: bool | None = None,
    weights: SpreadGroupwiseVoiceLeadingWeights | None = None,
    max_upper_options: int = 12,
    legal_only: bool = True,
) -> BalladSpreadRuntimeSafeDryRunResult:
    """Run a safe notes-only Ballad SPREAD dry run across chord symbols.

    The chain is: Ballad entry contract -> SPREAD selector gate -> basic
    projection -> group-wise ranking -> notes-only selected candidate.  It does
    not convert the selected candidate to a runtime ``VoicingCandidate``.
    """

    symbols = tuple(str(symbol) for symbol in chord_symbols)
    plan = ballad_spread_runtime_pilot_wiring_plan(policy, style_name=style_name, enabled=explicit_enable)
    if not plan.dry_run_enabled:
        return BalladSpreadRuntimeSafeDryRunResult(
            wiring_plan=plan,
            chord_symbols=symbols,
            traces=(),
            blocked_reason="ballad_spread_runtime_safe_dry_run_not_enabled",
        )

    traces: list[BalladSpreadRuntimeDryRunChordTrace] = []
    previous: SpreadProjectionCandidate | None = None
    for symbol in symbols:
        pilot_result = select_ballad_spread_pilot_candidate(
            symbol,
            policy,
            previous=previous,
            texture_state=texture_state,
            style_name=plan.style_name,
            scene=scene,
            explicit_enable=explicit_enable,
            weights=weights,
            max_upper_options=max_upper_options,
            legal_only=legal_only,
        )
        trace = BalladSpreadRuntimeDryRunChordTrace(
            chord_symbol=symbol,
            pilot_result=pilot_result,
            previous_candidate=previous,
        )
        traces.append(trace)
        if pilot_result.selected is not None:
            previous = pilot_result.selected
        else:
            return BalladSpreadRuntimeSafeDryRunResult(
                wiring_plan=plan,
                chord_symbols=symbols,
                traces=tuple(traces),
                blocked_reason=pilot_result.decision.reason,
            )

    return BalladSpreadRuntimeSafeDryRunResult(
        wiring_plan=plan,
        chord_symbols=symbols,
        traces=tuple(traces),
    )


def ballad_spread_runtime_safe_dry_run_debug(
    chord_symbols: tuple[str, ...] | list[str] = ("Dm7", "G7", "Cmaj7"),
    policy: Any | None = None,
    *,
    texture_state: Any | None = None,
    style_name: str | None = None,
    scene: str | BalladSpreadEntryScene | None = None,
    explicit_enable: bool | None = None,
) -> dict[str, object]:
    """Return v2_2_44 Ballad SPREAD safe dry-run debug metadata."""

    result = run_ballad_spread_runtime_safe_dry_run(
        chord_symbols,
        policy,
        texture_state=texture_state,
        style_name=style_name,
        scene=scene,
        explicit_enable=explicit_enable,
    )
    return {
        "ballad_spread_runtime_safe_dry_run_version": BALLAD_SPREAD_RUNTIME_SAFE_DRY_RUN_VERSION,
        "layer": "core.voicing.disposition.spread",
        "purpose": "Ballad SPREAD Runtime Pilot Wiring Plan + Safe Dry Run",
        "result": result.to_debug_dict(),
        "candidate_conversion_allowed": False,
        "style_runtime_wiring_enabled": False,
        "runtime_enabled": False,
        "notes_only": True,
        "no_expression_or_pedal": True,
        "safe_dry_run_only": True,
        "does_not_change_medium_swing_or_bossa": True,
    }


def spread_runtime_conversion_boundary_audit(
    candidate: SpreadProjectionCandidate | None = None,
) -> SpreadRuntimeConversionBoundaryAudit:
    """Audit the future SPREAD -> VoicingCandidate conversion boundary.

    v2_2_45 is intentionally non-converting.  The returned audit names safe
    field mappings, unresolved adapter decisions, and hard blocks that must stay
    closed until a later explicit runtime wiring pass.
    """

    fields = [
        SpreadRuntimeConversionFieldAudit(
            source_field="candidate.notes",
            target_field="VoicingCandidate.notes",
            status=SpreadRuntimeConversionBoundaryStatus.MAPPABLE_NOT_CONVERTED,
            reason="placed MIDI notes are available on the notes-only SPREAD candidate but are not copied into a runtime candidate in v2_2_45",
            future_adapter_required=True,
        ),
        SpreadRuntimeConversionFieldAudit(
            source_field="candidate.degrees",
            target_field="VoicingCandidate.degrees",
            status=SpreadRuntimeConversionBoundaryStatus.MAPPABLE_NOT_CONVERTED,
            reason="placed degree labels are available but need a dedicated adapter to preserve lower/upper group metadata",
            future_adapter_required=True,
        ),
        SpreadRuntimeConversionFieldAudit(
            source_field="candidate.recipe_contract.grouping",
            target_field="VoicingCandidate.functional_grouping",
            status=SpreadRuntimeConversionBoundaryStatus.REQUIRES_RUNTIME_ADAPTER,
            reason="SPREAD grouping values are reconciled with core FunctionalGrouping, including 1+4, but runtime conversion still requires a dedicated adapter",
            future_adapter_required=True,
        ),
        SpreadRuntimeConversionFieldAudit(
            source_field="candidate.lower/upper metadata",
            target_field="VoicingCandidate.group_roles",
            status=SpreadRuntimeConversionBoundaryStatus.REQUIRES_RUNTIME_ADAPTER,
            reason="lower/foundation and upper/projection roles are metadata-rich and need explicit role mapping instead of implicit LH/RH assumptions",
            future_adapter_required=True,
        ),
        SpreadRuntimeConversionFieldAudit(
            source_field="candidate.metadata",
            target_field="VoicingCandidate.metadata",
            status=SpreadRuntimeConversionBoundaryStatus.REQUIRES_RUNTIME_ADAPTER,
            reason="metadata can be preserved later, but runtime selector/rescue fields must be merged deliberately",
            future_adapter_required=True,
        ),
        SpreadRuntimeConversionFieldAudit(
            source_field="candidate.recipe_contract / upper_source",
            target_field="VoicingCandidate.content_family/root_support/bass_relation/interval_structure",
            status=SpreadRuntimeConversionBoundaryStatus.REQUIRES_RUNTIME_ADAPTER,
            reason="runtime semantic axes must be resolved from style policy and source content, not guessed inside the SPREAD projection helper",
            future_adapter_required=True,
        ),
        SpreadRuntimeConversionFieldAudit(
            source_field="candidate.runtime_enabled",
            target_field="candidate_generator runtime pool",
            status=SpreadRuntimeConversionBoundaryStatus.BLOCKED_CURRENT_STAGE,
            reason="v2_2_45 audits the boundary only; style runtime wiring and candidate-generator injection remain disabled",
            future_adapter_required=True,
        ),
    ]
    return SpreadRuntimeConversionBoundaryAudit(
        candidate=candidate,
        field_audits=tuple(fields),
        conversion_allowed=False,
        candidate_generator_wiring_allowed=False,
        style_runtime_wiring_enabled=False,
        runtime_enabled=False,
    )


def audit_ballad_spread_runtime_conversion_boundaries(
    chord_symbols: tuple[str, ...] | list[str],
    policy: Any | None,
    *,
    texture_state: Any | None = None,
    explicit_enable: bool | None = None,
) -> BalladSpreadRuntimeConversionBoundaryAuditResult:
    """Run the safe dry-run path and audit selected candidate conversion edges.

    This is still a dry-run/audit surface.  It never creates a
    ``VoicingCandidate`` and never wires SPREAD into style runtime generation.
    """

    dry_run = run_ballad_spread_runtime_safe_dry_run(
        chord_symbols,
        policy,
        texture_state=texture_state,
        explicit_enable=explicit_enable,
    )
    audits = tuple(spread_runtime_conversion_boundary_audit(candidate) for candidate in dry_run.selected_candidates)
    return BalladSpreadRuntimeConversionBoundaryAuditResult(
        dry_run_result=dry_run,
        candidate_audits=audits,
        runtime_enabled=False,
    )


def spread_runtime_conversion_boundary_debug(
    candidate: SpreadProjectionCandidate | None = None,
) -> dict[str, object]:
    audit = spread_runtime_conversion_boundary_audit(candidate)
    return {
        "spread_runtime_conversion_boundary_audit_version": SPREAD_RUNTIME_CONVERSION_BOUNDARY_AUDIT_VERSION,
        "default_conversion_allowed": False,
        "candidate_generator_wiring_allowed": False,
        "style_runtime_wiring_enabled": False,
        "runtime_enabled": False,
        "audit": audit.to_debug_dict(),
        "notes_only": True,
        "no_expression_or_pedal": True,
        "boundary_audit_only": True,
    }


def ballad_spread_runtime_conversion_boundary_debug(
    chord_symbols: tuple[str, ...] | list[str] = ("Dm7", "G7", "Cmaj7"),
    policy: Any | None = None,
    *,
    texture_state: Any | None = None,
    explicit_enable: bool | None = None,
) -> dict[str, object]:
    result = audit_ballad_spread_runtime_conversion_boundaries(
        chord_symbols,
        policy,
        texture_state=texture_state,
        explicit_enable=explicit_enable,
    )
    return {
        "spread_runtime_conversion_boundary_audit_version": SPREAD_RUNTIME_CONVERSION_BOUNDARY_AUDIT_VERSION,
        "result": result.to_debug_dict(),
        "candidate_conversion_allowed": False,
        "candidate_generator_wiring_allowed": False,
        "style_runtime_wiring_enabled": False,
        "runtime_enabled": False,
        "converted_now": False,
        "notes_only": True,
        "no_expression_or_pedal": True,
        "boundary_audit_only": True,
    }


def spread_projection_candidate_to_voicing_candidate_adapter(
    candidate: SpreadProjectionCandidate | None,
    policy: Any | None = None,
    *,
    allow_conversion: bool | None = None,
    score: float | None = None,
    selector_reason: str = "explicit_spread_runtime_adapter_skeleton",
) -> SpreadRuntimeAdapterResult:
    """Adapt a SPREAD projection candidate into a runtime candidate only in an explicit dry-run.

    This is the v2_2_47 adapter skeleton.  It solves field mapping and metadata
    preservation but keeps runtime wiring closed.  Ordinary style generation must
    not call this path unless a later explicit runtime pilot wires it through a
    policy gate.
    """

    conversion_requested = _spread_runtime_adapter_conversion_requested(policy, allow_conversion)
    field_mappings = _spread_runtime_adapter_field_mappings()
    if candidate is None:
        return SpreadRuntimeAdapterResult(
            source_candidate=None,
            adapted_candidate=None,
            status=SpreadRuntimeAdapterStatus.INVALID_SOURCE_CANDIDATE,
            field_mappings=field_mappings,
            conversion_requested=conversion_requested,
            conversion_allowed=False,
            reason="source_candidate_missing",
        )
    if not bool(candidate.is_legal):
        return SpreadRuntimeAdapterResult(
            source_candidate=candidate,
            adapted_candidate=None,
            status=SpreadRuntimeAdapterStatus.INVALID_SOURCE_CANDIDATE,
            field_mappings=field_mappings,
            conversion_requested=conversion_requested,
            conversion_allowed=False,
            reason=f"source_candidate_illegal:{candidate.legality_reason}",
        )
    if not conversion_requested:
        return SpreadRuntimeAdapterResult(
            source_candidate=candidate,
            adapted_candidate=None,
            status=SpreadRuntimeAdapterStatus.DEFAULT_BLOCKED,
            field_mappings=field_mappings,
            conversion_requested=False,
            conversion_allowed=False,
            reason="adapter_conversion_not_explicitly_allowed",
        )

    try:
        from jammate_engine.core.voicing.selection.candidate import VoicingCandidate
        from jammate_engine.core.voicing.policy import (
            BassRelation,
            ContentFamily,
            Disposition,
            FunctionalGrouping,
            IntervalStructure,
            RootSupportPolicy,
        )
        from jammate_engine.core.voicing.taxonomy.projection_map import build_projection_map, group_indices_for_projection
        from jammate_engine.core.voicing.taxonomy.recipes import group_roles_for_grouping
    except Exception as exc:  # pragma: no cover - defensive import boundary
        return SpreadRuntimeAdapterResult(
            source_candidate=candidate,
            adapted_candidate=None,
            status=SpreadRuntimeAdapterStatus.POLICY_BLOCKED,
            field_mappings=field_mappings,
            conversion_requested=True,
            conversion_allowed=False,
            reason=f"runtime_import_boundary_failed:{exc}",
        )

    try:
        grouping = FunctionalGrouping(candidate.recipe_contract.grouping.value)
    except ValueError:
        return SpreadRuntimeAdapterResult(
            source_candidate=candidate,
            adapted_candidate=None,
            status=SpreadRuntimeAdapterStatus.UNSUPPORTED_GROUPING,
            field_mappings=field_mappings,
            conversion_requested=True,
            conversion_allowed=False,
            reason=f"unsupported_runtime_functional_grouping:{candidate.recipe_contract.grouping.value}",
        )

    content_family = _spread_runtime_content_family(candidate, policy, ContentFamily)
    root_support = _spread_runtime_root_support(candidate, policy, RootSupportPolicy)
    bass_relation = _spread_runtime_bass_relation(candidate, BassRelation)
    interval_structure = _spread_runtime_interval_structure(policy, IntervalStructure)
    group_roles = group_roles_for_grouping(grouping, candidate.degrees, content_family)
    projection_map = build_projection_map(list(candidate.notes), grouping, group_roles)
    abstract_group_indices = group_indices_for_projection(len(candidate.notes), grouping, group_roles)
    metadata = {
        **candidate.metadata,
        "spread_runtime_adapter_skeleton_version": SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION,
        "source_candidate_type": "SpreadProjectionCandidate",
        "target_candidate_type": "VoicingCandidate",
        "adapter_skeleton_only": True,
        "converted_from_spread_projection_candidate": True,
        "converted_now": True,
        "candidate_conversion_allowed": True,
        "candidate_generator_wiring_allowed": False,
        "style_runtime_wiring_enabled": False,
        "runtime_enabled": False,
        "no_expression_or_pedal": True,
        "does_not_change_default_style_runtime": True,
        "functional_grouping": grouping.value,
        "group_roles": [role.value for role in group_roles],
        "projection_map": projection_map,
        "abstract_group_indices": abstract_group_indices,
        "source_candidate_metadata_preserved": True,
        "source_candidate_notes_only": True,
        "selector_reason": selector_reason,
    }
    adapted = VoicingCandidate(
        notes=list(candidate.notes),
        degrees=list(candidate.degrees),
        score=float(score if score is not None else 0.0),
        content_family=content_family,
        root_support=root_support,
        bass_relation=bass_relation,
        disposition=Disposition.SPREAD,
        interval_structure=interval_structure,
        functional_grouping=grouping,
        recipe_id=candidate.recipe_contract.recipe_id,
        group_roles=group_roles,
        root_support_decision=_spread_runtime_root_support_decision(policy),
        disposition_guard={
            "spread_runtime_adapter_skeleton_version": SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION,
            "passed": bool(candidate.is_legal),
            "family": "spread",
            "reason": candidate.legality_reason,
            "candidate_generator_wiring_allowed": False,
        },
        register_guard={
            "spread_runtime_adapter_skeleton_version": SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION,
            "passed": bool(candidate.is_legal),
            "group_gap_guard": dict(candidate.metadata.get("group_gap_guard") or {}),
            "span_guard": dict(candidate.metadata.get("span_guard") or {}),
            "register_policy": dict(candidate.metadata.get("register_policy") or {}),
        },
        voice_leading_profile={
            "spread_runtime_adapter_skeleton_version": SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION,
            "source": "spread_groupwise_voice_leading_future_runtime_boundary",
            "runtime_scorer_wiring_enabled": False,
        },
        selector_decision={
            "spread_runtime_adapter_skeleton_version": SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION,
            "source": selector_reason,
            "candidate_conversion_allowed": True,
            "candidate_generator_wiring_allowed": False,
            "style_runtime_wiring_enabled": False,
            "runtime_enabled": False,
        },
        metadata=metadata,
    )
    return SpreadRuntimeAdapterResult(
        source_candidate=candidate,
        adapted_candidate=adapted,
        status=SpreadRuntimeAdapterStatus.ADAPTED_SKELETON_ONLY,
        field_mappings=field_mappings,
        conversion_requested=True,
        conversion_allowed=True,
        reason="explicit_adapter_skeleton_conversion_only_not_runtime_wiring",
    )


def run_ballad_spread_runtime_adapter_skeleton(
    chord_symbols: tuple[str, ...] | list[str],
    policy: Any | None,
    *,
    texture_state: Any | None = None,
    explicit_enable: bool | None = None,
    allow_conversion: bool | None = None,
) -> BalladSpreadRuntimeAdapterSkeletonResult:
    """Run the Ballad safe dry-run path and optionally adapt selected candidates.

    Even when ``allow_conversion`` is true, this remains a skeleton/debug path:
    no candidate-generator pool is changed and no style runtime uses the adapted
    candidates by default.
    """

    dry_run = run_ballad_spread_runtime_safe_dry_run(
        chord_symbols,
        policy,
        texture_state=texture_state,
        explicit_enable=explicit_enable,
    )
    requested = _spread_runtime_adapter_conversion_requested(policy, allow_conversion)
    adapters = tuple(
        spread_projection_candidate_to_voicing_candidate_adapter(
            candidate,
            policy,
            allow_conversion=requested,
            selector_reason="ballad_spread_runtime_adapter_skeleton_safe_dry_run",
        )
        for candidate in dry_run.selected_candidates
    )
    return BalladSpreadRuntimeAdapterSkeletonResult(
        dry_run_result=dry_run,
        adapter_results=adapters,
        conversion_requested=requested,
        conversion_allowed=bool(requested),
        runtime_enabled=False,
    )


@dataclass(frozen=True)
class BalladSpreadPilotSelectionWeightPlan:
    """Audit-only plan for SPREAD pilot selection weight and fallback safety.

    Candidate order is explicitly not considered a selection priority in the V2
    runtime; selector/scorer will recompute scores later.  This contract exists
    so future Ballad SPREAD runtime wiring cannot accidentally treat prepended
    pilot candidates as an unconditional override of the existing pool.
    """

    style_name: str
    audit_enabled: bool
    fallback_required: bool
    max_spread_candidate_share: float
    max_spread_score_margin: float
    candidate_order_is_selection_priority: bool = False
    source: str = "policy_metadata_or_explicit_arguments"
    runtime_enabled: bool = False

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "ballad_spread_pilot_selection_weight_fallback_audit_version": BALLAD_SPREAD_PILOT_SELECTION_WEIGHT_FALLBACK_AUDIT_VERSION,
            "layer": "core.voicing.disposition.spread",
            "purpose": "Ballad SPREAD Pilot Selection Weight + Fallback Audit",
            "style_name": self.style_name,
            "audit_enabled": bool(self.audit_enabled),
            "fallback_required": bool(self.fallback_required),
            "max_spread_candidate_share": float(self.max_spread_candidate_share),
            "max_spread_score_margin": float(self.max_spread_score_margin),
            "candidate_order_is_selection_priority": bool(self.candidate_order_is_selection_priority),
            "source": self.source,
            "runtime_enabled": bool(self.runtime_enabled),
            "audit_only": True,
            "does_not_change_default_style_runtime": True,
        }


@dataclass(frozen=True)
class BalladSpreadPilotSelectionWeightFallbackAuditResult:
    """Audit result for explicit Ballad SPREAD pilot pool weighting safety.

    It compares SPREAD pilot candidates with the retained fallback pool using the
    raw candidate scores available before the normal selector/scorer pass.  This
    is deliberately conservative and metadata-only; it does not alter candidate
    scores, selector temperature, or runtime selection.
    """

    chord_symbol: str
    plan: BalladSpreadPilotSelectionWeightPlan
    pool_result: BalladSpreadRuntimeCandidatePoolResult
    status: BalladSpreadPilotSelectionAuditStatus
    reason: str
    spread_raw_scores: tuple[float, ...]
    fallback_raw_scores: tuple[float, ...]
    spread_candidates_prepend_fallback: bool
    fallback_retained: bool
    dominance_risk: bool
    runtime_enabled: bool = False

    @property
    def spread_candidate_count(self) -> int:
        return len(self.spread_raw_scores)

    @property
    def fallback_candidate_count(self) -> int:
        return len(self.fallback_raw_scores)

    @property
    def merged_candidate_count(self) -> int:
        return self.pool_result.merged_candidate_count

    @property
    def spread_candidate_share(self) -> float:
        total = self.merged_candidate_count
        if total <= 0:
            return 0.0
        return float(self.spread_candidate_count) / float(total)

    @property
    def max_spread_raw_score(self) -> float | None:
        if not self.spread_raw_scores:
            return None
        return max(self.spread_raw_scores)

    @property
    def max_fallback_raw_score(self) -> float | None:
        if not self.fallback_raw_scores:
            return None
        return max(self.fallback_raw_scores)

    @property
    def score_margin_vs_fallback(self) -> float | None:
        if self.max_spread_raw_score is None or self.max_fallback_raw_score is None:
            return None
        return float(self.max_spread_raw_score) - float(self.max_fallback_raw_score)

    @property
    def fallback_protected(self) -> bool:
        return self.status == BalladSpreadPilotSelectionAuditStatus.FALLBACK_PROTECTED

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "ballad_spread_pilot_selection_weight_fallback_audit_version": BALLAD_SPREAD_PILOT_SELECTION_WEIGHT_FALLBACK_AUDIT_VERSION,
            "layer": "core.voicing.disposition.spread",
            "purpose": "Ballad SPREAD Pilot Selection Weight + Fallback Audit",
            "chord_symbol": self.chord_symbol,
            "plan": self.plan.to_debug_dict(),
            "pool_status": self.pool_result.status.value,
            "status": self.status.value,
            "reason": self.reason,
            "spread_candidate_count": self.spread_candidate_count,
            "fallback_candidate_count": self.fallback_candidate_count,
            "merged_candidate_count": self.merged_candidate_count,
            "spread_candidate_share": round(self.spread_candidate_share, 4),
            "max_spread_raw_score": round(self.max_spread_raw_score, 4) if self.max_spread_raw_score is not None else None,
            "max_fallback_raw_score": round(self.max_fallback_raw_score, 4) if self.max_fallback_raw_score is not None else None,
            "score_margin_vs_fallback": round(self.score_margin_vs_fallback, 4) if self.score_margin_vs_fallback is not None else None,
            "spread_raw_scores": [round(score, 4) for score in self.spread_raw_scores],
            "fallback_raw_scores_sample": [round(score, 4) for score in self.fallback_raw_scores[:8]],
            "spread_candidates_prepend_fallback": bool(self.spread_candidates_prepend_fallback),
            "candidate_order_is_selection_priority": bool(self.plan.candidate_order_is_selection_priority),
            "candidate_order_warning": bool(self.spread_candidates_prepend_fallback and not self.plan.candidate_order_is_selection_priority),
            "fallback_retained": bool(self.fallback_retained),
            "fallback_required": bool(self.plan.fallback_required),
            "dominance_risk": bool(self.dominance_risk),
            "fallback_protected": bool(self.fallback_protected),
            "candidate_selection_not_performed": True,
            "selector_scoring_still_authoritative": True,
            "audit_only": True,
            "style_runtime_default_enabled": False,
            "default_style_runtime_unchanged": True,
            "runtime_enabled": bool(self.runtime_enabled),
            "no_expression_or_pedal": True,
            "pool_result": self.pool_result.to_debug_dict(),
        }



@dataclass(frozen=True)
class BalladSpreadPilotRuntimeEnablementGuardPlan:
    """Explicit runtime guard for the first Ballad SPREAD listening isolation.

    The guard prevents earlier debug/pilot metadata from being interpreted as a
    real runtime retune.  A caller must explicitly ask for the guard and the
    first-listening isolation path, while the existing fallback pool remains
    required.
    """

    style_name: str
    runtime_guard_enabled: bool
    listening_isolation_enabled: bool
    candidate_pool_plan: BalladSpreadRuntimeCandidatePoolPlan
    selection_weight_plan: BalladSpreadPilotSelectionWeightPlan
    reason: str
    source: str = "policy_metadata_or_explicit_arguments"
    default_style_runtime_unchanged: bool = True
    no_expression_or_pedal: bool = True

    @property
    def guard_open(self) -> bool:
        return (
            self.style_name == "jazz_ballad"
            and self.runtime_guard_enabled
            and self.listening_isolation_enabled
            and self.candidate_pool_plan.integration_allowed
        )

    @property
    def status(self) -> BalladSpreadPilotRuntimeEnablementGuardStatus:
        if self.style_name != "jazz_ballad":
            return BalladSpreadPilotRuntimeEnablementGuardStatus.STYLE_BLOCKED
        if not self.runtime_guard_enabled:
            return BalladSpreadPilotRuntimeEnablementGuardStatus.DEFAULT_DISABLED
        if not self.listening_isolation_enabled:
            return BalladSpreadPilotRuntimeEnablementGuardStatus.LISTENING_ISOLATION_REQUIRED
        if not self.candidate_pool_plan.integration_allowed:
            return BalladSpreadPilotRuntimeEnablementGuardStatus.CANDIDATE_POOL_NOT_READY
        return BalladSpreadPilotRuntimeEnablementGuardStatus.ENABLED_FOR_LISTENING_ISOLATION

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "ballad_spread_pilot_runtime_enablement_guard_version": BALLAD_SPREAD_PILOT_RUNTIME_ENABLEMENT_GUARD_VERSION,
            "ballad_spread_1plus4_true_isolation_fix_version": BALLAD_SPREAD_1PLUS4_TRUE_ISOLATION_FIX_VERSION,
            "layer": "core.voicing.disposition.spread",
            "purpose": "Ballad SPREAD Pilot Runtime Enablement Guard + First Listening Isolation",
            "style_name": self.style_name,
            "runtime_guard_enabled": bool(self.runtime_guard_enabled),
            "listening_isolation_enabled": bool(self.listening_isolation_enabled),
            "candidate_pool_integration_allowed": bool(self.candidate_pool_plan.integration_allowed),
            "selection_weight_audit_required": bool(self.selection_weight_plan.audit_enabled),
            "fallback_required": bool(self.selection_weight_plan.fallback_required),
            "guard_open": bool(self.guard_open),
            "status": self.status.value,
            "reason": self.reason,
            "source": self.source,
            "candidate_pool_plan": self.candidate_pool_plan.to_debug_dict(),
            "selection_weight_plan": self.selection_weight_plan.to_debug_dict(),
            "style_runtime_default_enabled": False,
            "default_style_runtime_unchanged": bool(self.default_style_runtime_unchanged),
            "no_expression_or_pedal": bool(self.no_expression_or_pedal),
            "does_not_change_medium_swing_or_bossa": True,
        }


@dataclass(frozen=True)
class BalladSpreadPilotRuntimeEnablementGuardResult:
    """Guarded result for the first SPREAD listening-isolation runtime path."""

    chord_symbol: str
    plan: BalladSpreadPilotRuntimeEnablementGuardPlan
    pool_result: BalladSpreadRuntimeCandidatePoolResult
    selection_audit: BalladSpreadPilotSelectionWeightFallbackAuditResult | None
    guarded_candidates: tuple[Any, ...]
    status: BalladSpreadPilotRuntimeEnablementGuardStatus
    reason: str
    runtime_pilot_enabled: bool = False

    @property
    def enabled_for_listening_isolation(self) -> bool:
        return self.status == BalladSpreadPilotRuntimeEnablementGuardStatus.ENABLED_FOR_LISTENING_ISOLATION

    @property
    def spread_candidate_count(self) -> int:
        return self.pool_result.spread_candidate_count

    @property
    def fallback_candidate_count(self) -> int:
        return self.pool_result.base_candidate_count

    @property
    def guarded_candidate_count(self) -> int:
        return len(self.guarded_candidates)

    @property
    def fallback_retained(self) -> bool:
        if self.selection_audit is not None:
            return bool(self.selection_audit.fallback_retained)
        return _fallback_pool_retained(self.pool_result)

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "ballad_spread_pilot_runtime_enablement_guard_version": BALLAD_SPREAD_PILOT_RUNTIME_ENABLEMENT_GUARD_VERSION,
            "ballad_spread_1plus4_true_isolation_fix_version": BALLAD_SPREAD_1PLUS4_TRUE_ISOLATION_FIX_VERSION,
            "layer": "core.voicing.disposition.spread",
            "purpose": "Ballad SPREAD Pilot Runtime Enablement Guard + First Listening Isolation",
            "chord_symbol": self.chord_symbol,
            "plan": self.plan.to_debug_dict(),
            "status": self.status.value,
            "reason": self.reason,
            "enabled_for_listening_isolation": bool(self.enabled_for_listening_isolation),
            "runtime_pilot_enabled": bool(self.runtime_pilot_enabled),
            "style_runtime_default_enabled": False,
            "default_style_runtime_unchanged": True,
            "spread_candidate_count": self.spread_candidate_count,
            "fallback_candidate_count": self.fallback_candidate_count,
            "guarded_candidate_count": self.guarded_candidate_count,
            "fallback_retained": bool(self.fallback_retained),
            "pool_result": self.pool_result.to_debug_dict(),
            "selection_audit": self.selection_audit.to_debug_dict() if self.selection_audit is not None else None,
            "candidate_generator_wiring_allowed": bool(self.enabled_for_listening_isolation),
            "first_listening_isolation_only": True,
            "no_expression_or_pedal": True,
            "does_not_change_medium_swing_or_bossa": True,
        }


def ballad_spread_pilot_runtime_enablement_guard_plan(
    policy: Any | None = None,
    *,
    style_name: str | None = None,
    runtime_guard_enabled: bool | None = None,
    listening_isolation_enabled: bool | None = None,
) -> BalladSpreadPilotRuntimeEnablementGuardPlan:
    """Resolve the v2_2_50 explicit runtime enablement guard.

    This sits above the candidate-pool builder.  It reuses the existing v2_2_48
    and v2_2_49 plans instead of adding a parallel selector or voicing system.
    """

    values = _ballad_spread_runtime_enablement_guard_values(policy)
    resolved_style = _normalize_style_name(style_name or values.get("style_name") or values.get("style")) or ""
    guard_enabled = bool(runtime_guard_enabled) if runtime_guard_enabled is not None else _spread_bool_any(
        values,
        (
            "runtime_guard_enabled",
            "pilot_runtime_enablement_guard_enabled",
            "ballad_spread_runtime_enablement_guard_enabled",
            "enable_ballad_spread_first_listening_isolation",
        ),
        default=False,
    )
    isolation_enabled = bool(listening_isolation_enabled) if listening_isolation_enabled is not None else _spread_bool_any(
        values,
        (
            "listening_isolation_enabled",
            "first_listening_isolation_enabled",
            "runtime_listening_isolation_enabled",
            "ballad_spread_first_listening_isolation_enabled",
        ),
        default=False,
    )
    pool_plan = ballad_spread_runtime_candidate_pool_plan(policy, style_name=resolved_style or None)
    selection_plan = ballad_spread_pilot_selection_weight_plan(policy, style_name=resolved_style or None)

    if resolved_style != "jazz_ballad":
        reason = "style_not_allowed_for_ballad_spread_runtime_enablement_guard"
    elif not guard_enabled:
        reason = "ballad_spread_runtime_enablement_guard_not_enabled"
    elif not isolation_enabled:
        reason = "ballad_spread_first_listening_isolation_not_enabled"
    elif not pool_plan.integration_allowed:
        reason = f"candidate_pool_not_ready:{pool_plan.status.value}"
    else:
        reason = "ballad_spread_runtime_enablement_guard_open_for_first_listening_isolation"

    return BalladSpreadPilotRuntimeEnablementGuardPlan(
        style_name=resolved_style,
        runtime_guard_enabled=guard_enabled,
        listening_isolation_enabled=isolation_enabled,
        candidate_pool_plan=pool_plan,
        selection_weight_plan=selection_plan,
        reason=reason,
        source="explicit_argument" if any(item is not None for item in (style_name, runtime_guard_enabled, listening_isolation_enabled)) else "policy_metadata",
    )


def guard_ballad_spread_pilot_runtime_enablement(
    chord_symbol: str,
    policy: Any | None,
    *,
    base_candidates: tuple[Any, ...] | list[Any] | None = None,
    runtime_guard_enabled: bool | None = None,
    listening_isolation_enabled: bool | None = None,
) -> BalladSpreadPilotRuntimeEnablementGuardResult:
    """Return a guarded candidate pool for the first Ballad SPREAD isolation listen.

    The returned ``guarded_candidates`` is the only object candidate generation
    should consume.  When blocked, it is exactly the incoming fallback pool.
    """

    base = tuple(base_candidates or ())
    plan = ballad_spread_pilot_runtime_enablement_guard_plan(
        policy,
        runtime_guard_enabled=runtime_guard_enabled,
        listening_isolation_enabled=listening_isolation_enabled,
    )
    pool = build_ballad_spread_runtime_pilot_candidate_pool(
        chord_symbol,
        policy,
        base_candidates=base,
    )

    if plan.status != BalladSpreadPilotRuntimeEnablementGuardStatus.ENABLED_FOR_LISTENING_ISOLATION:
        return BalladSpreadPilotRuntimeEnablementGuardResult(
            chord_symbol=str(chord_symbol),
            plan=plan,
            pool_result=pool,
            selection_audit=None,
            guarded_candidates=base,
            status=plan.status,
            reason=plan.reason,
            runtime_pilot_enabled=False,
        )

    if not pool.candidate_pool_integrated:
        return BalladSpreadPilotRuntimeEnablementGuardResult(
            chord_symbol=str(chord_symbol),
            plan=plan,
            pool_result=pool,
            selection_audit=None,
            guarded_candidates=base,
            status=BalladSpreadPilotRuntimeEnablementGuardStatus.CANDIDATE_POOL_NOT_READY,
            reason=f"candidate_pool_not_integrated:{pool.status.value}",
            runtime_pilot_enabled=False,
        )

    audit = audit_ballad_spread_pilot_selection_weight_and_fallback(
        chord_symbol,
        policy,
        base_candidates=base,
    )
    if not audit.fallback_protected:
        return BalladSpreadPilotRuntimeEnablementGuardResult(
            chord_symbol=str(chord_symbol),
            plan=plan,
            pool_result=pool,
            selection_audit=audit,
            guarded_candidates=base,
            status=BalladSpreadPilotRuntimeEnablementGuardStatus.FALLBACK_AUDIT_BLOCKED,
            reason=f"selection_weight_fallback_audit_blocked:{audit.status.value}",
            runtime_pilot_enabled=False,
        )

    strict_isolation = _ballad_spread_true_isolation_contract(policy)
    spread_source = tuple(pool.spread_candidates)
    if strict_isolation["enabled"]:
        required_recipe_id = str(strict_isolation["required_recipe_id"] or "").strip()
        if required_recipe_id:
            spread_source = tuple(
                candidate for candidate in spread_source
                if _spread_candidate_recipe_id(candidate) == required_recipe_id
            )

    guarded_spread = tuple(
        _annotate_ballad_spread_runtime_enablement_guard_candidate(
            item,
            true_isolation=strict_isolation,
        )
        for item in spread_source
    )
    candidate_pool_values = _ballad_spread_candidate_pool_values(policy)
    compatible_pool_values = candidate_pool_values.get("spread_grouping_mix_candidate_pool") or candidate_pool_values.get("ballad_spread_grouping_mix_candidate_pool") or {}
    if not isinstance(compatible_pool_values, dict):
        compatible_pool_values = {}
    compatible_spread_only = _spread_bool_any(
        {**candidate_pool_values, **compatible_pool_values},
        (
            "use_compatible_contracts",
            "spread_grouping_mix_candidate_pool_uses_compatible_contracts",
            "ballad_spread_grouping_mix_candidate_pool_uses_compatible_contracts",
        ),
        default=False,
    )
    if compatible_spread_only and guarded_spread:
        guarded = guarded_spread
        reason = "ballad_spread_grouping_mix_compatible_texture_contracts_spread_only_candidate_pool"
    elif strict_isolation["enabled"] and guarded_spread:
        guarded = guarded_spread
        reason = "ballad_spread_1plus4_true_isolation_enabled_spread_only_candidate_pool"
    elif strict_isolation["enabled"] and not guarded_spread and strict_isolation["fallback_only_when_missing"]:
        guarded = pool.base_candidates
        reason = "ballad_spread_1plus4_true_isolation_fallback_used_no_matching_spread_candidate"
    else:
        guarded = (*guarded_spread, *pool.base_candidates)
        reason = "ballad_spread_pilot_enabled_for_first_listening_isolation_with_fallback_protected"

    return BalladSpreadPilotRuntimeEnablementGuardResult(
        chord_symbol=str(chord_symbol),
        plan=plan,
        pool_result=pool,
        selection_audit=audit,
        guarded_candidates=guarded,
        status=BalladSpreadPilotRuntimeEnablementGuardStatus.ENABLED_FOR_LISTENING_ISOLATION,
        reason=reason,
        runtime_pilot_enabled=True,
    )


def ballad_spread_pilot_runtime_enablement_guard_debug(
    chord_symbol: str = "Dm7",
    policy: Any | None = None,
    *,
    base_candidates: tuple[Any, ...] | list[Any] | None = None,
) -> dict[str, object]:
    result = guard_ballad_spread_pilot_runtime_enablement(
        chord_symbol,
        policy,
        base_candidates=base_candidates,
    )
    return {
        "ballad_spread_pilot_runtime_enablement_guard_version": BALLAD_SPREAD_PILOT_RUNTIME_ENABLEMENT_GUARD_VERSION,
        "result": result.to_debug_dict(),
        "enabled_for_listening_isolation": result.enabled_for_listening_isolation,
        "runtime_pilot_enabled": result.runtime_pilot_enabled,
        "fallback_retained": result.fallback_retained,
        "first_listening_isolation_only": True,
        "default_style_runtime_unchanged": True,
        "does_not_change_medium_swing_or_bossa": True,
    }


def ballad_spread_runtime_candidate_pool_plan(
    policy: Any | None = None,
    *,
    style_name: str | None = None,
    enabled: bool | None = None,
    allow_conversion: bool | None = None,
    allow_pool_merge: bool | None = None,
) -> BalladSpreadRuntimeCandidatePoolPlan:
    """Resolve the explicit v2_2_48 Ballad SPREAD pilot pool plan.

    Enabling the pilot requires three explicit yeses: the pool itself, adapter
    conversion, and candidate-pool merge.  This prevents a style's broad SPREAD
    preference from silently becoming runtime SPREAD candidate injection.
    """

    values = _ballad_spread_candidate_pool_values(policy)
    resolved_style = _normalize_style_name(style_name or values.get("style_name") or values.get("style")) or ""
    pool_enabled = bool(enabled) if enabled is not None else _spread_bool_any(
        values,
        (
            "candidate_pool_enabled",
            "pilot_candidate_pool_enabled",
            "ballad_spread_runtime_candidate_pool_enabled",
            "enable_ballad_spread_runtime_candidate_pool",
        ),
        default=False,
    )
    conversion_allowed = bool(allow_conversion) if allow_conversion is not None else _spread_bool_any(
        values,
        (
            "adapter_conversion_allowed",
            "candidate_conversion_allowed",
            "spread_runtime_adapter_conversion_allowed",
            "allow_spread_runtime_adapter_conversion",
        ),
        default=False,
    )
    merge_allowed = bool(allow_pool_merge) if allow_pool_merge is not None else _spread_bool_any(
        values,
        (
            "candidate_pool_merge_allowed",
            "candidate_generator_wiring_allowed",
            "pilot_candidate_pool_merge_allowed",
            "merge_spread_candidates_into_runtime_pool",
        ),
        default=False,
    )

    if resolved_style != "jazz_ballad":
        reason = "style_not_allowed_for_ballad_spread_candidate_pool"
    elif not pool_enabled:
        reason = "ballad_spread_runtime_candidate_pool_not_enabled"
    elif not conversion_allowed:
        reason = "spread_runtime_adapter_conversion_not_allowed_for_candidate_pool"
    elif not merge_allowed:
        reason = "candidate_pool_merge_not_allowed"
    else:
        reason = "ballad_spread_candidate_pool_integration_allowed_with_existing_pool_fallback"

    return BalladSpreadRuntimeCandidatePoolPlan(
        style_name=resolved_style,
        candidate_pool_enabled=pool_enabled,
        adapter_conversion_allowed=conversion_allowed,
        candidate_pool_merge_allowed=merge_allowed,
        reason=reason,
        source="explicit_argument" if any(item is not None for item in (style_name, enabled, allow_conversion, allow_pool_merge)) else "policy_metadata",
    )


def build_ballad_spread_runtime_pilot_candidate_pool(
    chord_symbol: str,
    policy: Any | None,
    *,
    base_candidates: tuple[Any, ...] | list[Any] | None = None,
    texture_state: Any | None = None,
    enabled: bool | None = None,
    allow_conversion: bool | None = None,
    allow_pool_merge: bool | None = None,
) -> BalladSpreadRuntimeCandidatePoolResult:
    """Build an explicit Ballad SPREAD pilot candidate pool for one chord.

    The returned pool is safe-by-default: blocked plans return the original base
    pool unchanged; integrated plans prepend annotated SPREAD pilot candidates
    while retaining the existing non-SPREAD pool as fallback.
    """

    base = tuple(base_candidates or ())
    plan = ballad_spread_runtime_candidate_pool_plan(
        policy,
        enabled=enabled,
        allow_conversion=allow_conversion,
        allow_pool_merge=allow_pool_merge,
    )
    if not plan.integration_allowed:
        return BalladSpreadRuntimeCandidatePoolResult(
            chord_symbol=str(chord_symbol),
            plan=plan,
            base_candidates=base,
            adapter_result=None,
            spread_candidates=(),
            merged_candidates=base,
            status=plan.status,
            reason=plan.reason,
        )

    resolved_texture_state = texture_state or _default_spread_texture_state_for_candidate_pool()
    values = _ballad_spread_candidate_pool_values(policy)
    emit_all_candidates = _spread_bool_any(
        values,
        (
            "spread_runtime_adapter_emit_all_candidates",
            "spread_groupwise_voice_leading_runtime_enabled",
            "spread_emit_all_candidates_for_groupwise_selection",
        ),
        default=False,
    )
    adapter_result = None
    if emit_all_candidates:
        strict_isolation = _ballad_spread_true_isolation_contract(policy)
        contract_ids: tuple[str, ...] | None = None
        compatible_pool_values = values.get("spread_grouping_mix_candidate_pool") or values.get("ballad_spread_grouping_mix_candidate_pool") or {}
        if not isinstance(compatible_pool_values, dict):
            compatible_pool_values = {}
        use_compatible_pool = _spread_bool_any(
            {**values, **compatible_pool_values},
            (
                "use_compatible_contracts",
                "spread_grouping_mix_candidate_pool_uses_compatible_contracts",
                "ballad_spread_grouping_mix_candidate_pool_uses_compatible_contracts",
            ),
            default=False,
        )
        compatible_ids_raw = (
            compatible_pool_values.get("compatible_contract_ids")
            or values.get("spread_grouping_mix_candidate_contract_ids")
            or values.get("compatible_contract_ids")
            or ()
        )
        if isinstance(compatible_ids_raw, str):
            compatible_ids_raw = (compatible_ids_raw,)
        compatible_ids = tuple(str(item) for item in compatible_ids_raw if str(item).strip())
        if use_compatible_pool and compatible_ids:
            contract_ids = compatible_ids
        else:
            required_recipe_id = str(strict_isolation.get("required_recipe_id") or "").strip() if strict_isolation.get("enabled") else ""
            if required_recipe_id:
                contract_ids = (required_recipe_id,)
        max_upper_options = int(values.get("spread_runtime_adapter_max_upper_options", values.get("max_upper_options", 12)) or 12)
        projected = project_basic_spread_candidates(
            str(chord_symbol),
            policy,
            contract_ids=contract_ids,
            max_upper_options=max_upper_options,
        )
        projection_candidates = tuple(
            candidate
            for result in projected
            for candidate in result.candidates
            if candidate.is_legal
        )
        spread_candidates = tuple(
            _annotate_ballad_spread_pool_candidate(item.adapted_candidate)
            for item in (
                spread_projection_candidate_to_voicing_candidate_adapter(
                    candidate,
                    policy,
                    allow_conversion=True,
                    selector_reason="ballad_spread_runtime_adapter_all_candidates_for_groupwise_selection",
                )
                for candidate in projection_candidates
            )
            if item.converted and item.adapted_candidate is not None
        )
    else:
        adapter_result = run_ballad_spread_runtime_adapter_skeleton(
            [str(chord_symbol)],
            policy,
            texture_state=resolved_texture_state,
            explicit_enable=True,
            allow_conversion=True,
        )
        spread_candidates = tuple(
            _annotate_ballad_spread_pool_candidate(item.adapted_candidate)
            for item in adapter_result.adapter_results
            if item.converted and item.adapted_candidate is not None
        )
    if not spread_candidates:
        return BalladSpreadRuntimeCandidatePoolResult(
            chord_symbol=str(chord_symbol),
            plan=plan,
            base_candidates=base,
            adapter_result=adapter_result,
            spread_candidates=(),
            merged_candidates=base,
            status=BalladSpreadRuntimeCandidatePoolStatus.PILOT_NO_SPREAD_CANDIDATES,
            reason="spread_adapter_skeleton_returned_no_convertible_candidates_existing_pool_retained",
        )

    merged = (*spread_candidates, *base)
    return BalladSpreadRuntimeCandidatePoolResult(
        chord_symbol=str(chord_symbol),
        plan=plan,
        base_candidates=base,
        adapter_result=adapter_result,
        spread_candidates=spread_candidates,
        merged_candidates=merged,
        status=BalladSpreadRuntimeCandidatePoolStatus.PILOT_CANDIDATES_INTEGRATED,
        reason="explicit_ballad_spread_pilot_candidates_added_existing_pool_retained",
    )


def ballad_spread_runtime_candidate_pool_debug(
    chord_symbol: str = "Dm7",
    policy: Any | None = None,
    *,
    base_candidates: tuple[Any, ...] | list[Any] | None = None,
    enabled: bool | None = None,
    allow_conversion: bool | None = None,
    allow_pool_merge: bool | None = None,
) -> dict[str, object]:
    result = build_ballad_spread_runtime_pilot_candidate_pool(
        chord_symbol,
        policy,
        base_candidates=base_candidates,
        enabled=enabled,
        allow_conversion=allow_conversion,
        allow_pool_merge=allow_pool_merge,
    )
    return {
        "ballad_spread_runtime_candidate_pool_integration_version": BALLAD_SPREAD_RUNTIME_CANDIDATE_POOL_INTEGRATION_VERSION,
        "result": result.to_debug_dict(),
        "candidate_pool_integrated": result.candidate_pool_integrated,
        "fallback_to_existing_pool": True,
        "default_style_runtime_unchanged": True,
        "style_runtime_default_enabled": False,
        "no_expression_or_pedal": True,
    }


def ballad_spread_pilot_selection_weight_plan(
    policy: Any | None = None,
    *,
    style_name: str | None = None,
    audit_enabled: bool | None = None,
    max_spread_candidate_share: float | None = None,
    max_spread_score_margin: float | None = None,
    fallback_required: bool | None = None,
) -> BalladSpreadPilotSelectionWeightPlan:
    """Resolve the v2_2_49 Ballad SPREAD pilot selection/fallback audit plan."""

    values = _ballad_spread_selection_audit_values(policy)
    resolved_style = _normalize_style_name(style_name or values.get("style_name") or values.get("style")) or ""
    enabled = bool(audit_enabled) if audit_enabled is not None else _spread_bool_any(
        values,
        (
            "audit_enabled",
            "selection_weight_audit_enabled",
            "fallback_audit_enabled",
            "ballad_spread_pilot_selection_weight_audit_enabled",
        ),
        default=True,
    )
    required = bool(fallback_required) if fallback_required is not None else _spread_bool_any(
        values,
        ("fallback_required", "fallback_to_existing_pool", "require_fallback_pool"),
        default=True,
    )
    share = _spread_float_value(values, "max_spread_candidate_share", default=0.35)
    if max_spread_candidate_share is not None:
        share = float(max_spread_candidate_share)
    margin = _spread_float_value(values, "max_spread_score_margin", default=0.15)
    if max_spread_score_margin is not None:
        margin = float(max_spread_score_margin)
    order_priority = _spread_bool_any(
        values,
        ("candidate_order_is_selection_priority", "order_is_selection_priority"),
        default=False,
    )
    return BalladSpreadPilotSelectionWeightPlan(
        style_name=resolved_style,
        audit_enabled=enabled,
        fallback_required=required,
        max_spread_candidate_share=max(0.0, min(1.0, share)),
        max_spread_score_margin=max(0.0, margin),
        candidate_order_is_selection_priority=order_priority,
        source="explicit_argument" if any(item is not None for item in (style_name, audit_enabled, max_spread_candidate_share, max_spread_score_margin, fallback_required)) else "policy_metadata",
    )


def audit_ballad_spread_pilot_selection_weight_and_fallback(
    chord_symbol: str,
    policy: Any | None,
    *,
    base_candidates: tuple[Any, ...] | list[Any] | None = None,
    enabled: bool | None = None,
    allow_conversion: bool | None = None,
    allow_pool_merge: bool | None = None,
    max_spread_candidate_share: float | None = None,
    max_spread_score_margin: float | None = None,
) -> BalladSpreadPilotSelectionWeightFallbackAuditResult:
    """Audit explicit Ballad SPREAD pilot pool weights and fallback safety.

    The audit reuses the v2_2_48 candidate-pool builder and does not run the
    selector.  It only checks whether a future runtime pilot would keep a safe
    fallback pool and whether SPREAD pilot candidates appear to dominate by raw
    score or share before normal selector scoring.
    """

    plan = ballad_spread_pilot_selection_weight_plan(
        policy,
        max_spread_candidate_share=max_spread_candidate_share,
        max_spread_score_margin=max_spread_score_margin,
    )
    base = tuple(base_candidates or ())
    pool = build_ballad_spread_runtime_pilot_candidate_pool(
        chord_symbol,
        policy,
        base_candidates=base,
        enabled=enabled,
        allow_conversion=allow_conversion,
        allow_pool_merge=allow_pool_merge,
    )
    spread_scores = tuple(_candidate_raw_score(candidate) for candidate in pool.spread_candidates)
    fallback_scores = tuple(_candidate_raw_score(candidate) for candidate in pool.base_candidates)
    spread_prefix = bool(
        pool.spread_candidate_count
        and tuple(pool.merged_candidates[: pool.spread_candidate_count]) == tuple(pool.spread_candidates)
    )
    fallback_retained = _fallback_pool_retained(pool)

    if plan.style_name != "jazz_ballad":
        status = BalladSpreadPilotSelectionAuditStatus.STYLE_BLOCKED
        reason = "style_not_allowed_for_ballad_spread_selection_audit"
    elif not pool.candidate_pool_integrated:
        status = (
            BalladSpreadPilotSelectionAuditStatus.DEFAULT_DISABLED
            if pool.status == BalladSpreadRuntimeCandidatePoolStatus.DEFAULT_DISABLED
            else BalladSpreadPilotSelectionAuditStatus.POOL_NOT_INTEGRATED
        )
        reason = f"candidate_pool_not_integrated:{pool.status.value}"
    elif plan.fallback_required and not fallback_retained:
        status = BalladSpreadPilotSelectionAuditStatus.FALLBACK_MISSING
        reason = "fallback_pool_not_retained_after_spread_pilot_merge"
    else:
        spread_share = (float(len(spread_scores)) / float(max(1, pool.merged_candidate_count)))
        score_margin = None
        if spread_scores and fallback_scores:
            score_margin = max(spread_scores) - max(fallback_scores)
        dominance_risk = bool(
            spread_share > plan.max_spread_candidate_share
            or (score_margin is not None and score_margin > plan.max_spread_score_margin)
            or (spread_prefix and plan.candidate_order_is_selection_priority)
        )
        if dominance_risk:
            status = BalladSpreadPilotSelectionAuditStatus.SPREAD_DOMINANCE_RISK
            reason = "spread_pilot_candidates_exceed_share_or_score_boundary"
        else:
            status = BalladSpreadPilotSelectionAuditStatus.FALLBACK_PROTECTED
            reason = "fallback_pool_retained_and_spread_pilot_weight_within_audit_bounds"

    dominance = status == BalladSpreadPilotSelectionAuditStatus.SPREAD_DOMINANCE_RISK
    return BalladSpreadPilotSelectionWeightFallbackAuditResult(
        chord_symbol=str(chord_symbol),
        plan=plan,
        pool_result=pool,
        status=status,
        reason=reason,
        spread_raw_scores=spread_scores,
        fallback_raw_scores=fallback_scores,
        spread_candidates_prepend_fallback=spread_prefix,
        fallback_retained=fallback_retained,
        dominance_risk=dominance,
        runtime_enabled=False,
    )


def ballad_spread_pilot_selection_weight_fallback_audit_debug(
    chord_symbol: str = "Dm7",
    policy: Any | None = None,
    *,
    base_candidates: tuple[Any, ...] | list[Any] | None = None,
    enabled: bool | None = None,
    allow_conversion: bool | None = None,
    allow_pool_merge: bool | None = None,
) -> dict[str, object]:
    """Debug payload for the v2_2_49 selection-weight/fallback audit."""

    result = audit_ballad_spread_pilot_selection_weight_and_fallback(
        chord_symbol,
        policy,
        base_candidates=base_candidates,
        enabled=enabled,
        allow_conversion=allow_conversion,
        allow_pool_merge=allow_pool_merge,
    )
    return {
        "ballad_spread_pilot_selection_weight_fallback_audit_version": BALLAD_SPREAD_PILOT_SELECTION_WEIGHT_FALLBACK_AUDIT_VERSION,
        "result": result.to_debug_dict(),
        "fallback_protected": result.fallback_protected,
        "dominance_risk": result.dominance_risk,
        "candidate_selection_not_performed": True,
        "selector_scoring_still_authoritative": True,
        "style_runtime_default_enabled": False,
        "default_style_runtime_unchanged": True,
        "no_expression_or_pedal": True,
    }



def spread_runtime_adapter_skeleton_debug(
    chord_symbol: str = "Dm7",
    policy: Any | None = None,
    *,
    allow_conversion: bool | None = None,
) -> dict[str, object]:
    """Return a compact v2_2_47 adapter skeleton debug payload."""

    result = project_basic_spread_candidates(chord_symbol, contract_ids=("spread_1plus4_contract",), max_upper_options=1)[0]
    candidate = result.candidates[0] if result.candidates else None
    adapter = spread_projection_candidate_to_voicing_candidate_adapter(
        candidate,
        policy,
        allow_conversion=allow_conversion,
    )
    return {
        "spread_runtime_adapter_skeleton_version": SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION,
        "default_conversion_allowed": False,
        "candidate_generator_wiring_allowed": False,
        "style_runtime_wiring_enabled": False,
        "runtime_enabled": False,
        "adapter": adapter.to_debug_dict(),
        "adapter_skeleton_only": True,
        "no_expression_or_pedal": True,
    }


def ballad_spread_runtime_adapter_skeleton_debug(
    chord_symbols: tuple[str, ...] | list[str] = ("Dm7", "G7", "Cmaj7"),
    policy: Any | None = None,
    *,
    texture_state: Any | None = None,
    explicit_enable: bool | None = None,
    allow_conversion: bool | None = None,
) -> dict[str, object]:
    result = run_ballad_spread_runtime_adapter_skeleton(
        chord_symbols,
        policy,
        texture_state=texture_state,
        explicit_enable=explicit_enable,
        allow_conversion=allow_conversion,
    )
    return {
        "spread_runtime_adapter_skeleton_version": SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION,
        "result": result.to_debug_dict(),
        "candidate_generator_wiring_allowed": False,
        "style_runtime_wiring_enabled": False,
        "runtime_enabled": False,
        "adapter_skeleton_only": True,
        "no_expression_or_pedal": True,
    }


def _spread_runtime_adapter_field_mappings() -> tuple[SpreadRuntimeAdapterFieldMapping, ...]:
    return (
        SpreadRuntimeAdapterFieldMapping("candidate.notes", "VoicingCandidate.notes", True, "MIDI notes are copied verbatim from the legal SPREAD projection candidate"),
        SpreadRuntimeAdapterFieldMapping("candidate.degrees", "VoicingCandidate.degrees", True, "degree labels are copied verbatim so lower/upper metadata remains auditable"),
        SpreadRuntimeAdapterFieldMapping("candidate.recipe_contract.grouping", "VoicingCandidate.functional_grouping", True, "grouping is coerced through core FunctionalGrouping, including 1+4"),
        SpreadRuntimeAdapterFieldMapping("candidate.recipe_contract.grouping", "VoicingCandidate.group_roles", True, "group roles are derived through core recipes.group_roles_for_grouping rather than hand semantics"),
        SpreadRuntimeAdapterFieldMapping("candidate.upper_source.source_family", "VoicingCandidate.content_family", True, "content family is reused from the upper source adapter when it matches core ContentFamily"),
        SpreadRuntimeAdapterFieldMapping("candidate.metadata", "VoicingCandidate.metadata", True, "SPREAD projection metadata is preserved and marked adapter_skeleton_only"),
        SpreadRuntimeAdapterFieldMapping("candidate.runtime_enabled", "candidate_generator runtime pool", False, "candidate-generator wiring remains disabled in v2_2_47"),
    )


def _ballad_spread_candidate_pool_values(policy: Any | None) -> dict[str, object]:
    try:
        metadata = dict(getattr(policy, "metadata", None) or {})
    except Exception:
        metadata = dict(policy or {}) if isinstance(policy, dict) else {}
    nested = (
        metadata.get("ballad_spread_runtime_candidate_pool")
        or metadata.get("ballad_spread_candidate_pool")
        or metadata.get("spread_runtime_candidate_pool")
        or {}
    )
    if not isinstance(nested, dict):
        nested = {"candidate_pool_enabled": nested}
    return {**metadata, **nested}


def _default_spread_texture_state_for_candidate_pool() -> Any:
    from jammate_engine.core.voicing.runtime.texture_plan import VoicingTextureState
    from jammate_engine.core.voicing.disposition.models import DispositionFamily

    return VoicingTextureState(
        primary_family=DispositionFamily.SPREAD,
        allowed_families=(DispositionFamily.SPREAD,),
    )


def _annotate_ballad_spread_pool_candidate(candidate: Any) -> Any:
    metadata = {
        **dict(getattr(candidate, "metadata", {}) or {}),
        "ballad_spread_runtime_candidate_pool_integration_version": BALLAD_SPREAD_RUNTIME_CANDIDATE_POOL_INTEGRATION_VERSION,
        "ballad_spread_pilot_selection_weight_fallback_audit_version": BALLAD_SPREAD_PILOT_SELECTION_WEIGHT_FALLBACK_AUDIT_VERSION,
        "ballad_spread_runtime_pilot_pool_candidate": True,
        "candidate_pool_source": "ballad_spread_runtime_pilot",
        "candidate_pool_integration_status": BalladSpreadRuntimeCandidatePoolStatus.PILOT_CANDIDATES_INTEGRATED.value,
        "fallback_non_spread_pool_retained": True,
        "candidate_generator_wiring_allowed": True,
        "pilot_candidate_pool_integration_allowed": True,
        "selection_weight_fallback_audit_required": True,
        "candidate_order_is_selection_priority": False,
        "spread_pilot_weight_role": "secondary_pilot_candidate_not_default_replacement",
        "style_runtime_default_enabled": False,
        "default_style_runtime_unchanged": True,
        "no_expression_or_pedal": True,
    }
    selector_decision = {
        **dict(getattr(candidate, "selector_decision", {}) or {}),
        "ballad_spread_runtime_candidate_pool_integration_version": BALLAD_SPREAD_RUNTIME_CANDIDATE_POOL_INTEGRATION_VERSION,
        "ballad_spread_pilot_selection_weight_fallback_audit_version": BALLAD_SPREAD_PILOT_SELECTION_WEIGHT_FALLBACK_AUDIT_VERSION,
        "candidate_pool_source": "ballad_spread_runtime_pilot",
        "fallback_non_spread_pool_retained": True,
        "candidate_order_is_selection_priority": False,
    }
    try:
        return replace(candidate, metadata=metadata, selector_decision=selector_decision)
    except Exception:
        return candidate



def _ballad_spread_runtime_enablement_guard_values(policy: Any | None) -> dict[str, object]:
    try:
        metadata = dict(getattr(policy, "metadata", None) or {})
    except Exception:
        metadata = dict(policy or {}) if isinstance(policy, dict) else {}
    nested = (
        metadata.get("ballad_spread_pilot_runtime_enablement_guard")
        or metadata.get("ballad_spread_runtime_enablement_guard")
        or metadata.get("ballad_spread_first_listening_isolation")
        or {}
    )
    if not isinstance(nested, dict):
        nested = {"runtime_guard_enabled": nested}
    return {**metadata, **nested}


def _ballad_spread_true_isolation_contract(policy: Any | None) -> dict[str, object]:
    """Resolve strict listening-isolation filtering for v2_2_52.

    This is deliberately narrower than the v2_2_50 first-listening guard.  It is
    only for debugging/listening demos that must hear a specific SPREAD contract
    without the normal fallback pool being allowed to win the selector.
    Fallback candidates remain available only when the requested SPREAD contract
    cannot be built at all.
    """

    values = _ballad_spread_true_isolation_values(policy)
    enabled = _spread_bool_any(
        values,
        (
            "enabled",
            "true_isolation_enabled",
            "strict_contract_isolation_enabled",
            "ballad_spread_1plus4_true_isolation_enabled",
        ),
        default=False,
    )
    required = str(
        values.get("required_recipe_id")
        or values.get("recipe_id")
        or values.get("required_contract_id")
        or values.get("contract_id")
        or "spread_1plus4_contract"
    )
    fallback_only = _spread_bool_any(
        values,
        ("fallback_only_when_missing", "fallback_to_existing_pool_when_missing", "fallback_if_no_matching_candidate"),
        default=True,
    )
    return {
        "version": BALLAD_SPREAD_1PLUS4_TRUE_ISOLATION_FIX_VERSION,
        "enabled": bool(enabled),
        "required_recipe_id": required,
        "fallback_only_when_missing": bool(fallback_only),
        "candidate_pool_mode": "spread_only_when_available" if enabled else "spread_plus_fallback",
        "grouping_mix_decision": values.get("grouping_mix_decision")
        or values.get("ballad_spread_grouping_mix_policy_decision"),
    }


def _ballad_spread_true_isolation_values(policy: Any | None) -> dict[str, object]:
    try:
        metadata = dict(getattr(policy, "metadata", None) or {})
    except Exception:
        metadata = dict(policy or {}) if isinstance(policy, dict) else {}
    # Prefer the generic contract-isolation key so later SPREAD grouping pilots
    # can request a specific recipe without being shadowed by the older
    # 1+4-only metadata block left on the style policy for compatibility.
    nested = (
        metadata.get("spread_contract_true_isolation")
        or metadata.get("ballad_spread_true_isolation")
        or metadata.get("ballad_spread_1plus4_true_isolation")
        or {}
    )
    if not isinstance(nested, dict):
        nested = {"enabled": nested}
    return {**metadata, **nested}


def _spread_candidate_recipe_id(candidate: Any) -> str:
    recipe_id = getattr(candidate, "recipe_id", None)
    if recipe_id:
        return str(recipe_id)
    metadata = dict(getattr(candidate, "metadata", {}) or {})
    for key in ("recipe_id", "spread_recipe_id", "spread_contract_id", "source_recipe_id"):
        if metadata.get(key):
            return str(metadata[key])
    source = metadata.get("source_candidate_summary") or metadata.get("source_candidate") or {}
    if isinstance(source, dict) and source.get("recipe_id"):
        return str(source["recipe_id"])
    return ""


def _annotate_ballad_spread_runtime_enablement_guard_candidate(
    candidate: Any,
    *,
    true_isolation: dict[str, object] | None = None,
) -> Any:
    isolation = dict(true_isolation or {})
    true_isolation_enabled = bool(isolation.get("enabled", False))
    required_recipe_id = str(isolation.get("required_recipe_id") or "")
    grouping_mix_decision = isolation.get("grouping_mix_decision")
    metadata = {
        **dict(getattr(candidate, "metadata", {}) or {}),
        "ballad_spread_grouping_mix_policy_decision": grouping_mix_decision,
        "ballad_spread_pilot_runtime_enablement_guard_version": BALLAD_SPREAD_PILOT_RUNTIME_ENABLEMENT_GUARD_VERSION,
        "ballad_spread_1plus4_true_isolation_fix_version": BALLAD_SPREAD_1PLUS4_TRUE_ISOLATION_FIX_VERSION,
        "ballad_spread_runtime_pilot_enabled": True,
        "ballad_spread_first_listening_isolation_candidate": True,
        "ballad_spread_1plus4_true_isolation_enabled": true_isolation_enabled,
        "ballad_spread_true_isolation_required_recipe_id": required_recipe_id or None,
        "ballad_spread_true_isolation_candidate_pool_mode": "spread_only_when_available" if true_isolation_enabled else "spread_plus_fallback",
        "first_listening_isolation_only": True,
        "fallback_non_spread_pool_retained": not true_isolation_enabled,
        "fallback_only_when_true_isolation_candidate_missing": bool(isolation.get("fallback_only_when_missing", False)),
        "candidate_generator_wiring_allowed": True,
        "style_runtime_default_enabled": False,
        "default_style_runtime_unchanged": True,
        "runtime_pilot_guard_status": BalladSpreadPilotRuntimeEnablementGuardStatus.ENABLED_FOR_LISTENING_ISOLATION.value,
        "no_expression_or_pedal": True,
        "does_not_change_medium_swing_or_bossa": True,
    }
    selector_decision = {
        **dict(getattr(candidate, "selector_decision", {}) or {}),
        "ballad_spread_grouping_mix_policy_decision": grouping_mix_decision,
        "ballad_spread_pilot_runtime_enablement_guard_version": BALLAD_SPREAD_PILOT_RUNTIME_ENABLEMENT_GUARD_VERSION,
        "ballad_spread_1plus4_true_isolation_fix_version": BALLAD_SPREAD_1PLUS4_TRUE_ISOLATION_FIX_VERSION,
        "ballad_spread_runtime_pilot_enabled": True,
        "ballad_spread_1plus4_true_isolation_enabled": true_isolation_enabled,
        "ballad_spread_true_isolation_required_recipe_id": required_recipe_id or None,
        "first_listening_isolation_only": True,
        "fallback_non_spread_pool_retained": not true_isolation_enabled,
    }
    try:
        return replace(candidate, metadata=metadata, selector_decision=selector_decision)
    except Exception:
        return candidate

def _ballad_spread_selection_audit_values(policy: Any | None) -> dict[str, object]:
    try:
        metadata = dict(getattr(policy, "metadata", None) or {})
    except Exception:
        metadata = dict(policy or {}) if isinstance(policy, dict) else {}
    nested = (
        metadata.get("ballad_spread_pilot_selection_weight_fallback_audit")
        or metadata.get("ballad_spread_selection_weight_fallback_audit")
        or metadata.get("spread_pilot_selection_weight_audit")
        or {}
    )
    if not isinstance(nested, dict):
        nested = {"audit_enabled": nested}
    return {**metadata, **nested}


def _candidate_raw_score(candidate: Any) -> float:
    try:
        return float(getattr(candidate, "score", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _fallback_pool_retained(pool: BalladSpreadRuntimeCandidatePoolResult) -> bool:
    base = tuple(pool.base_candidates)
    if not base:
        return False
    merged = tuple(pool.merged_candidates)
    if len(merged) < len(base):
        return False
    # The current v2_2_48 pilot merge prepends SPREAD candidates and appends the
    # original base pool unchanged.  Keep the check explicit so future rewiring
    # cannot silently drop the fallback pool.
    return tuple(merged[-len(base):]) == base


def _spread_float_value(values: dict[str, object], key: str, *, default: float) -> float:
    try:
        return float(values.get(key, default))
    except (TypeError, ValueError):
        return float(default)


def _spread_runtime_adapter_values(policy: Any | None) -> dict[str, object]:
    try:
        metadata = dict(getattr(policy, "metadata", None) or {})
    except Exception:
        metadata = dict(policy or {}) if isinstance(policy, dict) else {}
    nested = metadata.get("spread_runtime_adapter") or metadata.get("spread_runtime_adapter_skeleton") or {}
    if not isinstance(nested, dict):
        nested = {"adapter_conversion_allowed": nested}
    return {**metadata, **nested}


def _spread_runtime_adapter_conversion_requested(policy: Any | None, allow_conversion: bool | None) -> bool:
    if allow_conversion is not None:
        return bool(allow_conversion)
    values = _spread_runtime_adapter_values(policy)
    return _spread_bool_any(
        values,
        (
            "adapter_conversion_allowed",
            "spread_runtime_adapter_conversion_allowed",
            "spread_projection_candidate_to_voicing_candidate_adapter_enabled",
            "allow_spread_runtime_adapter_conversion",
        ),
        default=False,
    )


def _spread_runtime_content_family(candidate: SpreadProjectionCandidate, policy: Any | None, content_family_enum: Any) -> Any | None:
    for value in (
        getattr(getattr(candidate, "upper_source", None), "source_family", None),
        getattr(policy, "preferred_content", None),
    ):
        if value is None:
            continue
        if isinstance(value, content_family_enum):
            return value
        try:
            return content_family_enum(str(value))
        except ValueError:
            continue
    return None


def _spread_runtime_root_support(candidate: SpreadProjectionCandidate, policy: Any | None, root_support_enum: Any) -> Any:
    requested = getattr(policy, "root_support", None)
    if isinstance(requested, root_support_enum):
        return requested
    try:
        if requested is not None:
            return root_support_enum(str(requested))
    except ValueError:
        pass
    if "R" in candidate.degrees:
        return root_support_enum.ROOT_PREFERRED
    return root_support_enum.ROOTLESS_ALLOWED


def _spread_runtime_bass_relation(candidate: SpreadProjectionCandidate, bass_relation_enum: Any) -> Any:
    if candidate.degrees and candidate.degrees[0] == "R":
        return bass_relation_enum.ROOT_POSITION
    if "R" not in candidate.degrees:
        return bass_relation_enum.BASS_OMITTED
    return bass_relation_enum.ROOT_POSITION


def _spread_runtime_interval_structure(policy: Any | None, interval_structure_enum: Any) -> Any:
    requested = getattr(policy, "interval_structure", None)
    if isinstance(requested, interval_structure_enum):
        return requested
    try:
        if requested is not None:
            return interval_structure_enum(str(requested))
    except ValueError:
        pass
    return interval_structure_enum.MIXED


def _spread_runtime_root_support_decision(policy: Any | None) -> dict[str, object]:
    try:
        metadata = dict(getattr(policy, "metadata", None) or {})
    except Exception:
        metadata = {}
    decision = metadata.get("root_support_decision")
    return dict(decision) if isinstance(decision, dict) else {}


def _spread_selector_gate_values(policy: Any | None) -> dict[str, object]:
    try:
        metadata = dict(getattr(policy, "metadata", None) or {})
    except Exception:
        metadata = dict(policy or {}) if isinstance(policy, dict) else {}
    nested = metadata.get("spread_selector") or metadata.get("spread_runtime_gate") or metadata.get("spread_runtime") or {}
    if not isinstance(nested, dict):
        nested = {"spread_candidate_selector_enabled": nested}
    return {**metadata, **nested}


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


def _spread_requested_families(values: dict[str, object], texture_state: Any | None) -> tuple[str | None, tuple[str, ...]]:
    primary = _spread_family_value(
        getattr(texture_state, "primary_family", None)
        or values.get("primary_family")
        or values.get("voicing_texture_primary_family")
        or values.get("primary_texture_family")
    )
    allowed_raw = (
        getattr(texture_state, "allowed_families", None)
        or values.get("allowed_families")
        or values.get("voicing_texture_allowed_families")
        or values.get("allowed_texture_families")
    )
    allowed = _spread_family_tuple(allowed_raw)
    if primary and primary not in allowed:
        allowed = (primary, *allowed)
    return primary, allowed


def _spread_family_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        values = [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = [value]
    out: list[str] = []
    for item in values:
        normalized = _spread_family_value(item)
        if normalized and normalized not in out:
            out.append(normalized)
    return tuple(out)


def _spread_family_value(value: object) -> str | None:
    raw = getattr(value, "value", value)
    if raw is None:
        return None
    text = str(raw).strip().lower().replace("-", "_")
    aliases = {
        "two_hand_spread": "spread",
        "spread_ballad": "spread",
        "rooted_spread": "spread",
        "wide_warm_ballad": "spread",
    }
    return aliases.get(text, text) if text else None




def _ballad_spread_dry_run_values(policy: Any | None) -> dict[str, object]:
    try:
        metadata = dict(getattr(policy, "metadata", None) or {})
    except Exception:
        metadata = dict(policy or {}) if isinstance(policy, dict) else {}
    nested = (
        metadata.get("ballad_spread_runtime_safe_dry_run")
        or metadata.get("ballad_spread_safe_dry_run")
        or metadata.get("ballad_spread_dry_run")
        or {}
    )
    if not isinstance(nested, dict):
        nested = {"dry_run_enabled": nested}
    return {**metadata, **nested}


def _ballad_spread_entry_values(policy: Any | None) -> dict[str, object]:
    try:
        metadata = dict(getattr(policy, "metadata", None) or {})
    except Exception:
        metadata = dict(policy or {}) if isinstance(policy, dict) else {}
    nested = (
        metadata.get("ballad_spread_runtime_pilot")
        or metadata.get("ballad_spread_entry_contract")
        or metadata.get("ballad_spread_entry")
        or {}
    )
    if not isinstance(nested, dict):
        nested = {"enabled": nested}
    return {**metadata, **nested}


def _normalize_style_name(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def _coerce_ballad_spread_scene(value: object | None) -> BalladSpreadEntryScene:
    text = str(getattr(value, "value", value) or "").strip().lower().replace("-", "_")
    aliases = {
        "": BalladSpreadEntryScene.EXPLICIT_TEXTURE_REQUEST,
        "explicit": BalladSpreadEntryScene.EXPLICIT_TEXTURE_REQUEST,
        "explicit_request": BalladSpreadEntryScene.EXPLICIT_TEXTURE_REQUEST,
        "texture_request": BalladSpreadEntryScene.EXPLICIT_TEXTURE_REQUEST,
        "wide_warm_ballad": BalladSpreadEntryScene.WARM_SPREAD_PHRASE,
        "warm_spread": BalladSpreadEntryScene.WARM_SPREAD_PHRASE,
        "phrase": BalladSpreadEntryScene.WARM_SPREAD_PHRASE,
        "cadence": BalladSpreadEntryScene.FINAL_CADENCE_LIFT,
        "ending": BalladSpreadEntryScene.THICK_ENDING_PREP,
        "thick_ending": BalladSpreadEntryScene.THICK_ENDING_PREP,
        "solo": BalladSpreadEntryScene.SOLO_PIANO_SECTION,
        "solo_piano": BalladSpreadEntryScene.SOLO_PIANO_SECTION,
        "no_bass": BalladSpreadEntryScene.NO_BASS_FOUNDATION,
    }
    if text in aliases:
        return aliases[text]
    try:
        return BalladSpreadEntryScene(text)
    except ValueError:
        return BalladSpreadEntryScene.EXPLICIT_TEXTURE_REQUEST


def _valid_ballad_spread_contract_ids(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        raw_values = [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
    elif isinstance(value, (list, tuple, set)):
        raw_values = [str(item).strip() for item in value if str(item).strip()]
    else:
        raw_values = [str(value).strip()] if str(value).strip() else []
    allowed = set(BALLAD_SPREAD_ENTRY_ALLOWED_CONTRACT_IDS)
    out: list[str] = []
    for item in raw_values:
        if item in allowed and item not in out:
            out.append(item)
    return tuple(out)


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


def _paired_note_motion(previous_notes: tuple[int, ...] | list[int], current_notes: tuple[int, ...] | list[int]) -> int:
    previous_values = tuple(sorted(int(note) for note in previous_notes))
    current_values = tuple(sorted(int(note) for note in current_notes))
    if not previous_values:
        return 0
    if not current_values:
        return int(len(previous_values) * 3)
    from jammate_engine.core.voicing.selection.voice_leading import set_based_voice_leading_distance

    return int(round(set_based_voice_leading_distance(previous_values, current_values, birth_death_penalty=3.0).distance))


def _top_voice_motion(previous: SpreadProjectionCandidate | None, current: SpreadProjectionCandidate) -> int:
    if previous is None or not previous.notes or not current.notes:
        return 0
    return int(abs(max(previous.notes) - max(current.notes)))


def _group_gap_change(previous: SpreadProjectionCandidate | None, current: SpreadProjectionCandidate) -> int:
    if previous is None:
        return 0
    if previous.group_gap_semitones is None or current.group_gap_semitones is None:
        return 0
    return int(abs(int(previous.group_gap_semitones) - int(current.group_gap_semitones)))


def _spread_span_penalty(candidate: SpreadProjectionCandidate) -> int:
    max_span = int(candidate.register_policy.max_overall_span)
    return int(max(0, candidate.overall_span_semitones - max_span))


def _outside_register_distance(notes: tuple[int, ...], low: int, high: int) -> int:
    penalty = 0
    for note in notes:
        if int(note) < int(low):
            penalty += int(low) - int(note)
        elif int(note) > int(high):
            penalty += int(note) - int(high)
    return int(penalty)


def _spread_register_penalty(candidate: SpreadProjectionCandidate) -> int:
    policy = candidate.register_policy
    return int(
        _outside_register_distance(candidate.lower_notes, int(policy.lower_low), int(policy.lower_high))
        + _outside_register_distance(candidate.upper_notes, int(policy.upper_low), int(policy.upper_high))
    )


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
