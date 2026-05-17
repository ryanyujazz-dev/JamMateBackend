from __future__ import annotations

# harness token: test_v2_2_54_global_seventh_chord_expansion_source_integrity_gate

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    GLOBAL_SEVENTH_CHORD_EXPANSION_SOURCE_INTEGRITY_GATE_VERSION,
    ContentFamily,
    ColorPolicyMode,
    RootSupportPolicy,
    VoicingPolicy,
    generate_candidates,
    plan_content_recipes,
    source_preserves_seventh_chord_identity,
)
from jammate_engine.core.voicing.disposition.spread import project_basic_spread_candidates


def _rooted_color_expansion_policy() -> VoicingPolicy:
    return VoicingPolicy(
        allowed_content=(ContentFamily.ROOTED_COLOR,),
        preferred_content=ContentFamily.ROOTED_COLOR,
        root_support=RootSupportPolicy.ROOT_OPTIONAL,
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
        min_density=4,
        preferred_density=4,
        max_density=4,
        max_voicing_span=28,
        metadata={"harmonic_expansion_target_families": [ContentFamily.ROOTED_COLOR.value]},
    )


def _rooted_color_recipes(symbol: str):
    return [recipe for recipe in plan_content_recipes(symbol, _rooted_color_expansion_policy()) if recipe.family == ContentFamily.ROOTED_COLOR]


def test_v2_2_54_version_and_gate_constant_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert GLOBAL_SEVENTH_CHORD_EXPANSION_SOURCE_INTEGRITY_GATE_VERSION == "v2_2_54"


def test_rooted_color_expansion_for_major_seventh_uses_1379_not_1359() -> None:
    recipes = _rooted_color_recipes("Ebmaj7")
    assert recipes
    first = recipes[0]
    assert first.degree_names == ("R", "3", "7", "9")
    assert source_preserves_seventh_chord_identity("Ebmaj7", first.degree_names)
    assert "rooted_color_4note_content_type_1_3_7_9" in first.validity_notes
    assert "rooted_color_4note_content_type_1359" not in first.validity_notes
    assert "seventh_chord_expansion_preserves_3_and_7" in first.validity_notes
    assert "triad_add9_source_blocked_for_seventh_chord" in first.validity_notes


def test_explicit_major_ninth_also_preserves_major_seventh_identity() -> None:
    recipes = _rooted_color_recipes("Cmaj9")
    assert recipes
    first = recipes[0]
    assert first.degree_names == ("R", "3", "7", "9")
    assert "rooted_color_4note_source_role_order_root_third_seventh_ninth" in first.validity_notes
    assert "rooted_color_4note_1_3_7_9_alias" in first.validity_notes
    assert "rooted_color_4note_1359_alias" not in first.validity_notes


def test_plain_add9_keeps_triad_add_source_path() -> None:
    recipes = _rooted_color_recipes("Cadd9")
    assert recipes
    first = recipes[0]
    assert first.degree_names == ("R", "3", "5", "9")
    assert not source_preserves_seventh_chord_identity("Cadd9", first.degree_names) is False
    assert "rooted_color_4note_content_type_1359" in first.validity_notes
    assert "seventh_chord_source_integrity_not_required_for_triad_or_add_chord" in first.validity_notes


def test_dominant_altered_rooted_source_still_preserves_3_and_7() -> None:
    recipes = _rooted_color_recipes("G7b9")
    assert recipes
    first = recipes[0]
    assert first.degree_names == ("R", "3", "b7", "b9")
    assert source_preserves_seventh_chord_identity("G7b9", first.degree_names)
    assert "rooted_color_4note_altered_dominant_source_1_3_b7_X" in first.validity_notes
    assert "seventh_chord_expansion_preserves_3_and_7" in first.validity_notes


def test_open_drop_candidate_for_ebmaj7_no_longer_uses_add9_source() -> None:
    candidates = generate_candidates("Ebmaj7", _rooted_color_expansion_policy())
    assert candidates
    for candidate in candidates:
        if candidate.metadata.get("rooted_color_4note_source_family"):
            assert candidate.metadata["rooted_color_4note_source_family"] != "root_third_fifth_ninth"
            assert candidate.metadata["rooted_color_4note_legacy_source_family_alias"] != "1359"
            assert "7" in candidate.degrees


def test_spread_1plus4_upper_source_for_ebmaj7_preserves_seventh_identity() -> None:
    policy = VoicingPolicy(
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
        metadata={"harmonic_expansion_target_families": [ContentFamily.ROOTED_COLOR.value]},
    )
    result = project_basic_spread_candidates(
        "Ebmaj7",
        policy=policy,
        contract_ids=("spread_1plus4_contract",),
        max_upper_options=4,
    )[0]
    assert result.candidates
    legal = [candidate for candidate in result.candidates if candidate.is_legal]
    assert legal
    for candidate in legal:
        if candidate.upper_source.source_family == ContentFamily.ROOTED_COLOR.value:
            assert candidate.upper_source.functional_source_type != "root_third_fifth_ninth"
            assert "7" in candidate.upper_source.degree_names
            assert source_preserves_seventh_chord_identity("Ebmaj7", candidate.upper_source.degree_names)
