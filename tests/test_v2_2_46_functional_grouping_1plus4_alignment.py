from __future__ import annotations

# harness token: test_v2_2_46_functional_grouping_1plus4_alignment

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    FUNCTIONAL_GROUPING_1PLUS4_CONTRACT_ALIGNMENT_VERSION,
    FunctionalGrouping,
    VoicingGroupRole,
    align_spread_functional_grouping_contract,
    functional_grouping_1plus4_contract_alignment_debug,
    group_indices_for_projection,
)
from jammate_engine.core.voicing.disposition.spread import (
    SpreadFunctionalGroupingContractAlignment,
    SpreadGrouping,
    project_basic_spread_candidates,
    spread_runtime_conversion_boundary_audit,
)
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v2_2_46_version_is_current_and_1plus4_is_core_functional_grouping() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert FUNCTIONAL_GROUPING_1PLUS4_CONTRACT_ALIGNMENT_VERSION == "v2_2_46"
    assert FunctionalGrouping.ONE_PLUS_FOUR.value == "1+4"


def test_projection_map_partitions_1plus4_without_hand_semantics() -> None:
    groups = group_indices_for_projection(
        5,
        FunctionalGrouping.ONE_PLUS_FOUR,
        (VoicingGroupRole.FOUNDATION, VoicingGroupRole.PROJECTION),
    )

    assert groups == {
        "foundation_group": [0],
        "projection_group": [1, 2, 3, 4],
    }
    assert "left_hand" not in groups
    assert "right_hand" not in groups


def test_spread_alignment_contract_reports_runtime_grouping_exists_but_no_conversion() -> None:
    alignment = align_spread_functional_grouping_contract(SpreadGrouping.ONE_PLUS_FOUR)
    assert isinstance(alignment, SpreadFunctionalGroupingContractAlignment)
    assert alignment.spread_grouping == "1+4"
    assert alignment.runtime_grouping == "1+4"
    assert alignment.runtime_grouping_exists is True
    assert alignment.functional_grouping_gap == "runtime_functional_grouping_value_exists"
    assert alignment.group_roles == ("foundation", "projection")
    assert alignment.projection_partition == ((0,), (1, 2, 3, 4))
    assert alignment.projection_map_supported is True
    assert alignment.conversion_allowed is False
    assert alignment.runtime_enabled is False

    debug = functional_grouping_1plus4_contract_alignment_debug()
    assert debug["spread_grouping"] == "1+4"
    assert debug["runtime_grouping_exists"] is True
    assert debug["functional_grouping_gap"] == "runtime_functional_grouping_value_exists"
    assert debug["candidate_conversion_allowed"] is False
    assert debug["converted_now"] is False


def test_conversion_audit_no_longer_reports_1plus4_enum_gap_but_stays_closed() -> None:
    result = project_basic_spread_candidates("Dm7", contract_ids=("spread_1plus4_contract",))[0]
    candidate = result.candidates[0]
    audit = spread_runtime_conversion_boundary_audit(candidate)

    assert audit.functional_grouping_gap == "runtime_functional_grouping_value_exists"
    assert audit.conversion_allowed is False
    assert audit.candidate_generator_wiring_allowed is False
    assert audit.style_runtime_wiring_enabled is False
    assert audit.runtime_enabled is False
    assert "functional_grouping_1plus4_contract_aligned_before_runtime_conversion" in audit.to_debug_dict()["required_future_steps"]


def test_jazz_ballad_policy_declares_1plus4_alignment_without_runtime_enablement() -> None:
    metadata = JazzBalladProfile().voicing_policy.metadata["functional_grouping_1plus4_contract_alignment"]
    assert metadata["version"] == "v2_2_46"
    assert metadata["runtime_grouping_value_exists"] is True
    assert metadata["projection_map_supported"] is True
    assert metadata["candidate_conversion_allowed"] is False
    assert metadata["runtime_enabled"] is False


def test_docs_capture_1plus4_alignment_contract() -> None:
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
        "FunctionalGrouping 1+4 Contract Alignment",
        "FUNCTIONAL_GROUPING_1PLUS4_CONTRACT_ALIGNMENT_VERSION",
        "SpreadFunctionalGroupingContractAlignment",
        "align_spread_functional_grouping_contract",
        "functional_grouping_1plus4_contract_alignment_debug",
        "FunctionalGrouping.ONE_PLUS_FOUR",
        "runtime_functional_grouping_value_exists",
        "foundation_group",
        "projection_group",
        "candidate_conversion_allowed=false",
        "runtime_enabled=false",
        "Medium Swing and Bossa remain unaffected",
    ]
    for token in required:
        assert token in docs
