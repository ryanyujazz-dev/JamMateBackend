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


def test_expansion_enabled_reduces_but_does_not_remove_1or5_fallback() -> None:
    policy = _policy()
    counts = {"color": 0, "5": 0, "root": 0, "other": 0}
    candidates = generate_candidates("G7", policy)
    for seed in range(1200):
        selected = select_candidate(candidates, policy=policy, state=VoicingState.empty(), rng=random.Random(seed))
        counts[_component(selected.degrees)] += 1

    assert counts["5"] > 0 and counts["color"] > 0 and counts["root"] > 0
    assert counts["root"] < counts["color"] * 0.08


def test_major_second_is_no_longer_forced_apart() -> None:
    policy = _policy()
    color_candidates = [
        candidate
        for candidate in generate_candidates("Cmaj7", policy)
        if set(candidate.degrees) == {"3", "7", "9"}
    ]
    assert color_candidates

    best = max(color_candidates, key=lambda candidate: score_candidate(candidate, policy, VoicingState.empty()).total)

    # v2_1_9 intentionally stops treating M2 like a spacing defect.
    # B-D-E / D-E-B style shapes can beat the older E-B-D preference.
    assert 2 in _intervals(best.notes)


def test_color_minor_second_direction_rule_is_superseded_by_closed_nearest_motion() -> None:
    policy = _policy()
    color_candidates = [
        candidate
        for candidate in generate_candidates("G7#9", policy)
        if set(candidate.degrees) == {"3", "b7", "#9"}
    ]
    assert color_candidates

    # v2_1_40 removes the directed color-octave preference. Minor-second color
    # bites are no longer punished or rescued inside source selection; closed
    # legality happens first and nearest-motion placement decides the layout.
    assert any(1 in _intervals(candidate.notes) for candidate in color_candidates)
    assert all(candidate.metadata.get("strict_closed_compact_pitch_class_layout") for candidate in color_candidates)


def test_shell_root_cluster_bite_is_not_erased_by_directed_color_policy() -> None:
    policy = _policy()
    root_candidates = [candidate for candidate in generate_candidates("Cmaj7", policy) if "R" in candidate.degrees]
    assert root_candidates
    assert any(any(interval in {1, 2} for interval in _intervals(candidate.notes)) for candidate in root_candidates)


def test_v2_1_9_directed_color_m2_rule_is_documented_as_superseded() -> None:
    required_docs = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "VOICING_TUNING_WORKFLOW_V2.md",
        ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md",
        ROOT / "docs" / "STYLE_RULE_BASELINE_V2.md",
        ROOT / "docs" / "VOICING_SYSTEM_V2_DESIGN.md",
        ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md",
        ROOT / "docs" / "API_CONTRACT_V2.md",
        ROOT / "docs" / "SYSTEM_CONTRACTS_V2.md",
    ]
    for path in required_docs:
        text = path.read_text(encoding="utf-8")
        assert "v2_1_9" in text, path
        assert "directed minor-second" in text.lower() or "directed m2" in text.lower(), path
        assert "superseded" in text.lower(), path
        assert "shell+1/root" in text, path
