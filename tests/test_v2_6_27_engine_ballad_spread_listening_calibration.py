from __future__ import annotations

# harness token: test_v2_6_27_engine_ballad_spread_listening_calibration

from collections import Counter
from pathlib import Path
import json

from jammate_engine.core.voicing.disposition.spread import resolve_ballad_spread_grouping_mix_policy
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SPREAD_LISTENING_CALIBRATION_V2_6_27.md"
MISTY = ROOT / "examples" / "leadsheets" / "misty.json"


def _voicing_events(debug: dict) -> list[dict]:
    return [event.get("voicing") or {} for event in debug.get("piano_musical_audit_events", [])]


def _notes(voicing: dict) -> list[int]:
    raw = voicing.get("midi_notes")
    if isinstance(raw, list) and raw:
        return [int(note) for note in raw]
    return [int(note["midi_note"]) for note in voicing.get("notes", []) if isinstance(note, dict) and "midi_note" in note]


def test_v2_6_27_doc_exists_and_states_listening_calibration_scope() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "v2_6_27",
        "Ballad SPREAD Listening Calibration",
        "voicing-only",
        "1+4",
        "upper4 color lane",
        "2+3",
        "2+4",
        "3+3",
        "Pattern",
        "Anticipation",
        "Expression",
        "MIDI",
    ]
    for token in required:
        assert token in text


def test_v2_6_27_policy_demotes_1plus4_from_ordinary_runtime_body() -> None:
    policy = get_voicing_policy()
    metadata = dict(policy.metadata or {})
    calibration = dict(metadata.get("ballad_spread_listening_calibration") or {})
    assert calibration["version"] == "v2_6_27"
    assert calibration["ordinary_runtime_groupings"] == ["2+3", "2+4", "3+3"]
    assert "upper4 color lane" in calibration["one_plus_four_role"]

    runtime_ids = tuple(metadata.get("spread_density_runtime_contract_ids") or ())
    assert runtime_ids == (
        "spread_2plus3_contract",
        "spread_2plus4_contract",
        "spread_3plus3_contract",
    )

    weights_by_scene = metadata["ballad_spread_grouping_mix_policy"]["weights_by_scene"]
    for scene in ("normal_comping", "chorus_lift", "ending_climax"):
        assert int(weights_by_scene[scene]["spread_1plus4_contract"]) == 0
    assert float(metadata["spread_grouping_mix_selected_6note_contract_bias"]) == 3.0


def test_v2_6_27_zero_weight_compatible_contracts_are_filtered_from_texture_state() -> None:
    policy = get_voicing_policy()
    found_normal_5_lane = False
    for bar in range(32):
        decision = resolve_ballad_spread_grouping_mix_policy(
            policy,
            event_context={
                "region_id": f"c0_b{bar}_ch0",
                "region_chorus_index": 0,
                "region_total_choruses": 3,
                "region_bar_index": bar,
                "region_chord_index": 0,
                "region_phrase": "A",
            },
            explicit_enable=True,
        )
        if decision.texture_family == "rooted_5note_phrase":
            found_normal_5_lane = True
            assert "spread_1plus4_contract" not in decision.compatible_contract_ids
            assert decision.compatible_contract_ids == ("spread_2plus3_contract",)
            assert decision.selected_contract_id == "spread_2plus3_contract"
            assert decision.weights.get("spread_1plus4_contract", 0) == 0
            break
    assert found_normal_5_lane is True


def test_v2_6_27_misty_ballad_runtime_removes_default_1plus4_but_keeps_6_to_4_balance(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_27.mid"),
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
    assert densities[7] <= 2
    assert groupings["1+4"] == 0
    assert recipes["spread_1plus4_contract"] == 0
    assert "1+3" not in groupings
    assert "2+2" not in groupings

    five = densities[5]
    six = densities[6]
    assert five > 0 and six > 0
    ratio = five / float(five + six)
    assert 0.58 <= ratio <= 0.62
    assert groupings["2+3"] == five
    assert groupings["2+4"] + groupings["3+3"] == six

    note_sets = [_notes(voicing) for voicing in voicings]
    assert max(max(notes) for notes in note_sets if notes) <= 77
    assert min(min(notes) for notes in note_sets if notes) >= 40

    maj7_sharp11 = [
        voicing
        for voicing in voicings
        if "maj7" in str(voicing.get("chord_symbol"))
        and any(str(degree) == "#11" for degree in voicing.get("degrees", []))
    ]
    assert maj7_sharp11 == []
