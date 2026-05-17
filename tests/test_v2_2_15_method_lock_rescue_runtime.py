from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    Disposition,
    VOICING_CONTRACT_VERSION,
    VoicingPolicy,
    generate_candidates,
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


def test_v2_2_20_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_CONTRACT_VERSION == "v2_2_21"
    assert Path("VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"


def test_rescue_runtime_is_explicit_and_not_enabled_by_default() -> None:
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
    assert candidates[0].metadata["fallback"] is True
    assert candidates[0].metadata["voicing_method_lock_rescue_needed"] is True
    assert "voicing_method_lock_rescue_runtime_executed" not in candidates[0].metadata


def test_rescue_runtime_executes_closed_compact_when_locked_spread_has_no_candidates() -> None:
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
                    "method_lock_rescue_runtime_enabled": True,
                }
            }
        ),
    )

    assert candidates
    assert all(not candidate.metadata.get("fallback") for candidate in candidates)
    assert {candidate.metadata["disposition_projection_family"] for candidate in candidates} == {"closed"}
    assert {candidate.metadata["disposition_projection_method"] for candidate in candidates} == {"compact"}
    assert all(candidate.metadata["voicing_method_lock_rescue_runtime_executed"] is True for candidate in candidates)
    assert all(candidate.metadata["voicing_method_lock_rescue_runtime_action"] == "try_closed_compact" for candidate in candidates)
    assert all(candidate.metadata["voicing_method_lock_rescue_runtime_succeeded"] is True for candidate in candidates)
    assert all(candidate.metadata["voicing_method_lock_rescue_original_family"] == "spread" for candidate in candidates)
    assert all(candidate.metadata["voicing_method_lock_rescue_original_method"] == "lower_upper_grouped" for candidate in candidates)


def test_open_named_method_rescue_prefers_same_family_generic_open() -> None:
    # Make the locked DROP2 impossible through a very narrow register.  Runtime
    # rescue should first try OPEN/GENERIC_OPEN before closed/unlocked fallbacks.
    policy = _open_4note_policy(
        {
            "voicing_method_lock": {
                "enabled": True,
                "mode": "strict",
                "family": "open",
                "method": "drop2",
                "runtime_filtering_enabled": True,
                "method_lock_rescue_runtime_enabled": True,
            }
        }
    )
    from dataclasses import replace
    policy = replace(policy, register_low=70, register_high=72, comfort_register_low=70, comfort_register_high=72)
    candidates = generate_candidates("G7", policy)

    assert candidates
    assert all(candidate.metadata["voicing_method_lock_rescue_runtime_executed"] is True for candidate in candidates)
    assert all(candidate.metadata["voicing_method_lock_rescue_runtime_action"] in {"try_same_family_safe_method", "try_closed_compact", "unlock_current_region_with_audit"} for candidate in candidates)
    assert all(candidate.metadata["voicing_method_lock_rescue_original_family"] == "open" for candidate in candidates)
    assert all(candidate.metadata["voicing_method_lock_rescue_original_method"] == "drop2" for candidate in candidates)


def test_docs_record_method_lock_rescue_runtime_pilot() -> None:
    docs = Path("docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md").read_text(encoding="utf-8")
    assert "v2_2_20" in docs
    assert "Method Lock Rescue Runtime" in docs
    assert "method_lock_rescue_runtime_enabled" in docs
