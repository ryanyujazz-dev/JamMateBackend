from __future__ import annotations

from pathlib import Path

from jammate_engine.core.gestures.gesture import GestureKind, GestureRequest
from jammate_engine.core.voicing import ContentFamily, RootSupportPolicy, VoicingPolicy
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.runtime.override import build_voicing_override_policy
from jammate_engine.core.voicing.runtime.request import VoicingRequest
from jammate_engine.core.voicing.runtime.voicing_resolver import VoicingResolver

ROOT = Path(__file__).resolve().parents[1]


def _rootless_recipes(symbol: str):
    policy = build_voicing_override_policy({}, {"enabled": True, "preset": "rootless_ab_safe"}, style_name="medium_swing")
    return plan_content_recipes(symbol, policy)


def test_rootless_ab_generates_with_5_and_with_13_orientation_families() -> None:
    recipes = {(recipe.family, recipe.degree_names): recipe for recipe in _rootless_recipes("Cmaj7")}

    assert (ContentFamily.ROOTLESS_A, ("3", "5", "7", "9")) in recipes
    assert (ContentFamily.ROOTLESS_B, ("7", "9", "3", "5")) in recipes
    assert (ContentFamily.ROOTLESS_A, ("3", "13", "7", "9")) in recipes
    assert (ContentFamily.ROOTLESS_B, ("7", "9", "3", "13")) in recipes
    assert "rootless_ab_content_type_with_5" in recipes[(ContentFamily.ROOTLESS_A, ("3", "5", "7", "9"))].validity_notes
    assert "rootless_ab_content_type_with_13" in recipes[(ContentFamily.ROOTLESS_A, ("3", "13", "7", "9"))].validity_notes


def test_rootless_ab_orientation_is_preserved_in_candidate_placement() -> None:
    policy = build_voicing_override_policy({}, {"enabled": True, "preset": "rootless_ab_safe"}, style_name="medium_swing")
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
                plan.metadata.get("rootless_ab_degree_order"),
            )
        )

    assert [item[2] for item in selected] == ["with_5", "with_5", "with_5"]
    assert [item[3] for item in selected] == ["A", "B", "A"]
    # v2_1_15+ derives A/B from canonical source rotations. Therefore A is no
    # longer limited to the literal source order; v2_1_17 may choose the centered
    # 7-9-3-5-like rotation while still preserving the A/B orientation family.
    assert len({item[4] for item in selected}) == 1
    assert [item[5] for item in selected] == ["flat7_9_flat3_5", "3_5_flat7_9", "7_9_3_5"]
    assert selected[0][1] == ("b7", "9", "b3", "5")
    assert selected[1][1] == ("3", "5", "b7", "9")
    assert selected[2][1] == ("7", "9", "3", "5")


def test_explicit_color_gate_still_uses_only_chart_color_when_expansion_is_off() -> None:
    policy = VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B),
        preferred_density=4,
        max_density=4,
    )

    cmaj9_orders = {(recipe.family, recipe.degree_names) for recipe in plan_content_recipes("Cmaj9", policy)}
    g13_orders = {(recipe.family, recipe.degree_names) for recipe in plan_content_recipes("G13", policy)}

    assert (ContentFamily.ROOTLESS_A, ("3", "5", "7", "9")) in cmaj9_orders
    assert (ContentFamily.ROOTLESS_A, ("7", "9", "3", "5")) in cmaj9_orders
    # In chord_symbol_only mode, G13 may use the explicit 13 but must not sneak in an unnotated 9.
    assert (ContentFamily.ROOTLESS_A, ("3", "13", "b7", "5")) in g13_orders
    assert all("9" not in degree_names for _, degree_names in g13_orders if "13" in degree_names)


def test_v2_1_12_rootless_ab_orientation_is_documented() -> None:
    required_docs = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "VOICING_TUNING_WORKFLOW_V2.md",
        ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md",
        ROOT / "docs" / "STYLE_RULE_BASELINE_V2.md",
        ROOT / "docs" / "VOICING_SYSTEM_V2_DESIGN.md",
        ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md",
        ROOT / "docs" / "API_CONTRACT_V2.md",
        ROOT / "docs" / "SYSTEM_CONTRACTS_V2.md",
    ]
    for path in required_docs:
        text = path.read_text(encoding="utf-8")
        assert "v2_1_12" in text, path
        assert "rootless_ab_content_type_with_5" in text, path
        assert "rootless_ab_content_type_with_13" in text, path
        assert "A-B-A" in text and "B-A-B" in text, path
