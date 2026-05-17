from __future__ import annotations

from pathlib import Path

from jammate_engine.core.voicing import ContentFamily, RootSupportPolicy, VoicingPolicy
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.runtime.override import build_voicing_override_policy

ROOT = Path(__file__).resolve().parents[1]


def _rootless_types(symbol: str, policy: VoicingPolicy) -> set[str]:
    return {note for recipe in plan_content_recipes(symbol, policy) for note in recipe.validity_notes if note.startswith("rootless_ab_content_type_")}


def test_ordinary_minor_7_does_not_get_rootless_ab_with_13_in_safe_expansion() -> None:
    policy = build_voicing_override_policy({}, {"enabled": True, "preset": "rootless_ab_safe"}, style_name="medium_swing")
    recipes = plan_content_recipes("F#m7", policy)

    assert recipes
    assert _rootless_types("F#m7", policy) == {"rootless_ab_content_type_with_5"}
    assert all("13" not in recipe.degree_names for recipe in recipes)


def test_minor_13_is_allowed_when_chart_explicitly_requests_13() -> None:
    policy = VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B),
        preferred_density=4,
        max_density=4,
    )
    recipes = plan_content_recipes("Dm13", policy)

    assert any(recipe.degree_names in {("b3", "13", "b7", "5"), ("b7", "5", "b3", "13")} for recipe in recipes)
    assert any("rootless_ab_content_type_with_13" in recipe.validity_notes for recipe in recipes)


def test_minor_13_is_allowed_in_explicit_dorian_or_modal_context() -> None:
    policy = VoicingPolicy.from_legacy_dict(
        {
            "root_support": "rootless_allowed",
            "allowed_content": ["rootless_A", "rootless_B"],
            "preferred_density": 4,
            "max_density": 4,
            "harmonic_expansion_enabled": True,
            "metadata": {"scale_mode": "dorian"},
        }
    )
    recipes = plan_content_recipes("Dm7", policy)

    assert any("rootless_ab_content_type_with_13" in recipe.validity_notes for recipe in recipes)
    assert any("rootless_ab_minor_13_dorian_modal_context" in recipe.validity_notes for recipe in recipes)


def test_v2_1_13_minor_13_modal_gate_is_documented() -> None:
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
        assert "v2_1_13" in text, path
        assert "m7 + 13" in text, path
        assert "Dorian" in text and "modal" in text, path
