from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import ColorPolicyMode, ContentFamily, RootSupportPolicy, VoicingPolicy
from jammate_engine.core.voicing.sources.content_planner import choose_content_families, plan_content_recipes
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy as get_ballad_voicing_policy

ROOT = Path(__file__).resolve().parents[1]


def _policy(*families: ContentFamily, expansion: bool = False, mode: ColorPolicyMode = ColorPolicyMode.CHORD_SYMBOL_ONLY) -> VoicingPolicy:
    return VoicingPolicy(
        allowed_content=families,
        preferred_content=families[0] if families else None,
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        min_density=4,
        preferred_density=4,
        max_density=4,
        max_voicing_span=24,
        harmonic_expansion_enabled=expansion,
        color_policy_mode=mode,
    )


def test_v2_1_24_plain_chord_symbol_only_falls_back_to_basic_4note_source() -> None:
    policy = _policy(ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B, ContentFamily.ROOTED_COLOR)

    families = choose_content_families("Cmaj7", policy)
    recipes = plan_content_recipes("Cmaj7", policy)

    assert families == [ContentFamily.SEVENTH_BASIC]
    assert {recipe.family for recipe in recipes} == {ContentFamily.SEVENTH_BASIC}
    assert all(recipe.degree_names in {("R", "3", "5", "7"), ("3", "5", "7", "R"), ("5", "7", "R", "3"), ("7", "R", "3", "5")} for recipe in recipes)
    assert all("four_note_color_gate_open_explicit_chord_symbol_color" not in recipe.validity_notes for recipe in recipes)
    assert all("four_note_color_gate_open_harmonic_expansion" not in recipe.validity_notes for recipe in recipes)


def test_v2_1_24_explicit_chart_color_opens_color_sources_without_expansion() -> None:
    policy = _policy(ContentFamily.ROOTLESS_A, ContentFamily.ROOTED_COLOR)
    recipes = plan_content_recipes("Cmaj9", policy)

    assert any(recipe.family == ContentFamily.ROOTLESS_A and recipe.degree_names == ("3", "5", "7", "9") for recipe in recipes)
    assert any(recipe.family == ContentFamily.ROOTED_COLOR and recipe.degree_names == ("R", "3", "7", "9") for recipe in recipes)
    assert any("four_note_color_gate_open_explicit_chord_symbol_color" in recipe.validity_notes for recipe in recipes)
    assert all("four_note_color_gate_open_harmonic_expansion" not in recipe.validity_notes for recipe in recipes)


def test_v2_1_24_harmonic_expansion_opens_unnotated_color_sources() -> None:
    policy = _policy(
        ContentFamily.ROOTLESS_A,
        ContentFamily.ROOTED_COLOR,
        expansion=True,
        mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
    )
    recipes = plan_content_recipes("Cmaj7", policy)

    assert any(recipe.family == ContentFamily.ROOTLESS_A and recipe.degree_names == ("3", "5", "7", "9") for recipe in recipes)
    assert any(recipe.family == ContentFamily.ROOTLESS_A and recipe.degree_names == ("3", "13", "7", "9") for recipe in recipes)
    assert any(recipe.family == ContentFamily.ROOTED_COLOR and recipe.degree_names == ("R", "3", "7", "9") for recipe in recipes)
    assert any("four_note_color_gate_open_harmonic_expansion" in recipe.validity_notes for recipe in recipes)


def test_v2_1_24_ballad_explicitly_opts_into_style_safe_expansion() -> None:
    policy = get_ballad_voicing_policy()

    assert policy.harmonic_expansion_enabled is True
    assert policy.color_policy_mode == ColorPolicyMode.STYLE_SAFE_EXTENSIONS
    assert policy.metadata["harmonic_expansion_role"].startswith("ballad intentionally opens")
    assert policy.metadata["harmonic_expansion_target_families"] == [ContentFamily.ROOTED_COLOR.value]


def test_v2_1_24_contract_and_docs_are_updated() -> None:
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
        assert "v2_1_24" in text, path
        assert "4-Note Source Gating Audit" in text, path
        assert "four_note_color_gate" in text, path
