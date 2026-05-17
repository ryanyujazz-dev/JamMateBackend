from __future__ import annotations

# harness token: test_v2_2_38_spread_recipe_reuse_contract

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.disposition.spread import (
    SPREAD_RECIPE_CONTRACT_VERSION,
    SpreadGrouping,
    SpreadReuseStatus,
    SpreadUpperSourceKind,
    spread_recipe_contract_debug,
    spread_recipe_contract_skeleton,
    spread_recipe_reuse_audit,
)

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v2_2_38_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert SPREAD_RECIPE_CONTRACT_VERSION == "v2_2_40"


def test_spread_reuse_audit_prefers_existing_resources_and_forbids_final_results() -> None:
    audit = spread_recipe_reuse_audit()
    by_id = {item.resource_id: item for item in audit}

    assert by_id["three_note_content_source_inventory"].status == SpreadReuseStatus.ADAPTER_REQUIRED
    assert "content_planner" in by_id["three_note_content_source_inventory"].owner_path
    assert by_id["four_note_source_orientation_inventory"].status == SpreadReuseStatus.ADAPTER_REQUIRED
    assert "four_note_sources" in by_id["four_note_source_orientation_inventory"].owner_path
    assert by_id["drop_family_projection_resource"].reusable_level == "projection_resource_only"
    assert "disposition.open" in by_id["drop_family_projection_resource"].owner_path
    assert by_id["color_permission_policy"].status == SpreadReuseStatus.REUSE_READY

    forbidden = by_id["final_closed_or_open_voicing_candidate"]
    assert forbidden.status == SpreadReuseStatus.NOT_REUSABLE
    assert forbidden.final_placed_result_reuse_allowed is False


def test_spread_contract_skeleton_covers_lower_upper_groupings_without_runtime_enablement() -> None:
    contracts = spread_recipe_contract_skeleton()
    by_group = {contract.grouping: contract for contract in contracts}

    assert set(by_group) == {
        SpreadGrouping.ONE_PLUS_THREE,
        SpreadGrouping.TWO_PLUS_TWO,
        SpreadGrouping.ONE_PLUS_FOUR,
        SpreadGrouping.TWO_PLUS_THREE,
        SpreadGrouping.TWO_PLUS_FOUR,
        SpreadGrouping.THREE_PLUS_THREE,
        SpreadGrouping.THREE_PLUS_FOUR,
    }

    one_four = by_group[SpreadGrouping.ONE_PLUS_FOUR]
    assert one_four.density == 5
    assert one_four.lower_group.degree_role_contract == ("root",)
    assert one_four.upper_source.kind == SpreadUpperSourceKind.DROP_FAMILY_DERIVED_PROJECTION_BLOCK
    assert one_four.upper_source.projection_methods == ("DROP2", "DROP3")
    assert one_four.upper_source.final_placed_result_reuse_allowed is False

    for contract in contracts:
        assert contract.notes_only is True
        assert contract.runtime_enabled is False
        assert contract.expression_allowed_in_this_layer is False
        assert contract.owns_group_register_gap_span is True
        assert contract.owns_groupwise_voice_leading is True
        assert contract.lower_group.requires_within_octave is True
        assert contract.upper_source.adapter_required is True


def test_spread_contract_debug_is_metadata_first_and_notes_only() -> None:
    debug = spread_recipe_contract_debug()
    assert debug["contract_version"] == "v2_2_40"
    assert debug["layer"] == "core.voicing.disposition.spread"
    assert debug["runtime_enabled"] is False
    assert debug["notes_only"] is True
    assert debug["no_expression_or_pedal"] is True
    assert len(debug["reuse_audit"]) >= 5
    assert len(debug["recipe_contracts"]) == 7


def test_spread_recipe_reuse_contract_is_documented_and_harnessed() -> None:
    docs = "\n".join(
        _read(rel)
        for rel in (
            "agent.md",
            "README.md",
            "docs/VOICING_SYSTEM_V2_DESIGN.md",
            "docs/VOICING_MODULE_CORE_LOGIC_V2.md",
            "docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md",
            "docs/DEVELOPMENT_TASK_PLAN_V2.md",
            "docs/DEVELOPMENT_HARNESS_V2.md",
        )
    )
    required = [
        "Spread Recipe Reuse Audit + Contract Skeleton",
        "SPREAD_RECIPE_CONTRACT_VERSION",
        "SpreadRecipeContract",
        "LowerGroupRecipeContract",
        "UpperSourceRef",
        "SpreadReuseAuditItem",
        "spread_recipe_reuse_audit",
        "spread_recipe_contract_skeleton",
        "source/orientation/projection",
        "final placed closed/open",
        "notes-only",
        "DROP2/DROP3",
    ]
    for token in required:
        assert token in docs
