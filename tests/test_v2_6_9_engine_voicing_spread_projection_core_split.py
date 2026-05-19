from __future__ import annotations

import ast
from pathlib import Path

from jammate_engine.core.voicing.disposition import (
    SPREAD_PROJECTION_CORE_SPLIT_VERSION as package_projection_core_split_version,
    basic_spread_projection_debug as package_basic_projection_debug,
    project_basic_spread_candidates as package_project_candidates,
    project_basic_spread_contract as package_project_contract,
)
from jammate_engine.core.voicing.disposition.spread import (
    SPREAD_PROJECTION_CORE_SPLIT_VERSION as public_projection_core_split_version,
    basic_spread_projection_debug as public_basic_projection_debug,
    project_basic_spread_candidates as public_project_candidates,
    project_basic_spread_contract as public_project_contract,
)
from jammate_engine.core.voicing.disposition.spread_projection_core import (
    SPREAD_PROJECTION_CORE_SPLIT_VERSION as owner_projection_core_split_version,
    basic_spread_projection_debug as owner_basic_projection_debug,
    project_basic_spread_candidates as owner_project_candidates,
    project_basic_spread_contract as owner_project_contract,
)

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_SPREAD_PROJECTION_CORE_SPLIT_V2_6_9.md"
SPREAD = ROOT / "src" / "jammate_engine" / "core" / "voicing" / "disposition" / "spread.py"
SPREAD_PROJECTION_CORE = ROOT / "src" / "jammate_engine" / "core" / "voicing" / "disposition" / "spread_projection_core.py"
DEMO = ROOT / "demos" / "v2_6_9_misty_jazz_ballad_voicing_spread_projection_core_demo.mid"


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
    for result in public_project_candidates(chord):
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


def test_v2_6_9_projection_core_doc_exists_and_states_voicing_only_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "v2_6_9_engine_voicing_spread_projection_core_behavior_preserving_split",
        "behavior-preserving split",
        "spread_projection_core.py",
        "project_basic_spread_contract",
        "project_basic_spread_candidates",
        "basic_spread_projection_debug",
        "Public API Compatibility Rule",
        "jammate_engine.core.voicing.disposition.spread_projection_core",
        "does not own pattern",
        "does not own expression",
        "does not own MIDI",
        "notes-only lower+upper projection construction",
        "v2_6_9_misty_jazz_ballad_voicing_spread_projection_core_demo.mid",
        "v2_6_10_engine_voicing_spread_groupwise_voice_leading_behavior_preserving_split",
    ]
    for token in required:
        assert token in text


def test_v2_6_9_projection_core_symbols_have_single_owner_and_public_compatibility() -> None:
    owner_symbols = _defined_symbols(SPREAD_PROJECTION_CORE)
    spread_symbols = _defined_symbols(SPREAD)
    extracted_symbols = {
        "project_basic_spread_contract",
        "project_basic_spread_candidates",
        "basic_spread_projection_debug",
    }
    assert sorted(extracted_symbols - owner_symbols) == []
    assert extracted_symbols & spread_symbols == set()

    assert public_project_contract is owner_project_contract
    assert public_project_candidates is owner_project_candidates
    assert public_basic_projection_debug is owner_basic_projection_debug
    assert package_project_contract is owner_project_contract
    assert package_project_candidates is owner_project_candidates
    assert package_basic_projection_debug is owner_basic_projection_debug
    assert public_projection_core_split_version == owner_projection_core_split_version == package_projection_core_split_version == "v2_6_9"


def test_v2_6_9_projection_core_owner_does_not_import_non_voicing_layers() -> None:
    imports = _imported_modules(SPREAD_PROJECTION_CORE)
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

    text = SPREAD_PROJECTION_CORE.read_text(encoding="utf-8")
    forbidden_tokens = [
        "PatternEvent",
        "EventExpression",
        "NoteEvent",
        "PedalEvent",
        "velocity",
        "duration_beats",
        "write_midi",
    ]
    hits = [token for token in forbidden_tokens if token in text]
    assert hits == []


def test_v2_6_9_projection_debug_is_owned_by_projection_core_module() -> None:
    debug = public_basic_projection_debug("Cmaj7")
    assert debug["spread_projection_core_split_version"] == "v2_6_9"
    assert debug["owner"] == "core.voicing.disposition.spread_projection_core"
    assert debug["notes_only"] is True
    assert debug["no_expression_or_pedal"] is True
    assert debug["no_pattern_anticipation_gesture_or_midi"] is True
    assert len(debug["results"]) == 5


def test_v2_6_9_spread_projection_behavior_signature_matches_v2_6_10_active_spread_freeze() -> None:
    expected = {
        "Cmaj7": (
            ("spread_1plus4_contract", 2, ((36, 55, 64, 71, 72), ("R", "5", "3", "7", "R"), "drop3", 5, 19, True, True)),
            ("spread_2plus3_contract", 11, ((47, 48, 55, 59, 64), ("7", "R", "5", "7", "3"), "closed_upper_stack", 5, 7, True, True)),
            ("spread_2plus4_contract", 3, ((48, 52, 59, 64, 67, 72), ("R", "3", "7", "3", "5", "R"), "drop2", 6, 7, True, True)),
            ("spread_3plus3_contract", 11, ((36, 40, 47, 52, 55, 59), ("R", "3", "7", "3", "5", "7"), "closed_upper_stack", 6, 5, True, True)),
            ("spread_3plus4_contract", 3, ((36, 47, 52, 57, 64, 71, 74), ("R", "7", "3", "13", "3", "7", "9"), "drop3", 7, 5, True, True)),
        ),
        "G7b9": (
            ("spread_1plus4_contract", 2, ((43, 55, 65, 68, 71), ("R", "R", "b7", "b9", "3"), "drop3", 5, 12, True, True)),
            ("spread_2plus3_contract", 24, ((43, 47, 53, 56, 59), ("R", "3", "b7", "b9", "3"), "closed_upper_stack", 5, 6, True, True)),
            ("spread_2plus4_contract", 4, ((43, 47, 55, 65, 68, 71), ("R", "3", "R", "b7", "b9", "3"), "drop3", 6, 8, True, True)),
            ("spread_3plus3_contract", 17, ((43, 47, 53, 59, 62, 65), ("R", "3", "b7", "3", "5", "b7"), "closed_upper_stack", 6, 6, True, True)),
            ("spread_3plus4_contract", 0, None),
        ),
        "Bm7b5": (
            ("spread_1plus4_contract", 2, ((47, 57, 65, 71, 74), ("R", "b7", "b5", "R", "b3"), "drop3", 5, 10, True, True)),
            ("spread_2plus3_contract", 11, ((45, 47, 53, 57, 62), ("b7", "R", "b5", "b7", "b3"), "closed_upper_stack", 5, 6, True, True)),
            ("spread_2plus4_contract", 4, ((47, 50, 57, 65, 71, 74), ("R", "b3", "b7", "b5", "R", "b3"), "drop3", 6, 7, True, True)),
            ("spread_3plus3_contract", 10, ((47, 50, 57, 62, 65, 69), ("R", "b3", "b7", "b3", "b5", "b7"), "closed_upper_stack", 6, 5, True, True)),
            ("spread_3plus4_contract", 2, ((35, 45, 50, 57, 65, 72, 74), ("R", "b7", "b3", "b7", "b5", "b9", "b3"), "drop3", 7, 7, True, True)),
        ),
    }
    for chord, signature in expected.items():
        assert _first_legal_signature(chord) == signature


def test_v2_6_9_misty_demo_exists_and_is_midi_file_when_generated() -> None:
    if not DEMO.exists():
        return
    assert DEMO.read_bytes()[:4] == b"MThd"
    assert DEMO.stat().st_size > 1000
