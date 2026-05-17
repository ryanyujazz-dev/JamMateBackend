from __future__ import annotations

from jammate_engine.core.voicing.disposition import (
    BALLAD_SPREAD_GROUPING_MIX_DEFAULT_WEIGHTS,
    BALLAD_SPREAD_GROUPING_MIX_POLICY_VERSION,
    BalladSpreadGroupingMixScene,
    ballad_spread_grouping_mix_policy_debug,
    resolve_ballad_spread_grouping_mix_policy,
)


def _policy(enabled: bool = True) -> dict:
    return {
        "metadata": {
            "ballad_spread_grouping_mix_policy": {
                "enabled": enabled,
                "weight_cycle": 100,
            }
        }
    }


def test_ballad_spread_grouping_mix_default_disabled() -> None:
    decision = resolve_ballad_spread_grouping_mix_policy({}, event_context={"region_id": "c0_b1_ch0"})
    assert decision.enabled is False
    assert decision.selected_contract_id is None
    assert decision.runtime_enabled is False
    assert decision.style_runtime_default_enabled is False


def test_ballad_spread_grouping_mix_scene_weights_match_draft() -> None:
    assert BALLAD_SPREAD_GROUPING_MIX_POLICY_VERSION == "v2_2_84"
    normal = BALLAD_SPREAD_GROUPING_MIX_DEFAULT_WEIGHTS[BalladSpreadGroupingMixScene.NORMAL_COMPING.value]
    lift = BALLAD_SPREAD_GROUPING_MIX_DEFAULT_WEIGHTS[BalladSpreadGroupingMixScene.CHORUS_LIFT.value]
    climax = BALLAD_SPREAD_GROUPING_MIX_DEFAULT_WEIGHTS[BalladSpreadGroupingMixScene.ENDING_CLIMAX.value]
    assert "spread_1plus3_contract" not in normal
    assert "spread_1plus3_contract" not in lift
    assert "spread_1plus3_contract" not in climax
    assert normal["spread_1plus4_contract"] == 40
    assert normal["spread_3plus4_contract"] == 0
    assert lift["spread_3plus4_contract"] == 5
    assert climax["spread_3plus4_contract"] == 35
    assert sum(normal.values()) == 100
    assert sum(lift.values()) == 100
    assert sum(climax.values()) == 100


def test_ballad_spread_grouping_mix_event_scene_and_selection() -> None:
    first_chorus = resolve_ballad_spread_grouping_mix_policy(
        _policy(), event_context={"region_id": "c0_b1_ch0", "region_chorus_index": 0, "region_total_choruses": 3}
    )
    second_chorus = resolve_ballad_spread_grouping_mix_policy(
        _policy(), event_context={"region_id": "c1_b1_ch0", "region_chorus_index": 1, "region_total_choruses": 3}
    )
    ending = resolve_ballad_spread_grouping_mix_policy(
        _policy(), event_context={"region_id": "c2_b30_ch0", "region_chorus_index": 2, "region_total_choruses": 3, "region_bar_index": 30}
    )
    assert first_chorus.scene == BalladSpreadGroupingMixScene.NORMAL_COMPING
    assert second_chorus.scene == BalladSpreadGroupingMixScene.CHORUS_LIFT
    assert ending.scene == BalladSpreadGroupingMixScene.ENDING_CLIMAX
    assert first_chorus.selected_contract_id in first_chorus.weights
    assert ending.selected_contract_id in ending.weights
    assert first_chorus.weights["spread_3plus4_contract"] == 0
    assert ending.weights["spread_3plus4_contract"] > 0
    assert first_chorus.selected_contract_id != "spread_1plus3_contract"
    assert second_chorus.selected_contract_id != "spread_1plus3_contract"
    assert ending.selected_contract_id != "spread_1plus3_contract"


def test_ballad_spread_grouping_mix_debug_remains_policy_audit_only() -> None:
    payload = ballad_spread_grouping_mix_policy_debug(
        _policy(), event_context={"region_id": "c0_b1_ch0", "region_chorus_index": 0, "region_total_choruses": 3}
    )
    assert payload["runtime_enabled"] is False
    assert payload["candidate_conversion_allowed"] is False
    assert payload["style_runtime_default_enabled"] is False
    assert payload["decision"]["enabled"] is True
