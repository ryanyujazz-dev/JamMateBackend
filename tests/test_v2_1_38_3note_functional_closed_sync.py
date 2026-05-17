from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION, build_voicing_override_policy
from jammate_engine.core.voicing.selection.selector import select_candidate
from jammate_engine.core.voicing.runtime.state import VoicingState

ROOT = Path(__file__).resolve().parents[1]


def _policy(preset: str = "shell_plus_specified_color"):
    return build_voicing_override_policy({"max_voicing_span": 16}, {"enabled": True, "preset": preset}, style_name="medium_swing")


def test_v2_1_40_versions_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_OVERRIDE_CONTRACT_VERSION == "v2_1_43"


def test_three_note_sources_use_functional_role_metadata() -> None:
    policy = _policy("shell_plus_specified_color")
    candidates = generate_candidates("Cmaj9", policy)
    assert candidates
    for candidate in candidates:
        notes = candidate.metadata["content_recipe"]["validity_notes"]
        assert "three_note_functional_source_family" in notes
        assert "three_note_functional_source_type_third_seventh_ninth" in notes
        assert "three_note_source_role_order_third_seventh_ninth" in notes
        assert "voicing_source_roles_resolved_by_core_harmony" in notes


def test_three_note_strict_closed_filters_before_nearest_motion() -> None:
    policy = _policy("shell_plus_specified_color")
    candidates = generate_candidates("Cmaj9", policy)
    assert candidates
    assert {candidate.disposition.value for candidate in candidates} == {"closed"}
    assert {candidate.density for candidate in candidates} == {3}
    for candidate in candidates:
        assert min(candidate.notes) >= 57
        assert max(candidate.notes) - min(candidate.notes) <= 12
        assert candidate.metadata["strict_closed_compact_pitch_class_layout"] is True

    state = VoicingState(
        previous_notes=(57, 60, 64),
        previous_top_note=64,
        previous_low_note=57,
        previous_chord_symbol="Fmaj7",
        previous_event_id="prev",
    )
    selected = select_candidate(candidates, policy=policy, state=state)
    assert selected.metadata["closed_3note_per_source_minimum_motion"] is True
    assert selected.metadata["closed_3note_source_collapse_candidate_count"] == 3
    assert selected.metadata["closed_3note_source_collapse_selected_total_motion"] == 4.0
    assert selected.notes == [59, 62, 64]


def test_three_note_altered_dominant_does_not_leak_4note_rooted_family() -> None:
    policy = _policy("shell_plus_specified_color")
    candidates = generate_candidates("G7#9", policy)
    assert candidates
    assert {candidate.content_family.value for candidate in candidates} == {"shell_plus_color"}
    for candidate in candidates:
        notes = candidate.metadata["content_recipe"]["validity_notes"]
        assert "three_note_functional_source_type_third_seventh_altered_color" in notes
        assert not any(str(note).startswith("rooted_color_4note") for note in notes)


def test_three_note_directed_color_octave_shift_rule_is_removed_from_runtime() -> None:
    source = (ROOT / "src" / "jammate_engine" / "core" / "voicing" / "selection" / "candidate_generator.py").read_text(encoding="utf-8")
    assert "_color_minor_second_direction_adjustment" not in source
    assert "move color toward the other shell" not in source


def test_v2_1_40_docs_record_3note_closed_contract() -> None:
    required = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "DEVELOPMENT_HARNESS_V2.md",
        ROOT / "docs" / "VOICING_TUNING_WORKFLOW_V2.md",
        ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md",
        ROOT / "docs" / "SYSTEM_CONTRACTS_V2.md",
    ]
    for path in required:
        text = path.read_text(encoding="utf-8")
        assert "v2_1_40" in text, path
        assert "3-note functional closed" in text, path
        assert "closed legality" in text and "nearest motion" in text, path
        assert "directed minor-second" in text and "superseded" in text, path
