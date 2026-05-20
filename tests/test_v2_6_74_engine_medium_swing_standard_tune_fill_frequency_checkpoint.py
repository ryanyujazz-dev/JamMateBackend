from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles.base import _apply_piano_comping_optional_fill_variation_vocabulary_policy
from jammate_engine.styles.medium_swing import arrangement_policy, comping_patterns
from jammate_engine.styles.medium_swing.profile import MediumSwingProfile

SOURCE_KEY = "medium_swing:0:jammate_engine.styles.medium_swing.comping_patterns.get_pattern_candidates"


def _region(
    chord: str = "G7",
    prev: str | None = "Dm7",
    next_: str | None = "Cmaj7",
    *,
    duration: float = 4.0,
    source_bar_index: int = 3,
    is_last_region_of_bar: bool = True,
    is_section_end: bool = False,
    is_ending: bool = False,
    metadata: dict | None = None,
) -> HarmonicRegion:
    return HarmonicRegion(
        region_id=f"r_{chord}_{source_bar_index}_{'ending' if is_ending else 'middle'}",
        chord_symbol=chord,
        next_chord_symbol=next_,
        chorus_index=0,
        bar_index=source_bar_index,
        chord_index=0,
        start_beat=float(source_bar_index * 4),
        duration_beats=duration,
        source_bar_index=source_bar_index,
        bar_local_start_beat=1.0,
        bar_local_end_beat=1.0 + duration,
        is_first_region_of_bar=True,
        is_last_region_of_bar=is_last_region_of_bar,
        is_last_bar_of_section=is_section_end,
        is_last_bar_of_chorus=is_ending,
        metadata={"previous_chord_symbol": prev, **dict(metadata or {})} if prev else dict(metadata or {}),
    )


def _rows_by_name(candidates):
    return {candidate.name: candidate for candidate in candidates}


def test_v2_6_74_policy_declares_audit_only_fill_frequency_checkpoint() -> None:
    policy = arrangement_policy.get_arrangement_policy()

    assert policy["piano_comping_optional_fill_variation_vocabulary_policy_version"] == "v2_6_71"
    assert policy["piano_comping_optional_fill_variation_listening_refinement_policy_version"] == "v2_6_72"
    assert policy["piano_comping_phrase_end_fill_context_precision_policy_version"] == "v2_6_73"
    assert policy["piano_comping_standard_tune_fill_frequency_checkpoint"] is True
    assert policy["piano_comping_standard_tune_fill_frequency_checkpoint_version"] == "v2_6_74"
    assert "behavior-preserving standard-tune fill-frequency checkpoint" in policy["piano_comping_standard_tune_fill_frequency_checkpoint_contract"]
    assert "without changing weights" in policy["piano_comping_standard_tune_fill_frequency_checkpoint_contract"]
    assert policy["piano_comping_standard_tune_fill_frequency_checkpoint_milestone"] == "v2_6_74_medium_swing_standard_tune_fill_frequency_checkpoint"


def test_v2_6_74_does_not_expand_optional_vocabulary_or_add_bar_first_markers() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    optional = [candidate for candidate in candidates if candidate.metadata.get("optional_fill_variation_vocabulary_candidate")]

    assert {candidate.name for candidate in optional} == {
        "medium_swing_piano_optional_variation_1_2and_3and",
        "medium_swing_piano_optional_fill_2and_4_4and",
        "medium_swing_piano_optional_busy_1and_2and_3and_4",
    }
    assert len(optional) == 3
    assert all(candidate.metadata["optional_fill_variation_vocabulary_version"] == "v2_6_71" for candidate in optional)
    assert all(candidate.metadata["time_reference"] == "region_local_beats" for candidate in optional)

    forbidden_expression = {"velocity", "duration", "duration_beats", "pedal", "release_beats", "accent", "midi_note"}
    forbidden_voicing = {"midi_notes", "notes", "degrees", "chord_tones", "voicing", "content_family", "disposition"}
    for candidate in optional:
        text = " ".join([candidate.name, candidate.category, str(candidate.metadata), " ".join(candidate.tags)])
        assert "two_chord_bar" not in text
        assert "split_bar" not in text
        assert forbidden_expression.isdisjoint(candidate.metadata)
        assert forbidden_voicing.isdisjoint(candidate.metadata)
        for event in candidate.events:
            assert forbidden_expression.isdisjoint(event.metadata)
            assert forbidden_voicing.isdisjoint(event.metadata)


def test_v2_6_74_stamps_checkpoint_metadata_without_changing_v2_6_73_weights() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    phrase_tail = _apply_piano_comping_optional_fill_variation_vocabulary_policy(
        candidates,
        region=_region(source_bar_index=3, is_last_region_of_bar=True),
        context={"region_duration_beats": 4.0},
        history={},
        source_key=SOURCE_KEY,
    )
    harmonic_only = _apply_piano_comping_optional_fill_variation_vocabulary_policy(
        candidates,
        region=_region(source_bar_index=1, is_last_region_of_bar=True),
        context={"region_duration_beats": 4.0},
        history={},
        source_key=SOURCE_KEY,
    )
    fill_name = "medium_swing_piano_optional_fill_2and_4_4and"
    phrase_rows = _rows_by_name(phrase_tail)
    harmonic_rows = _rows_by_name(harmonic_only)

    assert phrase_rows[fill_name].metadata["standard_tune_fill_frequency_checkpoint_version"] == "v2_6_74"
    assert phrase_rows[fill_name].metadata["standard_tune_fill_frequency_checkpoint_scope"] == "audit_only_no_behavior_change"
    assert phrase_rows[fill_name].metadata["phrase_end_fill_context_precision_policy_version"] == "v2_6_73"
    assert "transition_fill_clear_phrase_end_history_micro_bonus_v2_6_73" in phrase_rows[fill_name].metadata["optional_fill_variation_reasons"]
    assert "transition_fill_harmonic_only_context_precision_downweight_v2_6_73" in harmonic_rows[fill_name].metadata["optional_fill_variation_reasons"]
    assert phrase_rows[fill_name].weight > harmonic_rows[fill_name].weight


def test_v2_6_74_plan_region_stamps_checkpoint_metadata_without_pattern_expression_or_voicing_leakage() -> None:
    profile = MediumSwingProfile()
    plan = profile.plan_region(_region(source_bar_index=3), {"style_pattern_history": {}})
    piano_events = [event for event in plan.events if event.track == "piano"]

    assert piano_events
    assert all(event.metadata.get("optional_fill_variation_policy_version") == "v2_6_71" for event in piano_events)
    assert all(event.metadata.get("optional_fill_variation_listening_refinement_policy_version") == "v2_6_72" for event in piano_events)
    assert all(event.metadata.get("phrase_end_fill_context_precision_policy_version") == "v2_6_73" for event in piano_events)
    assert all(event.metadata.get("standard_tune_fill_frequency_checkpoint_version") == "v2_6_74" for event in piano_events)
    assert all(event.metadata.get("time_reference") == "region_local_beats" for event in piano_events)
    assert all("velocity" not in event.metadata for event in piano_events)
    assert all("duration" not in event.metadata for event in piano_events)
    assert all("voicing" not in event.metadata for event in piano_events)


def test_v2_6_74_audit_script_static_acceptance_without_generating_demos() -> None:
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_medium_swing_standard_tune_fill_frequency_checkpoint.py"
    spec = importlib.util.spec_from_file_location("generate_medium_swing_standard_tune_fill_frequency_checkpoint", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    static = module.build_static_audit()

    assert static["checkpoint_version"] == "v2_6_74"
    assert static["checkpoint_policy_enabled"] is True
    assert static["checkpoint_policy_version"] == "v2_6_74"
    assert static["optional_policy_version"] == "v2_6_71"
    assert static["optional_refinement_policy_version"] == "v2_6_72"
    assert static["phrase_end_precision_policy_version"] == "v2_6_73"
    assert static["optional_candidate_count"] == 3
    assert static["pattern_forbidden_expression_candidates"] == []
    assert static["pattern_forbidden_voicing_candidates"] == []
    assert static["bar_first_two_chord_bar_candidates"] == []
    assert module._frequency_band(0.01) == "very_low_intrusion"
    assert module._acceptance(static, [])["passed"] is True
