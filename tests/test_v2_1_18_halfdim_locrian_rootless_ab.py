from __future__ import annotations

from pathlib import Path

from jammate_engine.core.harmony import parse_chord, resolve_scale_policy_detail, scale_spelling_for_extension
from jammate_engine.core.voicing import ContentFamily
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.runtime.override import build_voicing_override_policy

ROOT = Path(__file__).resolve().parents[1]


def _rootless_policy():
    return build_voicing_override_policy({}, {"enabled": True, "preset": "rootless_ab_safe"}, style_name="medium_swing")


def _content_types(symbol: str) -> set[str]:
    return {
        note.removeprefix("rootless_ab_content_type_")
        for recipe in plan_content_recipes(symbol, _rootless_policy())
        for note in recipe.validity_notes
        if note.startswith("rootless_ab_content_type_")
    }


def test_v2_1_18_common_harmony_recognizes_extended_half_diminished_as_locrian() -> None:
    for symbol in ["Gm7b5", "Gm11b5", "Gm13b5"]:
        chord = parse_chord(symbol)
        scale = resolve_scale_policy_detail(symbol)

        assert chord.quality == "half_diminished"
        assert chord.is_half_diminished
        assert scale.mode == "locrian"
        assert "b9" in scale.scale_degrees
        assert "b13" in scale.scale_degrees
        assert scale_spelling_for_extension(symbol, "9") == "b9"
        assert scale_spelling_for_extension(symbol, "13") == "b13"


def test_v2_1_18_half_diminished_rootless_ab_uses_with_5_and_with_13_not_with_9() -> None:
    recipes = plan_content_recipes("Gm7b5", _rootless_policy())
    orders = {(recipe.family, recipe.degree_names) for recipe in recipes}

    assert (ContentFamily.ROOTLESS_A, ("b3", "b5", "b7", "b9")) in orders
    assert (ContentFamily.ROOTLESS_B, ("b7", "b9", "b3", "b5")) in orders
    assert (ContentFamily.ROOTLESS_A, ("b3", "b13", "b7", "b9")) in orders
    assert (ContentFamily.ROOTLESS_B, ("b7", "b9", "b3", "b13")) in orders
    assert _content_types("Gm7b5") == {"with_5", "with_13"}
    assert all(
        "rootless_ab_content_type_halfdim_with_9" not in recipe.validity_notes
        for recipe in recipes
    )
    assert any("rootless_ab_scale_ninth_flat9" in recipe.validity_notes for recipe in recipes)
    assert any("rootless_ab_scale_thirteenth_flat13" in recipe.validity_notes for recipe in recipes)


def test_v2_1_18_explicit_m9b5_keeps_written_natural_9_without_new_content_bucket() -> None:
    recipes = plan_content_recipes("Gm9b5", _rootless_policy())
    orders = {recipe.degree_names for recipe in recipes}

    assert ("b3", "b5", "b7", "9") in orders
    assert ("b3", "b13", "b7", "9") in orders
    assert _content_types("Gm9b5") == {"with_5", "with_13"}
    assert all(
        "rootless_ab_content_type_halfdim_with_9" not in recipe.validity_notes
        for recipe in recipes
    )


def test_v2_1_18_halfdim_locrian_rule_is_documented() -> None:
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
        assert "v2_1_18" in text, path
        assert "Locrian" in text, path
        assert "b9" in text and "b13" in text, path
        assert "halfdim_with_9" in text, path
