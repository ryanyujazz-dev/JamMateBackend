from __future__ import annotations

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
from jammate_engine.core.voicing.selection.selector import select_candidate
from jammate_engine.styles.bossa_nova.voicing_policy import get_voicing_policy as bossa_policy
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy as ballad_policy
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as swing_policy


def _probe_policy(*, expansion: bool = False) -> VoicingPolicy:
    return VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(
            ContentFamily.SEVENTH_BASIC,
            ContentFamily.ROOTED_COLOR,
            ContentFamily.ROOTLESS_A,
            ContentFamily.ROOTLESS_B,
        ),
        preferred_content=ContentFamily.ROOTLESS_A if expansion else ContentFamily.SEVENTH_BASIC,
        harmonic_expansion_enabled=expansion,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS if expansion else ColorPolicyMode.CHORD_SYMBOL_ONLY,
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED, Disposition.OPEN),
        preferred_density=4,
        min_density=4,
        max_density=4,
        source_family_weights={
            "with_5": 0.25,
            "with_13": -0.25,
            "root_third_fifth_seventh": -0.10,
            "root_third_seventh_thirteenth": 0.15,
        },
        selector_temperature=0.0,
        selection_pool_size=1,
    )


def test_v2_1_27_source_family_weights_are_policy_contract() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_OVERRIDE_CONTRACT_VERSION == "v2_1_43"

    policy = VoicingPolicy.from_legacy_dict(
        {
            "source_family_weights": {
                "with_5": 0.12,
                "with_13": -0.10,
                "root_third_fifth_ninth": 0.20,
            }
        }
    )
    debug = policy.to_debug_dict()
    assert debug["source_family_weights"]["with_5"] == 0.12
    assert debug["source_family_weights"]["with_13"] == -0.10
    assert debug["source_family_weights"]["root_third_fifth_ninth"] == 0.20


def test_v2_1_27_audit_has_no_legacy_or_unknown_4note_rows_after_balance_cleanup() -> None:
    audit = build_four_note_source_balance_audit(
        ["Bm7b5", "G13", "G7alt", "G7sus4"],
        {
            "chord_symbol_only": _probe_policy(expansion=False),
            "harmonic_expansion": _probe_policy(expansion=True),
            "style_medium_swing": swing_policy(),
            "style_bossa_nova": bossa_policy(),
            "style_jazz_ballad": ballad_policy(),
        },
    )
    rows = [row.to_debug_dict() for row in audit.rows]
    assert rows
    assert all(row["source_family"] != "rooted_color_legacy_fallback" for row in rows)
    assert all(row["source_family"] != "unknown" for row in rows)
    assert all(row["gate_reason"] != "unknown" for row in rows)
    assert any(row["source_family"] == "root_third_seventh_thirteenth" for row in rows if row["symbol"] == "G13")


def test_v2_1_27_style_source_balance_weights_show_in_audit() -> None:
    audit = build_four_note_source_balance_audit(
        ["Cmaj9", "G13", "G7alt"],
        {
            "style_medium_swing": swing_policy(),
            "style_bossa_nova": bossa_policy(),
            "style_jazz_ballad": ballad_policy(),
        },
    )
    rows = [row.to_debug_dict() for row in audit.rows]
    assert any(row["policy_label"] == "style_medium_swing" and row["legacy_alias"] == "with_5" and row["source_balance_weight"] > 0 for row in rows)
    assert any(row["policy_label"] == "style_bossa_nova" and row["legacy_alias"] == "with_13" and row["source_balance_weight"] < 0 for row in rows)
    assert any(row["policy_label"] == "style_jazz_ballad" and row["source_family"] == "root_third_seventh_ninth" and row["source_balance_weight"] > 0 for row in rows)


def test_v2_1_27_source_balance_score_is_applied_after_gate() -> None:
    policy = _probe_policy(expansion=True)
    candidates = generate_candidates("Cmaj7", policy)
    selected = select_candidate(candidates, policy=policy)
    score = selected.metadata["score_breakdown"]["details"]
    assert score["four_note_source_balance_key"]
    assert "four_note_source_balance_score" in score
