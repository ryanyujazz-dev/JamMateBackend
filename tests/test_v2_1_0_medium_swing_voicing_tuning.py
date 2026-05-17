from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.registry import get_style

ROOT = Path(__file__).resolve().parents[1]


def _tuning_result(tmp_path):
    leadsheet = json.loads((ROOT / "examples" / "leadsheets" / "minimal_ii_v_i.json").read_text(encoding="utf-8"))
    return generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "medium_swing_voicing_tuning",
            "tempo": 132,
            "choruses": 1,
            "seed": 210,
            "output_path": str(tmp_path / "v2_1_0_voicing_tuning.mid"),
            "ensemble": {"bass_present": True},
        }
    )


def test_medium_swing_voicing_tuning_profile_is_registered_and_not_normal_default() -> None:
    normal = get_style("medium_swing")
    tuning = get_style("medium_swing_voicing_tuning")

    assert normal.name == "medium_swing"
    assert tuning.name == "medium_swing_voicing_tuning"
    assert tuning.anticipation_policy.enabled is False
    assert tuning.bass_foundation_source is None
    assert tuning.voicing_policy.metadata["tuning_target"] == "2_note_shell"
    assert tuning.voicing_policy.preferred_density == 2
    assert tuning.voicing_policy.min_density == 2
    assert tuning.voicing_policy.max_density == 2
    assert normal.voicing_policy.preferred_density == 4


def test_voicing_tuning_emits_only_region_start_piano_events_with_shell_density_2(tmp_path) -> None:
    result = _tuning_result(tmp_path)
    audit = build_piano_musical_audit(result.debug)

    assert audit.summary["top_patterns"] == [("medium_swing_voicing_tuning_region_start_anchor", 4)]
    assert audit.summary["content_families"] == {"shell": 4}
    assert audit.summary["densities"] == {"2": 4}
    assert audit.summary["rootless_events"] == 4
    assert audit.summary["root_included_events"] == 0
    assert audit.summary["note_events_by_track"] == {"piano": 8}
    assert result.debug["suppressed_pattern_events"] == 0

    for row in audit.event_rows:
        assert row["local_beat"] == 0.0
        assert row["pattern_id"] == "medium_swing_voicing_tuning_region_start_anchor"
        assert row["expression_profile"] == "sustain"
        assert row["content_family"] == "shell"
        assert row["density"] == 2
        assert len(row["degrees"]) == 2
        assert row["root_included"] is False
