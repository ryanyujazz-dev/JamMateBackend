from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION, build_voicing_override_policy

ROOT = Path(__file__).resolve().parents[1]


def _policy(*, expansion: bool = False):
    return build_voicing_override_policy(
        {
            "harmonic_expansion_enabled": expansion,
            "color_policy_mode": "style_safe_extensions" if expansion else "chord_symbol_only",
        },
        {
            "enabled": True,
            "allowed_content": ["seventh_chord_basic", "rooted_color", "rootless_A", "rootless_B"],
            "preferred_density": 4,
            "min_density": 4,
            "max_density": 4,
            "preferred_disposition": "closed",
            "allowed_dispositions": ["closed"],
            "register_low": 46,
            "register_high": 76,
            "top_voice_low": 55,
            "top_voice_high": 76,
            "comfort_register_low": 52,
            "comfort_register_high": 66,
            "max_voicing_span": 16,
            "metadata": {
                "strict_closed_compact_pitch_class_layout": True,
                "strict_closed_max_span": 12,
                "closed_voicing_lowest_note_floor": 53,
                "closed_4note_per_source_minimum_motion": True,
                "closed_4note_triad_doubled_rotation_contract": "1351/3513/5135; sus2 = 1251/2512/5125",
            },
        },
        style_name="medium_swing",
    )


def _source_types(symbol: str, *, expansion: bool = False) -> set[str]:
    out: set[str] = set()
    for recipe in plan_content_recipes(symbol, _policy(expansion=expansion)):
        for note in recipe.validity_notes:
            if note.startswith("triad_4note_functional_content_type_"):
                out.add(note.removeprefix("triad_4note_functional_content_type_"))
            if note.startswith("rooted_color_4note_functional_content_type_"):
                out.add(note.removeprefix("rooted_color_4note_functional_content_type_"))
            if note.startswith("basic_4note_functional_content_type_"):
                out.add(note.removeprefix("basic_4note_functional_content_type_"))
    return out


def test_v2_1_42_versions_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_OVERRIDE_CONTRACT_VERSION == "v2_1_43"


def test_plain_major_minor_triads_use_1351_3513_5135_doubled_closed_sources() -> None:
    expected = {"root_third_fifth_root", "third_fifth_root_third", "fifth_root_third_fifth"}
    assert _source_types("C") == expected
    assert _source_types("Cm") == expected


def test_sus_triads_use_matching_doubled_closed_source_logic() -> None:
    assert _source_types("Csus2") == {"root_second_fifth_root", "second_fifth_root_second", "fifth_root_second_fifth"}
    assert _source_types("Csus4") == {"root_fourth_fifth_root", "fourth_fifth_root_fourth", "fifth_root_fourth_fifth"}


def test_add_sixth_symbols_use_explicit_four_note_functional_sources() -> None:
    assert "root_third_fifth_ninth" in _source_types("Cadd9")
    assert "root_third_fifth_ninth" in _source_types("Cmadd9")
    assert "root_third_fifth_sixth" in _source_types("C6")
    assert "root_third_sixth_ninth" in _source_types("C6/9")


def test_triad_expansion_stays_low_order_for_four_note_sources() -> None:
    source_types = _source_types("C", expansion=True)
    assert "root_third_fifth_seventh" in source_types
    assert "root_third_fifth_sixth" in source_types
    assert "root_third_fifth_ninth" in source_types
    assert "third_seventh_ninth" not in source_types
    assert "third_seventh_eleventh" not in source_types
    assert "third_seventh_thirteenth" not in source_types


def test_four_note_triad_closed_candidates_remain_density_four_and_downshifted() -> None:
    policy = _policy()
    candidates = generate_candidates("Csus2", policy)
    assert candidates
    assert {candidate.density for candidate in candidates} == {4}
    assert {candidate.disposition.value for candidate in candidates} == {"closed"}
    assert min(min(candidate.notes) for candidate in candidates) >= 53
    assert max(max(candidate.notes) - min(candidate.notes) for candidate in candidates) <= 12
    assert any(candidate.degrees == ["R", "2", "5", "R"] for candidate in candidates)
    assert any(candidate.degrees == ["2", "5", "R", "2"] for candidate in candidates)
    assert any(candidate.degrees == ["5", "R", "2", "5"] for candidate in candidates)


def test_v2_1_42_docs_record_four_note_triad_closed_contract() -> None:
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
        assert "v2_1_43" in text, path
        assert "1351" in text and "3513" in text and "5135" in text, path
        assert "closed register downshift" in text.lower(), path
