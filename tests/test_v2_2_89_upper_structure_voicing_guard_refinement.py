from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    LOW_REGISTER_SINGLE_NOTE_GUARD_VERSION,
    LOW_REGISTER_SINGLE_NOTE_THRESHOLD,
    MAX_NOTES_BELOW_LOW_REGISTER_SINGLE_NOTE_THRESHOLD,
    ColorPolicyMode,
    ContentFamily,
    Disposition,
    VoicingCandidate,
    VoicingPolicy,
    evaluate_register_guard,
)
from jammate_engine.core.voicing.selection.scorer import (
    UPPER_STRUCTURE_REGISTER_REFINEMENT_VERSION,
    score_candidate,
)
from jammate_engine.styles.bossa_nova.voicing_policy import get_voicing_policy as bossa_policy
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy as ballad_policy
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as swing_policy

ROOT = Path(__file__).resolve().parents[1]


def _upper_structure_candidate(notes: list[int]) -> VoicingCandidate:
    return VoicingCandidate(
        notes=notes,
        degrees=["3", "b9", "#9"],
        content_family=ContentFamily.ROOTED_COLOR,
        disposition=Disposition.OPEN,
        metadata={
            "symbol": "G7",
            "content_recipe": {
                "validity_notes": [
                    "upper_structure_source_family",
                    "upper_structure_profile_kind_altered",
                ],
            },
        },
    )


def _policy() -> VoicingPolicy:
    return VoicingPolicy(
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        register_low=36,
        register_high=84,
        top_voice_low=58,
        top_voice_high=78,
        comfort_register_low=52,
        comfort_register_high=70,
        metadata={
            "upper_structure_register_refinement_enabled": True,
            "upper_structure_top_soft_high": 74,
            "upper_structure_top_hard_high": 78,
            "upper_structure_average_pitch_soft_high": 68,
            "low_register_single_note_threshold": 40,
            "max_notes_below_low_register_single_note_threshold": 1,
        },
    )


def test_low_register_single_note_guard_rejects_two_notes_below_threshold() -> None:
    guard = evaluate_register_guard([36, 39, 55, 62], _policy())
    debug = guard.to_debug_dict()
    assert LOW_REGISTER_SINGLE_NOTE_GUARD_VERSION == "v2_2_89"
    assert LOW_REGISTER_SINGLE_NOTE_THRESHOLD == 40
    assert MAX_NOTES_BELOW_LOW_REGISTER_SINGLE_NOTE_THRESHOLD == 1
    assert debug["low_register_single_note_count"] == 2
    assert debug["low_register_single_note_ok"] is False
    assert debug["passed"] is False
    assert "low_register_single_note_guard" in debug["reasons"]


def test_low_register_single_note_guard_uses_policy_metadata_threshold() -> None:
    policy = VoicingPolicy(
        register_low=36,
        register_high=84,
        metadata={
            "low_register_single_note_threshold": 48,
            "max_notes_below_low_register_single_note_threshold": 1,
        },
    )
    guard = evaluate_register_guard([43, 47, 60], policy)
    assert guard.low_register_single_note_threshold == 48
    assert guard.low_register_single_note_count == 2
    assert guard.low_register_single_note_ok is False


def test_upper_structure_register_refinement_penalizes_sharp_top_notes() -> None:
    policy = _policy()
    warm = score_candidate(_upper_structure_candidate([60, 66, 72]), policy)
    sharp = score_candidate(_upper_structure_candidate([64, 70, 82]), policy)
    assert warm.details["upper_structure_register_refinement_version"] == UPPER_STRUCTURE_REGISTER_REFINEMENT_VERSION
    assert warm.details["upper_structure_register_score"] > sharp.details["upper_structure_register_score"]
    assert sharp.details["upper_structure_register_score"] < 0.0


def test_style_policies_publish_upper_structure_register_refinement_metadata() -> None:
    swing = swing_policy().metadata or {}
    ballad = ballad_policy().metadata or {}
    bossa = bossa_policy().metadata or {}
    assert swing["upper_structure_register_refinement"]["version"] == "v2_2_89"
    assert ballad["upper_structure_top_soft_high"] <= ballad["upper_structure_top_hard_high"]
    assert bossa["upper_structure_top_soft_high"] < swing["upper_structure_top_soft_high"]
    for metadata in (swing, ballad, bossa):
        assert metadata["upper_structure_register_refinement_enabled"] is True
        assert metadata["low_register_single_note_threshold"] == 40
        assert metadata["max_notes_below_low_register_single_note_threshold"] == 1


def test_v2_2_89_contract_and_docs_are_updated() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"
    docs = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md",
        ROOT / "docs" / "UPPER_STRUCTURE_VOICING_GUARD_REFINEMENT_V2_2_89.md",
    ]
    for path in docs:
        text = path.read_text(encoding="utf-8")
        assert "v2_2_89" in text, path
        assert "Upper Structure / Voicing Guard Listening Refinement" in text, path
        assert "low_register_single_note" in text or "single-low-note" in text, path
