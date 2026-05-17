from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.harmony.chord_parser import parse_chord
from jammate_engine.core.harmony.harmonic_context import classify_functional_motion
from jammate_engine.core.voicing import (
    AlteredDominantFunctionalScope,
    ColorPolicyMode,
    ContentFamily,
    VoicingPolicy,
    resolve_altered_dominant_policy,
)
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes

ROOT = Path(__file__).resolve().parents[1]


def _policy(
    *,
    scopes: list[str] | tuple[str, ...] | str,
    previous: str | None = None,
    current_region: str = "r1",
    next_symbol: str | None = None,
    home_key: str | None = "C",
    selected_region_ids: list[str] | None = None,
    force_current: bool = False,
    allowed_content: tuple[ContentFamily, ...] = (ContentFamily.ROOTED_COLOR, ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B),
    semantic: str | None = None,
) -> VoicingPolicy:
    nested: dict[str, object] = {
        "enabled": True,
        "intensity": "high",
        "scopes": scopes,
    }
    if selected_region_ids is not None:
        nested["selected_region_ids"] = selected_region_ids
    if force_current:
        nested["force_current_chord"] = True
    metadata: dict[str, object] = {
        "harmonic_expansion_enabled": True,
        "color_policy_mode": "style_safe_extensions",
        "previous_chord_symbol": previous,
        "next_chord_symbol": next_symbol,
        "region_id": current_region,
        "home_key": home_key,
        "key": home_key,
        "altered_dominant_policy": nested,
    }
    if semantic:
        metadata["dominant_context"] = semantic
    return VoicingPolicy(
        allowed_content=allowed_content,
        preferred_content=allowed_content[0],
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
        min_density=4,
        preferred_density=4,
        max_density=4,
        metadata=metadata,
    )


def test_resolving_v7_scope_authorizes_only_direct_v_to_tonic_motion() -> None:
    decision = resolve_altered_dominant_policy(
        _policy(scopes="resolving_v7", previous="Dm7", next_symbol="Cmaj7"),
        parse_chord("G7"),
    )
    assert decision.authorized_for_chord is True
    assert decision.functional_scope is AlteredDominantFunctionalScope.RESOLVING_V7

    secondary = resolve_altered_dominant_policy(
        _policy(scopes="resolving_v7", previous="Cmaj7", next_symbol="Dm7"),
        parse_chord("A7"),
    )
    assert secondary.authorized_for_chord is False
    assert secondary.functional_scope is AlteredDominantFunctionalScope.SECONDARY_DOMINANT


def test_secondary_backdoor_and_static_blues_dominants_are_distinct_scopes() -> None:
    secondary = resolve_altered_dominant_policy(
        _policy(scopes="secondary_dominants", previous="Cmaj7", next_symbol="Dm7"),
        parse_chord("A7"),
    )
    assert secondary.authorized_for_chord is True
    assert secondary.functional_scope is AlteredDominantFunctionalScope.SECONDARY_DOMINANT

    backdoor = resolve_altered_dominant_policy(
        _policy(scopes="backdoor_dominants", previous="Fm7", next_symbol="Cmaj7"),
        parse_chord("Bb7"),
    )
    assert backdoor.authorized_for_chord is True
    assert backdoor.functional_scope is AlteredDominantFunctionalScope.BACKDOOR_DOMINANT

    static = resolve_altered_dominant_policy(
        _policy(scopes="static_blues_dominants", previous="G7", next_symbol="G7"),
        parse_chord("G7"),
    )
    assert static.authorized_for_chord is True
    assert static.functional_scope is AlteredDominantFunctionalScope.STATIC_BLUES_DOMINANT

    functional_only = resolve_altered_dominant_policy(
        _policy(scopes="functional_dominants", previous="G7", next_symbol="G7"),
        parse_chord("G7"),
    )
    assert functional_only.authorized_for_chord is False
    assert functional_only.functional_scope is AlteredDominantFunctionalScope.STATIC_BLUES_DOMINANT


def test_llm_selected_scope_can_force_a_specific_region_without_global_dominant_spread() -> None:
    selected = resolve_altered_dominant_policy(
        _policy(scopes="llm_selected", current_region="A:4", selected_region_ids=["A:4"], next_symbol="G7"),
        parse_chord("G7"),
    )
    assert selected.authorized_for_chord is True
    assert selected.functional_scope is AlteredDominantFunctionalScope.LLM_SELECTED

    not_selected = resolve_altered_dominant_policy(
        _policy(scopes="llm_selected", current_region="A:5", selected_region_ids=["A:4"], next_symbol="G7"),
        parse_chord("G7"),
    )
    assert not_selected.authorized_for_chord is False


def test_plain_resolving_dominant_gets_altered_rooted_and_rootless_sources_only_when_authorized() -> None:
    rooted = plan_content_recipes(
        "G7",
        _policy(
            scopes="resolving_v7",
            previous="Dm7",
            next_symbol="Cmaj7",
            allowed_content=(ContentFamily.ROOTED_COLOR,),
        ),
    )
    assert any("rooted_color_4note_altered_dominant_source_1_3_b7_X" in recipe.validity_notes for recipe in rooted)
    assert any("altered_dominant_functional_scope_resolving_v7" in recipe.validity_notes for recipe in rooted)

    blocked = plan_content_recipes(
        "G7",
        _policy(
            scopes="resolving_v7",
            previous="G7",
            next_symbol="G7",
            allowed_content=(ContentFamily.ROOTED_COLOR,),
        ),
    )
    assert all("rooted_color_4note_altered_dominant_source_1_3_b7_X" not in recipe.validity_notes for recipe in blocked)

    rootless = plan_content_recipes(
        "G7",
        _policy(
            scopes="resolving_v7",
            previous="Dm7",
            next_symbol="Cmaj7",
            allowed_content=(ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B),
        ),
    )
    assert any("rootless_ab_content_type_altered_dominant_rootless" in recipe.validity_notes for recipe in rootless)
    assert any("altered_dominant_functional_scope_resolving_v7" in recipe.validity_notes for recipe in rootless)


def test_harmonic_motion_classifier_exposes_backdoor_and_static_dominant_context() -> None:
    backdoor = classify_functional_motion(chord_symbol="Bb7", next_chord_symbol="Cmaj7", previous_chord_symbol="Fm7")
    assert backdoor.is_backdoor_dominant
    assert backdoor.current_to_next_type == "backdoor_dominant"

    static = classify_functional_motion(chord_symbol="G7", next_chord_symbol="G7", previous_chord_symbol="C7")
    assert static.is_static_blues_dominant
    assert static.current_to_next_type == "static_blues_dominant"


def test_v2_2_88_contract_and_docs_are_updated() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"
    docs = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "VOICING_MODULE_CORE_LOGIC_V2.md",
        ROOT / "docs" / "VOICING_SYSTEM_V2_DESIGN.md",
        ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md",
    ]
    for path in docs:
        text = path.read_text(encoding="utf-8")
        assert "v2_2_88" in text, path
        assert "Altered Dominant Functional Scope" in text, path
        assert "LLM-selected altered dominant region" in text, path
