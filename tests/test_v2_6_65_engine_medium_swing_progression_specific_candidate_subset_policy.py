from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles.base import _apply_piano_comping_progression_specific_subset_policy
from jammate_engine.styles.medium_swing import arrangement_policy, comping_patterns
from jammate_engine.styles.medium_swing.profile import MediumSwingProfile


def _region(chord: str, prev: str | None, next_: str | None, *, duration: float = 4.0) -> HarmonicRegion:
    return HarmonicRegion(
        region_id=f"r_{chord}",
        chord_symbol=chord,
        next_chord_symbol=next_,
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=0.0,
        duration_beats=duration,
        metadata={"previous_chord_symbol": prev} if prev else {},
    )


def test_v2_6_65_arrangement_policy_declares_progression_subset_without_disabling_existing_layers() -> None:
    policy = arrangement_policy.get_arrangement_policy()
    assert policy["piano_comping_progression_specific_subset_policy"] is True
    assert policy["piano_comping_progression_specific_subset_policy_version"] == "v2_6_65"
    assert policy["piano_comping_harmonic_function_policy"] is True
    assert policy["piano_comping_history_continuity_scorer"] is True
    assert "ChordRegion-first preferred subset" in policy["piano_comping_progression_specific_subset_contract"]


def test_v2_6_65_predominant_to_dominant_prefers_ii_setup_subset_inside_existing_region_pool() -> None:
    region = _region("Dm7", "Cmaj7", "G7")
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    adjusted = _apply_piano_comping_progression_specific_subset_policy(candidates, region=region, context={"region_duration_beats": 4.0})

    rows = {candidate.name: candidate for candidate in adjusted}
    assert any(candidate.metadata.get("progression_specific_subset_policy_applied") for candidate in adjusted)
    assert rows["medium_swing_piano_charleston_1_2and"].metadata["progression_specific_subset_key"] == "ii_setup_region"
    assert rows["medium_swing_piano_charleston_1_2and"].metadata["progression_specific_subset_status"] == "preferred_subset_candidate"
    assert rows["medium_swing_piano_charleston_1_2and"].weight > rows["medium_swing_piano_1_2and_4and_rare_push"].weight
    assert rows["medium_swing_piano_1_2and_4and_rare_push"].metadata["progression_specific_subset_status"] == "fallback_candidate_downweighted"


def test_v2_6_65_dominant_resolution_translates_major_251_without_bar_first_or_texture_logic() -> None:
    region = _region("G7", "Dm7", "Cmaj7")
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    adjusted = _apply_piano_comping_progression_specific_subset_policy(candidates, region=region, context={"region_duration_beats": 4.0})
    preferred = [candidate for candidate in adjusted if "preferred" in str(candidate.metadata.get("progression_specific_subset_status"))]

    assert preferred
    assert {candidate.metadata["progression_specific_subset_key"] for candidate in adjusted} == {"major_251_dominant_region"}
    for candidate in adjusted:
        text = " ".join([candidate.name, candidate.category, str(candidate.metadata), " ".join(candidate.tags)])
        assert "two_chord_bar" not in text
        assert "split_bar" not in text
        assert "rootless4" not in text
        assert "shell2" not in text
        for event in candidate.events:
            assert "velocity" not in event.metadata
            assert "duration" not in event.metadata
            assert "pedal" not in event.metadata


def test_v2_6_65_plan_region_stamps_progression_subset_metadata_on_runtime_events() -> None:
    profile = MediumSwingProfile()
    region = _region("G7", "Dm7", "Cmaj7")
    plan = profile.plan_region(region, {"style_pattern_history": {}})
    piano_events = [event for event in plan.events if event.track == "piano"]
    assert piano_events
    assert any(event.metadata.get("progression_specific_subset_policy_version") == "v2_6_65" for event in piano_events)
    assert any(event.metadata.get("progression_specific_subset_policy_applied") for event in piano_events)
    assert all(event.metadata.get("time_reference") == "region_local_beats" for event in piano_events)


def test_v2_6_65_audit_script_static_acceptance_without_generating_demos() -> None:
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_medium_swing_piano_progression_subset_audit.py"
    spec = importlib.util.spec_from_file_location("generate_medium_swing_piano_progression_subset_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    static = module.build_static_progression_subset_audit()
    assert static["checkpoint_version"] == "v2_6_65"
    assert static["progression_specific_subset_policy_version"] == "v2_6_65"
    assert static["forbidden_pattern_expression_key_candidates"] == []
    assert static["bar_first_two_chord_bar_candidates"] == []
    assert module._acceptance(static, [])["passed"] is True
