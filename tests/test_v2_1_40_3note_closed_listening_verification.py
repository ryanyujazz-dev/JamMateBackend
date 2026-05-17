from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = Path(__file__).resolve().parents[1]


def test_v2_1_40_versions_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_OVERRIDE_CONTRACT_VERSION == "v2_1_43"


def test_three_note_closed_listening_assets_exist() -> None:
    assert (ROOT / "examples" / "leadsheets" / "three_note_closed_source_stress.json").exists()
    assert (ROOT / "examples" / "scripts" / "generate_3note_closed_listening_verification_demos.py").exists()


def test_three_note_closed_listening_trace_exposes_functional_sources(tmp_path: Path) -> None:
    score = json.loads((ROOT / "examples" / "leadsheets" / "three_note_closed_source_stress.json").read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": 132,
            "choruses": 1,
            "seed": 2140,
            "output_path": str(tmp_path / "three_note_closed.mid"),
            "ensemble": {"bass_present": True},
            "voicing_override": {
                "enabled": True,
                "preset": "shell_plus_specified_color",
                "allowed_content": ["shell_plus_color", "shell_plus_5"],
                "preferred_density": 3,
                "min_density": 3,
                "max_density": 3,
                "preferred_disposition": "closed",
                "allowed_dispositions": ["closed"],
                "metadata": {
                    "strict_closed_compact_pitch_class_layout": True,
                    "strict_closed_max_span": 12,
                    "closed_voicing_lowest_note_floor": 53,
                    "closed_3note_per_source_minimum_motion": True,
                    "closed_3note_closed_legality_then_nearest_motion": True,
                },
            },
        }
    )
    audit = build_piano_musical_audit(result.debug)
    summary = audit.summary
    assert summary["densities"] == {"3": summary["events"]}
    assert summary["dispositions"] == {"closed": summary["events"]}
    assert summary["closed_3note_minimum_motion_events"] == summary["events"]
    assert summary["closed_4note_minimum_motion_events"] == 0
    assert summary["failed_register_guard_count"] == 0
    assert summary["missing_note_events"] == 0
    assert summary["min_closed_voicing_lowest_note"] >= 53
    assert summary["max_closed_voicing_span"] <= 12
    source_types = set(summary["three_note_source_types"])
    assert "root_third_fifth" in source_types
    assert "root_third_ninth" in source_types
    assert "root_third_sixth" in source_types
    assert "root_fourth_fifth" in source_types
    assert "third_seventh_fifth" in source_types
    assert "third_seventh_ninth" in source_types
    assert "third_seventh_altered_color" in source_types


def test_v2_1_40_docs_record_three_note_listening_contract() -> None:
    required = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "DEVELOPMENT_HARNESS_V2.md",
        ROOT / "docs" / "VOICING_TUNING_WORKFLOW_V2.md",
        ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md",
        ROOT / "docs" / "FUTURE_IDEAS_BACKLOG_V2.md",
    ]
    for path in required:
        text = path.read_text(encoding="utf-8")
        assert "v2_1_43" in text, path
        assert "3-note closed" in text, path
        assert "root-third-fifth" in text, path
        assert "per-source nearest" in text, path
