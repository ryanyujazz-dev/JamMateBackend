from __future__ import annotations

# harness token: test_v2_6_16_engine_voicing_content_planner_boundary_split_plan

import ast
from collections import Counter
import json
from pathlib import Path

from jammate_engine.core.voicing.policy import VoicingPolicy
from jammate_engine.core.voicing.sources import color_permission, content_planner, source_balance, upper_structure
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = Path(__file__).resolve().parents[1]
CONTENT_PLANNER = ROOT / "src/jammate_engine/core/voicing/sources/content_planner.py"
COLOR_PERMISSION = ROOT / "src/jammate_engine/core/voicing/sources/color_permission.py"
SOURCE_BALANCE = ROOT / "src/jammate_engine/core/voicing/sources/source_balance.py"
UPPER_STRUCTURE = ROOT / "src/jammate_engine/core/voicing/sources/upper_structure.py"
DOC = ROOT / "docs" / "ENGINE_VOICING_CONTENT_PLANNER_BOUNDARY_SPLIT_PLAN_V2_6_16.md"
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


def test_v2_6_16_doc_records_content_planner_boundary_split_plan() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_16_engine_voicing_content_planner_boundary_split_plan",
        "content_family_router.py",
        "content_source_inventory.py",
        "color_permission.py",
        "source_balance.py",
        "upper_structure.py",
        "Upper Structure must not reimplement disposition projection",
        "5-note:6-note = 6:4",
        "maj7 prefers 9 / 13",
        "v2_6_17_engine_voicing_content_family_router_behavior_preserving_split",
    ):
        assert token in text


def test_v2_6_16_current_content_source_owners_are_explicit_and_importable() -> None:
    planner_symbols = _defined_symbols(CONTENT_PLANNER)
    assert "VoicingContentRecipe" in planner_symbols
    assert "choose_content_families" in planner_symbols
    assert "plan_content_recipes" in planner_symbols
    assert "choose_degrees" in planner_symbols
    assert "source_preserves_seventh_chord_identity" in planner_symbols
    assert "seventh_chord_source_integrity_notes" in planner_symbols

    color_symbols = _defined_symbols(COLOR_PERMISSION)
    assert "ColorPermissionContext" in color_symbols
    assert "build_color_permission_context" in color_symbols
    assert "four_note_color_permission_notes" in color_symbols
    assert "source_color_degrees" in color_symbols

    balance_symbols = _defined_symbols(SOURCE_BALANCE)
    assert "score_source_balance" in balance_symbols
    assert "score_altered_dominant_intensity_balance" in balance_symbols
    assert "source_balance_key" in balance_symbols

    upper_symbols = _defined_symbols(UPPER_STRUCTURE)
    assert "UpperStructureSource" in upper_symbols
    assert "plan_upper_structure_sources" in upper_symbols

    # Exercise public APIs lightly so this planning pass is tied to real objects,
    # not only to file names.
    recipes = content_planner.plan_content_recipes("Cmaj7", VoicingPolicy())
    assert recipes
    assert all(recipe.symbol == "Cmaj7" for recipe in recipes)
    assert color_permission.build_color_permission_context is not None
    assert source_balance.score_source_balance is not None
    assert upper_structure.plan_upper_structure_sources("Cmaj7", density=3, policy=VoicingPolicy()) == ()


def test_v2_6_16_content_planner_has_not_absorbed_non_voicing_layers() -> None:
    imports = _imported_top_level_modules(CONTENT_PLANNER)
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
    )
    for module in imports:
        assert not any(fragment in module for fragment in forbidden_fragments), module

    text = CONTENT_PLANNER.read_text(encoding="utf-8")
    for forbidden in (
        "NoteEvent(",
        "PedalEvent(",
        "midi_base64",
        "FluidSynth",
        "PatternTimeline",
        "AnticipationResolver",
    ):
        assert forbidden not in text


def test_v2_6_16_upper_structure_stays_source_only_and_projection_reusing() -> None:
    expanded_policy = VoicingPolicy.from_legacy_dict({
        "harmonic_expansion_enabled": True,
        "metadata": {
            "harmonic_expansion_enabled": True,
            "spread_upper_structure_enabled": True,
            "upper_structure": {"enabled": True},
        },
    })
    sources = upper_structure.plan_upper_structure_sources("Cmaj7", density=3, policy=expanded_policy)
    assert sources
    debug = sources[0].to_debug_dict()
    assert debug["source_only_no_projection"] is True
    assert debug["reuse_existing_closed_inversion_drop_projection"] is True
    assert "source_only_reuses_existing_projection" in debug["source_notes"]
    assert any("three_note_reuses_closed_inversion" in str(note) for note in debug["source_notes"])


def test_v2_6_16_misty_density_and_color_guardrails_remain_unchanged(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_16.mid"),
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
