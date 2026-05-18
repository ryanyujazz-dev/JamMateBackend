from __future__ import annotations

from jammate_engine.core.expression.expression_plan import EventExpression, ExpressionPlan
from jammate_engine.core.expression.expression_resolver import ExpressionResolver
from jammate_engine.core.gestures import GestureKind, simultaneous_onset
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime import PatternCandidate, event_spec
from jammate_engine.core.voicing.runtime.plan import VoicedNote, VoicingPlan
from jammate_engine.realization.gesture_realizer import GestureRealizer
from jammate_engine.realization.harmonic_realizer import HarmonicRealizer
from jammate_engine.styles.jazz_ballad.expression_policy import get_expression_policy
from jammate_engine.styles.jazz_ballad.gesture_policy import inner_movement_request


class StaticVoicingResolver:
    def __init__(self, plan: VoicingPlan) -> None:
        self.plan = plan
        self.calls = 0

    def resolve(self, request):  # noqa: ANN001 - test double mirrors runtime protocol
        self.calls += 1
        return self.plan


def _ballad_region() -> HarmonicRegion:
    return HarmonicRegion(
        region_id="r_v2_5_4_ballad_partial",
        chord_symbol="Cmaj9",
        next_chord_symbol="Fmaj7",
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=0.0,
        duration_beats=4.0,
        metadata={"home_key": "C"},
    )


def _inner_motion_candidate(projection_ref: str = "inner_1") -> PatternCandidate:
    return PatternCandidate(
        name="v2_5_4_partial_reattack_demo",
        weight=1.0,
        category="test_partial_reattack",
        events=(
            event_spec(
                track="piano",
                beat=0.0,
                role="harmonic",
                gesture=simultaneous_onset(),
                expression_hint="soft_sustain",
            ),
            event_spec(
                track="piano",
                beat=2.5,
                role="harmonic_motion",
                gesture=inner_movement_request(target_voice_class=projection_ref),
                expression_hint="soft_answer",
            ),
        ),
    )


def _voicing_plan() -> VoicingPlan:
    return VoicingPlan(
        event_id="selected_voicing_v254",
        chord_symbol="Cmaj9",
        notes=[
            VoicedNote(midi_note=52, degree="3", voice_role="lowest", group_id="support_group"),
            VoicedNote(midi_note=59, degree="7", voice_role="inner_1", group_id="support_group"),
            VoicedNote(midi_note=62, degree="9", voice_role="inner_2", group_id="color_group"),
            VoicedNote(midi_note=67, degree="5", voice_role="top", group_id="color_group"),
        ],
        projection_map={
            "all_voices": [0, 1, 2, 3],
            "lowest": [0],
            "inner": [1, 2],
            "inner_1": [1],
            "inner_2": [2],
            "top": [3],
            "support_group": [0, 1],
            "color_group": [2, 3],
            "projection_group": [2, 3],
        },
        groups={"support_group": [0, 1], "color_group": [2, 3], "projection_group": [2, 3]},
    )


def test_v2_5_4_inner_movement_projects_only_requested_motion_voice_not_full_voicing() -> None:
    event = _inner_motion_candidate("inner_1").instantiate(_ballad_region()).events[1]
    expression = EventExpression(
        event_id=event.event_id,
        duration_beats=1.0,
        velocity=42,
        articulation="sustain",
        pedal="light",
    )

    notes = GestureRealizer().realize_harmonic_event(event, _voicing_plan(), expression)

    assert event.gesture.kind == GestureKind.INNER_MOVEMENT
    assert [note.note for note in notes] == [59]
    assert [note.projection_ref for note in notes] == ["inner_1"]
    assert all(note.projection_ref != "all_voices" for note in notes)


def test_v2_5_4_expression_does_not_cut_anchor_for_later_inner_movement() -> None:
    plan = _inner_motion_candidate("inner_1").instantiate(_ballad_region())
    expression = ExpressionResolver().resolve(plan.events, get_expression_policy())

    anchor = expression.events[plan.events[0].event_id]
    motion = expression.events[plan.events[1].event_id]

    assert anchor.profile_name == "soft_sustain"
    assert anchor.duration_beats == 3.5
    assert anchor.metadata["duration_next_event_clamp_applied"] is False
    assert motion.profile_name == "soft_answer"
    assert motion.duration_beats == 1.05


def test_v2_5_4_harmonic_realizer_holds_foundation_and_releases_only_reattacked_voice() -> None:
    plan = _inner_motion_candidate("inner_1").instantiate(_ballad_region())
    expression = ExpressionResolver().resolve(plan.events, get_expression_policy())
    realizer = HarmonicRealizer()
    realizer.voicing_resolver = StaticVoicingResolver(_voicing_plan())

    notes = realizer.realize(
        list(plan.events),
        expression=expression,
        style_voicing_policy=None,
        ensemble={"bass_present": True},
    )

    anchor_notes = [note for note in notes if note.expression_event_id == plan.events[0].event_id]
    motion_notes = [note for note in notes if note.expression_event_id == plan.events[1].event_id]

    assert [note.note for note in motion_notes] == [59]
    durations_by_pitch = {note.note: note.duration_beats for note in anchor_notes}
    assert durations_by_pitch[59] == 2.5
    assert durations_by_pitch[52] == 3.5
    assert durations_by_pitch[62] == 3.5
    assert durations_by_pitch[67] == 3.5
    trimmed = next(note for note in anchor_notes if note.note == 59)
    assert trimmed.pedal_debug["partial_reattack_release_version"] == "v2_5_4"
    assert trimmed.pedal_debug["partial_reattack_release_applied"] is True


def test_v2_5_4_color_group_inner_movement_uses_projection_group_without_texture_binding() -> None:
    event = _inner_motion_candidate("color_group").instantiate(_ballad_region()).events[1]
    expression = EventExpression(
        event_id=event.event_id,
        duration_beats=1.0,
        velocity=42,
        articulation="sustain",
        pedal="light",
    )

    notes = GestureRealizer().realize_harmonic_event(event, _voicing_plan(), expression)

    assert [note.note for note in notes] == [62, 67]
    assert [note.group_id for note in notes] == ["color_group", "color_group"]
    assert [note.projection_ref for note in notes] == ["color_group", "color_group"]
