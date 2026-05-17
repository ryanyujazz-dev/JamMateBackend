from __future__ import annotations

from pathlib import Path

from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.runtime.override import build_voicing_override_policy
from jammate_engine.core.voicing.runtime.texture_plan import VoicingDispositionFamily, derive_voicing_texture_plan

ROOT = Path(__file__).resolve().parents[1]


def _rootless_policy():
    return build_voicing_override_policy({}, {"enabled": True, "preset": "rootless_ab_safe"}, style_name="medium_swing")


def test_v2_1_14_plain_half_diminished_rootless_uses_locrian_b9_not_default_11() -> None:
    policy = _rootless_policy()
    recipes = plan_content_recipes("Gm7b5", policy)

    assert recipes
    orders = {recipe.degree_names for recipe in recipes}
    assert ("b3", "b5", "b7", "b9") in orders
    assert ("b7", "b9", "b3", "b5") in orders
    assert ("b3", "b13", "b7", "b9") in orders
    assert all("11" not in recipe.degree_names for recipe in recipes)
    assert any("rootless_ab_content_type_with_5" in recipe.validity_notes for recipe in recipes)
    assert any("rootless_ab_content_type_with_13" in recipe.validity_notes for recipe in recipes)
    assert all("rootless_ab_content_type_halfdim_with_9" not in recipe.validity_notes for recipe in recipes)


def test_v2_1_14_explicit_m11b5_uses_compact_11_source() -> None:
    policy = _rootless_policy()
    recipes = plan_content_recipes("Gm11b5", policy)

    orders = {recipe.degree_names for recipe in recipes}
    assert ("b3", "11", "b5", "b7") in orders
    assert ("b7", "b3", "11", "b5") in orders
    assert any("rootless_ab_half_diminished_explicit_11_compact" in recipe.validity_notes for recipe in recipes)
    assert all("rootless_ab_content_type_halfdim_with_9" not in recipe.validity_notes for recipe in recipes)

    candidates = generate_candidates("Gm11b5", policy)
    compact = [candidate for candidate in candidates if candidate.degrees == ["b3", "11", "b5", "b7"]]
    assert compact
    assert min(max(candidate.notes) - min(candidate.notes) for candidate in compact) <= 8


def test_v2_1_14_rootless_candidates_carry_texture_and_canonical_source_metadata() -> None:
    policy = _rootless_policy()
    candidates = generate_candidates("Dm7", policy)

    assert candidates
    candidate = candidates[0]
    texture = candidate.metadata.get("voicing_texture_plan")
    source = candidate.metadata.get("canonical_closed_source")
    assert texture["primary_disposition_family"] == "compact_rootless"
    assert texture["architecture_contract"] == "VoicingTexturePlan -> ContentRecipe -> CanonicalClosedSource -> DispositionGenerator -> VoiceLeadingScorer"
    assert source["source_kind"] == "canonical_closed_position_source"
    assert source["not_a_final_random_disposition"] is True

    plan = derive_voicing_texture_plan(policy, content_family=candidate.content_family)
    assert plan.primary_disposition_family == VoicingDispositionFamily.COMPACT_ROOTLESS


def test_v2_1_14_voicing_architecture_is_documented() -> None:
    required_docs = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "VOICING_SYSTEM_V2_DESIGN.md",
        ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md",
        ROOT / "docs" / "STYLE_RULE_BASELINE_V2.md",
        ROOT / "docs" / "VOICING_TUNING_WORKFLOW_V2.md",
        ROOT / "docs" / "DEVELOPMENT_HARNESS_V2.md",
        ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md",
    ]
    for path in required_docs:
        text = path.read_text(encoding="utf-8")
        assert "v2_1_15" in text, path
        assert "VoicingTexturePlan" in text, path
        assert "CanonicalClosedSource" in text, path
        assert "m7b5" in text and "m11b5" in text, path
