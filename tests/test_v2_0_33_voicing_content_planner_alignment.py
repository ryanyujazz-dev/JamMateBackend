from __future__ import annotations

from jammate_engine.core.harmony import resolve_degree_token
from jammate_engine.core.voicing import (
    VOICING_CONTRACT_VERSION,
    VOICING_CORE_PIPELINE,
    ContentFamily,
    Disposition,
    RootSupportPolicy,
    VoicingPolicy,
    content_degree_names,
    content_degrees,
    generate_candidates,
    plan_content_recipes,
)


def test_voicing_content_planner_exports_v2_0_33_content_recipe_contract() -> None:
    assert VOICING_CONTRACT_VERSION >= "v2_0_33"
    assert "content_recipe" in VOICING_CORE_PIPELINE

    policy = VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        preferred_content=ContentFamily.ROOTLESS_A,
        preferred_disposition=Disposition.OPEN,
        preferred_density=4,
    )
    recipe = plan_content_recipes("G13", policy)[0]
    debug = recipe.to_debug_dict()

    assert recipe.family == ContentFamily.ROOTLESS_A
    assert recipe.degree_names == ("3", "13", "b7", "5")
    assert debug["density_recipe"]["recipe_id"] == "d4__unGrouped__rootless_A__rootless_allowed"
    assert debug["density_recipe"]["functional_grouping"] is None
    assert debug["harmony_material"]["available_tensions"] == ["9", "13"]
    assert "rootless_ab_explicit_chord_symbol_color_used" in recipe.validity_notes


def test_content_planner_preserves_triad_and_power_chord_foundations() -> None:
    policy = VoicingPolicy(root_support=RootSupportPolicy.ROOT_REQUIRED, preferred_density=3)
    expected = {
        "C": (ContentFamily.MAJOR_TRIAD, ("R", "3", "5")),
        "Cm": (ContentFamily.MINOR_TRIAD, ("R", "b3", "5")),
        "Cdim": (ContentFamily.DIMINISHED_TRIAD, ("R", "b3", "b5")),
        "Caug": (ContentFamily.AUGMENTED_TRIAD, ("R", "3", "#5")),
        "Csus2": (ContentFamily.SUS2_TRIAD, ("R", "2", "5")),
        "Csus4": (ContentFamily.SUS4_TRIAD, ("R", "4", "5")),
    }
    for symbol, (family, degrees) in expected.items():
        recipe = plan_content_recipes(symbol, policy)[0]
        assert recipe.family == family
        assert recipe.degree_names == degrees

    power = plan_content_recipes(
        "C",
        VoicingPolicy(
            root_support=RootSupportPolicy.ROOT_REQUIRED,
            preferred_content=ContentFamily.POWER_CHORD_5TH,
            preferred_density=2,
        ),
    )[0]
    assert power.degree_names == ("R", "5")
    assert power.density_recipe.functional_grouping.value == "2"


def test_content_resolver_consumes_harmony_alterations_for_color_content() -> None:
    rootless = content_degree_names("G7b9", ContentFamily.ROOTLESS_A, RootSupportPolicy.ROOTLESS_ALLOWED)
    rooted = content_degree_names("G7b9", ContentFamily.ROOTED_COLOR, RootSupportPolicy.ROOT_REQUIRED)
    altered = content_degree_names("G7alt", ContentFamily.ROOTLESS_A, RootSupportPolicy.ROOTLESS_ALLOWED)

    assert rootless == ["3", "b7", "b9", "13"]
    assert rooted == ["R", "3", "b7", "b9", "13"]
    assert altered == ["3", "b7", "b9", "#9"]


def test_voicing_literal_four_does_not_override_bassfoundation_next_root_legacy() -> None:
    sus4_degrees = content_degrees("Csus4", ContentFamily.SUS4_TRIAD, RootSupportPolicy.ROOT_REQUIRED)
    assert sus4_degrees == [("R", 0), ("4", 5), ("5", 7)]

    # Harmony's BassFoundation compatibility resolver still preserves legacy
    # bass vocabulary semantics where token 4 means nextR.  Voicing content
    # does not call that resolver for literal sus4 degrees.
    bass_legacy = resolve_degree_token(chord_symbol="C7", token="4", next_chord_symbol="Fmaj7")
    assert bass_legacy.degree == "nextR"
    assert bass_legacy.pitch_class == 5


def test_candidates_include_content_recipe_debug_without_changing_family_selection() -> None:
    policy = VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        preferred_content=ContentFamily.ROOTLESS_A,
        preferred_disposition=Disposition.OPEN,
        preferred_density=4,
        selector_temperature=0.0,
    )
    candidate = generate_candidates("G13", policy)[0]
    debug = candidate.to_debug_dict()

    assert set(candidate.degrees) == {"3", "5", "b7", "13"}
    assert debug["metadata"]["content_recipe"]["family"] == "rootless_A"
    assert debug["metadata"]["content_recipe"]["degree_names"] == ["3", "13", "b7", "5"]
    assert debug["metadata"]["density_recipe"]["recipe_id"] == debug["recipe_id"]
