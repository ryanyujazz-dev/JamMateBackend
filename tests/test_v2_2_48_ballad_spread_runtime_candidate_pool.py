from __future__ import annotations

# harness token: test_v2_2_48_ballad_spread_runtime_candidate_pool

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    BALLAD_SPREAD_RUNTIME_CANDIDATE_POOL_INTEGRATION_VERSION,
    BalladSpreadRuntimeCandidatePoolResult,
    BalladSpreadRuntimeCandidatePoolStatus,
    Disposition,
    VoicingPolicy,
    ballad_spread_runtime_candidate_pool_debug,
    build_ballad_spread_runtime_pilot_candidate_pool,
    generate_candidates,
)
from jammate_engine.styles.bossa_nova.profile import BossaNovaProfile
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile
from jammate_engine.styles.medium_swing.profile import MediumSwingProfile

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


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
            "ballad_spread_runtime_safe_dry_run": {
                "dry_run_enabled": True,
            },
            "spread_runtime_adapter_skeleton": {
                "adapter_conversion_allowed": True,
            },
            "ballad_spread_runtime_candidate_pool": {
                "candidate_pool_enabled": True,
                "adapter_conversion_allowed": True,
                "candidate_pool_merge_allowed": True,
                "candidate_generator_wiring_allowed": True,
            },
            "ballad_spread_pilot_runtime_enablement_guard": {
                "runtime_guard_enabled": True,
                "listening_isolation_enabled": True,
                "first_listening_isolation_only": True,
            },
        },
    )


def test_v2_2_48_version_is_current_and_candidate_pool_version_is_new() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert BALLAD_SPREAD_RUNTIME_CANDIDATE_POOL_INTEGRATION_VERSION == "v2_2_48"


def test_default_ballad_policy_declares_candidate_pool_but_keeps_it_closed() -> None:
    policy = JazzBalladProfile().voicing_policy
    metadata = policy.metadata["ballad_spread_runtime_candidate_pool"]
    assert metadata["version"] == "v2_2_48"
    assert metadata["candidate_pool_enabled"] is False
    assert metadata["adapter_conversion_allowed"] is False
    assert metadata["candidate_pool_merge_allowed"] is False
    assert metadata["candidate_generator_wiring_allowed"] is False
    assert metadata["fallback_to_existing_pool"] is True
    assert metadata["default_style_runtime_unchanged"] is True

    base = tuple(generate_candidates("Dm7", VoicingPolicy(preferred_disposition=Disposition.OPEN, allowed_dispositions=(Disposition.OPEN,), metadata={"style": "jazz_ballad"})))
    result = build_ballad_spread_runtime_pilot_candidate_pool("Dm7", policy, base_candidates=base)
    assert result.status == BalladSpreadRuntimeCandidatePoolStatus.DEFAULT_DISABLED
    assert result.spread_candidate_count == 0
    assert result.merged_candidates == base
    assert result.candidate_pool_integrated is False


def test_explicit_ballad_pool_adds_spread_candidate_while_retaining_existing_pool() -> None:
    base = tuple(generate_candidates("Dm7", VoicingPolicy(preferred_disposition=Disposition.OPEN, allowed_dispositions=(Disposition.OPEN,), metadata={"style": "jazz_ballad"})))
    result = build_ballad_spread_runtime_pilot_candidate_pool("Dm7", _explicit_pool_policy(), base_candidates=base)
    assert isinstance(result, BalladSpreadRuntimeCandidatePoolResult)
    assert result.status == BalladSpreadRuntimeCandidatePoolStatus.PILOT_CANDIDATES_INTEGRATED
    assert result.spread_candidate_count == 1
    assert result.merged_candidate_count == len(base) + 1
    assert tuple(result.merged_candidates[-len(base):]) == base

    spread_candidate = result.spread_candidates[0]
    assert spread_candidate.disposition == Disposition.SPREAD
    assert spread_candidate.metadata["ballad_spread_runtime_pilot_pool_candidate"] is True
    assert spread_candidate.metadata["ballad_spread_runtime_candidate_pool_integration_version"] == "v2_2_48"
    assert spread_candidate.metadata["fallback_non_spread_pool_retained"] is True
    assert spread_candidate.metadata["candidate_generator_wiring_allowed"] is True
    assert spread_candidate.metadata["default_style_runtime_unchanged"] is True


def test_candidate_generator_only_merges_pilot_pool_when_explicitly_enabled() -> None:
    default_policy = VoicingPolicy(preferred_disposition=Disposition.OPEN, allowed_dispositions=(Disposition.OPEN,), metadata={"style": "jazz_ballad"})
    default_candidates = generate_candidates("Dm7", default_policy)
    assert not any(candidate.metadata.get("ballad_spread_runtime_pilot_pool_candidate") for candidate in default_candidates)

    explicit_candidates = generate_candidates("Dm7", _explicit_pool_policy())
    pilot_candidates = [candidate for candidate in explicit_candidates if candidate.metadata.get("ballad_spread_runtime_pilot_pool_candidate")]
    fallback_candidates = [candidate for candidate in explicit_candidates if not candidate.metadata.get("ballad_spread_runtime_pilot_pool_candidate")]
    assert len(pilot_candidates) == 1
    assert fallback_candidates
    assert pilot_candidates[0].disposition == Disposition.SPREAD
    assert all(candidate.disposition == Disposition.OPEN for candidate in fallback_candidates)


def test_medium_swing_and_bossa_remain_blocked_even_with_explicit_arguments() -> None:
    base = tuple(generate_candidates("Cmaj7", VoicingPolicy(preferred_disposition=Disposition.OPEN, allowed_dispositions=(Disposition.OPEN,))))
    for policy in (MediumSwingProfile().voicing_policy, BossaNovaProfile().voicing_policy):
        result = build_ballad_spread_runtime_pilot_candidate_pool(
            "Cmaj7",
            policy,
            base_candidates=base,
            enabled=True,
            allow_conversion=True,
            allow_pool_merge=True,
        )
        assert result.status == BalladSpreadRuntimeCandidatePoolStatus.STYLE_BLOCKED
        assert result.spread_candidate_count == 0
        assert result.merged_candidates == base
        assert result.candidate_pool_integrated is False


def test_debug_surfaces_and_docs_are_synced() -> None:
    closed_debug = ballad_spread_runtime_candidate_pool_debug("Dm7", JazzBalladProfile().voicing_policy)
    assert closed_debug["ballad_spread_runtime_candidate_pool_integration_version"] == "v2_2_48"
    assert closed_debug["candidate_pool_integrated"] is False
    assert closed_debug["result"]["status"] == "default_disabled"
    assert closed_debug["default_style_runtime_unchanged"] is True

    explicit_debug = ballad_spread_runtime_candidate_pool_debug("Dm7", _explicit_pool_policy())
    assert explicit_debug["candidate_pool_integrated"] is True
    assert explicit_debug["result"]["spread_candidate_count"] == 1
    assert explicit_debug["result"]["fallback_to_existing_pool"] is True

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
        "Ballad SPREAD Runtime Pilot Candidate Pool Integration",
        "BALLAD_SPREAD_RUNTIME_CANDIDATE_POOL_INTEGRATION_VERSION",
        "BalladSpreadRuntimeCandidatePoolStatus",
        "BalladSpreadRuntimeCandidatePoolPlan",
        "BalladSpreadRuntimeCandidatePoolResult",
        "ballad_spread_runtime_candidate_pool_plan",
        "build_ballad_spread_runtime_pilot_candidate_pool",
        "ballad_spread_runtime_candidate_pool_debug",
        "candidate_pool_enabled=false",
        "candidate_pool_merge_allowed=false",
        "fallback_to_existing_pool=true",
        "default_style_runtime_unchanged=true",
        "Medium Swing and Bossa remain unaffected",
    ]
    for token in required:
        assert token in docs
