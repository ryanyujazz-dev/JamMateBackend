from __future__ import annotations

import random

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.voicing import ContentFamily, VoicingRequest, VoicingResolver, generate_candidates
from jammate_engine.styles.registry import get_style


def _resolve(symbol: str, *, event_id: str = "event"):
    style = get_style("medium_swing")
    return VoicingResolver().resolve(
        VoicingRequest(
            event_id=event_id,
            chord_symbol=symbol,
            track="piano",
            gesture_type="simultaneous_onset",
            gesture=simultaneous_onset(),
            expression_articulation="short",
            ensemble_context={"bass_present": True},
            policy=style.voicing_policy,
            onset_beat=0.0,
            rng=random.Random(38),
        )
    )


def test_medium_swing_policy_exposes_small_content_bias_contract() -> None:
    policy = get_style("medium_swing").voicing_policy
    debug = policy.to_debug_dict()

    assert debug["max_density"] == 5
    assert debug["selector_temperature"] <= 0.08
    assert debug["content_family_weights"][ContentFamily.SHELL.value] < 0
    assert "#11" in debug["low_priority_degrees"]
    assert debug["metadata"]["milestone"] == "v2_1_43_closed_source_weight_finalization"


def test_medium_swing_ordinary_major_seventh_no_longer_adds_unwritten_rootless_color() -> None:
    plan = _resolve("Cmaj7")

    assert plan.content_family != ContentFamily.ROOTLESS_B.value
    assert plan.content_family != ContentFamily.ROOTLESS_A.value
    assert "#11" not in plan.degrees
    assert "9" not in plan.degrees
    assert plan.metadata["score_breakdown"]["details"]["voice_leading_profile"]["current_top_note"] == max(plan.midi_notes)


def test_medium_swing_explicit_sharp_eleven_is_still_respected() -> None:
    plan = _resolve("Cmaj7#11")

    assert "#11" in plan.degrees
    assert plan.content_family == ContentFamily.ROOTLESS_A.value


def test_medium_swing_shell_remains_available_but_default_weight_is_rare() -> None:
    policy = get_style("medium_swing").voicing_policy
    candidates = generate_candidates("G7", policy)
    shell_candidates = [candidate for candidate in candidates if candidate.content_family == ContentFamily.SHELL]
    rootless_candidates = [candidate for candidate in candidates if candidate.content_family == ContentFamily.ROOTLESS_A]

    assert shell_candidates
    assert not rootless_candidates
