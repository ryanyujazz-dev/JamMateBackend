from __future__ import annotations

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.disposition.spread import (
    LowerGroupRecipeId,
    SPREAD_LOWER_FOUNDATION_QUALITY_GATE_VERSION,
    _lower_recipe_ids_for_contract,
    spread_recipe_contract_by_id,
)


def test_v2_2_73_version_and_quality_gate_constant_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert SPREAD_LOWER_FOUNDATION_QUALITY_GATE_VERSION == "v2_2_73"


def test_lower_2note_quality_gate_treats_root5_as_triad_family() -> None:
    contract = spread_recipe_contract_by_id("spread_2plus3_contract")

    seventh_recipes = _lower_recipe_ids_for_contract(contract, chord_symbol="Ebmaj7")
    assert LowerGroupRecipeId.ROOT_THIRD in seventh_recipes
    assert LowerGroupRecipeId.ROOT_SEVENTH in seventh_recipes
    assert LowerGroupRecipeId.ROOT_FIFTH not in seventh_recipes

    triad_recipes = _lower_recipe_ids_for_contract(contract, chord_symbol="Eb")
    assert LowerGroupRecipeId.ROOT_THIRD in triad_recipes
    assert LowerGroupRecipeId.ROOT_FIFTH in triad_recipes
    assert LowerGroupRecipeId.ROOT_SEVENTH not in triad_recipes


def test_lower_3note_quality_gate_splits_seventh_and_triad_foundations() -> None:
    contract = spread_recipe_contract_by_id("spread_3plus3_contract")

    seventh_recipes = _lower_recipe_ids_for_contract(contract, chord_symbol="Ebmaj7")
    assert seventh_recipes == (
        LowerGroupRecipeId.ROOT_THIRD_SEVENTH,
        LowerGroupRecipeId.ROOT_SEVENTH_UPPER_THIRD,
    )

    triad_recipes = _lower_recipe_ids_for_contract(contract, chord_symbol="Eb")
    assert triad_recipes == (
        LowerGroupRecipeId.ROOT_FIFTH_UPPER_ROOT,
        LowerGroupRecipeId.ROOT_FIFTH_UPPER_THIRD,
    )
