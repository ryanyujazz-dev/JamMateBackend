from __future__ import annotations

import random
from pathlib import Path

from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_PRESETS, build_voicing_override_policy
from jammate_engine.core.voicing.selection.selector import select_candidate
from jammate_engine.core.voicing.runtime.state import VoicingState

ROOT = Path(__file__).resolve().parents[1]


def _policy(preset: str = "shell_plus_expanded_color", **override):
    data = {"enabled": True, "preset": preset}
    data.update(override)
    return build_voicing_override_policy({}, data, style_name="medium_swing")


def _component(degrees: list[str]) -> str:
    if "R" in degrees:
        return "root"
    if any(degree in {"9", "11", "13", "b9", "#9", "#11", "b13"} for degree in degrees):
        return "color"
    if any(degree in {"5", "b5", "#5"} for degree in degrees):
        return "5"
    return "other"


def test_shell_plus_expanded_color_generates_color_5_and_low_weight_root_candidates() -> None:
    policy = _policy()
    candidates = generate_candidates("G7", policy)
    component_sets = {_component(candidate.degrees) for candidate in candidates}

    assert policy.harmonic_expansion_enabled is True
    assert policy.color_policy_mode.value == "style_safe_extensions"
    assert {"color", "5", "root"}.issubset(component_sets)


def test_shell_plus_expanded_color_samples_5_most_color_sometimes_root_rarely() -> None:
    policy = _policy()
    counts = {"color": 0, "5": 0, "root": 0}
    candidates = generate_candidates("G7", policy)
    for seed in range(800):
        selected = select_candidate(candidates, policy=policy, state=VoicingState.empty(), rng=random.Random(seed))
        component = _component(selected.degrees)
        if component in counts:
            counts[component] += 1

    assert counts["5"] > counts["color"] > counts["root"] > 0


def test_shell_plus_5_is_now_shell_plus_1or5_but_selects_5_by_default() -> None:
    policy = _policy("shell_plus_1or5")
    candidates = generate_candidates("G7", policy)
    component_sets = {_component(candidate.degrees) for candidate in candidates}
    selected = select_candidate(candidates, policy=policy, state=VoicingState.empty())

    assert {"5", "root"}.issubset(component_sets)
    assert _component(selected.degrees) == "5"
    assert policy.metadata["root_component_role"].startswith("occasional")


def test_explicit_chord_symbol_color_still_overrides_expansion_pool() -> None:
    policy = _policy()
    selected = select_candidate(generate_candidates("G7b9", policy), policy=policy, state=VoicingState.empty(), rng=random.Random(1))

    assert "b9" in selected.degrees
    assert "explicit_chord_symbol_color_used" in selected.metadata["content_recipe"]["validity_notes"]


def test_v2_1_7_expanded_shell_color_rule_is_documented() -> None:
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
        assert "v2_1_7" in text, path
        assert "shell_plus_expanded_color" in text, path
        assert "shell_plus_1or5" in text, path
        assert "root/1" in text or "root / 1" in text, path
