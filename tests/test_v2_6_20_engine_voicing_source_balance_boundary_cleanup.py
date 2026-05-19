from __future__ import annotations

# harness token: test_v2_6_20_engine_voicing_source_balance_boundary_cleanup

import ast
from collections import Counter
import json
from pathlib import Path

from jammate_engine.core.voicing.policy import ContentFamily, Disposition, VoicingPolicy
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.selection.scorer import score_candidate
from jammate_engine.core.voicing.sources import source_balance
from jammate_engine.core.voicing.sources.source_balance import (
    SOURCE_BALANCE_BOUNDARY_CLEANUP_VERSION,
    SOURCE_BALANCE_CONTRACT_VERSION,
    source_balance_key,
    source_balance_profile,
    source_gate_mode,
)
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = Path(__file__).resolve().parents[1]
SOURCE_BALANCE = ROOT / "src/jammate_engine/core/voicing/sources/source_balance.py"
DOC = ROOT / "docs" / "ENGINE_VOICING_SOURCE_BALANCE_BOUNDARY_CLEANUP_V2_6_20.md"
MISTY = ROOT / "examples" / "leadsheets" / "misty.json"


def _defined_symbols(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in module.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))}


def _imported_modules(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    return imports


def _voicing_events(debug: dict) -> list[dict]:
    return [event.get("voicing") or {} for event in debug.get("piano_musical_audit_events", [])]


def test_v2_6_20_source_balance_boundary_contract_is_explicit() -> None:
    assert SOURCE_BALANCE_CONTRACT_VERSION == "v2_1_43"
    assert SOURCE_BALANCE_BOUNDARY_CLEANUP_VERSION == "v2_6_20"

    symbols = _defined_symbols(SOURCE_BALANCE)
    for expected in (
        "SourceBalanceProfile",
        "source_balance_key",
        "source_gate_mode",
        "source_balance_profile",
        "score_source_balance",
        "score_altered_dominant_intensity_balance",
        "altered_dominant_source_kind",
    ):
        assert expected in symbols

    text = SOURCE_BALANCE.read_text(encoding="utf-8")
    assert "SOURCE_BALANCE_OWNED_RESPONSIBILITIES" in text
    assert "SOURCE_BALANCE_FORBIDDEN_RESPONSIBILITIES" in text


def test_v2_6_20_source_balance_does_not_import_other_source_owners() -> None:
    imports = _imported_modules(SOURCE_BALANCE)
    forbidden = {
        "jammate_engine.core.voicing.sources.content_family_router",
        "jammate_engine.core.voicing.sources.content_source_inventory",
        "jammate_engine.core.voicing.sources.color_permission",
        "jammate_engine.core.voicing.sources.upper_structure",
        "..sources.content_family_router",
        "..sources.content_source_inventory",
        "..sources.color_permission",
        "..sources.upper_structure",
        ".content_family_router",
        ".content_source_inventory",
        ".color_permission",
        ".upper_structure",
    }
    assert not (imports & forbidden)

    text = SOURCE_BALANCE.read_text(encoding="utf-8")
    for forbidden_token in (
        "def content_degree_options",
        "def choose_content_families",
        "def build_voicing_color_permission_context",
        "def plan_upper_structure_sources",
        "ContentFamilyRouter",
    ):
        assert forbidden_token not in text


def test_v2_6_20_source_balance_profile_preserves_3note_gate_and_score() -> None:
    policy = VoicingPolicy(
        allowed_content=(ContentFamily.SHELL_PLUS_COLOR, ContentFamily.SHELL_PLUS_5),
        preferred_content=ContentFamily.SHELL_PLUS_COLOR,
        preferred_density=3,
        min_density=3,
        max_density=3,
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED,),
        source_family_weights_by_gate={
            "explicit_chart_color": {"third_seventh_ninth": 0.25},
            "chord_symbol_only": {"third_seventh_fifth": 0.11},
        },
        metadata={
            "strict_closed_compact_pitch_class_layout": True,
            "strict_closed_max_span": 12,
            "closed_voicing_lowest_note_floor": 53,
            "closed_3note_per_source_minimum_motion": True,
        },
    )
    selected = next(candidate for candidate in generate_candidates("Cmaj9", policy) if source_balance_key(candidate) == "third_seventh_ninth")
    profile = source_balance_profile(selected)

    assert profile.key == "third_seventh_ninth"
    assert profile.gate_mode == "explicit_chart_color"
    assert "third_seventh_ninth" in profile.weight_lookup_keys
    assert profile.to_debug_dict()["source_balance_boundary_cleanup_version"] == "v2_6_20"
    breakdown = score_candidate(selected, policy)
    assert breakdown.details["three_note_source_balance_key"] == "third_seventh_ninth"
    assert breakdown.details["three_note_source_balance_score"] == 0.25


def test_v2_6_20_source_balance_profile_preserves_4note_gate_and_score() -> None:
    policy = VoicingPolicy(
        allowed_content=(ContentFamily.MAJOR_TRIAD,),
        preferred_content=ContentFamily.MAJOR_TRIAD,
        preferred_density=4,
        min_density=4,
        max_density=4,
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED,),
        source_family_weights_by_gate={"chord_symbol_only": {"root_third_fifth_root": 0.17}},
        metadata={
            "strict_closed_compact_pitch_class_layout": True,
            "strict_closed_max_span": 12,
            "closed_voicing_lowest_note_floor": 53,
        },
    )
    selected = next(candidate for candidate in generate_candidates("C", policy) if source_balance_key(candidate) == "root_third_fifth_root")
    profile = source_balance_profile(selected)

    assert selected.density == 4
    assert source_gate_mode(selected) == "chord_symbol_only"
    assert profile.key == "root_third_fifth_root"
    assert profile.gate_mode == "chord_symbol_only"
    assert profile.weight_lookup_keys[:2] == ("root_third_fifth_root", "third_fifth_root")
    breakdown = score_candidate(selected, policy)
    assert breakdown.details["four_note_source_balance_key"] == "root_third_fifth_root"
    assert breakdown.details["source_balance_score"] == 0.17


def test_v2_6_20_doc_records_source_balance_boundary_cleanup() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_20_engine_voicing_source_balance_boundary_cleanup",
        "source_balance.py",
        "source-family scoring / bias only",
        "does not construct sources",
        "does not route ContentFamily",
        "does not decide color permission",
        "SourceBalanceProfile",
        "5-note:6-note ~= 6:4",
        "maj7#11 remains off by default",
        "v2_6_21_engine_voicing_upper_structure_boundary_audit",
    ):
        assert token in text


def test_v2_6_20_misty_density_and_color_guardrails_remain_unchanged(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_20.mid"),
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
