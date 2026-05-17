from __future__ import annotations

# harness token: test_v2_2_43_ballad_spread_runtime_entry_contract

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.disposition.models import DispositionFamily
from jammate_engine.core.voicing.disposition.spread import (
    BALLAD_SPREAD_RUNTIME_ENTRY_CONTRACT_VERSION,
    SPREAD_SELECTOR_RUNTIME_GATE_VERSION,
    BalladSpreadEntryScene,
    BalladSpreadRuntimeEntryContract,
    BalladSpreadRuntimeEntryDecision,
    BalladSpreadRuntimePilotResult,
    ballad_spread_runtime_entry_contract,
    ballad_spread_runtime_entry_debug,
    resolve_ballad_spread_runtime_entry,
    select_ballad_spread_pilot_candidate,
)
from jammate_engine.core.voicing.policy import VoicingPolicy
from jammate_engine.core.voicing.runtime.texture_plan import VoicingTextureState
from jammate_engine.styles.bossa_nova.profile import BossaNovaProfile
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile
from jammate_engine.styles.medium_swing.profile import MediumSwingProfile

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _pilot_policy(style: str = "jazz_ballad") -> VoicingPolicy:
    return VoicingPolicy(
        metadata={
            "style": style,
            "primary_family": "spread",
            "allowed_families": ["spread"],
            "spread_selector_enabled": True,
            "ballad_spread_runtime_pilot": {
                "enabled": True,
                "scene": "warm_spread_phrase",
                "contract_ids": ["spread_1plus4_contract", "spread_2plus3_contract"],
                "preferred_contract_ids": ["spread_1plus4_contract"],
            },
        }
    )


def test_v2_2_43_version_is_current_while_preserving_selector_gate_subcontract() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert BALLAD_SPREAD_RUNTIME_ENTRY_CONTRACT_VERSION == "v2_2_43"
    assert SPREAD_SELECTOR_RUNTIME_GATE_VERSION == "v2_2_42"


def test_ballad_spread_entry_contract_is_disabled_by_default() -> None:
    contract = ballad_spread_runtime_entry_contract()
    assert isinstance(contract, BalladSpreadRuntimeEntryContract)
    assert contract.pilot_enabled is False
    assert contract.runtime_enabled is False
    assert contract.style_runtime_wiring_enabled is False
    assert contract.candidate_conversion_allowed is False
    assert contract.notes_only is True
    assert "spread_3plus4_contract" in contract.allowed_contract_ids
    assert contract.allowed_groupings == ("1+4", "2+3", "2+4", "3+3", "3+4")
    assert "spread_1plus3_contract" not in contract.allowed_contract_ids


def test_default_jazz_ballad_policy_declares_pilot_but_does_not_enable_entry() -> None:
    policy = JazzBalladProfile().voicing_policy
    assert policy.metadata["style"] == "jazz_ballad"
    assert policy.metadata["ballad_spread_runtime_pilot"]["enabled"] is False
    decision = resolve_ballad_spread_runtime_entry(policy)
    assert isinstance(decision, BalladSpreadRuntimeEntryDecision)
    assert decision.entry_allowed is False
    assert decision.reason == "ballad_spread_runtime_pilot_not_enabled"
    assert decision.runtime_enabled is False
    debug = decision.to_debug_dict()
    assert debug["candidate_conversion_allowed"] is False
    assert debug["style_runtime_wiring_enabled"] is False
    assert debug["notes_only"] is True


def test_ballad_entry_requires_ballad_style_and_existing_spread_gate() -> None:
    medium = _pilot_policy("medium_swing")
    blocked_style = resolve_ballad_spread_runtime_entry(medium)
    assert blocked_style.entry_allowed is False
    assert blocked_style.reason == "style_not_allowed_for_ballad_spread_pilot"

    missing_gate = VoicingPolicy(
        metadata={
            "style": "jazz_ballad",
            "primary_family": "spread",
            "allowed_families": ["spread"],
            "ballad_spread_runtime_pilot": {"enabled": True, "scene": "warm_spread_phrase"},
        }
    )
    blocked_gate = resolve_ballad_spread_runtime_entry(missing_gate)
    assert blocked_gate.entry_allowed is False
    assert blocked_gate.reason.startswith("spread_selector_gate_closed:")

    allowed = resolve_ballad_spread_runtime_entry(_pilot_policy())
    assert allowed.entry_allowed is True
    assert allowed.reason == "ballad_spread_pilot_entry_allowed_notes_only"
    assert allowed.gate.selector_gate_open is True


def test_ballad_pilot_selection_returns_notes_only_candidate_when_explicitly_allowed() -> None:
    state = VoicingTextureState(
        primary_family=DispositionFamily.SPREAD,
        allowed_families=(DispositionFamily.SPREAD,),
    )
    result = select_ballad_spread_pilot_candidate("Dm7", _pilot_policy(), texture_state=state)
    assert isinstance(result, BalladSpreadRuntimePilotResult)
    assert result.decision.entry_allowed is True
    assert result.selector_result is not None
    assert result.selected is not None
    assert result.selected.runtime_enabled is False
    debug = result.to_debug_dict()
    assert debug["candidate_conversion_allowed"] is False
    assert debug["style_runtime_wiring_enabled"] is False
    assert debug["runtime_enabled"] is False
    assert debug["notes_only"] is True
    assert debug["no_expression_or_pedal"] is True


def test_medium_swing_and_bossa_default_policies_are_unaffected() -> None:
    for policy in (MediumSwingProfile().voicing_policy, BossaNovaProfile().voicing_policy):
        decision = resolve_ballad_spread_runtime_entry(policy)
        assert decision.entry_allowed is False
        assert decision.reason == "style_not_allowed_for_ballad_spread_pilot"
        result = select_ballad_spread_pilot_candidate("Cmaj7", policy)
        assert result.selected is None
        assert result.selector_result is None


def test_ballad_spread_entry_debug_and_docs_are_synced() -> None:
    closed_debug = ballad_spread_runtime_entry_debug("Cmaj7", JazzBalladProfile().voicing_policy)
    assert closed_debug["ballad_spread_runtime_entry_contract_version"] == "v2_2_43"
    assert closed_debug["default_entry_closed_without_explicit_ballad_pilot"] is True
    assert closed_debug["candidate_conversion_allowed"] is False
    assert closed_debug["style_runtime_wiring_enabled"] is False
    assert closed_debug["runtime_enabled"] is False

    open_debug = ballad_spread_runtime_entry_debug("Cmaj7", _pilot_policy())
    assert open_debug["result"]["decision"]["entry_allowed"] is True
    assert open_debug["result"]["selected_candidate"] is not None

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
        "SPREAD Runtime Pilot Planning / Ballad Entry Contract",
        "BALLAD_SPREAD_RUNTIME_ENTRY_CONTRACT_VERSION",
        "BalladSpreadEntryScene",
        "BalladSpreadRuntimeEntryContract",
        "BalladSpreadRuntimeEntryDecision",
        "BalladSpreadRuntimePilotResult",
        "ballad_spread_runtime_entry_contract",
        "resolve_ballad_spread_runtime_entry",
        "select_ballad_spread_pilot_candidate",
        "ballad_spread_runtime_entry_debug",
        "style_runtime_wiring_enabled=false",
        "candidate_conversion_allowed=false",
        "runtime_enabled=false",
        "notes-only",
        "Medium Swing and Bossa remain unaffected",
    ]
    for token in required:
        assert token in docs
