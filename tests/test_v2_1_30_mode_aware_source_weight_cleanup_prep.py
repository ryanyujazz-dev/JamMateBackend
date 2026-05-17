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
)
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION
from jammate_engine.core.voicing.selection.scorer import score_candidate
from jammate_engine.styles.bossa_nova.voicing_policy import get_voicing_policy as bossa_policy
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as swing_policy

ROOT = Path(__file__).resolve().parents[1]


def _policy(*, expansion: bool) -> VoicingPolicy:
    return VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(ContentFamily.SEVENTH_BASIC, ContentFamily.ROOTED_COLOR, ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B),
        preferred_content=ContentFamily.ROOTLESS_A,
        harmonic_expansion_enabled=expansion,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS if expansion else ColorPolicyMode.CHORD_SYMBOL_ONLY,
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED,),
        min_density=4,
        preferred_density=4,
        max_density=4,
        source_family_weights={"root_third_fifth_seventh": -0.03},
        source_family_weights_by_gate={
            "explicit_chart_color": {"third_fifth_seventh_ninth": 0.31},
            "harmonic_expansion": {"third_fifth_seventh_ninth": 0.11},
        },
        selector_temperature=0.0,
        selection_pool_size=1,
    )


def _first_functional_source(symbol: str, policy: VoicingPolicy, source_type: str):
    for candidate in generate_candidates(symbol, policy):
        if candidate.metadata.get("rootless_ab_functional_source_type") == source_type:
            return candidate
    raise AssertionError(f"missing {source_type} for {symbol}")


def test_v2_1_37_policy_supports_mode_aware_source_weight_contract() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_OVERRIDE_CONTRACT_VERSION == "v2_1_43"

    policy = VoicingPolicy.from_legacy_dict(
        {
            "source_family_weights": {"root_third_fifth_seventh": -0.04},
            "source_family_weights_by_gate": {
                "explicit_chart_color": {"third_fifth_seventh_ninth": 0.32},
                "harmonic_expansion": {"third_fifth_seventh_ninth": 0.12},
            },
        }
    )
    debug = policy.to_debug_dict()
    assert debug["source_family_weights"]["root_third_fifth_seventh"] == -0.04
    assert debug["source_family_weights_by_gate"]["explicit_chart_color"]["third_fifth_seventh_ninth"] == 0.32
    assert debug["source_family_weights_by_gate"]["harmonic_expansion"]["third_fifth_seventh_ninth"] == 0.12


def test_v2_1_37_mode_aware_source_weights_distinguish_chart_color_from_expansion() -> None:
    explicit_policy = _policy(expansion=False)
    expansion_policy = _policy(expansion=True)

    explicit_candidate = _first_functional_source("Cmaj9", explicit_policy, "third_fifth_seventh_ninth")
    expansion_candidate = _first_functional_source("Cmaj7", expansion_policy, "third_fifth_seventh_ninth")

    explicit_details = score_candidate(explicit_candidate, explicit_policy).details
    expansion_details = score_candidate(expansion_candidate, expansion_policy).details

    assert explicit_details["four_note_source_balance_gate_mode"] == "explicit_chart_color"
    assert expansion_details["four_note_source_balance_gate_mode"] == "harmonic_expansion"
    assert explicit_details["four_note_source_balance_score"] == 0.31
    assert expansion_details["four_note_source_balance_score"] == 0.11


def test_v2_1_37_swing_and_bossa_allow_gated_rooted_color_candidates() -> None:
    assert ContentFamily.ROOTED_COLOR in swing_policy().allowed_content
    assert ContentFamily.ROOTED_COLOR in bossa_policy().allowed_content

    audit = build_four_note_source_balance_audit(
        ["Cmaj9", "G13", "C6/9"],
        {"swing": swing_policy(), "bossa": bossa_policy()},
    )
    rows = [row.to_debug_dict() for row in audit.rows]
    assert any(row["policy_label"] == "swing" and row["content_family"] == ContentFamily.ROOTED_COLOR.value for row in rows)
    assert any(row["policy_label"] == "bossa" and row["content_family"] == ContentFamily.ROOTED_COLOR.value for row in rows)
    assert all(row["gate_reason"] != "unknown" for row in rows)


def test_v2_1_37_explicit_rootless_sources_have_functional_role_metadata() -> None:
    audit = build_four_note_source_balance_audit(
        ["Cmaj7", "Cmaj9", "G13", "Dm11", "Cmaj7#11", "G7b9b13", "G7alt"],
        {"symbol_only": _policy(expansion=False), "expansion": _policy(expansion=True)},
    )
    rows = [row.to_debug_dict() for row in audit.rows]
    rootless_rows = [row for row in rows if row["content_family"] in {ContentFamily.ROOTLESS_A.value, ContentFamily.ROOTLESS_B.value}]
    assert rootless_rows
    assert all(row["degree_role_order"] != "unknown" for row in rootless_rows)
    assert all(row["source_family"] != "unknown" for row in rows)
    assert any(row["source_balance_gate_mode"] == "explicit_chart_color" for row in rows)
    assert any(row["source_balance_gate_mode"] == "harmonic_expansion" for row in rows)


def test_v2_1_37_docs_are_updated() -> None:
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
