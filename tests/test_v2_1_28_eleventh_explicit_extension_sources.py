from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import ColorPolicyMode, ContentFamily, Disposition, RootSupportPolicy, VoicingPolicy
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION

ROOT = Path(__file__).resolve().parents[1]


def _policy(*, expansion: bool = False) -> VoicingPolicy:
    return VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(
            ContentFamily.ROOTED_COLOR,
            ContentFamily.ROOTLESS_A,
            ContentFamily.ROOTLESS_B,
        ),
        harmonic_expansion_enabled=expansion,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS if expansion else ColorPolicyMode.CHORD_SYMBOL_ONLY,
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED,),
        min_density=4,
        preferred_density=4,
        max_density=4,
        max_voicing_span=24,
    )


def test_v2_1_37_dm11_gets_rooted_and_rootless_explicit_eleventh_sources() -> None:
    recipes = plan_content_recipes("Dm11", _policy(expansion=False))
    rooted = [recipe for recipe in recipes if recipe.family == ContentFamily.ROOTED_COLOR]
    rootless = [recipe for recipe in recipes if recipe.family == ContentFamily.ROOTLESS_A]

    assert any(recipe.degree_names == ("R", "b3", "b7", "11") for recipe in rooted)
    assert any("rooted_color_4note_functional_content_type_root_third_seventh_eleventh" in recipe.validity_notes for recipe in rooted)
    assert any(recipe.degree_names == ("b3", "5", "b7", "11") for recipe in rootless)
    assert any("rootless_ab_functional_source_type_third_fifth_seventh_eleventh" in recipe.validity_notes for recipe in rootless)
    assert all("four_note_color_permission_blocked_unallowed_color" not in recipe.validity_notes for recipe in rooted + rootless)


def test_v2_1_37_cmaj7_sharp11_resolves_eleventh_role_to_sharp11_without_false_omission() -> None:
    recipes = plan_content_recipes("Cmaj7#11", _policy(expansion=False))
    rooted = [recipe for recipe in recipes if recipe.family == ContentFamily.ROOTED_COLOR]
    rootless = [recipe for recipe in recipes if recipe.family == ContentFamily.ROOTLESS_A]

    assert any(recipe.degree_names == ("R", "3", "7", "#11") for recipe in rooted)
    assert any(recipe.degree_names == ("3", "5", "7", "#11") for recipe in rootless)
    assert any("explicit_sharp_eleventh_source_family" in recipe.validity_notes for recipe in rooted + rootless)
    assert all("chart_color_fidelity_explicit_omitted_11" not in recipe.validity_notes for recipe in rooted + rootless)
    assert any("four_note_explicit_chart_color_set_sharp11" in recipe.validity_notes for recipe in rooted + rootless)


def test_v2_1_37_expansion_allows_third_seventh_ninth_eleventh_when_chart_writes_11() -> None:
    recipes = plan_content_recipes("Dm11", _policy(expansion=True))
    rootless = [recipe for recipe in recipes if recipe.family == ContentFamily.ROOTLESS_A]

    assert any(recipe.degree_names == ("b3", "b7", "9", "11") for recipe in rootless)
    assert any("rootless_ab_functional_source_type_third_seventh_ninth_eleventh" in recipe.validity_notes for recipe in rootless)
    assert any("four_note_color_gate_open_explicit_chart_color_plus_harmonic_expansion" in recipe.validity_notes for recipe in rootless)


def test_v2_1_37_halfdim_m11b5_treats_b5_as_identity_not_chart_color() -> None:
    recipes = plan_content_recipes("Bm11b5", _policy(expansion=False))
    rootless = [recipe for recipe in recipes if recipe.family == ContentFamily.ROOTLESS_A]

    assert any(recipe.degree_names == ("b3", "11", "b5", "b7") for recipe in rootless)
    assert any("chart_color_fidelity_contains_explicit_color" in recipe.validity_notes for recipe in rootless)
    assert all("chart_color_fidelity_explicit_omitted_flat5" not in recipe.validity_notes for recipe in recipes)


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
        assert "Eleventh / #11 / Explicit Extension Source Completion" in text, path
        assert "root-third-seventh-eleventh" in text, path
