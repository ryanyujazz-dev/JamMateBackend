from __future__ import annotations

# harness token: test_v2_2_42_spread_selector_runtime_gate

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.disposition.models import DispositionFamily
from jammate_engine.core.voicing.disposition.spread import (
    GROUPWISE_SPREAD_VOICE_LEADING_VERSION,
    SPREAD_SELECTOR_RUNTIME_GATE_VERSION,
    SpreadRuntimeGateDecision,
    SpreadCandidateSelectorResult,
    select_spread_candidate_with_runtime_gate,
    spread_candidate_selector_contract_debug,
    spread_runtime_gate_from_policy,
)
from jammate_engine.core.voicing.policy import VoicingPolicy
from jammate_engine.core.voicing.runtime.texture_plan import VoicingTextureState

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _explicit_spread_policy() -> VoicingPolicy:
    return VoicingPolicy(
        metadata={
            "spread_selector": {"spread_candidate_selector_enabled": True},
            "primary_family": "spread",
            "allowed_families": ["spread"],
        }
    )


def test_v2_2_42_version_is_current_while_preserving_groupwise_subcontract() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert SPREAD_SELECTOR_RUNTIME_GATE_VERSION == "v2_2_42"
    assert GROUPWISE_SPREAD_VOICE_LEADING_VERSION == "v2_2_41"


def test_spread_runtime_gate_is_closed_by_default() -> None:
    gate = spread_runtime_gate_from_policy(None)
    assert isinstance(gate, SpreadRuntimeGateDecision)
    debug = gate.to_debug_dict()
    assert gate.selector_gate_open is False
    assert debug["reason"] == "explicit_spread_runtime_gate_not_requested"
    assert debug["explicit_request"] is False
    assert debug["style_runtime_wiring_enabled"] is False
    assert debug["candidate_conversion_allowed"] is False
    assert debug["runtime_enabled"] is False
    assert debug["notes_only"] is True
    assert debug["no_expression_or_pedal"] is True


def test_spread_runtime_gate_requires_explicit_request_and_spread_family() -> None:
    explicit_without_family = VoicingPolicy(metadata={"spread_selector_enabled": True, "primary_family": "open"})
    blocked = spread_runtime_gate_from_policy(explicit_without_family)
    assert blocked.selector_gate_open is False
    assert blocked.reason == "explicit_request_without_spread_texture_family"
    assert blocked.explicit_request is True
    assert blocked.spread_family_requested is False

    spread_family_without_explicit = VoicingPolicy(metadata={"primary_family": "spread", "allowed_families": ["spread"]})
    still_closed = spread_runtime_gate_from_policy(spread_family_without_explicit)
    assert still_closed.selector_gate_open is False
    assert still_closed.reason == "explicit_spread_runtime_gate_not_requested"

    open_gate = spread_runtime_gate_from_policy(_explicit_spread_policy())
    assert open_gate.selector_gate_open is True
    assert open_gate.reason == "explicit_policy_requested_spread_selector_gate"
    assert open_gate.spread_family_requested is True
    assert open_gate.style_runtime_wiring_enabled is False
    assert open_gate.candidate_conversion_allowed is False


def test_spread_selector_uses_texture_state_as_family_request_but_stays_notes_only() -> None:
    policy = VoicingPolicy(metadata={"spread_runtime_gate_enabled": True})
    state = VoicingTextureState(
        primary_family=DispositionFamily.SPREAD,
        allowed_families=(DispositionFamily.SPREAD,),
    )
    result = select_spread_candidate_with_runtime_gate(
        "Dm7",
        policy,
        texture_state=state,
        contract_ids=("spread_2plus3_contract",),
    )
    assert isinstance(result, SpreadCandidateSelectorResult)
    assert result.gate.selector_gate_open is True
    assert result.projected_result_count == 1
    assert result.legal_candidate_count > 0
    assert result.ranked_score_count > 0
    assert result.selected is not None
    assert result.selected.runtime_enabled is False
    debug = result.to_debug_dict()
    assert debug["candidate_conversion_allowed"] is False
    assert debug["style_runtime_wiring_enabled"] is False
    assert debug["runtime_enabled"] is False
    assert debug["notes_only"] is True
    assert debug["no_expression_or_pedal"] is True


def test_spread_selector_returns_no_candidates_when_gate_closed() -> None:
    result = select_spread_candidate_with_runtime_gate(
        "Cmaj7",
        VoicingPolicy(metadata={"primary_family": "spread", "allowed_families": ["spread"]}),
        contract_ids=("spread_1plus4_contract",),
    )
    assert result.gate.selector_gate_open is False
    assert result.projected_result_count == 0
    assert result.candidate_count == 0
    assert result.selected is None
    assert result.runtime_enabled is False


def test_spread_selector_contract_debug_and_docs_are_synced() -> None:
    default_debug = spread_candidate_selector_contract_debug("Cmaj7")
    assert default_debug["spread_selector_runtime_gate_version"] == "v2_2_42"
    assert default_debug["default_gate_closed_without_explicit_policy"] is True
    assert default_debug["candidate_conversion_allowed"] is False
    assert default_debug["style_runtime_wiring_enabled"] is False
    assert default_debug["runtime_enabled"] is False

    open_debug = spread_candidate_selector_contract_debug(
        "Cmaj7",
        _explicit_spread_policy(),
        contract_ids=("spread_1plus4_contract",),
    )
    assert open_debug["result"]["gate"]["selector_gate_open"] is True
    assert open_debug["result"]["selected_candidate"] is not None
    assert open_debug["result"]["selected_candidate_runtime_enabled"] is False

    docs = "\n".join(
        _read(rel)
        for rel in (
            "agent.md",
            "README.md",
            "docs/VOICING_SYSTEM_V2_DESIGN.md",
            "docs/VOICING_MODULE_CORE_LOGIC_V2.md",
            "docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md",
            "docs/VOICING_TEXTURE_STATE_ARCHITECTURE_V2.md",
            "docs/DEVELOPMENT_TASK_PLAN_V2.md",
            "docs/DEVELOPMENT_HARNESS_V2.md",
            "docs/GENERATION_RULES_SUMMARY_V2.md",
        )
    )
    required = [
        "SPREAD Candidate Selector Contract / Runtime Gate Skeleton",
        "SPREAD_SELECTOR_RUNTIME_GATE_VERSION",
        "SpreadRuntimeGateDecision",
        "SpreadCandidateSelectorRequest",
        "SpreadCandidateSelectorResult",
        "spread_runtime_gate_from_policy",
        "select_spread_candidate_with_runtime_gate",
        "spread_candidate_selector_contract_debug",
        "candidate_conversion_allowed=false",
        "style_runtime_wiring_enabled=false",
        "runtime_enabled=false",
        "notes-only",
    ]
    for token in required:
        assert token in docs
