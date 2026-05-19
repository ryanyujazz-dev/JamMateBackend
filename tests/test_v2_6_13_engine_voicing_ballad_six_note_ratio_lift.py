from __future__ import annotations

# harness token: test_v2_6_13_engine_voicing_ballad_six_note_ratio_lift

from collections import Counter
from pathlib import Path
import json

from jammate_engine.core.voicing.disposition.spread_voice_leading import (
    SPREAD_GROUPWISE_VOICE_LEADING_SPLIT_VERSION,
    spread_grouping_mix_contract_intent_cost,
    spread_grouping_mix_contract_intent_debug,
)
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SIX_NOTE_RATIO_LIFT_V2_6_13.md"
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


def test_v2_6_13_doc_exists_and_states_scope() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "v2_6_13_engine_voicing_ballad_six_note_ratio_lift",
        "6-note",
        "spread_grouping_mix_selected_6note_contract_bias",
        "core.voicing.disposition.spread_voice_leading",
        "Pattern",
        "Anticipation",
        "Expression",
        "MIDI",
    ]
    for token in required:
        assert token in text


def test_v2_6_13_selected_6note_contract_bias_is_owned_by_spread_voice_leading() -> None:
    policy = get_voicing_policy()
    assert SPREAD_GROUPWISE_VOICE_LEADING_SPLIT_VERSION == "v2_6_12"
    assert float(policy.metadata["spread_grouping_mix_selected_6note_contract_bias"]) >= 0.20

    matching = _Candidate("spread_2plus4_contract")
    neighbor = _Candidate("spread_2plus3_contract")
    unrelated = _Candidate("spread_3plus4_contract")

    assert spread_grouping_mix_contract_intent_cost(matching, policy) < 0
    assert spread_grouping_mix_contract_intent_cost(neighbor, policy) > 0
    assert spread_grouping_mix_contract_intent_cost(unrelated, policy) == 0

    debug = spread_grouping_mix_contract_intent_debug(matching, policy)
    assert debug["implementation_owner"] == "core.voicing.disposition.spread_voice_leading"
    assert debug["notes_only"] is True
    assert debug["no_expression_or_pedal"] is True


def test_v2_6_13_misty_ballad_six_note_ratio_is_lifted_without_breaking_guards(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_13.mid"),
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

    # v2_6_12 Misty audit had 8 six-note voicings.  v2_6_13 introduced
    # the selected-contract bias knob; later voicing-only calibration passes may
    # raise this further while preserving retired 4-note and maj7#11 guards.
    assert densities[6] >= 10
    assert recipes["spread_2plus3_contract"] >= recipes["spread_2plus4_contract"]

    maj7_sharp11 = [
        voicing for voicing in voicings
        if "maj7" in str(voicing.get("chord_symbol"))
        and any(str(degree) == "#11" for degree in voicing.get("degrees", []))
    ]
    assert maj7_sharp11 == []
