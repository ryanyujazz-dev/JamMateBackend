from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.styles.bossa_nova import arrangement_policy, comping_patterns

SCRIPT_PATH = PROJECT_ROOT / "examples" / "scripts" / "generate_engine_bossa_nova_long_sustain_pattern_weight_calibration.py"


def _load_audit_module():
    spec = importlib.util.spec_from_file_location("v2_6_125_bossa_long_sustain_audit", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _candidate_by_name(name: str):
    candidates = comping_patterns.get_pattern_candidates({}, apply_context_policy=False)
    return next(candidate for candidate in candidates if candidate.name == name)


def test_v2_6_125_declares_pattern_weight_only_bossa_calibration_boundary() -> None:
    policy = arrangement_policy.get_arrangement_policy()

    assert comping_patterns.BOSSA_LONG_SUSTAIN_WEIGHT_CALIBRATION_VERSION == "v2_6_125"
    assert "long_sustain_pattern_weight_calibration_v2_6_125" in comping_patterns.BOUNDARY_NOTES
    assert policy["bossa_nova_long_sustain_pattern_weight_calibration_active"] is True
    assert policy["bossa_nova_long_sustain_pattern_weight_calibration_no_voicing_change"] is True
    assert policy["bossa_nova_long_sustain_pattern_weight_calibration_no_expression_numeric_change"] is True
    assert policy["bossa_nova_long_sustain_pattern_weight_calibration_no_new_pattern_vocabulary"] is True
    assert policy["bossa_nova_long_sustain_pattern_weight_calibration_no_open_or_generic_change"] is True


def test_v2_6_125_rebalances_bossa_long_hold_vs_split_cells_without_new_vocabulary() -> None:
    library = comping_patterns.describe_pattern_library()
    candidate_names = {candidate["name"] for candidate in library["candidates"]}

    assert library["candidate_count"] == 13
    assert "bossa_piano_cell_A_1" in candidate_names
    assert "bossa_piano_cell_A_1_3and" in candidate_names
    assert "bossa_piano_cell_A_1_2and" in candidate_names
    assert "bossa_piano_cell_A_1_2_3and" in candidate_names

    assert _candidate_by_name("bossa_piano_cell_A_1").weight == 108.0
    assert _candidate_by_name("bossa_piano_cell_A_1_3and").weight == 198.0
    assert _candidate_by_name("bossa_piano_cell_A_1_3").weight == 56.0
    assert _candidate_by_name("bossa_piano_cell_A_1_2and").weight == 216.0
    assert _candidate_by_name("bossa_piano_cell_A_1_2_3and").weight == 236.0


def test_v2_6_125_blue_bossa_runtime_reduces_sparse_long_hold_cells_and_preserves_voicing_route() -> None:
    module = _load_audit_module()
    runtime = module._generate_blue_bossa_runtime_demo()

    assert runtime["ok"] is True
    assert runtime["a1_3and_count_delta_vs_v2_6_124"] <= -4
    assert runtime["a1_count_delta_vs_v2_6_124"] <= -2
    assert runtime["a1_2and_count_delta_vs_v2_6_124"] >= 6
    assert runtime["extreme_long_duration_event_count_ge_3_beats"] <= 13
    assert runtime["five_note_spread_1plus4_selected_count"] >= 2
    assert runtime["open_5note_selected_count"] == 0
    assert runtime["generic_open_selected_count"] == 0
    assert set(runtime["core_batida_front_velocities_first_four"]) == {48}


def test_v2_6_125_audit_script_acceptance_passes() -> None:
    module = _load_audit_module()
    module.main()
    summary_path = PROJECT_ROOT / "demos" / "v2_6_125_engine_bossa_nova_long_sustain_pattern_weight_calibration_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["acceptance"]["passed"] is True
