from __future__ import annotations

from collections import Counter
from pathlib import Path
import json

from jammate_engine.core.voicing import (
    VOICING_DENSITY_DISPOSITION_POLICY_VERSION,
    SPREAD_RETIRED_FOUR_NOTE_GROUPINGS,
    density_disposition_decision,
)
from jammate_engine.core.voicing.disposition import Disposition
from jammate_engine.core.voicing.disposition.spread import (
    spread_recipe_contract_skeleton,
    project_basic_spread_candidates,
)
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_SPREAD_DENSITY_SYSTEM_RESET_V2_6_10.md"
MISTY = ROOT / "examples" / "leadsheets" / "misty.json"


def _voicing_events(debug: dict) -> list[dict]:
    return [event.get("voicing") or {} for event in debug.get("piano_musical_audit_events", [])]


def test_v2_6_10_doc_exists_and_states_density_reset_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "v2_6_10_engine_voicing_spread_density_system_reset",
        "4-note SPREAD 1+3 / 2+2 retired",
        "density/disposition routing",
        "spread_2plus3_contract",
        "spread_2plus4_contract",
        "not a scorer patch",
        "Pattern",
        "Expression",
        "MIDI",
    ]
    for token in required:
        assert token in text


def test_v2_6_10_density_disposition_policy_blocks_legacy_four_note_spread() -> None:
    policy = get_voicing_policy()
    for grouping in SPREAD_RETIRED_FOUR_NOTE_GROUPINGS:
        decision = density_disposition_decision(
            disposition=Disposition.SPREAD,
            density=4,
            functional_grouping=grouping,
            policy=policy,
        )
        assert decision.version == VOICING_DENSITY_DISPOSITION_POLICY_VERSION == "v2_6_10"
        assert decision.allowed is False
        assert decision.reason == "legacy_4note_spread_grouping_retired_use_5plus_grouped_spread_contracts"

    open_decision = density_disposition_decision(
        disposition=Disposition.OPEN,
        density=4,
        functional_grouping="2+2",
        policy=policy,
    )
    assert open_decision.allowed is True


def test_v2_6_10_default_spread_contract_skeleton_excludes_legacy_four_note_groupings() -> None:
    contracts = spread_recipe_contract_skeleton()
    signature = tuple((contract.recipe_id, contract.grouping.value, contract.density) for contract in contracts)
    assert signature == (
        ("spread_1plus4_contract", "1+4", 5),
        ("spread_2plus3_contract", "2+3", 5),
        ("spread_2plus4_contract", "2+4", 6),
        ("spread_3plus3_contract", "3+3", 6),
        ("spread_3plus4_contract", "3+4", 7),
    )
    assert all(grouping not in {"1+3", "2+2"} for _, grouping, _ in signature)

    legacy_contracts = spread_recipe_contract_skeleton(include_retired_four_note=True)
    legacy_signature = tuple((contract.recipe_id, contract.grouping.value, contract.density) for contract in legacy_contracts[:2])
    assert legacy_signature == (
        ("spread_1plus3_contract", "1+3", 4),
        ("spread_2plus2_contract", "2+2", 4),
    )


def test_v2_6_10_default_basic_spread_projection_outputs_only_active_5plus_contracts() -> None:
    for chord in ("Ebmaj7", "G7b9", "Bm7b5"):
        results = project_basic_spread_candidates(chord)
        assert results
        for result in results:
            assert result.recipe_contract.recipe_id not in {"spread_1plus3_contract", "spread_2plus2_contract"}
            assert result.recipe_contract.density >= 5
            assert result.recipe_contract.grouping.value not in {"1+3", "2+2"}


def test_v2_6_10_jazz_ballad_runtime_uses_grouped_5plus_spread_not_legacy_four_note(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 1,
            "seed": 26910,
            "output_path": str(tmp_path / "misty_v2_6_10.mid"),
        }
    )
    assert result.ok is True
    voicings = _voicing_events(result.debug)
    assert len(voicings) >= 40

    densities = Counter(int(voicing.get("density", 0)) for voicing in voicings)
    groupings = Counter(str(voicing.get("functional_grouping")) for voicing in voicings)
    recipe_ids = Counter(str(voicing.get("recipe_id")) for voicing in voicings)
    dispositions = Counter(str(voicing.get("disposition")) for voicing in voicings)

    assert set(dispositions) == {"spread"}
    assert all(density >= 5 for density in densities)
    assert "1+3" not in groupings
    assert "2+2" not in groupings
    assert "spread_1plus3_contract" not in recipe_ids
    assert "spread_2plus2_contract" not in recipe_ids

    # The reset is systemic: ordinary Ballad comping should now be centered on
    # the 5-note 2+3 grouped SPREAD lane, while 6/7-note lanes remain available
    # for lift and ending contexts.
    assert densities[5] > densities[6]
    assert groupings["2+3"] > groupings["2+4"]
    assert recipe_ids["spread_2plus3_contract"] > 0
