from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from examples.scripts.generate_4note_source_weight_listening_verification_demos import (
    DEMO_SPECS,
    FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE,
)


def test_v2_1_37_contract_versions_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_OVERRIDE_CONTRACT_VERSION == "v2_1_43"


def test_v2_1_37_listening_demo_specs_cover_requested_styles_and_scope() -> None:
    ids = {spec["id"] for spec in DEMO_SPECS}
    styles = {spec["style"] for spec in DEMO_SPECS}
    assert ids == {
        "medium_swing_all_the_things_you_are",
        "medium_swing_color_rich_251_stress",
        "bossa_color_rich_progression",
        "ballad_color_rich_warm_voicing",
    }
    assert styles == {"medium_swing", "bossa_nova", "jazz_ballad"}
    assert FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE["preferred_density"] == 4
    assert FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE["min_density"] == 4
    assert FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE["max_density"] == 4
    assert FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE["preferred_disposition"] == "closed"
    assert FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE["allowed_dispositions"] == ["closed"]
    assert "5-note" in FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE["metadata"]["excluded_scope"]


def test_v2_1_37_color_rich_fixtures_cover_explicit_source_weight_targets() -> None:
    fixtures = [
        ROOT / "examples" / "leadsheets" / "color_rich_251_stress.json",
        ROOT / "examples" / "leadsheets" / "color_rich_bossa_progression.json",
        ROOT / "examples" / "leadsheets" / "color_rich_ballad_voicing_progression.json",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in fixtures)
    for token in ("Cmaj9", "Cmaj7#11", "Dm11", "G13", "G7b9", "G7alt", "Bm11b5", "E7b9b13", "C6/9"):
        assert token in text


def test_v2_1_37_runtime_trace_exposes_4note_source_weight_details(tmp_path: Path) -> None:
    score = json.loads((ROOT / "examples" / "leadsheets" / "color_rich_251_stress.json").read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": 132,
            "choruses": 1,
            "seed": 934,
            "output_path": str(tmp_path / "v2_1_37_trace_probe.mid"),
            "ensemble": {"bass_present": True},
            "voicing_override": dict(FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE),
        }
    )
    audit = build_piano_musical_audit(result.debug)
    rows = audit.event_rows
    assert rows
    assert {row["density"] for row in rows} == {4}
    assert {row["disposition"] for row in rows} == {"closed"}
    assert all(row["four_note_source_balance_key"] for row in rows)
    assert all(row["four_note_source_balance_gate_mode"] for row in rows)
    assert any(row["chart_color_fidelity_score"] and row["chart_color_fidelity_score"] > 0 for row in rows)
    assert audit.summary["four_note_source_balance_keys"]
    assert audit.summary["four_note_source_balance_gate_modes"]


def test_v2_1_37_docs_are_synced_for_listening_verification_pass() -> None:
    required_docs = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "VOICING_MODULE_CORE_LOGIC_V2.md",
        ROOT / "docs" / "VOICING_SYSTEM_V2_DESIGN.md",
        ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md",
        ROOT / "docs" / "STYLE_RULE_BASELINE_V2.md",
        ROOT / "docs" / "VOICING_TUNING_WORKFLOW_V2.md",
        ROOT / "docs" / "DEVELOPMENT_HARNESS_V2.md",
        ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md",
        ROOT / "docs" / "API_CONTRACT_V2.md",
        ROOT / "docs" / "SYSTEM_CONTRACTS_V2.md",
        ROOT / "docs" / "ARCHITECTURE_V2.md",
    ]
    for path in required_docs:
        text = path.read_text(encoding="utf-8")
        assert "v2_1_37" in text, path
        assert "4-Note Source Weight Listening Verification Pass" in text, path
        assert "generate_4note_source_weight_listening_verification_demos.py" in text, path
        assert "four_note_source_balance_key" in text, path
        assert "v2_1_37" in text, path
