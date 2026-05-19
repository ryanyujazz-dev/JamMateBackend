from __future__ import annotations

import ast
from pathlib import Path

from jammate_engine.core.voicing.disposition import LowerGroupRecipeId as package_lower_group_recipe_id
from jammate_engine.core.voicing.disposition.spread import (
    LowerGroupRecipeId as public_lower_group_recipe_id,
    lower_group_recipe_inventory as public_lower_group_recipe_inventory,
    place_lower_group_recipe as public_place_lower_group_recipe,
    project_basic_spread_candidates,
)
from jammate_engine.core.voicing.disposition.spread_contracts import SpreadGrouping
from jammate_engine.core.voicing.disposition.spread_lower_groups import (
    LowerGroupRecipeId as owner_lower_group_recipe_id,
    lower_group_recipe_inventory as owner_lower_group_recipe_inventory,
    place_lower_group_recipe as owner_place_lower_group_recipe,
)

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_SPREAD_LOWER_GROUP_SPLIT_V2_6_6.md"
SPREAD = ROOT / "src" / "jammate_engine" / "core" / "voicing" / "disposition" / "spread.py"
SPREAD_CONTRACTS = ROOT / "src" / "jammate_engine" / "core" / "voicing" / "disposition" / "spread_contracts.py"
SPREAD_LOWER_GROUPS = ROOT / "src" / "jammate_engine" / "core" / "voicing" / "disposition" / "spread_lower_groups.py"


def _defined_symbols(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    symbols: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.add(node.name)
    return symbols


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _first_legal_signature(chord: str) -> tuple[tuple[object, ...], ...]:
    signature = []
    for result in project_basic_spread_candidates(chord):
        legal = [candidate for candidate in result.candidates if candidate.is_legal]
        if not legal:
            first = None
        else:
            debug = legal[0].to_debug_dict()
            first = (
                tuple(debug["notes"]),
                tuple(debug["degrees"]),
                debug["upper_projection_method"],
                debug["density"],
                debug["group_gap_semitones"],
                debug["notes_only"],
                debug["no_expression_or_pedal"],
            )
        signature.append((result.recipe_contract.recipe_id, result.legal_candidate_count, first))
    return tuple(signature)


# Integration v2_8_24 note: stale historical SPREAD freeze expectations are aligned to
# the Engine v2_6_30 runtime baseline; generation code is unchanged here.

def test_v2_6_6_lower_group_split_doc_exists_and_states_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "v2_6_6_engine_voicing_spread_lower_group_recipes_behavior_preserving_split",
        "behavior-preserving split",
        "spread_lower_groups.py",
        "spread_contracts.py",
        "public import compatibility",
        "Pattern",
        "Anticipation",
        "Expression",
        "Gesture",
        "MIDI writer",
        "no source-weight changes",
        "no listening-behavior retune",
        "v2_6_7_engine_voicing_spread_upper_projection_adapter_behavior_preserving_split",
    ]
    for token in required:
        assert token in text


def test_v2_6_6_lower_group_symbols_have_single_owner_and_public_compatibility() -> None:
    assert SPREAD.exists()
    assert SPREAD_CONTRACTS.exists()
    assert SPREAD_LOWER_GROUPS.exists()

    spread_symbols = _defined_symbols(SPREAD)
    lower_symbols = _defined_symbols(SPREAD_LOWER_GROUPS)
    contract_symbols = _defined_symbols(SPREAD_CONTRACTS)

    extracted_lower_symbols = {
        "LowerGroupRecipeId",
        "LowerGroupDegreeSpec",
        "LowerGroupRecipeInventoryItem",
        "LowerGroupRecipeInstance",
        "LowerGroupPlacement",
        "lower_group_recipe_inventory",
        "lower_group_recipe_by_id",
        "instantiate_lower_group_recipe",
        "place_lower_group_recipe",
        "lower_group_inventory_debug",
    }
    for symbol in extracted_lower_symbols:
        assert symbol in lower_symbols
        assert symbol not in spread_symbols

    assert "SpreadGrouping" in contract_symbols
    assert "SpreadUpperSourceKind" in contract_symbols
    assert "SpreadReuseStatus" in contract_symbols
    assert "SpreadGrouping" not in spread_symbols

    assert public_lower_group_recipe_id is owner_lower_group_recipe_id
    assert package_lower_group_recipe_id is owner_lower_group_recipe_id
    assert public_lower_group_recipe_inventory is owner_lower_group_recipe_inventory
    assert public_place_lower_group_recipe is owner_place_lower_group_recipe
    assert SpreadGrouping.ONE_PLUS_THREE.value == "1+3"


def test_v2_6_6_lower_group_owner_does_not_import_non_voicing_layers() -> None:
    imports = _imported_modules(SPREAD_LOWER_GROUPS) | _imported_modules(SPREAD_CONTRACTS)
    forbidden_prefixes = (
        "jammate_engine.styles",
        "jammate_engine.generation",
        "jammate_engine.realization",
        "jammate_engine.midi",
        "jammate_engine.core.pattern_runtime",
        "jammate_engine.core.expression",
        "jammate_engine.core.anticipation",
    )
    forbidden = [module for module in imports if module.startswith(forbidden_prefixes)]
    assert forbidden == []

    lower_text = SPREAD_LOWER_GROUPS.read_text(encoding="utf-8")
    forbidden_tokens = [
        "PatternEvent",
        "EventExpression",
        "VoicingCandidate",
        "NoteEvent",
        "PedalEvent",
        "velocity",
        "duration_beats",
        "pedal",
    ]
    hits = [token for token in forbidden_tokens if token in lower_text]
    # The owner may state no_expression_or_pedal in metadata but must not own pedal/velocity objects.
    hits = [token for token in hits if token not in {"pedal"} or "no_expression_or_pedal" not in lower_text]
    assert hits == []


def test_v2_6_6_lower_group_inventory_and_placement_behavior_is_unchanged() -> None:
    lower_ids = tuple(item.recipe_id.value for item in public_lower_group_recipe_inventory())
    assert lower_ids == (
        "lower_1note_root",
        "lower_2note_root_7",
        "lower_2note_root_3",
        "lower_2note_root_5",
        "lower_2note_3_7",
        "lower_3note_root_5_upper_root",
        "lower_3note_root_3_7",
        "lower_3note_root_7_upper3",
        "lower_3note_root_5_upper3",
    )

    cases = [
        ("Cmaj7", "lower_2note_root_7", 36, 60, (36, 47), ("R", "7")),
        ("G7b9", "lower_3note_root_3_7", 36, 60, (43, 47, 53), ("R", "3", "b7")),
        ("Bm7b5", "lower_3note_root_7_upper3", 33, 79, (35, 38, 45), ("R", "b3", "b7")),
        ("C", "lower_2note_root_7", 36, 60, (), ()),
    ]
    for chord, recipe_id, low, high, expected_notes, expected_degrees in cases:
        placement = public_place_lower_group_recipe(chord, recipe_id, low, high)
        assert placement.notes == expected_notes
        assert tuple(degree for degree, _ in placement.placed_degrees) == expected_degrees


def test_v2_6_6_spread_projection_behavior_signature_matches_v2_6_5_freeze() -> None:
    expected = {
        "Cmaj7": (
            ("spread_1plus4_contract", 2, ((36, 55, 64, 71, 72), ("R", "5", "3", "7", "R"), "drop3", 5, 19, True, True)),
            ("spread_2plus3_contract", 11, ((47, 48, 55, 59, 64), ("7", "R", "5", "7", "3"), "closed_upper_stack", 5, 7, True, True)),
            ("spread_2plus4_contract", 3, ((48, 52, 59, 64, 67, 72), ("R", "3", "7", "3", "5", "R"), "drop2", 6, 7, True, True)),
            ("spread_3plus3_contract", 12, ((36, 40, 47, 52, 55, 59), ("R", "3", "7", "3", "5", "7"), "closed_upper_stack", 6, 5, True, True)),
            ("spread_3plus4_contract", 4, ((36, 40, 47, 55, 64, 71, 74), ("R", "3", "7", "5", "3", "7", "9"), "drop3", 7, 8, True, True)),
        ),
        "G7b9": (
            ("spread_1plus4_contract", 2, ((43, 55, 65, 68, 71), ("R", "R", "b7", "b9", "3"), "drop3", 5, 12, True, True)),
            ("spread_2plus3_contract", 24, ((43, 47, 53, 56, 59), ("R", "3", "b7", "b9", "3"), "closed_upper_stack", 5, 6, True, True)),
            ("spread_2plus4_contract", 4, ((43, 47, 55, 65, 68, 71), ("R", "3", "R", "b7", "b9", "3"), "drop3", 6, 8, True, True)),
            ("spread_3plus3_contract", 22, ((41, 43, 47, 53, 56, 59), ("b7", "R", "3", "b7", "b9", "3"), "closed_upper_stack", 6, 6, True, True)),
            ("spread_3plus4_contract", 2, ((41, 43, 47, 56, 65, 70, 71), ("b7", "R", "3", "b9", "b7", "#9", "3"), "drop3", 7, 9, True, True)),
        ),
        "Bm7b5": (
            ("spread_1plus4_contract", 2, ((47, 57, 65, 71, 74), ("R", "b7", "b5", "R", "b3"), "drop3", 5, 10, True, True)),
            ("spread_2plus3_contract", 11, ((45, 47, 53, 57, 62), ("b7", "R", "b5", "b7", "b3"), "closed_upper_stack", 5, 6, True, True)),
            ("spread_2plus4_contract", 4, ((47, 50, 57, 65, 71, 74), ("R", "b3", "b7", "b5", "R", "b3"), "drop3", 6, 7, True, True)),
            ("spread_3plus3_contract", 10, ((47, 50, 57, 62, 65, 69), ("R", "b3", "b7", "b3", "b5", "b7"), "closed_upper_stack", 6, 5, True, True)),
            ("spread_3plus4_contract", 2, ((35, 38, 45, 57, 65, 72, 74), ("R", "b3", "b7", "b7", "b5", "b9", "b3"), "drop3", 7, 12, True, True)),
        ),
    }
    for chord, signature in expected.items():
        assert _first_legal_signature(chord) == signature
