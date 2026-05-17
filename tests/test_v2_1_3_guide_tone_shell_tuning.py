from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.runtime.override import build_voicing_override_policy
from jammate_engine.core.voicing.selection.selector import select_candidate
from jammate_engine.core.voicing.runtime.state import VoicingState


def _guide_policy():
    return build_voicing_override_policy(
        {},
        {"enabled": True, "preset": "2_note_shell"},
        style_name="medium_swing",
    )


def test_two_note_shell_generates_mixed_octave_guide_tone_inversion():
    policy = _guide_policy()
    candidates = generate_candidates("G7", policy)
    candidate_keys = {(tuple(candidate.degrees), tuple(candidate.notes)) for candidate in candidates}

    # G7 guide tones should include B3-F4, not only F4-B4 or F3-B3.
    assert (("3", "b7"), (59, 65)) in candidate_keys


def test_two_note_shell_prefers_common_tone_guide_voice_leading():
    policy = _guide_policy()
    state = VoicingState.empty().advance(
        event_id="prev",
        chord_symbol="Dm7",
        notes=[60, 65],  # C4-F4, a common ii-7 shell realization.
        degrees=["b7", "b3"],
    )

    selected = select_candidate(generate_candidates("G7", policy), policy=policy, state=state)

    # Dm7 C-F -> G7 B-F: one common tone and one half-step resolution.
    assert selected.degrees == ["3", "b7"]
    assert selected.notes == [59, 65]
    assert selected.voice_leading_profile["smoothness_label"] == "smooth"
    assert selected.voice_leading_profile["voice_leading_distance"] <= 1.0


def test_two_note_shell_preset_alias_accepts_guide_tone_name():
    policy = build_voicing_override_policy(
        {},
        {"enabled": True, "preset": "2_note_guide_tone_shell"},
        style_name="medium_swing",
    )

    assert policy.preferred_density == 2
    assert policy.min_density == 2
    assert policy.max_density == 2
    assert policy.metadata["voicing_override_preset"] == "2_note_guide_tone_shell"



def test_v2_1_3_rules_are_recorded_in_baseline_docs():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    baseline = (root / "docs" / "STYLE_RULE_BASELINE_V2.md").read_text(encoding="utf-8")
    summary = (root / "docs" / "GENERATION_RULES_SUMMARY_V2.md").read_text(encoding="utf-8")

    for token in (
        "v2_1_3",
        "2-note Guide-Tone Shell",
        "B3-F4",
        "common-tone",
        "2_note_guide_tone_shell",
        "All the Things You Are",
        "BassFoundation",
    ):
        assert token in baseline
        assert token in summary
