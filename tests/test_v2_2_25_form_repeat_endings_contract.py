from __future__ import annotations

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.form import expand_form_to_regions
from jammate_engine.core.leadsheet import parse_leadsheet


def _repeat_ending_score() -> dict:
    return {
        "schema_version": "jammate_leadsheet_v2",
        "title": "V2 Repeat Ending Contract Fixture",
        "key": "C",
        "sections": {
            "A": {"label": "A", "phrase": "A", "bars": [{"chords": [{"beat": 1.0, "symbol": "Cmaj7"}]}]},
            "E1": {"label": "E1", "phrase": "A", "role": "first_ending", "bars": [{"chords": [{"beat": 1.0, "symbol": "G7"}]}]},
            "E2": {"label": "E2", "phrase": "A", "role": "second_ending", "bars": [{"chords": [{"beat": 1.0, "symbol": "C6"}]}]},
            "TAG": {"label": "TAG", "phrase": "tag", "role": "tag", "bars": [{"chords": [{"beat": 1.0, "symbol": "Fmaj7"}]}]},
            "END": {"label": "END", "phrase": "ending", "role": "ending", "bars": [{"chords": [{"beat": 1.0, "symbol": "Cmaj7"}]}]},
        },
        "written_form": [
            {
                "type": "repeat",
                "id": "head_repeat",
                "times": 2,
                "body": ["A"],
                "endings": [
                    {"number": 1, "body": ["E1"]},
                    {"number": 2, "body": ["E2"]},
                ],
            },
            {"type": "tag", "body": ["TAG"]},
            {"type": "final_ending", "body": ["END"]},
        ],
    }


def test_v2_2_28_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"


def test_repeat_with_first_second_endings_compiles_to_flat_written_form() -> None:
    leadsheet = parse_leadsheet(_repeat_ending_score())

    assert [item.section_id for item in leadsheet.written_form] == ["A", "E1", "A", "E2", "TAG", "END"]
    assert len(leadsheet.bars) == 6
    assert [bar.section_id for bar in leadsheet.bars] == ["A", "E1", "A", "E2", "TAG", "END"]

    first_ending = leadsheet.bars[1]
    second_ending = leadsheet.bars[3]
    tag = leadsheet.bars[4]
    final = leadsheet.bars[5]

    assert first_ending.metadata["repeat_group"] == "head_repeat"
    assert first_ending.metadata["repeat_pass"] == 1
    assert first_ending.metadata["ending_number"] == 1
    assert first_ending.metadata["form_role"] == "ending"

    assert second_ending.metadata["repeat_pass"] == 2
    assert second_ending.metadata["ending_number"] == 2
    assert second_ending.metadata["form_role"] == "ending"

    assert tag.metadata["form_role"] == "tag"
    assert final.metadata["form_role"] == "final_ending"


def test_repeat_ending_metadata_reaches_chord_region_timeline() -> None:
    timeline = expand_form_to_regions(parse_leadsheet(_repeat_ending_score()), choruses=2)

    assert timeline.written_bars == 6
    assert timeline.performance_bars == 12
    assert timeline.choruses == 2
    assert [region.chord_symbol for region in timeline.regions[:6]] == ["Cmaj7", "G7", "Cmaj7", "C6", "Fmaj7", "Cmaj7"]

    first_ending_region = timeline.regions[1]
    second_ending_region = timeline.regions[3]
    final_region = timeline.regions[5]
    second_chorus_first = timeline.regions[6]

    assert first_ending_region.metadata["ending_number"] == 1
    assert first_ending_region.metadata["repeat_pass"] == 1
    assert second_ending_region.metadata["ending_number"] == 2
    assert second_ending_region.metadata["repeat_pass"] == 2
    assert final_region.metadata["form_role"] == "final_ending"
    assert second_chorus_first.start_beat == 24.0
    assert second_chorus_first.performance_bar_index == 6
