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
from jammate_engine.core.voicing.selection.selector import select_candidate
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates

ROOT = Path(__file__).resolve().parents[1]


def _policy(*, expansion: bool = False, temperature: float = 0.0) -> VoicingPolicy:
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
        selector_temperature=temperature,
        selection_pool_size=1,
    )


def test_v2_1_27_allowed_color_set_combines_chart_color_and_expansion() -> None:
    recipes = plan_content_recipes("Cmaj9", _policy(expansion=True))
    rootless = [recipe for recipe in recipes if recipe.family == ContentFamily.ROOTLESS_A]

    assert any(recipe.degree_names == ("3", "5", "7", "9") for recipe in rootless)
    assert any(recipe.degree_names == ("3", "13", "7", "9") for recipe in rootless)
    assert any("four_note_color_gate_open_explicit_chart_color_plus_harmonic_expansion" in recipe.validity_notes for recipe in rootless)
    assert any("chart_color_fidelity_contains_explicit_color" in recipe.validity_notes for recipe in rootless)
    assert all("four_note_color_permission_blocked_unallowed_color" not in recipe.validity_notes for recipe in rootless)


def test_v2_1_27_explicit_11_is_preserved_when_expansion_also_opens_safe_colors() -> None:
    recipes = plan_content_recipes("Dm11", _policy(expansion=True))
    rootless = [recipe for recipe in recipes if recipe.family == ContentFamily.ROOTLESS_A]

    assert any("11" in recipe.degree_names and "chart_color_fidelity_contains_explicit_color" in recipe.validity_notes for recipe in rootless)
    assert any(recipe.degree_names == ("b3", "5", "b7", "9") and "chart_color_fidelity_omits_explicit_color" in recipe.validity_notes for recipe in rootless)
    assert any("four_note_allowed_color_set_11_13_9" in recipe.validity_notes for recipe in rootless)


def test_v2_1_27_altered_chart_colors_remain_faithful_under_expansion() -> None:
    recipes = plan_content_recipes("G7b9b13", _policy(expansion=True))
    rootless = [recipe for recipe in recipes if recipe.family == ContentFamily.ROOTLESS_A]

    assert any(recipe.degree_names == ("3", "b7", "b9", "b13") for recipe in rootless)
    assert any("chart_color_fidelity_contains_explicit_color" in recipe.validity_notes for recipe in rootless)
    assert all("5" not in recipe.degree_names for recipe in rootless if "rootless_ab_content_type_altered_dominant_rootless" in recipe.validity_notes)


def test_v2_1_27_chart_fidelity_score_prefers_written_color_candidates() -> None:
    candidates = generate_candidates("Dm11", _policy(expansion=True, temperature=0.0))
    selected = select_candidate(candidates, policy=_policy(expansion=True, temperature=0.0))
    details = selected.metadata["score_breakdown"]["details"]

    assert "chart_color_fidelity_score" in details
    assert details["chart_color_fidelity_score"] >= 0
    assert "11" in selected.degrees


def test_v2_1_27_audit_reports_allowed_colors_and_chart_fidelity() -> None:
    audit = build_four_note_source_balance_audit(
        ["Cmaj7", "Cmaj9", "Dm11", "G7b9b13"],
        {
            "chord_symbol_only": _policy(expansion=False),
            "harmonic_expansion": _policy(expansion=True),
        },
    )
    rows = [row.to_debug_dict() for row in audit.rows]

    cmaj7_plain = [row for row in rows if row["policy_label"] == "chord_symbol_only" and row["symbol"] == "Cmaj7"]
    assert {row["source_family"] for row in cmaj7_plain} == {"root_third_fifth_seventh"}

    cmaj9_expanded = [row for row in rows if row["policy_label"] == "harmonic_expansion" and row["symbol"] == "Cmaj9"]
    assert any(row["gate_reason"] == "four_note_color_gate_open_explicit_chart_color_plus_harmonic_expansion" for row in cmaj9_expanded)
    assert any(row["chart_color_fidelity"] == "contains_explicit_chart_color" for row in cmaj9_expanded)
    assert any("13" in row["allowed_color_set"] and "9" in row["allowed_color_set"] for row in cmaj9_expanded)

    dm11_expanded = [row for row in rows if row["policy_label"] == "harmonic_expansion" and row["symbol"] == "Dm11"]
    assert any(row["chart_color_fidelity"] == "contains_explicit_chart_color" for row in dm11_expanded)
    assert any(row["chart_color_fidelity"] == "omits_explicit_chart_color" for row in dm11_expanded)


def test_v2_1_27_contract_and_docs_are_updated() -> None:
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
        assert "Unified Color Permission + Chart Fidelity" in text, path
        assert "AllowedColorSet" in text, path
