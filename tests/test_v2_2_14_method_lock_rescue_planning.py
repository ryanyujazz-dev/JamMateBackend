from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    Disposition,
    DispositionFamily,
    OpenProjectionMethod,
    SpreadProjectionMethod,
    VOICING_CONTRACT_VERSION,
    VoicingMethodLockMode,
    VoicingMethodLockRescueAction,
    VoicingMethodLockSpec,
    VoicingPolicy,
    generate_candidates,
    method_lock_rescue_plan_for_generation,
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


def test_v2_2_14_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_CONTRACT_VERSION == "v2_2_21"
    assert Path("VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"


def test_strict_open_drop2_rescue_plan_prefers_same_family_generic_open_then_closed() -> None:
    spec = VoicingMethodLockSpec(
        enabled=True,
        mode=VoicingMethodLockMode.STRICT,
        family=DispositionFamily.OPEN,
        open_method=OpenProjectionMethod.DROP2,
    )
    plan = method_lock_rescue_plan_for_generation(
        spec,
        kept_candidate_count=0,
        filtered_candidate_count=4,
        runtime_filtering_enabled=True,
        fallback_returned=True,
    )
    debug = plan.to_debug_dict()

    assert plan.rescue_needed is True
    assert plan.same_family_safe_method == "generic_open"
    assert plan.recommended_actions[:2] == (
        VoicingMethodLockRescueAction.TRY_SAME_FAMILY_SAFE_METHOD,
        VoicingMethodLockRescueAction.TRY_CLOSED_COMPACT,
    )
    assert debug["contract"] == "method_lock_rescue_planning_v2_2_14"
    assert debug["break_reason"] == "method_lock_filtered_all_candidates"


def test_strict_lock_with_available_candidate_does_not_need_rescue() -> None:
    spec = VoicingMethodLockSpec(
        enabled=True,
        mode=VoicingMethodLockMode.STRICT,
        family=DispositionFamily.OPEN,
        open_method=OpenProjectionMethod.DROP2,
    )
    plan = method_lock_rescue_plan_for_generation(
        spec,
        kept_candidate_count=2,
        filtered_candidate_count=1,
        runtime_filtering_enabled=True,
    )

    assert plan.rescue_needed is False
    assert plan.reason == "locked_candidate_available"
    assert plan.recommended_actions == (VoicingMethodLockRescueAction.KEEP_LOCKED_CANDIDATE,)


def test_generate_candidates_records_rescue_plan_when_strict_lock_filters_all_candidates() -> None:
    # Force an impossible request for this policy: only OPEN candidates are generated,
    # but the lock requires SPREAD + lower_upper_grouped.  v2_2_14 must not silently
    # treat this as a soft preference; it records an explicit rescue audit plan.
    candidates = generate_candidates(
        "G7",
        _open_4note_policy(
            {
                "voicing_method_lock": {
                    "enabled": True,
                    "mode": "strict",
                    "family": "spread",
                    "method": "lower_upper_grouped",
                    "runtime_filtering_enabled": True,
                }
            }
        ),
    )

    assert len(candidates) == 1
    fallback = candidates[0]
    assert fallback.metadata["fallback"] is True
    assert fallback.metadata["voicing_method_lock_rescue_needed"] is True
    assert fallback.metadata["voicing_method_lock_rescue_break_reason"] == "method_lock_filtered_all_candidates"
    assert fallback.metadata["voicing_method_lock_filtered_candidate_count"] > 0
    rescue_plan = fallback.metadata["voicing_method_lock_rescue_plan"]
    assert rescue_plan["locked_family"] == "spread"
    assert rescue_plan["locked_method"] == "lower_upper_grouped"
    assert "try_closed_compact" in rescue_plan["recommended_actions"]
    assert "unlock_current_region_with_audit" in rescue_plan["recommended_actions"]


def test_docs_record_method_lock_rescue_planning() -> None:
    docs = Path("docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md").read_text(encoding="utf-8")
    harness = Path("docs/DEVELOPMENT_HARNESS_V2.md").read_text(encoding="utf-8")
    assert "v2_2_14" in docs
    assert "Method Lock Rescue" in docs
    assert "Capability Reuse Before New Construction" in harness
