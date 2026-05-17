from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.generation.bass_foundation import build_bass_foundation_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.medium_swing.bass_foundation_patterns import get_bass_foundation_policy


def test_medium_swing_bass_foundation_tuning_policy_is_conservative() -> None:
    policy = get_bass_foundation_policy()

    assert policy["root_echo_probability"] <= 0.14
    assert policy["root_echo_compact_probability_multiplier"] <= 0.25
    assert policy["classic_fill_two_bar_tonic_probability"] <= 0.18
    assert policy["classic_fill_min_gap_regions"] >= 14
    # v2_0_22 preserves the old engine connector family reference
    # distribution: scaleNearNextR : approachToNextR : dominantConnection = 40 : 40 : 10.
    assert policy["connector_family_weights"]["scale_near_nextR"] == 40.0
    assert policy["connector_family_weights"]["approach_nextR"] == 40.0
    assert policy["connector_family_weights"]["dominant_connection"] == 10.0
    # v2_0_22 retires the temporary V2 register-gravity caps so the old
    # engine lane table + degree multipliers are the source of truth again.
    assert "high_zone_upper_lane_cap" not in policy
    assert "very_high_zone_upper_lane_cap" not in policy


def test_attya_bass_foundation_audit_after_musicality_tuning(tmp_path: Path) -> None:
    score = json.loads(Path("examples/leadsheets/all_the_things_you_are.json").read_text())
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "choruses": 1,
            "tempo": int(score.get("tempo", 132)),
            "seed": 1,
            "output_path": str(tmp_path / "attya_tuned.mid"),
        }
    )
    audit = build_bass_foundation_audit(result.debug)
    summary = audit.summary

    assert summary["span_violations"] == 0
    assert summary["root_echo_bad_same"] == 0
    assert summary["root_echo_bad_timing"] == 0
    assert summary["root_echo_count"] <= 34
    assert summary["classic_fill_count"] <= 2
    assert summary["span_violations"] == 0

    high_upward_segments = [
        row
        for row in audit.segment_rows
        if row.get("zone") in {"high", "very_high"} and row.get("lane") == "upper"
    ]
    assert len(high_upward_segments) <= 5
