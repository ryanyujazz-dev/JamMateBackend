from __future__ import annotations

from pathlib import Path

from jammate_engine.generation.bass_foundation import (
    BassFoundationGenerator,
    BassFoundationPolicy,
    build_bass_foundation_audit,
    root_zone,
)


ROOT = Path(__file__).resolve().parents[1]


def test_bass_foundation_runtime_rules_are_organized_as_domain_package() -> None:
    package_root = ROOT / "src" / "jammate_engine" / "generation" / "bass_foundation"
    expected = {"__init__.py", "policy.py", "models.py", "rules.py", "generator.py", "audit.py"}
    assert expected.issubset({path.name for path in package_root.iterdir()})
    assert not (ROOT / "src" / "jammate_engine" / "generation" / "bass_foundation_generation.py").exists()
    assert not (ROOT / "src" / "jammate_engine" / "generation" / "bass_foundation_audit.py").exists()
    assert BassFoundationGenerator is not None
    assert BassFoundationPolicy.from_dict({}).register_low == 26
    assert build_bass_foundation_audit is not None
    assert root_zone(44) == "high"


def test_bass_foundation_rule_organization_is_documented() -> None:
    docs = (ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md").read_text(encoding="utf-8")
    assert "规则包组织方式" in docs
    assert "generation/bass_foundation/" in docs
    assert "policy.py" in docs
    assert "generator.py" in docs
    assert "audit.py" in docs
