from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG

ROOT = Path(__file__).resolve().parents[1]


def test_v2_2_28_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"


def test_agent_md_records_demo_first_delivery_workflow() -> None:
    agent = (ROOT / "agent.md").read_text(encoding="utf-8")
    assert "Development delivery workflow rule" in agent
    assert "Do not output a continuation development document by default" in agent
    assert "only when the user explicitly asks" in agent
    assert "current standard-tune listening demo" in agent
    assert "All the Things You Are" in agent
    assert "Runtime generation logic is unchanged" in agent
