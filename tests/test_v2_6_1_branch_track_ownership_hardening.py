from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v2_6_1_track_ownership_docs_exist_and_split_rolling_files() -> None:
    assert (ROOT / "docs" / "BRANCH_AND_TRACK_OWNERSHIP_V2.md").exists()
    assert (ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_ENGINE_V2.md").exists()
    assert (ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_AGENT_V2.md").exists()
    assert (ROOT / "docs" / "CHANGELOG_ENGINE.md").exists()
    assert (ROOT / "docs" / "CHANGELOG_AGENT.md").exists()

    branch_doc = _read("docs/BRANCH_AND_TRACK_OWNERSHIP_V2.md")
    assert "Engine-Owned Paths" in branch_doc
    assert "Agent-Owned Paths" in branch_doc
    assert "Shared Files: Integration-Owned Only" in branch_doc
    assert "integration/agent-engine-merge" in branch_doc


def test_v2_6_1_agent_harness_declares_owner_boundaries() -> None:
    agent = _read("agent.md")
    assert "Track Ownership and Branch Split" in agent
    assert "Engine tasks must not edit `src/jammate_agent/`" in agent
    assert "Agent tasks must not edit `src/jammate_engine/core/`" in agent
    assert "shared files" in agent.lower()
    assert "docs/BRANCH_AND_TRACK_OWNERSHIP_V2.md" in agent


def test_v2_6_1_main_plan_is_integration_index() -> None:
    main_plan = _read("docs/DEVELOPMENT_TASK_PLAN_V2.md")
    assert "stable integration index" in main_plan
    assert "DEVELOPMENT_TASK_PLAN_ENGINE_V2.md" in main_plan
    assert "DEVELOPMENT_TASK_PLAN_AGENT_V2.md" in main_plan
    assert "v2_6_2_engine_jazz_ballad_bass_anchor_path_policy" in main_plan


def test_v2_6_1_harness_checker_requires_track_ownership_docs() -> None:
    harness = _read("tools/check_development_harness.py")
    assert "check_track_ownership_documented" in harness
    assert "BRANCH_AND_TRACK_OWNERSHIP_V2.md" in harness
    assert "CHANGELOG_ENGINE.md" in harness
    assert "DEVELOPMENT_TASK_PLAN_AGENT_V2.md" in harness
