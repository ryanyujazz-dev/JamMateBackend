from __future__ import annotations

from collections.abc import Iterator

from jammate_engine.core.expression.expression_plan import EventExpression
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing.runtime.plan import VoicedNote, VoicingPlan
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.realization.realizer_voicing_request_orchestration import (
    MEDIUM_SWING_PHRASE_SCOPE_METHOD_LOCK_POLICY_VERSION,
    RealizerVoicingRequestOrchestrator,
)
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy


def _event(index: int, chord: str, *, previous: str | None = None, next_: str | None = None, section: str = "A") -> PatternEvent:
    return PatternEvent(
        event_id=f"ev{index}",
        track="piano",
        region_id=f"c0_b{index}_ch0_{chord}",
        chord_symbol=chord,
        onset_beat=float(index * 4),
        local_beat=0.0,
        role="comp",
        metadata={
            "previous_chord_symbol": previous,
            "next_chord_symbol": next_,
            "region_section_id": section,
            "region_section_label": section,
            "region_phrase": section,
            "region_section_role": "normal",
            "region_chorus_index": 0,
            "region_total_choruses": 1,
            "region_performance_bar_index": index,
            "region_chord_index": 0,
        },
    )


def _expr(event_id: str) -> EventExpression:
    return EventExpression(event_id=event_id, duration_beats=0.5, velocity=64, articulation="short", pedal="none")


def _plan(event_id: str, chord: str, method: str, extra_metadata: dict | None = None) -> VoicingPlan:
    return VoicingPlan(
        event_id=event_id,
        chord_symbol=chord,
        notes=[
            VoicedNote(midi_note=55, degree="R", voice_role="lowest"),
            VoicedNote(midi_note=59, degree="3", voice_role="inner_1"),
            VoicedNote(midi_note=62, degree="5", voice_role="inner_2"),
            VoicedNote(midi_note=65, degree="7", voice_role="top"),
        ],
        disposition="open",
        metadata={
            "disposition_projection_family": "open",
            "disposition_projection_method": method,
            **(extra_metadata or {}),
        },
    )


class SequenceResolver:
    def __init__(self, methods: list[str]) -> None:
        self.methods: Iterator[str] = iter(methods)
        self.requests = []

    def resolve(self, request):  # noqa: ANN001 - test double mirrors runtime resolver protocol
        self.requests.append(request)
        method = next(self.methods)
        return _plan(request.event_id, request.chord_symbol, method, dict(request.policy.metadata or {}))


def test_v2_6_49_policy_exposes_runtime_method_lock_contract() -> None:
    metadata = dict(get_voicing_policy().metadata or {})

    assert metadata["medium_swing_phrase_scope_method_lock_policy_version"] == "v2_6_49"
    assert metadata["medium_swing_phrase_scope_method_lock_policy_enabled"] is True
    assert metadata["medium_swing_phrase_scope_method_lock_policy_target"] == {
        "locked_pair_types": ["ii_v", "minor_ii_v", "v_i_major", "v_i_minor", "dominant_to_tonic"],
        "propagated_seed_methods": ["drop2", "drop3"],
        "non_propagated_color_methods": ["drop2_and_4", "generic_open"],
        "runtime_filtering_enabled": True,
        "same_texture_scope_only": True,
    }


def test_v2_6_49_orchestrator_locks_local_ii_v_i_follow_regions_to_previous_drop_method() -> None:
    orchestrator = RealizerVoicingRequestOrchestrator()
    resolver = SequenceResolver(["drop2", "drop2", "drop2"])
    orchestrator.voicing_resolver = resolver
    orchestrator.begin_realization_pass()
    policy = get_voicing_policy()
    events = [
        _event(1, "Dm7", next_="G7"),
        _event(2, "G7", previous="Dm7", next_="Cmaj7"),
        _event(3, "Cmaj7", previous="G7"),
    ]

    for event in events:
        orchestrator.resolve_event_voicing(event=event, expression=_expr(event.event_id), base_policy=policy, ensemble={"bass_present": True})

    assert len(resolver.requests) == 3
    first_meta = resolver.requests[0].policy.metadata
    second_meta = resolver.requests[1].policy.metadata
    third_meta = resolver.requests[2].policy.metadata

    assert first_meta["medium_swing_phrase_scope_method_lock_policy_applied"] is False
    assert second_meta["medium_swing_phrase_scope_method_lock_policy_applied"] is True
    assert second_meta["medium_swing_phrase_scope_method_lock_policy_pair_type"] == "ii_v"
    assert second_meta["medium_swing_phrase_scope_method_lock_policy_previous_method"] == "drop2"
    assert second_meta["voicing_method_lock"]["family"] == "open"
    assert second_meta["voicing_method_lock"]["method"] == "drop2"
    assert second_meta["voicing_method_lock"]["runtime_filtering_enabled"] is True
    assert second_meta["method_lock_runtime_filtering_enabled"] is True

    assert third_meta["medium_swing_phrase_scope_method_lock_policy_applied"] is True
    assert third_meta["medium_swing_phrase_scope_method_lock_policy_pair_type"] in {"v_i_major", "dominant_to_tonic"}
    assert third_meta["voicing_method_lock"]["method"] == "drop2"


def test_v2_6_49_orchestrator_does_not_propagate_drop2_and_4_as_phrase_body() -> None:
    orchestrator = RealizerVoicingRequestOrchestrator()
    resolver = SequenceResolver(["drop2_and_4", "drop2"])
    orchestrator.voicing_resolver = resolver
    orchestrator.begin_realization_pass()
    policy = get_voicing_policy()

    first = _event(1, "Dm7", next_="G7")
    second = _event(2, "G7", previous="Dm7", next_="Cmaj7")
    orchestrator.resolve_event_voicing(event=first, expression=_expr("ev1"), base_policy=policy, ensemble={"bass_present": True})
    orchestrator.resolve_event_voicing(event=second, expression=_expr("ev2"), base_policy=policy, ensemble={"bass_present": True})

    second_meta = resolver.requests[1].policy.metadata
    assert second_meta["medium_swing_phrase_scope_method_lock_policy_applied"] is False
    assert second_meta["medium_swing_phrase_scope_method_lock_policy_reason"] == "previous_method_not_propagated"
    assert "voicing_method_lock" not in second_meta


def _raw_audit_event(index: int, *, chord: str, method: str, lock_applied: bool, pair_type: str = "", candidate_match: bool = True) -> dict:
    event_id = f"lock_audit_{index}"
    metadata = {
        "disposition_projection_family": "open",
        "disposition_projection_method": method,
        "medium_swing_phrase_scope_method_lock_policy_runtime_enabled": True,
        "medium_swing_phrase_scope_method_lock_policy_applied": lock_applied,
        "medium_swing_phrase_scope_method_lock_policy_reason": "local_progression_follow_region_locked_to_previous_method" if lock_applied else "no_previous_distinct_seed_region",
        "medium_swing_phrase_scope_method_lock_policy_pair_type": pair_type,
        "medium_swing_phrase_scope_method_lock_policy_previous_method": method,
        "medium_swing_phrase_scope_method_lock_policy_previous_region_id": f"r{index - 1}",
        "voicing_method_lock_candidate_matches": candidate_match if lock_applied else False,
        "voicing_method_lock_runtime_filtering_enabled": lock_applied,
        "voicing_texture_state": {
            "scope_id": "chorus:0|section:A",
            "scope_type": "section",
            "primary_family": "open",
            "allowed_families": ["open"],
            "contrast_role": "baseline_open_swing",
        },
    }
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
        "expression": {"event_id": event_id, "profile_name": "comp_short", "articulation": "short", "duration_beats": 0.5, "velocity": 60, "pedal": "none", "touch": "clear"},
        "voicing": {
            "event_id": event_id,
            "chord_symbol": chord,
            "midi_notes": [55, 59, 62, 65],
            "degrees": ["R", "3", "5", "7"],
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
            "metadata": metadata,
        },
        "realized_notes": [
            {"note": note, "start_beat": float(index * 4), "duration_beats": 0.5, "velocity": 60, "track": "piano", "channel": 0, "timing_intent": "auto"}
            for note in [55, 59, 62, 65]
        ],
    }


def test_v2_6_49_piano_audit_reports_method_lock_policy_application_and_matches() -> None:
    events = [
        _raw_audit_event(1, chord="Dm7", method="drop2", lock_applied=False),
        _raw_audit_event(2, chord="G7", method="drop2", lock_applied=True, pair_type="ii_v"),
        _raw_audit_event(3, chord="Cmaj7", method="drop2", lock_applied=True, pair_type="v_i_major"),
    ]
    summary = build_piano_musical_audit(
        {
            "title": "Synthetic v2_6_49",
            "style": "medium_swing",
            "timing_policy": {"feel": "swing"},
            "piano_musical_audit_events": events,
            "expression_foundation_audit_events": [],
        }
    ).summary

    assert MEDIUM_SWING_PHRASE_SCOPE_METHOD_LOCK_POLICY_VERSION == "v2_6_49"
    assert summary["medium_swing_phrase_scope_method_lock_policy_version"] == "v2_6_49"
    assert summary["medium_swing_phrase_scope_method_lock_policy_applied_events"] == 2
    assert summary["medium_swing_phrase_scope_method_lock_policy_candidate_match_events"] == 2
    assert summary["medium_swing_phrase_scope_method_lock_policy_candidate_mismatch_events"] == 0
    assert summary["medium_swing_phrase_scope_method_lock_policy_runtime_filtering_events"] == 2
    assert summary["medium_swing_phrase_scope_method_lock_policy_pair_types"] == {"ii_v": 1, "v_i_major": 1}
    assert summary["medium_swing_phrase_scope_method_lock_policy_checkpoint_passed"] is True
