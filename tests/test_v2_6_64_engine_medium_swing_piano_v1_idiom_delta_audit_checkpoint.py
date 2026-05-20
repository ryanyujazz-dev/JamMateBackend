from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.styles.medium_swing import comping_patterns


def _load_audit_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_medium_swing_piano_v1_idiom_delta_audit.py"
    spec = importlib.util.spec_from_file_location("generate_medium_swing_piano_v1_idiom_delta_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_6_64_static_v1_idiom_delta_audit_is_region_first_and_no_runtime_change() -> None:
    audit_module = _load_audit_module()
    audit = audit_module.build_static_idiom_delta_audit()

    assert audit["checkpoint_version"] == "v2_6_64"
    assert audit["pattern_library_version"] == "v2_6_56"
    assert audit["candidate_lookup_policy_version"] == "v2_6_57"
    assert audit["weight_calibration_policy_version"] == "v2_6_58"
    assert audit["expression_hint_handoff_policy_version"] == "v2_6_63"

    assert audit["forbidden_pattern_expression_key_candidates"] == []
    assert audit["bar_first_two_chord_bar_candidates"] == []

    active_by_length = audit["active_by_region_length_family"]
    assert active_by_length["four_beat_region"] > 0
    assert active_by_length["two_beat_region"] > 0
    assert active_by_length["one_beat_region"] > 0


def test_v2_6_64_translation_matrix_marks_v1_progression_specific_vocab_as_partial_not_done() -> None:
    audit_module = _load_audit_module()
    audit = audit_module.build_static_idiom_delta_audit()
    matrix = audit["translation_matrix"]

    progression = next(row for row in matrix if row["v1_idiom"] == "major_251 / minor_251 / two_five / ii_setup priority")
    assert progression["v2_status"] == "partial_multiplier_only"
    assert "context-specific candidate subset" in progression["next_action"]

    split_bar = next(row for row in matrix if row["v1_idiom"] == "two_chord_bar split vocabulary")
    assert split_bar["v2_status"] == "covered_as_region_first_translation"
    assert "2-beat / 1-beat ChordRegion" in split_bar["v2_translation"]

    texture = next(row for row in matrix if row["v1_idiom"] == "texture expansion shell2/shell4/rootless4")
    assert texture["v2_status"] == "rejected_for_v2_pattern_layer"
    assert "voicing policy" in texture["next_action"]


def test_v2_6_64_v1_expression_numeric_ranges_are_reference_only_not_pattern_values() -> None:
    audit_module = _load_audit_module()
    ranges = audit_module.V1_EXPRESSION_TOUCH_RANGES
    assert ranges["soft_hold"]["duration_ticks"] == [84, 140]
    assert ranges["light_stab"]["duration_ticks"] == [62, 88]
    assert ranges["accent_stab"]["velocity"] == [60, 70]

    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    for candidate in candidates:
        for event in candidate.events:
            assert "velocity" not in event.metadata
            assert "duration_ticks" not in event.metadata
            assert "duration" not in event.metadata
            assert "duration_beats" not in event.metadata
            assert "pedal" not in event.metadata


def test_v2_6_64_static_v1_idiom_delta_audit_acceptance_passes_without_generating_demos() -> None:
    audit_module = _load_audit_module()
    audit = audit_module.build_static_idiom_delta_audit()
    acceptance = audit_module._acceptance(audit, [])
    assert acceptance["passed"] is True
