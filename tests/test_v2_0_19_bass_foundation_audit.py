from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.generation.bass_foundation import build_bass_foundation_audit, format_bass_foundation_audit_report
from jammate_engine.runtime.generate import generate_accompaniment


def test_bass_foundation_audit_report_contains_region_decision_trace(tmp_path: Path) -> None:
    score = json.loads(Path("examples/leadsheets/all_the_things_you_are.json").read_text())
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "choruses": 1,
            "tempo": int(score.get("tempo", 132)),
            "seed": 1,
            "output_path": str(tmp_path / "audit.mid"),
        }
    )
    audit = build_bass_foundation_audit(result.debug)
    report = format_bass_foundation_audit_report(result.debug, max_segments=8)

    assert audit.summary["segments"] > 0
    assert audit.summary["root_echo_bad_same"] == 0
    assert audit.summary["root_echo_bad_timing"] == 0
    assert audit.summary["span_violations"] == 0
    assert "BassFoundation Musicality Audit" in report
    assert "Region Decision Trace" in report
    assert "Root echo same-root violations" in report
    assert "Performed Timing" in report
    assert result.debug["bass_foundation_audit"]["segments"] == audit.summary["segments"]
