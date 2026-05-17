from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LeadsheetValidationIssue:
    """One user-facing leadsheet validation problem.

    Validation belongs at the leadsheet/form boundary so V2 generation can stay
    chord-region-first and never silently consumes malformed score notation.
    """

    path: str
    code: str
    message: str

    def format(self) -> str:
        return f"{self.path}: {self.code}: {self.message}"


class LeadsheetValidationError(ValueError):
    """Raised when a leadsheet document cannot safely compile to chord regions."""

    def __init__(self, issues: list[LeadsheetValidationIssue]):
        self.issues = list(issues)
        preview = "; ".join(issue.format() for issue in self.issues[:5])
        if len(self.issues) > 5:
            preview += f"; ... +{len(self.issues) - 5} more"
        super().__init__(f"Invalid V2 leadsheet document ({len(self.issues)} issue(s)): {preview}")


def validate_leadsheet_document(data: dict[str, Any]) -> None:
    """Raise a detailed error if the source document is not safe to compile."""

    issues = collect_leadsheet_validation_issues(data)
    if issues:
        raise LeadsheetValidationError(issues)


def collect_leadsheet_validation_issues(data: Any) -> list[LeadsheetValidationIssue]:
    issues: list[LeadsheetValidationIssue] = []
    if not isinstance(data, dict):
        return [_issue("$", "document_type", "leadsheet document must be a dict/object")]

    default_ts = _read_time_signature(data.get("default_time_signature"), "$.default_time_signature", issues, fallback=(4, 4))
    section_ids = _collect_section_ids(data, issues)

    has_sections = bool(section_ids)
    has_bars = "bars" in data
    if not has_sections and not has_bars:
        issues.append(_issue("$", "missing_score_body", "provide sections/written_form or flat bars; silent fallback chords are forbidden"))

    if "sections" in data:
        _validate_sections(data, default_ts, issues)
        _validate_written_form(data, section_ids, issues)
    elif has_bars:
        _validate_bar_list(data.get("bars"), "$.bars", default_ts, issues)

    return issues


def _collect_section_ids(data: dict[str, Any], issues: list[LeadsheetValidationIssue]) -> set[str]:
    raw_sections = data.get("sections")
    if raw_sections is None:
        return set()
    section_ids: set[str] = set()
    if isinstance(raw_sections, dict):
        for key in raw_sections:
            section_id = str(key)
            if not section_id.strip():
                issues.append(_issue("$.sections", "blank_section_id", "section id cannot be blank"))
            elif section_id in section_ids:
                issues.append(_issue(f"$.sections.{section_id}", "duplicate_section_id", f"duplicate section id {section_id!r}"))
            section_ids.add(section_id)
    elif isinstance(raw_sections, list):
        for index, value in enumerate(raw_sections):
            path = f"$.sections[{index}]"
            if not isinstance(value, dict):
                issues.append(_issue(path, "section_type", "section entries must be objects"))
                continue
            section_id = str(value.get("id", value.get("label", f"S{index + 1}")))
            if not section_id.strip():
                issues.append(_issue(path, "blank_section_id", "section id cannot be blank"))
            elif section_id in section_ids:
                issues.append(_issue(path, "duplicate_section_id", f"duplicate section id {section_id!r}"))
            section_ids.add(section_id)
    else:
        issues.append(_issue("$.sections", "sections_type", "sections must be a dict or list"))
    return section_ids


def _validate_sections(data: dict[str, Any], default_ts: tuple[int, int], issues: list[LeadsheetValidationIssue]) -> None:
    raw_sections = data.get("sections")
    if isinstance(raw_sections, dict):
        iterable = [(str(key), value, f"$.sections.{key}") for key, value in raw_sections.items()]
    elif isinstance(raw_sections, list):
        iterable = []
        for index, value in enumerate(raw_sections):
            section_id = str(value.get("id", value.get("label", f"S{index + 1}"))) if isinstance(value, dict) else f"S{index + 1}"
            iterable.append((section_id, value, f"$.sections[{index}]"))
    else:
        return

    if not iterable:
        issues.append(_issue("$.sections", "empty_sections", "sections cannot be empty"))
    for section_id, raw_section, path in iterable:
        if not isinstance(raw_section, dict):
            issues.append(_issue(path, "section_type", "section must be an object"))
            continue
        raw_bars = raw_section.get("bars")
        if not isinstance(raw_bars, list) or not raw_bars:
            issues.append(_issue(f"{path}.bars", "empty_section", f"section {section_id!r} must contain at least one bar"))
            continue
        _validate_bar_list(raw_bars, f"{path}.bars", default_ts, issues)


def _validate_written_form(data: dict[str, Any], section_ids: set[str], issues: list[LeadsheetValidationIssue]) -> None:
    raw_form = data.get("written_form", data.get("form"))
    if raw_form is None:
        return
    if not isinstance(raw_form, list) or not raw_form:
        issues.append(_issue("$.written_form", "written_form_type", "written_form/form must be a non-empty list when provided"))
        return
    for index, item in enumerate(raw_form):
        _validate_form_item(item, f"$.written_form[{index}]", section_ids, issues, repeat_times=None)


def _validate_form_item(
    item: Any,
    path: str,
    section_ids: set[str],
    issues: list[LeadsheetValidationIssue],
    *,
    repeat_times: int | None,
) -> None:
    if isinstance(item, str):
        _validate_section_reference(item, path, section_ids, issues)
        return
    if not isinstance(item, dict):
        issues.append(_issue(path, "form_item_type", "form items must be section strings or objects"))
        return

    item_type = item.get("type")
    if item_type == "repeat" or ("body" in item and "section" not in item and item_type not in {"tag", "ending", "final_ending"}):
        times = _positive_int(item.get("times", item.get("repeat", 1)))
        if times is None:
            issues.append(_issue(f"{path}.times", "repeat_times", "repeat times must be a positive integer"))
            times = 1
        body = item.get("body")
        if not isinstance(body, list) or not body:
            issues.append(_issue(f"{path}.body", "repeat_body", "repeat body must be a non-empty list"))
        else:
            for index, child in enumerate(body):
                _validate_form_item(child, f"{path}.body[{index}]", section_ids, issues, repeat_times=times)
        _validate_repeat_endings(item.get("endings", []), f"{path}.endings", section_ids, issues, repeat_times=times)
        return

    if item_type in {"tag", "ending", "final_ending"}:
        if "section" in item:
            _validate_section_reference(str(item.get("section", "")), f"{path}.section", section_ids, issues)
        body = item.get("body")
        if body is not None:
            if not isinstance(body, list) or not body:
                issues.append(_issue(f"{path}.body", "role_body", f"{item_type} body must be a non-empty list when provided"))
            else:
                for index, child in enumerate(body):
                    _validate_form_item(child, f"{path}.body[{index}]", section_ids, issues, repeat_times=repeat_times)
        elif "section" not in item:
            issues.append(_issue(path, "role_body", f"{item_type} must provide section or body"))
        return

    if "section" in item:
        _validate_section_reference(str(item.get("section", "")), f"{path}.section", section_ids, issues)
        repeat = _positive_int(item.get("repeat", item.get("times", 1)))
        if repeat is None:
            issues.append(_issue(f"{path}.repeat", "section_repeat", "section repeat must be a positive integer"))
        return

    if item_type == "block" or "label" in item:
        _validate_section_reference(str(item.get("label", "")), f"{path}.label", section_ids, issues)
        return

    issues.append(_issue(path, "unknown_form_item", "form item must reference a section, repeat, tag, ending, or final_ending"))


def _validate_repeat_endings(
    endings: Any,
    path: str,
    section_ids: set[str],
    issues: list[LeadsheetValidationIssue],
    *,
    repeat_times: int,
) -> None:
    if endings in (None, []):
        return
    if not isinstance(endings, list):
        issues.append(_issue(path, "endings_type", "repeat endings must be a list"))
        return
    pass_to_path: dict[int, str] = {}
    for index, ending in enumerate(endings):
        ending_path = f"{path}[{index}]"
        if not isinstance(ending, dict):
            issues.append(_issue(ending_path, "ending_type", "ending must be an object"))
            continue
        passes = _ending_passes(ending)
        if not passes:
            issues.append(_issue(ending_path, "ending_passes", "ending must declare at least one positive pass"))
        for pass_no in passes:
            if pass_no < 1 or pass_no > repeat_times:
                issues.append(_issue(ending_path, "ending_pass_out_of_range", f"ending pass {pass_no} is outside repeat times 1..{repeat_times}"))
            if pass_no in pass_to_path:
                issues.append(_issue(ending_path, "duplicate_ending_pass", f"ending pass {pass_no} is already claimed by {pass_to_path[pass_no]}"))
            pass_to_path[pass_no] = ending_path
        body = ending.get("body")
        if body is None and "section" in ending:
            _validate_section_reference(str(ending.get("section", "")), f"{ending_path}.section", section_ids, issues)
        elif isinstance(body, list) and body:
            for child_index, child in enumerate(body):
                _validate_form_item(child, f"{ending_path}.body[{child_index}]", section_ids, issues, repeat_times=repeat_times)
        else:
            issues.append(_issue(ending_path, "ending_body", "ending must provide section or non-empty body"))


def _validate_section_reference(section_id: str, path: str, section_ids: set[str], issues: list[LeadsheetValidationIssue]) -> None:
    if not section_id.strip():
        issues.append(_issue(path, "blank_section_reference", "section reference cannot be blank"))
    elif section_id not in section_ids:
        issues.append(_issue(path, "unknown_section", f"section {section_id!r} is not defined"))


def _validate_bar_list(raw_bars: Any, path: str, default_ts: tuple[int, int], issues: list[LeadsheetValidationIssue]) -> None:
    if not isinstance(raw_bars, list) or not raw_bars:
        issues.append(_issue(path, "bar_list", "bars must be a non-empty list"))
        return
    for index, raw_bar in enumerate(raw_bars):
        _validate_bar(raw_bar, f"{path}[{index}]", default_ts, issues)


def _validate_bar(raw_bar: Any, path: str, default_ts: tuple[int, int], issues: list[LeadsheetValidationIssue]) -> None:
    if isinstance(raw_bar, str):
        if not raw_bar.strip():
            issues.append(_issue(path, "blank_chord_symbol", "flat string bar chord symbol cannot be blank"))
        return
    if not isinstance(raw_bar, dict):
        issues.append(_issue(path, "bar_type", "bar must be a chord-symbol string or object"))
        return

    time_signature = _read_time_signature(raw_bar.get("time_signature"), f"{path}.time_signature", issues, fallback=default_ts)
    total_beats = float(time_signature[0])
    raw_chords = raw_bar.get("chords")
    if not isinstance(raw_chords, list) or not raw_chords:
        issues.append(_issue(f"{path}.chords", "empty_bar_chords", "bar must contain at least one chord event"))
        return

    previous_beat: float | None = None
    seen_beats: set[float] = set()
    for chord_index, raw_chord in enumerate(raw_chords):
        chord_path = f"{path}.chords[{chord_index}]"
        if not isinstance(raw_chord, dict):
            issues.append(_issue(chord_path, "chord_event_type", "chord event must be an object"))
            continue
        symbol = str(raw_chord.get("symbol", ""))
        if not symbol.strip():
            issues.append(_issue(f"{chord_path}.symbol", "blank_chord_symbol", "chord symbol cannot be blank"))
        beat = _positive_float(raw_chord.get("beat", 1.0))
        if beat is None:
            issues.append(_issue(f"{chord_path}.beat", "beat_value", "beat must be a positive number"))
            continue
        if beat < 1.0 or beat > total_beats:
            issues.append(_issue(f"{chord_path}.beat", "beat_out_of_range", f"beat {beat:g} must be within 1..{total_beats:g}"))
        if previous_beat is not None and beat < previous_beat:
            issues.append(_issue(f"{chord_path}.beat", "beat_order", "chord beats must be written in ascending order; parser will not silently reorder"))
        if beat in seen_beats:
            issues.append(_issue(f"{chord_path}.beat", "duplicate_chord_beat", f"multiple chord events on beat {beat:g} are ambiguous"))
        seen_beats.add(beat)
        previous_beat = beat
        if "beats" in raw_chord:
            explicit_beats = _positive_float(raw_chord.get("beats"))
            if explicit_beats is None:
                issues.append(_issue(f"{chord_path}.beats", "duration_value", "explicit beats must be a positive number"))
            elif beat + explicit_beats > total_beats + 1.0:
                issues.append(_issue(f"{chord_path}.beats", "duration_out_of_range", "explicit chord duration overruns the bar boundary"))


def _read_time_signature(raw: Any, path: str, issues: list[LeadsheetValidationIssue], *, fallback: tuple[int, int]) -> tuple[int, int]:
    if raw is None:
        return fallback
    if not isinstance(raw, dict):
        issues.append(_issue(path, "time_signature_type", "time signature must be an object with numerator/denominator"))
        return fallback
    numerator = _positive_int(raw.get("numerator", fallback[0]))
    denominator = _positive_int(raw.get("denominator", fallback[1]))
    if numerator is None:
        issues.append(_issue(f"{path}.numerator", "time_signature_numerator", "numerator must be a positive integer"))
        numerator = fallback[0]
    if denominator is None:
        issues.append(_issue(f"{path}.denominator", "time_signature_denominator", "denominator must be a positive integer"))
        denominator = fallback[1]
    return (numerator, denominator)


def _ending_passes(ending: dict[str, Any]) -> list[int]:
    raw_passes = ending.get("passes", ending.get("repeat_passes", ending.get("pass")))
    if raw_passes is None:
        number = ending.get("number", ending.get("ending"))
        raw_passes = [number] if number is not None else []
    if not isinstance(raw_passes, list):
        raw_passes = [raw_passes]
    passes: list[int] = []
    for value in raw_passes:
        parsed = _positive_int(value)
        if parsed is not None:
            passes.append(parsed)
    return passes


def _positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _positive_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _issue(path: str, code: str, message: str) -> LeadsheetValidationIssue:
    return LeadsheetValidationIssue(path=path, code=code, message=message)
