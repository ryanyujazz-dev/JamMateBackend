from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import VOICING_CONTRACT_VERSION


def _read(rel: str) -> str:
    return Path(rel).read_text(encoding="utf-8")


def test_v2_2_20_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_CONTRACT_VERSION == "v2_2_21"
    assert _read("VERSION").strip() == "v2_3_9"


def test_voicing_texture_state_architecture_doc_exists_and_sets_boundary() -> None:
    doc = _read("docs/VOICING_TEXTURE_STATE_ARCHITECTURE_V2.md")
    for token in (
        "VoicingTextureIntent",
        "VoicingTextureState",
        "LLM",
        "texture_plan.py",
        "Disposition Projection",
        "method lock",
        "family",
        "Capability Reuse Before New Construction",
    ):
        assert token in doc
    assert "Do not place `VoicingTextureState` in" in doc
    assert "core/voicing/disposition/" in doc


def test_core_docs_reference_v2_2_20_texture_state_plan() -> None:
    combined = "\n".join(
        _read(rel)
        for rel in (
            "agent.md",
            "README.md",
            "docs/DEVELOPMENT_TASK_PLAN_V2.md",
            "docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md",
            "docs/VOICING_SYSTEM_V2_DESIGN.md",
        )
    )
    assert "v2_2_20 update — VoicingTextureState / LLM Intent Architecture Planning" in combined
    assert "the next engineering target should be selected by the user" in combined
