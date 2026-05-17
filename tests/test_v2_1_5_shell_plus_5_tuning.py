from pathlib import Path

from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_PRESETS, build_voicing_override_policy
from jammate_engine.core.voicing.selection.selector import select_candidate
from jammate_engine.core.voicing.runtime.state import VoicingState

ROOT = Path(__file__).resolve().parents[1]


def _policy():
    return build_voicing_override_policy(
        {},
        {"enabled": True, "preset": "shell_plus_5"},
        style_name="medium_swing",
    )


def test_shell_plus_5_preset_is_three_note_rootless_not_triad() -> None:
    policy = _policy()
    selected = select_candidate(generate_candidates("Cmaj7", policy), policy=policy, state=VoicingState.empty())

    assert policy.preferred_density == 3
    assert policy.min_density == 3
    assert policy.max_density == 3
    assert policy.metadata["tuning_target"] == "shell_plus_1or5"
    assert policy.metadata["legacy_alias"] == "shell_plus_5"
    assert selected.content_family.value == "shell_plus_5"
    assert len(selected.notes) == 3
    assert "R" not in selected.degrees
    assert set(selected.degrees) == {"3", "5", "7"}


def test_shell_plus_5_uses_quality_correct_fifth_for_half_diminished() -> None:
    policy = _policy()
    selected = select_candidate(generate_candidates("Bm7b5", policy), policy=policy, state=VoicingState.empty())

    assert selected.content_family.value == "shell_plus_5"
    assert set(selected.degrees) == {"b3", "b5", "b7"}
    assert "5" not in selected.degrees
    assert "R" not in selected.degrees
    assert "half_diminished_b5_retained" in selected.metadata["content_recipe"]["validity_notes"]


def test_shell_plus_5_keeps_smooth_ii_v_i_guide_tone_motion() -> None:
    policy = _policy()
    state = VoicingState.empty()

    dm = select_candidate(generate_candidates("Dm7", policy), policy=policy, state=state)
    state = state.advance(event_id="dm", chord_symbol="Dm7", notes=dm.notes, degrees=dm.degrees)
    g = select_candidate(generate_candidates("G7", policy), policy=policy, state=state)
    state = state.advance(event_id="g", chord_symbol="G7", notes=g.notes, degrees=g.degrees)
    c = select_candidate(generate_candidates("Cmaj7", policy), policy=policy, state=state)

    assert set(dm.degrees) == {"b3", "5", "b7"}
    assert set(g.degrees) == {"3", "5", "b7"}
    assert set(c.degrees) == {"3", "5", "7"}
    assert g.voice_leading_profile["smoothness_label"] == "smooth"
    assert g.voice_leading_profile["common_tones"] >= 1
    assert g.voice_leading_profile["voice_leading_distance"] <= 2.0
    assert c.voice_leading_profile["smoothness_label"] == "smooth"


def test_shell_plus_5_aliases_are_available() -> None:
    assert "shell_plus_5" in VOICING_OVERRIDE_PRESETS
    assert "3_note_shell_5" in VOICING_OVERRIDE_PRESETS
    assert "3_note_guide_shell_with_5" in VOICING_OVERRIDE_PRESETS
    assert "shell_plus_1or5" in VOICING_OVERRIDE_PRESETS
    assert "root_plus_3_10" not in VOICING_OVERRIDE_PRESETS


def test_v2_1_5_shell_plus_5_rule_is_documented() -> None:
    required_docs = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "VOICING_TUNING_WORKFLOW_V2.md",
        ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md",
        ROOT / "docs" / "STYLE_RULE_BASELINE_V2.md",
        ROOT / "docs" / "VOICING_SYSTEM_V2_DESIGN.md",
        ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md",
    ]
    for path in required_docs:
        text = path.read_text(encoding="utf-8")
        assert "v2_1_5" in text, path
        assert "shell_plus_5" in text, path
        assert "3rd + 7th + 5th" in text or "3 + 7 + 5" in text, path
        assert "not a triad" in text or "不是 triad" in text or "不是三和弦" in text, path
