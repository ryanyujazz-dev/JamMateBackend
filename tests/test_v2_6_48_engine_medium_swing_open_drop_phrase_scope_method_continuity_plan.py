from __future__ import annotations

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy


def _raw_event(index: int, *, chord: str, method: str, notes: list[int], scope: str = "section:A", role: str = "baseline_open_swing") -> dict:
    event_id = f"v2_6_48_e{index}"
    return {
        "event_id": event_id,
        "pattern_event": {
            "event_id": event_id,
            "track": "piano",
            "region_id": f"r{index}",
            "chord_symbol": chord,
            "onset_beat": float(index * 4),
            "local_beat": 0.0,
            "role": "comp",
            "gesture_type": "simultaneous_onset",
            "gesture": {"gesture_type": "simultaneous_onset", "projection_refs": [], "onset_offsets_beats": [], "metadata": {}},
            "expression_hint": None,
            "pattern_id": "medium_swing_piano_anchor_1",
            "source_event_id": None,
            "status": "active",
            "metadata": {},
        },
        "expression": {
            "event_id": event_id,
            "profile_name": "comp_short",
            "articulation": "short",
            "duration_beats": 0.5,
            "velocity": 60,
            "pedal": "none",
            "touch": "clear",
        },
        "voicing": {
            "event_id": event_id,
            "chord_symbol": chord,
            "midi_notes": list(notes),
            "degrees": ["R", "3", "5", "b7"],
            "voice_roles": ["lowest", "inner_1", "inner_2", "top"],
            "groups": {},
            "projection_map": {},
            "content_family": "seventh_chord_basic",
            "disposition": "open",
            "root_support": "rootless_allowed",
            "root_included": True,
            "density": 4,
            "functional_grouping": "2+2",
            "recipe_id": "d4__2plus2__seventh_chord_basic__rootless_allowed",
            "register_guard": {"passed": True, "reasons": ["ok"]},
            "selector_decision": {"mode": "weighted_pool", "selected_rank": 1, "selected_score": 1.0, "candidate_count": 4},
            "metadata": {
                "disposition_projection_family": "open",
                "disposition_projection_method": method,
                "voicing_texture_state": {
                    "scope_id": scope,
                    "scope_type": "section",
                    "primary_family": "open",
                    "allowed_families": ["open"],
                    "contrast_role": role,
                    "open_method_weights": {"generic_open": 0.0, "drop2": 0.52, "drop3": 0.38, "drop2_and_4": 0.10},
                },
            },
        },
        "realized_notes": [
            {"note": note, "start_beat": float(index * 4), "duration_beats": 0.5, "velocity": 60, "track": "piano", "channel": 0, "timing_intent": "auto"}
            for note in notes
        ],
    }


def _debug(events: list[dict]) -> dict:
    return {
        "title": "Synthetic Medium Swing Phrase-Scope Method Continuity",
        "style": "medium_swing",
        "timing_policy": {"feel": "swing", "swing_ratio": 2 / 3, "half_beat_grid": 0.5},
        "note_events_by_track": {"piano": len(events) * 4},
        "expression_foundation_audit_events": [],
        "piano_musical_audit_events": events,
    }


def _acceptable_phrase_events() -> list[dict]:
    chords = ["Dm7", "G7", "Cmaj7", "Fmaj7"]
    methods = ["drop2", "drop2", "drop2", "drop3"]
    notes = [[55, 60, 64, 69], [56, 60, 65, 70], [55, 59, 64, 69], [56, 61, 65, 70]]
    events: list[dict] = []
    for phrase_index in range(8):
        for offset, chord in enumerate(chords):
            index = phrase_index * 4 + offset
            events.append(
                _raw_event(
                    index,
                    chord=chord,
                    method=methods[offset],
                    notes=notes[offset],
                    scope=f"section:{phrase_index // 2}",
                    role="bridge_open_contrast" if phrase_index // 2 == 1 else "baseline_open_swing",
                )
            )
    return events


def test_v2_6_48_policy_exposes_phrase_scope_method_continuity_plan() -> None:
    metadata = dict(get_voicing_policy().metadata or {})

    assert metadata["medium_swing_phrase_scope_method_continuity_version"] == "v2_6_48"
    assert metadata["medium_swing_phrase_scope_method_continuity_thresholds"] == {
        "phrase_scope_events_min": 20,
        "method_switch_ratio_max": 0.70,
        "drop2_and_4_run_max": 2,
        "high_motion_switch_events": 0,
        "avg_motion_max": 6.0,
    }


def test_v2_6_48_piano_audit_reports_phrase_scope_method_continuity_without_runtime_changes() -> None:
    summary = build_piano_musical_audit(_debug(_acceptable_phrase_events())).summary

    assert summary["medium_swing_phrase_scope_method_continuity_version"] == "v2_6_48"
    assert summary["medium_swing_phrase_scope_events"] >= 20
    assert summary["medium_swing_phrase_scope_method_switch_events"] == 8
    assert summary["medium_swing_phrase_scope_method_switch_ratio"] <= 0.70
    assert summary["medium_swing_phrase_scope_drop2_and_4_run_max"] == 0
    assert summary["medium_swing_phrase_scope_ii_v_i_events"] == 8
    assert summary["medium_swing_phrase_scope_ii_v_i_method_consistent_events"] == 8
    assert summary["medium_swing_phrase_scope_high_motion_switch_events"] == 0
    assert summary["medium_swing_phrase_scope_checkpoint_passed"] is True


def test_v2_6_48_piano_audit_flags_drop2_and_4_run_and_high_motion_method_switch() -> None:
    events = _acceptable_phrase_events()
    events[0]["voicing"]["metadata"]["disposition_projection_method"] = "drop2"
    events[1]["voicing"]["metadata"]["disposition_projection_method"] = "drop3"
    events[1]["voicing"]["midi_notes"] = [70, 75, 79, 84]
    events[1]["realized_notes"] = [
        {"note": note, "start_beat": 4.0, "duration_beats": 0.5, "velocity": 60, "track": "piano", "channel": 0, "timing_intent": "auto"}
        for note in [70, 75, 79, 84]
    ]
    for index in (4, 5, 6):
        events[index]["voicing"]["metadata"]["disposition_projection_method"] = "drop2_and_4"

    summary = build_piano_musical_audit(_debug(events)).summary

    assert summary["medium_swing_phrase_scope_drop2_and_4_run_max"] == 3
    assert summary["medium_swing_phrase_scope_high_motion_switch_events"] >= 1
    assert summary["medium_swing_phrase_scope_warning_events"] >= 1
    assert summary["medium_swing_phrase_scope_checkpoint_passed"] is False
