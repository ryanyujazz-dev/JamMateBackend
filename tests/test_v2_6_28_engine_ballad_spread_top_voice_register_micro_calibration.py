from __future__ import annotations

# harness token: test_v2_6_28_engine_ballad_spread_top_voice_register_micro_calibration

from collections import Counter
from pathlib import Path
import json

from jammate_engine.core.voicing.selection.selector import SPREAD_TOP_REGISTER_MICRO_CALIBRATION_VERSION
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SPREAD_TOP_VOICE_REGISTER_MICRO_CALIBRATION_V2_6_28.md"
MISTY = ROOT / "examples" / "leadsheets" / "misty.json"


def _voicing_events(debug: dict) -> list[dict]:
    return [event.get("voicing") or {} for event in debug.get("piano_musical_audit_events", [])]


def _notes(voicing: dict) -> list[int]:
    raw = voicing.get("midi_notes")
    if isinstance(raw, list) and raw:
        return [int(note) for note in raw]
    return [int(note["midi_note"]) for note in voicing.get("notes", []) if isinstance(note, dict) and "midi_note" in note]


def test_v2_6_28_doc_exists_and_states_micro_calibration_scope() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "v2_6_28",
        "Ballad SPREAD Top Voice / Register Micro Calibration",
        "voicing-only",
        "top voice",
        "register",
        "does not change density lane",
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


def test_v2_6_28_policy_enables_narrow_spread_top_register_micro_bias() -> None:
    policy = get_voicing_policy()
    metadata = dict(policy.metadata or {})
    calibration = dict(metadata.get("ballad_spread_top_voice_register_micro_calibration") or {})

    assert SPREAD_TOP_REGISTER_MICRO_CALIBRATION_VERSION == "v2_6_28"
    assert calibration["version"] == "v2_6_28"
    assert calibration["density_lane_unchanged"] is True
    assert calibration["one_plus_four_restored_low_frequency"] is True
    assert metadata["spread_top_register_micro_calibration_enabled"] is True
    assert metadata["spread_top_register_micro_calibration_version"] == "v2_6_28"
    assert int(metadata["spread_top_register_micro_soft_high"]) == 74
    assert int(metadata["spread_top_register_micro_hard_high"]) == 76

    runtime_ids = tuple(metadata.get("spread_density_runtime_contract_ids") or ())
    assert runtime_ids == (
        "spread_1plus4_contract",
        "spread_2plus3_contract",
        "spread_2plus4_contract",
        "spread_3plus3_contract",
    )


def test_v2_6_28_misty_ballad_runtime_keeps_density_but_softens_top_ceiling(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_28.mid"),
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
    assert densities[7] == 0
    assert 4 <= groupings["1+4"] <= 10
    assert recipes["spread_1plus4_contract"] == groupings["1+4"]
    assert "1+3" not in groupings
    assert "2+2" not in groupings

    five = densities[5]
    six = densities[6]
    assert five > 0 and six > 0
    ratio = five / float(five + six)
    assert 0.62 <= ratio <= 0.64
    assert groupings["2+3"] + groupings["1+4"] == five
    assert groupings["2+4"] + groupings["3+3"] == six

    note_sets = [_notes(voicing) for voicing in voicings]
    assert max(max(notes) for notes in note_sets if notes) <= 74
    assert sum(1 for notes in note_sets if notes and max(notes) >= 75) == 0
    assert min(min(notes) for notes in note_sets if notes) >= 40
    assert max(sum(notes) / len(notes) for notes in note_sets if notes) <= 62.0

    micro_profiles = [
        (voicing.get("metadata") or {}).get("spread_top_register_micro_calibration_profile")
        for voicing in voicings
    ]
    assert any(isinstance(profile, dict) and profile.get("version") == "v2_6_28" for profile in micro_profiles)
    first_profile = voicings[0].get("metadata", {}).get("spread_top_register_micro_calibration_profile")
    assert first_profile["version"] == "v2_6_28"
    assert first_profile["enabled"] is True
    assert first_profile["top_note"] <= 74
    assert first_profile["does_not_change_density_lane"] is True

    maj7_sharp11 = [
        voicing
        for voicing in voicings
        if "maj7" in str(voicing.get("chord_symbol"))
        and any(str(degree) == "#11" for degree in voicing.get("degrees", []))
    ]
    assert maj7_sharp11 == []
