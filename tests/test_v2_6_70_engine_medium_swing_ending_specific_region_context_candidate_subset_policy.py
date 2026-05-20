from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles.base import _apply_piano_comping_ending_specific_subset_policy
from jammate_engine.styles.medium_swing import arrangement_policy, comping_patterns
from jammate_engine.styles.medium_swing.profile import MediumSwingProfile


def _region(
    chord: str,
    prev: str | None,
    next_: str | None,
    *,
    duration: float = 4.0,
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
        is_last_bar_of_chorus=is_ending,
        metadata={"previous_chord_symbol": prev} if prev else {},
    )


def test_v2_6_70_arrangement_policy_declares_ending_specific_subset_without_disabling_prior_layers() -> None:
    policy = arrangement_policy.get_arrangement_policy()

    assert policy["piano_comping_ending_specific_subset_policy"] is True
    assert policy["piano_comping_ending_specific_subset_policy_version"] == "v2_6_70"
    assert "existing ChordRegion-length pool" in policy["piano_comping_ending_specific_subset_contract"]
    assert "does not add an ending selector" in policy["piano_comping_ending_specific_subset_contract"]
    assert policy["piano_comping_progression_specific_subset_policy_version"] == "v2_6_65"
    assert policy["piano_comping_active_fill_busy_multi_region_history_scorer_version"] == "v2_6_67"
    assert policy["piano_expression_policy_v1_numeric_calibration_version"] == "v2_6_68"
    assert policy["piano_comping_ending_specific_subset_milestone"] == "v2_6_70_medium_swing_ending_specific_region_context_candidate_subset_policy"


def test_v2_6_70_ending_region_prefers_stable_settle_and_controls_4and_push_inside_existing_pool() -> None:
    region = _region("Cmaj7", "G7", None, is_ending=True)
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    adjusted = _apply_piano_comping_ending_specific_subset_policy(candidates, region=region, context={"region_duration_beats": 4.0})
    rows = {candidate.name: candidate for candidate in adjusted}

    anchor = rows["medium_swing_piano_anchor_1"]
    push = rows["medium_swing_piano_1_4and_rare_push"]
    offbeat = rows["medium_swing_piano_light_2and_only"]
    tail = rows["medium_swing_piano_backbeat_2_4"]

    assert anchor.metadata["ending_specific_subset_policy_version"] == "v2_6_70"
    assert anchor.metadata["ending_specific_subset_policy_applied"] is True
    assert anchor.metadata["ending_specific_subset_status"] == "ending_settle_anchor_preferred"
    assert anchor.weight > push.weight
    assert push.metadata["ending_specific_subset_status"] == "ending_tail_push_near_block"
    assert push.metadata["ending_specific_subset_multiplier"] < 0.2
    assert offbeat.metadata["ending_specific_subset_status"] == "ending_offbeat_without_anchor_downweighted"
    assert tail.metadata["ending_specific_subset_status"] == "ending_tail_support_allowed"

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


def test_v2_6_70_non_ending_region_is_audited_but_not_reweighted() -> None:
    region = _region("Cmaj7", "G7", "Fmaj7", is_ending=False)
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    adjusted = _apply_piano_comping_ending_specific_subset_policy(candidates, region=region, context={"region_duration_beats": 4.0})

    assert [candidate.weight for candidate in adjusted] == [candidate.weight for candidate in candidates]
    assert all(candidate.metadata["ending_specific_subset_policy_version"] == "v2_6_70" for candidate in adjusted)
    assert all(candidate.metadata["ending_specific_subset_policy_applied"] is False for candidate in adjusted)
    assert {candidate.metadata["ending_specific_subset_status"] for candidate in adjusted} == {"non_ending_context_passthrough"}


def test_v2_6_70_plan_region_stamps_runtime_events_from_existing_profile_path() -> None:
    profile = MediumSwingProfile()
    region = _region("Cmaj7", "G7", None, is_ending=True)
    plan = profile.plan_region(region, {"style_pattern_history": {}})
    piano_events = [event for event in plan.events if event.track == "piano"]

    assert piano_events
    assert any(event.metadata.get("ending_specific_subset_policy_version") == "v2_6_70" for event in piano_events)
    assert any(event.metadata.get("ending_specific_subset_policy_applied") is True for event in piano_events)
    assert all(event.metadata.get("time_reference") == "region_local_beats" for event in piano_events)
    assert all("voicing" not in event.metadata for event in piano_events)
    assert all("velocity" not in event.metadata for event in piano_events)


def test_v2_6_70_audit_script_static_acceptance_without_generating_demos() -> None:
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_medium_swing_ending_specific_subset_audit.py"
    spec = importlib.util.spec_from_file_location("generate_medium_swing_ending_specific_subset_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    static = module.build_static_audit()

    assert static["checkpoint_version"] == "v2_6_70"
    assert static["ending_specific_policy_version"] == "v2_6_70"
    assert static["missing_or_mismatched_prior_policy_versions"] == {}
    assert static["pattern_forbidden_expression_candidates"] == []
    assert static["pattern_forbidden_voicing_candidates"] == []
    assert static["bar_first_two_chord_bar_candidates"] == []
    assert module._acceptance(static, [])["passed"] is True
