from __future__ import annotations

from jammate_engine.midi.render_pipeline import (
    TIMING_CONTRACT_VERSION,
    TimingPolicy,
    apply_timing_policy,
    describe_timing_policy,
    performed_beat,
)
from jammate_engine.realization.note_event_builder import NoteEvent
from jammate_engine.styles.bossa_nova.profile import BossaNovaProfile
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile
from jammate_engine.styles.medium_swing.profile import MediumSwingProfile


def _note(**overrides) -> NoteEvent:
    data = {
        "track": "piano",
        "channel": 0,
        "note": 60,
        "velocity": 64,
        "start_beat": 0.5,
        "duration_beats": 0.25,
    }
    data.update(overrides)
    return NoteEvent(**data)


def test_timing_contract_exposes_normalized_style_policies() -> None:
    assert TIMING_CONTRACT_VERSION == "v2_0_43"
    for profile in (MediumSwingProfile(), BossaNovaProfile(), JazzBalladProfile()):
        debug = describe_timing_policy(profile.timing_policy)
        assert debug["version"] == "v2_0_43"
        assert debug["boundary"] == "timing_policy_only_no_pattern_voicing_expression_content"
        assert "humanization" in debug
        assert debug["humanization"]["enabled"] is False


def test_medium_swing_keeps_existing_swing_grid_behavior() -> None:
    policy = MediumSwingProfile().timing_policy
    assert performed_beat(0.5, "auto", policy) == 2.0 / 3.0
    assert performed_beat(2.5, "swing_upbeat", policy) == 2.0 + 2.0 / 3.0
    assert performed_beat(0.5, "straight_even", policy) == 0.5
    assert performed_beat(0.5, "literal", policy) == 0.5


def test_apply_timing_policy_adds_diagnostic_metadata_without_changing_duration() -> None:
    event = _note(start_beat=0.5, duration_beats=0.4)
    [performed] = apply_timing_policy([event], MediumSwingProfile().timing_policy)
    assert event.start_beat == 0.5
    assert abs(performed.start_beat - (2.0 / 3.0)) < 1e-9
    assert performed.duration_beats == 0.4
    assert performed.logical_start_beat == 0.5
    assert abs(performed.timing_grid_offset_beats - (1.0 / 6.0)) < 1e-9
    assert performed.humanization_offset_beats == 0.0
    assert performed.timing_policy_version == "v2_0_43"
    assert performed.timing_debug["feel"] == "swing"


def test_humanization_policy_is_deterministic_and_track_scoped() -> None:
    policy = {
        "version": "v2_0_43",
        "feel": "straight",
        "humanization": {
            "enabled": True,
            "max_offset_beats": 0.01,
            "velocity_jitter": 3,
            "seed": 123,
            "affect_tracks": ["piano"],
            "profile_name": "test_microtiming",
        },
    }
    piano = _note(track="piano", start_beat=1.0, velocity=70)
    bass = _note(track="bass", channel=1, start_beat=1.0, velocity=70)
    first = apply_timing_policy([piano, bass], policy)
    second = apply_timing_policy([piano, bass], policy)

    assert first == second
    assert abs(first[0].humanization_offset_beats) <= 0.01
    assert 67 <= first[0].velocity <= 73
    assert first[0].timing_debug["humanization_profile"] == "test_microtiming"
    assert first[1].start_beat == 1.0
    assert first[1].velocity == 70
    assert first[1].humanization_offset_beats == 0.0


def test_timing_policy_accepts_dataclass_and_legacy_dict() -> None:
    policy = TimingPolicy.from_mapping({"feel": "swing", "swing_ratio": 0.625})
    assert performed_beat(0.5, "auto", policy) == 0.625
    assert describe_timing_policy({"feel": "straight"})["feel"] == "straight"
