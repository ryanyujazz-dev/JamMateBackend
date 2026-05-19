from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from jammate_engine.core.voicing import ContentFamily, RootSupportPolicy
from jammate_engine.core.voicing.disposition.spread import project_basic_spread_candidates
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy


def _degree_names(recipes):
    return {tuple(recipe.degree_names) for recipe in recipes}


def test_ballad_default_major_seventh_safe_extensions_prioritize_9_and_13_not_unnotated_sharp11():
    policy = get_voicing_policy()
    upper3_policy = replace(
        policy,
        allowed_content=(ContentFamily.SHELL_PLUS_COLOR,),
        preferred_content=None,
        root_support=RootSupportPolicy.ROOT_OPTIONAL,
        preferred_density=3,
        min_density=3,
        max_density=3,
    )

    recipes = plan_content_recipes("Ebmaj7", upper3_policy)
    degree_sets = _degree_names(recipes)

    assert ("3", "7", "9") in degree_sets
    assert ("3", "7", "13") in degree_sets
    assert all("#11" not in degrees for degrees in degree_sets)


def test_explicit_maj7_sharp11_chart_symbol_remains_faithful():
    policy = get_voicing_policy()
    recipes = plan_content_recipes("Ebmaj7#11", policy)

    assert any("#11" in recipe.degree_names for recipe in recipes)
    assert any(
        "explicit_sharp_eleventh_source_family" in recipe.validity_notes
        for recipe in recipes
        if "#11" in recipe.degree_names
    )


def test_harmonic_color_intent_can_enable_unnotated_maj7_sharp11():
    policy = get_voicing_policy()
    upper3_policy = replace(
        policy,
        allowed_content=(ContentFamily.SHELL_PLUS_COLOR,),
        preferred_content=None,
        root_support=RootSupportPolicy.ROOT_OPTIONAL,
        preferred_density=3,
        min_density=3,
        max_density=3,
        metadata={**policy.metadata, "harmonic_color_intent": "lydian"},
    )

    recipes = plan_content_recipes("Ebmaj7", upper3_policy)

    assert any("#11" in recipe.degree_names for recipe in recipes)


def test_ballad_spread_default_upper_source_gate_excludes_unnotated_maj7_sharp11():
    policy = get_voicing_policy()
    results = project_basic_spread_candidates(
        "Ebmaj7",
        policy,
        contract_ids=("spread_2plus3_contract",),
        max_upper_options=20,
    )
    candidates = [candidate for result in results for candidate in result.candidates]

    assert candidates
    assert all("#11" not in candidate.upper_source.degree_names for candidate in candidates)


def test_ballad_misty_runtime_default_demo_has_no_unnotated_maj7_sharp11(tmp_path):
    leadsheet = json.loads(Path("examples/leadsheets/misty.json").read_text())
    out = tmp_path / "misty_v2_6_11_color_gate.mid"
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 74,
            "choruses": 1,
            "seed": 26911,
            "output_path": str(out),
        }
    )

    assert result.ok
    assert out.exists()
    audit_events = result.debug.get("piano_musical_audit_events", [])
    maj7_events = [
        event for event in audit_events
        if "maj7" in str(event.get("pattern_event", {}).get("chord_symbol", ""))
    ]
    assert maj7_events
    assert all("#11" not in event.get("voicing", {}).get("degrees", []) for event in maj7_events)
