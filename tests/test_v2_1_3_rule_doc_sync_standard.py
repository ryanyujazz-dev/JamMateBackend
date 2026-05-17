from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_rule_change_documentation_sync_standard_is_in_agent_and_harness() -> None:
    agent = (ROOT / "agent.md").read_text(encoding="utf-8")
    harness = (ROOT / "docs" / "DEVELOPMENT_HARNESS_V2.md").read_text(encoding="utf-8")

    required_tokens = [
        "Rule Change Documentation Sync Standard",
        "GENERATION_RULES_SUMMARY_V2.md",
        "STYLE_RULE_BASELINE_V2.md",
        "VOICING_TUNING_WORKFLOW_V2.md",
        "API_CONTRACT_V2.md",
        "ARCHITECTURE_V2.md",
        "DEVELOPMENT_TASK_PLAN_V2.md",
    ]

    for token in required_tokens:
        assert token in agent
        assert token in harness


def test_rule_doc_sync_standard_states_code_only_updates_are_invalid() -> None:
    harness = (ROOT / "docs" / "DEVELOPMENT_HARNESS_V2.md").read_text(encoding="utf-8")
    assert "不能只改代码、不改规则文档" in harness
    assert "规则变化就必须同步文档" in harness
