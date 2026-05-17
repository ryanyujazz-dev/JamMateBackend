from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG

ROOT = Path(__file__).resolve().parents[1]


def test_v2_2_0_version_and_documentation_audit_exist() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    audit = ROOT / "docs" / "PROJECT_DOCUMENTATION_AUDIT_V2.md"
    assert audit.exists()
    text = audit.read_text(encoding="utf-8")
    assert "Current audit version: `v2_2_10`" in text
    assert "Source-of-truth matrix" in text
    assert "Canonical reading path" in text
    assert "Documentation update policy" in text


def test_v2_2_0_documentation_audit_records_no_new_docs_subfolder_decision() -> None:
    text = (ROOT / "docs" / "PROJECT_DOCUMENTATION_AUDIT_V2.md").read_text(encoding="utf-8")
    assert "No new docs subfolder is needed" in text
    assert "Minimal File Split Principle" in (ROOT / "docs" / "DEVELOPMENT_HARNESS_V2.md").read_text(encoding="utf-8")
    assert "PROJECT_DOCUMENTATION_AUDIT_V2.md" in (ROOT / "agent.md").read_text(encoding="utf-8")


def test_v2_2_0_canonical_docs_are_mapped() -> None:
    text = (ROOT / "docs" / "PROJECT_DOCUMENTATION_AUDIT_V2.md").read_text(encoding="utf-8")
    for token in [
        "docs/ARCHITECTURE_V2.md",
        "docs/PIPELINE_V2.md",
        "docs/API_CONTRACT_V2.md",
        "docs/GENERATION_RULES_SUMMARY_V2.md",
        "docs/STYLE_RULE_BASELINE_V2.md",
        "docs/VOICING_SYSTEM_V2_DESIGN.md",
        "docs/VOICING_MODULE_CORE_LOGIC_V2.md",
        "docs/VOICING_TUNING_WORKFLOW_V2.md",
        "docs/FUTURE_IDEAS_BACKLOG_V2.md",
    ]:
        assert token in text
