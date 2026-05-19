from __future__ import annotations

# harness token: test_v2_6_14_engine_voicing_ballad_spread_5_to_6_ratio_calibration

from collections import Counter
from pathlib import Path
import json

from jammate_engine.core.voicing.disposition.spread_voice_leading import (
    spread_grouping_mix_contract_intent_cost,
)
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SPREAD_5_TO_6_RATIO_CALIBRATION_V2_6_14.md"
MISTY = ROOT / "examples" / "leadsheets" / "misty.json"


class _Candidate:
    def __init__(self, recipe_id: str, selected_contract_id: str = "spread_2plus4_contract") -> None:
        self.metadata = {
            "recipe_id": recipe_id,
            "ballad_spread_grouping_mix_policy_decision": {
                "selected_contract_id": selected_contract_id,
            },
        }


def _voicing_events(debug: dict) -> list[dict]:
    return [event.get("voicing") or {} for event in debug.get("piano_musical_audit_events", [])]


def test_v2_6_14_doc_exists_and_states_voicing_only_ratio_scope() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "v2_6_14_engine_voicing_ballad_spread_5_to_6_ratio_calibration",
        "5-note:6-note",
        "6:4",
        "spread_grouping_mix_selected_6note_contract_bias",
        "Pattern",
        "Anticipation",
        "Expression",
        "MIDI",
    ]
    for token in required:
        assert token in text


def test_v2_6_14_policy_bias_targets_selected_six_note_contracts_only() -> None:
    policy = get_voicing_policy()
    assert float(policy.metadata["spread_grouping_mix_selected_6note_contract_bias"]) >= 3.0
    # Integration v2_8_24 note: Engine v2_6_30 keeps the ratio target while
    # adding low-frequency 1+4 restoration wording to the metadata label.
    assert policy.metadata["ballad_spread_5_to_6_density_ratio_target"]["target"].startswith("5-note:6-note ~= 6:4")

    selected_6 = _Candidate("spread_2plus4_contract")
    selected_5_neighbor = _Candidate("spread_2plus3_contract")
    unrelated_7 = _Candidate("spread_3plus4_contract")

    assert spread_grouping_mix_contract_intent_cost(selected_6, policy) < -2.5
    assert spread_grouping_mix_contract_intent_cost(selected_5_neighbor, policy) > 0.0
    assert spread_grouping_mix_contract_intent_cost(unrelated_7, policy) == 0.0


def test_v2_6_14_misty_ballad_5_to_6_density_ratio_is_approximately_6_to_4(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_14.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    voicings = _voicing_events(result.debug)
    assert len(voicings) >= 180

    densities = Counter(int(voicing.get("density", 0)) for voicing in voicings)
    groupings = Counter(str(voicing.get("functional_grouping")) for voicing in voicings)
    recipes = Counter(str(voicing.get("recipe_id")) for voicing in voicings)
    dispositions = Counter(str(voicing.get("disposition")) for voicing in voicings)

    assert set(dispositions) == {"spread"}
    assert densities[4] == 0
    assert "1+3" not in groupings
    assert "2+2" not in groupings
    assert "spread_1plus3_contract" not in recipes
    assert "spread_2plus2_contract" not in recipes

    five = densities[5]
    six = densities[6]
    assert five > 0 and six > 0
    ratio = five / float(five + six)
    assert 0.58 <= ratio <= 0.62
    assert densities[7] <= 3

    maj7_sharp11 = [
        voicing for voicing in voicings
        if "maj7" in str(voicing.get("chord_symbol"))
        and any(str(degree) == "#11" for degree in voicing.get("degrees", []))
    ]
    assert maj7_sharp11 == []
