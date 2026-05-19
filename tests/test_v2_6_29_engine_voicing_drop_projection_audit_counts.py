from __future__ import annotations

# harness token: test_v2_6_29_engine_voicing_drop_projection_audit_counts

from collections import Counter
from pathlib import Path
import json

from jammate_engine.generation.piano_audit import PIANO_DROP_PROJECTION_AUDIT_VERSION, build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_DROP_PROJECTION_AUDIT_COUNTS_V2_6_29.md"
MISTY = ROOT / "examples" / "leadsheets" / "misty.json"


def _raw_piano_event(
    *,
    event_id: str,
    density: int,
    grouping: str,
    recipe_id: str,
    disposition: str = "spread",
    upper_method: str | None = None,
    upper_metadata: dict | None = None,
    main_metadata: dict | None = None,
) -> dict:
    metadata = dict(main_metadata or {})
    if upper_method is not None:
        metadata["upper_projection_method"] = upper_method
    if upper_metadata is not None:
        metadata["upper_projection_metadata"] = dict(upper_metadata)
    return {
        "event_id": event_id,
        "pattern_event": {
            "event_id": event_id,
            "track": "piano",
            "region_id": "r1",
            "chord_symbol": "Cmaj7",
            "onset_beat": 1.0,
            "local_beat": 1.0,
            "role": "comp",
            "gesture_type": "chordal_onset",
            "pattern_id": "audit_fixture",
            "metadata": {},
        },
        "expression": {
            "profile_name": "audit_fixture",
            "articulation": "sustain",
            "duration_beats": 1.0,
            "velocity": 64,
            "pedal": None,
            "touch": None,
        },
        "voicing": {
            "chord_symbol": "Cmaj7",
            "content_family": "rooted_color",
            "density": density,
            "functional_grouping": grouping,
            "recipe_id": recipe_id,
            "disposition": disposition,
            "root_support": "root_preferred",
            "root_included": True,
            "degrees": ["R", "3", "5", "7"],
            "midi_notes": [48, 52, 55, 59, 64, 67][:density],
            "voice_roles": [],
            "groups": {},
            "projection_map": {},
            "register_guard": {"passed": True, "reasons": []},
            "selector_decision": {"mode": "audit_fixture"},
            "metadata": metadata,
        },
        "realized_notes": [
            {
                "track": "piano",
                "note": note,
                "velocity": 64,
                "start_beat": 1.0,
                "duration_beats": 1.0,
                "timing_intent": "auto",
            }
            for note in [48, 52, 55, 59, 64, 67][:density]
        ],
    }


def test_v2_6_29_doc_exists_and_states_drop_projection_audit_scope() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "v2_6_29",
        "Drop Projection Audit Counts",
        "main_voicing",
        "spread_upper_group",
        "spread_upper_drop_projection_methods_by_density",
        "5-note",
        "6-note",
        "upper group",
        "voicing-only",
        "does not change",
    ]
    for token in required:
        assert token in text


def test_v2_6_29_synthetic_audit_counts_main_and_spread_upper_drop_methods() -> None:
    debug = {
        "title": "drop audit fixture",
        "style": "jazz_ballad",
        "piano_musical_audit_events": [
            _raw_piano_event(
                event_id="spread5",
                density=5,
                grouping="1+4",
                recipe_id="spread_1plus4_contract",
                upper_method="drop2",
                upper_metadata={
                    "open_named_projection_method": "drop2",
                    "open_drop2_projection": True,
                    "spread_upper_projection_uses_drop_family_resource": True,
                },
            ),
            _raw_piano_event(
                event_id="spread6",
                density=6,
                grouping="2+4",
                recipe_id="spread_2plus4_contract",
                upper_method="drop3",
                upper_metadata={
                    "open_named_projection_method": "drop3",
                    "open_drop3_projection": True,
                    "spread_upper_projection_uses_drop_family_resource": True,
                },
            ),
            _raw_piano_event(
                event_id="open4",
                density=4,
                grouping="2+2",
                recipe_id="open_drop2_fixture",
                disposition="open",
                main_metadata={"open_named_projection_method": "drop2", "open_drop2_projection": True},
            ),
        ],
    }
    summary = build_piano_musical_audit(debug).summary

    assert summary["drop_projection_audit_version"] == "v2_6_29"
    assert PIANO_DROP_PROJECTION_AUDIT_VERSION == "v2_6_29"
    assert summary["drop_projection_methods_by_scope"] == {
        "spread_upper_group": {"drop2": 1, "drop3": 1},
        "main_voicing": {"drop2": 1},
    }
    assert summary["drop_projection_methods_total"] == {"drop2": 2, "drop3": 1}
    assert summary["spread_upper_drop_projection_methods_by_density"] == {
        "5": {"drop2": 1},
        "6": {"drop3": 1},
    }
    assert summary["spread_upper_drop_projection_methods_by_grouping"] == {
        "1+4": {"drop2": 1},
        "2+4": {"drop3": 1},
    }
    assert summary["spread_upper_drop_projection_methods_by_recipe"] == {
        "spread_1plus4_contract": {"drop2": 1},
        "spread_2plus4_contract": {"drop3": 1},
    }


def test_v2_6_29_misty_audit_counts_spread_upper_drop_inside_six_note_runtime(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_29.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    audit = build_piano_musical_audit(result.debug).summary

    assert audit["drop_projection_audit_version"] == "v2_6_29"
    assert audit["densities"] == {"5": 124, "6": 72}
    assert audit["functional_groupings"] == {"2+3": 114, "2+4": 68, "1+4": 10, "3+3": 4}
    assert audit["spread_upper_projection_methods"] == {
        "closed_upper_stack": 118,
        "drop3": 72,
        "drop2": 6,
    }
    assert audit["spread_upper_drop_projection_methods"] == {"drop3": 72, "drop2": 6}
    assert audit["spread_upper_drop_projection_events"] == 78
    assert audit["drop_projection_methods_total"] == {"drop3": 72, "drop2": 6}
    assert audit["drop_projection_methods_by_scope"] == {"spread_upper_group": {"drop3": 72, "drop2": 6}}
    assert audit["spread_upper_drop_projection_methods_by_density"] == {"6": {"drop3": 62, "drop2": 6}, "5": {"drop3": 10}}
    assert audit["spread_upper_drop_projection_events_by_density"] == {"6": 68, "5": 10}
    assert audit["spread_upper_drop_projection_methods_by_grouping"] == {"2+4": {"drop3": 62, "drop2": 6}, "1+4": {"drop3": 10}}
    assert audit["spread_upper_drop_projection_methods_by_recipe"] == {
        "spread_2plus4_contract": {"drop3": 62, "drop2": 6},
        "spread_1plus4_contract": {"drop3": 10},
    }

    voicings = [event.get("voicing") or {} for event in result.debug.get("piano_musical_audit_events", [])]
    note_sets = [[int(note) for note in voicing.get("midi_notes", [])] for voicing in voicings]
    assert max(max(notes) for notes in note_sets if notes) <= 74
    assert sum(1 for voicing in voicings if voicing.get("functional_grouping") == "1+4") == 10
    assert [
        voicing
        for voicing in voicings
        if "maj7" in str(voicing.get("chord_symbol"))
        and any(str(degree) == "#11" for degree in voicing.get("degrees", []))
    ] == []
