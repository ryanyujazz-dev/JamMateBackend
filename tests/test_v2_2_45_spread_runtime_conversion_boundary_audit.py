from __future__ import annotations

# harness token: test_v2_2_45_spread_runtime_conversion_boundary_audit

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.disposition.models import DispositionFamily
from jammate_engine.core.voicing.disposition.spread import (
    BALLAD_SPREAD_RUNTIME_SAFE_DRY_RUN_VERSION,
    SPREAD_RUNTIME_CONVERSION_BOUNDARY_AUDIT_VERSION,
    BalladSpreadRuntimeConversionBoundaryAuditResult,
    SpreadRuntimeConversionBoundaryAudit,
    SpreadRuntimeConversionBoundaryStatus,
    audit_ballad_spread_runtime_conversion_boundaries,
    ballad_spread_runtime_conversion_boundary_debug,
    spread_runtime_conversion_boundary_audit,
    spread_runtime_conversion_boundary_debug,
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
                "contract_ids": ["spread_1plus4_contract"],
                "preferred_contract_ids": ["spread_1plus4_contract"],
            },
            "ballad_spread_runtime_safe_dry_run": {
                "dry_run_enabled": True,
            },
        }
    )


def test_v2_2_45_version_is_current_while_preserving_safe_dry_run_subcontract() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert SPREAD_RUNTIME_CONVERSION_BOUNDARY_AUDIT_VERSION == "v2_2_45"
    assert BALLAD_SPREAD_RUNTIME_SAFE_DRY_RUN_VERSION == "v2_2_44"


def test_default_conversion_boundary_audit_is_closed_and_non_converting() -> None:
    audit = spread_runtime_conversion_boundary_audit()
    assert isinstance(audit, SpreadRuntimeConversionBoundaryAudit)
    assert audit.candidate_present is False
    assert audit.conversion_allowed is False
    assert audit.candidate_generator_wiring_allowed is False
    assert audit.style_runtime_wiring_enabled is False
    assert audit.runtime_enabled is False
    assert audit.mappable_field_count >= 2
    assert audit.adapter_required_field_count >= 3
    assert audit.blocked_field_count >= 1
    statuses = {item.status for item in audit.field_audits}
    assert SpreadRuntimeConversionBoundaryStatus.MAPPABLE_NOT_CONVERTED in statuses
    assert SpreadRuntimeConversionBoundaryStatus.REQUIRES_RUNTIME_ADAPTER in statuses
    assert SpreadRuntimeConversionBoundaryStatus.BLOCKED_CURRENT_STAGE in statuses


def test_explicit_ballad_dry_run_candidates_are_audited_but_not_converted() -> None:
    texture_state = VoicingTextureState(
        primary_family=DispositionFamily.SPREAD,
        allowed_families=(DispositionFamily.SPREAD,),
    )
    result = audit_ballad_spread_runtime_conversion_boundaries(
        ("Dm7", "G7", "Cmaj7"),
        _dry_run_policy(),
        texture_state=texture_state,
    )
    assert isinstance(result, BalladSpreadRuntimeConversionBoundaryAuditResult)
    assert result.dry_run_result.dry_run_completed is True
    assert result.selected_candidate_count == 3
    assert result.audit_count == 3
    assert result.conversion_allowed is False
    assert result.runtime_enabled is False
    assert all(audit.candidate_present for audit in result.candidate_audits)
    assert all(audit.candidate_is_legal for audit in result.candidate_audits)
    assert all(audit.conversion_allowed is False for audit in result.candidate_audits)

    first = result.candidate_audits[0]
    assert first.functional_grouping_gap == "runtime_functional_grouping_value_exists"
    debug = first.to_debug_dict()
    assert debug["candidate_summary"]["grouping"] == "1+4"
    assert debug["candidate_conversion_allowed"] is False
    assert debug["candidate_generator_wiring_allowed"] is False
    assert debug["style_runtime_wiring_enabled"] is False
    assert debug["converted_now"] is False


def test_medium_swing_and_bossa_boundary_audit_remain_blocked_by_ballad_gate() -> None:
    for policy in (MediumSwingProfile().voicing_policy, BossaNovaProfile().voicing_policy):
        result = audit_ballad_spread_runtime_conversion_boundaries(("Cmaj7",), policy, explicit_enable=True)
        assert result.dry_run_result.dry_run_completed is False
        assert result.dry_run_result.blocked_reason == "style_not_allowed_for_ballad_spread_pilot"
        assert result.audit_count == 0
        assert result.runtime_enabled is False


def test_default_jazz_ballad_policy_declares_conversion_audit_without_enabling_runtime() -> None:
    policy = JazzBalladProfile().voicing_policy
    metadata = policy.metadata["ballad_spread_runtime_conversion_boundary_audit"]
    assert metadata["version"] == "v2_2_45"
    assert metadata["boundary_audit_enabled"] is True
    assert metadata["conversion_allowed"] is False
    assert metadata["candidate_generator_wiring_allowed"] is False
    assert metadata["style_runtime_wiring_enabled"] is False
    assert metadata["runtime_enabled"] is False


def test_conversion_boundary_debug_and_docs_are_synced() -> None:
    default_debug = spread_runtime_conversion_boundary_debug()
    assert default_debug["spread_runtime_conversion_boundary_audit_version"] == "v2_2_45"
    assert default_debug["default_conversion_allowed"] is False
    assert default_debug["candidate_generator_wiring_allowed"] is False
    assert default_debug["runtime_enabled"] is False

    open_debug = ballad_spread_runtime_conversion_boundary_debug(("Dm7", "G7", "Cmaj7"), _dry_run_policy())
    assert open_debug["result"]["dry_run_completed"] is True
    assert open_debug["result"]["audit_count"] == 3
    assert open_debug["result"]["candidate_conversion_allowed"] is False
    assert open_debug["converted_now"] is False

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
        "Ballad SPREAD Runtime Conversion Boundary Audit",
        "SPREAD_RUNTIME_CONVERSION_BOUNDARY_AUDIT_VERSION",
        "SpreadRuntimeConversionBoundaryStatus",
        "SpreadRuntimeConversionFieldAudit",
        "SpreadRuntimeConversionBoundaryAudit",
        "BalladSpreadRuntimeConversionBoundaryAuditResult",
        "spread_runtime_conversion_boundary_audit",
        "audit_ballad_spread_runtime_conversion_boundaries",
        "spread_runtime_conversion_boundary_debug",
        "ballad_spread_runtime_conversion_boundary_debug",
        "SpreadProjectionCandidate_to_VoicingCandidate_boundary_audit_only",
        "runtime_functional_grouping_value_exists",
        "candidate_conversion_allowed=false",
        "candidate_generator_wiring_allowed=false",
        "style_runtime_wiring_enabled=false",
        "runtime_enabled=false",
        "boundary audit only",
        "Medium Swing and Bossa remain unaffected",
    ]
    for token in required:
        assert token in docs
