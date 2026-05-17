from __future__ import annotations

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import Disposition, OpenProjectionMethod, VoicingPolicy, generate_candidates, project_source_to_disposition
from jammate_engine.core.voicing.disposition.open import place_drop2_projection_from_closed_parent

TEST_MODULE_NAME = "test_v2_2_5_drop2_parent_closed_projection"


def _drop2(parent: list[tuple[str, int]], policy: VoicingPolicy | None = None) -> list[tuple[str, int]]:
    return place_drop2_projection_from_closed_parent(
        parent,
        policy
        or VoicingPolicy(
            preferred_disposition=Disposition.OPEN,
            allowed_dispositions=(Disposition.OPEN,),
            register_low=48,
            register_high=84,
            max_voicing_span=28,
        ),
    )


def test_v2_2_5_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"


def test_drop2_is_derived_from_parent_closed_rotation_not_raw_source_order() -> None:
    # root-third-fifth-seventh closed parent: C E G B -> G C E B
    assert _drop2([("R", 60), ("3", 64), ("5", 67), ("7", 71)]) == [
        ("5", 55),
        ("R", 60),
        ("3", 64),
        ("7", 71),
    ]

    # third-fifth-seventh-root closed parent: E G B C -> B E G C
    assert _drop2([("3", 64), ("5", 67), ("7", 71), ("R", 72)]) == [
        ("7", 59),
        ("3", 64),
        ("5", 67),
        ("R", 72),
    ]

    # fifth-seventh-root-third closed parent: G B C E -> C G B E
    assert _drop2([("5", 67), ("7", 71), ("R", 72), ("3", 76)]) == [
        ("R", 60),
        ("5", 67),
        ("7", 71),
        ("3", 76),
    ]


def test_drop2_supports_doubled_triad_parent_closed_rotation() -> None:
    # root-third-fifth-root is a real 4-note closed source even though it repeats
    # a pitch class.  DROP2 must derive from that parent, not reject it as a
    # duplicate pitch-class strict-closed seed.
    placed = _drop2([("R", 60), ("3", 64), ("5", 67), ("R", 72)])

    assert placed == [("5", 55), ("R", 60), ("3", 64), ("R", 72)]


def test_projection_entry_uses_closed_parent_callback_for_drop2() -> None:
    policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        register_low=48,
        register_high=84,
        max_voicing_span=28,
        metadata={"open_projection_method": "drop2"},
    )

    result = project_source_to_disposition(
        disposition=Disposition.OPEN,
        policy=policy,
        root_pc=0,
        degrees=[("R", 0), ("3", 4), ("5", 7), ("7", 11)],
        legacy_placement_callback=lambda: [("legacy_open", 60)],
        closed_parent_placement_callback=lambda: [("3", 64), ("5", 67), ("7", 71), ("R", 72)],
    )

    assert result.spec.open_method == OpenProjectionMethod.DROP2
    assert result.metadata["legacy_projection_callback_used"] is False
    assert result.metadata["open_drop2_projection_migrated"] is True
    assert result.metadata["open_drop2_from_parent_closed_projection"] is True
    assert result.metadata["open_drop2_parent_closed_degrees"] == ["3", "5", "7", "R"]
    assert result.metadata["open_drop2_parent_closed_notes"] == [64, 67, 71, 72]
    assert result.placed_list == [("7", 59), ("3", 64), ("5", 67), ("R", 72)]


def test_candidate_generation_can_request_parent_closed_drop2_without_changing_default_open() -> None:
    default_policy = VoicingPolicy(preferred_disposition=Disposition.OPEN, allowed_dispositions=(Disposition.OPEN,))
    default_candidates = generate_candidates("Cmaj7", default_policy)
    assert default_candidates
    assert all(candidate.metadata["disposition_projection_method"] == "generic_open" for candidate in default_candidates)

    drop2_policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        preferred_density=4,
        min_density=4,
        max_density=4,
        metadata={"open_projection_method": "drop2"},
    )
    drop2_candidates = generate_candidates("Cmaj7", drop2_policy)
    assert drop2_candidates
    assert all(candidate.metadata["disposition_projection_family"] == "open" for candidate in drop2_candidates)
    assert all(candidate.metadata["disposition_projection_method"] == "drop2" for candidate in drop2_candidates)
    assert all(candidate.metadata["legacy_projection_callback_used"] is False for candidate in drop2_candidates)
    assert all(len(candidate.notes) == 4 for candidate in drop2_candidates)
    assert any(candidate.metadata.get("open_drop2_from_parent_closed_projection") is True for candidate in drop2_candidates)
    assert all("open_drop2_parent_closed_notes" in candidate.metadata for candidate in drop2_candidates)
