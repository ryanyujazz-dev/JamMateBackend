from __future__ import annotations

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy


def _raw_event(index: int, *, method: str, notes: list[int], scope: str, role: str, region: str | None = None) -> dict:
    event_id = f"v2_6_47_e{index}"
    region_id = region or f"r{index}"
    return {
        "event_id": event_id,
        "pattern_event": {
            "event_id": event_id,
            "track": "piano",
            "region_id": region_id,
            "chord_symbol": "Dm7" if index % 2 == 0 else "G7",
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
            "chord_symbol": "Dm7" if index % 2 == 0 else "G7",
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
        "title": "Synthetic Medium Swing Section Boundary Review",
        "style": "medium_swing",
        "timing_policy": {"feel": "swing", "swing_ratio": 2 / 3, "half_beat_grid": 0.5},
        "note_events_by_track": {"piano": len(events) * 4},
        "expression_foundation_audit_events": [],
        "piano_musical_audit_events": events,
    }


def test_v2_6_47_medium_swing_policy_exposes_section_boundary_method_lock_review() -> None:
    metadata = dict(get_voicing_policy().metadata or {})

    assert metadata["medium_swing_open_drop_section_boundary_review_version"] == "v2_6_47"
    assert metadata["medium_swing_open_drop_section_boundary_review_thresholds"] == {
        "boundary_events_min": 6,
        "drop2_and_4_entry_events": 0,
        "warning_events": 0,
        "top_motion_max_abs": 7,
        "low_motion_max_abs": 8,
        "avg_motion_max": 6.0,
    }


def test_v2_6_47_piano_audit_accepts_readable_drop2_drop3_section_boundary_entries() -> None:
    note_pool = [[55, 60, 64, 69], [56, 60, 65, 70], [55, 59, 64, 69], [56, 61, 65, 70]]
    roles = ["baseline_open_swing", "bridge_open_contrast", "baseline_open_swing", "final_chorus_open_lift"]
    methods = ["drop2", "drop3", "drop2", "drop3"]
    events = []
    for index in range(84):
        section = index // 12
        role = roles[section % len(roles)]
        method = methods[section % len(methods)]
        events.append(
            _raw_event(
                index,
                method=method,
                notes=note_pool[index % len(note_pool)],
                scope=f"section:{section}",
                role=role,
            )
        )

    summary = build_piano_musical_audit(_debug(events)).summary

    assert summary["medium_swing_open_drop_section_boundary_review_version"] == "v2_6_47"
    assert summary["medium_swing_open_drop_section_boundary_review_events"] >= 6
    assert summary["medium_swing_open_drop_section_boundary_review_warning_events"] == 0
    assert summary["medium_swing_open_drop_section_boundary_review_drop2_and_4_entry_events"] == 0
    assert summary["medium_swing_open_drop_section_boundary_review_checkpoint_passed"] is True
    assert set(summary["medium_swing_open_drop_section_boundary_review_entry_methods_by_role"].keys()) >= {
        "baseline_open_swing",
        "bridge_open_contrast",
        "final_chorus_open_lift",
    }


def test_v2_6_47_piano_audit_flags_drop2_and_4_section_boundary_entry_without_changing_notes() -> None:
    events = []
    for index in range(84):
        section = index // 12
        method = "drop2_and_4" if section == 1 and index == 12 else ("drop3" if section % 2 else "drop2")
        role = "bridge_open_contrast" if section == 1 else "baseline_open_swing"
        events.append(
            _raw_event(
                index,
                method=method,
                notes=[55 + (index % 2), 60, 64, 69],
                scope=f"section:{section}",
                role=role,
            )
        )

    summary = build_piano_musical_audit(_debug(events)).summary

    assert summary["medium_swing_open_drop_section_boundary_review_events"] >= 6
    assert summary["medium_swing_open_drop_section_boundary_review_drop2_and_4_entry_events"] >= 1
    assert summary["medium_swing_open_drop_section_boundary_review_warning_events"] >= 1
    assert summary["medium_swing_open_drop_section_boundary_review_checkpoint_passed"] is False
    assert summary["disposition_projection_methods"]["drop2_and_4"] == 1
