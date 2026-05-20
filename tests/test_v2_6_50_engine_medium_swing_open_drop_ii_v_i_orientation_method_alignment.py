from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace

from jammate_engine.core.expression.expression_plan import EventExpression
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing.runtime.plan import VoicedNote, VoicingPlan
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.realization.realizer_voicing_request_orchestration import (
    MEDIUM_SWING_ROOTLESS_AB_ORIENTATION_ALIGNMENT_VERSION,
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
            VoicedNote(midi_note=57, degree="3", voice_role="lowest"),
            VoicedNote(midi_note=60, degree="5", voice_role="inner_1"),
            VoicedNote(midi_note=64, degree="7", voice_role="inner_2"),
            VoicedNote(midi_note=67, degree="9", voice_role="top"),
        ],
        content_family="rootless_A",
        disposition="open",
        metadata={
            "disposition_projection_family": "open",
            "disposition_projection_method": method,
            **(extra_metadata or {}),
        },
    )


class SequenceResolver:
    def __init__(self, plans: list[VoicingPlan]) -> None:
        self.plans: Iterator[VoicingPlan] = iter(plans)
        self.requests = []

    def resolve(self, request):  # noqa: ANN001 - test double mirrors runtime resolver protocol
        self.requests.append(request)
        plan = next(self.plans)
        return replace(plan, event_id=request.event_id, chord_symbol=request.chord_symbol)


def test_v2_6_50_policy_exposes_rootless_ab_alignment_contract() -> None:
    metadata = dict(get_voicing_policy().metadata or {})

    assert metadata["medium_swing_rootless_ab_orientation_alignment_version"] == "v2_6_50"
    assert metadata["medium_swing_rootless_ab_orientation_alignment_enabled"] is True
    assert metadata["medium_swing_rootless_ab_orientation_alignment_target"] == {
        "scope": "same_texture_scope_local_functional_pair",
        "desired_motion": "flip_A_B_while_preserving_content_type_and_inversion_index",
        "mode": "strict_when_matching_candidate_available",
        "runtime_filtering_enabled": True,
        "does_not_force_rootless_when_seed_is_not_rootless": True,
    }


def test_v2_6_50_orchestrator_requests_ab_flip_inside_method_locked_follow_pair() -> None:
    orchestrator = RealizerVoicingRequestOrchestrator()
    first_plan = _plan(
        "ev1",
        "Dm9",
        "drop2",
        {
            "rootless_ab_orientation_family": "A",
            "rootless_ab_content_type": "with_5",
            "rootless_ab_inversion_index": 0,
        },
    )
    second_plan = _plan("ev2", "G13", "drop2", {"rootless_ab_orientation_family": "B", "rootless_ab_content_type": "with_5", "rootless_ab_inversion_index": 0})
    resolver = SequenceResolver([first_plan, second_plan])
    orchestrator.voicing_resolver = resolver
    orchestrator.begin_realization_pass()
    policy = get_voicing_policy()

    first = _event(1, "Dm9", next_="G13")
    second = _event(2, "G13", previous="Dm9", next_="Cmaj9")
    orchestrator.resolve_event_voicing(event=first, expression=_expr("ev1"), base_policy=policy, ensemble={"bass_present": True})
    orchestrator.resolve_event_voicing(event=second, expression=_expr("ev2"), base_policy=policy, ensemble={"bass_present": True})

    second_meta = resolver.requests[1].policy.metadata
    assert second_meta["medium_swing_phrase_scope_method_lock_policy_applied"] is True
    assert second_meta["medium_swing_rootless_ab_orientation_alignment_version"] == MEDIUM_SWING_ROOTLESS_AB_ORIENTATION_ALIGNMENT_VERSION
    assert second_meta["medium_swing_rootless_ab_orientation_alignment_policy_applied"] is True
    assert second_meta["medium_swing_rootless_ab_orientation_alignment_previous_orientation"] == "A"
    assert second_meta["medium_swing_rootless_ab_orientation_alignment_desired_orientation"] == "B"
    assert second_meta["medium_swing_rootless_ab_orientation_alignment_desired_content_type"] == "with_5"
    assert second_meta["medium_swing_rootless_ab_orientation_alignment_desired_inversion_index"] == 0


def test_v2_6_50_candidate_generation_filters_to_matching_rootless_ab_orientation_when_available() -> None:
    policy = get_voicing_policy()
    metadata = dict(policy.metadata or {})
    metadata.update(
        {
            "medium_swing_rootless_ab_orientation_alignment_runtime_enabled": True,
            "medium_swing_rootless_ab_orientation_alignment_policy_applied": True,
            "medium_swing_rootless_ab_orientation_alignment_runtime_filtering_enabled": True,
            "medium_swing_rootless_ab_orientation_alignment_desired_orientation": "B",
            "medium_swing_rootless_ab_orientation_alignment_desired_content_type": "with_13",
            "medium_swing_rootless_ab_orientation_alignment_desired_inversion_index": 0,
        }
    )
    candidates = generate_candidates("G13", replace(policy, metadata=metadata))

    assert candidates
    assert {candidate.metadata.get("rootless_ab_orientation_family") for candidate in candidates} == {"B"}
    assert {candidate.metadata.get("rootless_ab_content_type") for candidate in candidates} == {"with_13"}
    assert {candidate.metadata.get("rootless_ab_inversion_index") for candidate in candidates} == {0}
    assert all(candidate.metadata.get("medium_swing_rootless_ab_orientation_alignment_filter_applied") is True for candidate in candidates)
    assert all(candidate.metadata.get("medium_swing_rootless_ab_orientation_alignment_candidate_matches") is True for candidate in candidates)


def _raw_audit_event(index: int, *, chord: str, orientation: str, desired: str, match: bool) -> dict:
    event_id = f"ab_audit_{index}"
    metadata = {
        "disposition_projection_family": "open",
        "disposition_projection_method": "drop2",
        "rootless_ab_orientation_family": orientation,
        "rootless_ab_content_type": "with_5",
        "rootless_ab_inversion_index": 0,
        "medium_swing_rootless_ab_orientation_alignment_runtime_enabled": True,
        "medium_swing_rootless_ab_orientation_alignment_policy_applied": True,
        "medium_swing_rootless_ab_orientation_alignment_reason": "method_locked_local_progression_follow_region_requests_ab_flip",
        "medium_swing_rootless_ab_orientation_alignment_pair_type": "ii_v",
        "medium_swing_rootless_ab_orientation_alignment_previous_region_id": f"r{index - 1}",
        "medium_swing_rootless_ab_orientation_alignment_previous_orientation": "A" if desired == "B" else "B",
        "medium_swing_rootless_ab_orientation_alignment_desired_orientation": desired,
        "medium_swing_rootless_ab_orientation_alignment_desired_content_type": "with_5",
        "medium_swing_rootless_ab_orientation_alignment_desired_inversion_index": 0,
        "medium_swing_rootless_ab_orientation_alignment_filter_applied": match,
        "medium_swing_rootless_ab_orientation_alignment_filter_reason": "filtered_to_matching_rootless_ab_orientation" if match else "no_matching_rootless_ab_candidate_available",
        "medium_swing_rootless_ab_orientation_alignment_candidate_matches": match,
        "medium_swing_rootless_ab_orientation_alignment_selected_orientation": orientation,
        "medium_swing_rootless_ab_orientation_alignment_selected_content_type": "with_5",
        "medium_swing_rootless_ab_orientation_alignment_selected_inversion_index": 0,
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
            "pattern_id": "medium_swing_piano_anchor_1",
            "metadata": {},
        },
        "expression": {"event_id": event_id, "profile_name": "comp_short", "articulation": "short", "duration_beats": 0.5, "velocity": 60, "pedal": "none", "touch": "clear"},
        "voicing": {
            "event_id": event_id,
            "chord_symbol": chord,
            "midi_notes": [57, 60, 64, 67],
            "degrees": ["3", "5", "7", "9"],
            "voice_roles": ["lowest", "inner_1", "inner_2", "top"],
            "groups": {},
            "projection_map": {},
            "content_family": "rootless_A" if orientation == "A" else "rootless_B",
            "disposition": "open",
            "root_support": "rootless_allowed",
            "root_included": False,
            "density": 4,
            "functional_grouping": "2+2",
            "recipe_id": "d4__2plus2__rootless_ab",
            "register_guard": {"passed": True, "reasons": ["ok"]},
            "selector_decision": {"mode": "weighted_pool", "selected_rank": 1, "selected_score": 1.0, "candidate_count": 4},
            "metadata": metadata,
        },
        "realized_notes": [
            {"note": note, "start_beat": float(index * 4), "duration_beats": 0.5, "velocity": 60, "track": "piano", "channel": 0, "timing_intent": "auto"}
            for note in [57, 60, 64, 67]
        ],
    }


def test_v2_6_50_piano_audit_reports_rootless_ab_orientation_alignment() -> None:
    summary = build_piano_musical_audit(
        {
            "title": "Synthetic",
            "piano_musical_audit_events": [
                _raw_audit_event(1, chord="G13", orientation="B", desired="B", match=True),
                _raw_audit_event(2, chord="Cmaj9", orientation="A", desired="A", match=True),
            ],
        }
    ).summary

    assert summary["medium_swing_rootless_ab_orientation_alignment_version"] == "v2_6_50"
    assert summary["medium_swing_rootless_ab_orientation_alignment_policy_applied_events"] == 2
    assert summary["medium_swing_rootless_ab_orientation_alignment_filter_applied_events"] == 2
    assert summary["medium_swing_rootless_ab_orientation_alignment_candidate_match_events"] == 2
    assert summary["medium_swing_rootless_ab_orientation_alignment_candidate_mismatch_events"] == 0
    assert summary["medium_swing_rootless_ab_orientation_alignment_desired_orientations"] == {"B": 1, "A": 1}
    assert summary["medium_swing_rootless_ab_orientation_alignment_checkpoint_passed"] is True
