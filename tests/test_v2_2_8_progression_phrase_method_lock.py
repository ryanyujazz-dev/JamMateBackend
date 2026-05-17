from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    Disposition,
    DispositionFamily,
    OpenProjectionMethod,
    VoicingMethodLockMode,
    VoicingMethodLockPattern,
    VoicingMethodLockScope,
    VoicingPolicy,
    generate_candidates,
    method_lock_spec_from_metadata,
)

TEST_MODULE_NAME = "test_v2_2_8_progression_phrase_method_lock"


def test_v2_2_8_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"


def test_method_lock_metadata_contract_accepts_ii_v_i_open_drop2() -> None:
    spec = method_lock_spec_from_metadata(
        {
            "voicing_method_lock": {
                "enabled": True,
                "scope": "progression",
                "progression_pattern": "ii_v_i",
                "scope_id": "bars_1_3",
                "locked_from_region_id": "bar1_chord1",
                "family": "open",
                "method": "drop2",
                "mode": "prefer",
            }
        }
    )

    assert spec.enabled is True
    assert spec.scope == VoicingMethodLockScope.PROGRESSION
    assert spec.pattern == VoicingMethodLockPattern.II_V_I
    assert spec.mode == VoicingMethodLockMode.PREFER
    assert spec.scope_id == "bars_1_3"
    assert spec.locked_from_region_id == "bar1_chord1"
    assert spec.family == DispositionFamily.OPEN
    assert spec.open_method == OpenProjectionMethod.DROP2
    assert spec.method_value == "drop2"
    assert "gesture_driven_revoice" in spec.break_triggers


def test_method_lock_metadata_is_debug_only_and_does_not_change_default_open_pool() -> None:
    policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        preferred_density=4,
        min_density=4,
        max_density=4,
        metadata={
            "voicing_method_lock": {
                "scope": "progression",
                "progression_pattern": "ii_v_i",
                "scope_id": "bars_1_3",
                "family": "open",
                "method": "drop2",
                "mode": "prefer",
            }
        },
    )

    candidates = generate_candidates("Cmaj7", policy)
    assert candidates
    assert {candidate.metadata["disposition_projection_method"] for candidate in candidates} == {"generic_open"}
    assert all(candidate.metadata["voicing_method_lock_enabled"] is True for candidate in candidates)
    first_lock = candidates[0].metadata["voicing_method_lock_plan"]
    assert first_lock["pattern"] == "ii_v_i"
    assert first_lock["family"] == "open"
    assert first_lock["method"] == "drop2"
    assert first_lock["contract"] == "progression_phrase_voicing_method_lock_planning_only"


def test_v2_2_8_docs_record_method_lock_contract_and_next_step() -> None:
    text = Path("docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md").read_text(encoding="utf-8")
    assert "v2_2_8 Progression / Phrase-level Voicing Method Lock Contract" in text
    assert "VoicingMethodLockSpec" in text
    assert "ii-V" in text
    assert "V-I" in text
    assert "ii-V-I" in text
    assert "same DispositionFamily + ProjectionMethod" in text
    assert "planning-only" in text
    assert "v2_2_12" in Path("docs/DEVELOPMENT_TASK_PLAN_V2.md").read_text(encoding="utf-8")
