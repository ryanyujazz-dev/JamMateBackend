from __future__ import annotations

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.voicing import (
    VOICING_CONTRACT_VERSION,
    VOICING_CORE_PIPELINE,
    ContentFamily,
    Disposition,
    FunctionalGrouping,
    RootSupportPolicy,
    VoicingGroupRole,
    VoicingPolicy,
    VoicingRequest,
    VoicingResolver,
    build_projection_map,
    group_indices_for_projection,
)


def test_projection_map_exports_abstract_group_keys_and_keeps_compatibility_keys() -> None:
    projection = build_projection_map(
        [55, 59, 64, 69],
        functional_grouping=FunctionalGrouping.TWO_PLUS_TWO,
        group_roles=(VoicingGroupRole.SUPPORT, VoicingGroupRole.COLOR),
    )

    assert projection["all_voices"] == [0, 1, 2, 3]
    assert projection["lowest"] == [0]
    assert projection["inner"] == [1, 2]
    assert projection["inner_1"] == [1]
    assert projection["inner_2"] == [2]
    assert projection["top"] == [3]

    assert projection["support_group"] == [0, 1]
    assert projection["color_group"] == [2, 3]
    assert projection["projection_group"] == [2, 3]

    # Existing piano realization compatibility hints remain available, but they
    # are not the canonical core grouping vocabulary.
    assert "left_hand" in projection
    assert "right_hand" in projection


def test_group_indices_helper_supports_future_motion_projection_without_hands() -> None:
    groups = group_indices_for_projection(
        5,
        FunctionalGrouping.TWO_PLUS_THREE,
        (VoicingGroupRole.SUPPORT, VoicingGroupRole.MOTION),
    )

    assert groups == {
        "support_group": [0, 1],
        "motion_group": [2, 3, 4],
    }
    assert "left_hand" not in groups
    assert "right_hand" not in groups


def test_voicing_plan_exposes_projection_ready_groups_without_changing_content() -> None:
    assert VOICING_CONTRACT_VERSION >= "v2_0_37"
    assert "projection_map" in VOICING_CORE_PIPELINE
    assert "functional_group_projection" in VOICING_CORE_PIPELINE

    request = VoicingRequest(
        event_id="v2_0_34_event",
        chord_symbol="G13",
        track="piano",
        gesture_type="simultaneous_onset",
        gesture=simultaneous_onset(metadata={"source": "projection_map_contract_test"}),
        expression_articulation="sustain",
        ensemble_context={"bass_present": True},
        policy=VoicingPolicy(
            root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
            preferred_content=ContentFamily.ROOTLESS_A,
            preferred_disposition=Disposition.OPEN,
            preferred_density=4,
            selector_temperature=0.0,
        ),
        onset_beat=1.0,
    )

    plan = VoicingResolver().resolve(request)
    debug = plan.to_debug_dict()

    assert set(debug["degrees"]) == {"3", "5", "b7", "13"}
    assert debug["functional_grouping"] == "2+2"
    assert debug["groups"]["support_group"] == [0, 1]
    assert debug["groups"]["color_group"] == [2, 3]
    assert debug["projection_map"]["support_group"] == [0, 1]
    assert debug["projection_map"]["color_group"] == [2, 3]
    assert debug["projection_map"]["all_voices"] == [0, 1, 2, 3]
    assert debug["projection_map"]["top"] == [3]
    assert debug["notes"][0]["group_id"] == "support_group"
    assert debug["notes"][1]["group_id"] == "support_group"
    assert debug["notes"][2]["group_id"] == "color_group"
    assert debug["notes"][3]["group_id"] == "color_group"
    assert debug["metadata"]["voicing_contract_version"] >= "v2_0_37"
    assert "functional_group_projection" in debug["metadata"]["voicing_core_pipeline"]


def test_rooted_one_plus_three_adds_anchor_foundation_and_projection_refs() -> None:
    projection = build_projection_map(
        [48, 60, 64, 67],
        functional_grouping=FunctionalGrouping.ONE_PLUS_THREE,
        group_roles=(VoicingGroupRole.ANCHOR, VoicingGroupRole.PROJECTION),
    )

    assert projection["anchor_group"] == [0]
    assert projection["foundation_group"] == [0]
    assert projection["projection_group"] == [1, 2, 3]
    assert projection["all_voices"] == [0, 1, 2, 3]
