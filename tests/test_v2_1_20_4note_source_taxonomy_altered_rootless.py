from __future__ import annotations

from pathlib import Path

from jammate_engine.core.voicing import ContentFamily
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION, build_voicing_override_policy

ROOT = Path(__file__).resolve().parents[1]


def _rootless_policy():
    return build_voicing_override_policy({}, {"enabled": True, "preset": "rootless_ab_safe"}, style_name="medium_swing")


def _rootless_recipes(symbol: str):
    return [
        recipe
        for recipe in plan_content_recipes(symbol, _rootless_policy())
        if recipe.family in {ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B}
    ]


def test_v2_1_20_halfdim_uses_generic_rootless_sources_not_dedicated_source_family() -> None:
    recipes = _rootless_recipes("Gm7b5")
    orders = {(recipe.family, recipe.degree_names) for recipe in recipes}

    assert (ContentFamily.ROOTLESS_A, ("b3", "b5", "b7", "b9")) in orders
    assert (ContentFamily.ROOTLESS_A, ("b3", "b13", "b7", "b9")) in orders
    assert any("rootless_ab_generic_scale_spelled_source" in recipe.validity_notes for recipe in recipes)
    assert any("half_diminished_uses_generic_rootless_sources_via_harmony_resolution" in recipe.validity_notes for recipe in recipes)
    assert all("rootless_ab_half_diminished_with_5_locrian_spelling" not in recipe.validity_notes for recipe in recipes)
    assert all("rootless_ab_content_type_halfdim_with_9" not in recipe.validity_notes for recipe in recipes)


def test_v2_1_20_altered_dominant_has_no_root_rootless_source() -> None:
    recipes = _rootless_recipes("G7alt")
    orders = {recipe.degree_names for recipe in recipes}

    assert ("3", "b7", "b9", "#9") in orders
    assert ("b7", "b9", "3", "#9") in orders
    assert all("R" not in recipe.degree_names for recipe in recipes)
    assert all("5" not in recipe.degree_names for recipe in recipes)
    assert any("rootless_ab_altered_dominant_source_3_b7_x_y" in recipe.validity_notes for recipe in recipes)
    assert any("rootless_ab_content_type_altered_dominant_rootless" in recipe.validity_notes for recipe in recipes)
    assert any("altered_dominant_natural_5_omitted" in recipe.validity_notes for recipe in recipes)


def test_v2_1_20_explicit_two_color_altered_dominant_uses_written_colors_without_root() -> None:
    recipes = _rootless_recipes("G7b9b13")
    orders = {recipe.degree_names for recipe in recipes}

    assert ("3", "b7", "b9", "b13") in orders
    assert ("b7", "b9", "3", "b13") in orders
    assert all("R" not in recipe.degree_names for recipe in recipes)
    assert all("5" not in recipe.degree_names for recipe in recipes)
    assert any("rootless_ab_altered_color_x_flat9" in recipe.validity_notes for recipe in recipes)
    assert any("rootless_ab_altered_color_y_flat13" in recipe.validity_notes for recipe in recipes)


def test_v2_1_20_docs_and_contract_are_updated() -> None:
    assert VOICING_OVERRIDE_CONTRACT_VERSION == "v2_1_43"
    required_docs = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "VOICING_MODULE_CORE_LOGIC_V2.md",
        ROOT / "docs" / "VOICING_SYSTEM_V2_DESIGN.md",
        ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md",
        ROOT / "docs" / "STYLE_RULE_BASELINE_V2.md",
        ROOT / "docs" / "VOICING_TUNING_WORKFLOW_V2.md",
        ROOT / "docs" / "DEVELOPMENT_HARNESS_V2.md",
        ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md",
        ROOT / "docs" / "API_CONTRACT_V2.md",
        ROOT / "docs" / "SYSTEM_CONTRACTS_V2.md",
        ROOT / "docs" / "ARCHITECTURE_V2.md",
    ]
    for path in required_docs:
        text = path.read_text(encoding="utf-8")
        assert "v2_1_20" in text, path
        assert "3-b7-X-Y" in text, path
        assert "Half-diminished is not a separate rootless source" in text, path
