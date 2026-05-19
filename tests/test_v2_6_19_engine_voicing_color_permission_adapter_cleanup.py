from __future__ import annotations

# harness token: test_v2_6_19_engine_voicing_color_permission_adapter_cleanup

import ast
from collections import Counter
import json
from pathlib import Path

from jammate_engine.core.harmony.chord_parser import parse_chord
from jammate_engine.core.harmony.material import chord_material
from jammate_engine.core.voicing.policy import ContentFamily, VoicingPolicy
from jammate_engine.core.voicing.sources import color_permission, content_planner, content_source_inventory
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = Path(__file__).resolve().parents[1]
COLOR_PERMISSION = ROOT / "src/jammate_engine/core/voicing/sources/color_permission.py"
INVENTORY = ROOT / "src/jammate_engine/core/voicing/sources/content_source_inventory.py"
ROUTER = ROOT / "src/jammate_engine/core/voicing/sources/content_family_router.py"
DOC = ROOT / "docs" / "ENGINE_VOICING_COLOR_PERMISSION_ADAPTER_CLEANUP_V2_6_19.md"
MISTY = ROOT / "examples" / "leadsheets" / "misty.json"


def _defined_symbols(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in module.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))}


def _recipe_signature(symbol: str, policy: VoicingPolicy) -> list[tuple[str, tuple[str, ...], tuple[str, ...]]]:
    return [
        (recipe.family.value, recipe.degree_names, tuple(recipe.validity_notes))
        for recipe in content_planner.plan_content_recipes(symbol, policy)
    ]


def _voicing_events(debug: dict) -> list[dict]:
    return [event.get("voicing") or {} for event in debug.get("piano_musical_audit_events", [])]


def test_v2_6_19_color_permission_owns_admission_context_not_source_inventory() -> None:
    color_symbols = _defined_symbols(COLOR_PERMISSION)
    assert "ColorPermissionContext" in color_symbols
    assert "build_color_permission_context" in color_symbols
    assert "build_voicing_color_permission_context" in color_symbols
    assert "explicit_symbol_color_degrees" in color_symbols
    assert "rootless_ab_explicit_color_degrees" in color_symbols
    assert "ordered_explicit_colors" in color_symbols
    assert "expansion_color_candidates" in color_symbols
    assert "major_seventh_safe_extension_preference" in color_symbols
    assert "major_seventh_sharp11_harmonic_color_intent_enabled" in color_symbols
    assert "COLOR_PERMISSION_ADAPTER_VERSION" in COLOR_PERMISSION.read_text(encoding="utf-8")

    inventory_symbols = _defined_symbols(INVENTORY)
    assert "_color_permission_context" not in inventory_symbols
    assert "_explicit_symbol_color_degrees" not in inventory_symbols
    assert "_rootless_ab_explicit_color_degrees" not in inventory_symbols
    assert "_ordered_explicit_colors" not in inventory_symbols
    assert "_expansion_color_candidates" not in inventory_symbols
    assert "_major_seventh_safe_extension_preference" not in inventory_symbols
    assert "_major_seventh_sharp11_harmonic_color_intent_enabled" not in inventory_symbols

    inventory_text = INVENTORY.read_text(encoding="utf-8")
    assert "build_voicing_color_permission_context as _color_permission_context" in inventory_text
    assert "explicit_symbol_color_degrees as _explicit_symbol_color_degrees" in inventory_text
    assert "expansion_color_candidates as _expansion_color_candidates" in inventory_text
    assert "ALTERED_DOMINANT_PALETTE" not in inventory_text
    assert "build_color_permission_context" not in inventory_text


def test_v2_6_19_router_reuses_color_permission_explicit_color_helpers() -> None:
    router_symbols = _defined_symbols(ROUTER)
    assert "_explicit_symbol_color_degrees" not in router_symbols
    assert "_rootless_ab_explicit_color_degrees" not in router_symbols

    router_text = ROUTER.read_text(encoding="utf-8")
    assert "explicit_symbol_color_degrees as _explicit_symbol_color_degrees" in router_text
    assert "rootless_ab_explicit_color_degrees as _rootless_ab_explicit_color_degrees" in router_text
    assert "build_voicing_color_permission_context" not in router_text
    assert "content_degree_options" not in router_text


def test_v2_6_19_color_permission_context_behavior_is_preserved() -> None:
    expanded_policy = VoicingPolicy.from_legacy_dict({
        "harmonic_expansion_enabled": True,
        "metadata": {"harmonic_expansion_enabled": True},
    })
    lydian_policy = VoicingPolicy.from_legacy_dict({
        "harmonic_expansion_enabled": True,
        "metadata": {"harmonic_expansion_enabled": True, "lydian_major_color_enabled": True},
    })

    cmaj7 = parse_chord("Cmaj7")
    cmaj7_material = chord_material("Cmaj7")
    default_context = color_permission.build_voicing_color_permission_context(cmaj7, cmaj7_material, expanded_policy)
    assert default_context.explicit == frozenset()
    assert default_context.expansion == frozenset({"9", "13"})
    assert "#11" not in default_context.allowed

    lydian_context = color_permission.build_voicing_color_permission_context(cmaj7, cmaj7_material, lydian_policy)
    assert "#11" in lydian_context.allowed

    explicit_sharp11_context = color_permission.build_voicing_color_permission_context(
        parse_chord("Cmaj7#11"),
        chord_material("Cmaj7#11"),
        expanded_policy,
    )
    assert "#11" in explicit_sharp11_context.explicit
    assert "#11" in explicit_sharp11_context.allowed

    assert color_permission.explicit_symbol_color_degrees(parse_chord("Bm7b5")) == set()
    assert color_permission.explicit_symbol_color_degrees(parse_chord("Bm9b5")) == {"9"}


def test_v2_6_19_source_inventory_behavior_is_preserved_through_adapter() -> None:
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
        "Cmaj7#11": _recipe_signature("Cmaj7#11", expanded_policy),
        "G7alt": _recipe_signature("G7alt", altered_policy),
        "Bm7b5": _recipe_signature("Bm7b5", expanded_policy),
    }
    assert signatures["C"]
    assert any("9" in degrees for _, degrees, _ in signatures["Cmaj7"])
    assert not any("#11" in degrees for _, degrees, _ in signatures["Cmaj7"])
    assert any("#11" in degrees for _, degrees, _ in signatures["Cmaj7#11"])
    assert any("altered_dominant_natural_5_omitted" in notes for _, _, notes in signatures["G7alt"])
    assert any(
        "half_diminished_b5_retained" in notes
        or "half_diminished_uses_generic_rootless_sources_via_harmony_resolution" in notes
        for _, _, notes in signatures["Bm7b5"]
    )

    chord = parse_chord("G7alt")
    raw_options = content_source_inventory.content_degree_options(
        "G7alt",
        chord,
        chord_material("G7alt"),
        ContentFamily.ROOTED_COLOR,
        altered_policy,
    )
    assert raw_options
    assert any("altered_dominant_natural_5_omitted" in notes for _, notes in raw_options)


def test_v2_6_19_doc_records_color_permission_adapter_cleanup() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_19_engine_voicing_color_permission_adapter_cleanup",
        "color_permission.py",
        "content_source_inventory.py remains the source-construction owner",
        "does not construct voicing sources",
        "explicit_symbol_color_degrees",
        "build_voicing_color_permission_context",
        "5-note:6-note ~= 6:4",
        "maj7#11 remains off by default",
        "v2_6_20_engine_voicing_source_balance_boundary_cleanup",
    ):
        assert token in text


def test_v2_6_19_misty_density_and_color_guardrails_remain_unchanged(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_19.mid"),
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
