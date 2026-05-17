from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    ColorPolicyMode,
    ContentFamily,
    Disposition,
    RootSupportPolicy,
    VoicingPolicy,
    build_four_note_source_balance_audit,
)
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION

ROOT = Path(__file__).resolve().parents[1]


def _policy(*, expansion: bool = False) -> VoicingPolicy:
    return VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(
            ContentFamily.SEVENTH_BASIC,
            ContentFamily.ROOTED_COLOR,
            ContentFamily.ROOTLESS_A,
            ContentFamily.ROOTLESS_B,
        ),
        preferred_content=ContentFamily.ROOTLESS_A if expansion else ContentFamily.SEVENTH_BASIC,
        harmonic_expansion_enabled=expansion,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS if expansion else ColorPolicyMode.CHORD_SYMBOL_ONLY,
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED,),
        min_density=4,
        preferred_density=4,
        max_density=4,
        max_voicing_span=24,
    )


def _four_note_recipes(symbol: str, *, expansion: bool = False):
    return [recipe for recipe in plan_content_recipes(symbol, _policy(expansion=expansion)) if len(recipe.degree_names) == 4]


def test_v2_1_37_plain_chord_symbol_only_remains_conservative() -> None:
    recipes = _four_note_recipes("Cmaj7", expansion=False)

    assert {recipe.family for recipe in recipes} == {ContentFamily.SEVENTH_BASIC}
    assert {recipe.degree_names for recipe in recipes} == {
        ("R", "3", "5", "7"),
        ("3", "5", "7", "R"),
        ("5", "7", "R", "3"),
        ("7", "R", "3", "5"),
    }
    assert all("four_note_color_gate_open_harmonic_expansion" not in recipe.validity_notes for recipe in recipes)


def test_v2_1_37_plain_chord_with_expansion_opens_only_allowed_color_sources() -> None:
    recipes = _four_note_recipes("Cmaj7", expansion=True)
    rootless = [recipe for recipe in recipes if recipe.family == ContentFamily.ROOTLESS_A]

    assert any(recipe.degree_names == ("3", "5", "7", "9") for recipe in rootless)
    assert any(recipe.degree_names == ("3", "13", "7", "9") for recipe in rootless)
    assert any("four_note_color_gate_open_harmonic_expansion" in recipe.validity_notes for recipe in rootless)
    assert all("four_note_color_permission_blocked_unallowed_color" not in recipe.validity_notes for recipe in rootless)


def test_v2_1_37_explicit_chart_color_without_expansion_does_not_add_extra_color() -> None:
    cmaj9 = _four_note_recipes("Cmaj9", expansion=False)
    cmaj9_rootless = [recipe for recipe in cmaj9 if recipe.family == ContentFamily.ROOTLESS_A]

    assert any(recipe.degree_names == ("3", "5", "7", "9") for recipe in cmaj9_rootless)
    assert all("13" not in recipe.degree_names for recipe in cmaj9_rootless)
    assert any("chart_color_fidelity_contains_explicit_color" in recipe.validity_notes for recipe in cmaj9_rootless)

    g13 = _four_note_recipes("G13", expansion=False)
    g13_rootless = [recipe for recipe in g13 if recipe.family == ContentFamily.ROOTLESS_A]
    assert any("13" in recipe.degree_names and "chart_color_fidelity_contains_explicit_color" in recipe.validity_notes for recipe in g13_rootless)
    assert all("9" not in recipe.degree_names for recipe in g13_rootless)


def test_v2_1_37_explicit_chart_color_plus_expansion_combines_allowed_sets() -> None:
    recipes = _four_note_recipes("Cmaj9", expansion=True)
    rootless = [recipe for recipe in recipes if recipe.family == ContentFamily.ROOTLESS_A]

    assert any(recipe.degree_names == ("3", "13", "7", "9") for recipe in rootless)
    assert any("four_note_color_gate_open_explicit_chart_color_plus_harmonic_expansion" in recipe.validity_notes for recipe in rootless)
    assert any(
        any(note.startswith("four_note_allowed_color_set_") and "13" in note and "9" in note for note in recipe.validity_notes)
        for recipe in rootless
    )
    assert any("chart_color_fidelity_contains_explicit_color" in recipe.validity_notes for recipe in rootless)


def test_v2_1_37_alt_symbol_is_palette_not_all_colors_required() -> None:
    recipes = _four_note_recipes("G7alt", expansion=True)
    altered = [recipe for recipe in recipes if recipe.family in {ContentFamily.ROOTED_COLOR, ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B}]

    assert altered
    assert any("rootless_ab_altered_dominant_rootless_source" in recipe.validity_notes for recipe in altered)
    assert all("chart_color_fidelity_omits_explicit_color" not in recipe.validity_notes for recipe in altered)
    assert all("chart_color_fidelity_explicit_omitted_sharp11_sharp9_flat13" not in recipe.validity_notes for recipe in altered)
    assert all("5" not in recipe.degree_names for recipe in altered if "rootless_ab_altered_dominant_rootless_source" in recipe.validity_notes)


def test_v2_1_37_audit_regression_has_no_unknown_gate_or_source_for_stress_symbols() -> None:
    audit = build_four_note_source_balance_audit(
        ["Cmaj7", "Cmaj9", "Dm11", "G13", "G7alt", "Bm7b5", "Bm9b5"],
        {
            "chord_symbol_only": _policy(expansion=False),
            "harmonic_expansion": _policy(expansion=True),
        },
    )
    rows = [row.to_debug_dict() for row in audit.rows]

    assert rows
    assert all(row["gate_reason"] != "unknown" for row in rows)
    assert all(row["source_family"] != "unknown" for row in rows)
    g7alt_rows = [row for row in rows if row["symbol"] == "G7alt" and row["content_family"] != "seventh_chord_basic"]
    assert any(row["chart_color_fidelity"] == "contains_explicit_chart_color" for row in g7alt_rows)
    assert all(row["chart_color_fidelity"] != "omits_explicit_chart_color" for row in g7alt_rows)


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
        assert "Color Source Gating Regression" in text, path
        assert "alt palette" in text, path
