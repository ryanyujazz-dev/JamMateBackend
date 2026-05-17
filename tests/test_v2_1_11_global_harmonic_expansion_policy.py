from __future__ import annotations

from pathlib import Path

from jammate_engine.core.harmony.chord_parser import parse_chord
from jammate_engine.core.voicing import (
    ContentFamily,
    RootSupportPolicy,
    VoicingPolicy,
    harmonic_expansion_allowed,
)
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_PRESETS

ROOT = Path(__file__).resolve().parents[1]


def test_harmonic_expansion_allowed_is_global_policy_helper() -> None:
    default_policy = VoicingPolicy()
    safe_policy = VoicingPolicy(harmonic_expansion_enabled=True)
    altered_policy = VoicingPolicy.from_legacy_dict({"color_policy_mode": "altered_dominant"})

    assert harmonic_expansion_allowed(default_policy, parse_chord("G7")) is False
    assert harmonic_expansion_allowed(safe_policy, parse_chord("Cmaj7")) is True
    assert harmonic_expansion_allowed(altered_policy, parse_chord("G7")) is True
    assert harmonic_expansion_allowed(altered_policy, parse_chord("Cmaj7")) is False


def test_three_note_and_four_note_color_families_share_same_expansion_gate() -> None:
    conservative_policy = VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(ContentFamily.SHELL_PLUS_COLOR, ContentFamily.ROOTLESS_A),
        preferred_density=4,
        max_density=4,
    )
    expanded_policy = VoicingPolicy.from_legacy_dict(
        {
            "root_support": "rootless_allowed",
            "allowed_content": ["shell_plus_color", "rootless_A"],
            "harmonic_expansion_enabled": True,
            "preferred_density": 4,
            "max_density": 4,
        }
    )

    conservative = {recipe.family: recipe for recipe in plan_content_recipes("G7", conservative_policy)}
    expanded = {recipe.family: recipe for recipe in plan_content_recipes("G7", expanded_policy)}

    assert ContentFamily.SHELL_PLUS_COLOR in conservative
    assert set(conservative[ContentFamily.SHELL_PLUS_COLOR].degree_names) == {"3", "5", "b7"}
    assert ContentFamily.ROOTLESS_A not in conservative

    assert ContentFamily.SHELL_PLUS_COLOR in expanded
    assert ContentFamily.ROOTLESS_A in expanded
    assert any(degree in expanded[ContentFamily.ROOTLESS_A].degree_names for degree in ("9", "13"))


def test_explicit_chord_color_is_not_harmonic_expansion_but_may_enable_color_voicing() -> None:
    policy = VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(ContentFamily.SHELL_PLUS_COLOR, ContentFamily.ROOTLESS_A),
        preferred_density=4,
        max_density=4,
    )
    recipes = plan_content_recipes("Cmaj9", policy)
    first_by_family = {}
    for recipe in recipes:
        first_by_family.setdefault(recipe.family, recipe)
    degree_sets = {(recipe.family, recipe.degree_names) for recipe in recipes}

    assert harmonic_expansion_allowed(policy, parse_chord("Cmaj9")) is False
    assert first_by_family[ContentFamily.SHELL_PLUS_COLOR].degree_names == ("3", "7", "9")
    assert (ContentFamily.ROOTLESS_A, ("3", "5", "7", "9")) in degree_sets
    assert any("rootless_ab_explicit_chord_symbol_color_used" in recipe.validity_notes for recipe in recipes if recipe.family == ContentFamily.ROOTLESS_A)


def test_rootless_ab_metadata_no_longer_describes_a_local_gate() -> None:
    metadata = VOICING_OVERRIDE_PRESETS["rootless_ab_safe"]["metadata"]
    assert "HarmonicExpansionPolicy" in metadata["gate"]
    assert "extra unnotated tensions" in metadata["explicit_color_rule"]


def test_v2_1_11_global_color_policy_is_documented() -> None:
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
        ROOT / "docs" / "DEVELOPMENT_HARNESS_V2.md",
    ]
    for path in required_docs:
        text = path.read_text(encoding="utf-8")
        assert "v2_1_11" in text, path
        assert "HarmonicExpansionPolicy" in text, path
        assert "VoicingColorPolicy" in text, path
        assert "3-note" in text and "5-note" in text and "6-note" in text, path
