from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.core.expression.expression_plan import EventExpression
from jammate_engine.core.gestures.gesture import simultaneous_onset
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing.runtime.plan import VoicedNote, VoicingPlan
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.realization.realizer_voicing_request_orchestration import (
    RealizerVoicingRequestOrchestrator,
    base_voicing_policy_from_style_input,
    deliberate_revoice_request_from_event,
    event_requests_fresh_voicing,
)
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
LEADSHEETS = ROOT / "examples" / "leadsheets"
DOC = ROOT / "docs" / "ENGINE_VOICING_MEDIUM_SWING_OPEN_DROP_DELIBERATE_REVOICE_GESTURE_BOUNDARY_PLAN_V2_6_54.md"


def _generate(slug: str, *, tmp_path: Path, seed: int):
    score = json.loads((LEADSHEETS / f"{slug}.json").read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": int(score.get("tempo", 132)),
            "choruses": 3,
            "seed": seed,
            "output_path": str(tmp_path / f"{slug}_v2_6_54.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return build_piano_musical_audit(result.debug)


def _event(event_id: str, *, metadata: dict | None = None, gesture_metadata: dict | None = None) -> PatternEvent:
    return PatternEvent(
        event_id=event_id,
        track="piano",
        region_id="r1",
        chord_symbol="Cmaj7",
        onset_beat=0.0,
        local_beat=1.0,
        role="comping",
        gesture=simultaneous_onset(metadata=gesture_metadata),
        metadata=metadata or {},
    )


def _expr(event_id: str) -> EventExpression:
    return EventExpression(event_id=event_id, duration_beats=1.0, velocity=64, articulation="sustain", pedal="none")


class ChangingResolver:
    def __init__(self) -> None:
        self.calls = 0

    def resolve(self, request):  # noqa: ANN001 - test double mirrors runtime protocol
        self.calls += 1
        base = 60 if self.calls == 1 else 62
        return VoicingPlan(
            event_id=request.event_id,
            chord_symbol=request.chord_symbol,
            notes=[
                VoicedNote(midi_note=base, degree="1", voice_role="lowest"),
                VoicedNote(midi_note=base + 4, degree="3", voice_role="inner_1"),
                VoicedNote(midi_note=base + 7, degree="5", voice_role="inner_2"),
                VoicedNote(midi_note=base + 11, degree="7", voice_role="top"),
            ],
            metadata={"disposition_projection_family": "open", "disposition_projection_method": "drop2"},
        )


def test_v2_6_54_policy_declares_deliberate_revoice_boundary() -> None:
    metadata = dict(get_voicing_policy().metadata or {})
    target = dict(metadata.get("medium_swing_deliberate_revoice_gesture_boundary_target") or {})

    assert metadata["medium_swing_deliberate_revoice_gesture_boundary_version"] == "v2_6_54"
    assert metadata["medium_swing_deliberate_revoice_gesture_boundary_enabled"] is True
    assert target["scope"] == "same_chord_region_explicit_gesture_intent"
    assert target["default_behavior"] == "reuse_cached_region_voicing_exactly"
    assert target["allowed_escape_hatches"] == ["force_fresh_voicing", "revoice_within_region"]
    assert target["allowed_intent_sources"] == ["event_metadata", "gesture_metadata"]
    assert target["implicit_revoicing_events"] == 0
    assert target["warning_events"] == 0
    assert target["does_not_change_pattern_anticipation_expression_or_midi"] is True


def test_v2_6_54_explicit_gesture_escape_hatch_bypasses_cache_and_is_marked() -> None:
    policy = base_voicing_policy_from_style_input(get_voicing_policy())
    orchestrator = RealizerVoicingRequestOrchestrator()
    resolver = ChangingResolver()
    orchestrator.voicing_resolver = resolver
    orchestrator.begin_realization_pass()

    first = _event("ev1")
    second = _event("ev2", gesture_metadata={"revoice_within_region": True, "gesture_reason": "deliberate_inner_motion"})

    request = deliberate_revoice_request_from_event(second)
    assert request["requested"] is True
    assert request["source"] == "gesture_metadata"
    assert request["escape_hatch"] == "revoice_within_region"
    assert event_requests_fresh_voicing(second) is True

    first_plan = orchestrator.resolve_event_voicing(event=first, expression=_expr("ev1"), base_policy=policy, ensemble={"bass_present": True})
    second_plan = orchestrator.resolve_event_voicing(event=second, expression=_expr("ev2"), base_policy=policy, ensemble={"bass_present": True})

    assert resolver.calls == 2
    assert first_plan.midi_notes == [60, 64, 67, 71]
    assert second_plan.midi_notes == [62, 66, 69, 73]
    assert second_plan.metadata["medium_swing_deliberate_revoice_gesture_boundary_version"] == "v2_6_54"
    assert second_plan.metadata["medium_swing_deliberate_revoice_gesture_boundary_applied"] is True
    assert second_plan.metadata["medium_swing_deliberate_revoice_gesture_boundary_escape_hatch"] == "revoice_within_region"
    assert second_plan.metadata["medium_swing_deliberate_revoice_gesture_boundary_source"] == "gesture_metadata"
    assert second_plan.metadata["medium_swing_deliberate_revoice_gesture_boundary_previous_event_id"] == "ev1"
    assert second_plan.metadata["medium_swing_deliberate_revoice_gesture_boundary_changed_notes"] is True
    assert second_plan.metadata["same_chord_reattack_explicit_fresh_revoicing"] is True
    assert second_plan.metadata["same_chord_reattack_continuity_region_cache_reuse"] is False


def test_v2_6_54_all_the_things_you_are_default_has_no_deliberate_or_implicit_revoices(tmp_path: Path) -> None:
    audit = _generate("all_the_things_you_are", tmp_path=tmp_path, seed=3300)
    summary = audit.summary

    assert summary["medium_swing_deliberate_revoice_gesture_boundary_version"] == "v2_6_54"
    default_reuse_events = summary["medium_swing_deliberate_revoice_gesture_boundary_default_reuse_events"]
    assert default_reuse_events >= 54
    assert summary["medium_swing_deliberate_revoice_gesture_boundary_explicit_revoice_events"] == 0
    assert summary["medium_swing_deliberate_revoice_gesture_boundary_implicit_revoice_events"] == 0
    assert summary["medium_swing_deliberate_revoice_gesture_boundary_warning_events"] == 0
    assert summary["medium_swing_deliberate_revoice_gesture_boundary_checkpoint_passed"] is True
    assert summary["medium_swing_same_chord_reattack_comping_reuse_region_voicing_reused_events"] == default_reuse_events


def test_v2_6_54_autumn_leaves_default_has_no_deliberate_or_implicit_revoices(tmp_path: Path) -> None:
    audit = _generate("autumn_leaves", tmp_path=tmp_path, seed=3301)
    summary = audit.summary

    assert summary["medium_swing_deliberate_revoice_gesture_boundary_version"] == "v2_6_54"
    default_reuse_events = summary["medium_swing_deliberate_revoice_gesture_boundary_default_reuse_events"]
    assert default_reuse_events >= 60
    assert summary["medium_swing_deliberate_revoice_gesture_boundary_explicit_revoice_events"] == 0
    assert summary["medium_swing_deliberate_revoice_gesture_boundary_implicit_revoice_events"] == 0
    assert summary["medium_swing_deliberate_revoice_gesture_boundary_warning_events"] == 0
    assert summary["medium_swing_deliberate_revoice_gesture_boundary_checkpoint_passed"] is True
    assert summary["medium_swing_same_chord_reattack_comping_reuse_region_voicing_reused_events"] == default_reuse_events


def test_v2_6_54_doc_records_deliberate_revoice_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_54",
        "Deliberate Revoice Gesture Boundary",
        "reuse_cached_region_voicing_exactly",
        "force_fresh_voicing",
        "revoice_within_region",
        "same_chord_region_explicit_gesture_intent",
        "implicit revoicing events: 0",
        "All The Things You Are",
        "Autumn Leaves",
        "Pattern",
        "Anticipation",
        "Expression",
        "MIDI",
        "Agent",
        "HarmonyOS",
    ):
        assert token in text
