from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    ContentFamily,
    FOUR_NOTE_SOURCE_BALANCE_AUDIT_VERSION,
    build_four_note_source_balance_audit,
)
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION
from jammate_engine.styles.bossa_nova.voicing_policy import get_voicing_policy as bossa_policy
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy as ballad_policy
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as swing_policy
from examples.scripts.generate_4note_source_balance_audit_report import SYMBOLS

REQUIRED_GATES = {
    "chord_symbol_only",
    "harmonic_expansion",
    "explicit_chart_color",
    "explicit_chart_color_plus_harmonic_expansion",
}

REQUIRED_AUDIT_SYMBOLS = {
    "Cmaj7",
    "Cmaj9",
    "Cmaj7#11",
    "C6/9",
    "Dm7",
    "Dm9",
    "Dm11",
    "Dm13",
    "G7",
    "G9",
    "G13",
    "G7#11",
    "G7b9",
    "G7#9",
    "G7b13",
    "G7b9b13",
    "G7alt",
    "Bm7b5",
    "Bm9b5",
    "Bm11b5",
}

CORE_SOURCE_WEIGHT_KEYS = {
    "root_third_fifth_seventh",
    "third_fifth_seventh_ninth",
    "third_thirteenth_seventh_ninth",
    "root_third_fifth_ninth",
    "root_third_sixth_ninth",
    "root_third_seventh_eleventh",
    "third_fifth_seventh_eleventh",
    "third_eleventh_fifth_seventh",
    "third_seventh_ninth_eleventh",
    "root_third_seventh_thirteenth",
    "root_third_seventh_altered_color",
    "third_seventh_altered_color_a_altered_color_b",
}


def test_v2_1_37_contract_versions_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_OVERRIDE_CONTRACT_VERSION == "v2_1_43"
    assert FOUR_NOTE_SOURCE_BALANCE_AUDIT_VERSION == "v2_1_37"


def test_v2_1_37_audit_symbol_set_covers_listening_prep_chords() -> None:
    assert REQUIRED_AUDIT_SYMBOLS.issubset(set(SYMBOLS))


def test_v2_1_37_three_styles_expose_four_gate_source_weight_maps() -> None:
    for label, policy in {
        "medium_swing": swing_policy(),
        "bossa_nova": bossa_policy(),
        "jazz_ballad": ballad_policy(),
    }.items():
        assert not dict(policy.source_family_weights or {}), label
        by_gate = dict(policy.source_family_weights_by_gate or {})
        assert REQUIRED_GATES.issubset(set(by_gate)), label
        assert "root_third_fifth_seventh" in by_gate["chord_symbol_only"], label
        weighted_keys = set().union(*(set(weights) for weights in by_gate.values()))
        assert CORE_SOURCE_WEIGHT_KEYS.issubset(weighted_keys), label


def test_v2_1_37_audit_rows_cover_new_symbols_and_style_weight_modes() -> None:
    audit = build_four_note_source_balance_audit(
        ["G9", "G7#9", "G7b13", "Bm11b5"],
        {
            "medium": swing_policy(),
            "bossa": bossa_policy(),
            "ballad": ballad_policy(),
        },
    )
    rows = [row.to_debug_dict() for row in audit.rows]
    assert {row["symbol"] for row in rows} == {"G9", "G7#9", "G7b13", "Bm11b5"}
    assert all(row["gate_reason"] != "unknown" for row in rows)
    assert any(row["source_balance_gate_mode"] == "chord_symbol_only" for row in rows)
    assert any(row["source_balance_gate_mode"] == "explicit_chart_color" for row in rows)
    assert any(row["source_balance_gate_mode"] == "explicit_chart_color_plus_harmonic_expansion" for row in rows)
    assert any(row["symbol"] == "Bm11b5" and row["source_family"] == "third_eleventh_fifth_seventh" for row in rows)
    assert any(row["symbol"] == "G7#9" and row["functional_source_type"] == "root_third_seventh_altered_color" for row in rows)
    assert any(row["content_family"] in {ContentFamily.ROOTLESS_A.value, ContentFamily.ROOTLESS_B.value} for row in rows)


def test_v2_1_37_docs_are_synced_for_source_weight_pass() -> None:
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
        assert "4-Note Source Weight Implementation / Listening Prep Pass" in text, path
        assert "four_mode_aware" in text, path
        assert "G9 / G7#9 / G7b13 / Bm11b5" in text, path
