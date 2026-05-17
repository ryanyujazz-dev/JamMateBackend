from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import ContentFamily, RootSupportPolicy, VoicingPolicy
from jammate_engine.core.voicing.sources.content_planner import choose_content_families, plan_content_recipes
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION
from jammate_engine.styles.bossa_nova.voicing_policy import get_voicing_policy as get_bossa_policy
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as get_swing_policy

ROOT = Path(__file__).resolve().parents[1]


def _basic_only_policy() -> VoicingPolicy:
    return VoicingPolicy(
        allowed_content=(ContentFamily.SEVENTH_BASIC,),
        preferred_content=ContentFamily.SEVENTH_BASIC,
        root_support=RootSupportPolicy.ROOT_OPTIONAL,
        min_density=4,
        preferred_density=4,
        max_density=4,
        max_voicing_span=24,
    )


def _color_policy() -> VoicingPolicy:
    return VoicingPolicy(
        allowed_content=(
            ContentFamily.SEVENTH_BASIC,
            ContentFamily.ROOTED_COLOR,
            ContentFamily.ROOTLESS_A,
            ContentFamily.ROOTLESS_B,
        ),
        preferred_content=ContentFamily.ROOTLESS_A,
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        min_density=4,
        preferred_density=4,
        max_density=4,
        max_voicing_span=24,
    )


def test_v2_1_37_altered_dominant_leaves_seventh_basic_in_style_policies() -> None:
    for policy in (get_swing_policy(), get_bossa_policy()):
        families = choose_content_families("G7alt", policy)
        assert ContentFamily.SEVENTH_BASIC not in families
        assert ContentFamily.ROOTED_COLOR in families
        assert ContentFamily.ROOTLESS_A in families or ContentFamily.ROOTLESS_B in families

        recipes = plan_content_recipes("G7alt", policy)
        assert all(recipe.family != ContentFamily.SEVENTH_BASIC for recipe in recipes)
        assert any("rooted_color_4note_altered_dominant_source_1_3_b7_X" in recipe.validity_notes for recipe in recipes)
        assert any("rootless_ab_altered_dominant_source_3_b7_x_y" in recipe.validity_notes for recipe in recipes)
        assert all("basic_4note_altered_dominant_compatibility_source" not in recipe.validity_notes for recipe in recipes)


def test_v2_1_37_basic_only_legacy_request_redirects_to_rooted_altered_source() -> None:
    families = choose_content_families("G7alt", _basic_only_policy())
    recipes = plan_content_recipes("G7alt", _basic_only_policy())

    assert families == [ContentFamily.ROOTED_COLOR]
    assert {recipe.family for recipe in recipes} == {ContentFamily.ROOTED_COLOR}
    assert any(recipe.degree_names == ("R", "3", "b7", "b9") for recipe in recipes)
    assert all("5" not in recipe.degree_names for recipe in recipes)
    assert all("basic_4note_altered_dominant_compatibility_source" not in recipe.validity_notes for recipe in recipes)


def test_v2_1_37_single_altered_color_does_not_fall_back_to_rootless_with_5() -> None:
    recipes = plan_content_recipes("G7b9", _color_policy())
    rootless = [recipe for recipe in recipes if recipe.family in {ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B}]
    rooted = [recipe for recipe in recipes if recipe.family == ContentFamily.ROOTED_COLOR]

    assert rootless == []
    assert rooted
    assert any(recipe.degree_names == ("R", "3", "b7", "b9") for recipe in rooted)
    assert all("5" not in recipe.degree_names for recipe in rooted)


def test_v2_1_37_two_altered_colors_use_dedicated_rootless_altered_source() -> None:
    recipes = plan_content_recipes("G7b9b13", _color_policy())
    rootless = [recipe for recipe in recipes if recipe.family in {ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B}]

    assert rootless
    assert any(recipe.degree_names == ("3", "b7", "b9", "b13") for recipe in rootless)
    assert any("rootless_ab_altered_dominant_source_3_b7_x_y" in recipe.validity_notes for recipe in rootless)
    assert all("R" not in recipe.degree_names for recipe in rootless)
    assert all("5" not in recipe.degree_names for recipe in rootless)


def test_v2_1_37_contract_and_docs_are_updated() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
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
        assert "v2_1_37" in text, path
        assert "SEVENTH_BASIC altered-dominant compatibility path has been removed" in text, path
        assert "rooted/rootless altered color families" in text, path
