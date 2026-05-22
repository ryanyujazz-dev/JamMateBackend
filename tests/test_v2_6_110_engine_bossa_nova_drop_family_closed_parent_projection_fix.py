from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.core.voicing import Disposition, generate_candidates
from jammate_engine.styles.bossa_nova import voicing_policy

MILESTONE_ID = "v2_6_110"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_drop_family_closed_parent_projection_fix_audit.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_drop_family_closed_parent_projection_fix_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _is_low_cluster_top_gap(notes: list[int]) -> bool:
    if len(notes) != 4:
        return False
    intervals = [notes[index + 1] - notes[index] for index in range(len(notes) - 1)]
    return intervals[0] <= 2 and intervals[1] <= 2 and intervals[2] >= 10


def test_v2_6_110_named_open_methods_project_from_compact_closed_parents() -> None:
    policy = voicing_policy.get_voicing_policy()
    for symbol in ("G7b9", "Fm7", "Dm7b5", "Cm7"):
        candidates = [candidate for candidate in generate_candidates(symbol, policy) if candidate.disposition == Disposition.OPEN]
        assert candidates
        for candidate in candidates:
            metadata = dict(candidate.metadata or {})
            method = metadata.get("disposition_projection_method")
            assert method in {"drop2", "drop3", "drop2_and_4"}
            assert metadata.get("open_projection_from_parent_closed_projection") is True
            assert int(metadata.get("open_named_projection_parent_closed_span") or 0) <= 12
            assert not _is_low_cluster_top_gap([int(note) for note in candidate.notes])


def test_v2_6_110_static_audit_detects_no_bad_parents_or_low_clusters() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static, [])

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["bad_parent_span_count"] == 0
    assert static["bad_low_cluster_candidate_count"] == 0
    assert static["no_new_voicing_ability"] is True
    assert acceptance["checks"]["static_drop_parents_are_compact"] is True
    assert acceptance["checks"]["static_no_low_cluster_candidates"] is True
    assert acceptance["passed"] is False


def test_v2_6_110_blue_bossa_bars_14_19_29_are_clean() -> None:
    module = _load_script_module()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 23110, "slug": "blue_bossa_3x_pytest_v2_6_110"})

    assert runtime["ok"] is True
    assert runtime["generic_open_event_count"] == 0
    assert runtime["low_cluster_top_gap_event_count"] == 0
    assert runtime["inspected_bars"] == [14, 19, 29]
    assert runtime["inspected_bar_bad_event_count"] == 0
    assert runtime["parent_closed_span_over_12_count"] == 0


def test_v2_6_110_acceptance_passes_for_blue_bossa_runtime() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 23110, "slug": "blue_bossa_3x_pytest_acceptance_v2_6_110"})
    acceptance = module._acceptance(static, [runtime])

    assert acceptance["passed"] is True
