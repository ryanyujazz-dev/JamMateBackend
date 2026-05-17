from __future__ import annotations

# harness token: test_v2_2_50_ballad_spread_runtime_enablement_guard

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    BALLAD_SPREAD_PILOT_RUNTIME_ENABLEMENT_GUARD_VERSION,
    BalladSpreadPilotRuntimeEnablementGuardResult,
    BalladSpreadPilotRuntimeEnablementGuardStatus,
    Disposition,
    VoicingPolicy,
    ballad_spread_pilot_runtime_enablement_guard_debug,
    generate_candidates,
    guard_ballad_spread_pilot_runtime_enablement,
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


def _pilot_pool_policy(*, guard: bool, isolation: bool, style: str = "jazz_ballad") -> VoicingPolicy:
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
                "runtime_guard_enabled": guard,
                "listening_isolation_enabled": isolation,
                "first_listening_isolation_only": True,
            },
        },
    )


def test_v2_2_50_version_is_current_and_guard_version_is_new() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert BALLAD_SPREAD_PILOT_RUNTIME_ENABLEMENT_GUARD_VERSION == "v2_2_50"


def test_default_ballad_policy_declares_guard_but_keeps_runtime_closed() -> None:
    policy = JazzBalladProfile().voicing_policy
    metadata = policy.metadata["ballad_spread_pilot_runtime_enablement_guard"]
    assert metadata["version"] == "v2_2_50"
    assert metadata["runtime_guard_enabled"] is False
    assert metadata["listening_isolation_enabled"] is False
    assert metadata["style_runtime_default_enabled"] is False
    assert metadata["runtime_pilot_enabled"] is False

    result = guard_ballad_spread_pilot_runtime_enablement("Dm7", policy, base_candidates=_base_candidates())
    assert result.status == BalladSpreadPilotRuntimeEnablementGuardStatus.DEFAULT_DISABLED
    assert result.enabled_for_listening_isolation is False
    assert result.runtime_pilot_enabled is False
    assert result.guarded_candidates == _base_candidates()


def test_candidate_pool_flags_alone_do_not_enter_runtime_candidate_generation() -> None:
    policy_without_guard = _pilot_pool_policy(guard=False, isolation=False)
    candidates = generate_candidates("Dm7", policy_without_guard)
    assert not any(candidate.metadata.get("ballad_spread_first_listening_isolation_candidate") for candidate in candidates)
    assert not any(candidate.metadata.get("ballad_spread_runtime_pilot_enabled") for candidate in candidates)

    result = guard_ballad_spread_pilot_runtime_enablement("Dm7", policy_without_guard, base_candidates=_base_candidates())
    assert result.status == BalladSpreadPilotRuntimeEnablementGuardStatus.DEFAULT_DISABLED
    assert result.runtime_pilot_enabled is False


def test_guard_and_listening_isolation_enable_one_spread_candidate_with_fallback_retained() -> None:
    policy = _pilot_pool_policy(guard=True, isolation=True)
    result = guard_ballad_spread_pilot_runtime_enablement("Dm7", policy, base_candidates=_base_candidates())
    assert isinstance(result, BalladSpreadPilotRuntimeEnablementGuardResult)
    assert result.status == BalladSpreadPilotRuntimeEnablementGuardStatus.ENABLED_FOR_LISTENING_ISOLATION
    assert result.enabled_for_listening_isolation is True
    assert result.runtime_pilot_enabled is True
    assert result.spread_candidate_count == 1
    assert result.fallback_candidate_count == len(_base_candidates())
    assert result.fallback_retained is True

    generated = generate_candidates("Dm7", policy)
    pilot_candidates = [candidate for candidate in generated if candidate.metadata.get("ballad_spread_first_listening_isolation_candidate")]
    fallback_candidates = [candidate for candidate in generated if not candidate.metadata.get("ballad_spread_first_listening_isolation_candidate")]
    assert len(pilot_candidates) == 1
    assert fallback_candidates
    assert pilot_candidates[0].disposition == Disposition.SPREAD
    assert pilot_candidates[0].metadata["ballad_spread_pilot_runtime_enablement_guard_version"] == "v2_2_50"
    assert pilot_candidates[0].metadata["style_runtime_default_enabled"] is False
    assert pilot_candidates[0].metadata["fallback_non_spread_pool_retained"] is True


def test_listening_isolation_flag_is_required_separately_from_guard() -> None:
    result = guard_ballad_spread_pilot_runtime_enablement(
        "Dm7",
        _pilot_pool_policy(guard=True, isolation=False),
        base_candidates=_base_candidates(),
    )
    assert result.status == BalladSpreadPilotRuntimeEnablementGuardStatus.LISTENING_ISOLATION_REQUIRED
    assert result.guarded_candidates == _base_candidates()
    assert result.runtime_pilot_enabled is False


def test_medium_swing_and_bossa_are_still_blocked_even_with_guard_like_metadata() -> None:
    base = _base_candidates()
    for policy in (MediumSwingProfile().voicing_policy, BossaNovaProfile().voicing_policy):
        result = guard_ballad_spread_pilot_runtime_enablement(
            "Dm7",
            policy,
            base_candidates=base,
            runtime_guard_enabled=True,
            listening_isolation_enabled=True,
        )
        assert result.status == BalladSpreadPilotRuntimeEnablementGuardStatus.STYLE_BLOCKED
        assert result.enabled_for_listening_isolation is False
        assert result.guarded_candidates == base


def test_debug_surface_demo_script_and_docs_are_synced() -> None:
    debug = ballad_spread_pilot_runtime_enablement_guard_debug("Dm7", _pilot_pool_policy(guard=True, isolation=True), base_candidates=_base_candidates())
    assert debug["ballad_spread_pilot_runtime_enablement_guard_version"] == "v2_2_50"
    assert debug["enabled_for_listening_isolation"] is True
    assert debug["runtime_pilot_enabled"] is True
    assert debug["fallback_retained"] is True

    script = _read("examples/scripts/generate_ballad_spread_first_listening_isolation_demo.py")
    assert "v2_2_56_misty_jazz_ballad_spread_1plus3_pilot_demo.mid" in script
    assert "ballad_spread_pilot_runtime_enablement_guard" in script

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
        "Ballad SPREAD Pilot Runtime Enablement Guard + First Listening Isolation",
        "BALLAD_SPREAD_PILOT_RUNTIME_ENABLEMENT_GUARD_VERSION",
        "BalladSpreadPilotRuntimeEnablementGuardStatus",
        "BalladSpreadPilotRuntimeEnablementGuardPlan",
        "BalladSpreadPilotRuntimeEnablementGuardResult",
        "guard_ballad_spread_pilot_runtime_enablement",
        "ballad_spread_pilot_runtime_enablement_guard_debug",
        "runtime_guard_enabled=false",
        "listening_isolation_enabled=false",
        "first_listening_isolation_only=true",
        "Medium Swing and Bossa remain unaffected",
    ]
    for token in required:
        assert token in docs
