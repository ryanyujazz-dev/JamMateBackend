from __future__ import annotations

from pathlib import Path

from jammate_engine.generation.piano_audit import build_piano_musical_audit


def test_piano_audit_exposes_open_drop2_projection_fields() -> None:
    audit = build_piano_musical_audit(
        {
            "title": "DROP2 Audit Fixture",
            "style": "medium_swing",
            "timing_policy": {},
            "note_events_by_track": {"piano": 4},
            "piano_musical_audit_events": [
                {
                    "event_id": "evt1",
                    "pattern_event": {
                        "event_id": "evt1",
                        "region_id": "r1",
                        "chord_symbol": "Dm7",
                        "onset_beat": 0.0,
                        "pattern_id": "fixture_pattern",
                        "gesture_type": "simultaneous_onset",
                    },
                    "expression": {"profile_name": "fixture", "articulation": "short", "duration_beats": 0.5, "velocity": 60},
                    "voicing": {
                        "content_family": "seventh_chord_basic",
                        "density": 4,
                        "functional_grouping": "2+2",
                        "recipe_id": "fixture_recipe",
                        "disposition": "open",
                        "root_support": "rootless_allowed",
                        "root_included": True,
                        "degrees": ["R", "5", "b7", "b3"],
                        "midi_notes": [50, 57, 60, 65],
                        "register_guard": {"passed": True, "reasons": ["ok"]},
                        "selector_decision": {"mode": "weighted_pool"},
                        "metadata": {
                            "disposition_projection_family": "open",
                            "disposition_projection_method": "drop2",
                            "migrated_projection_path": "core.voicing.disposition.open.place_drop2_projection_from_closed_parent",
                            "legacy_projection_callback_used": False,
                            "legacy_projection_cleanup_required": False,
                            "open_drop2_projection": True,
                            "open_drop2_span": 15,
                            "open_drop2_parent_closed_degrees": ["R", "b3", "5", "b7"],
                            "open_drop2_parent_closed_notes": [50, 53, 57, 60],
                            "open_drop2_parent_closed_span": 10,
                        },
                    },
                    "realized_notes": [
                        {"note": 50, "velocity": 60, "start_beat": 0.0, "duration_beats": 0.5},
                        {"note": 57, "velocity": 60, "start_beat": 0.0, "duration_beats": 0.5},
                        {"note": 60, "velocity": 60, "start_beat": 0.0, "duration_beats": 0.5},
                        {"note": 65, "velocity": 60, "start_beat": 0.0, "duration_beats": 0.5},
                    ],
                }
            ],
        }
    )

    assert audit.summary["disposition_projection_families"] == {"open": 1}
    assert audit.summary["disposition_projection_methods"] == {"drop2": 1}
    assert audit.summary["open_drop2_events"] == 1
    assert audit.summary["max_open_drop2_span"] == 15
    assert audit.summary["min_open_drop2_lowest_note"] == 50
    assert audit.summary["max_open_drop2_parent_closed_span"] == 10
    assert audit.summary["legacy_projection_callback_used_count"] == 0
    assert audit.event_rows[0]["open_drop2_parent_closed_degrees"] == ["R", "b3", "5", "b7"]


def test_v2_2_8_disposition_docs_record_open_pool_and_phrase_lock() -> None:
    text = Path("docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md").read_text(encoding="utf-8")
    assert "OPEN method candidate pool rule" in text
    assert "OpenProjectionMethod.DROP2" in text
    assert "OpenProjectionMethod.DROP3" in text
    assert "OpenProjectionMethod.DROP2_AND_4" in text
    assert "OpenProjectionMethod.GENERIC_OPEN" in text
    assert "Progression / phrase-level voicing method lock" in text
    assert "ii-V" in text
    assert "V-I" in text
    assert "ii-V-I" in text
