from __future__ import annotations

from jammate_engine.core.expression.expression_plan import EventExpression, ExpressionPlan
from jammate_engine.core.gestures import GESTURE_PROJECTION_CONTRACT_VERSION, GESTURE_PROJECTION_KEYS, arpeggiated_onset, rolled_onset
from jammate_engine.core.pattern_runtime import PatternCandidate, event_spec
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.voicing.runtime.plan import VoicedNote, VoicingPlan
from jammate_engine.realization.gesture_realizer import GestureRealizer
from jammate_engine.realization.harmonic_realizer import HarmonicRealizer


class StaticVoicingResolver:
    def __init__(self, plan: VoicingPlan) -> None:
        self.plan = plan
        self.calls = 0

    def resolve(self, request):  # noqa: ANN001 - test double mirrors runtime protocol
        self.calls += 1
        return self.plan


def _event(gesture) -> object:
    return PatternCandidate(
        name="projection_ref_demo",
        weight=1.0,
        category="test",
        events=(
            event_spec(
                track="piano",
                beat=0.0,
                role="harmonic",
                gesture=gesture,
            ),
        ),
    ).instantiate(
        HarmonicRegion(
            region_id="r_v2_0_40",
            chord_symbol="G13",
            next_chord_symbol="Cmaj7",
            chorus_index=0,
            bar_index=0,
            chord_index=0,
            start_beat=4.0,
            duration_beats=4.0,
        )
    ).events[0]


def _voicing_plan() -> VoicingPlan:
    return VoicingPlan(
        event_id="selected_voicing",
        chord_symbol="G13",
        notes=[
            VoicedNote(midi_note=53, degree="b7", voice_role="lowest", group_id="support_group"),
            VoicedNote(midi_note=59, degree="3", voice_role="inner_1", group_id="support_group"),
            VoicedNote(midi_note=64, degree="13", voice_role="inner_2", group_id="projection_group"),
            VoicedNote(midi_note=69, degree="9", voice_role="top", group_id="projection_group"),
        ],
        projection_map={
            "all_voices": [0, 1, 2, 3],
            "lowest": [0],
            "inner": [1, 2],
            "inner_1": [1],
            "inner_2": [2],
            "top": [3],
            "support_group": [0, 1],
            "projection_group": [2, 3],
        },
        groups={"support_group": [0, 1], "projection_group": [2, 3]},
    )


def test_gesture_projection_contract_exports_group_refs() -> None:
    assert GESTURE_PROJECTION_CONTRACT_VERSION == "v2_0_40"
    assert "support_group" in GESTURE_PROJECTION_KEYS
    assert "projection_group" in GESTURE_PROJECTION_KEYS


def test_gesture_realizer_consumes_voicing_projection_group_refs() -> None:
    event = _event(
        arpeggiated_onset(
            voice_order=("group_ref:projection_group", "group_ref:support_group"),
            onset_offsets_beats=(0.0, 0.25, 0.5, 0.75),
        )
    )
    expr = EventExpression(
        event_id=event.event_id,
        duration_beats=2.0,
        velocity=70,
        articulation="sustain",
        pedal="none",
    )

    notes = GestureRealizer().realize_harmonic_event(event, _voicing_plan(), expr)

    assert [note.note for note in notes] == [64, 69, 53, 59]
    assert [note.projection_ref for note in notes] == [
        "projection_group",
        "projection_group",
        "support_group",
        "support_group",
    ]
    assert [note.group_id for note in notes] == [
        "projection_group",
        "projection_group",
        "support_group",
        "support_group",
    ]
    assert [note.voice_role for note in notes] == ["inner_2", "top", "lowest", "inner_1"]
    assert all(note.voicing_event_id == "selected_voicing" for note in notes)


def test_gesture_realizer_keeps_positional_voice_ref_compatibility() -> None:
    event = _event(
        rolled_onset(
            voice_order=("voice_ref:lowest", "voice_ref:top", "voice_ref:inner_1"),
            onset_offsets_beats=(0.0, 0.1, 0.2, 0.3),
        )
    )
    expr = EventExpression(
        event_id=event.event_id,
        duration_beats=1.0,
        velocity=64,
        articulation="short",
        pedal="none",
    )

    notes = GestureRealizer().realize_harmonic_event(event, _voicing_plan(), expr)

    assert [note.note for note in notes] == [53, 69, 59, 64]
    assert [note.projection_ref for note in notes] == ["lowest", "top", "inner_1", "all_voices"]
    assert [note.start_beat for note in notes] == [4.0, 4.1, 4.2, 4.3]


def test_harmonic_realizer_projects_static_voicing_without_reselecting_notes() -> None:
    event = _event(
        arpeggiated_onset(
            voice_order=("support_group", "projection_group"),
            onset_offsets_beats=(0.0, 0.25, 0.5, 0.75),
        )
    )
    expression = ExpressionPlan(
        events={
            event.event_id: EventExpression(
                event_id=event.event_id,
                duration_beats=2.0,
                velocity=72,
                articulation="sustain",
                pedal="none",
            )
        }
    )
    static_resolver = StaticVoicingResolver(_voicing_plan())
    realizer = HarmonicRealizer()
    realizer.voicing_resolver = static_resolver

    notes = realizer.realize(
        [event],
        expression=expression,
        style_voicing_policy=None,
        ensemble={"bass_present": True},
    )

    assert static_resolver.calls == 1
    assert [note.note for note in notes] == [53, 59, 64, 69]
    assert [note.projection_ref for note in notes] == [
        "support_group",
        "support_group",
        "projection_group",
        "projection_group",
    ]
