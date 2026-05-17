from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v2_3_17_version_surfaces_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_17"
    assert _read("VERSION").strip() == "v2_3_17"
    assert 'version = "2.3.17"' in _read("pyproject.toml")
    assert 'CONTRACT_VERSION = "v2_3_17"' in _read("src/jammate_agent/core/contract_codegen.py")


def test_agent_md_is_compact_hard_harness_not_changelog() -> None:
    agent = _read("agent.md")
    assert len(agent.splitlines()) < 180
    assert "Mandatory Architecture Boundary" in agent
    assert "Capability Reuse Before New Construction" in agent
    assert "Minimal File Split Principle" in agent
    assert "Cleanup Before Every Delivery" in agent
    assert "v2_1_4 — Rooted Foundation" not in agent
    assert "## v2_2_" not in agent


def test_readme_and_changelog_have_separate_roles() -> None:
    readme = _read("README.md")
    changelog = _read("docs/CHANGELOG.md")
    assert "Core Design Principles" in readme
    assert "Directory Architecture" in readme
    assert "Current Main Capabilities" in readme
    assert "## v2_3_17" not in readme
    assert "## v2_3_17 — Harness Hardening and Changelog Split" in changelog
    assert "## v2_3_10 — Agent / Engine / API Boundary Foundation" in changelog


def test_harness_checker_is_focused_and_passes() -> None:
    harness = _read("tools/check_development_harness.py")
    assert "check_architecture_boundaries" in harness
    assert "check_capability_reuse_before_new_construction_documented" in harness
    assert "check_bass_foundation_three_beat_alignment_guard" not in harness
    shutil.rmtree(ROOT / "demos" / "agent_traces", ignore_errors=True)
    result = subprocess.run(
        [sys.executable, "tools/check_development_harness.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "HARNESS OK" in result.stdout
