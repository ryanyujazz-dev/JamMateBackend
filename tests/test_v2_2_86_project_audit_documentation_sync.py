from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v2_2_88_version_surfaces_are_synced() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert 'version = "2.3.9"' in _read("pyproject.toml")
    assert "Altered Dominant Intensity / Source Weight Calibration" in _read("README.md")


def test_v2_2_88_audit_plan_records_actual_next_path() -> None:
    plan = _read("docs/ALTERED_DOMINANT_INTENSITY_SOURCE_WEIGHT_CALIBRATION_V2_2_87.md")
    assert "PYTHONPATH=src python -m pytest -q" in plan
    assert "light / medium / high / full" in plan
    assert "rooted_color" in plan and "rootless_ab" in plan and "upper_structure" in plan
    assert "v2_2_88 — Minor V→i / Turnaround Altered Coverage Audit" in plan


def test_v2_2_88_entry_docs_point_to_current_audit_plan() -> None:
    for path in [
        "agent.md",
        "docs/DEVELOPMENT_HARNESS_V2.md",
        "docs/DEVELOPMENT_TASK_PLAN_V2.md",
        "docs/PROJECT_DOCUMENTATION_AUDIT_V2.md",
    ]:
        text = _read(path)
        assert "v2_2_88" in text, path
        assert "Altered Dominant Intensity / Source Weight Calibration" in text, path


def test_v2_2_88_keeps_altered_dominant_scope_as_audited_state_not_new_runtime_feature() -> None:
    combined = "\n".join(
        _read(path)
        for path in [
            "README.md",
            "agent.md",
            "docs/DEVELOPMENT_TASK_PLAN_V2.md",
            "docs/VOICING_SYSTEM_V2_DESIGN.md",
        ]
    )
    assert "Altered Dominant Functional Scope" in combined
    assert "LLM-selected altered dominant region" in combined
    assert "Altered Dominant Intensity / Source Weight Calibration" in combined
