from __future__ import annotations

from pathlib import Path

from jammate_engine.core.voicing import Disposition, VoicingPolicy, generate_candidates
from jammate_engine.core.voicing.disposition import (
    DispositionFamily,
    OpenProjectionMethod,
    VoicingMethodLockMode,
    method_lock_runtime_plan_for_projection,
    method_lock_spec_from_metadata,
)
from jammate_engine.api.version import ENGINE_VERSION_TAG


def test_strict_method_lock_runtime_plan_can_enable_hard_filtering() -> None:
    spec = method_lock_spec_from_metadata(
        {
            "voicing_method_lock": {
                "enabled": True,
                "scope": "progression",
                "pattern": "ii_v_i",
                "mode": "strict",
                "family": "open",
                "method": "drop2",
                "runtime_filtering_enabled": True,
            }
        }
    )
    assert spec.mode == VoicingMethodLockMode.STRICT

    matched = method_lock_runtime_plan_for_projection(
        spec,
        {"disposition_projection_family": "open", "disposition_projection_method": "drop2"},
        filtering_enabled=True,
    ).to_debug_dict()
    mismatched = method_lock_runtime_plan_for_projection(
        spec,
        {"disposition_projection_family": "open", "disposition_projection_method": "drop3"},
        filtering_enabled=True,
    ).to_debug_dict()

    assert matched["candidate_matches_lock"] is True
    assert matched["filtering_enabled"] is True
    assert matched["planned_action"] == "keep_candidate"
    assert matched["reason"] == "strict_runtime_filtering_enabled"
    assert mismatched["candidate_matches_lock"] is False
    assert mismatched["filtering_enabled"] is True
    assert mismatched["planned_action"] == "filter_candidate"


def test_strict_open_drop2_lock_filters_candidate_pool_when_explicitly_enabled() -> None:
    policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        preferred_density=4,
        min_density=4,
        max_density=4,
        register_low=46,
        register_high=84,
        max_voicing_span=28,
        metadata={
            "style": "medium_swing",
            # Even without open_projection_method_pool="all", the strict lock
            # should request the locked OPEN method so it can bind to DROP2.
            "voicing_method_lock": {
                "enabled": True,
                "scope": "progression",
                "pattern": "ii_v_i",
                "family": "open",
                "method": "drop2",
                "runtime_filtering_enabled": True,
            },
        },
    )
    candidates = generate_candidates("Dm7", policy)
    assert candidates
    methods = {candidate.metadata["disposition_projection_method"] for candidate in candidates}
    assert methods == {"drop2"}
    assert all(candidate.metadata["disposition_projection_family"] == "open" for candidate in candidates)
    assert all(candidate.metadata["voicing_method_lock_candidate_matches"] is True for candidate in candidates)
    assert all(candidate.metadata["voicing_method_lock_runtime_filtering_enabled"] is True for candidate in candidates)
    assert all(candidate.metadata["voicing_method_lock_runtime_action"] == "keep_candidate" for candidate in candidates)
    assert all(candidate.metadata["active_open_projection_method"] == "drop2" for candidate in candidates)


def test_strict_lock_without_runtime_filtering_remains_no_default_behavior_change() -> None:
    policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        preferred_density=4,
        min_density=4,
        max_density=4,
        register_low=46,
        register_high=84,
        max_voicing_span=28,
        metadata={
            "style": "medium_swing",
            "open_projection_method_pool": "all",
            "voicing_method_lock": {
                "enabled": True,
                "scope": "progression",
                "pattern": "ii_v_i",
                "family": "open",
                "method": "drop2",
                # Runtime filtering intentionally omitted.
            },
        },
    )
    candidates = generate_candidates("Dm7", policy)
    assert candidates
    methods = {candidate.metadata["disposition_projection_method"] for candidate in candidates}
    assert {"generic_open", "drop2", "drop3", "drop2_and_4"}.issubset(methods)
    assert any(candidate.metadata["voicing_method_lock_candidate_matches"] is False for candidate in candidates)
    assert all(candidate.metadata["voicing_method_lock_runtime_filtering_enabled"] is False for candidate in candidates)
    assert any(candidate.metadata["voicing_method_lock_runtime_action"] == "filter_candidate_future" for candidate in candidates)


def test_enabled_method_lock_defaults_to_strict_not_prefer() -> None:
    spec = method_lock_spec_from_metadata({"voicing_method_lock": {"enabled": True, "family": "open", "method": "drop2"}})
    assert spec.family == DispositionFamily.OPEN
    assert spec.open_method == OpenProjectionMethod.DROP2
    assert spec.mode == VoicingMethodLockMode.STRICT


def test_v2_2_10_docs_and_version_mark_method_lock_enforcement() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    docs = Path("docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md").read_text(encoding="utf-8")
    assert "v2_2_12" in docs
    assert "runtime_filtering_enabled=True" in docs
    assert "hard binding concept" in docs
