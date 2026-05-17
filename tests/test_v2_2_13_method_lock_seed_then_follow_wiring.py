from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    Disposition,
    OpenProjectionMethod,
    VOICING_CONTRACT_VERSION,
    VoicingPolicy,
    generate_candidates,
    method_lock_follow_metadata_from_seed_candidate,
    method_lock_scope_plan_from_symbols,
    method_lock_seed_follow_plan_from_seed_candidate_metadata,
    method_lock_spec_from_seed_follow_plan,
)


def _open_4note_policy(metadata: dict | None = None) -> VoicingPolicy:
    return VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        preferred_density=4,
        min_density=4,
        max_density=4,
        metadata={"style": "medium_swing", **(metadata or {})},
    )


def _first_drop2_seed_candidate():
    candidates = generate_candidates(
        "Dm7",
        _open_4note_policy({"open_projection_method": "drop2"}),
    )
    assert candidates
    seed = candidates[0]
    assert seed.metadata["disposition_projection_family"] == "open"
    assert seed.metadata["disposition_projection_method"] == "drop2"
    return seed


def test_v2_2_14_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_CONTRACT_VERSION == "v2_2_21"
    assert Path("VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"


def test_seed_candidate_metadata_builds_follow_runtime_lock_plan() -> None:
    scope_plan = method_lock_scope_plan_from_symbols(
        previous_chord_symbol="Dm7",
        chord_symbol="G7",
        next_chord_symbol="Cmaj7",
        previous_region_id="r1_Dm7",
        current_region_id="r2_G7",
        next_region_id="r3_Cmaj7",
    )
    seed = _first_drop2_seed_candidate()

    follow_plan = method_lock_seed_follow_plan_from_seed_candidate_metadata(
        scope_plan,
        seed.metadata,
        current_region_id="r2_G7",
        runtime_filtering_enabled=True,
    )
    debug = follow_plan.to_debug_dict()

    assert follow_plan.enabled is True
    assert follow_plan.target_open_method == OpenProjectionMethod.DROP2
    assert follow_plan.follow_region_ids == ("r2_G7", "r3_Cmaj7")
    assert follow_plan.current_region_id == "r2_G7"
    assert follow_plan.runtime_filtering_enabled is True
    assert debug["contract"] == "method_lock_seed_then_follow_runtime_wiring_v2_2_14"
    assert debug["target_family"] == "open"
    assert debug["target_method"] == "drop2"


def test_seed_follow_plan_converts_to_strict_lock_spec() -> None:
    scope_plan = method_lock_scope_plan_from_symbols(
        previous_chord_symbol="Dm7",
        chord_symbol="G7",
        next_chord_symbol="Cmaj7",
        previous_region_id="r1",
        current_region_id="r2",
        next_region_id="r3",
    )
    follow_plan = method_lock_seed_follow_plan_from_seed_candidate_metadata(
        scope_plan,
        _first_drop2_seed_candidate().metadata,
        current_region_id="r2",
    )
    spec = method_lock_spec_from_seed_follow_plan(follow_plan)

    assert spec.enabled is True
    assert spec.scope_id == scope_plan.scope_id
    assert spec.locked_from_region_id == "r1"
    assert spec.family.value == "open"
    assert spec.open_method == OpenProjectionMethod.DROP2
    assert spec.mode.value == "strict"


def test_follow_metadata_forces_follow_region_to_seed_selected_method_when_explicit() -> None:
    scope_plan = method_lock_scope_plan_from_symbols(
        previous_chord_symbol="Dm7",
        chord_symbol="G7",
        next_chord_symbol="Cmaj7",
        previous_region_id="r1_Dm7",
        current_region_id="r2_G7",
        next_region_id="r3_Cmaj7",
    )
    seed = _first_drop2_seed_candidate()
    follow_metadata = method_lock_follow_metadata_from_seed_candidate(
        scope_plan,
        seed.metadata,
        current_region_id="r2_G7",
        runtime_filtering_enabled=True,
    )

    follow_candidates = generate_candidates("G7", _open_4note_policy(follow_metadata))
    assert follow_candidates
    methods = {candidate.metadata["disposition_projection_method"] for candidate in follow_candidates}
    assert methods == {"drop2"}
    assert all(candidate.metadata["voicing_method_lock_candidate_matches"] is True for candidate in follow_candidates)
    assert all(candidate.metadata["voicing_method_lock_runtime_filtering_enabled"] is True for candidate in follow_candidates)
    assert all(candidate.metadata["voicing_method_lock_runtime_action"] == "keep_candidate" for candidate in follow_candidates)
    assert all(candidate.metadata["voicing_method_lock_scope_runtime_wiring_enabled"] is True for candidate in follow_candidates)
    assert all(candidate.metadata["voicing_method_lock_scope_runtime_wiring_seed_region_id"] == "r1_Dm7" for candidate in follow_candidates)


def test_seed_then_follow_wiring_is_explicit_and_default_open_still_generic() -> None:
    default_candidates = generate_candidates("G7", _open_4note_policy())
    assert default_candidates
    assert {candidate.metadata["disposition_projection_method"] for candidate in default_candidates} == {"generic_open"}
    assert all(candidate.metadata["voicing_method_lock_scope_runtime_wiring_enabled"] is False for candidate in default_candidates)


def test_v2_2_14_docs_record_seed_then_follow_wiring() -> None:
    docs = Path("docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md").read_text(encoding="utf-8")
    harness = Path("docs/DEVELOPMENT_HARNESS_V2.md").read_text(encoding="utf-8")
    assert "v2_2_14" in docs
    assert "Seed-Then-Follow" in docs
    assert "method_lock_follow_metadata_from_seed_candidate" in docs
    assert "Capability Reuse Before New Construction" in harness
