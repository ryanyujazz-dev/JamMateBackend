from __future__ import annotations

import random

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.voicing import ContentFamily, VoicingRequest, VoicingResolver
from jammate_engine.core.voicing.sources.content_planner import choose_content_families, plan_content_recipes
from jammate_engine.styles.bossa_nova.voicing_policy import get_voicing_policy as get_bossa_policy
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as get_swing_policy
from jammate_engine.styles.registry import get_style


def _resolve_medium_swing(symbol: str):
    style = get_style("medium_swing")
    return VoicingResolver().resolve(
        VoicingRequest(
            event_id="event",
            chord_symbol=symbol,
            track="piano",
            gesture_type="simultaneous_onset",
            gesture=simultaneous_onset(),
            expression_articulation="short",
            ensemble_context={"bass_present": True},
            policy=style.voicing_policy,
            onset_beat=0.0,
            rng=random.Random(39),
        )
    )


def test_plain_triad_does_not_use_fake_rootless_content_family() -> None:
    policy = get_swing_policy()

    assert choose_content_families("C", policy) == [ContentFamily.MAJOR_TRIAD]
    assert choose_content_families("Cm", policy) == [ContentFamily.MINOR_TRIAD]

    c_plan = _resolve_medium_swing("C")
    cm_plan = _resolve_medium_swing("Cm")
    assert c_plan.content_family == ContentFamily.MAJOR_TRIAD.value
    assert cm_plan.content_family == ContentFamily.MINOR_TRIAD.value
    assert c_plan.root_included
    assert cm_plan.root_included


def test_half_diminished_plain_symbol_does_not_open_rootless_color_gate() -> None:
    policy = get_swing_policy()
    recipes = {recipe.family: recipe for recipe in plan_content_recipes("Bø7", policy)}

    assert ContentFamily.ROOTLESS_A not in recipes
    assert ContentFamily.ROOTLESS_B not in recipes
    assert "b5" in recipes[ContentFamily.SEVENTH_BASIC].degree_names
    assert "half_diminished_b5_retained" in recipes[ContentFamily.SEVENTH_BASIC].validity_notes

    plan = _resolve_medium_swing("Bø7")
    assert "b5" in plan.degrees


def test_altered_dominant_content_omits_natural_five_in_altered_families() -> None:
    policy = get_swing_policy()
    recipes = {recipe.family: recipe for recipe in plan_content_recipes("G7alt", policy)}

    assert "5" not in recipes[ContentFamily.ROOTLESS_A].degree_names
    assert "5" not in recipes[ContentFamily.ROOTLESS_B].degree_names
    assert "altered_dominant_natural_5_omitted" in recipes[ContentFamily.ROOTLESS_A].validity_notes


def test_bossa_broad_triad_policy_is_filtered_by_actual_chord_quality() -> None:
    policy = get_bossa_policy()

    assert ContentFamily.MINOR_TRIAD not in choose_content_families("C", policy)
    assert ContentFamily.MAJOR_TRIAD not in choose_content_families("Cm", policy)
    assert choose_content_families("C", policy) == [ContentFamily.MAJOR_TRIAD]
    assert choose_content_families("Cm", policy) == [ContentFamily.MINOR_TRIAD]


def test_bossa_altered_dominant_filters_plain_major_triad_metadata() -> None:
    policy = get_bossa_policy()
    families = choose_content_families("G7alt", policy)
    recipes = {recipe.family: recipe for recipe in plan_content_recipes("G7alt", policy)}

    assert ContentFamily.MAJOR_TRIAD not in families
    assert ContentFamily.ROOTLESS_A in families
    assert ContentFamily.ROOTED_COLOR in families
    assert ContentFamily.SEVENTH_BASIC not in families
    assert "5" not in recipes[ContentFamily.ROOTED_COLOR].degree_names
    assert "rooted_color_4note_altered_dominant_source_1_3_b7_X" in recipes[ContentFamily.ROOTED_COLOR].validity_notes
