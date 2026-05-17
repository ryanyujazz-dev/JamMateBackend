from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v2_3_9_pedal_policy_boundary_is_documented() -> None:
    doc = read("docs/PEDAL_POLICY_EXPRESSION_BOUNDARY_V2_3_9.md")
    for token in (
        "Pedal is an expression-level musical decision",
        "Pattern must not directly emit CC64",
        "Expression policy should consider",
        "MIDI realizer must not invent musical pedal intent",
        "re-pedal offset",
        "Bossa and Medium Swing remain dry by default",
        "Jazz Ballad may use light or sustain pedal",
    ):
        assert token in doc


def test_v2_3_9_core_docs_reference_pedal_policy_boundary() -> None:
    docs = (
        read("agent.md")
        + read("docs/SYSTEM_CONTRACTS_V2.md")
        + read("docs/PIPELINE_V2.md")
        + read("docs/GENERATION_RULES_SUMMARY_V2.md")
        + read("docs/STYLE_RULE_BASELINE_V2.md")
    )
    for token in (
        "PEDAL_POLICY_EXPRESSION_BOUNDARY_V2_3_9.md",
        "Patterns expose pedal-relevant facts",
        "Expression chooses",
        "MIDI realizer",
        "Bossa",
        "Medium Swing",
        "Jazz Ballad",
    ):
        assert token in docs
