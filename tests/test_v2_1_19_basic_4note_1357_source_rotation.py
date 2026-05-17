from __future__ import annotations

from pathlib import Path

from jammate_engine.core.voicing import ColorPolicyMode, ContentFamily, Disposition, RootSupportPolicy, VoicingPolicy
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION, VOICING_OVERRIDE_PRESETS, build_voicing_override_policy
from jammate_engine.core.voicing.selection.selector import select_candidate

ROOT = Path(__file__).resolve().parents[1]


def _mixed_policy(*, expansion: bool = False) -> VoicingPolicy:
    return VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B, ContentFamily.SEVENTH_BASIC),
        preferred_content=ContentFamily.ROOTLESS_A,
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED,),
        preferred_density=4,
        min_density=4,
        max_density=4,
        harmonic_expansion_enabled=expansion,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS if expansion else ColorPolicyMode.CHORD_SYMBOL_ONLY,
        selector_temperature=0.20,
        selection_pool_size=8,
    )


def _basic_policy() -> VoicingPolicy:
    return build_voicing_override_policy({}, {"enabled": True, "preset": "basic_4note_1357"}, style_name="medium_swing")


def test_v2_1_19_basic_1357_uses_canonical_source_rotations() -> None:
    recipes = [recipe for recipe in plan_content_recipes("Cmaj7", _basic_policy()) if recipe.family == ContentFamily.SEVENTH_BASIC]

    assert [recipe.degree_names for recipe in recipes] == [
        ("R", "3", "5", "7"),
        ("3", "5", "7", "R"),
        ("5", "7", "R", "3"),
        ("7", "R", "3", "5"),
    ]
    assert all("basic_4note_1357_source_family" in recipe.validity_notes for recipe in recipes)
    assert all("basic_4note_content_type_1357" in recipe.validity_notes for recipe in recipes)


def test_v2_1_19_basic_1357_is_quality_correct_for_common_seventh_chords() -> None:
    policy = _basic_policy()
    expected = {
        "Dm7": ("R", "b3", "5", "b7"),
        "G7": ("R", "3", "5", "b7"),
        "Cmaj7": ("R", "3", "5", "7"),
        "Bm7b5": ("R", "b3", "b5", "b7"),
    }
    for symbol, first_rotation in expected.items():
        recipes = [recipe for recipe in plan_content_recipes(symbol, policy) if recipe.family == ContentFamily.SEVENTH_BASIC]
        assert recipes[0].degree_names == first_rotation
        assert "basic_4note_conservative_chord_symbol_material" in recipes[0].validity_notes


def test_v2_1_19_plain_chord_symbol_defaults_to_1357_not_rootless_color() -> None:
    recipes = plan_content_recipes("Cmaj7", _mixed_policy(expansion=False))

    assert {recipe.family for recipe in recipes} == {ContentFamily.SEVENTH_BASIC}
    assert {recipe.degree_names for recipe in recipes} == {
        ("R", "3", "5", "7"),
        ("3", "5", "7", "R"),
        ("5", "7", "R", "3"),
        ("7", "R", "3", "5"),
    }


def test_v2_1_19_explicit_color_still_opens_rootless_without_removing_1357() -> None:
    recipes = plan_content_recipes("Cmaj9", _mixed_policy(expansion=False))
    rootless = [recipe for recipe in recipes if recipe.family in {ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B}]
    basic = [recipe for recipe in recipes if recipe.family == ContentFamily.SEVENTH_BASIC]

    assert rootless
    assert basic
    assert any(recipe.degree_names == ("3", "5", "7", "9") for recipe in rootless)
    assert all("13" not in recipe.degree_names for recipe in rootless)
    assert any(recipe.degree_names == ("R", "3", "5", "7") for recipe in basic)


def test_v2_1_19_expansion_keeps_1357_as_grounding_candidate() -> None:
    recipes = plan_content_recipes("G7", _mixed_policy(expansion=True))
    families = {recipe.family for recipe in recipes}

    assert ContentFamily.ROOTLESS_A in families
    assert ContentFamily.ROOTLESS_B in families
    assert ContentFamily.SEVENTH_BASIC in families
    assert any(recipe.degree_names == ("R", "3", "5", "b7") for recipe in recipes)


def test_v2_1_19_basic_1357_rotation_prior_is_8_to_2() -> None:
    policy = _basic_policy()
    candidates = [
        candidate
        for candidate in generate_candidates("Cmaj7", policy)
        if candidate.content_family == ContentFamily.SEVENTH_BASIC
        and candidate.disposition.value == "closed"
        and candidate.metadata.get("register_variant") == 0
    ]
    by_index = {candidate.metadata["basic_4note_inversion_index"]: candidate for candidate in candidates}

    assert {index: by_index[index].metadata["basic_4note_rotation_weight"] for index in sorted(by_index)} == {
        0: 8,
        1: 2,
        2: 8,
        3: 2,
    }
    preferred = select_candidate([by_index[0]], policy=policy)
    secondary = select_candidate([by_index[1]], policy=policy)
    preferred_prior = preferred.metadata["score_breakdown"]["details"]["basic_4note_rotation_prior_score"]
    secondary_prior = secondary.metadata["score_breakdown"]["details"]["basic_4note_rotation_prior_score"]

    assert preferred_prior > secondary_prior
    assert round(preferred_prior - secondary_prior, 3) == 0.277


def test_v2_1_19_basic_1357_preset_and_docs_are_updated() -> None:
    assert VOICING_OVERRIDE_CONTRACT_VERSION == "v2_1_43"
    assert "basic_4note_1357" in VOICING_OVERRIDE_PRESETS
    assert "4_note_basic_1357" in VOICING_OVERRIDE_PRESETS

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
        assert "v2_1_19" in text, path
        assert "1357" in text or "1-3-5-7" in text, path
        assert "chord-symbol-only" in text or "chord_symbol_only" in text, path
