from __future__ import annotations

# harness token: test_v2_6_26_engine_voicing_realization_surface_final_cleanup

import ast
from collections import Counter
import json
from pathlib import Path

from jammate_engine.realization.harmonic_realizer import (
    HARMONIC_REALIZER_SURFACE_FINAL_CLEANUP_VERSION,
    HARMONIC_REALIZER_SURFACE_FORBIDDEN_RESPONSIBILITIES,
    HARMONIC_REALIZER_SURFACE_OWNED_RESPONSIBILITIES,
    harmonic_realizer_surface_final_cleanup_profile,
)
from jammate_engine.realization.realizer_note_audit import realizer_note_audit_cleanup_profile
from jammate_engine.realization.voicing_policy_context_adapter import harmonic_realizer_policy_context_adapter_profile
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = Path(__file__).resolve().parents[1]
HARMONIC_REALIZER = ROOT / "src" / "jammate_engine" / "realization" / "harmonic_realizer.py"
NOTE_AUDIT = ROOT / "src" / "jammate_engine" / "realization" / "realizer_note_audit.py"
REQUEST_ORCHESTRATION = ROOT / "src" / "jammate_engine" / "realization" / "realizer_voicing_request_orchestration.py"
DOC = ROOT / "docs" / "ENGINE_VOICING_REALIZATION_SURFACE_FINAL_CLEANUP_V2_6_26.md"
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


def test_v2_6_26_harmonic_realizer_surface_contract_is_explicit() -> None:
    assert HARMONIC_REALIZER_SURFACE_FINAL_CLEANUP_VERSION == "v2_6_26"
    assert "active_piano_pattern_event_iteration" in HARMONIC_REALIZER_SURFACE_OWNED_RESPONSIBILITIES
    assert "voicing_plan_request_delegation" in HARMONIC_REALIZER_SURFACE_OWNED_RESPONSIBILITIES
    assert "does_not_construct_degree_sources" in HARMONIC_REALIZER_SURFACE_FORBIDDEN_RESPONSIBILITIES
    assert "does_not_build_voicing_requests_directly" in HARMONIC_REALIZER_SURFACE_FORBIDDEN_RESPONSIBILITIES
    assert "does_not_build_note_audit_payloads_directly" in HARMONIC_REALIZER_SURFACE_FORBIDDEN_RESPONSIBILITIES

    profile = harmonic_realizer_surface_final_cleanup_profile()
    debug = profile.to_debug_dict()
    assert debug["harmonic_realizer_surface_final_cleanup_version"] == "v2_6_26"
    assert debug["implementation_owner"] == "jammate_engine.realization.harmonic_realizer"
    assert debug["request_orchestration_owner"] == "jammate_engine.realization.realizer_voicing_request_orchestration"
    assert debug["note_audit_owner"] == "jammate_engine.realization.realizer_note_audit"
    assert debug["realization_surface_only"] is True
    assert debug["delegates_request_cache_and_audit"] is True
    assert debug["no_source_color_projection_or_selector_ownership"] is True


def test_v2_6_26_harmonic_realizer_is_thin_surface_without_lower_level_voicing_ownership() -> None:
    symbols = _defined_symbols(HARMONIC_REALIZER)
    assert "HarmonicRealizer" in symbols
    assert "HarmonicRealizerSurfaceFinalCleanupProfile" in symbols

    forbidden_symbols = {
        "VoicingRequest",
        "VoicingResolver",
        "policy_with_event_voicing_context",
        "region_voicing_cache_key",
        "event_requests_fresh_voicing",
        "reuse_region_voicing",
        "piano_audit_event_debug_payload_construction",
        "note_event_debug",
        "gesture_debug",
    }
    assert forbidden_symbols.isdisjoint(symbols)

    imports = _imported_modules(HARMONIC_REALIZER)
    forbidden_imports = {
        "jammate_engine.core.voicing",
        "jammate_engine.core.voicing.sources.content_planner",
        "jammate_engine.core.voicing.sources.content_source_inventory",
        "jammate_engine.core.voicing.sources.color_permission",
        "jammate_engine.core.voicing.sources.source_balance",
        "jammate_engine.core.voicing.disposition.projection",
        "jammate_engine.core.voicing.selection.selector",
        "jammate_engine.core.voicing.selection.scorer",
        "jammate_engine.realization.voicing_policy_context_adapter",
        "jammate_engine.core.midi",
    }
    assert not (imports & forbidden_imports)

    text = HARMONIC_REALIZER.read_text(encoding="utf-8")
    assert "RealizerVoicingRequestOrchestrator" in text
    assert "piano_audit_event(event, expr, voicing, realized)" in text
    for forbidden_token in (
        "VoicingRequest(",
        "VoicingResolver(",
        "policy_with_event_voicing_context(",
        "region_voicing_cache =",
        "generate_candidates(",
        "project_basic_spread_candidates(",
        "select_voicing(",
        "NoteEvent(",
        "write_midi(",
    ):
        assert forbidden_token not in text


def test_v2_6_26_note_audit_and_policy_context_profiles_point_to_request_orchestration_owner() -> None:
    policy_context_debug = harmonic_realizer_policy_context_adapter_profile().to_debug_dict()
    assert policy_context_debug["consumed_by"] == "jammate_engine.realization.realizer_voicing_request_orchestration"

    debug = realizer_note_audit_cleanup_profile().to_debug_dict()
    assert debug["voicing_request_orchestration_owner"] == "jammate_engine.realization.realizer_voicing_request_orchestration"
    assert "realizer_note_audit_cleanup_version" in debug

    note_audit_text = NOTE_AUDIT.read_text(encoding="utf-8")
    assert "jammate_engine.realization.realizer_voicing_request_orchestration" in note_audit_text
    assert "jammate_engine.realization.harmonic_realizer" not in note_audit_text


def test_v2_6_26_doc_records_realization_surface_final_cleanup() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_26_engine_voicing_realization_surface_final_cleanup",
        "harmonic_realizer.py",
        "RealizerVoicingRequestOrchestrator",
        "realizer_note_audit.py",
        "GestureRealizer",
        "does not construct degree sources",
        "does not build VoicingRequest directly",
        "does not build piano audit payloads directly",
        "5-note:6-note ~= 6:4",
        "maj7#11 remains off by default",
        "v2_6_27_engine_ballad_spread_listening_calibration_pass",
    ):
        assert token in text


def test_v2_6_26_misty_audit_surface_and_guardrails_remain_stable(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_26.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    events = result.debug.get("piano_musical_audit_events", [])
    assert events
    assert all(event.get("harmonic_realizer_surface_final_cleanup_version") == "v2_6_26" for event in events)

    voicings = _voicing_events(result.debug)
    densities = Counter(int(voicing.get("density", 0)) for voicing in voicings)
    groupings = Counter(str(voicing.get("functional_grouping")) for voicing in voicings)

    assert densities[4] == 0
    assert "1+3" not in groupings
    assert "2+2" not in groupings
    five = densities[5]
    six = densities[6]
    ratio = five / float(five + six)
    assert 0.58 <= ratio <= 0.63
    assert densities[7] <= 3

    maj7_sharp11 = [
        voicing
        for voicing in voicings
        if "maj7" in str(voicing.get("chord_symbol"))
        and any(str(degree) == "#11" for degree in voicing.get("degrees", []))
    ]
    assert maj7_sharp11 == []

    reused = [voicing for voicing in voicings if voicing.get("metadata", {}).get("region_voicing_reused")]
    assert reused
    assert all(
        voicing.get("metadata", {}).get("realizer_voicing_request_orchestration_version") == "v2_6_25"
        for voicing in reused
    )
