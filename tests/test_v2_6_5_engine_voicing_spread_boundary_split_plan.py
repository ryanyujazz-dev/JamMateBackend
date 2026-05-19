from __future__ import annotations

import ast
from pathlib import Path

from jammate_engine.core.voicing.disposition.spread import (
    lower_group_recipe_inventory,
    project_basic_spread_candidates,
    spread_recipe_contract_skeleton,
)

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_SPREAD_BOUNDARY_SPLIT_PLAN_V2_6_5.md"
SPREAD = ROOT / "src" / "jammate_engine" / "core" / "voicing" / "disposition" / "spread.py"


def _defined_symbols(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    symbols: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.add(node.name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                symbols.add(alias.asname or alias.name)
    return symbols


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


def test_v2_6_5_spread_split_plan_doc_exists_and_names_real_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")

    required_tokens = [
        "v2_6_5_engine_voicing_spread_boundary_split_plan",
        "behavior-preserving cleanup",
        "SPREAD is a voicing **disposition/projection** family",
        "spread/contracts.py",
        "spread/lower_groups.py",
        "spread/upper_sources.py",
        "spread/register_guards.py",
        "spread/projection.py",
        "spread/voice_leading.py",
        "spread/runtime_gate.py",
        "spread/runtime_adapter.py",
        "spread/ballad_runtime.py",
        "Public API Compatibility Rule",
        "Behavior-Signature Gates Before Any Split",
        "v2_6_6 — Lower group extraction",
        "Do not create all files in one pass",
    ]
    for token in required_tokens:
        assert token in text

    # The plan must discuss current symbols, not an idealized rewrite.
    real_symbols = [
        "SpreadGrouping",
        "LowerGroupRecipeId",
        "SpreadRecipeContract",
        "SpreadProjectionCandidate",
        "lower_group_recipe_inventory",
        "adapt_spread_upper_source",
        "SpreadProjectionRegisterPolicy",
        "project_basic_spread_candidates",
        "score_spread_groupwise_voice_leading",
        "spread_projection_candidate_to_voicing_candidate_adapter",
    ]
    for symbol in real_symbols:
        assert symbol in text


def test_v2_6_5_spread_current_symbol_inventory_matches_split_plan_symbols() -> None:
    symbols = _defined_symbols(SPREAD)
    planned_symbols = {
        "SpreadGrouping",
        "SpreadUpperSourceKind",
        "LowerGroupRecipeId",
        "LowerGroupRecipeInventoryItem",
        "LowerGroupPlacement",
        "UpperSourceRef",
        "SpreadRecipeContract",
        "SpreadProjectionRegisterPolicy",
        "SpreadProjectionCandidate",
        "SpreadProjectionResult",
        "lower_group_recipe_inventory",
        "instantiate_lower_group_recipe",
        "place_lower_group_recipe",
        "spread_upper_source_refs",
        "adapt_spread_upper_source",
        "basic_spread_register_policy",
        "project_basic_spread_contract",
        "project_basic_spread_candidates",
        "score_spread_groupwise_voice_leading",
        "select_spread_candidate_with_runtime_gate",
        "spread_projection_candidate_to_voicing_candidate_adapter",
    }
    missing = sorted(planned_symbols - symbols)
    assert missing == []


def test_v2_6_5_spread_active_contract_and_lower_inventory_signature_is_frozen() -> None:
    lower_ids = tuple(item.recipe_id.value for item in lower_group_recipe_inventory())
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

    contract_signature = tuple(
        (
            contract.recipe_id,
            contract.grouping.value,
            contract.lower_group.note_count,
            contract.upper_source.note_count,
            contract.density,
            contract.notes_only,
            contract.expression_allowed_in_this_layer,
            contract.runtime_enabled,
        )
        for contract in spread_recipe_contract_skeleton()
    )
    assert contract_signature == (
        ("spread_1plus4_contract", "1+4", 1, 4, 5, True, False, False),
        ("spread_2plus3_contract", "2+3", 2, 3, 5, True, False, False),
        ("spread_2plus4_contract", "2+4", 2, 4, 6, True, False, False),
        ("spread_3plus3_contract", "3+3", 3, 3, 6, True, False, False),
        ("spread_3plus4_contract", "3+4", 3, 4, 7, True, False, False),
    )


def test_v2_6_5_spread_projection_active_spread_behavior_signature_is_frozen() -> None:
    # Integration v2_8_24 note: this historical freeze expectation is aligned to
    # the Engine v2_6_30 runtime baseline; generation code is unchanged here.
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


def test_v2_6_5_no_split_implementation_or_listening_behavior_change_in_this_task() -> None:
    spread_package_dir = SPREAD.parent / "spread"
    assert SPREAD.exists()
    assert not spread_package_dir.exists(), "v2_6_5 is a split plan only; implementation starts in v2_6_6."

    text = DOC.read_text(encoding="utf-8")
    forbidden_behavior_changes = [
        "source weights",
        "style voicing policies",
        "harmonic expansion policy",
        "altered dominant policy",
        "MIDI output timing/pedal/realization behavior",
    ]
    for token in forbidden_behavior_changes:
        assert token in text
