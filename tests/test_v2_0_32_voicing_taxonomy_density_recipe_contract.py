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
    describe_density_recipe,
    generate_candidates,
)


def test_voicing_taxonomy_exports_density_recipe_contract() -> None:
    assert VOICING_CONTRACT_VERSION >= "v2_0_32"
    assert "density_recipe" in VOICING_CORE_PIPELINE
    assert FunctionalGrouping.TWO_PLUS_TWO.value == "2+2"
    assert FunctionalGrouping.TWO_PLUS_THREE.value == "2+3"
    assert FunctionalGrouping.THREE_PLUS_FOUR.value == "3+4"
    assert VoicingGroupRole.FOUNDATION.value == "foundation"
    assert VoicingGroupRole.PROJECTION.value == "projection"


def test_describe_density_recipe_is_stable_metadata_only() -> None:
    rootless = describe_density_recipe(
        ["3", "b7", "9", "13"],
        ContentFamily.ROOTLESS_A,
        RootSupportPolicy.ROOTLESS_ALLOWED,
    )
    assert rootless.to_debug_dict() == {
        "recipe_id": "d4__2plus2__rootless_A__rootless_allowed",
        "density": 4,
        "functional_grouping": "2+2",
        "group_roles": ["support", "color"],
        "content_family": "rootless_A",
        "root_support": "rootless_allowed",
    }

    rooted_five = describe_density_recipe(
        ["R", "3", "b7", "9", "13"],
        ContentFamily.ROOTED_COLOR,
        RootSupportPolicy.ROOT_REQUIRED,
    )
    assert rooted_five.density == 5
    assert rooted_five.functional_grouping == FunctionalGrouping.TWO_PLUS_THREE
    assert rooted_five.group_roles == (VoicingGroupRole.SUPPORT, VoicingGroupRole.PROJECTION)


def test_candidates_expose_recipe_metadata_without_changing_degrees() -> None:
    policy = VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        preferred_content=ContentFamily.ROOTLESS_A,
        preferred_disposition=Disposition.OPEN,
        preferred_density=4,
        selector_temperature=0.0,
    )
    candidate = generate_candidates("G13", policy)[0]
    debug = candidate.to_debug_dict()

    assert set(candidate.degrees) == {"3", "5", "b7", "13"}
    assert "rootless_ab_explicit_chord_symbol_color_used" in debug["metadata"]["content_recipe"]["validity_notes"]
    assert debug["density"] == 4
    assert debug["functional_grouping"] == "2+2"
    assert debug["recipe_id"] == "d4__2plus2__rootless_A__rootless_allowed"
    assert debug["group_roles"] == ["support", "color"]
    assert debug["metadata"]["density_recipe"]["recipe_id"] == debug["recipe_id"]


def test_voicing_plan_debug_exposes_recipe_contract_backwards_compatibly() -> None:
    request = VoicingRequest(
        event_id="v2_0_32_event",
        chord_symbol="Cmaj13",
        track="piano",
        gesture_type="simultaneous_onset",
        gesture=simultaneous_onset(metadata={"source": "density_recipe_contract_test"}),
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

    assert debug["midi_notes"] == plan.midi_notes
    assert debug["degrees"] == plan.degrees
    assert debug["density"] == len(plan.notes)
    assert debug["functional_grouping"] == "2+2"
    assert debug["recipe_id"].startswith("d4__2plus2__")
    assert debug["group_roles"] == ["support", "color"]
    assert debug["metadata"]["voicing_contract_version"] >= "v2_0_32"
    assert "density_recipe" in debug["metadata"]["voicing_core_pipeline"]
