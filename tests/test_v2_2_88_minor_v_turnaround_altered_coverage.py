from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.harmony.chord_parser import parse_chord
from jammate_engine.core.harmony.harmonic_context import classify_functional_motion
from jammate_engine.core.voicing import (
    ALTERED_DOMINANT_POLICY_VERSION,
    AlteredDominantFunctionalScope,
    ColorPolicyMode,
    ContentFamily,
    VoicingPolicy,
    resolve_altered_dominant_policy,
)
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.sources.source_balance import ALTERED_DOMINANT_INTENSITY_BALANCE_VERSION
from jammate_engine.core.voicing.sources.upper_structure import plan_upper_structure_sources

ROOT = Path(__file__).resolve().parents[1]


def _policy(
    *,
    scopes: str | list[str] | tuple[str, ...] = "functional_dominants",
    previous: str | None,
    next_symbol: str | None,
    home_key: str | None,
    intensity: str = "high",
    allowed_content: tuple[ContentFamily, ...] = (ContentFamily.ROOTED_COLOR, ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B),
) -> VoicingPolicy:
    return VoicingPolicy(
        allowed_content=allowed_content,
        preferred_content=allowed_content[0],
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
        min_density=4,
        preferred_density=4,
        max_density=4,
        metadata={
            "harmonic_expansion_enabled": True,
            "color_policy_mode": "style_safe_extensions",
            "previous_chord_symbol": previous,
            "next_chord_symbol": next_symbol,
            "home_key": home_key,
            "key": home_key,
            "altered_dominant_policy": {
                "enabled": True,
                "intensity": intensity,
                "scopes": scopes,
            },
            "spread_upper_structure_enabled": True,
        },
    )


def test_home_minor_v_to_i_is_resolving_v7_not_secondary() -> None:
    motion = classify_functional_motion(previous_chord_symbol="Bm7b5", chord_symbol="E7", next_chord_symbol="Am6")
    assert motion.is_minor_ii_v_i
    assert motion.current_to_next_type == "v_i_minor"

    decision = resolve_altered_dominant_policy(
        _policy(scopes="resolving_v7", previous="Bm7b5", next_symbol="Am6", home_key="A minor"),
        parse_chord("E7"),
    )
    assert decision.authorized_for_chord is True
    assert decision.functional_scope is AlteredDominantFunctionalScope.RESOLVING_V7
    assert decision.inferred_functional_scope is AlteredDominantFunctionalScope.RESOLVING_V7


def test_local_minor_ii_v_to_relative_minor_is_secondary_in_major_home_key() -> None:
    motion = classify_functional_motion(previous_chord_symbol="Bm7b5", chord_symbol="E7", next_chord_symbol="Am7")
    assert motion.is_minor_ii_v_i

    blocked_as_home_v = resolve_altered_dominant_policy(
        _policy(scopes="resolving_v7", previous="Bm7b5", next_symbol="Am7", home_key="C"),
        parse_chord("E7"),
    )
    assert blocked_as_home_v.authorized_for_chord is False
    assert blocked_as_home_v.functional_scope is AlteredDominantFunctionalScope.SECONDARY_DOMINANT

    secondary = resolve_altered_dominant_policy(
        _policy(scopes="secondary_dominants", previous="Bm7b5", next_symbol="Am7", home_key="C"),
        parse_chord("E7"),
    )
    assert secondary.authorized_for_chord is True
    assert secondary.functional_scope is AlteredDominantFunctionalScope.SECONDARY_DOMINANT


def test_turnaround_vi7_and_final_v7_keep_distinct_altered_scopes() -> None:
    vi7 = resolve_altered_dominant_policy(
        _policy(scopes=["secondary_dominants", "resolving_v7"], previous="Cmaj7", next_symbol="Dm7", home_key="C"),
        parse_chord("A7"),
    )
    assert vi7.authorized_for_chord is True
    assert vi7.functional_scope is AlteredDominantFunctionalScope.SECONDARY_DOMINANT

    final_v = resolve_altered_dominant_policy(
        _policy(scopes=["secondary_dominants", "resolving_v7"], previous="Dm7", next_symbol="Cmaj7", home_key="C"),
        parse_chord("G7"),
    )
    assert final_v.authorized_for_chord is True
    assert final_v.functional_scope is AlteredDominantFunctionalScope.RESOLVING_V7


def test_minor_resolving_v7_emits_altered_rooted_rootless_and_upper_structure_audit_notes() -> None:
    policy = _policy(
        scopes="resolving_v7",
        previous="Bm7b5",
        next_symbol="Am6",
        home_key="A minor",
        allowed_content=(ContentFamily.ROOTED_COLOR,),
    )
    rooted = plan_content_recipes("E7", policy)
    assert any("rooted_color_4note_altered_dominant_source_1_3_b7_X" in recipe.validity_notes for recipe in rooted)
    assert any("altered_dominant_functional_scope_resolving_v7" in recipe.validity_notes for recipe in rooted)
    assert any("altered_dominant_inferred_functional_scope_resolving_v7" in recipe.validity_notes for recipe in rooted)

    rootless = plan_content_recipes(
        "E7",
        _policy(
            scopes="resolving_v7",
            previous="Bm7b5",
            next_symbol="Am6",
            home_key="A minor",
            allowed_content=(ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B),
        ),
    )
    assert any("rootless_ab_content_type_altered_dominant_rootless" in recipe.validity_notes for recipe in rootless)
    assert any("altered_dominant_inferred_functional_scope_resolving_v7" in recipe.validity_notes for recipe in rootless)

    upper_sources = plan_upper_structure_sources("E7", density=3, policy=policy)
    assert any("upper_structure_profile_kind_altered" in source.source_notes for source in upper_sources)
    assert any("altered_dominant_inferred_functional_scope_resolving_v7" in source.source_notes for source in upper_sources)


def test_explicit_minor_v_alt_keeps_chart_fidelity_but_audit_preserves_inferred_motion_scope() -> None:
    decision = resolve_altered_dominant_policy(
        _policy(scopes="resolving_v7", previous="Bm7b5", next_symbol="Am6", home_key="A minor", intensity="light"),
        parse_chord("E7b9"),
    )
    assert decision.authorized_for_chord is True
    assert decision.explicit_chord_symbol_altered is True
    assert decision.functional_scope is AlteredDominantFunctionalScope.EXPLICIT_CHORD_SYMBOL_ALTERED
    assert decision.inferred_functional_scope is AlteredDominantFunctionalScope.RESOLVING_V7
    assert decision.source_weight_bias("rooted_color") >= 0.10


def test_v2_2_88_contract_and_docs_are_updated() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert ALTERED_DOMINANT_POLICY_VERSION == "v2_2_88"
    assert ALTERED_DOMINANT_INTENSITY_BALANCE_VERSION == "v2_2_88"
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"
    docs = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md",
        ROOT / "docs" / "ALTERED_DOMINANT_MINOR_TURNAROUND_COVERAGE_AUDIT_V2_2_88.md",
    ]
    for path in docs:
        text = path.read_text(encoding="utf-8")
        assert "v2_2_88" in text, path
        assert "Minor V→i / Turnaround Altered Coverage Audit" in text, path
        assert "Bm7b5 → E7 → Am" in text, path
