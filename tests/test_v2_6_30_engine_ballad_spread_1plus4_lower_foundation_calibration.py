from __future__ import annotations

# harness token: test_v2_6_30_engine_ballad_spread_1plus4_lower_foundation_calibration

from collections import Counter
from dataclasses import replace
from pathlib import Path
import json

from jammate_engine.core.voicing.disposition.spread import resolve_ballad_spread_grouping_mix_policy
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SPREAD_1PLUS4_LOWER_FOUNDATION_CALIBRATION_V2_6_30.md"
MISTY = ROOT / "examples" / "leadsheets" / "misty.json"


def _generate_misty(tmp_path: Path):
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_30.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return result


def test_v2_6_30_doc_exists_and_states_voicing_only_scope() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "v2_6_30",
        "1+4",
        "low-frequency",
        "lower foundation",
        "5-note",
        "6-note",
        "6:4",
        "4-note",
        "maj7#11",
        "voicing-only",
        "Pattern",
        "Anticipation",
        "Expression",
        "MIDI",
    ]
    for token in required:
        assert token in text


def test_v2_6_30_policy_restores_1plus4_as_low_frequency_lane() -> None:
    policy = get_voicing_policy()
    metadata = dict(policy.metadata or {})

    assert metadata["milestone"] == "v2_6_30_ballad_spread_1plus4_lower_foundation_calibration"
    calibration = dict(metadata.get("ballad_spread_1plus4_lower_foundation_calibration") or {})
    assert calibration["version"] == "v2_6_30"
    assert calibration["scope"] == "voicing_only"
    assert calibration["one_plus_four_target_events_per_196"] == "4_to_10"
    assert calibration["lower_foundation_span_limit_semitones"] == 12

    runtime_ids = tuple(metadata.get("spread_density_runtime_contract_ids") or ())
    assert runtime_ids == (
        "spread_1plus4_contract",
        "spread_2plus3_contract",
        "spread_2plus4_contract",
        "spread_3plus3_contract",
    )

    weights_by_scene = metadata["ballad_spread_grouping_mix_policy"]["weights_by_scene"]
    assert int(weights_by_scene["normal_comping"]["spread_1plus4_contract"]) == 4
    assert int(weights_by_scene["chorus_lift"]["spread_1plus4_contract"]) == 3
    assert int(weights_by_scene["ending_climax"]["spread_1plus4_contract"]) == 0
    assert int(weights_by_scene["normal_comping"]["spread_2plus3_contract"]) > int(weights_by_scene["normal_comping"]["spread_1plus4_contract"])


def test_v2_6_30_zero_weight_1plus4_does_not_leak_as_compatible_neighbor() -> None:
    policy = get_voicing_policy()
    metadata = dict(policy.metadata or {})
    mix = dict(metadata.get("ballad_spread_grouping_mix_policy") or {})
    weights_by_scene = {
        scene: {**dict(weights), "spread_1plus4_contract": 0}
        for scene, weights in dict(mix.get("weights_by_scene") or {}).items()
    }
    policy = replace(
        policy,
        metadata={
            **metadata,
            "ballad_spread_grouping_mix_policy": {**mix, "weights_by_scene": weights_by_scene},
        },
    )

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


def test_v2_6_30_misty_runtime_restores_1plus4_without_breaking_density_guardrails(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug).summary

    assert audit["densities"] == {"5": 120, "6": 76}
    assert audit["functional_groupings"] == {"2+3": 110, "2+4": 72, "1+4": 10, "3+3": 4}
    assert audit["densities"].get("4", 0) == 0
    assert audit["densities"].get("7", 0) == 0
    assert 4 <= audit["functional_groupings"]["1+4"] <= 10

    five = audit["densities"]["5"]
    six = audit["densities"]["6"]
    assert 0.60 <= five / float(five + six) <= 0.62
    assert audit["functional_groupings"]["2+3"] + audit["functional_groupings"]["1+4"] == five
    assert audit["functional_groupings"]["2+4"] + audit["functional_groupings"]["3+3"] == six

    voicings = [event.get("voicing") or {} for event in result.debug.get("piano_musical_audit_events", [])]
    note_sets = [[int(note) for note in voicing.get("midi_notes", [])] for voicing in voicings]
    assert len(voicings) >= 180
    assert max(max(notes) for notes in note_sets if notes) <= 74
    assert sum(1 for notes in note_sets if notes and max(notes) >= 75) == 0
    assert min(min(notes) for notes in note_sets if notes) >= 40
    assert [
        voicing
        for voicing in voicings
        if "maj7" in str(voicing.get("chord_symbol"))
        and any(str(degree) == "#11" for degree in voicing.get("degrees", []))
    ] == []


def test_v2_6_30_drop_projection_audit_covers_restored_1plus4_upper_drop(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug).summary

    assert audit["drop_projection_audit_version"] == "v2_6_29"
    assert audit["spread_upper_projection_methods"] == {
        "closed_upper_stack": 114,
        "drop3": 72,
        "drop2": 10,
    }
    assert audit["spread_upper_drop_projection_methods"] == {"drop3": 72, "drop2": 10}
    assert audit["spread_upper_drop_projection_events"] == 82
    assert audit["drop_projection_methods_total"] == {"drop3": 72, "drop2": 10}
    assert audit["drop_projection_methods_by_scope"] == {"spread_upper_group": {"drop3": 72, "drop2": 10}}
    assert audit["spread_upper_drop_projection_methods_by_density"] == {"6": {"drop3": 62, "drop2": 10}, "5": {"drop3": 10}}
    assert audit["spread_upper_drop_projection_events_by_density"] == {"6": 72, "5": 10}
    assert audit["spread_upper_drop_projection_methods_by_grouping"] == {
        "2+4": {"drop3": 62, "drop2": 10},
        "1+4": {"drop3": 10},
    }
    assert audit["spread_upper_drop_projection_methods_by_recipe"] == {
        "spread_2plus4_contract": {"drop3": 62, "drop2": 10},
        "spread_1plus4_contract": {"drop3": 10},
    }


def test_v2_6_30_lower_foundation_audit_and_span_guardrails(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug).summary

    assert audit["lower_foundation_audit_version"] == "v2_6_30"
    assert audit["lower_foundation_note_min"] == 41
    assert audit["lower_foundation_note_max"] == 58
    assert 49.0 <= audit["lower_foundation_note_average"] <= 51.0
    assert audit["lower_foundation_span_max"] <= 12
    assert audit["lower_foundation_span_violation_events"] == 0
    assert 5.0 <= audit["lower_foundation_span_average"] <= 7.0

    notes_by_grouping = audit["lower_foundation_notes_by_grouping"]
    spans_by_grouping = audit["lower_foundation_spans_by_grouping"]
    assert set(notes_by_grouping) == {"2+3", "2+4", "1+4", "3+3"}
    assert notes_by_grouping["2+4"]["min"] == 41
    assert notes_by_grouping["1+4"]["count"] == 10
    assert spans_by_grouping["3+3"]["max"] <= 12

    assert audit["lower_foundation_recipe_counts"] == {
        "lower_2note_root_3": 109,
        "lower_2note_root_7": 73,
        "lower_1note_root": 10,
        "lower_3note_root_3_7": 4,
    }
    assert audit["lower_foundation_low_register_events"] <= 30
    assert audit["lower_foundation_low_register_events_by_grouping"] == {"2+4": 26, "2+3": 2}

    assert audit["lower_foundation_spans_by_density"]["6"]["max"] <= 12
    assert audit["lower_foundation_recipe_counts"]["lower_1note_root"] == audit["functional_groupings"]["1+4"]
