from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION, build_voicing_override_policy

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "examples" / "scripts" / "generate_4note_triad_closed_listening_verification_demos.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("generate_4note_triad_closed_listening_verification_demos", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _policy():
    module = _load_script_module()
    return build_voicing_override_policy(
        {"harmonic_expansion_enabled": False, "color_policy_mode": "chord_symbol_only"},
        module.FOUR_NOTE_TRIAD_CLOSED_ISOLATION_OVERRIDE,
        style_name="medium_swing",
    )


def _source_types(symbol: str) -> set[str]:
    out: set[str] = set()
    for recipe in plan_content_recipes(symbol, _policy()):
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


def test_v2_1_42_fixture_covers_four_note_triad_closed_stress_symbols() -> None:
    fixture = json.loads((ROOT / "examples" / "leadsheets" / "four_note_triad_closed_source_stress.json").read_text(encoding="utf-8"))
    bars = set(fixture["bars"])
    for symbol in ["C", "Cm", "Csus2", "Csus4", "Cadd9", "Cmadd9", "C6", "C6/9"]:
        assert symbol in bars


def test_v2_1_42_override_forces_strict_four_note_closed_without_global_expansion() -> None:
    module = _load_script_module()
    override = module.FOUR_NOTE_TRIAD_CLOSED_ISOLATION_OVERRIDE
    assert override["harmonic_expansion_enabled"] is False
    assert override["color_policy_mode"] == "chord_symbol_only"
    assert override["preferred_density"] == 4
    assert override["min_density"] == 4
    assert override["max_density"] == 4
    assert override["allowed_dispositions"] == ["closed"]
    assert override["metadata"]["closed_voicing_lowest_note_floor"] == 53
    assert override["metadata"]["strict_closed_max_span"] == 12
    assert override["metadata"]["closed_4note_per_source_minimum_motion"] is True
    assert "1351" in override["metadata"]["closed_4note_triad_doubled_rotation_contract"]
    assert "1251" in override["metadata"]["closed_4note_triad_doubled_rotation_contract"]


def test_v2_1_42_plain_triad_and_sus_sources_remain_doubled_closed_rotations() -> None:
    assert _source_types("C") == {"root_third_fifth_root", "third_fifth_root_third", "fifth_root_third_fifth"}
    assert _source_types("Cm") == {"root_third_fifth_root", "third_fifth_root_third", "fifth_root_third_fifth"}
    assert _source_types("Csus2") == {"root_second_fifth_root", "second_fifth_root_second", "fifth_root_second_fifth"}
    assert _source_types("Csus4") == {"root_fourth_fifth_root", "fourth_fifth_root_fourth", "fifth_root_fourth_fifth"}


def test_v2_1_42_add_six_symbols_remain_explicit_functional_sources() -> None:
    assert "root_third_fifth_ninth" in _source_types("Cadd9")
    assert "root_third_fifth_ninth" in _source_types("Cmadd9")
    assert "root_third_fifth_sixth" in _source_types("C6")
    assert "root_third_sixth_ninth" in _source_types("C6/9")


def test_v2_1_42_candidates_are_density_four_closed_downshifted_and_not_partial() -> None:
    policy = _policy()
    for symbol in ["C", "Cm", "Csus2", "Csus4", "Cadd9", "C6", "C6/9"]:
        candidates = generate_candidates(symbol, policy)
        assert candidates, symbol
        assert {candidate.density for candidate in candidates} == {4}, symbol
        assert {candidate.disposition.value for candidate in candidates} == {"closed"}, symbol
        assert min(min(candidate.notes) for candidate in candidates) >= 53, symbol
        assert max(max(candidate.notes) - min(candidate.notes) for candidate in candidates) <= 12, symbol


def test_v2_1_42_piano_audit_records_triad_four_note_source_fields() -> None:
    summary_path = ROOT / "demos" / "v2_2_0_4note_triad_closed_listening_verification_summary.json"
    if not summary_path.exists():
        return
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["contract_version"] == "v2_2_0"
    for output in summary["outputs"]:
        audit = output["audit_summary"]
        assert audit["densities"] == {"4": audit["events"]}
        assert audit["dispositions"] == {"closed": audit["events"]}
        assert audit["failed_register_guard_count"] == 0
        assert audit["missing_note_events"] == 0
        assert audit["min_closed_voicing_lowest_note"] >= 53
        assert audit["max_closed_voicing_span"] <= 12
        assert audit["triad_4note_source_types"]
        assert audit["closed_4note_minimum_motion_events"] == audit["events"]


def test_v2_1_42_docs_record_four_note_triad_closed_listening_contract() -> None:
    required = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "DEVELOPMENT_HARNESS_V2.md",
        ROOT / "docs" / "VOICING_TUNING_WORKFLOW_V2.md",
        ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md",
        ROOT / "docs" / "SYSTEM_CONTRACTS_V2.md",
        ROOT / "docs" / "FUTURE_IDEAS_BACKLOG_V2.md",
    ]
    for path in required:
        text = path.read_text(encoding="utf-8")
        assert "v2_1_43" in text, path
        assert "4-note triad-aware closed listening" in text.lower(), path
        assert "1351" in text and "1251" in text and "1451" in text, path
        assert "open" in text and "drop2" in text and "5-note" in text, path
