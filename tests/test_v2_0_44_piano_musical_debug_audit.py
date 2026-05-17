from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.generation.piano_audit import (
    PIANO_MUSICAL_AUDIT_CONTRACT_VERSION,
    build_piano_musical_audit,
    format_piano_musical_audit_report,
)
from jammate_engine.runtime.generate import generate_accompaniment


ROOT = Path(__file__).resolve().parents[1]


def _minimal_result(tmp_path):
    leadsheet = json.loads((ROOT / "examples" / "leadsheets" / "minimal_ii_v_i.json").read_text(encoding="utf-8"))
    return generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "medium_swing",
            "tempo": 132,
            "choruses": 1,
            "seed": 44,
            "output_path": str(tmp_path / "v2_0_44_piano_audit.mid"),
            "ensemble": {"bass_present": True},
        }
    )


def test_piano_musical_audit_is_attached_to_generation_debug(tmp_path) -> None:
    result = _minimal_result(tmp_path)
    debug = result.debug

    assert "piano_musical_audit_events" in debug
    assert "piano_musical_audit" in debug
    assert debug["piano_musical_audit"]["contract_version"] == PIANO_MUSICAL_AUDIT_CONTRACT_VERSION
    assert debug["piano_musical_audit"]["events"] == len(debug["piano_musical_audit_events"])
    assert debug["piano_musical_audit"]["events"] > 0
    assert "piano_musical_debug_audit" in debug["pipeline"]


def test_piano_audit_event_rows_expose_pattern_expression_voicing_and_realization(tmp_path) -> None:
    result = _minimal_result(tmp_path)
    audit = build_piano_musical_audit(result.debug)
    row = audit.event_rows[0]

    assert row["event_id"]
    assert row["pattern_id"] is not None
    assert row["gesture_type"] == "simultaneous_onset"
    assert row["expression_profile"] is not None
    assert row["duration_beats"] is not None
    assert row["velocity"] is not None
    assert row["content_family"] is not None
    assert row["density"] >= 2
    assert row["midi_notes"]
    assert row["degrees"]
    assert row["realized_note_count"] == len(row["realized_notes"])
    assert row["performed_starts"]


def test_piano_audit_report_is_markdown_and_observational(tmp_path) -> None:
    result = _minimal_result(tmp_path)
    report = format_piano_musical_audit_report(result.debug, max_events=2)

    assert "# Piano Musical Debug Audit" in report
    assert "## Piano Event Trace" in report
    assert "This report is observational" in report
    assert "Pattern" in report and "Voicing" in report and "Performed" in report


def test_piano_audit_trace_keeps_voicing_selector_debug(tmp_path) -> None:
    result = _minimal_result(tmp_path)
    raw = result.debug["piano_musical_audit_events"][0]
    voicing = raw["voicing"]

    assert "selector_decision" in voicing
    assert "register_guard" in voicing
    assert "voice_leading_profile" in voicing
    assert "projection_map" in voicing
    assert raw["realized_notes"][0]["voicing_event_id"] == voicing["event_id"]
