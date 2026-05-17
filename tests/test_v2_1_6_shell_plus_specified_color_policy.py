from pathlib import Path

from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_PRESETS, build_voicing_override_policy
from jammate_engine.core.voicing.selection.selector import select_candidate
from jammate_engine.core.voicing.runtime.state import VoicingState

ROOT = Path(__file__).resolve().parents[1]


def _policy(**override):
    data = {"enabled": True, "preset": "shell_plus_specified_color"}
    data.update(override)
    return build_voicing_override_policy({}, data, style_name="medium_swing")


def _selected(symbol: str, **override):
    policy = _policy(**override)
    return select_candidate(generate_candidates(symbol, policy), policy=policy, state=VoicingState.empty()), policy


def test_shell_plus_specified_color_defaults_to_chord_symbol_only_internal_tones() -> None:
    selected, policy = _selected("G7")

    assert policy.harmonic_expansion_enabled is False
    assert policy.color_policy_mode.value == "chord_symbol_only"
    assert selected.content_family.value == "shell_plus_color"
    assert set(selected.degrees) == {"3", "5", "b7"}
    assert "9" not in selected.degrees
    assert "13" not in selected.degrees
    assert "no_unspecified_color_added" in selected.metadata["content_recipe"]["validity_notes"]


def test_shell_plus_specified_color_must_use_chord_symbol_color_when_present() -> None:
    examples = {
        "Cmaj9": "9",
        "G13": "13",
        "G7b9": "b9",
        "G7#11": "#11",
        "Dm11": "11",
    }
    for symbol, color in examples.items():
        selected, _ = _selected(symbol)
        assert color in selected.degrees, (symbol, selected.degrees)
        assert "explicit_chord_symbol_color_used" in selected.metadata["content_recipe"]["validity_notes"]


def test_shell_plus_specified_color_half_diminished_uses_b3_b7_b5_not_random_color() -> None:
    selected, _ = _selected("Bm7b5")

    assert set(selected.degrees) == {"b3", "b5", "b7"}
    assert "5" not in selected.degrees
    assert "9" not in selected.degrees
    assert "half_diminished_uses_b3_b7_b5" in selected.metadata["content_recipe"]["validity_notes"]


def test_shell_plus_specified_color_diminished_uses_internal_dim_identity_tones() -> None:
    selected, _ = _selected("Cdim7")

    assert set(selected.degrees) == {"b3", "b5", "bb7"}
    assert "diminished_internal_identity_tones" in selected.metadata["content_recipe"]["validity_notes"]


def test_shell_plus_specified_color_allows_unnotated_color_only_when_expansion_enabled() -> None:
    default_selected, _ = _selected("G7")
    expanded_selected, expanded_policy = _selected("G7", harmonic_expansion_enabled=True)

    assert set(default_selected.degrees) == {"3", "5", "b7"}
    assert expanded_policy.harmonic_expansion_enabled is True
    assert any(
        "9" in candidate.degrees or "13" in candidate.degrees
        for candidate in generate_candidates("G7", expanded_policy)
    )
    # v2_1_8: expansion means allowed, not forced; deterministic top choice may
    # remain the internal 5 fallback when it scores as the most stable ordering.
    assert set(expanded_selected.degrees) in ({"3", "b7", "5"}, {"3", "b7", "9"}, {"3", "b7", "13"})


def test_shell_plus_specified_color_aliases_are_available() -> None:
    for preset in (
        "shell_plus_specified_color",
        "shell_plus_color",
        "shell_plus_one_color_note",
        "3_note_shell_color",
        "3_note_guide_shell_with_color",
    ):
        assert preset in VOICING_OVERRIDE_PRESETS


def test_v2_1_6_shell_plus_specified_color_rule_is_documented() -> None:
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
        assert "v2_1_6" in text, path
        assert "shell_plus_specified_color" in text, path
        assert "chord_symbol_only" in text, path
        assert "harmonic_expansion_enabled" in text, path
        assert "b3 + b7 + b5" in text, path
