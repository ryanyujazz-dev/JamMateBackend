from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.generation.bass_foundation import build_bass_foundation_audit, format_bass_foundation_audit_report
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = Path(__file__).resolve().parents[1]


def _generate_attya():
    score = json.loads((ROOT / "examples" / "leadsheets" / "all_the_things_you_are.json").read_text(encoding="utf-8"))
    return generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "choruses": 1,
            "tempo": int(score.get("tempo", 132)),
            "seed": 1,
        }
    )


def test_bass_foundation_inherits_previous_target_nextR_note() -> None:
    result = _generate_attya()
    segments = list(result.debug["bass_foundation_plan"]["segments"])
    inherited = [segment for segment in segments if segment.get("previous_target_nextR_note") is not None]
    assert inherited, "expected non-initial BassFoundation segments to carry previous target_nextR_note"
    assert all(segment.get("start_note") == segment.get("previous_target_nextR_note") for segment in inherited)
    assert all(segment.get("target_continuity_match") for segment in inherited)
    assert all(segment.get("start_note_source") == "inherited_previous_target_nextR_note" for segment in inherited)


def test_bass_foundation_audit_reports_seventh_bias_and_target_continuity() -> None:
    result = _generate_attya()
    audit = build_bass_foundation_audit(result.debug)
    summary = audit.summary
    assert summary["seventh_family_segments"] > 0
    assert summary["seventh_lower_lane_ratio"] >= 0.5
    assert summary["target_continuity_total"] > 0
    assert summary["target_continuity_mismatches"] == 0
    report = format_bass_foundation_audit_report(result.debug, max_segments=4)
    assert "Seventh Bias Audit" in report
    assert "Target Continuity Audit" in report
    assert "target_nextR_note" in (ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md").read_text(encoding="utf-8")


def test_generation_rules_summary_document_exists_and_tracks_bass_foundation_rules() -> None:
    text = (ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md").read_text(encoding="utf-8")
    for token in [
        "生成规则梳理总结",
        "Medium Swing / BassFoundation",
        "ThreeBeatSkeleton",
        "Five-zone register model",
        "Seventh Bias Audit",
        "Target Continuity Audit",
        "代码落位",
    ]:
        assert token in text
