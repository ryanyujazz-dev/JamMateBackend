from __future__ import annotations

# harness token: test_v2_2_47_spread_runtime_adapter_skeleton

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION,
    FunctionalGrouping,
    VoicingCandidate,
    VoicingGroupRole,
    spread_projection_candidate_to_voicing_candidate_adapter,
    spread_runtime_adapter_skeleton_debug,
    run_ballad_spread_runtime_adapter_skeleton,
    ballad_spread_runtime_adapter_skeleton_debug,
)
from jammate_engine.core.voicing.disposition.models import DispositionFamily
from jammate_engine.core.voicing.disposition.spread import (
    SpreadRuntimeAdapterResult,
    SpreadRuntimeAdapterStatus,
    project_basic_spread_candidates,
)
from jammate_engine.core.voicing.policy import Disposition, VoicingPolicy
from jammate_engine.core.voicing.runtime.texture_plan import VoicingTextureState
from jammate_engine.styles.bossa_nova.profile import BossaNovaProfile
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile
from jammate_engine.styles.medium_swing.profile import MediumSwingProfile

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _candidate():
    result = project_basic_spread_candidates("Dm7", contract_ids=("spread_1plus4_contract",), max_upper_options=1)[0]
    return result.candidates[0]


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
            "spread_runtime_adapter_skeleton": {
                "adapter_conversion_allowed": True,
            },
        }
    )


def test_v2_2_47_version_is_current_and_adapter_version_is_new() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION == "v2_2_47"


def test_adapter_is_blocked_by_default_and_does_not_create_runtime_candidate() -> None:
    result = spread_projection_candidate_to_voicing_candidate_adapter(_candidate())
    assert isinstance(result, SpreadRuntimeAdapterResult)
    assert result.status == SpreadRuntimeAdapterStatus.DEFAULT_BLOCKED
    assert result.converted is False
    assert result.adapted_candidate is None
    assert result.conversion_allowed is False
    assert result.candidate_generator_wiring_allowed is False
    assert result.style_runtime_wiring_enabled is False
    assert result.runtime_enabled is False


def test_explicit_adapter_conversion_preserves_spread_metadata_without_runtime_wiring() -> None:
    source = _candidate()
    result = spread_projection_candidate_to_voicing_candidate_adapter(source, allow_conversion=True, score=123.0)
    assert result.status == SpreadRuntimeAdapterStatus.ADAPTED_SKELETON_ONLY
    assert result.converted is True
    assert result.conversion_allowed is True
    assert result.candidate_generator_wiring_allowed is False
    assert result.style_runtime_wiring_enabled is False
    assert result.runtime_enabled is False

    adapted = result.adapted_candidate
    assert isinstance(adapted, VoicingCandidate)
    assert adapted.notes == list(source.notes)
    assert adapted.degrees == list(source.degrees)
    assert adapted.score == 123.0
    assert adapted.disposition == Disposition.SPREAD
    assert adapted.functional_grouping == FunctionalGrouping.ONE_PLUS_FOUR
    assert adapted.group_roles == (VoicingGroupRole.FOUNDATION, VoicingGroupRole.PROJECTION)
    assert adapted.recipe_id == "spread_1plus4_contract"
    assert adapted.metadata["spread_runtime_adapter_skeleton_version"] == "v2_2_47"
    assert adapted.metadata["source_candidate_metadata_preserved"] is True
    assert adapted.metadata["candidate_generator_wiring_allowed"] is False
    assert adapted.metadata["style_runtime_wiring_enabled"] is False
    assert adapted.metadata["runtime_enabled"] is False
    assert adapted.metadata["projection_map"]["foundation_group"] == [0]
    assert adapted.metadata["projection_map"]["projection_group"] == [1, 2, 3, 4]


def test_ballad_safe_dry_run_can_run_adapter_skeleton_only_when_explicit() -> None:
    texture_state = VoicingTextureState(
        primary_family=DispositionFamily.SPREAD,
        allowed_families=(DispositionFamily.SPREAD,),
    )
    result = run_ballad_spread_runtime_adapter_skeleton(
        ["Dm7", "G7", "Cmaj7"],
        _dry_run_policy(),
        texture_state=texture_state,
    )
    assert result.dry_run_result.dry_run_completed is True
    assert result.selected_candidate_count == 3
    assert result.adapted_candidate_count == 3
    assert result.conversion_allowed is True
    assert result.runtime_enabled is False
    assert all(item.status == SpreadRuntimeAdapterStatus.ADAPTED_SKELETON_ONLY for item in result.adapter_results)
    assert all(item.candidate_generator_wiring_allowed is False for item in result.adapter_results)


def test_medium_swing_and_bossa_remain_blocked_by_ballad_gate() -> None:
    for policy in (MediumSwingProfile().voicing_policy, BossaNovaProfile().voicing_policy):
        result = run_ballad_spread_runtime_adapter_skeleton(
            ["Cmaj7"],
            policy,
            explicit_enable=True,
            allow_conversion=True,
        )
        assert result.dry_run_result.dry_run_completed is False
        assert result.selected_candidate_count == 0
        assert result.adapted_candidate_count == 0
        assert result.runtime_enabled is False


def test_jazz_ballad_policy_declares_adapter_skeleton_without_enabling_runtime() -> None:
    metadata = JazzBalladProfile().voicing_policy.metadata["spread_runtime_adapter_skeleton"]
    assert metadata["version"] == "v2_2_47"
    assert metadata["adapter_skeleton_exists"] is True
    assert metadata["adapter_conversion_allowed"] is False
    assert metadata["candidate_generator_wiring_allowed"] is False
    assert metadata["style_runtime_wiring_enabled"] is False
    assert metadata["runtime_enabled"] is False


def test_debug_surfaces_and_docs_are_synced() -> None:
    default_debug = spread_runtime_adapter_skeleton_debug()
    assert default_debug["spread_runtime_adapter_skeleton_version"] == "v2_2_47"
    assert default_debug["default_conversion_allowed"] is False
    assert default_debug["runtime_enabled"] is False
    assert default_debug["adapter"]["status"] == "default_blocked"

    explicit_debug = spread_runtime_adapter_skeleton_debug(allow_conversion=True)
    assert explicit_debug["adapter"]["status"] == "adapted_skeleton_only"
    assert explicit_debug["adapter"]["candidate_generator_wiring_allowed"] is False
    assert explicit_debug["adapter"]["style_runtime_wiring_enabled"] is False

    ballad_debug = ballad_spread_runtime_adapter_skeleton_debug(
        ("Dm7", "G7", "Cmaj7"),
        _dry_run_policy(),
        allow_conversion=True,
    )
    assert ballad_debug["result"]["adapted_candidate_count"] == 3
    assert ballad_debug["runtime_enabled"] is False

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
        "SPREAD Runtime Adapter Skeleton",
        "SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION",
        "SpreadRuntimeAdapterStatus",
        "SpreadRuntimeAdapterFieldMapping",
        "SpreadRuntimeAdapterResult",
        "BalladSpreadRuntimeAdapterSkeletonResult",
        "spread_projection_candidate_to_voicing_candidate_adapter",
        "run_ballad_spread_runtime_adapter_skeleton",
        "spread_runtime_adapter_skeleton_debug",
        "ballad_spread_runtime_adapter_skeleton_debug",
        "SpreadProjectionCandidate_to_VoicingCandidate_adapter_skeleton_only",
        "candidate_generator_wiring_allowed=false",
        "style_runtime_wiring_enabled=false",
        "runtime_enabled=false",
        "adapter skeleton only",
        "Medium Swing and Bossa remain unaffected",
    ]
    for token in required:
        assert token in docs
