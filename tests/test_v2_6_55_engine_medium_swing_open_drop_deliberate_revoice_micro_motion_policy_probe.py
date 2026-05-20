from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.core.voicing.policy import VoicingPolicy
from jammate_engine.core.voicing.runtime.plan import VoicedNote, VoicingPlan
from jammate_engine.core.voicing.selection.candidate import VoicingCandidate
from jammate_engine.core.voicing.selection.candidate_generator import _apply_medium_swing_deliberate_revoice_micro_motion_policy
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.realization.realizer_voicing_request_orchestration import policy_with_deliberate_revoice_micro_motion_context
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
LEADSHEETS = ROOT / "examples" / "leadsheets"
DOC = ROOT / "docs" / "ENGINE_VOICING_MEDIUM_SWING_OPEN_DROP_DELIBERATE_REVOICE_MICRO_MOTION_POLICY_PROBE_V2_6_55.md"


def _generate(slug: str, *, tmp_path: Path, seed: int):
    score = json.loads((LEADSHEETS / f"{slug}.json").read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": int(score.get("tempo", 132)),
            "choruses": 3,
            "seed": seed,
            "output_path": str(tmp_path / f"{slug}_v2_6_55.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return build_piano_musical_audit(result.debug)


def _previous_plan() -> VoicingPlan:
    return VoicingPlan(
        event_id="ev1",
        chord_symbol="Cmaj7",
        notes=[
            VoicedNote(midi_note=60, degree="1", voice_role="lowest"),
            VoicedNote(midi_note=64, degree="3", voice_role="inner_1"),
            VoicedNote(midi_note=67, degree="5", voice_role="inner_2"),
            VoicedNote(midi_note=71, degree="7", voice_role="top"),
        ],
        content_family="seventh_basic",
        density=4,
        metadata={"disposition_projection_family": "open", "disposition_projection_method": "drop2"},
    )


def _candidate(notes: list[int], *, method: str = "drop2") -> VoicingCandidate:
    return VoicingCandidate(
        notes=notes,
        degrees=["1", "3", "5", "7"],
        metadata={"disposition_projection_family": "open", "disposition_projection_method": method},
    )


def test_v2_6_55_policy_declares_micro_motion_probe_boundary() -> None:
    metadata = dict(get_voicing_policy().metadata or {})
    target = dict(metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_target") or {})

    assert metadata["medium_swing_deliberate_revoice_micro_motion_policy_version"] == "v2_6_55"
    assert metadata["medium_swing_deliberate_revoice_micro_motion_policy_enabled"] is True
    assert target["scope"] == "same_chord_region_explicit_revoice_micro_motion"
    assert target["allowed_motion_policies"] == ["micro_motion", "inner_motion", "top_voice_answer"]
    assert target["require_foundation_stable"] is True
    assert target["max_low_motion"] == 0
    assert target["max_top_motion"] == 2
    assert target["max_avg_motion"] == 2.5
    assert target["does_not_create_revoice_gestures"] is True
    assert target["does_not_change_pattern_anticipation_expression_or_midi"] is True


def test_v2_6_55_orchestration_attaches_previous_voicing_micro_motion_context() -> None:
    policy = get_voicing_policy()
    out = policy_with_deliberate_revoice_micro_motion_context(
        policy,
        previous_voicing=_previous_plan(),
        request={"motion_policy": "micro_motion", "requested": True},
    )
    metadata = dict(out.metadata or {})

    assert metadata["medium_swing_deliberate_revoice_micro_motion_policy_version"] == "v2_6_55"
    assert metadata["medium_swing_deliberate_revoice_micro_motion_policy_runtime_enabled"] is True
    assert metadata["medium_swing_deliberate_revoice_micro_motion_policy_requested"] is True
    assert metadata["medium_swing_deliberate_revoice_micro_motion_policy_previous_notes"] == [60, 64, 67, 71]
    assert metadata["medium_swing_deliberate_revoice_micro_motion_policy_previous_projection_method"] == "drop2"
    assert metadata["medium_swing_deliberate_revoice_micro_motion_policy_max_top_motion"] == 2


def test_v2_6_55_candidate_filter_keeps_only_safe_micro_motion_candidates() -> None:
    policy = policy_with_deliberate_revoice_micro_motion_context(
        get_voicing_policy(),
        previous_voicing=_previous_plan(),
        request={"motion_policy": "micro_motion", "requested": True},
    )
    candidates = [
        _candidate([60, 65, 67, 73]),  # low stable, top +2, avg small
        _candidate([62, 66, 69, 74]),  # low moves, so not a foundation-stable micro motion
        _candidate([60, 64, 67, 71], method="drop3"),  # wrong projection method for this revoice lane
    ]

    kept = _apply_medium_swing_deliberate_revoice_micro_motion_policy(candidates, policy)

    assert len(kept) == 1
    assert kept[0].notes == [60, 65, 67, 73]
    metadata = dict(kept[0].metadata or {})
    assert metadata["medium_swing_deliberate_revoice_micro_motion_policy_filter_applied"] is True
    assert metadata["medium_swing_deliberate_revoice_micro_motion_policy_filter_reason"] == "filtered_to_safe_micro_motion_candidate"
    assert metadata["medium_swing_deliberate_revoice_micro_motion_policy_candidate_matches"] is True
    assert metadata["medium_swing_deliberate_revoice_micro_motion_policy_low_motion_abs"] == 0
    assert metadata["medium_swing_deliberate_revoice_micro_motion_policy_top_motion_abs"] == 2
    assert metadata["medium_swing_deliberate_revoice_micro_motion_policy_foundation_stable"] is True


def test_v2_6_55_all_the_things_you_are_default_keeps_micro_motion_probe_inactive(tmp_path: Path) -> None:
    audit = _generate("all_the_things_you_are", tmp_path=tmp_path, seed=3300)
    summary = audit.summary

    assert summary["medium_swing_deliberate_revoice_micro_motion_policy_version"] == "v2_6_55"
    assert summary["medium_swing_deliberate_revoice_micro_motion_policy_runtime_enabled_events"] == 0
    assert summary["medium_swing_deliberate_revoice_micro_motion_policy_filter_applied_events"] == 0
    assert summary["medium_swing_deliberate_revoice_micro_motion_policy_warning_events"] == 0
    assert summary["medium_swing_deliberate_revoice_micro_motion_policy_checkpoint_passed"] is True
    assert summary["medium_swing_deliberate_revoice_gesture_boundary_explicit_revoice_events"] == 0


def test_v2_6_55_autumn_leaves_default_keeps_micro_motion_probe_inactive(tmp_path: Path) -> None:
    audit = _generate("autumn_leaves", tmp_path=tmp_path, seed=3301)
    summary = audit.summary

    assert summary["medium_swing_deliberate_revoice_micro_motion_policy_version"] == "v2_6_55"
    assert summary["medium_swing_deliberate_revoice_micro_motion_policy_runtime_enabled_events"] == 0
    assert summary["medium_swing_deliberate_revoice_micro_motion_policy_filter_applied_events"] == 0
    assert summary["medium_swing_deliberate_revoice_micro_motion_policy_warning_events"] == 0
    assert summary["medium_swing_deliberate_revoice_micro_motion_policy_checkpoint_passed"] is True
    assert summary["medium_swing_deliberate_revoice_gesture_boundary_explicit_revoice_events"] == 0


def test_v2_6_55_doc_records_micro_motion_probe() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_55",
        "Deliberate Revoice Micro-Motion Policy Probe",
        "same_chord_region_explicit_revoice_micro_motion",
        "micro_motion",
        "inner_motion",
        "top_voice_answer",
        "foundation stable",
        "max_top_motion",
        "default same-chord reuse",
        "Pattern",
        "Anticipation",
        "Expression",
        "MIDI",
        "Agent",
        "HarmonyOS",
    ):
        assert token in text
