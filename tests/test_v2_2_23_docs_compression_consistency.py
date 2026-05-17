from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v2_2_28_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"


def test_agent_and_docs_are_compact_and_current() -> None:
    agent = _read("agent.md")
    assert len(agent.splitlines()) < 180
    assert "v2_1_4 — Rooted Foundation Component Classification Correction" not in agent
    assert "Recommended next task: `v2_2_22 — Medium Swing OPEN Texture State Runtime Pilot`" not in agent
    assert "Do not output a continuation development document by default" in agent
    assert "current standard-tune listening demo" in agent

    for path in (ROOT / "docs").glob("*.md"):
        lines = path.read_text(encoding="utf-8").splitlines()
        assert len(lines) < 220, f"{path.name} should stay compact"


def test_docs_do_not_force_medium_swing_runtime_pilot() -> None:
    combined = "\n".join(p.read_text(encoding="utf-8") for p in [ROOT / "README.md", ROOT / "agent.md", *sorted((ROOT / "docs").glob("*.md"))])
    forbidden = "Recommended next task: `v2_2_22 — Medium Swing OPEN Texture State Runtime Pilot`"
    assert forbidden not in combined
    assert "the next engineering target should be selected by the user" in combined
