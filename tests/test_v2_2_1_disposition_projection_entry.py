from jammate_engine.core.voicing import (
    Disposition,
    DispositionFamily,
    OpenProjectionMethod,
    VoicingPolicy,
    generate_candidates,
    project_source_to_disposition,
)


def test_projection_entry_normalizes_legacy_disposition_without_changing_placement() -> None:
    policy = VoicingPolicy(preferred_disposition=Disposition.OPEN)
    result = project_source_to_disposition(
        disposition=Disposition.OPEN,
        policy=policy,
        legacy_placement_callback=lambda: [("R", 60), ("3", 64), ("5", 67), ("7", 71)],
    )

    assert result.placed_list == [("R", 60), ("3", 64), ("5", 67), ("7", 71)]
    assert result.spec.family == DispositionFamily.OPEN
    assert result.spec.open_method == OpenProjectionMethod.GENERIC_OPEN
    assert result.metadata["disposition_projection_entry"].endswith("project_source_to_disposition")
    assert result.metadata["legacy_projection_callback_used"] is True
    assert result.disposition_guard["disposition"] == "open"


def test_candidate_generation_routes_through_projection_entry_metadata() -> None:
    policy = VoicingPolicy(preferred_disposition=Disposition.OPEN, allowed_dispositions=(Disposition.OPEN,))
    candidate = generate_candidates("Cmaj7", policy)[0]
    debug = candidate.to_debug_dict()

    assert debug["metadata"]["disposition_projection_family"] == "open"
    assert debug["metadata"]["disposition_projection_method"] == "generic_open"
    assert debug["metadata"]["legacy_projection_callback_used"] is True
    assert debug["metadata"]["legacy_projection_cleanup_required"] is True
    assert debug["metadata"]["disposition_projection_spec"]["legacy_disposition"] == "open"
    assert debug["disposition_guard"]["disposition"] == "open"
