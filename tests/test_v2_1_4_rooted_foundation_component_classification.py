from pathlib import Path

from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_PRESETS

ROOT = Path(__file__).resolve().parents[1]


def test_root_plus_three_ten_is_not_a_default_standalone_override_preset() -> None:
    forbidden_presets = {
        "root_plus_3_10",
        "root_3_10",
        "2_note_root_3_10",
        "2_note_root_plus_3",
        "root_plus_10",
    }
    assert forbidden_presets.isdisjoint(set(VOICING_OVERRIDE_PRESETS))


def test_voicing_tuning_workflow_moves_root_plus_three_to_component_pool() -> None:
    workflow = (ROOT / "docs" / "VOICING_TUNING_WORKFLOW_V2.md").read_text(encoding="utf-8")

    assert "2-note standalone voicings" in workflow
    assert "Do **not** treat `root + 3 / 10` as an independent 2-note tuning class" in workflow
    assert "Rooted dyad component pool, not standalone review targets" in workflow
    assert "foundation/support component for 4/5/6-note recipes" in workflow


def test_rooted_foundation_component_rule_is_synced_across_core_docs() -> None:
    required_docs = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md",
        ROOT / "docs" / "STYLE_RULE_BASELINE_V2.md",
        ROOT / "docs" / "VOICING_SYSTEM_V2_DESIGN.md",
        ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md",
    ]

    for path in required_docs:
        text = path.read_text(encoding="utf-8")
        assert "root" in text.lower(), path
        assert "foundation component" in text or "rooted foundation component" in text, path
        assert "standalone" in text, path
