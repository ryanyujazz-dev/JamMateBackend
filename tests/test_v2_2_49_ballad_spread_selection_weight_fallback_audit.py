from __future__ import annotations

# harness token: test_v2_2_49_ballad_spread_selection_weight_fallback_audit

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    BALLAD_SPREAD_PILOT_SELECTION_WEIGHT_FALLBACK_AUDIT_VERSION,
    BalladSpreadPilotSelectionAuditStatus,
    BalladSpreadPilotSelectionWeightFallbackAuditResult,
    Disposition,
    VoicingPolicy,
    audit_ballad_spread_pilot_selection_weight_and_fallback,
    ballad_spread_pilot_selection_weight_fallback_audit_debug,
    build_ballad_spread_runtime_pilot_candidate_pool,
    generate_candidates,
)
from jammate_engine.styles.bossa_nova.profile import BossaNovaProfile
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile
from jammate_engine.styles.medium_swing.profile import MediumSwingProfile

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _base_candidates() -> tuple:
    return tuple(
        generate_candidates(
            "Dm7",
            VoicingPolicy(
                preferred_disposition=Disposition.OPEN,
                allowed_dispositions=(Disposition.OPEN,),
                metadata={"style": "jazz_ballad"},
            ),
        )
    )


def _explicit_pool_policy(style: str = "jazz_ballad") -> VoicingPolicy:
    return VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
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
            "ballad_spread_runtime_safe_dry_run": {"dry_run_enabled": True},
            "spread_runtime_adapter_skeleton": {"adapter_conversion_allowed": True},
            "ballad_spread_runtime_candidate_pool": {
                "candidate_pool_enabled": True,
                "adapter_conversion_allowed": True,
                "candidate_pool_merge_allowed": True,
                "candidate_generator_wiring_allowed": True,
            },
            "ballad_spread_pilot_selection_weight_fallback_audit": {
                "audit_enabled": True,
                "fallback_required": True,
                "max_spread_candidate_share": 0.35,
                "max_spread_score_margin": 0.15,
                "candidate_order_is_selection_priority": False,
            },
            "ballad_spread_pilot_runtime_enablement_guard": {
                "runtime_guard_enabled": True,
                "listening_isolation_enabled": True,
                "first_listening_isolation_only": True,
            },
        },
    )


def test_v2_2_49_version_is_current_and_selection_audit_version_is_new() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert BALLAD_SPREAD_PILOT_SELECTION_WEIGHT_FALLBACK_AUDIT_VERSION == "v2_2_49"


def test_default_ballad_policy_declares_audit_but_keeps_runtime_unchanged() -> None:
    policy = JazzBalladProfile().voicing_policy
    metadata = policy.metadata["ballad_spread_pilot_selection_weight_fallback_audit"]
    assert metadata["version"] == "v2_2_49"
    assert metadata["audit_enabled"] is True
    assert metadata["fallback_required"] is True
    assert metadata["candidate_order_is_selection_priority"] is False
    assert metadata["style_runtime_default_enabled"] is False
    assert metadata["runtime_enabled"] is False

    result = audit_ballad_spread_pilot_selection_weight_and_fallback(
        "Dm7",
        policy,
        base_candidates=_base_candidates(),
    )
    assert result.status == BalladSpreadPilotSelectionAuditStatus.DEFAULT_DISABLED
    assert result.pool_result.candidate_pool_integrated is False
    assert result.fallback_retained is True
    assert result.dominance_risk is False
    assert result.runtime_enabled is False


def test_explicit_pilot_pool_is_audited_as_fallback_protected_not_order_priority() -> None:
    base = _base_candidates()
    result = audit_ballad_spread_pilot_selection_weight_and_fallback(
        "Dm7",
        _explicit_pool_policy(),
        base_candidates=base,
    )
    assert isinstance(result, BalladSpreadPilotSelectionWeightFallbackAuditResult)
    assert result.status == BalladSpreadPilotSelectionAuditStatus.FALLBACK_PROTECTED
    assert result.pool_result.candidate_pool_integrated is True
    assert result.spread_candidate_count == 1
    assert result.fallback_candidate_count == len(base)
    assert result.fallback_retained is True
    assert result.spread_candidates_prepend_fallback is True
    assert result.plan.candidate_order_is_selection_priority is False
    assert result.dominance_risk is False
    assert result.fallback_protected is True
    assert result.spread_candidate_share <= result.plan.max_spread_candidate_share
    assert result.score_margin_vs_fallback is not None
    assert result.score_margin_vs_fallback <= result.plan.max_spread_score_margin

    pool = build_ballad_spread_runtime_pilot_candidate_pool("Dm7", _explicit_pool_policy(), base_candidates=base)
    spread_candidate = pool.spread_candidates[0]
    assert spread_candidate.metadata["ballad_spread_pilot_selection_weight_fallback_audit_version"] == "v2_2_49"
    assert spread_candidate.metadata["selection_weight_fallback_audit_required"] is True
    assert spread_candidate.metadata["candidate_order_is_selection_priority"] is False
    assert spread_candidate.metadata["spread_pilot_weight_role"] == "secondary_pilot_candidate_not_default_replacement"


def test_audit_detects_artificial_spread_dominance_risk_without_runtime_selection() -> None:
    base = _base_candidates()
    result = audit_ballad_spread_pilot_selection_weight_and_fallback(
        "Dm7",
        _explicit_pool_policy(),
        base_candidates=base,
        max_spread_candidate_share=0.01,
    )
    assert result.status == BalladSpreadPilotSelectionAuditStatus.SPREAD_DOMINANCE_RISK
    assert result.dominance_risk is True
    debug = result.to_debug_dict()
    assert debug["candidate_selection_not_performed"] is True
    assert debug["selector_scoring_still_authoritative"] is True
    assert debug["runtime_enabled"] is False


def test_medium_swing_and_bossa_are_still_blocked_by_style_gate() -> None:
    base = _base_candidates()
    for policy in (MediumSwingProfile().voicing_policy, BossaNovaProfile().voicing_policy):
        result = audit_ballad_spread_pilot_selection_weight_and_fallback(
            "Dm7",
            policy,
            base_candidates=base,
            enabled=True,
            allow_conversion=True,
            allow_pool_merge=True,
        )
        assert result.status == BalladSpreadPilotSelectionAuditStatus.STYLE_BLOCKED
        assert result.pool_result.candidate_pool_integrated is False
        assert result.runtime_enabled is False


def test_debug_surface_and_docs_are_synced() -> None:
    closed_debug = ballad_spread_pilot_selection_weight_fallback_audit_debug(
        "Dm7",
        JazzBalladProfile().voicing_policy,
        base_candidates=_base_candidates(),
    )
    assert closed_debug["ballad_spread_pilot_selection_weight_fallback_audit_version"] == "v2_2_49"
    assert closed_debug["result"]["status"] == "default_disabled"
    assert closed_debug["candidate_selection_not_performed"] is True
    assert closed_debug["default_style_runtime_unchanged"] is True

    explicit_debug = ballad_spread_pilot_selection_weight_fallback_audit_debug(
        "Dm7",
        _explicit_pool_policy(),
        base_candidates=_base_candidates(),
    )
    assert explicit_debug["fallback_protected"] is True
    assert explicit_debug["dominance_risk"] is False
    assert explicit_debug["result"]["candidate_order_warning"] is True

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
        "Ballad SPREAD Pilot Selection Weight + Fallback Audit",
        "BALLAD_SPREAD_PILOT_SELECTION_WEIGHT_FALLBACK_AUDIT_VERSION",
        "BalladSpreadPilotSelectionAuditStatus",
        "BalladSpreadPilotSelectionWeightPlan",
        "BalladSpreadPilotSelectionWeightFallbackAuditResult",
        "audit_ballad_spread_pilot_selection_weight_and_fallback",
        "ballad_spread_pilot_selection_weight_fallback_audit_debug",
        "fallback_required=true",
        "candidate_order_is_selection_priority=false",
        "selector_scoring_still_authoritative=true",
        "candidate_selection_not_performed=true",
        "Medium Swing and Bossa remain unaffected",
    ]
    for token in required:
        assert token in docs
