from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_style_rule_baseline_docs_exist_and_cover_three_piano_styles() -> None:
    baseline = (ROOT / "docs" / "STYLE_RULE_BASELINE_V2.md").read_text(encoding="utf-8")
    entry = (ROOT / "docs" / "STYLE_TUNING_ENTRY_POINT_V2.md").read_text(encoding="utf-8")

    for token in (
        "Medium Swing Piano Baseline",
        "Bossa Nova Piano Baseline",
        "Jazz Ballad Piano Baseline",
        "Pattern rules",
        "Voicing rules",
        "Expression rules",
        "Timing rules",
        "Current known",
    ):
        assert token in baseline

    assert "v2_1_0 — Medium Swing Piano Musicality Tuning Pass 1" in entry
    assert "Do not add more core infrastructure" in entry


def test_development_plan_declares_infrastructure_close_and_next_tuning_entry() -> None:
    plan = (ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    agent = (ROOT / "agent.md").read_text(encoding="utf-8")

    for doc in (plan, readme, agent):
        assert "v2_0_46" in doc
        assert "v2_1_0 — Medium Swing Piano Musicality Tuning Pass 1" in doc

    assert "Style rule baseline docs and formal tuning entry point through `v2_0_46`" in plan
    assert "No BassFoundation retune" in readme


def test_generation_rules_summary_records_v2_0_46_style_baseline_contract() -> None:
    rules = (ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md").read_text(encoding="utf-8")

    for token in (
        "v2_0_46 Style Rule Baseline Docs + Tuning Entry Point",
        "STYLE_RULE_BASELINE_V2.md",
        "STYLE_TUNING_ENTRY_POINT_V2.md",
        "Medium Swing Piano baseline",
        "Bossa Piano baseline",
        "Jazz Ballad Piano baseline",
        "v2_1_0 — Medium Swing Piano Musicality Tuning Pass 1",
    ):
        assert token in rules
