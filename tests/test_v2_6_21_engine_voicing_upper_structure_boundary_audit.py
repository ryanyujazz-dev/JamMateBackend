from __future__ import annotations

# harness token: test_v2_6_21_engine_voicing_upper_structure_boundary_audit

import ast
from collections import Counter
import json
from pathlib import Path

from jammate_engine.core.voicing.policy import ColorPolicyMode, VoicingPolicy
from jammate_engine.core.voicing.sources.upper_structure import (
    UPPER_STRUCTURE_BOUNDARY_AUDIT_VERSION,
    UPPER_STRUCTURE_FORBIDDEN_RESPONSIBILITIES,
    UPPER_STRUCTURE_OWNED_RESPONSIBILITIES,
    UPPER_STRUCTURE_SOURCE_VERSION,
    plan_upper_structure_sources,
    upper_structure_boundary_profile,
)
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = Path(__file__).resolve().parents[1]
UPPER_STRUCTURE = ROOT / "src/jammate_engine/core/voicing/sources/upper_structure.py"
DOC = ROOT / "docs" / "ENGINE_VOICING_UPPER_STRUCTURE_BOUNDARY_AUDIT_V2_6_21.md"
MISTY = ROOT / "examples" / "leadsheets" / "misty.json"


def _imported_modules(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    return imports


def _defined_symbols(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in module.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))}


def _policy(*, expansion: bool = True, altered: bool = False) -> VoicingPolicy:
    return VoicingPolicy(
        harmonic_expansion_enabled=expansion,
        color_policy_mode=(
            ColorPolicyMode.ALTERED_DOMINANT
            if altered
            else (ColorPolicyMode.STYLE_SAFE_EXTENSIONS if expansion else ColorPolicyMode.CHORD_SYMBOL_ONLY)
        ),
        metadata={
            "spread_upper_structure_enabled": True,
            "harmonic_expansion_enabled": expansion,
            "color_policy_mode": "altered_dominant" if altered else ("style_safe_extensions" if expansion else "chord_symbol_only"),
            "previous_chord_symbol": "Dm7",
            "next_chord_symbol": "Cmaj7",
            "altered_dominant_policy": {
                "enabled": altered,
                "intensity": "high" if altered else "off",
                "scope": "functional_dominants",
            },
        },
    )


def _voicing_events(debug: dict) -> list[dict]:
    return [event.get("voicing") or {} for event in debug.get("piano_musical_audit_events", [])]


def test_v2_6_21_upper_structure_boundary_contract_is_explicit() -> None:
    assert UPPER_STRUCTURE_SOURCE_VERSION == "v2_2_88"
    assert UPPER_STRUCTURE_BOUNDARY_AUDIT_VERSION == "v2_6_21"
    assert "source_level_upper_structure_degree_recipes" in UPPER_STRUCTURE_OWNED_RESPONSIBILITIES
    assert "does_not_choose_register_or_octave_placement" in UPPER_STRUCTURE_FORBIDDEN_RESPONSIBILITIES

    symbols = _defined_symbols(UPPER_STRUCTURE)
    for expected in (
        "UpperStructureBoundaryProfile",
        "UpperStructureSource",
        "upper_structure_boundary_profile",
        "plan_upper_structure_sources",
    ):
        assert expected in symbols

    profile = upper_structure_boundary_profile()
    debug = profile.to_debug_dict()
    assert debug["upper_structure_boundary_audit_version"] == "v2_6_21"
    assert debug["source_only"] is True
    assert debug["reuses_existing_projection_layers"] is True
    assert debug["allowed_densities"] == [3, 4]


def test_v2_6_21_upper_structure_does_not_import_projection_register_or_selection_owners() -> None:
    imports = _imported_modules(UPPER_STRUCTURE)
    forbidden = {
        "jammate_engine.core.voicing.disposition.spread",
        "jammate_engine.core.voicing.disposition.projection",
        "jammate_engine.core.voicing.disposition.open",
        "jammate_engine.core.voicing.disposition.closed",
        "jammate_engine.core.voicing.selection.selector",
        "jammate_engine.core.voicing.selection.scorer",
        "jammate_engine.core.voicing.selection.voice_leading",
        "jammate_engine.core.midi",
        ".spread",
        ".projection",
        ".selector",
        ".scorer",
        ".voice_leading",
    }
    assert not (imports & forbidden)

    text = UPPER_STRUCTURE.read_text(encoding="utf-8")
    for forbidden_token in (
        "def project_",
        "def score_",
        "def select_",
        "class VoicingCandidate",
        "class SpreadProjectionCandidate",
        "write_midi(",
    ):
        assert forbidden_token not in text


def test_v2_6_21_upper_structure_sources_remain_source_only_and_density_limited() -> None:
    assert plan_upper_structure_sources("G7", density=2, policy=_policy()) == ()
    assert plan_upper_structure_sources("G7", density=5, policy=_policy()) == ()

    triads = plan_upper_structure_sources("G7", density=3, policy=_policy(expansion=True, altered=False))
    four_note = plan_upper_structure_sources("G7", density=4, policy=_policy(expansion=True, altered=False))
    assert triads and four_note
    assert all(source.density == 3 for source in triads)
    assert all(source.structure_kind == "upper_structure_triad" for source in triads)
    assert all(source.structure_kind == "upper_structure_4note" for source in four_note)

    for source in (*triads, *four_note):
        debug = source.to_debug_dict()
        assert debug["upper_structure_boundary_audit_version"] == "v2_6_21"
        assert debug["source_only_no_projection"] is True
        assert debug["reuse_existing_closed_inversion_drop_projection"] is True
        assert "does_not_score_or_select_candidates" in debug["forbidden_responsibilities"]
        assert any(str(note) == "source_only_reuses_existing_projection" for note in source.source_notes)


def test_v2_6_21_upper_structure_policy_gates_remain_unchanged() -> None:
    assert plan_upper_structure_sources("G7", density=3, policy=_policy(expansion=False, altered=False)) == ()

    safe = plan_upper_structure_sources("G7", density=3, policy=_policy(expansion=True, altered=False))
    assert safe
    assert all(source.chord_quality_gate == "dominant_safe" for source in safe)
    assert all("upper_structure_profile_kind_safe" in source.source_notes for source in safe)

    altered = plan_upper_structure_sources("G7", density=4, policy=_policy(expansion=True, altered=True))
    assert altered
    assert any("upper_structure_profile_kind_altered" in source.source_notes for source in altered)
    assert any("upper_structure_altered_dominant_authorized_true" in source.source_notes for source in altered)


def test_v2_6_21_doc_records_upper_structure_boundary_audit() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_21_engine_voicing_upper_structure_boundary_audit",
        "upper_structure.py",
        "source-only",
        "does not project closed/open/spread voicings",
        "does not choose register or octave placement",
        "does not score or select candidates",
        "UpperStructureBoundaryProfile",
        "5-note:6-note ~= 6:4",
        "maj7#11 remains off by default",
        "v2_6_22_engine_voicing_harmonic_realizer_policy_context_adapter_cleanup",
    ):
        assert token in text


def test_v2_6_21_misty_density_and_color_guardrails_remain_unchanged(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_21.mid"),
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
