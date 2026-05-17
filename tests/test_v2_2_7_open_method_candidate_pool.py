from __future__ import annotations

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import Disposition, OpenProjectionMethod, VoicingPolicy, generate_candidates
from jammate_engine.core.voicing.disposition.models import open_projection_method_pool_from_metadata
from jammate_engine.core.voicing.disposition.open import (
    place_drop2_and_4_projection_from_closed_parent,
    place_drop3_projection_from_closed_parent,
)

TEST_MODULE_NAME = "test_v2_2_7_open_method_candidate_pool"


def test_v2_2_8_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"


def test_open_method_pool_defaults_to_generic_open_only() -> None:
    assert open_projection_method_pool_from_metadata({}) == (OpenProjectionMethod.GENERIC_OPEN,)


def test_open_method_pool_accepts_explicit_multiple_methods() -> None:
    methods = open_projection_method_pool_from_metadata(
        {"allowed_open_projection_methods": ["generic_open", "drop2", "drop3", "drop2_and_4"]}
    )
    assert methods == (
        OpenProjectionMethod.GENERIC_OPEN,
        OpenProjectionMethod.DROP2,
        OpenProjectionMethod.DROP3,
        OpenProjectionMethod.DROP2_AND_4,
    )


def test_drop3_and_drop2_and_4_are_parent_closed_derived_skeletons() -> None:
    policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        register_low=48,
        register_high=84,
        max_voicing_span=28,
        metadata={"drop_family_register_low_offset_semitones": 0},
    )
    parent = [("R", 60), ("3", 64), ("5", 67), ("7", 71)]

    # DROP3 drops the third voice from the top: E4 -> E3.
    assert place_drop3_projection_from_closed_parent(parent, policy) == [
        ("3", 52),
        ("R", 60),
        ("5", 67),
        ("7", 71),
    ]

    # DROP2&4 drops the second and fourth voices from the top: G4 -> G3 and C4 -> C3.
    assert place_drop2_and_4_projection_from_closed_parent(parent, policy) == [
        ("R", 48),
        ("5", 55),
        ("3", 64),
        ("7", 71),
    ]


def test_generate_candidates_can_put_multiple_open_methods_in_one_candidate_pool() -> None:
    policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        preferred_density=4,
        min_density=4,
        max_density=4,
        register_low=48,
        register_high=84,
        max_voicing_span=28,
        metadata={"allowed_open_projection_methods": ["generic_open", "drop2", "drop3", "drop2_and_4"]},
    )

    candidates = generate_candidates("Cmaj7", policy)
    assert candidates
    methods = {candidate.metadata["disposition_projection_method"] for candidate in candidates}
    assert {"generic_open", "drop2", "drop3", "drop2_and_4"}.issubset(methods)
    assert any(candidate.metadata["open_projection_method_pool_enabled"] is True for candidate in candidates)
    assert all(candidate.metadata["open_projection_method_pool_size"] == 4 for candidate in candidates)
    assert any(candidate.metadata.get("open_named_projection_method") == "drop3" for candidate in candidates)
    assert any(candidate.metadata.get("open_named_projection_method") == "drop2_and_4" for candidate in candidates)


def test_default_open_generation_still_does_not_auto_enter_drop_pool() -> None:
    policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        preferred_density=4,
        min_density=4,
        max_density=4,
    )
    candidates = generate_candidates("Cmaj7", policy)
    assert candidates
    assert {candidate.metadata["disposition_projection_method"] for candidate in candidates} == {"generic_open"}
    assert all(candidate.metadata["open_projection_method_pool_enabled"] is False for candidate in candidates)
