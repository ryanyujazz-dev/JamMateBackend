from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.generation.piano_audit import build_piano_musical_audit


def _raw_event(event_id: str, *, role: str, method: str) -> dict:
    return {
        "event_id": event_id,
        "pattern_event": {
            "event_id": event_id,
            "track": "piano",
            "region_id": f"r_{event_id}",
            "chord_symbol": "G7",
            "onset_beat": 0.0,
            "local_beat": 0.0,
            "role": "comp",
            "gesture_type": "simultaneous_onset",
            "gesture": {"gesture_type": "simultaneous_onset", "projection_refs": [], "onset_offsets_beats": [], "metadata": {}},
            "expression_hint": None,
            "pattern_id": "test_pattern",
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
            "chord_symbol": "G7",
            "midi_notes": [55, 59, 62, 65],
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
            "recipe_id": "d4__2_plus_2__basic_seventh_chord",
            "register_guard": {"passed": True, "reasons": ["ok"]},
            "selector_decision": {"mode": "weighted_pool", "selected_rank": 1, "selected_score": 1.0, "candidate_count": 4},
            "metadata": {
                "disposition_projection_family": "open",
                "disposition_projection_method": method,
                "voicing_texture_state": {
                    "scope_id": f"chorus:0|section:{role}",
                    "scope_type": "section",
                    "primary_family": "open",
                    "allowed_families": ["open"],
                    "contrast_role": role,
                    "open_method_weights": {"generic_open": 0.28, "drop2": 0.36, "drop3": 0.26, "drop2_and_4": 0.10},
                },
            },
        },
        "realized_notes": [
            {"note": 55, "start_beat": 0.0, "duration_beats": 0.5, "velocity": 60, "track": "piano", "channel": 0, "timing_intent": "auto"},
            {"note": 59, "start_beat": 0.0, "duration_beats": 0.5, "velocity": 60, "track": "piano", "channel": 0, "timing_intent": "auto"},
            {"note": 62, "start_beat": 0.0, "duration_beats": 0.5, "velocity": 60, "track": "piano", "channel": 0, "timing_intent": "auto"},
            {"note": 65, "start_beat": 0.0, "duration_beats": 0.5, "velocity": 60, "track": "piano", "channel": 0, "timing_intent": "auto"},
        ],
    }


def _audit_script_module():
    path = Path("examples/scripts/generate_medium_swing_texture_method_audit.py")
    spec = spec_from_file_location("medium_swing_texture_method_audit", path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_2_38_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"


def test_piano_audit_reports_texture_methods_by_contrast_role() -> None:
    debug = {
        "title": "Synthetic Texture Audit",
        "style": "medium_swing",
        "timing_policy": {},
        "note_events_by_track": {"piano": 12},
        "expression_foundation_audit_events": [],
        "piano_musical_audit_events": [
            _raw_event("e1", role="baseline_open_swing", method="drop2"),
            _raw_event("e2", role="baseline_open_swing", method="generic_open"),
            _raw_event("e3", role="bridge_open_contrast", method="drop3"),
            _raw_event("e4", role="final_chorus_open_lift", method="drop2"),
        ],
    }
    audit = build_piano_musical_audit(debug)
    summary = audit.summary

    assert summary["contract_version"] == "v2_2_38"
    assert summary["voicing_texture_contrast_roles"] == {
        "baseline_open_swing": 2,
        "bridge_open_contrast": 1,
        "final_chorus_open_lift": 1,
    }
    assert summary["voicing_texture_methods_by_contrast_role"]["bridge_open_contrast"] == {"drop3": 1}
    assert summary["voicing_texture_method_percentages_by_contrast_role"]["baseline_open_swing"] == {"drop2": 0.5, "generic_open": 0.5}
    assert summary["voicing_texture_open_method_weight_plans_by_contrast_role"]["baseline_open_swing"]["drop2"] == 0.36


def test_medium_swing_texture_method_audit_acceptance_checks_balance_direction() -> None:
    module = _audit_script_module()
    outputs = [
        {
            "ok": True,
            "slug": "synthetic_standard",
            "events": 120,
            "families": {"open": 120},
            "methods": {"drop2": 55, "drop3": 35, "generic_open": 25, "drop2_and_4": 5},
            "contrast_roles": {"baseline_open_swing": 60, "bridge_open_contrast": 30, "final_chorus_open_lift": 30},
            "method_percentages_by_contrast_role": {
                "baseline_open_swing": {"drop2": 0.50, "drop3": 0.10, "generic_open": 0.40},
                "bridge_open_contrast": {"drop2": 0.30, "drop3": 0.40, "generic_open": 0.30},
                "final_chorus_open_lift": {"drop2": 0.45, "drop3": 0.35, "generic_open": 0.15, "drop2_and_4": 0.05},
            },
            "failed_register_guard_count": 0,
            "missing_note_events": 0,
        }
    ]

    acceptance = module._acceptance(outputs)
    assert acceptance["passed"] is True
    assert acceptance["failed_checks"] == []
