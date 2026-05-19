from __future__ import annotations

# harness token: test_v2_6_17_engine_voicing_content_family_router_behavior_preserving_split

import ast
from collections import Counter
import json
from pathlib import Path

from jammate_engine.core.voicing.policy import ContentFamily, VoicingPolicy
from jammate_engine.core.voicing.sources import content_family_router, content_planner
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "src/jammate_engine/core/voicing/sources/content_family_router.py"
PLANNER = ROOT / "src/jammate_engine/core/voicing/sources/content_planner.py"
DOC = ROOT / "docs" / "ENGINE_VOICING_CONTENT_FAMILY_ROUTER_SPLIT_V2_6_17.md"
MISTY = ROOT / "examples" / "leadsheets" / "misty.json"


def _defined_symbols(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in module.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))}


def _imported_top_level_modules(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in module.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


def _voicing_events(debug: dict) -> list[dict]:
    return [event.get("voicing") or {} for event in debug.get("piano_musical_audit_events", [])]


def test_v2_6_17_content_family_router_is_the_family_routing_owner() -> None:
    router_symbols = _defined_symbols(ROUTER)
    assert "choose_content_families" in router_symbols
    assert "normalize_content_families_for_chord" in router_symbols
    assert "is_three_note_closed_request" in router_symbols
    assert "four_note_color_gate_open" in router_symbols
    assert "family_expansion_target_allowed" in router_symbols

    planner_symbols = _defined_symbols(PLANNER)
    assert "VoicingContentRecipe" in planner_symbols
    assert "choose_content_families" in planner_symbols  # compatibility wrapper
    assert "plan_content_recipes" in planner_symbols
    assert "choose_degrees" in planner_symbols
    assert "_normalize_content_families_for_chord" not in planner_symbols
    assert "_four_note_color_gate_open" not in planner_symbols
    assert "_is_three_note_closed_request" not in planner_symbols

    planner_text = PLANNER.read_text(encoding="utf-8")
    assert "choose_content_families as _route_content_families" in planner_text
    assert "return _route_content_families(symbol, policy)" in planner_text


def test_v2_6_17_router_does_not_absorb_source_inventory_or_downstream_layers() -> None:
    router_text = ROUTER.read_text(encoding="utf-8")
    assert "rootless_ab_options" not in router_text
    assert "seventh_basic_1357_options" not in router_text
    assert "VoicingContentRecipe" not in router_text
    assert "describe_density_recipe" not in router_text

    imports = _imported_top_level_modules(ROUTER)
    forbidden_fragments = (
        "jammate_engine.styles",
        "jammate_engine.realization",
        "jammate_engine.api",
        "jammate_engine.agent",
        "jammate_agent",
        "midi",
        "pattern",
        "expression",
        "gesture",
        "anticipation",
        "disposition",
        "selection",
    )
    for module in imports:
        assert not any(fragment in module for fragment in forbidden_fragments), module


def test_v2_6_17_content_family_routing_behavior_is_preserved_through_planner_facade() -> None:
    default_policy = VoicingPolicy()
    assert content_planner.choose_content_families("C", default_policy) == content_family_router.choose_content_families("C", default_policy)
    assert content_planner.choose_content_families("Cm", default_policy) == content_family_router.choose_content_families("Cm", default_policy)

    major_minor_policy = VoicingPolicy.from_legacy_dict({
        "allowed_content": ["major_triad", "minor_triad", "rootless_a", "seventh_basic"],
    })
    assert content_planner.choose_content_families("C", major_minor_policy) == [ContentFamily.MAJOR_TRIAD]
    assert content_planner.choose_content_families("Cm", major_minor_policy) == [ContentFamily.MINOR_TRIAD]

    altered_policy = VoicingPolicy.from_legacy_dict({"allowed_content": ["seventh_basic"]})
    assert ContentFamily.ROOTED_COLOR in content_planner.choose_content_families("G7alt", altered_policy)
    assert ContentFamily.SEVENTH_BASIC not in content_planner.choose_content_families("G7alt", altered_policy)

    expanded_policy = VoicingPolicy.from_legacy_dict({
        "harmonic_expansion_enabled": True,
        "metadata": {"harmonic_expansion_enabled": True},
    })
    recipes = content_planner.plan_content_recipes("Cmaj7", expanded_policy)
    assert recipes
    assert all(recipe.symbol == "Cmaj7" for recipe in recipes)


def test_v2_6_17_doc_records_behavior_preserving_split() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_17_engine_voicing_content_family_router_behavior_preserving_split",
        "content_family_router.py",
        "content_planner.py remains the compatibility facade",
        "source inventory stays in content_planner.py",
        "does not own disposition / register / projection",
        "5-note:6-note ~= 6:4",
        "maj7#11 remains off by default",
        "v2_6_18_engine_voicing_content_source_inventory_behavior_preserving_split",
    ):
        assert token in text


def test_v2_6_17_misty_density_and_color_guardrails_remain_unchanged(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_17.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    voicings = _voicing_events(result.debug)
    densities = Counter(int(voicing.get("density", 0)) for voicing in voicings)
    groupings = Counter(str(voicing.get("functional_grouping")) for voicing in voicings)

    assert densities[4] == 0
    assert "1+3" not in groupings
    assert "2+2" not in groupings
    five = densities[5]
    six = densities[6]
    ratio = five / float(five + six)
    assert 0.58 <= ratio <= 0.62
    assert densities[7] <= 3

    maj7_sharp11 = [
        voicing
        for voicing in voicings
        if "maj7" in str(voicing.get("chord_symbol"))
        and any(str(degree) == "#11" for degree in voicing.get("degrees", []))
    ]
    assert maj7_sharp11 == []
