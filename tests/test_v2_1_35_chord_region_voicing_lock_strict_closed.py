from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.scripts.generate_4note_source_weight_listening_verification_demos import FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE
from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION, build_voicing_override_policy
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment


def _multi_hit_one_region_score() -> dict:
    return {
        "title": "Region Voicing Lock Probe",
        "sections": [
            {
                "id": "A",
                "bars": [
                    {"chords": [{"symbol": "Cmaj9", "beats": 4}]},
                ],
            }
        ],
        "form": ["A"],
    }


def test_v2_1_37_contract_versions_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_OVERRIDE_CONTRACT_VERSION == "v2_1_43"


def test_v2_1_37_listening_override_is_strict_closed_span_capped() -> None:
    assert FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE["preferred_density"] == 4
    assert FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE["min_density"] == 4
    assert FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE["max_density"] == 4
    assert FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE["preferred_disposition"] == "closed"
    assert FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE["allowed_dispositions"] == ["closed"]
    assert FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE["max_voicing_span"] == 16
    assert FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE["allowed_content"] == [
        "seventh_chord_basic",
        "rooted_color",
        "rootless_A",
        "rootless_B",
    ]
    assert FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE["metadata"]["closed_voicing_lowest_note_floor"] == 53
    assert FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE["metadata"]["strict_closed_compact_pitch_class_layout"] is True
    effective = build_voicing_override_policy({}, dict(FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE), style_name="jazz_ballad")
    assert effective.metadata["closed_voicing_lowest_note_floor"] == 53
    assert effective.metadata["strict_closed_compact_pitch_class_layout"] is True
    assert "drop2/open/spread" in FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE["metadata"]["excluded_scope"]


def test_v2_1_37_same_chord_region_reuses_selected_voicing_for_multiple_hits(tmp_path: Path) -> None:
    result = generate_accompaniment(
        {
            "leadsheet": _multi_hit_one_region_score(),
            "style": "bossa_nova",
            "tempo": 128,
            "choruses": 1,
            "seed": 351,
            "output_path": str(tmp_path / "region_voicing_lock_probe.mid"),
            "ensemble": {"bass_present": True},
            "voicing_override": {
                **dict(FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE),
                "disable_anticipation": True,
            },
        }
    )
    audit = build_piano_musical_audit(result.debug)
    rows = audit.event_rows
    assert len(rows) >= 2
    assert {row["region_id"] for row in rows} == {"c0_b0_ch0"}
    first_notes = rows[0]["midi_notes"]
    first_degrees = rows[0]["degrees"]
    assert all(row["midi_notes"] == first_notes for row in rows)
    assert all(row["degrees"] == first_degrees for row in rows)
    assert any(row["region_voicing_reused"] for row in rows[1:])




def test_v2_1_37_strict_closed_compacts_rooted_add9_instead_of_source_order_spread(tmp_path: Path) -> None:
    score_path = ROOT / "examples" / "leadsheets" / "color_rich_ballad_voicing_progression.json"
    score = json.loads(score_path.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "jazz_ballad",
            "tempo": 76,
            "choruses": 1,
            "seed": 361,
            "output_path": str(tmp_path / "strict_closed_compact_cmaj9.mid"),
            "ensemble": {"bass_present": True},
            "voicing_override": dict(FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE),
        }
    )
    audit = build_piano_musical_audit(result.debug)
    rows = audit.event_rows
    assert rows
    first = rows[0]
    assert first["chord_symbol"] == "Cmaj9"
    assert first["density"] == 4
    assert first["disposition"] == "closed"
    assert min(first["midi_notes"]) >= 57
    assert max(first["midi_notes"]) - min(first["midi_notes"]) <= 8
    assert first["midi_notes"] != [60, 64, 67, 74]

def test_v2_1_37_ballad_strict_closed_listening_has_no_open_span_side_effects(tmp_path: Path) -> None:
    score_path = ROOT / "examples" / "leadsheets" / "color_rich_ballad_voicing_progression.json"
    score = json.loads(score_path.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "jazz_ballad",
            "tempo": 76,
            "choruses": 1,
            "seed": 935,
            "output_path": str(tmp_path / "ballad_strict_closed_probe.mid"),
            "ensemble": {"bass_present": True},
            "voicing_override": dict(FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE),
        }
    )
    audit = build_piano_musical_audit(result.debug)
    rows = audit.event_rows
    assert rows
    assert {row["density"] for row in rows} == {4}
    assert {row["disposition"] for row in rows} == {"closed"}
    lows = [min(row["midi_notes"]) for row in rows]
    spans = [max(row["midi_notes"]) - min(row["midi_notes"]) for row in rows]
    assert min(lows) >= 53
    assert max(spans) <= 12
    assert audit.summary["failed_register_guard_count"] == 0
