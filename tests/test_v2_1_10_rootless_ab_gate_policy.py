from __future__ import annotations

from pathlib import Path

from jammate_engine.core.voicing import ContentFamily, RootSupportPolicy, VoicingPolicy
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_PRESETS, build_voicing_override_policy

ROOT = Path(__file__).resolve().parents[1]


def _families(symbol: str, policy: VoicingPolicy) -> set[ContentFamily]:
    return {recipe.family for recipe in plan_content_recipes(symbol, policy)}


def test_plain_chord_symbol_does_not_open_rootless_ab_gate() -> None:
    policy = VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B, ContentFamily.SEVENTH_BASIC),
        preferred_content=ContentFamily.ROOTLESS_A,
        preferred_density=4,
    )

    recipes = plan_content_recipes("G7", policy)
    assert ContentFamily.ROOTLESS_A not in {recipe.family for recipe in recipes}
    assert ContentFamily.ROOTLESS_B not in {recipe.family for recipe in recipes}
    assert any(recipe.family == ContentFamily.SEVENTH_BASIC for recipe in recipes)


def test_explicit_chord_symbol_color_can_open_rootless_ab_without_global_expansion() -> None:
    policy = VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B),
        preferred_content=ContentFamily.ROOTLESS_A,
        preferred_density=4,
    )

    recipes = plan_content_recipes("Cmaj9", policy)
    degree_sets = {(recipe.family, recipe.degree_names) for recipe in recipes}
    assert any(recipe.family == ContentFamily.ROOTLESS_A for recipe in recipes)
    assert any(recipe.family == ContentFamily.ROOTLESS_B for recipe in recipes)
    assert (ContentFamily.ROOTLESS_A, ("3", "5", "7", "9")) in degree_sets
    assert any("rootless_ab_explicit_chord_symbol_color_used" in recipe.validity_notes for recipe in recipes if recipe.family == ContentFamily.ROOTLESS_A)


def test_harmonic_expansion_enabled_opens_safe_rootless_ab_for_plain_chords() -> None:
    policy = build_voicing_override_policy({}, {"enabled": True, "preset": "rootless_ab_safe"}, style_name="medium_swing")
    recipes = list(plan_content_recipes("G7", policy))
    degree_sets = {(recipe.family, recipe.degree_names) for recipe in recipes}

    assert policy.harmonic_expansion_enabled is True
    assert VOICING_OVERRIDE_PRESETS["4_note_rootless_ab_safe"]["preferred_density"] == 4
    assert (ContentFamily.ROOTLESS_A, ("3", "5", "b7", "9")) in degree_sets
    assert (ContentFamily.ROOTLESS_B, ("b7", "9", "3", "5")) in degree_sets
    assert (ContentFamily.ROOTLESS_A, ("3", "13", "b7", "9")) in degree_sets
    assert (ContentFamily.ROOTLESS_B, ("b7", "9", "3", "13")) in degree_sets
    assert any("rootless_ab_harmonic_expansion_enabled" in recipe.validity_notes for recipe in recipes)


def test_half_diminished_b5_identity_is_not_enough_to_open_rootless_ab_gate() -> None:
    policy = VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(ContentFamily.ROOTLESS_A, ContentFamily.SEVENTH_BASIC),
        preferred_content=ContentFamily.ROOTLESS_A,
        preferred_density=4,
    )

    assert ContentFamily.ROOTLESS_A not in _families("Bm7b5", policy)
    explicit_color_orders = {(recipe.family, recipe.degree_names) for recipe in plan_content_recipes("Bm9b5", policy)}
    assert (ContentFamily.ROOTLESS_A, ("b3", "b5", "b7", "9")) in explicit_color_orders
    assert all("rootless_ab_content_type_halfdim_with_9" not in recipe.validity_notes for recipe in plan_content_recipes("Bm9b5", policy))


def test_v2_1_10_rootless_ab_gate_is_documented() -> None:
    required_docs = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "VOICING_TUNING_WORKFLOW_V2.md",
        ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md",
        ROOT / "docs" / "STYLE_RULE_BASELINE_V2.md",
        ROOT / "docs" / "VOICING_SYSTEM_V2_DESIGN.md",
        ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md",
        ROOT / "docs" / "API_CONTRACT_V2.md",
        ROOT / "docs" / "SYSTEM_CONTRACTS_V2.md",
    ]
    for path in required_docs:
        text = path.read_text(encoding="utf-8")
        assert "v2_1_10" in text, path
        assert "rootless_ab_safe" in text, path
        assert "chord_symbol_has_explicit_color" in text, path
