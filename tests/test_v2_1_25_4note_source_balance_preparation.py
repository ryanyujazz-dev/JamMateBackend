from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    ColorPolicyMode,
    ContentFamily,
    Disposition,
    RootSupportPolicy,
    VoicingPolicy,
    build_four_note_source_balance_audit,
    format_four_note_source_balance_audit_report,
)
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION

ROOT = Path(__file__).resolve().parents[1]


def _probe_policy(*, expansion: bool = False) -> VoicingPolicy:
    return VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(
            ContentFamily.SEVENTH_BASIC,
            ContentFamily.ROOTED_COLOR,
            ContentFamily.ROOTLESS_A,
            ContentFamily.ROOTLESS_B,
        ),
        preferred_content=ContentFamily.SEVENTH_BASIC if not expansion else ContentFamily.ROOTLESS_A,
        harmonic_expansion_enabled=expansion,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS if expansion else ColorPolicyMode.CHORD_SYMBOL_ONLY,
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED, Disposition.OPEN),
        min_density=4,
        preferred_density=4,
        max_density=4,
        max_voicing_span=24,
        selection_pool_size=8,
        selector_temperature=0.20,
    )


def test_v2_1_27_source_audit_exposes_gate_modes_before_ratio_tuning() -> None:
    audit = build_four_note_source_balance_audit(
        ["Cmaj7", "Cmaj9", "G7alt", "Bm7b5", "Bm9b5"],
        {
            "chord_symbol_only": _probe_policy(expansion=False),
            "harmonic_expansion": _probe_policy(expansion=True),
        },
    )
    rows = [row.to_debug_dict() for row in audit.rows]

    cmaj7_symbol_only = [row for row in rows if row["policy_label"] == "chord_symbol_only" and row["symbol"] == "Cmaj7"]
    assert cmaj7_symbol_only
    assert {row["content_family"] for row in cmaj7_symbol_only} == {ContentFamily.SEVENTH_BASIC.value}
    assert {row["source_family"] for row in cmaj7_symbol_only} == {"root_third_fifth_seventh"}
    assert {row["gate_reason"] for row in cmaj7_symbol_only} == {"basic_4note_conservative_chord_symbol_material"}

    cmaj9_symbol_only = [row for row in rows if row["policy_label"] == "chord_symbol_only" and row["symbol"] == "Cmaj9"]
    assert any(row["source_family"] == "root_third_seventh_ninth" for row in cmaj9_symbol_only)
    assert any(row["legacy_alias"] == "with_5" for row in cmaj9_symbol_only)
    assert any(row["gate_reason"] == "four_note_color_gate_open_explicit_chord_symbol_color" for row in cmaj9_symbol_only)

    cmaj7_expansion = [row for row in rows if row["policy_label"] == "harmonic_expansion" and row["symbol"] == "Cmaj7"]
    assert any(row["legacy_alias"] == "with_5" for row in cmaj7_expansion)
    assert any(row["legacy_alias"] == "with_13" for row in cmaj7_expansion)
    assert any(row["gate_reason"] == "four_note_color_gate_open_harmonic_expansion" for row in cmaj7_expansion)

    g7alt_rows = [row for row in rows if row["symbol"] == "G7alt"]
    assert any(row["legacy_alias"] == "altered_dominant_rootless" for row in g7alt_rows)
    assert any(row["source_family"] == "root_third_seventh_altered_color_a" for row in g7alt_rows)

    bm7b5_expansion = [row for row in rows if row["policy_label"] == "harmonic_expansion" and row["symbol"] == "Bm7b5"]
    assert any(row["legacy_alias"] == "with_5" and "b9" in row["degree_order"] for row in bm7b5_expansion)
    assert all(row["source_family"] != "half_diminished_locrian_rootless" for row in bm7b5_expansion)

    report = format_four_note_source_balance_audit_report(audit)
    assert "4-Note Source Balance Decision Audit" in report
    assert "before and during weighted selection" in report
    assert "root_third_fifth_seventh" in report


def test_v2_1_27_contract_and_docs_are_updated() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_OVERRIDE_CONTRACT_VERSION == "v2_1_43"

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
        assert "v2_1_37" in text, path
        assert "Mode-Aware Source Weight" in text, path
        assert "source_family_weights_by_gate" in text, path
