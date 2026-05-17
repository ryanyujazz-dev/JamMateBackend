from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.registry import get_style

ROOT = Path(__file__).resolve().parents[1]


def _minimal_leadsheet() -> dict:
    return json.loads((ROOT / "examples" / "leadsheets" / "minimal_ii_v_i.json").read_text(encoding="utf-8"))


def test_global_voicing_override_forces_shell_density_2_without_replacing_style_patterns(tmp_path) -> None:
    normal = get_style("bossa_nova")
    result = generate_accompaniment(
        {
            "leadsheet": _minimal_leadsheet(),
            "style": "bossa_nova",
            "tempo": 132,
            "choruses": 1,
            "seed": 211,
            "output_path": str(tmp_path / "bossa_shell_override.mid"),
            "ensemble": {"bass_present": True},
            "voicing_override": {"enabled": True, "preset": "2_note_shell"},
        }
    )
    audit = build_piano_musical_audit(result.debug)

    assert normal.voicing_policy.preferred_density != 2
    assert result.debug["style"] == "bossa_nova"
    assert result.debug["voicing_override"]["enabled"] is True
    assert result.debug["voicing_override"]["isolation_enabled"] is False
    assert result.debug["effective_voicing_policy"]["preferred_density"] == 2
    assert audit.summary["content_families"] == {"shell": audit.summary["events"]}
    assert audit.summary["densities"] == {"2": audit.summary["events"]}
    assert all(row["pattern_id"] != "global_voicing_override_region_start_anchor" for row in audit.event_rows)


def test_global_voicing_isolation_anchor_mode_freezes_only_piano_and_preserves_other_tracks(tmp_path) -> None:
    result = generate_accompaniment(
        {
            "leadsheet": _minimal_leadsheet(),
            "style": "jazz_ballad",
            "tempo": 82,
            "choruses": 1,
            "seed": 212,
            "output_path": str(tmp_path / "ballad_shell_isolation.mid"),
            "ensemble": {"bass_present": True},
            "voicing_override": {
                "enabled": True,
                "preset": "2_note_shell",
                "pattern_mode": "region_start_anchor_only",
            },
        }
    )
    audit = build_piano_musical_audit(result.debug)

    assert result.debug["style"] == "jazz_ballad"
    assert result.debug["voicing_override"]["isolation_enabled"] is True
    assert result.debug["voicing_override"]["mute_bass"] is False
    assert result.debug["bass_foundation_plan"] is None
    assert result.debug["note_events_by_track"] == {"piano": 8, "bass": 4}
    assert audit.summary["top_patterns"] == [("global_voicing_override_region_start_anchor", 4)]
    assert audit.summary["content_families"] == {"shell": 4}
    assert audit.summary["densities"] == {"2": 4}
    assert audit.summary["rootless_events"] == 4
    assert all(row["local_beat"] == 0.0 for row in audit.event_rows)


def test_global_voicing_isolation_preserves_bossa_bass_and_drums(tmp_path) -> None:
    result = generate_accompaniment(
        {
            "leadsheet": _minimal_leadsheet(),
            "style": "bossa_nova",
            "tempo": 132,
            "choruses": 1,
            "seed": 213,
            "output_path": str(tmp_path / "bossa_shell_isolation.mid"),
            "ensemble": {"bass_present": True},
            "voicing_override": {
                "enabled": True,
                "preset": "2_note_shell",
                "pattern_mode": "region_start_anchor_only",
            },
        }
    )
    audit = build_piano_musical_audit(result.debug)

    assert result.debug["voicing_override"]["isolation_enabled"] is True
    assert result.debug["voicing_override"]["mute_bass"] is False
    assert result.debug["note_events_by_track"] == {"piano": 8, "bass": 8, "drums": 8}
    assert audit.summary["top_patterns"] == [("global_voicing_override_region_start_anchor", 4)]
    assert audit.summary["content_families"] == {"shell": 4}
    assert all(row["local_beat"] == 0.0 for row in audit.event_rows)
