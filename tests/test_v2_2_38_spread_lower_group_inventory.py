from __future__ import annotations

# harness token: test_v2_2_38_spread_lower_group_inventory

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.disposition.spread import (
    LOWER_GROUP_INVENTORY_VERSION,
    SPREAD_RECIPE_CONTRACT_VERSION,
    LowerGroupRecipeId,
    instantiate_lower_group_recipe,
    lower_group_inventory_debug,
    lower_group_recipe_inventory,
    place_lower_group_recipe,
)

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v2_2_38_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert SPREAD_RECIPE_CONTRACT_VERSION == "v2_2_40"
    assert LOWER_GROUP_INVENTORY_VERSION == "v2_2_38"


def test_lower_group_inventory_contains_exact_planned_recipe_set() -> None:
    inventory = lower_group_recipe_inventory()
    by_id = {item.recipe_id: item for item in inventory}

    assert set(by_id) == {
        LowerGroupRecipeId.ROOT,
        LowerGroupRecipeId.ROOT_SEVENTH,
        LowerGroupRecipeId.ROOT_THIRD,
        LowerGroupRecipeId.ROOT_FIFTH,
        LowerGroupRecipeId.THIRD_SEVENTH,
        LowerGroupRecipeId.ROOT_FIFTH_UPPER_ROOT,
        LowerGroupRecipeId.ROOT_THIRD_SEVENTH,
        LowerGroupRecipeId.ROOT_SEVENTH_UPPER_THIRD,
        LowerGroupRecipeId.ROOT_FIFTH_UPPER_THIRD,
    }

    assert by_id[LowerGroupRecipeId.ROOT].role_contract == ("root",)
    assert by_id[LowerGroupRecipeId.ROOT_SEVENTH].role_contract == ("root", "seventh")
    assert by_id[LowerGroupRecipeId.ROOT_THIRD].role_contract == ("root", "third")
    assert by_id[LowerGroupRecipeId.ROOT_FIFTH].role_contract == ("root", "fifth")
    assert by_id[LowerGroupRecipeId.THIRD_SEVENTH].role_contract == ("third", "seventh")
    assert by_id[LowerGroupRecipeId.ROOT_FIFTH_UPPER_ROOT].role_contract == ("root", "fifth", "upper_root")
    assert by_id[LowerGroupRecipeId.ROOT_THIRD_SEVENTH].role_contract == ("root", "third", "seventh")
    assert by_id[LowerGroupRecipeId.ROOT_SEVENTH_UPPER_THIRD].role_contract == ("root", "seventh", "upper3")
    assert by_id[LowerGroupRecipeId.ROOT_FIFTH_UPPER_THIRD].role_contract == ("root", "fifth", "upper3")

    for item in inventory:
        assert item.group_role == "lower/foundation"
        if item.note_count == 3:
            assert item.requires_within_octave is False
            assert item.max_span_semitones == 16
        else:
            assert item.requires_within_octave is True
            assert item.max_span_semitones == 12
        assert item.runtime_enabled is False
        assert item.implementation_status == "implemented_inventory_notes_only"


def test_lower_group_instances_resolve_chord_quality_via_harmony_material() -> None:
    major = instantiate_lower_group_recipe("Cmaj7", LowerGroupRecipeId.ROOT_SEVENTH_UPPER_THIRD)
    assert major.degree_names == ("R", "7", "3")
    assert major.role_names == ("root", "seventh", "upper3")
    assert major.relative_semitones == (0, 11, 16)

    half_dim = instantiate_lower_group_recipe("Bm7b5", LowerGroupRecipeId.ROOT_THIRD_SEVENTH)
    assert half_dim.degree_names == ("R", "b3", "b7")
    assert half_dim.relative_semitones == (0, 3, 10)

    dim7 = instantiate_lower_group_recipe("Cdim7", LowerGroupRecipeId.ROOT_THIRD_SEVENTH)
    assert dim7.degree_names == ("R", "b3", "bb7")
    assert dim7.relative_semitones == (0, 3, 9)


def test_lower_group_placement_enforces_one_octave_and_register_guard() -> None:
    for recipe in lower_group_recipe_inventory():
        placement = place_lower_group_recipe("Cmaj7", recipe.recipe_id, 36, 60, target_low=36)
        assert placement.is_legal is True
        assert placement.span_semitones <= recipe.max_span_semitones
        assert all(36 <= note <= 60 for note in placement.notes)
        assert placement.metadata["lower_group_recipe_id"] == recipe.recipe_id.value
        assert placement.metadata["lower_group_note_count"] == recipe.note_count
        assert placement.metadata["lower_group_requires_within_octave"] is recipe.requires_within_octave
        assert placement.metadata["notes_only"] is True
        assert placement.metadata["no_expression_or_pedal"] is True
        assert placement.metadata["runtime_enabled"] is False

    octave_recipe = place_lower_group_recipe("Cmaj7", LowerGroupRecipeId.ROOT_FIFTH_UPPER_ROOT, 36, 60)
    assert octave_recipe.placed_degrees == (("R", 36), ("5", 43), ("R", 48))
    assert octave_recipe.span_semitones == 12


def test_lower_group_inventory_marks_unavailable_seventh_recipe_for_plain_triad() -> None:
    unavailable = instantiate_lower_group_recipe("C", LowerGroupRecipeId.ROOT_SEVENTH)
    assert unavailable.is_available is False
    assert "without explicit seventh/sixth material" in unavailable.unavailable_reason

    placement = place_lower_group_recipe("C", LowerGroupRecipeId.ROOT_SEVENTH, 36, 60)
    assert placement.is_legal is False
    assert placement.placed_degrees == ()
    assert placement.metadata["is_legal"] is False

    root_only = place_lower_group_recipe("C", LowerGroupRecipeId.ROOT, 36, 60)
    assert root_only.is_legal is True
    assert root_only.placed_degrees == (("R", 36),)


def test_lower_group_inventory_debug_and_docs_are_synced() -> None:
    debug = lower_group_inventory_debug("G7", low=36, high=60)
    assert debug["contract_version"] == "v2_2_40"
    assert debug["inventory_version"] == "v2_2_38"
    assert debug["runtime_enabled"] is False
    assert debug["notes_only"] is True
    assert debug["no_expression_or_pedal"] is True
    assert len(debug["inventory"]) == 9
    assert len(debug["placements"]) == 9

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
            "docs/GENERATION_RULES_SUMMARY_V2.md",
        )
    )
    required = [
        "Lower Group Recipe Inventory",
        "LOWER_GROUP_INVENTORY_VERSION",
        "LowerGroupRecipeId",
        "LowerGroupRecipeInventoryItem",
        "instantiate_lower_group_recipe",
        "place_lower_group_recipe",
        "lower_group_inventory_debug",
        "root+7 / root+3 / root+5 / 3+7",
        "root+5+upper_root / root+3+7 / root+7+upper3 / root+5+upper3",
        "within one octave",
        "notes-only",
    ]
    for token in required:
        assert token in docs
