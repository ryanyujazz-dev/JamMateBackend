from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles.base import _apply_piano_comping_optional_fill_variation_vocabulary_policy
from jammate_engine.styles.medium_swing import arrangement_policy, comping_patterns
from jammate_engine.styles.medium_swing.profile import MediumSwingProfile

SOURCE_KEY = "medium_swing:0:jammate_engine.styles.medium_swing.comping_patterns.get_pattern_candidates"


def _region(
    chord: str = "Cmaj7",
    prev: str | None = "G7",
    next_: str | None = "Fmaj7",
    *,
    duration: float = 4.0,
    is_section_end: bool = False,
    is_ending: bool = False,
) -> HarmonicRegion:
    return HarmonicRegion(
        region_id=f"r_{chord}_{'ending' if is_ending else 'middle'}",
        chord_symbol=chord,
        next_chord_symbol=next_,
        chorus_index=0,
        bar_index=31 if is_ending else 12,
        chord_index=0,
        start_beat=0.0,
        duration_beats=duration,
        is_last_bar_of_section=is_section_end,
        is_last_bar_of_chorus=is_ending,
        metadata={"previous_chord_symbol": prev} if prev else {},
    )


def _rows_by_name(candidates):
    return {candidate.name: candidate for candidate in candidates}


def test_v2_6_72_policy_declares_refinement_without_replacing_v2_6_71_vocabulary() -> None:
    policy = arrangement_policy.get_arrangement_policy()

    assert policy["piano_comping_optional_fill_variation_vocabulary_policy_version"] == "v2_6_71"
    assert policy["piano_comping_optional_fill_variation_listening_refinement_policy"] is True
    assert policy["piano_comping_optional_fill_variation_listening_refinement_policy_version"] == "v2_6_72"
    assert "keeps the v2_6_71 optional vocabulary unchanged" in policy["piano_comping_optional_fill_variation_listening_refinement_contract"]
    assert "busy fill stays near-blocked" in policy["piano_comping_optional_fill_variation_listening_refinement_contract"]
    assert policy["piano_comping_optional_fill_variation_listening_refinement_milestone"] == "v2_6_72_medium_swing_fill_variation_listening_refinement_after_user_review"


def test_v2_6_72_comping_library_keeps_only_the_three_existing_pitchless_optional_candidates() -> None:
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
        assert forbidden_expression.isdisjoint(candidate.metadata)
        assert forbidden_voicing.isdisjoint(candidate.metadata)
        for event in candidate.events:
            assert forbidden_expression.isdisjoint(event.metadata)
            assert forbidden_voicing.isdisjoint(event.metadata)


def test_v2_6_72_refines_variation_fill_busy_context_weights_inside_existing_policy_path() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    generic = _apply_piano_comping_optional_fill_variation_vocabulary_policy(
        candidates,
        region=_region(is_section_end=False),
        context={"region_duration_beats": 4.0},
        history={},
        source_key=SOURCE_KEY,
    )
    section_end = _apply_piano_comping_optional_fill_variation_vocabulary_policy(
        candidates,
        region=_region(is_section_end=True),
        context={"region_duration_beats": 4.0},
        history={},
        source_key=SOURCE_KEY,
    )
    ending = _apply_piano_comping_optional_fill_variation_vocabulary_policy(
        candidates,
        region=_region(is_ending=True),
        context={"region_duration_beats": 4.0},
        history={},
        source_key=SOURCE_KEY,
    )
    generic_rows = _rows_by_name(generic)
    section_rows = _rows_by_name(section_end)
    ending_rows = _rows_by_name(ending)

    variation_name = "medium_swing_piano_optional_variation_1_2and_3and"
    fill_name = "medium_swing_piano_optional_fill_2and_4_4and"
    busy_name = "medium_swing_piano_optional_busy_1and_2and_3and_4"

    assert generic_rows[variation_name].metadata["optional_fill_variation_policy_version"] == "v2_6_71"
    assert generic_rows[variation_name].metadata["optional_fill_variation_listening_refinement_policy_version"] == "v2_6_72"
    assert "generic_light_variation_low_frequency_allowance_v2_6_72" in generic_rows[variation_name].metadata["optional_fill_variation_reasons"]
    assert "section_end_transition_fill_phrase_end_bonus_v2_6_72" in section_rows[fill_name].metadata["optional_fill_variation_reasons"]
    assert section_rows[fill_name].weight > generic_rows[fill_name].weight
    assert ending_rows[fill_name].weight < section_rows[fill_name].weight
    assert ending_rows[fill_name].metadata["optional_fill_variation_status"] == "optional_ending_controlled"
    assert generic_rows[busy_name].metadata["optional_fill_variation_multiplier"] < 0.1


def test_v2_6_72_recent_history_keeps_transition_fill_and_busy_guarded() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    clean = _apply_piano_comping_optional_fill_variation_vocabulary_policy(
        candidates,
        region=_region(is_section_end=True),
        context={"region_duration_beats": 4.0},
        history={},
        source_key=SOURCE_KEY,
    )
    history = {
        f"{SOURCE_KEY}:recent_comping": [
            {"name": "previous_fill", "continuity_class": "fill", "is_fill": True, "is_active": True, "is_busy": False, "is_push": False, "is_tail_push": False},
            {"name": "previous_active", "continuity_class": "active", "is_fill": False, "is_active": True, "is_busy": False, "is_push": False, "is_tail_push": False},
        ]
    }
    guarded = _apply_piano_comping_optional_fill_variation_vocabulary_policy(
        candidates,
        region=_region(is_section_end=True),
        context={"region_duration_beats": 4.0},
        history=history,
        source_key=SOURCE_KEY,
    )
    clean_rows = _rows_by_name(clean)
    guarded_rows = _rows_by_name(guarded)
    fill_name = "medium_swing_piano_optional_fill_2and_4_4and"
    busy_name = "medium_swing_piano_optional_busy_1and_2and_3and_4"

    assert guarded_rows[fill_name].weight < clean_rows[fill_name].weight
    assert "optional_recent_fill_memory_guard" in guarded_rows[fill_name].metadata["optional_fill_variation_reasons"]
    assert guarded_rows[busy_name].weight < clean_rows[busy_name].weight
    assert "busy_fill_after_recent_activity_extra_guard_v2_6_72" in guarded_rows[busy_name].metadata["optional_fill_variation_reasons"]


def test_v2_6_72_plan_region_stamps_refinement_metadata_without_pattern_expression_or_voicing_leakage() -> None:
    profile = MediumSwingProfile()
    plan = profile.plan_region(_region(is_section_end=True), {"style_pattern_history": {}})
    piano_events = [event for event in plan.events if event.track == "piano"]

    assert piano_events
    assert all(event.metadata.get("optional_fill_variation_policy_version") == "v2_6_71" for event in piano_events)
    assert all(event.metadata.get("optional_fill_variation_listening_refinement_policy_version") == "v2_6_72" for event in piano_events)
    assert all(event.metadata.get("time_reference") == "region_local_beats" for event in piano_events)
    assert all("velocity" not in event.metadata for event in piano_events)
    assert all("duration" not in event.metadata for event in piano_events)
    assert all("voicing" not in event.metadata for event in piano_events)


def test_v2_6_72_audit_script_static_acceptance_without_generating_demos() -> None:
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_medium_swing_fill_variation_listening_refinement_audit.py"
    spec = importlib.util.spec_from_file_location("generate_medium_swing_fill_variation_listening_refinement_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    static = module.build_static_audit()

    assert static["checkpoint_version"] == "v2_6_72"
    assert static["optional_policy_version"] == "v2_6_71"
    assert static["optional_refinement_policy_enabled"] is True
    assert static["optional_refinement_policy_version"] == "v2_6_72"
    assert static["optional_candidate_count"] == 3
    assert static["pattern_forbidden_expression_candidates"] == []
    assert static["pattern_forbidden_voicing_candidates"] == []
    assert static["bar_first_two_chord_bar_candidates"] == []
    assert module._acceptance(static, [])["passed"] is True
