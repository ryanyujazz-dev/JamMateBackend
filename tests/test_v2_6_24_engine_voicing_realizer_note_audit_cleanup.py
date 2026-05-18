from __future__ import annotations

# harness token: test_v2_6_24_engine_voicing_realizer_note_audit_cleanup

import ast
from collections import Counter
import json
from pathlib import Path

from jammate_engine.realization.realizer_note_audit import (
    REALIZER_NOTE_AUDIT_CLEANUP_VERSION,
    REALIZER_NOTE_AUDIT_FORBIDDEN_RESPONSIBILITIES,
    REALIZER_NOTE_AUDIT_OWNED_RESPONSIBILITIES,
    realizer_note_audit_cleanup_profile,
)
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = Path(__file__).resolve().parents[1]
HARMONIC_REALIZER = ROOT / "src" / "jammate_engine" / "realization" / "harmonic_realizer.py"
NOTE_AUDIT = ROOT / "src" / "jammate_engine" / "realization" / "realizer_note_audit.py"
DOC = ROOT / "docs" / "ENGINE_VOICING_REALIZER_NOTE_AUDIT_CLEANUP_V2_6_24.md"
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


def test_v2_6_24_realizer_note_audit_contract_is_explicit() -> None:
    assert REALIZER_NOTE_AUDIT_CLEANUP_VERSION == "v2_6_24"
    assert "piano_audit_event_debug_payload_construction" in REALIZER_NOTE_AUDIT_OWNED_RESPONSIBILITIES
    assert "final_note_event_audit_sync" in REALIZER_NOTE_AUDIT_OWNED_RESPONSIBILITIES
    assert "does_not_build_voicing_requests" in REALIZER_NOTE_AUDIT_FORBIDDEN_RESPONSIBILITIES
    assert "does_not_score_or_select_voicing_candidates" in REALIZER_NOTE_AUDIT_FORBIDDEN_RESPONSIBILITIES

    profile = realizer_note_audit_cleanup_profile()
    debug = profile.to_debug_dict()
    assert debug["realizer_note_audit_cleanup_version"] == "v2_6_24"
    assert debug["implementation_owner"] == "jammate_engine.realization.realizer_note_audit"
    assert debug["note_event_boundary_only"] is True
    assert debug["voicing_request_orchestration_owner"] == "jammate_engine.realization.realizer_voicing_request_orchestration"


def test_v2_6_24_harmonic_realizer_no_longer_owns_note_audit_debug_helpers() -> None:
    realizer_symbols = _defined_symbols(HARMONIC_REALIZER)
    moved_helpers = {
        "_event_is_partial_reattack",
        "_release_reattacked_motion_voices",
        "_voice_identity_key",
        "_sync_piano_audit_realized_notes",
        "_piano_audit_event",
        "_gesture_debug",
        "_note_event_debug",
    }
    assert moved_helpers.isdisjoint(realizer_symbols)

    text = HARMONIC_REALIZER.read_text(encoding="utf-8")
    assert "from jammate_engine.realization.realizer_note_audit import" in text
    assert "piano_audit_event(event, expr, voicing, realized)" in text
    assert "sync_piano_audit_realized_notes(self.last_piano_audit_events, out)" in text
    assert "RealizerVoicingRequestOrchestrator" in text
    assert "VoicingRequest(" not in text
    assert "policy_with_event_voicing_context(" not in text


def test_v2_6_24_note_audit_module_owns_note_debug_without_voicing_source_or_selector_imports() -> None:
    symbols = _defined_symbols(NOTE_AUDIT)
    for expected in (
        "piano_audit_event",
        "sync_piano_audit_realized_notes",
        "note_event_debug",
        "gesture_debug",
        "event_is_partial_reattack",
        "release_reattacked_motion_voices",
        "RealizerNoteAuditCleanupProfile",
    ):
        assert expected in symbols

    imports = _imported_modules(NOTE_AUDIT)
    forbidden_imports = {
        "jammate_engine.core.voicing.sources.content_planner",
        "jammate_engine.core.voicing.sources.content_source_inventory",
        "jammate_engine.core.voicing.sources.color_permission",
        "jammate_engine.core.voicing.sources.source_balance",
        "jammate_engine.core.voicing.disposition.projection",
        "jammate_engine.core.voicing.selection.selector",
        "jammate_engine.core.voicing.selection.scorer",
        "jammate_engine.core.voicing.selection.candidate_generator",
        "jammate_engine.realization.voicing_policy_context_adapter",
        "jammate_engine.core.midi",
    }
    assert not (imports & forbidden_imports)

    text = NOTE_AUDIT.read_text(encoding="utf-8")
    for forbidden_token in (
        "VoicingResolver(",
        "VoicingRequest(",
        "generate_candidates(",
        "project_basic_spread_candidates(",
        "select_voicing(",
        "write_midi(",
    ):
        assert forbidden_token not in text


def test_v2_6_24_doc_records_realizer_note_audit_cleanup() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_24_engine_voicing_realizer_note_audit_cleanup",
        "harmonic_realizer.py",
        "realizer_note_audit.py",
        "piano_audit_event",
        "sync_piano_audit_realized_notes",
        "release_reattacked_motion_voices",
        "does not build VoicingRequest",
        "does not construct degree sources",
        "does not score or select candidates",
        "5-note:6-note ~= 6:4",
        "maj7#11 remains off by default",
        "v2_6_25_engine_voicing_request_orchestration_cache_boundary_audit",
    ):
        assert token in text


def test_v2_6_24_misty_audit_schema_and_density_guardrails_remain_stable(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_24.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    events = result.debug.get("piano_musical_audit_events", [])
    assert events
    assert all(event.get("realizer_note_audit_cleanup_version") == "v2_6_24" for event in events)
    assert all(event.get("realized_notes") for event in events)

    first_note = events[0]["realized_notes"][0]
    for key in ("note", "velocity", "start_beat", "duration_beats", "voice_role", "group_id", "projection_ref"):
        assert key in first_note

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
