from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v2_2_38_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"


def test_spread_voicing_notes_recipe_plan_is_documented() -> None:
    docs = "\n".join(
        _read(rel)
        for rel in (
            "agent.md",
            "README.md",
            "docs/VOICING_SYSTEM_V2_DESIGN.md",
            "docs/VOICING_MODULE_CORE_LOGIC_V2.md",
            "docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md",
            "docs/DEVELOPMENT_TASK_PLAN_V2.md",
        )
    )
    required = [
        "SPREAD notes",
        "lower functional group + upper source/projection group",
        "1-note: `root` only",
        "root+3",
        "root+7+upper3",
        "root+5+upper3",
        "5-note: `1+4`, `2+3`",
        "DROP2/DROP3",
        "not directly reuse a final placed closed/open voicing result",
        "notes-only",
        "Do not implement expression",
    ]
    for token in required:
        assert token in docs


def test_development_plan_starts_with_reuse_audit_before_spread_runtime() -> None:
    plan = _read("docs/DEVELOPMENT_TASK_PLAN_V2.md")
    assert "Spread Recipe Reuse Audit + Contract Skeleton" in plan
    assert "Upper Source Adapter" in plan
    assert "Basic SPREAD Projection" in plan
    assert "Group-wise Voice-Leading Scorer" in plan
    assert "Ballad SPREAD runtime pilot after notes/projection audits sound reliable" in plan
