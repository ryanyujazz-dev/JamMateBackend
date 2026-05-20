from __future__ import annotations

import pytest

from jammate_engine.core.pattern_runtime import PATTERN_RUNTIME_CONTRACT_VERSION, PatternCandidate, event_spec
from jammate_engine.styles.registry import get_style
from jammate_engine.styles.medium_swing import comping_patterns as medium_swing_comping
from jammate_engine.styles.bossa_nova import comping_patterns as bossa_comping
from jammate_engine.styles.jazz_ballad import comping_patterns as ballad_comping


COMPING_MODULES = (medium_swing_comping, bossa_comping, ballad_comping)


def test_pattern_runtime_exposes_v2_0_42_pitchless_contract() -> None:
    assert PATTERN_RUNTIME_CONTRACT_VERSION == "v2_0_42"
    with pytest.raises(ValueError, match="forbidden concrete keys"):
        event_spec(track="piano", beat=0.0, role="harmonic", metadata={"midi_note": 60})
    with pytest.raises(ValueError, match="forbidden concrete keys"):
        event_spec(track="piano", beat=0.0, role="harmonic", metadata={"nested": {"velocity": 90}})


def test_comping_libraries_are_describable_and_pitchless() -> None:
    for module in COMPING_MODULES:
        description = module.describe_pattern_library({})
        assert description["version"] in {"v2_0_42", "v2_5_0", "v2_5_4", "v2_5_5", "v2_5_7", "v2_5_9", "v2_6_56"}
        assert description["domain"] == "comping"
        assert description["track_role"] == "piano_harmonic_comping"
        assert "no_voicing_logic" in description["boundary_notes"]
        assert description["candidate_count"] == len(module.get_pattern_candidates({}))

        for candidate in module.get_pattern_candidates({}):
            assert isinstance(candidate, PatternCandidate)
            assert candidate.metadata["pattern_domain"] == "comping"
            assert candidate.metadata["track_role"] == "piano_harmonic_comping"
            assert candidate.metadata["voicing_boundary"] == "pattern_is_pitchless"
            assert candidate.metadata["pattern_library_version"] == description["version"]
            debug = candidate.to_debug_dict()
            assert debug["rhythm_beats"] == list(candidate.rhythm_beats)
            for event in debug["events"]:
                assert "midi_note" not in event["metadata"]
                assert "velocity" not in event["metadata"]
                assert "duration_beats" not in event["metadata"]


def test_medium_swing_two_beat_comping_keeps_region_shape_metadata() -> None:
    candidates = medium_swing_comping.get_pattern_candidates({"region_duration_beats": 2.0})
    assert candidates
    assert {candidate.metadata["region_shape"] for candidate in candidates} == {"two_beat_region"}
    assert all(max(candidate.rhythm_beats) < 2.0 for candidate in candidates)


def test_style_profiles_expose_pitchless_gesture_policy_without_runtime_retune() -> None:
    for style_name in ("medium_swing", "bossa_nova", "jazz_ballad"):
        style = get_style(style_name)
        policy = style.gesture_policy
        assert policy["version"] in {"v2_0_42", "v2_5_4", "v2_5_5", "v2_5_7", "v2_5_9"}
        assert policy["default_onset_mode"] == "simultaneous_onset"
        assert policy["boundary"] in {"gesture_policy_is_pitchless_and_projection_only", "gesture_policy_is_pitchless_projection_and_motion_intent_only"}
        assert "simultaneous_onset" in policy["allowed_gesture_kinds"]
        assert "top" in policy["allowed_projection_refs"]
