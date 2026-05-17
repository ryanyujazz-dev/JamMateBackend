from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION, build_voicing_override_policy
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates

ROOT = Path(__file__).resolve().parents[1]


def _policy(preset: str = "shell_plus_specified_color"):
    return build_voicing_override_policy({"max_voicing_span": 16}, {"enabled": True, "preset": preset}, style_name="medium_swing")


def _source_types(symbol: str, preset: str = "shell_plus_specified_color") -> set[str]:
    out: set[str] = set()
    for recipe in plan_content_recipes(symbol, _policy(preset)):
        for note in recipe.validity_notes:
            if note.startswith("three_note_functional_source_type_"):
                out.add(note.removeprefix("three_note_functional_source_type_"))
    return out


def _validity_notes(symbol: str, preset: str = "shell_plus_specified_color") -> list[str]:
    notes: list[str] = []
    for recipe in plan_content_recipes(symbol, _policy(preset)):
        notes.extend(recipe.validity_notes)
    return notes


def _degree_sets(symbol: str, preset: str = "shell_plus_specified_color") -> set[tuple[str, ...]]:
    return {tuple(recipe.degree_names) for recipe in plan_content_recipes(symbol, _policy(preset))}


def test_v2_1_40_versions_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_OVERRIDE_CONTRACT_VERSION == "v2_1_43"


def test_plain_triads_are_real_three_note_sources_not_partial_fallbacks() -> None:
    assert _source_types("C") == {"root_third_fifth"}
    assert _source_types("Cm") == {"root_third_fifth"}
    for symbol in ("C", "Cm"):
        notes = _validity_notes(symbol)
        assert "three_note_no_seventh_chord_not_partial_fallback" in notes
        assert not any("plain_triad_partial_source" in note for note in notes)


def test_add_sixth_and_sus_symbols_use_functional_triad_add_sus_sources() -> None:
    assert _source_types("Cadd9") == {"root_third_ninth"}
    assert _source_types("Cmadd9") == {"root_third_ninth"}
    assert _degree_sets("Cmadd9") == {("R", "b3", "9")}
    assert _source_types("C6") == {"root_third_sixth"}
    assert _source_types("C6/9") == {"root_third_sixth", "root_third_ninth"}
    assert _source_types("Csus2") == {"root_second_fifth"}
    assert _source_types("Csus4") == {"root_fourth_fifth"}


def test_triad_harmonic_expansion_stays_low_order_not_jazz_upper_shell() -> None:
    source_types = _source_types("C", preset="shell_plus_expanded_color")
    assert source_types == {
        "root_third_fifth",
        "root_third_sixth",
        "root_third_ninth",
        "root_third_seventh",
    }
    assert "third_seventh_ninth" not in source_types
    assert "third_seventh_eleventh" not in source_types
    assert "third_seventh_thirteenth" not in source_types
    notes = _validity_notes("C", preset="shell_plus_expanded_color")
    assert "triad_harmonic_expansion_low_order_add9" in notes
    assert "triad_harmonic_expansion_low_order_sixth" in notes
    assert "triad_harmonic_expansion_low_order_seventh" in notes


def test_triad_aware_sources_still_use_strict_closed_generation() -> None:
    policy = _policy("shell_plus_specified_color")
    candidates = generate_candidates("Cadd9", policy)
    assert candidates
    assert {candidate.density for candidate in candidates} == {3}
    assert {candidate.disposition.value for candidate in candidates} == {"closed"}
    for candidate in candidates:
        assert candidate.metadata["strict_closed_compact_pitch_class_layout"] is True
        assert max(candidate.notes) - min(candidate.notes) <= 12
        notes = candidate.metadata["content_recipe"]["validity_notes"]
        assert "three_note_functional_source_type_root_third_ninth" in notes
        assert "three_note_no_seventh_chord_not_partial_fallback" in notes


def test_v2_1_40_docs_record_triad_aware_three_note_contract() -> None:
    required = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "DEVELOPMENT_HARNESS_V2.md",
        ROOT / "docs" / "VOICING_MODULE_CORE_LOGIC_V2.md",
        ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md",
        ROOT / "docs" / "SYSTEM_CONTRACTS_V2.md",
        ROOT / "docs" / "FUTURE_IDEAS_BACKLOG_V2.md",
    ]
    for path in required:
        text = path.read_text(encoding="utf-8")
        assert "v2_1_40" in text, path
        assert "triad-aware" in text.lower() and "3-note" in text.lower(), path
        assert "root-third-fifth" in text, path
        assert "no partial fallback" in text, path
