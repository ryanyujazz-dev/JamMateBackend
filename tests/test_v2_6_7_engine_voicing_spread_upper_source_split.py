from __future__ import annotations

import ast
from pathlib import Path

from jammate_engine.core.voicing.disposition import UpperSourceRef as package_upper_source_ref
from jammate_engine.core.voicing.disposition.spread import (
    SpreadUpperSourceOption as public_upper_source_option,
    UpperSourceRef as public_upper_source_ref,
    _spread_allowed_upper_4note_projection_methods,
    adapt_spread_upper_source,
    project_basic_spread_candidates,
    spread_upper_source_adapter_debug,
)
from jammate_engine.core.voicing.disposition.spread_upper_sources import (
    SpreadUpperSourceOption as owner_upper_source_option,
    UpperSourceRef as owner_upper_source_ref,
    adapt_spread_upper_source_from_ref,
)

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_SPREAD_UPPER_SOURCE_SPLIT_V2_6_7.md"
SPREAD = ROOT / "src" / "jammate_engine" / "core" / "voicing" / "disposition" / "spread.py"
SPREAD_UPPER_SOURCES = ROOT / "src" / "jammate_engine" / "core" / "voicing" / "disposition" / "spread_upper_sources.py"


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


def _upper_adapter_signature(chord: str, ref_id: str) -> tuple[tuple[object, ...], ...]:
    result = adapt_spread_upper_source(chord, ref_id)
    return tuple(
        (
            option.source_family,
            option.degree_names,
            option.functional_source_type,
            option.orientation_token,
            option.projection_methods,
            option.final_placed_result_reuse_allowed,
            option.notes_only,
            option.runtime_enabled,
        )
        for option in result.options[:8]
    )


def test_v2_6_7_upper_source_split_doc_exists_and_states_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "v2_6_7_engine_voicing_spread_upper_projection_adapter_behavior_preserving_split",
        "behavior-preserving split",
        "spread_upper_sources.py",
        "UpperSourceRef",
        "SpreadUpperSourceOption",
        "SpreadUpperSourceAdapterResult",
        "adapt_spread_upper_source_from_ref",
        "Public API Compatibility Rule",
        "source-oriented upper adapter",
        "notes-only and source-oriented",
        "no source-weight changes",
        "no listening-behavior retune",
        "v2_6_8_engine_voicing_spread_register_guard_behavior_preserving_split",
    ]
    for token in required:
        assert token in text


def test_v2_6_7_upper_source_symbols_have_single_owner_and_public_compatibility() -> None:
    assert SPREAD.exists()
    assert SPREAD_UPPER_SOURCES.exists()

    spread_symbols = _defined_symbols(SPREAD)
    owner_symbols = _defined_symbols(SPREAD_UPPER_SOURCES)

    extracted_symbols = {
        "UpperSourceRef",
        "SpreadUpperSourceOption",
        "SpreadUpperSourceAdapterResult",
        "adapt_spread_upper_source_from_ref",
    }
    for symbol in extracted_symbols:
        assert symbol in owner_symbols
        assert symbol not in spread_symbols

    assert public_upper_source_ref is owner_upper_source_ref
    assert package_upper_source_ref is owner_upper_source_ref
    assert public_upper_source_option is owner_upper_source_option

    # The compatibility wrapper still accepts the historic string ref API.
    ref = public_upper_source_ref(
        ref_id="test_upper_3note",
        note_count=3,
        kind=next(ref.kind for ref in [adapt_spread_upper_source("Cmaj7", "upper_3note_existing_content_source_ref").upper_source_ref]),
        reusable_owner_paths=("core.voicing.sources.content_planner",),
    )
    direct = adapt_spread_upper_source_from_ref("Cmaj7", ref)
    assert direct.upper_source_ref is ref


def test_v2_6_7_upper_source_owner_does_not_import_non_voicing_layers() -> None:
    imports = _imported_modules(SPREAD_UPPER_SOURCES)
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

    text = SPREAD_UPPER_SOURCES.read_text(encoding="utf-8")
    forbidden_tokens = [
        "PatternEvent",
        "EventExpression",
        "NoteEvent",
        "PedalEvent",
        "velocity",
        "duration_beats",
    ]
    hits = [token for token in forbidden_tokens if token in text]
    assert hits == []


def test_v2_6_7_upper_adapter_behavior_signatures_are_unchanged() -> None:
    assert _upper_adapter_signature("G7b9", "upper_3note_existing_content_source_ref")[:3] == (
        ("shell_plus_5", ("3", "b7", "5"), "third_seventh_fifth", "three_note_degree_order_3_flat7_5", (), False, True, False),
        ("shell_plus_5", ("3", "b7", "R"), "third_seventh_root", "three_note_degree_order_3_flat7_R", (), False, True, False),
        ("shell_plus_color", ("3", "b7", "b9"), "third_seventh_altered_color", "three_note_degree_order_3_flat7_flat9", (), False, True, False),
    )

    assert _upper_adapter_signature("Cmaj7", "upper_4note_drop2_drop3_derived_source_ref")[:4] == (
        ("seventh_chord_basic", ("R", "3", "5", "7"), "root_third_fifth_seventh", "basic_4note_inversion_index_0", ("drop2", "drop3"), False, True, False),
        ("seventh_chord_basic", ("3", "5", "7", "R"), "root_third_fifth_seventh", "basic_4note_inversion_index_1", ("drop2", "drop3"), False, True, False),
        ("seventh_chord_basic", ("5", "7", "R", "3"), "root_third_fifth_seventh", "basic_4note_inversion_index_2", ("drop2", "drop3"), False, True, False),
        ("seventh_chord_basic", ("7", "R", "3", "5"), "root_third_fifth_seventh", "basic_4note_inversion_index_3", ("drop2", "drop3"), False, True, False),
    )

    assert _spread_allowed_upper_4note_projection_methods(("DROP2", "DROP2&4", "DROP3")) == ("drop2", "drop3")
    debug = spread_upper_source_adapter_debug("Dm7")
    assert debug["layer"] == "core.voicing.disposition.spread"
    assert debug["implementation_owner"] == "core.voicing.disposition.spread_upper_sources"
    assert debug["notes_only"] is True
    assert debug["no_expression_or_pedal"] is True


def test_v2_6_7_spread_projection_behavior_signature_matches_v2_6_10_active_spread_freeze() -> None:
    expected_subset = {
        "Cmaj7": (
            ("spread_1plus4_contract", 2, ((36, 55, 64, 71, 72), ("R", "5", "3", "7", "R"), "drop3", 5, 19, True, True)),
        ),
        "G7b9": (
            ("spread_1plus4_contract", 2, ((43, 55, 65, 68, 71), ("R", "R", "b7", "b9", "3"), "drop3", 5, 12, True, True)),
        ),
        "Bm7b5": (
            ("spread_1plus4_contract", 2, ((47, 57, 65, 71, 74), ("R", "b7", "b5", "R", "b3"), "drop3", 5, 10, True, True)),
        ),
    }
    for chord, expected_prefix in expected_subset.items():
        assert _first_legal_signature(chord)[:1] == expected_prefix
