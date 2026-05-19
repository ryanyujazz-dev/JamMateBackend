from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .spread_contracts import SPREAD_RECIPE_CONTRACT_VERSION
from .spread_register_guards import BASIC_SPREAD_PROJECTION_VERSION
from .spread_projection_core import project_basic_spread_candidates
from .spread_voice_leading import (
    GROUPWISE_SPREAD_VOICE_LEADING_VERSION,
    SpreadGroupwiseVoiceLeadingScore,
    SpreadGroupwiseVoiceLeadingWeights,
    rank_spread_candidates_by_groupwise_voice_leading,
)

SPREAD_SELECTOR_RUNTIME_GATE_VERSION = "v2_2_42"
SPREAD_RUNTIME_GATE_ADAPTER_CLEANUP_VERSION = "v2_6_15"


@dataclass(frozen=True)
class SpreadRuntimeGateDecision:
    """Safety gate for SPREAD candidate selection/runtime entry.

    This owner only decides whether notes-only SPREAD projection may be queried.
    It does not convert SPREAD candidates into runtime voicings, change style
    defaults, select patterns, apply expression, or write MIDI.
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
            "spread_runtime_gate_adapter_cleanup_version": SPREAD_RUNTIME_GATE_ADAPTER_CLEANUP_VERSION,
            "implementation_owner": "core.voicing.disposition.spread_runtime_gate",
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
            "no_pattern_anticipation_gesture_or_midi": True,
        }


@dataclass(frozen=True)
class SpreadCandidateSelectorRequest:
    """Selector request contract for notes-only SPREAD candidates."""

    chord_symbol: str
    contract_ids: tuple[str, ...] = ()
    max_upper_options: int = 12
    legal_only: bool = True
    source: str = "explicit_policy_gate"
    runtime_enabled: bool = False

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "spread_selector_runtime_gate_version": SPREAD_SELECTOR_RUNTIME_GATE_VERSION,
            "spread_runtime_gate_adapter_cleanup_version": SPREAD_RUNTIME_GATE_ADAPTER_CLEANUP_VERSION,
            "implementation_owner": "core.voicing.disposition.spread_runtime_gate",
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

    The selected object remains a notes-only projection candidate. Runtime
    conversion is owned by the adapter boundary and is never implied here.
    """

    request: SpreadCandidateSelectorRequest
    gate: SpreadRuntimeGateDecision
    projected_results: tuple[Any, ...]
    ranked_scores: tuple[SpreadGroupwiseVoiceLeadingScore, ...]
    selected: Any | None
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
            "spread_runtime_gate_adapter_cleanup_version": SPREAD_RUNTIME_GATE_ADAPTER_CLEANUP_VERSION,
            "layer": "core.voicing.disposition.spread_runtime_gate",
            "implementation_owner": "core.voicing.disposition.spread_runtime_gate",
            "purpose": "SPREAD Candidate Selector Contract / Runtime Gate Skeleton",
            "request": self.request.to_debug_dict(),
            "gate": self.gate.to_debug_dict(),
            "projected_result_count": self.projected_result_count,
            "candidate_count": self.candidate_count,
            "legal_candidate_count": self.legal_candidate_count,
            "ranked_score_count": self.ranked_score_count,
            "selected_candidate": self.selected.to_debug_dict() if self.selected is not None else None,
            "selected_score": self.selected_score.to_debug_dict() if self.selected_score is not None else None,
            "selected_candidate_runtime_enabled": bool(getattr(self.selected, "runtime_enabled", False)) if self.selected is not None else False,
            "candidate_conversion_allowed": False,
            "style_runtime_wiring_enabled": False,
            "runtime_enabled": bool(self.runtime_enabled),
            "notes_only": True,
            "no_expression_or_pedal": True,
            "does_not_change_default_style_runtime": True,
            "no_pattern_anticipation_gesture_or_midi": True,
        }


def spread_runtime_gate_from_policy(
    policy: Any | None = None,
    *,
    texture_state: Any | None = None,
    explicit_enable: bool | None = None,
) -> SpreadRuntimeGateDecision:
    """Resolve the safety gate for SPREAD notes-only candidate selection."""

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
    previous: Any | None = None,
    texture_state: Any | None = None,
    contract_ids: tuple[str, ...] | list[str] | None = None,
    weights: SpreadGroupwiseVoiceLeadingWeights | None = None,
    max_upper_options: int = 12,
    legal_only: bool = True,
    explicit_enable: bool | None = None,
) -> SpreadCandidateSelectorResult:
    """Select a notes-only SPREAD candidate through the runtime gate."""

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
    all_candidates: list[Any] = []
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
    """Return SPREAD selector/gate debug metadata from the new owner."""

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
        "spread_runtime_gate_adapter_cleanup_version": SPREAD_RUNTIME_GATE_ADAPTER_CLEANUP_VERSION,
        "layer": "core.voicing.disposition.spread_runtime_gate",
        "implementation_owner": "core.voicing.disposition.spread_runtime_gate",
        "purpose": "SPREAD Candidate Selector Contract / Runtime Gate Skeleton",
        "result": result.to_debug_dict(),
        "default_gate_closed_without_explicit_policy": not result.gate.selector_gate_open,
        "candidate_conversion_allowed": False,
        "style_runtime_wiring_enabled": False,
        "runtime_enabled": False,
        "notes_only": True,
        "no_expression_or_pedal": True,
        "no_pattern_anticipation_gesture_or_midi": True,
    }


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
