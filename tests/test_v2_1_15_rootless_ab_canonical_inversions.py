from __future__ import annotations

from pathlib import Path

from jammate_engine.core.gestures.gesture import GestureKind, GestureRequest
from jammate_engine.core.voicing import ContentFamily
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.runtime.override import build_voicing_override_policy
from jammate_engine.core.voicing.runtime.request import VoicingRequest
from jammate_engine.core.voicing.runtime.voicing_resolver import VoicingResolver

ROOT = Path(__file__).resolve().parents[1]


def _rootless_policy():
    return build_voicing_override_policy({}, {"enabled": True, "preset": "rootless_ab_safe"}, style_name="medium_swing")


def test_v2_1_15_with_5_rootless_ab_is_derived_from_canonical_rotations() -> None:
    recipes = plan_content_recipes("Cmaj7", _rootless_policy())
    orders_by_family_and_type = {
        (recipe.family, next(note for note in recipe.validity_notes if note.startswith("rootless_ab_content_type_"))): []
        for recipe in recipes
    }
    for recipe in recipes:
        content_type = next(note for note in recipe.validity_notes if note.startswith("rootless_ab_content_type_"))
        orders_by_family_and_type[(recipe.family, content_type)].append(recipe.degree_names)

    assert orders_by_family_and_type[(ContentFamily.ROOTLESS_A, "rootless_ab_content_type_with_5")] == [
        ("3", "5", "7", "9"),
        ("5", "7", "9", "3"),
        ("7", "9", "3", "5"),
        ("9", "3", "5", "7"),
    ]
    assert orders_by_family_and_type[(ContentFamily.ROOTLESS_B, "rootless_ab_content_type_with_5")] == [
        ("7", "9", "3", "5"),
        ("9", "3", "5", "7"),
        ("3", "5", "7", "9"),
        ("5", "7", "9", "3"),
    ]


def test_v2_1_15_with_13_rootless_ab_uses_the_same_rotation_model() -> None:
    recipes = plan_content_recipes("Cmaj7", _rootless_policy())
    a_with_13 = [
        recipe.degree_names
        for recipe in recipes
        if recipe.family == ContentFamily.ROOTLESS_A and "rootless_ab_content_type_with_13" in recipe.validity_notes
    ]
    b_with_13 = [
        recipe.degree_names
        for recipe in recipes
        if recipe.family == ContentFamily.ROOTLESS_B and "rootless_ab_content_type_with_13" in recipe.validity_notes
    ]

    assert a_with_13 == [
        ("3", "13", "7", "9"),
        ("13", "7", "9", "3"),
        ("7", "9", "3", "13"),
        ("9", "3", "13", "7"),
    ]
    assert b_with_13 == [
        ("7", "9", "3", "13"),
        ("9", "3", "13", "7"),
        ("3", "13", "7", "9"),
        ("13", "7", "9", "3"),
    ]


def test_v2_1_15_ii_v_i_prefers_aba_same_content_type_and_inversion_index() -> None:
    policy = _rootless_policy()
    resolver = VoicingResolver()
    gesture = GestureRequest(kind=GestureKind.SIMULTANEOUS_ONSET)
    selected = []
    for symbol in ["Dm7", "G7", "Cmaj7"]:
        plan = resolver.resolve(
            VoicingRequest(
                event_id=symbol,
                chord_symbol=symbol,
                track="piano",
                gesture_type="simultaneous_onset",
                gesture=gesture,
                expression_articulation="sustain",
                ensemble_context={"bass_present": True},
                policy=policy,
            )
        )
        selected.append(
            (
                symbol,
                tuple(note.degree for note in plan.notes),
                plan.metadata.get("rootless_ab_content_type"),
                plan.metadata.get("rootless_ab_orientation_family"),
                plan.metadata.get("rootless_ab_inversion_index"),
            )
        )

    assert [item[2] for item in selected] == ["with_5", "with_5", "with_5"]
    assert [item[3] for item in selected] == ["A", "B", "A"]
    assert len({item[4] for item in selected}) == 1


def test_v2_1_15_rootless_ab_canonical_inversion_rule_is_documented() -> None:
    required_docs = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "VOICING_SYSTEM_V2_DESIGN.md",
        ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md",
        ROOT / "docs" / "STYLE_RULE_BASELINE_V2.md",
        ROOT / "docs" / "VOICING_TUNING_WORKFLOW_V2.md",
        ROOT / "docs" / "DEVELOPMENT_HARNESS_V2.md",
        ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md",
    ]
    for path in required_docs:
        text = path.read_text(encoding="utf-8")
        assert "v2_1_15" in text, path
        assert "canonical source" in text.lower(), path
        assert "3-5-7-9" in text and "7-9-3-5" in text, path
        assert "ABA" in text and "BAB" in text, path
