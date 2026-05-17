from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import ContentFamily, RootSupportPolicy, VoicingPolicy
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION

ROOT = Path(__file__).resolve().parents[1]


def _policy(family: ContentFamily) -> VoicingPolicy:
    return VoicingPolicy(
        allowed_content=(family,),
        preferred_content=family,
        root_support=RootSupportPolicy.ROOT_OPTIONAL,
        min_density=4,
        preferred_density=4,
        max_density=4,
        max_voicing_span=24,
    )


def _first_recipe(symbol: str, family: ContentFamily):
    return next(recipe for recipe in plan_content_recipes(symbol, _policy(family)) if recipe.family == family)


def test_v2_1_23_basic_inventory_has_sixth_sus_and_dim7_sources() -> None:
    c6 = _first_recipe("C6", ContentFamily.SEVENTH_BASIC)
    assert c6.degree_names == ("R", "3", "5", "6")
    assert "basic_4note_source_role_order_root_third_fifth_sixth" in c6.validity_notes
    assert "basic_4note_content_type_1356" in c6.validity_notes

    sus = _first_recipe("G7sus4", ContentFamily.SEVENTH_BASIC)
    assert sus.degree_names == ("R", "4", "5", "b7")
    assert "basic_4note_source_role_order_root_fourth_fifth_seventh" in sus.validity_notes
    assert "basic_4note_content_type_145b7" in sus.validity_notes

    dim7 = _first_recipe("Cdim7", ContentFamily.SEVENTH_BASIC)
    assert dim7.degree_names == ("R", "b3", "b5", "bb7")
    assert "basic_4note_dim7_source_family" in dim7.validity_notes
    assert "voicing_source_roles_resolved_by_core_harmony" in dim7.validity_notes


def test_v2_1_23_rooted_color_inventory_has_add9_69_and_rooted_altered_sources() -> None:
    add9 = _first_recipe("Cadd9", ContentFamily.ROOTED_COLOR)
    assert add9.degree_names == ("R", "3", "5", "9")
    assert "rooted_color_4note_source_role_order_root_third_fifth_ninth" in add9.validity_notes
    assert "rooted_color_4note_content_type_1359" in add9.validity_notes

    six_nine = _first_recipe("C6/9", ContentFamily.ROOTED_COLOR)
    assert six_nine.degree_names == ("R", "3", "6", "9")
    assert "rooted_color_4note_source_role_order_root_third_sixth_ninth" in six_nine.validity_notes
    assert "rooted_color_4note_content_type_1369" in six_nine.validity_notes

    altered = _first_recipe("G7b9", ContentFamily.ROOTED_COLOR)
    assert altered.degree_names == ("R", "3", "b7", "b9")
    assert "rooted_color_4note_source_role_order_root_third_seventh_altered_color_a" in altered.validity_notes
    assert "rooted_color_4note_altered_dominant_source_1_3_b7_X" in altered.validity_notes
    assert "5" not in altered.degree_names


def test_v2_1_23_candidate_metadata_exposes_inventory_source_names() -> None:
    sus_candidate = next(
        candidate
        for candidate in generate_candidates("G7sus4", _policy(ContentFamily.SEVENTH_BASIC))
        if candidate.metadata.get("basic_4note_inversion_index") == 0
    )
    assert sus_candidate.metadata["basic_4note_source_family"] == "root_fourth_fifth_seventh"
    assert sus_candidate.metadata["basic_4note_legacy_source_family_alias"] == "145b7"

    add9_candidate = next(
        candidate
        for candidate in generate_candidates("Cadd9", _policy(ContentFamily.ROOTED_COLOR))
        if candidate.metadata.get("rooted_color_4note_inversion_index") == 0
    )
    assert add9_candidate.metadata["rooted_color_4note_source_family"] == "root_third_fifth_ninth"
    assert add9_candidate.metadata["rooted_color_4note_legacy_source_family_alias"] == "1359"


def test_v2_1_23_version_contract_and_docs_are_updated() -> None:
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
        assert "v2_1_23" in text, path
        assert "root-third-fifth-sixth" in text, path
        assert "root-third-seventh-altered-color" in text, path
