from __future__ import annotations

from pathlib import Path

from jammate_engine.core.harmony.scale_resolver import resolve_functional_degree_role
from jammate_engine.core.voicing import ContentFamily
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION, VOICING_OVERRIDE_PRESETS, build_voicing_override_policy
from jammate_engine.api.version import ENGINE_VERSION_TAG

ROOT = Path(__file__).resolve().parents[1]


def _rootless_policy():
    return build_voicing_override_policy({}, {"enabled": True, "preset": "rootless_ab_safe"}, style_name="medium_swing")


def _basic_policy():
    return build_voicing_override_policy({}, {"enabled": True, "preset": "basic_4note_root_third_fifth_seventh"}, style_name="medium_swing")


def test_v2_1_22_harmony_resolves_functional_degree_roles() -> None:
    assert [resolve_functional_degree_role("Cmaj7", role) for role in ("root", "third", "fifth", "seventh")] == ["R", "3", "5", "7"]
    assert [resolve_functional_degree_role("Gm7b5", role) for role in ("third", "fifth", "seventh", "ninth")] == ["b3", "b5", "b7", "b9"]
    assert [resolve_functional_degree_role("Gm9b5", role) for role in ("third", "fifth", "seventh", "ninth")] == ["b3", "b5", "b7", "9"]


def test_v2_1_22_basic_4note_uses_functional_source_roles_with_legacy_alias() -> None:
    recipes = [recipe for recipe in plan_content_recipes("Gm7b5", _basic_policy()) if recipe.family == ContentFamily.SEVENTH_BASIC]

    assert recipes[0].degree_names == ("R", "b3", "b5", "b7")
    assert "basic_4note_source_role_order_root_third_fifth_seventh" in recipes[0].validity_notes
    assert "basic_4note_functional_content_type_root_third_fifth_seventh" in recipes[0].validity_notes
    assert "basic_4note_content_type_1357" in recipes[0].validity_notes
    assert "voicing_source_roles_resolved_by_core_harmony" in recipes[0].validity_notes


def test_v2_1_22_rootless_ab_uses_functional_source_roles_and_harmony_resolution() -> None:
    recipes = [
        recipe
        for recipe in plan_content_recipes("Gm7b5", _rootless_policy())
        if recipe.family == ContentFamily.ROOTLESS_A and recipe.degree_names == ("b3", "b5", "b7", "b9")
    ]

    assert recipes
    recipe = recipes[0]
    assert "rootless_ab_source_role_order_third_fifth_seventh_ninth" in recipe.validity_notes
    assert "rootless_ab_functional_source_type_third_fifth_seventh_ninth" in recipe.validity_notes
    assert "rootless_ab_content_type_with_5" in recipe.validity_notes
    assert "rootless_ab_generic_functional_source" in recipe.validity_notes
    assert "half_diminished_uses_generic_rootless_sources_via_harmony_resolution" in recipe.validity_notes


def test_v2_1_22_candidate_metadata_exposes_functional_role_order() -> None:
    basic_candidate = next(
        candidate
        for candidate in generate_candidates("Cmaj7", _basic_policy())
        if candidate.metadata.get("basic_4note_inversion_index") == 0
    )
    assert basic_candidate.metadata["basic_4note_source_family"] == "root_third_fifth_seventh"
    assert basic_candidate.metadata["basic_4note_legacy_source_family_alias"] == "1357"
    assert basic_candidate.metadata["basic_4note_source_role_order"] == "root_third_fifth_seventh"

    rootless_candidate = next(
        candidate
        for candidate in generate_candidates("Gm7b5", _rootless_policy())
        if candidate.metadata.get("rootless_ab_orientation_family") == "A"
        and candidate.metadata.get("rootless_ab_content_type") == "with_5"
        and candidate.metadata.get("rootless_ab_inversion_index") == 0
    )
    assert rootless_candidate.metadata["rootless_ab_source_role_order"] == "third_fifth_seventh_ninth"
    assert rootless_candidate.degrees == ["b3", "b5", "b7", "b9"]


def test_v2_1_22_version_contract_and_docs_are_updated() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_OVERRIDE_CONTRACT_VERSION == "v2_1_43"
    assert "basic_4note_root_third_fifth_seventh" in VOICING_OVERRIDE_PRESETS
    assert "rootless_third_fifth_seventh_ninth" in VOICING_OVERRIDE_PRESETS

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
        assert "v2_1_22" in text, path
        assert "functional degree source" in text, path
        assert "third-fifth-seventh-ninth" in text, path
