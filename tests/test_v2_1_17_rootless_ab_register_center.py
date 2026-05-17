from __future__ import annotations

from pathlib import Path

from jammate_engine.core.gestures.gesture import GestureKind, GestureRequest
from jammate_engine.core.voicing.runtime.override import build_voicing_override_policy
from jammate_engine.core.voicing.runtime.request import VoicingRequest
from jammate_engine.core.voicing.runtime.voicing_resolver import VoicingResolver

ROOT = Path(__file__).resolve().parents[1]


def _rootless_policy():
    return build_voicing_override_policy({}, {"enabled": True, "preset": "rootless_ab_safe"}, style_name="medium_swing")


def test_v2_1_17_rootless_ab_preset_has_centered_register_band() -> None:
    policy = _rootless_policy()

    assert policy.register_low == 52
    assert policy.register_high == 74
    assert policy.top_voice_low == 60
    assert policy.top_voice_high == 74
    assert policy.comfort_register_low == 58
    assert policy.comfort_register_high == 68
    assert policy.max_voicing_span == 18
    assert policy.metadata["rootless_ab_lowest_note_floor"] == 54
    assert policy.metadata["rootless_ab_top_voice_soft_high"] == 72
    assert policy.metadata["rootless_ab_average_pitch_target_low"] == 59
    assert policy.metadata["rootless_ab_average_pitch_target_high"] == 66


def test_v2_1_17_rootless_ab_ii_v_i_stays_centered_without_breaking_aba() -> None:
    policy = _rootless_policy()
    resolver = VoicingResolver()
    gesture = GestureRequest(kind=GestureKind.SIMULTANEOUS_ONSET)
    selected = []

    for symbol in ["Dm7", "G7", "Cmaj7"]:
        plan = resolver.resolve(
            VoicingRequest(
                event_id=symbol,
                chord_symbol=symbol,
                track="piano",
                gesture_type="simultaneous_onset",
                gesture=gesture,
                expression_articulation="sustain",
                ensemble_context={"bass_present": True},
                policy=policy,
            )
        )
        notes = [note.midi_note for note in plan.notes]
        selected.append(plan)
        assert min(notes) >= 54
        assert max(notes) <= 72
        assert 59 <= sum(notes) / len(notes) <= 66
        assert plan.metadata["score_breakdown"]["details"]["rootless_ab_register_center_score"] > 0

    assert [plan.metadata.get("rootless_ab_orientation_family") for plan in selected] == ["A", "B", "A"]
    assert len({plan.metadata.get("rootless_ab_inversion_index") for plan in selected}) == 1


def test_v2_1_17_register_center_rule_is_documented() -> None:
    required_docs = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "VOICING_MODULE_CORE_LOGIC_V2.md",
        ROOT / "docs" / "VOICING_SYSTEM_V2_DESIGN.md",
        ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md",
        ROOT / "docs" / "STYLE_RULE_BASELINE_V2.md",
        ROOT / "docs" / "VOICING_TUNING_WORKFLOW_V2.md",
        ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md",
    ]
    for path in required_docs:
        text = path.read_text(encoding="utf-8")
        assert "v2_1_17" in text, path
        assert "Register Center" in text or "register center" in text, path
        assert "52-74" in text and "60-74" in text, path
        assert "rootless_ab_register_center_score" in text, path
