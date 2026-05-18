from __future__ import annotations

import pytest

from jammate_engine.core.gestures import GestureKind, GestureRequest
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime import PatternCandidate, event_spec
from jammate_engine.styles.jazz_ballad import gesture_policy
from jammate_engine.styles.registry import get_style


def test_v2_5_4_ballad_gesture_policy_allows_inner_movement_and_rolled_onset_only_as_contract() -> None:
    policy = gesture_policy.get_gesture_policy()

    assert policy["version"] in {"v2_5_4", "v2_5_4"}
    assert policy["default_onset_mode"] == "simultaneous_onset"
    assert set(policy["allowed_gesture_kinds"]) == {
        "simultaneous_onset",
        "inner_movement",
        "rolled_onset",
    }
    assert "arpeggiated_onset" not in policy["allowed_gesture_kinds"]
    assert policy["boundary"] == "gesture_policy_is_pitchless_projection_and_motion_intent_only"
    assert policy["v2_5_4_contract"]["voicing_boundary"] == "voicing_remains_the_only_vertical_pitch_selector"


def test_v2_5_4_ballad_inner_movement_request_is_pitchless_and_projection_scoped() -> None:
    request = gesture_policy.inner_movement_request(motion_shape="inner_resolution", target_voice_class="inner")

    assert request.kind == GestureKind.INNER_MOVEMENT
    assert request.projection_refs == ("inner",)
    assert request.metadata["gesture_family"] == "ballad_inner_movement"
    assert request.metadata["motion_shape"] == "inner_resolution"
    assert request.metadata["held_voice_policy"] == "hold_foundation_common_tones"
    assert "midi_note" not in request.metadata
    assert "velocity" not in request.metadata
    assert "duration_beats" not in request.metadata
    assert "voicing_texture" not in request.metadata


def test_v2_5_4_ballad_rolled_cadence_request_uses_functional_projection_refs() -> None:
    request = gesture_policy.rolled_cadence_request(
        voice_order=("group_ref:foundation_group", "group_ref:projection_group"),
        onset_offsets_beats=(0.0, 0.04),
    )

    assert request.kind == GestureKind.ROLLED_ONSET
    assert request.projection_refs == ("foundation_group", "projection_group")
    assert request.onset_offsets_beats == (0.0, 0.04)
    assert request.metadata["roll_shape"] == "low_to_high_cadence_roll"


def test_v2_5_4_ballad_gesture_validator_rejects_v1_texture_or_concrete_metadata() -> None:
    with pytest.raises(ValueError, match="voicingless"):
        gesture_policy.validate_gesture_request(
            GestureRequest(
                kind=GestureKind.INNER_MOVEMENT,
                voice_order=("inner",),
                metadata={"motion_shape": "inner_resolution", "voicing_texture": "rootless5"},
            )
        )

    with pytest.raises(ValueError):
        GestureRequest(kind=GestureKind.INNER_MOVEMENT, metadata={"midi_note": 60})

    with pytest.raises(ValueError, match="not style-approved"):
        gesture_policy.validate_gesture_request(
            GestureRequest(kind=GestureKind.ARPEGGIATED_ONSET, voice_order=("inner",), metadata={"motion_shape": "run"})
        )

    with pytest.raises(ValueError, match="unknown keys"):
        gesture_policy.validate_gesture_request(
            GestureRequest(kind=GestureKind.INNER_MOVEMENT, voice_order=("inner",), metadata={"legacy_slot": "INNER_DYAD"})
        )


def test_v2_5_4_pattern_event_can_carry_ballad_gesture_request_without_selecting_notes() -> None:
    request = gesture_policy.inner_movement_request(motion_shape="inner_voice_breath", target_voice_class="color_group")
    candidate = PatternCandidate(
        name="ballad_future_inner_motion_slot",
        weight=1.0,
        category="future_phrase_contract",
        events=(
            event_spec(track="piano", beat=2.0, role="harmonic_motion", gesture=request, expression_hint="soft_answer"),
        ),
        metadata={"future_phrase_contract": "gesture_slot_only_no_notes"},
    )
    plan = candidate.instantiate(
        HarmonicRegion(
            region_id="r_ballad_gesture_contract",
            chord_symbol="Dm7",
            next_chord_symbol="G7",
            chorus_index=0,
            bar_index=0,
            chord_index=0,
            start_beat=8.0,
            duration_beats=4.0,
        )
    )
    event = plan.events[0]

    assert event.gesture.kind == GestureKind.INNER_MOVEMENT
    assert event.gesture.projection_refs == ("color_group",)
    assert event.gesture_type == "inner_movement"
    assert event.onset_beat == 10.0
    assert not hasattr(event, "midi_note")
    assert "notes" not in event.metadata
    assert plan.metadata["future_phrase_contract"] == "gesture_slot_only_no_notes"


def test_v2_5_4_default_ballad_runtime_selection_remains_audibly_unchanged_until_phrase_pass() -> None:
    style = get_style("jazz_ballad")
    region = HarmonicRegion(
        region_id="r_ballad_default_v252",
        chord_symbol="Cmaj7",
        next_chord_symbol="Fmaj7",
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=0.0,
        duration_beats=4.0,
    )

    plan = style.plan_region(region, context={})
    assert plan.selected_candidate == "ballad_piano_soft_downbeat_sustain + ballad_bass_root_anchor"
    piano_events = [event for event in plan.events if event.track == "piano"]
    assert [event.gesture_type for event in piano_events] == ["simultaneous_onset"]
