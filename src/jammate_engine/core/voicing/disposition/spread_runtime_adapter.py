from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION = "v2_2_47"
SPREAD_RUNTIME_GATE_ADAPTER_CLEANUP_VERSION = "v2_6_15"


class SpreadRuntimeAdapterStatus(str, Enum):
    """Status for the SPREAD runtime adapter skeleton.

    The adapter owns field mapping and explicit conversion metadata only. It is
    not candidate-generator wiring and does not change any style runtime by
    itself.
    """

    DEFAULT_BLOCKED = "default_blocked"
    POLICY_BLOCKED = "policy_blocked"
    INVALID_SOURCE_CANDIDATE = "invalid_source_candidate"
    UNSUPPORTED_GROUPING = "unsupported_grouping"
    ADAPTED_SKELETON_ONLY = "adapted_skeleton_only"


@dataclass(frozen=True)
class SpreadRuntimeAdapterFieldMapping:
    """One explicit source-to-runtime field mapping for the adapter skeleton."""

    source_field: str
    target_field: str
    copied: bool
    reason: str
    source_owner_path: str = "core.voicing.disposition.spread.SpreadProjectionCandidate"
    target_owner_path: str = "core.voicing.selection.candidate.VoicingCandidate"

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "spread_runtime_adapter_skeleton_version": SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION,
            "spread_runtime_gate_adapter_cleanup_version": SPREAD_RUNTIME_GATE_ADAPTER_CLEANUP_VERSION,
            "implementation_owner": "core.voicing.disposition.spread_runtime_adapter",
            "source_field": self.source_field,
            "target_field": self.target_field,
            "copied": bool(self.copied),
            "reason": self.reason,
            "source_owner_path": self.source_owner_path,
            "target_owner_path": self.target_owner_path,
        }


@dataclass(frozen=True)
class SpreadRuntimeAdapterResult:
    """Result of explicit SPREAD projection -> VoicingCandidate adaptation."""

    source_candidate: Any | None
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
            "spread_runtime_gate_adapter_cleanup_version": SPREAD_RUNTIME_GATE_ADAPTER_CLEANUP_VERSION,
            "layer": "core.voicing.disposition.spread_runtime_adapter",
            "implementation_owner": "core.voicing.disposition.spread_runtime_adapter",
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
            "no_pattern_anticipation_gesture_or_midi": True,
        }


def spread_runtime_adapter_field_mappings() -> tuple[SpreadRuntimeAdapterFieldMapping, ...]:
    return (
        SpreadRuntimeAdapterFieldMapping("candidate.notes", "VoicingCandidate.notes", True, "MIDI notes are copied verbatim from the legal SPREAD projection candidate"),
        SpreadRuntimeAdapterFieldMapping("candidate.degrees", "VoicingCandidate.degrees", True, "degree labels are copied verbatim so lower/upper metadata remains auditable"),
        SpreadRuntimeAdapterFieldMapping("candidate.recipe_contract.grouping", "VoicingCandidate.functional_grouping", True, "grouping is coerced through core FunctionalGrouping, including 1+4"),
        SpreadRuntimeAdapterFieldMapping("candidate.recipe_contract.grouping", "VoicingCandidate.group_roles", True, "group roles are derived through core recipes.group_roles_for_grouping rather than hand semantics"),
        SpreadRuntimeAdapterFieldMapping("candidate.upper_source.source_family", "VoicingCandidate.content_family", True, "content family is reused from the upper source adapter when it matches core ContentFamily"),
        SpreadRuntimeAdapterFieldMapping("candidate.metadata", "VoicingCandidate.metadata", True, "SPREAD projection metadata is preserved and marked adapter_skeleton_only"),
        SpreadRuntimeAdapterFieldMapping("candidate.runtime_enabled", "candidate_generator runtime pool", False, "candidate-generator wiring remains explicitly gated outside the adapter"),
    )


# Backward-compatible private name imported by spread.py; implementation owner is this module.
_spread_runtime_adapter_field_mappings = spread_runtime_adapter_field_mappings


def spread_runtime_adapter_values(policy: Any | None) -> dict[str, object]:
    try:
        metadata = dict(getattr(policy, "metadata", None) or {})
    except Exception:
        metadata = dict(policy or {}) if isinstance(policy, dict) else {}
    nested = metadata.get("spread_runtime_adapter") or metadata.get("spread_runtime_adapter_skeleton") or {}
    if not isinstance(nested, dict):
        nested = {"adapter_conversion_allowed": nested}
    return {**metadata, **nested}


_spread_runtime_adapter_values = spread_runtime_adapter_values


def spread_runtime_adapter_conversion_requested(policy: Any | None, allow_conversion: bool | None) -> bool:
    if allow_conversion is not None:
        return bool(allow_conversion)
    values = spread_runtime_adapter_values(policy)
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


_spread_runtime_adapter_conversion_requested = spread_runtime_adapter_conversion_requested


def spread_runtime_content_family(candidate: Any, policy: Any | None, content_family_enum: Any) -> Any | None:
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


_spread_runtime_content_family = spread_runtime_content_family


def spread_runtime_root_support(candidate: Any, policy: Any | None, root_support_enum: Any) -> Any:
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


_spread_runtime_root_support = spread_runtime_root_support


def spread_runtime_bass_relation(candidate: Any, bass_relation_enum: Any) -> Any:
    if candidate.degrees and candidate.degrees[0] == "R":
        return bass_relation_enum.ROOT_POSITION
    if "R" not in candidate.degrees:
        return bass_relation_enum.BASS_OMITTED
    return bass_relation_enum.ROOT_POSITION


_spread_runtime_bass_relation = spread_runtime_bass_relation


def spread_runtime_interval_structure(policy: Any | None, interval_structure_enum: Any) -> Any:
    requested = getattr(policy, "interval_structure", None)
    if isinstance(requested, interval_structure_enum):
        return requested
    try:
        if requested is not None:
            return interval_structure_enum(str(requested))
    except ValueError:
        pass
    return interval_structure_enum.MIXED


_spread_runtime_interval_structure = spread_runtime_interval_structure


def spread_runtime_root_support_decision(policy: Any | None) -> dict[str, object]:
    try:
        metadata = dict(getattr(policy, "metadata", None) or {})
    except Exception:
        metadata = {}
    decision = metadata.get("root_support_decision")
    return dict(decision) if isinstance(decision, dict) else {}


_spread_runtime_root_support_decision = spread_runtime_root_support_decision


def spread_runtime_adapter_owner_debug(policy: Any | None = None) -> dict[str, object]:
    values = spread_runtime_adapter_values(policy)
    return {
        "spread_runtime_adapter_skeleton_version": SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION,
        "spread_runtime_gate_adapter_cleanup_version": SPREAD_RUNTIME_GATE_ADAPTER_CLEANUP_VERSION,
        "implementation_owner": "core.voicing.disposition.spread_runtime_adapter",
        "field_mapping_count": len(spread_runtime_adapter_field_mappings()),
        "field_mappings": [item.to_debug_dict() for item in spread_runtime_adapter_field_mappings()],
        "adapter_conversion_requested": spread_runtime_adapter_conversion_requested(policy, None),
        "policy_keys": sorted(str(key) for key in values.keys()),
        "runtime_enabled": False,
        "notes_only_source": True,
        "no_expression_or_pedal": True,
        "no_pattern_anticipation_gesture_or_midi": True,
    }


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
