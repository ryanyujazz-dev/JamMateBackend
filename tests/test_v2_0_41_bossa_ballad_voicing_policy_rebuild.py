from __future__ import annotations

import random

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.voicing import ContentFamily, Disposition, VoicingRequest, VoicingResolver
from jammate_engine.core.voicing.sources.chord_tone_resolver import content_degree_names
from jammate_engine.styles.bossa_nova.voicing_policy import get_voicing_policy as get_bossa_policy
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy as get_ballad_policy
from jammate_engine.styles.registry import get_style


def _resolve(style_name: str, symbol: str):
    style = get_style(style_name)
    return VoicingResolver().resolve(
        VoicingRequest(
            event_id=f"{style_name}:{symbol}",
            chord_symbol=symbol,
            track="piano",
            gesture_type="simultaneous_onset",
            gesture=simultaneous_onset(),
            expression_articulation="short",
            ensemble_context={"bass_present": True},
            policy=style.voicing_policy,
            onset_beat=0.0,
            rng=random.Random(41),
        )
    )


def test_bossa_policy_is_light_compact_and_avoids_six_note_default() -> None:
    policy = get_bossa_policy()
    debug = policy.to_debug_dict()

    assert policy.preferred_content == ContentFamily.ROOTLESS_A
    assert ContentFamily.ROOTLESS_A in policy.allowed_content
    assert ContentFamily.ROOTLESS_B in policy.allowed_content
    assert ContentFamily.SEVENTH_BASIC in policy.allowed_content
    assert ContentFamily.SHELL not in policy.allowed_content
    assert policy.preferred_disposition == Disposition.CLOSED
    assert policy.preferred_density == 4
    assert policy.max_density == 5
    assert "#11" in policy.low_priority_degrees
    assert debug["metadata"]["density_rule"] == "default_4_rich_5_avoid_6_plus"


def test_bossa_representative_plain_seventh_chords_no_longer_force_rootless_color() -> None:
    dm = _resolve("bossa_nova", "Dm7")
    g = _resolve("bossa_nova", "G7")
    c = _resolve("bossa_nova", "Cmaj7")

    assert dm.content_family != ContentFamily.ROOTLESS_A.value
    assert g.content_family != ContentFamily.ROOTLESS_A.value
    assert c.content_family != ContentFamily.ROOTLESS_B.value
    assert len(dm.notes) == len(g.notes) == len(c.notes) == 4
    assert dm.root_included
    assert g.root_included
    assert c.root_included
    assert "#11" not in c.degrees
    assert c.register_guard["passed"] is True


def test_bossa_explicit_sharp_eleven_is_still_respected() -> None:
    plan = _resolve("bossa_nova", "Cmaj7#11")

    assert plan.content_family == ContentFamily.ROOTLESS_A.value
    assert "#11" in plan.degrees
    assert plan.register_guard["passed"] is True


def test_ballad_policy_is_warm_rich_but_controlled() -> None:
    policy = get_ballad_policy()
    debug = policy.to_debug_dict()

    assert policy.preferred_content == ContentFamily.ROOTED_COLOR
    assert ContentFamily.ROOTLESS_A in policy.allowed_content
    assert ContentFamily.ROOTLESS_B in policy.allowed_content
    assert policy.preferred_disposition == Disposition.SPREAD
    assert Disposition.TWO_HAND_SPREAD in policy.allowed_dispositions
    assert policy.preferred_density == 5
    assert policy.min_density == 4
    assert policy.max_density == 6
    assert debug["metadata"]["density_rule"] == "default_4_5_common_5_rich_6_special_7_future_only"


def test_ballad_representative_chords_use_rich_rooted_color() -> None:
    dm = _resolve("jazz_ballad", "Dm7")
    g = _resolve("jazz_ballad", "G7")
    c = _resolve("jazz_ballad", "Cmaj7")

    for plan in (dm, g, c):
        assert plan.content_family == ContentFamily.ROOTED_COLOR.value
        assert plan.root_included
        assert len(plan.notes) in {4, 5, 6}
        assert plan.register_guard["passed"] is True
        assert plan.disposition in {Disposition.SPREAD.value, Disposition.TWO_HAND_SPREAD.value, Disposition.OPEN.value}


def test_ballad_half_diminished_rooted_color_keeps_flat_five_identity() -> None:
    assert "b5" in content_degree_names("Bø7", ContentFamily.ROOTED_COLOR)

    plan = _resolve("jazz_ballad", "Bø7")
    assert plan.content_family == ContentFamily.ROOTED_COLOR.value
    assert "b5" in plan.degrees
    assert "half_diminished_b5_retained" in plan.metadata["content_recipe"]["validity_notes"]
