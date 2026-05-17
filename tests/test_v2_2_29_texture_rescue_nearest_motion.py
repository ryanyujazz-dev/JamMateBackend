from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import Disposition, VOICING_CONTRACT_VERSION, VoicingCandidate, VoicingPolicy
from jammate_engine.core.voicing.selection.selector import select_candidate
from jammate_engine.core.voicing.runtime.state import VoicingState
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as get_medium_swing_voicing_policy


def _state() -> VoicingState:
    return VoicingState.empty().advance(
        event_id="prev",
        chord_symbol="Dm7",
        notes=[60, 64, 67, 71],
        degrees=["R", "3", "5", "7"],
    )


def test_v2_2_29_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_CONTRACT_VERSION == "v2_2_21"
    assert Path("VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"


def test_rescue_pool_collapses_to_nearest_previous_voicing_before_scoring() -> None:
    policy = VoicingPolicy(
        selector_temperature=0.0,
        metadata={"texture_state_rescue_nearest_motion_enabled": True},
    )
    far_high_score = VoicingCandidate(
        notes=[84, 88, 91, 95],
        degrees=["R", "3", "5", "7"],
        score=20.0,
        disposition=Disposition.CLOSED,
        metadata={"voicing_method_lock_rescue_runtime_executed": True},
    )
    near_low_score = VoicingCandidate(
        notes=[61, 65, 68, 72],
        degrees=["R", "3", "5", "7"],
        score=0.0,
        disposition=Disposition.CLOSED,
        metadata={"voicing_method_lock_rescue_runtime_executed": True},
    )

    selected = select_candidate([far_high_score, near_low_score], policy=policy, state=_state())

    assert selected.notes == [61, 65, 68, 72]
    assert selected.metadata["texture_state_rescue_nearest_motion_contract"] == "v2_2_29"
    assert selected.metadata["texture_state_rescue_nearest_motion_applied"] is True
    assert selected.metadata["texture_state_rescue_nearest_motion_candidate_count"] == 2
    assert selected.metadata["texture_state_rescue_nearest_motion_selected_total_motion"] < 10


def test_non_rescue_pool_keeps_normal_selector_behavior() -> None:
    policy = VoicingPolicy(selector_temperature=0.0)
    far_high_score = VoicingCandidate(
        notes=[84, 88, 91, 95],
        degrees=["R", "3", "5", "7"],
        score=20.0,
        disposition=Disposition.CLOSED,
    )
    near_low_score = VoicingCandidate(
        notes=[61, 65, 68, 72],
        degrees=["R", "3", "5", "7"],
        score=0.0,
        disposition=Disposition.CLOSED,
    )

    selected = select_candidate([far_high_score, near_low_score], policy=policy, state=_state())

    assert selected.notes == [84, 88, 91, 95]
    assert "texture_state_rescue_nearest_motion_applied" not in selected.metadata


def test_medium_swing_policy_enables_texture_rescue_nearest_motion() -> None:
    policy = get_medium_swing_voicing_policy()
    assert policy.metadata["texture_state_rescue_nearest_motion_enabled"] is True
    assert "v2_2_29" in policy.metadata["texture_state_rescue_nearest_motion_contract"]


def test_docs_record_texture_state_rescue_nearest_motion_pass() -> None:
    docs = (
        Path("README.md").read_text(encoding="utf-8")
        + Path("docs/VOICING_TEXTURE_STATE_ARCHITECTURE_V2.md").read_text(encoding="utf-8")
        + Path("docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md").read_text(encoding="utf-8")
    )
    assert "v2_2_29" in docs
    assert "Texture-State Rescue / Nearest-Motion" in docs
    assert "texture_state_rescue_nearest_motion" in docs
