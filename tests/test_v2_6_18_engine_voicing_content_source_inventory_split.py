from __future__ import annotations

# harness token: test_v2_6_18_engine_voicing_content_source_inventory_behavior_preserving_split

import ast
from collections import Counter
import json
from pathlib import Path

from jammate_engine.core.harmony.chord_parser import parse_chord
from jammate_engine.core.harmony.material import chord_material
from jammate_engine.core.voicing.policy import ContentFamily, VoicingPolicy
from jammate_engine.core.voicing.sources import content_planner, content_source_inventory
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = Path(__file__).resolve().parents[1]
PLANNER = ROOT / "src/jammate_engine/core/voicing/sources/content_planner.py"
INVENTORY = ROOT / "src/jammate_engine/core/voicing/sources/content_source_inventory.py"
DOC = ROOT / "docs" / "ENGINE_VOICING_CONTENT_SOURCE_INVENTORY_SPLIT_V2_6_18.md"
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


def _recipe_signature(symbol: str, policy: VoicingPolicy) -> list[tuple[str, tuple[str, ...], tuple[str, ...]]]:
    return [
        (recipe.family.value, recipe.degree_names, tuple(recipe.validity_notes))
        for recipe in content_planner.plan_content_recipes(symbol, policy)
    ]


def _voicing_events(debug: dict) -> list[dict]:
    return [event.get("voicing") or {} for event in debug.get("piano_musical_audit_events", [])]


def test_v2_6_18_content_source_inventory_is_the_source_inventory_owner() -> None:
    inventory_symbols = _defined_symbols(INVENTORY)
    assert "content_degree_options" in inventory_symbols
    assert "trim_content_degrees" in inventory_symbols
    assert "content_validity_notes" in inventory_symbols
    assert "source_preserves_seventh_chord_identity" in inventory_symbols
    assert "seventh_chord_source_integrity_notes" in inventory_symbols
    assert "_rootless_ab_options" in inventory_symbols
    assert "_rooted_color_4note_source_inventory_options" in inventory_symbols
    assert "_seventh_basic_1357_options" in inventory_symbols
    assert "_four_note_triad_symbol_options" in inventory_symbols
    assert "CONTENT_SOURCE_INVENTORY_VERSION" not in _defined_symbols(INVENTORY)
    assert "CONTENT_SOURCE_INVENTORY_VERSION" in INVENTORY.read_text(encoding="utf-8")

    planner_symbols = _defined_symbols(PLANNER)
    assert "VoicingContentRecipe" in planner_symbols
    assert "choose_content_families" in planner_symbols
    assert "plan_content_recipes" in planner_symbols
    assert "choose_degrees" in planner_symbols
    assert "_content_degree_options" not in planner_symbols
    assert "_rootless_ab_options" not in planner_symbols
    assert "_rooted_color_4note_source_inventory_options" not in planner_symbols
    assert "_seventh_basic_1357_options" not in planner_symbols
    assert "_four_note_triad_symbol_options" not in planner_symbols

    planner_text = PLANNER.read_text(encoding="utf-8")
    assert "from .content_source_inventory import" in planner_text
    assert "content_degree_options" in planner_text
    assert "content_validity_notes" in planner_text


def test_v2_6_18_inventory_does_not_absorb_router_or_downstream_layers() -> None:
    inventory_text = INVENTORY.read_text(encoding="utf-8")
    assert "VoicingContentRecipe" not in inventory_text
    assert "describe_density_recipe" not in inventory_text
    assert "generate_accompaniment" not in inventory_text
    assert "choose_content_families" not in inventory_text
    assert "normalize_content_families_for_chord" not in inventory_text

    imports = _imported_top_level_modules(INVENTORY)
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


def test_v2_6_18_source_inventory_behavior_is_preserved_through_planner_facade() -> None:
    default_policy = VoicingPolicy()
    expanded_policy = VoicingPolicy.from_legacy_dict({
        "harmonic_expansion_enabled": True,
        "metadata": {"harmonic_expansion_enabled": True},
    })
    altered_policy = VoicingPolicy.from_legacy_dict({
        "allowed_content": ["rootless_a", "rooted_color"],
        "harmonic_expansion_enabled": True,
        "color_policy_mode": "altered_dominant",
        "metadata": {"harmonic_expansion_enabled": True},
    })

    signatures = {
        "C": _recipe_signature("C", default_policy),
        "Cmaj7": _recipe_signature("Cmaj7", expanded_policy),
        "Dm9": _recipe_signature("Dm9", default_policy),
        "G7alt": _recipe_signature("G7alt", altered_policy),
        "Bm7b5": _recipe_signature("Bm7b5", expanded_policy),
    }
    assert signatures["C"]
    assert any("R" in degrees for _, degrees, _ in signatures["C"])
    assert any("9" in degrees for _, degrees, _ in signatures["Cmaj7"])
    assert any(any("explicit" in note and "color" in note for note in notes) for _, _, notes in signatures["Dm9"])
    assert any("altered_dominant_natural_5_omitted" in notes for _, _, notes in signatures["G7alt"])
    assert any("half_diminished_b5_retained" in notes or "half_diminished_uses_generic_rootless_sources_via_harmony_resolution" in notes for _, _, notes in signatures["Bm7b5"])

    chord = parse_chord("G7alt")
    material = chord_material("G7alt")
    raw_options = content_source_inventory.content_degree_options(
        "G7alt",
        chord,
        material,
        ContentFamily.ROOTED_COLOR,
        altered_policy,
    )
    assert raw_options
    assert any("altered_dominant_natural_5_omitted" in notes for _, notes in raw_options)


def test_v2_6_18_doc_records_behavior_preserving_split() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_18_engine_voicing_content_source_inventory_behavior_preserving_split",
        "content_source_inventory.py",
        "content_planner.py remains the compatibility facade",
        "family -> degree source options",
        "does not own family routing / chord-quality normalization",
        "does not own disposition / register / projection",
        "5-note:6-note ~= 6:4",
        "maj7#11 remains off by default",
        "v2_6_19_engine_voicing_color_permission_adapter_cleanup",
    ):
        assert token in text


def test_v2_6_18_misty_density_and_color_guardrails_remain_unchanged(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_18.mid"),
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
