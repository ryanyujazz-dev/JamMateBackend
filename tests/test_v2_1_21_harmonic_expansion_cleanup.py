from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import ContentFamily, RootSupportPolicy
from jammate_engine.core.voicing.sources.chord_tone_resolver import content_degree_names
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION

ROOT = Path(__file__).resolve().parents[1]


def test_v2_1_21_version_and_contract_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_OVERRIDE_CONTRACT_VERSION == "v2_1_43"


def test_v2_1_21_legacy_halfdim_rootless_11_shortcut_is_removed() -> None:
    assert content_degree_names("Gm7b5", ContentFamily.ROOTLESS_A, RootSupportPolicy.ROOTLESS_ALLOWED) == ["b3", "b5", "b7", "b9"]
    assert content_degree_names("Gm7b5", ContentFamily.ROOTLESS_B, RootSupportPolicy.ROOTLESS_ALLOWED) == ["b7", "b9", "b3", "b5"]
    assert content_degree_names("Gm9b5", ContentFamily.ROOTLESS_A, RootSupportPolicy.ROOTLESS_ALLOWED) == ["b3", "b5", "b7", "9"]


def test_v2_1_21_historical_generated_demo_artifacts_are_not_packaged() -> None:
    demo_dir = ROOT / "demos"
    historical_outputs = [
        path
        for path in demo_dir.rglob("*")
        if path.is_file()
        and path.suffix in {".mid", ".json", ".md"}
        and path.name != "README.md"
        and not path.name.startswith(f"{ENGINE_VERSION_TAG}_")
    ]
    assert historical_outputs == []


def test_v2_1_21_harmonic_expansion_definition_is_documented() -> None:
    required_docs = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "VOICING_MODULE_CORE_LOGIC_V2.md",
        ROOT / "docs" / "VOICING_SYSTEM_V2_DESIGN.md",
        ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md",
        ROOT / "docs" / "STYLE_RULE_BASELINE_V2.md",
        ROOT / "docs" / "VOICING_TUNING_WORKFLOW_V2.md",
        ROOT / "docs" / "DEVELOPMENT_HARNESS_V2.md",
        ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md",
        ROOT / "docs" / "API_CONTRACT_V2.md",
        ROOT / "docs" / "SYSTEM_CONTRACTS_V2.md",
        ROOT / "docs" / "ARCHITECTURE_V2.md",
    ]
    for path in required_docs:
        text = path.read_text(encoding="utf-8")
        assert "v2_1_21" in text, path
        assert "Harmonic expansion does not replace the chord" in text, path
        assert "generated demo artifacts are not packaged" in text, path
