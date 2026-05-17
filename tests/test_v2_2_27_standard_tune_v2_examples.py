from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.form import expand_form_to_regions
from jammate_engine.core.leadsheet import LEADSHEET_SCHEMA_VERSION, parse_leadsheet
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = Path(__file__).resolve().parents[1]
LEADSHEET_DIR = ROOT / "examples" / "leadsheets"

STANDARD_TUNE_CASES = {
    "autumn_leaves.json": {"title": "Autumn Leaves", "style": "medium_swing", "written_bars": 32, "regions": 54},
    "blue_bossa.json": {"title": "Blue Bossa", "style": "bossa_nova", "written_bars": 16, "regions": 17},
    "misty.json": {"title": "Misty", "style": "jazz_ballad", "written_bars": 32, "regions": 50},
}


def _load(name: str) -> dict:
    return json.loads((LEADSHEET_DIR / name).read_text(encoding="utf-8"))


def test_v2_2_28_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"


def test_standard_tune_examples_are_native_v2_written_form_documents() -> None:
    for filename, expected in STANDARD_TUNE_CASES.items():
        raw = _load(filename)
        leadsheet = parse_leadsheet(raw)

        assert raw["schema_version"] == LEADSHEET_SCHEMA_VERSION
        assert raw["metadata"]["fixture_role"] == "standard_tune_v2_leadsheet_example"
        assert raw["metadata"]["performance_repetitions_live_in_request"] is True
        assert leadsheet.title == expected["title"]
        assert len(leadsheet.bars) == expected["written_bars"]
        assert leadsheet.metadata["source_shape"] == "v2_sections_written_form"
        assert "form" not in raw
        assert "blocks" not in raw
        assert "bars" not in raw


def test_standard_tune_examples_compile_to_chord_region_first_timelines() -> None:
    for filename, expected in STANDARD_TUNE_CASES.items():
        leadsheet = parse_leadsheet(_load(filename))
        timeline = expand_form_to_regions(leadsheet, choruses=3)

        assert timeline.written_bars == expected["written_bars"]
        assert timeline.performance_bars == expected["written_bars"] * 3
        assert timeline.choruses == 3
        assert len(timeline.regions) == expected["regions"] * 3
        assert timeline.regions[0].metadata["schema_version"] == LEADSHEET_SCHEMA_VERSION
        assert timeline.regions[0].section_id is not None
        assert timeline.regions[0].performance_bar_index == 0
        assert timeline.regions[expected["regions"]].chorus_index == 1


def test_standard_tune_examples_generate_three_chorus_demos(tmp_path: Path) -> None:
    for index, (filename, expected) in enumerate(STANDARD_TUNE_CASES.items()):
        raw = _load(filename)
        result = generate_accompaniment(
            {
                "leadsheet": raw,
                "style": expected["style"],
                "tempo": int(raw.get("tempo", 120)),
                "choruses": 3,
                "seed": 22700 + index,
                "output_path": str(tmp_path / f"{Path(filename).stem}_{expected['style']}.mid"),
                "ensemble": {"bass_present": True},
            }
        )

        assert Path(result.midi_path).exists()
        assert result.debug["leadsheet_schema_version"] == LEADSHEET_SCHEMA_VERSION
        assert result.debug["written_bars"] == expected["written_bars"]
        assert result.debug["performance_choruses"] == 3
        assert result.debug["performance_bars"] == expected["written_bars"] * 3


def test_v2_examples_do_not_reenable_v1_blocks_form_compatibility() -> None:
    legacy_shape = {
        "title": "Legacy Blocks Shape",
        "blocks": {"A": {"bars": [{"chords": [{"beat": 1.0, "symbol": "Cmaj7"}]}]}},
        "form": ["A"],
    }

    from jammate_engine.core.leadsheet import collect_leadsheet_validation_issues

    issues = collect_leadsheet_validation_issues(legacy_shape)
    assert any(issue.code == "missing_score_body" for issue in issues)
