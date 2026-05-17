from __future__ import annotations

# harness token: test_v2_2_52_ballad_spread_1plus4_true_isolation

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    BALLAD_SPREAD_1PLUS4_TRUE_ISOLATION_FIX_VERSION,
    BalladSpreadPilotRuntimeEnablementGuardStatus,
    Disposition,
    VoicingPolicy,
    generate_candidates,
    guard_ballad_spread_pilot_runtime_enablement,
)
from jammate_engine.styles.bossa_nova.profile import BossaNovaProfile
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


def _true_isolation_policy(required_recipe_id: str = "spread_1plus4_contract") -> VoicingPolicy:
    return VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        metadata={
            "style": "jazz_ballad",
            "primary_family": "spread",
            "allowed_families": ["spread"],
            "spread_selector_enabled": True,
            "ballad_spread_runtime_pilot": {
                "version": "v2_2_52",
                "enabled": True,
                "scene": "warm_spread_phrase",
                "contract_ids": ["spread_1plus4_contract"],
                "preferred_contract_ids": ["spread_1plus4_contract"],
            },
            "ballad_spread_runtime_safe_dry_run": {
                "version": "v2_2_52",
                "dry_run_enabled": True,
                "candidate_conversion_allowed": True,
            },
            "spread_runtime_adapter_skeleton": {
                "version": "v2_2_52",
                "adapter_conversion_allowed": True,
            },
            "ballad_spread_runtime_candidate_pool": {
                "version": "v2_2_52",
                "candidate_pool_enabled": True,
                "adapter_conversion_allowed": True,
                "candidate_pool_merge_allowed": True,
                "candidate_generator_wiring_allowed": True,
                "fallback_to_existing_pool": True,
            },
            "ballad_spread_pilot_selection_weight_fallback_audit": {
                "version": "v2_2_52",
                "audit_enabled": True,
                "fallback_required": True,
                "max_spread_candidate_share": 0.35,
                "max_spread_score_margin": 0.15,
                "candidate_order_is_selection_priority": False,
            },
            "ballad_spread_pilot_runtime_enablement_guard": {
                "version": "v2_2_52",
                "runtime_guard_enabled": True,
                "listening_isolation_enabled": True,
                "first_listening_isolation_only": True,
            },
            "ballad_spread_1plus4_true_isolation": {
                "version": "v2_2_52",
                "enabled": True,
                "required_recipe_id": required_recipe_id,
                "fallback_only_when_missing": True,
            },
        },
    )


def test_v2_2_52_version_is_current_and_true_isolation_version_is_new() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert BALLAD_SPREAD_1PLUS4_TRUE_ISOLATION_FIX_VERSION == "v2_2_52"


def test_true_isolation_filters_candidate_generator_to_one_1plus4_spread_candidate() -> None:
    policy = _true_isolation_policy()
    candidates = generate_candidates("Dm7", policy)
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.disposition == Disposition.SPREAD
    assert candidate.recipe_id == "spread_1plus4_contract"
    assert candidate.density == 5
    assert len(candidate.notes) == 5
    assert candidate.metadata["converted_from_spread_projection_candidate"] is True
    assert candidate.metadata["ballad_spread_1plus4_true_isolation_enabled"] is True
    assert candidate.metadata["ballad_spread_true_isolation_candidate_pool_mode"] == "spread_only_when_available"
    assert candidate.metadata["fallback_non_spread_pool_retained"] is False


def test_true_isolation_guard_uses_spread_only_when_matching_candidate_exists() -> None:
    result = guard_ballad_spread_pilot_runtime_enablement(
        "Dm7",
        _true_isolation_policy(),
        base_candidates=_base_candidates(),
    )
    assert result.status == BalladSpreadPilotRuntimeEnablementGuardStatus.ENABLED_FOR_LISTENING_ISOLATION
    assert result.reason == "ballad_spread_1plus4_true_isolation_enabled_spread_only_candidate_pool"
    assert len(result.guarded_candidates) == 1
    assert result.guarded_candidates[0].recipe_id == "spread_1plus4_contract"
    assert len(result.guarded_candidates[0].notes) == 5


def test_true_isolation_falls_back_only_when_required_recipe_is_missing() -> None:
    base = _base_candidates()
    result = guard_ballad_spread_pilot_runtime_enablement(
        "Dm7",
        _true_isolation_policy("missing_spread_contract"),
        base_candidates=base,
    )
    assert result.status == BalladSpreadPilotRuntimeEnablementGuardStatus.ENABLED_FOR_LISTENING_ISOLATION
    assert result.reason == "ballad_spread_1plus4_true_isolation_fallback_used_no_matching_spread_candidate"
    assert result.guarded_candidates == base


def test_true_isolation_does_not_open_non_ballad_styles() -> None:
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
        assert result.guarded_candidates == base


def test_demo_script_requests_true_1plus4_isolation() -> None:
    script = _read("examples/scripts/generate_ballad_spread_first_listening_isolation_demo.py")
    assert "v2_2_56_misty_jazz_ballad_spread_1plus3_pilot_demo.mid" in script
    assert "spread_contract_true_isolation" in script
    assert '"required_recipe_id": "spread_1plus3_contract"' in script
