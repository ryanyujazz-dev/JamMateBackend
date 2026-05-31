from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.styles.bossa_nova import arrangement_policy, bass_foundation_patterns, percussion_patterns
from jammate_engine.styles.registry import get_style

MILESTONE_ID = "v2_6_96"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_bass_and_drums_identity_audit.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_bass_and_drums_identity_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_6_96_bossa_bass_and_drums_identity_policy_metadata_registered() -> None:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()

    assert style.arrangement_policy == policy
    assert policy["bossa_nova_bass_and_drums_identity_audit_active"] is True
    assert policy["bossa_nova_bass_and_drums_identity_audit_version"] == MILESTONE_ID
    assert policy["bossa_nova_bass_and_drums_identity_audit_no_parallel_selector"] is True
    assert policy["bossa_nova_bass_and_drums_identity_audit_no_bar_first_restore"] is True
    assert policy["bossa_nova_bass_and_drums_identity_audit_no_piano_pattern_change"] is True
    assert policy["bossa_nova_bass_and_drums_identity_audit_no_expression_numeric_change"] is True
    assert policy["bossa_nova_bass_and_drums_identity_audit_no_core_voicing_change"] is True
    assert policy["bossa_nova_bass_and_drums_identity_audit_no_api_agent_harmonyos_change"] is True
    assert policy["bossa_nova_bass_identity"] == "root_fifth_support_not_walking"
    assert policy["bossa_nova_drums_identity"] == "shaker_cross_stick_light_kick"


def test_v2_6_96_bossa_bass_replaces_one_size_pattern_with_region_duration_identity() -> None:
    full = bass_foundation_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "bar_index": 0})[0]
    split = bass_foundation_patterns.get_pattern_candidates({"region_duration_beats": 2.0, "bar_index": 0})[0]
    short = bass_foundation_patterns.get_pattern_candidates({"region_duration_beats": 1.0, "bar_index": 0})[0]

    assert full.name == "bossa_bass_root_fifth_2bar_A"
    assert full.rhythm_beats == (0.0, 2.0)
    assert [event.metadata["degree"] for event in full.events] == ["root", "fifth"]
    assert all(event.metadata["walking_bass"] is False for event in full.events)
    assert all(event.metadata["bossa_bass_and_drums_identity_audit_version"] == MILESTONE_ID for event in full.events)
    assert "not_walking" in full.tags

    assert split.name == "bossa_bass_split_region_root_only"
    assert split.rhythm_beats == (0.0,)
    assert [event.metadata["degree"] for event in split.events] == ["root"]
    assert split.metadata["pattern_function"] == "split_region_root_only_clarity"

    assert short.name == "bossa_bass_short_region_root_touch"
    assert short.rhythm_beats == (0.0,)
    assert [event.metadata["degree"] for event in short.events] == ["root"]


def test_v2_6_96_bossa_drums_replace_hihat_placeholder_with_identity_layer() -> None:
    full = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "bar_index": 0})[0]
    split = percussion_patterns.get_pattern_candidates({"region_duration_beats": 2.0, "bar_index": 0})[0]

    full_voices = [event.metadata["bossa_drum_voice"] for event in full.events]
    split_beats = [event.local_beat for event in split.events]

    assert full.category == "bossa_shaker_cross_stick_light_kick_identity"
    assert "shaker" in full.tags
    assert "cross_stick" in full.tags
    assert "light_kick" in full.tags
    assert "not_swing_ride" in full.tags
    assert "not_rock_backbeat" in full.tags
    assert any(voice == "shaker_time" for voice in full_voices)
    assert any(str(voice).startswith("cross_stick_A") for voice in full_voices)
    assert "soft_kick_root_shadow" in full_voices
    assert "soft_kick_fifth_shadow" in full_voices
    assert all(event.metadata["bossa_bass_and_drums_identity_audit_version"] == MILESTONE_ID for event in full.events)
    assert all(event.metadata["swing_ride_pattern"] is False for event in full.events)
    assert all(event.metadata["rock_backbeat_pattern"] is False for event in full.events)

    assert max(split_beats) < 2.0
    assert any(event.metadata["bossa_drum_voice"] == "cross_stick_split_mark" for event in split.events)


def test_v2_6_96_static_audit_acceptance_requires_runtime_for_full_pass() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static, [])

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["arrangement_policy_version"] == MILESTONE_ID
    assert static["bass_identity"] == "root_fifth_support_not_walking"
    assert static["drums_identity"] == "shaker_cross_stick_light_kick"
    assert acceptance["checks"]["runtime_blue_bossa_full_band_identity_passes"] is False
    assert acceptance["passed"] is False


def test_v2_6_96_blue_bossa_runtime_keeps_bass_and_drums_identity() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 22706, "slug": "blue_bossa_3x_pytest_v2_6_96"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert runtime["note_events_by_track"]["piano"] > 0
    assert runtime["note_events_by_track"]["bass"] > 0
    assert runtime["note_events_by_track"]["drums"] > 0
    assert runtime["planned_bass_degree_counts"]["root"] > 0
    assert runtime["planned_bass_degree_counts"]["fifth"] > 0
    assert runtime["planned_bass_walking_like_event_count"] == 0
    assert runtime["planned_bass_short_region_non_root_event_count"] == 0
    assert runtime["planned_drum_voice_counts"]["shaker_time"] > 0
    assert runtime["planned_drum_voice_counts"]["soft_kick_root_shadow"] > 0
    assert any(key.startswith("cross_stick") for key in runtime["planned_drum_voice_counts"])
    assert runtime["planned_drum_swing_ride_or_rock_event_count"] == 0
    assert acceptance["passed"] is True
