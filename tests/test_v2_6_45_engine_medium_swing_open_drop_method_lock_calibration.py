from __future__ import annotations

from collections.abc import Iterable

from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing import derive_voicing_texture_state
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.realization.voicing_policy_context_adapter import _policy_with_event_texture_scope
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy


def _event(section_id: str, *, role: str = "normal", phrase: str | None = None, chorus_index: int = 0, total: int = 3) -> PatternEvent:
    return PatternEvent(
        event_id=f"c{chorus_index}_{section_id}_event",
        track="piano",
        region_id=f"c{chorus_index}_{section_id}_r0",
        chord_symbol="G7",
        onset_beat=0.0,
        role="comp",
        local_beat=0.0,
        metadata={
            "region_section_id": section_id,
            "region_section_label": section_id,
            "region_phrase": phrase or ("B" if section_id == "B" else "A"),
            "region_section_role": role,
            "region_chorus_index": chorus_index,
            "region_total_choruses": total,
            "region_performance_bar_index": 8,
        },
    )


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
                    "open_method_weights": {"generic_open": 0.0, "drop2": 0.52, "drop3": 0.38, "drop2_and_4": 0.10},
                },
            },
        },
        "realized_notes": [
            {"note": note, "start_beat": 0.0, "duration_beats": 0.5, "velocity": 60, "track": "piano", "channel": 0, "timing_intent": "auto"}
            for note in [55, 59, 62, 65]
        ],
    }


def _events(role: str, methods: Iterable[str], *, prefix: str) -> list[dict]:
    return [_raw_event(f"{prefix}_{idx}", role=role, method=method) for idx, method in enumerate(methods)]


def test_v2_6_45_medium_swing_policy_freezes_calibrated_open_drop_weights() -> None:
    policy = get_voicing_policy()
    metadata = dict(policy.metadata or {})

    assert metadata["medium_swing_open_drop_method_lock_calibration_version"] == "v2_6_45"
    assert metadata["disposition_method_weights"]["open"] == {
        "generic_open": 0.0,
        "drop2": 0.52,
        "drop3": 0.38,
        "drop2_and_4": 0.10,
    }
    assert metadata["medium_swing_open_drop_method_lock_calibration_target"]["drop2_and_4_total_ratio_max"] == 0.20


def test_v2_6_45_medium_swing_bridge_and_final_chorus_keep_drop3_lift_with_controlled_drop24() -> None:
    base = get_voicing_policy()
    baseline_policy = _policy_with_event_texture_scope(base, _event("A1", chorus_index=0, total=3))
    bridge_policy = _policy_with_event_texture_scope(base, _event("B", role="bridge", phrase="B", chorus_index=0, total=3))
    final_policy = _policy_with_event_texture_scope(base, _event("A1", chorus_index=2, total=3))

    baseline_state = derive_voicing_texture_state(baseline_policy)
    bridge_state = derive_voicing_texture_state(bridge_policy)
    final_state = derive_voicing_texture_state(final_policy)

    assert baseline_state.open_method_weights == {"generic_open": 0.0, "drop2": 0.52, "drop3": 0.38, "drop2_and_4": 0.10}
    assert bridge_state.open_method_weights == {"generic_open": 0.0, "drop2": 0.35, "drop3": 0.53, "drop2_and_4": 0.10}
    assert final_state.open_method_weights == {"generic_open": 0.0, "drop2": 0.43, "drop3": 0.48, "drop2_and_4": 0.08}
    assert bridge_state.open_method_weights["drop3"] > baseline_state.open_method_weights["drop3"]
    assert final_state.open_method_weights["drop3"] > baseline_state.open_method_weights["drop3"]
    assert final_state.open_method_weights["drop2_and_4"] < baseline_state.open_method_weights["drop2_and_4"]


def test_v2_6_45_piano_audit_exposes_medium_swing_open_drop_checkpoint() -> None:
    events = []
    events += _events("baseline_open_swing", ["drop2"] * 55 + ["drop3"] * 25 + ["drop2_and_4"] * 8, prefix="b")
    events += _events("bridge_open_contrast", ["drop3"] * 18 + ["drop2"] * 6 + ["drop2_and_4"] * 2, prefix="br")
    events += _events("final_chorus_open_lift", ["drop3"] * 20 + ["drop2"] * 8 + ["drop2_and_4"] * 2, prefix="f")
    debug = {
        "title": "Synthetic Medium Swing Open Drop Calibration",
        "style": "medium_swing",
        "timing_policy": {},
        "note_events_by_track": {"piano": len(events)},
        "expression_foundation_audit_events": [],
        "piano_musical_audit_events": events,
    }

    summary = build_piano_musical_audit(debug).summary

    assert summary["medium_swing_open_drop_method_lock_calibration_version"] == "v2_6_45"
    assert summary["medium_swing_open_drop_method_lock_calibration_active"] is True
    assert summary["medium_swing_open_drop_method_lock_calibration_drop2_and_4_controlled"] is True
    assert summary["medium_swing_open_drop_method_lock_calibration_bridge_drop3_lift"] is True
    assert summary["medium_swing_open_drop_method_lock_calibration_final_drop3_lift"] is True
    assert summary["medium_swing_open_drop_method_lock_calibration_open_family_only"] is True
    assert summary["medium_swing_open_drop_method_lock_calibration_checkpoint_passed"] is True
    assert summary["medium_swing_open_drop_method_lock_calibration_drop2_and_4_ratio"] <= 0.20
