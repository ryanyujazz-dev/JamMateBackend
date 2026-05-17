from __future__ import annotations

import random
from pathlib import Path

from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.runtime.override import build_voicing_override_policy
from jammate_engine.core.voicing.selection.scorer import score_candidate
from jammate_engine.core.voicing.selection.selector import select_candidate
from jammate_engine.core.voicing.runtime.state import VoicingState

ROOT = Path(__file__).resolve().parents[1]
COLOR_DEGREES = {"9", "11", "13", "b9", "#9", "#11", "b13"}


def _policy(preset: str = "shell_plus_expanded_color", **override):
    data = {"enabled": True, "preset": preset}
    data.update(override)
    return build_voicing_override_policy({}, data, style_name="medium_swing")


def _component(degrees: list[str]) -> str:
    if "R" in degrees:
        return "root"
    if COLOR_DEGREES.intersection(degrees):
        return "color"
    if {"5", "b5", "#5"}.intersection(degrees):
        return "5"
    return "other"


def _intervals(notes: list[int]) -> list[int]:
    ordered = sorted(notes)
    return [upper - lower for lower, upper in zip(ordered, ordered[1:])]


def test_v2_1_8_spacing_policy_was_superseded_by_v2_1_9() -> None:
    text = (ROOT / "docs" / "VOICING_TUNING_WORKFLOW_V2.md").read_text(encoding="utf-8")
    assert "v2_1_8" in text
    assert "v2_1_9" in text
    assert "supersedes" in text.lower() or "replaces" in text.lower()
