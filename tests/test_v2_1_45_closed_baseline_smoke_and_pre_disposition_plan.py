from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG

ROOT = Path(__file__).resolve().parents[1]


def test_v2_2_0_version_and_pre_disposition_plan_exist() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    doc = ROOT / "docs" / "CLOSED_3_4_NOTE_BASELINE_AND_PRE_DISPOSITION_PLAN_V2.md"
    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    for token in [
        "Current plan version: `v2_2_5`",
        "closed legality filter",
        "per-source nearest-motion realization",
        "F3 / MIDI 53",
        "1351 / 3513 / 5135",
        "v2_2_1 — Disposition Projection Entry Pass",
    ]:
        assert token in text


def test_v2_2_0_combined_smoke_script_is_documented() -> None:
    script = ROOT / "examples" / "scripts" / "generate_closed_34note_baseline_smoke_listening.py"
    assert script.exists()
    script_text = script.read_text(encoding="utf-8")
    for token in [
        "generate_3note_closed_listening_verification_demos.py",
        "generate_4note_source_weight_listening_verification_demos.py",
        "generate_4note_triad_closed_listening_verification_demos.py",
        "closed_34note_baseline_smoke_summary",
    ]:
        assert token in script_text
    docs = (ROOT / "agent.md").read_text(encoding="utf-8") + (ROOT / "docs" / "DEVELOPMENT_HARNESS_V2.md").read_text(encoding="utf-8")
    assert "generate_closed_34note_baseline_smoke_listening.py" in docs
    assert "CLOSED_3_4_NOTE_BASELINE_AND_PRE_DISPOSITION_PLAN_V2.md" in docs


def test_v2_2_0_smoke_summary_passes_when_generated() -> None:
    summary = ROOT / "demos" / "v2_2_0_closed_34note_baseline_smoke_summary.json"
    if not summary.exists():
        return
    data = json.loads(summary.read_text(encoding="utf-8"))
    assert data["contract_version"] == "v2_2_0"
    assert data["acceptance"]["passed"] is True
    assert data["acceptance"]["failed_checks"] == []
    section_ids = {section["section_id"] for section in data["sections"]}
    assert section_ids == {"3note_closed", "4note_color_source", "4note_triad_source"}
    assert data["acceptance"]["check_count"] >= 70
