from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.form import expand_form_to_regions, expand_leadsheet_to_written_bars
from jammate_engine.core.leadsheet import LEADSHEET_SCHEMA_VERSION, normalize_leadsheet, parse_leadsheet
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = Path(__file__).resolve().parents[1]
SCORE_PATH = ROOT / "examples" / "leadsheets" / "all_the_things_you_are.json"


def test_v2_2_28_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"


def test_v2_leadsheet_uses_written_form_not_embedded_demo_repeats() -> None:
    score = json.loads(SCORE_PATH.read_text(encoding="utf-8"))
    leadsheet = normalize_leadsheet(parse_leadsheet(score))

    assert leadsheet.schema_version == LEADSHEET_SCHEMA_VERSION
    assert leadsheet.metadata["performance_repetitions_live_in_request"] is True
    assert len(leadsheet.sections) == 4
    assert [item.section_id for item in leadsheet.written_form] == ["A1", "A2", "B", "A3"]
    assert len(leadsheet.bars) == 36

    written_bars = expand_leadsheet_to_written_bars(leadsheet)
    assert len(written_bars) == 36
    assert written_bars[0].section_id == "A1"
    assert written_bars[16].section_id == "B"
    assert written_bars[16].role == "bridge"


def test_v2_form_compiler_outputs_chord_region_first_timeline_with_source_metadata() -> None:
    leadsheet = normalize_leadsheet(parse_leadsheet(json.loads(SCORE_PATH.read_text(encoding="utf-8"))))
    timeline = expand_form_to_regions(leadsheet, choruses=3)

    assert timeline.written_bars == 36
    assert timeline.performance_bars == 108
    assert timeline.total_beats == 432.0
    assert timeline.choruses == 3
    assert len(timeline.regions) == 120

    first = timeline.regions[0]
    assert first.region_id == "c0_b0_ch0"
    assert first.chord_symbol == "Fm7"
    assert first.section_id == "A1"
    assert first.phrase == "A"
    assert first.bar_local_start_beat == 1.0
    assert first.is_first_bar_of_chorus is True
    assert first.is_first_bar_of_section is True

    second_chord_in_split_bar = timeline.regions[6]
    assert second_chord_in_split_bar.chord_symbol == "G7"
    assert second_chord_in_split_bar.bar_index == 5
    assert second_chord_in_split_bar.chord_index == 1
    assert second_chord_in_split_bar.duration_beats == 2.0
    assert second_chord_in_split_bar.bar_local_start_beat == 3.0
    assert second_chord_in_split_bar.bar_local_end_beat == 5.0

    bridge = next(region for region in timeline.regions if region.section_id == "B")
    assert bridge.section_role == "bridge"
    assert bridge.phrase == "B"

    second_chorus_first = next(region for region in timeline.regions if region.region_id == "c1_b0_ch0")
    assert second_chorus_first.start_beat == 144.0
    assert second_chorus_first.performance_bar_index == 36
    assert second_chorus_first.total_choruses == 3


def test_runtime_debug_exposes_written_form_and_performance_chorus_boundary(tmp_path: Path) -> None:
    score = json.loads(SCORE_PATH.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": int(score.get("tempo", 132)),
            "choruses": 3,
            "seed": 424,
            "output_path": str(tmp_path / "v2_leadsheet_contract.mid"),
        }
    )
    assert Path(result.midi_path).exists()
    assert result.debug["leadsheet_schema_version"] == LEADSHEET_SCHEMA_VERSION
    assert result.debug["written_bars"] == 36
    assert result.debug["performance_choruses"] == 3
    assert result.debug["performance_bars"] == 108
    assert result.debug["regions"] == 120
