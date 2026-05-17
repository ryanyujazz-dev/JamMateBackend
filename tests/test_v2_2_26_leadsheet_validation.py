from __future__ import annotations

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.leadsheet import (
    LeadsheetValidationError,
    collect_leadsheet_validation_issues,
    parse_leadsheet,
    validate_leadsheet_document,
)


def test_v2_2_28_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"


def test_valid_flat_and_section_forms_still_parse() -> None:
    flat = {"title": "Flat", "bars": ["Dm7", "G7", "Cmaj7"]}
    sectioned = {
        "schema_version": "jammate_leadsheet_v2",
        "title": "Sectioned",
        "sections": {
            "A": {"bars": [{"chords": [{"beat": 1.0, "symbol": "Cmaj7"}]}]},
            "B": {"bars": [{"chords": [{"beat": 1.0, "symbol": "G7"}]}]},
        },
        "written_form": [{"section": "A"}, {"section": "B"}],
    }

    assert [bar.chords[0].symbol for bar in parse_leadsheet(flat).bars] == ["Dm7", "G7", "Cmaj7"]
    assert [bar.section_id for bar in parse_leadsheet(sectioned).bars] == ["A", "B"]


def test_unknown_section_reports_path_and_code() -> None:
    score = {
        "title": "Broken Unknown Section",
        "sections": {"A": {"bars": ["Cmaj7"]}},
        "written_form": [{"section": "A"}, {"section": "B"}],
    }

    try:
        parse_leadsheet(score)
    except LeadsheetValidationError as exc:
        assert exc.issues[0].code == "unknown_section"
        assert "$.written_form[1].section" in str(exc)
        assert "'B'" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("invalid unknown section should not parse")


def test_validation_rejects_empty_section_and_empty_bars_before_timeline_compile() -> None:
    score = {
        "title": "Broken Empty Section",
        "sections": {
            "A": {"bars": []},
            "B": {"bars": [{"chords": []}]},
        },
        "written_form": ["A", "B"],
    }

    issues = collect_leadsheet_validation_issues(score)
    assert {issue.code for issue in issues} >= {"empty_section", "empty_bar_chords"}


def test_validation_rejects_beat_out_of_range_unsorted_and_duplicate_onsets() -> None:
    score = {
        "title": "Broken Beats",
        "bars": [
            {"chords": [{"beat": 3.0, "symbol": "G7"}, {"beat": 1.0, "symbol": "Dm7"}]},
            {"chords": [{"beat": 1.0, "symbol": "Cmaj7"}, {"beat": 1.0, "symbol": "Fmaj7"}]},
            {"chords": [{"beat": 5.0, "symbol": "Cmaj7"}]},
        ],
    }

    issues = collect_leadsheet_validation_issues(score)
    codes = [issue.code for issue in issues]
    assert "beat_order" in codes
    assert "duplicate_chord_beat" in codes
    assert "beat_out_of_range" in codes


def test_validation_rejects_duplicate_and_out_of_range_ending_passes() -> None:
    score = {
        "title": "Broken Repeat Endings",
        "sections": {
            "A": {"bars": ["Cmaj7"]},
            "E1": {"bars": ["G7"]},
            "E2": {"bars": ["C6"]},
        },
        "written_form": [
            {
                "type": "repeat",
                "times": 2,
                "body": ["A"],
                "endings": [
                    {"passes": [1], "body": ["E1"]},
                    {"passes": [1, 3], "body": ["E2"]},
                ],
            }
        ],
    }

    issues = collect_leadsheet_validation_issues(score)
    assert "duplicate_ending_pass" in {issue.code for issue in issues}
    assert "ending_pass_out_of_range" in {issue.code for issue in issues}


def test_validate_leadsheet_document_raises_single_actionable_error() -> None:
    try:
        validate_leadsheet_document({})
    except LeadsheetValidationError as exc:
        assert exc.issues[0].code == "missing_score_body"
        assert "silent fallback chords are forbidden" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("empty document should not validate")
