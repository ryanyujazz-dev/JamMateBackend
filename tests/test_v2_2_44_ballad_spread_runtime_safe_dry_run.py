from __future__ import annotations

# harness token: test_v2_2_44_ballad_spread_runtime_safe_dry_run

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.disposition.models import DispositionFamily
from jammate_engine.core.voicing.disposition.spread import (
    BALLAD_SPREAD_RUNTIME_ENTRY_CONTRACT_VERSION,
    BALLAD_SPREAD_RUNTIME_SAFE_DRY_RUN_VERSION,
    BalladSpreadRuntimeDryRunChordTrace,
    BalladSpreadRuntimePilotWiringPlan,
    BalladSpreadRuntimeSafeDryRunResult,
    ballad_spread_runtime_pilot_wiring_plan,
    ballad_spread_runtime_safe_dry_run_debug,
    run_ballad_spread_runtime_safe_dry_run,
)
from jammate_engine.core.voicing.policy import VoicingPolicy
from jammate_engine.core.voicing.runtime.texture_plan import VoicingTextureState
from jammate_engine.styles.bossa_nova.profile import BossaNovaProfile
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile
from jammate_engine.styles.medium_swing.profile import MediumSwingProfile

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _dry_run_policy(style: str = "jazz_ballad") -> VoicingPolicy:
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
                "preferred_contract_ids": ["spread_1plus4_contract", "spread_2plus3_contract"],
            },
            "ballad_spread_runtime_safe_dry_run": {
                "dry_run_enabled": True,
            },
        }
    )


def test_v2_2_44_version_is_current_while_preserving_entry_subcontract() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert BALLAD_SPREAD_RUNTIME_SAFE_DRY_RUN_VERSION == "v2_2_44"
    assert BALLAD_SPREAD_RUNTIME_ENTRY_CONTRACT_VERSION == "v2_2_43"


def test_ballad_spread_safe_dry_run_plan_is_disabled_by_default() -> None:
    plan = ballad_spread_runtime_pilot_wiring_plan(JazzBalladProfile().voicing_policy)
    assert isinstance(plan, BalladSpreadRuntimePilotWiringPlan)
    assert plan.dry_run_enabled is False
    assert plan.runtime_enabled is False
    assert plan.style_runtime_wiring_enabled is False
    assert plan.candidate_conversion_allowed is False
    assert plan.output_candidate_type == "SpreadProjectionCandidate"
    assert plan.future_conversion_target == "VoicingCandidate"

    result = run_ballad_spread_runtime_safe_dry_run(("Dm7", "G7", "Cmaj7"), JazzBalladProfile().voicing_policy)
    assert isinstance(result, BalladSpreadRuntimeSafeDryRunResult)
    assert result.blocked_reason == "ballad_spread_runtime_safe_dry_run_not_enabled"
    assert result.traces == ()
    assert result.runtime_enabled is False


def test_explicit_ballad_safe_dry_run_selects_notes_only_path_without_conversion() -> None:
    texture_state = VoicingTextureState(
        primary_family=DispositionFamily.SPREAD,
        allowed_families=(DispositionFamily.SPREAD,),
    )
    result = run_ballad_spread_runtime_safe_dry_run(
        ("Dm7", "G7", "Cmaj7"),
        _dry_run_policy(),
        texture_state=texture_state,
    )
    assert result.dry_run_completed is True
    assert result.selected_candidate_count == 3
    assert len(result.traces) == 3
    assert all(isinstance(trace, BalladSpreadRuntimeDryRunChordTrace) for trace in result.traces)
    assert all(trace.entry_allowed for trace in result.traces)
    assert all(trace.selected is not None for trace in result.traces)
    assert all(trace.selected.runtime_enabled is False for trace in result.traces if trace.selected is not None)
    assert all(trace.conversion_boundary == "notes_only_candidate_not_converted_to_runtime_voicing" for trace in result.traces)

    debug = result.to_debug_dict()
    assert debug["candidate_conversion_allowed"] is False
    assert debug["style_runtime_wiring_enabled"] is False
    assert debug["runtime_enabled"] is False
    assert debug["notes_only"] is True
    assert debug["safe_dry_run_only"] is True


def test_explicit_enable_argument_opens_safe_dry_run_and_existing_entry_gate() -> None:
    policy = VoicingPolicy(
        metadata={
            "style": "jazz_ballad",
            "primary_family": "spread",
            "allowed_families": ["spread"],
            "ballad_spread_runtime_pilot": {"scene": "warm_spread_phrase"},
        }
    )
    result = run_ballad_spread_runtime_safe_dry_run(("Cmaj7",), policy, explicit_enable=True)
    assert result.dry_run_completed is True
    assert result.selected_candidate_count == 1
    assert result.traces[0].selected is not None
    assert result.traces[0].pilot_result.decision.reason == "ballad_spread_pilot_entry_allowed_notes_only"


def test_medium_swing_and_bossa_safe_dry_run_remain_blocked() -> None:
    for policy in (MediumSwingProfile().voicing_policy, BossaNovaProfile().voicing_policy):
        result = run_ballad_spread_runtime_safe_dry_run(("Cmaj7",), policy, explicit_enable=True)
        assert result.dry_run_completed is False
        assert result.blocked_reason == "style_not_allowed_for_ballad_spread_pilot"
        assert len(result.traces) == 1
        assert result.traces[0].selected is None
        assert result.runtime_enabled is False


def test_default_jazz_ballad_policy_declares_dry_run_metadata_but_keeps_it_closed() -> None:
    policy = JazzBalladProfile().voicing_policy
    assert policy.metadata["ballad_spread_runtime_safe_dry_run"]["version"] == "v2_2_44"
    assert policy.metadata["ballad_spread_runtime_safe_dry_run"]["dry_run_enabled"] is False
    assert policy.metadata["ballad_spread_runtime_safe_dry_run"]["candidate_conversion_allowed"] is False
    assert policy.metadata["ballad_spread_runtime_safe_dry_run"]["style_runtime_wiring_enabled"] is False
    assert policy.metadata["ballad_spread_runtime_safe_dry_run"]["runtime_enabled"] is False


def test_ballad_spread_safe_dry_run_debug_and_docs_are_synced() -> None:
    closed_debug = ballad_spread_runtime_safe_dry_run_debug(
        ("Dm7", "G7", "Cmaj7"),
        JazzBalladProfile().voicing_policy,
    )
    assert closed_debug["ballad_spread_runtime_safe_dry_run_version"] == "v2_2_44"
    assert closed_debug["result"]["blocked_reason"] == "ballad_spread_runtime_safe_dry_run_not_enabled"
    assert closed_debug["candidate_conversion_allowed"] is False
    assert closed_debug["style_runtime_wiring_enabled"] is False
    assert closed_debug["runtime_enabled"] is False

    open_debug = ballad_spread_runtime_safe_dry_run_debug(("Dm7", "G7", "Cmaj7"), _dry_run_policy())
    assert open_debug["result"]["dry_run_completed"] is True
    assert open_debug["result"]["selected_candidate_count"] == 3

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
        "Ballad SPREAD Runtime Pilot Wiring Plan + Safe Dry Run",
        "BALLAD_SPREAD_RUNTIME_SAFE_DRY_RUN_VERSION",
        "BalladSpreadRuntimePilotWiringPlan",
        "BalladSpreadRuntimeDryRunChordTrace",
        "BalladSpreadRuntimeSafeDryRunResult",
        "ballad_spread_runtime_pilot_wiring_plan",
        "run_ballad_spread_runtime_safe_dry_run",
        "ballad_spread_runtime_safe_dry_run_debug",
        "entry_contract_to_selector_gate_to_notes_only_candidate_to_future_conversion_boundary",
        "candidate_conversion_allowed=false",
        "style_runtime_wiring_enabled=false",
        "runtime_enabled=false",
        "safe dry run only",
        "Medium Swing and Bossa remain unaffected",
    ]
    for token in required:
        assert token in docs
