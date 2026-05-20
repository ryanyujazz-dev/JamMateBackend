from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace

from jammate_engine.core.expression.expression_plan import EventExpression
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing.runtime.plan import VoicedNote, VoicingPlan
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.realization.realizer_voicing_request_orchestration import (
    MEDIUM_SWING_FOUR_NOTE_ROTATION_ALIGNMENT_VERSION,
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


def _basic_plan(event_id: str, chord: str, method: str, inversion_index: int) -> VoicingPlan:
    return VoicingPlan(
        event_id=event_id,
        chord_symbol=chord,
        notes=[
            VoicedNote(midi_note=50, degree="R", voice_role="lowest"),
            VoicedNote(midi_note=53, degree="3", voice_role="inner_1"),
            VoicedNote(midi_note=57, degree="5", voice_role="inner_2"),
            VoicedNote(midi_note=60, degree="7", voice_role="top"),
        ],
        content_family="seventh_chord_basic",
        disposition="open",
        metadata={
            "disposition_projection_family": "open",
            "disposition_projection_method": method,
            "four_note_rotation_family": "basic_4note",
            "four_note_rotation_content_type": "root_third_fifth_seventh",
            "four_note_rotation_source_family": "root_third_fifth_seventh",
            "four_note_rotation_ab_side": "A" if inversion_index in {0, 1} else "B",
            "four_note_rotation_ab_pair_index": inversion_index % 2,
            "four_note_rotation_inversion_index": inversion_index,
            "four_note_rotation_follow_inversion_index": (inversion_index + 2) % 4,
            "four_note_rotation_ab_eligible": True,
            "basic_4note_inversion_index": inversion_index,
            "basic_4note_functional_content_type": "root_third_fifth_seventh",
            "basic_4note_source_family": "root_third_fifth_seventh",
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


def test_v2_6_51_policy_exposes_generic_four_note_rotation_alignment_contract() -> None:
    metadata = dict(get_voicing_policy().metadata or {})

    assert metadata["medium_swing_four_note_rotation_alignment_version"] == "v2_6_51"
    assert metadata["medium_swing_four_note_rotation_alignment_enabled"] is True
    assert metadata["medium_swing_four_note_rotation_alignment_target"] == {
        "scope": "same_texture_scope_local_functional_pair",
        "families": ["basic_4note", "rooted_color_4note", "rootless_ab"],
        "basic_rooted_motion": "1357_to_5713__3571_to_7135__5713_to_1357__7135_to_3571",
        "rootless_motion": "flip_A_B_while_preserving_content_type_and_rootless_inversion_index",
        "mode": "strict_when_matching_candidate_available",
        "runtime_filtering_enabled": True,
        "does_not_force_content_family_change": True,
    }


def test_v2_6_51_basic_1357_seed_requests_5713_follow_inside_method_scope() -> None:
    orchestrator = RealizerVoicingRequestOrchestrator()
    resolver = SequenceResolver([
        _basic_plan("ev1", "Dm7", "drop2", inversion_index=0),
        _basic_plan("ev2", "G7", "drop2", inversion_index=2),
    ])
    orchestrator.voicing_resolver = resolver
    orchestrator.begin_realization_pass()
    policy = get_voicing_policy()

    orchestrator.resolve_event_voicing(event=_event(1, "Dm7", next_="G7"), expression=_expr("ev1"), base_policy=policy, ensemble={"bass_present": True})
    orchestrator.resolve_event_voicing(event=_event(2, "G7", previous="Dm7", next_="Cmaj7"), expression=_expr("ev2"), base_policy=policy, ensemble={"bass_present": True})

    second_meta = resolver.requests[1].policy.metadata
    assert second_meta["medium_swing_phrase_scope_method_lock_policy_applied"] is True
    assert second_meta["medium_swing_four_note_rotation_alignment_version"] == MEDIUM_SWING_FOUR_NOTE_ROTATION_ALIGNMENT_VERSION
    assert second_meta["medium_swing_four_note_rotation_alignment_policy_applied"] is True
    assert second_meta["medium_swing_four_note_rotation_alignment_previous_family"] == "basic_4note"
    assert second_meta["medium_swing_four_note_rotation_alignment_desired_family"] == "basic_4note"
    assert second_meta["medium_swing_four_note_rotation_alignment_previous_inversion_index"] == 0
    assert second_meta["medium_swing_four_note_rotation_alignment_desired_inversion_index"] == 2
    assert second_meta["medium_swing_four_note_rotation_alignment_previous_ab_side"] == "A"
    assert second_meta["medium_swing_four_note_rotation_alignment_desired_ab_side"] == "B"


def test_v2_6_51_candidate_generation_filters_basic_4note_to_generic_ab_follow_when_available() -> None:
    policy = get_voicing_policy()
    metadata = dict(policy.metadata or {})
    metadata.update(
        {
            "medium_swing_four_note_rotation_alignment_runtime_enabled": True,
            "medium_swing_four_note_rotation_alignment_policy_applied": True,
            "medium_swing_four_note_rotation_alignment_runtime_filtering_enabled": True,
            "medium_swing_four_note_rotation_alignment_desired_family": "basic_4note",
            "medium_swing_four_note_rotation_alignment_desired_ab_side": "B",
            "medium_swing_four_note_rotation_alignment_desired_content_type": "root_third_fifth_seventh",
            "medium_swing_four_note_rotation_alignment_desired_source_family": "root_third_fifth_seventh",
            "medium_swing_four_note_rotation_alignment_desired_ab_pair_index": 0,
            "medium_swing_four_note_rotation_alignment_desired_inversion_index": 2,
        }
    )
    candidates = generate_candidates("G7", replace(policy, metadata=metadata))

    assert candidates
    assert {candidate.metadata.get("four_note_rotation_family") for candidate in candidates} == {"basic_4note"}
    assert {candidate.metadata.get("four_note_rotation_ab_side") for candidate in candidates} == {"B"}
    assert {candidate.metadata.get("four_note_rotation_ab_pair_index") for candidate in candidates} == {0}
    assert {candidate.metadata.get("four_note_rotation_inversion_index") for candidate in candidates} == {2}
    assert all(candidate.metadata.get("medium_swing_four_note_rotation_alignment_filter_applied") is True for candidate in candidates)
    assert all(candidate.metadata.get("medium_swing_four_note_rotation_alignment_candidate_matches") is True for candidate in candidates)


def test_v2_6_51_piano_audit_reports_generic_four_note_rotation_alignment() -> None:
    def row(index: int, *, selected_family: str, desired_side: str, selected_side: str, desired_inversion: int, selected_inversion: int) -> dict:
        event_id = f"generic_rotation_{index}"
        metadata = {
            "disposition_projection_family": "open",
            "disposition_projection_method": "drop2",
            "four_note_rotation_family": selected_family,
            "four_note_rotation_content_type": "root_third_fifth_seventh",
            "four_note_rotation_ab_side": selected_side,
            "four_note_rotation_ab_pair_index": selected_inversion % 2,
            "four_note_rotation_inversion_index": selected_inversion,
            "medium_swing_four_note_rotation_alignment_runtime_enabled": True,
            "medium_swing_four_note_rotation_alignment_policy_applied": True,
            "medium_swing_four_note_rotation_alignment_reason": "method_locked_local_progression_follow_region_requests_generic_four_note_rotation_flip",
            "medium_swing_four_note_rotation_alignment_pair_type": "ii_v",
            "medium_swing_four_note_rotation_alignment_previous_region_id": f"r{index - 1}",
            "medium_swing_four_note_rotation_alignment_previous_family": selected_family,
            "medium_swing_four_note_rotation_alignment_desired_family": selected_family,
            "medium_swing_four_note_rotation_alignment_previous_ab_side": "A" if desired_side == "B" else "B",
            "medium_swing_four_note_rotation_alignment_desired_ab_side": desired_side,
            "medium_swing_four_note_rotation_alignment_desired_content_type": "root_third_fifth_seventh",
            "medium_swing_four_note_rotation_alignment_desired_inversion_index": desired_inversion,
            "medium_swing_four_note_rotation_alignment_filter_applied": True,
            "medium_swing_four_note_rotation_alignment_filter_reason": "filtered_to_matching_four_note_rotation",
            "medium_swing_four_note_rotation_alignment_candidate_matches": True,
            "medium_swing_four_note_rotation_alignment_selected_family": selected_family,
            "medium_swing_four_note_rotation_alignment_selected_ab_side": selected_side,
            "medium_swing_four_note_rotation_alignment_selected_content_type": "root_third_fifth_seventh",
            "medium_swing_four_note_rotation_alignment_selected_inversion_index": selected_inversion,
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
                "chord_symbol": "G7" if index == 1 else "Cmaj7",
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
                "chord_symbol": "G7",
                "midi_notes": [50, 53, 57, 60],
                "degrees": ["R", "3", "5", "7"],
                "voice_roles": ["lowest", "inner_1", "inner_2", "top"],
                "groups": {},
                "projection_map": {},
                "content_family": "seventh_chord_basic",
                "disposition": "open",
                "root_support": "root_included",
                "root_included": True,
                "density": 4,
                "functional_grouping": "2+2",
                "recipe_id": "d4__2plus2__basic_4note",
                "register_guard": {"passed": True, "reasons": ["ok"]},
                "selector_decision": {"mode": "weighted_pool", "selected_rank": 1, "selected_score": 1.0, "candidate_count": 4},
                "metadata": metadata,
            },
            "realized_notes": [
                {"note": note, "start_beat": float(index * 4), "duration_beats": 0.5, "velocity": 60, "track": "piano", "channel": 0, "timing_intent": "auto"}
                for note in [50, 53, 57, 60]
            ],
        }

    summary = build_piano_musical_audit(
        {
            "title": "Synthetic",
            "piano_musical_audit_events": [
                row(1, selected_family="basic_4note", desired_side="B", selected_side="B", desired_inversion=2, selected_inversion=2),
                row(2, selected_family="basic_4note", desired_side="A", selected_side="A", desired_inversion=0, selected_inversion=0),
            ],
        }
    ).summary

    assert summary["medium_swing_four_note_rotation_alignment_version"] == "v2_6_51"
    assert summary["medium_swing_four_note_rotation_alignment_policy_applied_events"] == 2
    assert summary["medium_swing_four_note_rotation_alignment_filter_applied_events"] == 2
    assert summary["medium_swing_four_note_rotation_alignment_candidate_match_events"] == 2
    assert summary["medium_swing_four_note_rotation_alignment_candidate_mismatch_events"] == 0
    assert summary["medium_swing_four_note_rotation_alignment_desired_families"] == {"basic_4note": 2}
    assert summary["medium_swing_four_note_rotation_alignment_desired_sides"] == {"B": 1, "A": 1}
    assert summary["medium_swing_four_note_rotation_alignment_checkpoint_passed"] is True
