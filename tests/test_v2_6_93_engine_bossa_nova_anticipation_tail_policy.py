from __future__ import annotations

import importlib.util
import random
from dataclasses import replace
from pathlib import Path

from jammate_engine.core.anticipation import AnticipationResolver
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles.bossa_nova import anticipation_policy, arrangement_policy, comping_patterns
from jammate_engine.styles.registry import get_style

MILESTONE_ID = "v2_6_93"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_anticipation_tail_policy_audit.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_anticipation_tail_policy_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _region(region_id: str, chord: str, start: float, duration: float, *, chorus_index: int = 0, total_choruses: int = 3) -> HarmonicRegion:
    return HarmonicRegion(
        region_id=region_id,
        chord_symbol=chord,
        next_chord_symbol=None,
        chorus_index=chorus_index,
        total_choruses=total_choruses,
        bar_index=int(start // 4),
        chord_index=0,
        start_beat=start,
        duration_beats=duration,
        source_bar_index=int(start // 4),
        performance_bar_index=int(start // 4),
    )


def _candidate(name: str):
    for candidate in comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0}, apply_context_policy=False):
        if candidate.name == name:
            return candidate
    raise AssertionError(f"candidate not found: {name}")


def test_v2_6_93_bossa_arrangement_and_policy_metadata_are_registered() -> None:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()
    anticipation = anticipation_policy.get_anticipation_policy()

    assert style.arrangement_policy == policy
    assert policy["bossa_nova_anticipation_tail_policy_active"] is True
    assert policy["bossa_nova_anticipation_tail_policy_version"] == MILESTONE_ID
    assert policy["bossa_nova_anticipation_tail_policy_no_parallel_engine"] is True
    assert policy["bossa_nova_anticipation_tail_policy_no_pattern_embedded_anticipation"] is True
    assert policy["bossa_nova_anticipation_tail_policy_no_bar_first_restore"] is True
    assert anticipation.metadata["bossa_nova_anticipation_tail_policy_version"] == MILESTONE_ID
    assert anticipation.require_previous_last_beat_empty is True
    assert anticipation.require_previous_last_upbeat_empty is True
    assert anticipation.min_previous_region_duration_beats == 3.75
    assert anticipation.metadata["preserve_native_4and_current_chord_events"] is True


def test_v2_6_93_native_4and_current_chord_event_blocks_bossa_anticipation_tail() -> None:
    prev_region = _region("prev", "Cm7", 0.0, 4.0)
    next_region = _region("next", "F7", 4.0, 4.0)
    previous = _candidate("bossa_piano_cell_A_1_4and").instantiate(prev_region)
    current = _candidate("bossa_piano_cell_A_1").instantiate(next_region)
    policy = replace(anticipation_policy.get_anticipation_policy(), probability=1.0)

    rewritten = AnticipationResolver().resolve(
        list(previous.events) + list(current.events),
        policy,
        random.Random(1),
        regions=(prev_region, next_region),
        region_plans={prev_region.region_id: previous, next_region.region_id: current},
    )

    assert not any(event.source_event_id == current.events[0].event_id for event in rewritten)
    assert any(event.event_id == current.events[0].event_id and event.status == "active" for event in rewritten)


def test_v2_6_93_tail_free_full_region_allows_bossa_anticipation_and_stamps_policy_metadata() -> None:
    prev_region = _region("prev", "Cm7", 0.0, 4.0)
    next_region = _region("next", "F7", 4.0, 4.0)
    previous = _candidate("bossa_piano_cell_A_1_3and").instantiate(prev_region)
    current = _candidate("bossa_piano_cell_A_1").instantiate(next_region)
    policy = replace(anticipation_policy.get_anticipation_policy(), probability=1.0)

    rewritten = AnticipationResolver().resolve(
        list(previous.events) + list(current.events),
        policy,
        random.Random(1),
        regions=(prev_region, next_region),
        region_plans={prev_region.region_id: previous, next_region.region_id: current},
    )
    anticipated = [event for event in rewritten if event.source_event_id == current.events[0].event_id and event.status == "active"]
    suppressed = [event for event in rewritten if event.event_id == current.events[0].event_id and event.status == "suppressed"]

    assert len(anticipated) == 1
    assert len(suppressed) == 1
    assert anticipated[0].onset_beat == 3.5
    metadata = anticipated[0].metadata["anticipation"]
    assert metadata["target_local_beat_in_previous"] == 3.5
    assert metadata["tail_checked_local_beats"] == (3.0, 3.5)
    assert metadata["min_previous_region_duration_beats"] == 3.75
    assert metadata["style_anticipation_policy_metadata"]["bossa_nova_anticipation_tail_policy_version"] == MILESTONE_ID


def test_v2_6_93_short_region_does_not_receive_bossa_piano_anticipation() -> None:
    prev_region = _region("prev_short", "Cm7", 0.0, 2.0)
    next_region = _region("next_short", "F7", 2.0, 2.0)
    previous = comping_patterns.get_pattern_candidates({"region_duration_beats": 2.0}, apply_context_policy=False)[0].instantiate(prev_region)
    current = _candidate("bossa_piano_cell_A_1").instantiate(next_region)
    policy = replace(anticipation_policy.get_anticipation_policy(), probability=1.0)

    rewritten = AnticipationResolver().resolve(
        list(previous.events) + list(current.events),
        policy,
        random.Random(1),
        regions=(prev_region, next_region),
        region_plans={prev_region.region_id: previous, next_region.region_id: current},
    )

    assert not any(event.source_event_id == current.events[0].event_id for event in rewritten)
    assert any(event.event_id == current.events[0].event_id and event.status == "active" for event in rewritten)


def test_v2_6_93_static_audit_acceptance_passes() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static, [])

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["arrangement_policy_version"] == MILESTONE_ID
    assert static["anticipation_policy_min_previous_region_duration_beats"] == 3.75
    assert static["native_4and_probe"]["blocked"] is True
    assert static["tail_free_probe"]["allowed"] is True
    assert static["short_region_probe"]["blocked"] is True
    assert acceptance["checks"]["runtime_blue_bossa_full_band_passes"] is False
    assert acceptance["passed"] is False


def test_v2_6_93_blue_bossa_runtime_preserves_native_4and_and_tail_policy() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 22703, "slug": "blue_bossa_3x_pytest_v2_6_93"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert runtime["active_anticipation_count"] > 0
    assert runtime["anticipation_timing_grids"] == ["straight_upbeat"]
    assert runtime["anticipation_policy_versions"] == [MILESTONE_ID]
    assert runtime["anticipation_min_previous_region_duration_values"] == ["3.75"]
    assert runtime["anticipations_from_short_previous_region"] == 0
    assert runtime["native_4and_anticipated_event_count"] == 0
    assert runtime["terminal_ending_anticipation_count"] == 0
    assert acceptance["passed"] is True
