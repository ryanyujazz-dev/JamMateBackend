from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import VOICING_CONTRACT_VERSION

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v2_2_12_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_CONTRACT_VERSION == "v2_2_21"
    assert _read("VERSION").strip() == "v2_3_9"


def test_capability_reuse_rule_is_documented_in_harness_sources() -> None:
    targets = [
        "agent.md",
        "docs/DEVELOPMENT_HARNESS_V2.md",
        "docs/NEW_FILE_PLACEMENT_GUIDE_V2.md",
    ]
    for rel in targets:
        text = _read(rel)
        assert "Capability Reuse Before New Construction" in text
        assert "reuse audit" in text
        assert "local implementation" in text
        assert "adapter" in text
        assert "facade" in text
        assert "metadata" in text
        assert "core/harmony/harmonic_context.py" in text


def test_development_harness_checks_capability_reuse_rule() -> None:
    harness = _read("tools/check_development_harness.py")
    assert "check_capability_reuse_before_new_construction_documented" in harness
    assert "Capability Reuse Before New Construction" in harness
    assert "core/harmony/harmonic_context.py" in harness
