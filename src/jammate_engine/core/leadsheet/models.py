from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


LEADSHEET_SCHEMA_VERSION = "jammate_leadsheet_v2"


@dataclass(frozen=True)
class ChordEvent:
    """Source-score chord onset, written as a one-based bar beat.

    This is the UI/LLM-facing form. Durations are intentionally derived by the
    form compiler from the next chord onset or the bar boundary.
    """

    symbol: str
    beat: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChordCell:
    """Compiled chord span inside one bar.

    Generation remains chord-region-first. A ChordCell is the bridge between a
    source-score ChordEvent and a runtime HarmonicRegion.
    """

    symbol: str
    beats: float = 4.0
    beat: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Bar:
    chords: list[ChordCell]
    time_signature: tuple[int, int] = (4, 4)
    section_id: str | None = None
    section_label: str | None = None
    phrase: str | None = None
    role: str | None = None
    source_bar_index: int | None = None
    written_bar_index: int | None = None
    form_index: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_beats(self) -> float:
        return float(self.time_signature[0])


@dataclass(frozen=True)
class SectionBlock:
    id: str
    bars: list[Bar]
    label: str | None = None
    phrase: str | None = None
    role: str = "normal"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WrittenFormItem:
    """One compiled written-form section reference.

    Repeat signs, first/second endings, tags, and final endings are resolved
    into this flat written-form contract before runtime chorus repetition.
    Generation never consumes repeat-symbol syntax directly.
    """

    section_id: str
    repeat: int = 1
    label: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExpandedBar:
    """Compiled written-form bar before performance chorus repetition."""

    bar: Bar
    written_bar_index: int
    form_index: int
    section_bar_index: int
    section_id: str
    section_label: str | None = None
    phrase: str | None = None
    role: str | None = None


@dataclass(frozen=True)
class Leadsheet:
    """V2 leadsheet document.

    Source data may be human-readable section/form notation, but the compiler
    exposes expanded bars and then HarmonicRegion objects for V2 generation.
    Performance chorus count belongs to GenerationRequest, not this document.
    """

    title: str
    bars: list[Bar]
    key: str = "C"
    default_time_signature: tuple[int, int] = (4, 4)
    schema_version: str = LEADSHEET_SCHEMA_VERSION
    sections: dict[str, SectionBlock] = field(default_factory=dict)
    written_form: list[WrittenFormItem] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Leadsheet":
        title = str(data.get("title", "Untitled"))
        key = str(data.get("key", "C"))
        default_ts = _parse_time_signature(data.get("default_time_signature"))
        schema_version = str(data.get("schema_version", LEADSHEET_SCHEMA_VERSION))

        sections = _parse_sections(data, default_ts)
        written_form = _parse_written_form(data, sections)
        bars = _compile_written_form_bars(sections, written_form)

        if not bars:
            raw_bars = list(data.get("bars", []))
            bars = [
                _parse_bar(
                    raw_bar,
                    default_ts,
                    section_id="MAIN",
                    section_label="MAIN",
                    phrase="A",
                    role="normal",
                    source_bar_index=index,
                    written_bar_index=index,
                    form_index=0,
                )
                for index, raw_bar in enumerate(raw_bars)
            ]
            if bars:
                main_section = SectionBlock(id="MAIN", label="MAIN", phrase="A", role="normal", bars=bars)
                sections = {"MAIN": main_section}
                written_form = [WrittenFormItem(section_id="MAIN")]

        if not bars:
            bars = [
                Bar(
                    chords=[ChordCell(symbol="C", beats=float(default_ts[0]), beat=1.0)],
                    time_signature=default_ts,
                    section_id="MAIN",
                    section_label="MAIN",
                    phrase="A",
                    role="normal",
                    source_bar_index=0,
                    written_bar_index=0,
                    form_index=0,
                )
            ]
            sections = {"MAIN": SectionBlock(id="MAIN", label="MAIN", phrase="A", role="normal", bars=bars)}
            written_form = [WrittenFormItem(section_id="MAIN")]

        return Leadsheet(
            title=title,
            key=key,
            bars=bars,
            default_time_signature=default_ts,
            schema_version=schema_version,
            sections=sections,
            written_form=written_form,
            metadata={
                **dict(data.get("metadata", {})),
                "artist": data.get("artist"),
                "composer": data.get("composer", data.get("artist")),
                "tempo": data.get("tempo"),
                "source_shape": _source_shape(data),
                "written_bars": len(bars),
                "performance_repetitions_live_in_request": True,
            },
        )

    def expanded_bars(self) -> list[ExpandedBar]:
        expanded: list[ExpandedBar] = []
        for index, bar in enumerate(self.bars):
            expanded.append(
                ExpandedBar(
                    bar=bar,
                    written_bar_index=index,
                    form_index=int(bar.form_index or 0),
                    section_bar_index=int(bar.source_bar_index or 0),
                    section_id=str(bar.section_id or "MAIN"),
                    section_label=bar.section_label,
                    phrase=bar.phrase,
                    role=bar.role,
                )
            )
        return expanded


def _source_shape(data: dict[str, Any]) -> str:
    if "sections" in data and "written_form" in data:
        return "v2_sections_written_form"
    if "sections" in data and "form" in data:
        return "sections_form_import_shape"
    return "flat_bars"


def _parse_sections(data: dict[str, Any], default_ts: tuple[int, int]) -> dict[str, SectionBlock]:
    raw_sections: Any
    if "sections" in data:
        raw_sections = data.get("sections", {})
    else:
        return {}

    items: list[tuple[str, Any]] = []
    if isinstance(raw_sections, dict):
        items = [(str(key), value) for key, value in raw_sections.items()]
    elif isinstance(raw_sections, list):
        for index, value in enumerate(raw_sections):
            if isinstance(value, dict):
                section_id = str(value.get("id", value.get("label", f"S{index + 1}")))
                items.append((section_id, value))

    sections: dict[str, SectionBlock] = {}
    for section_id, raw in items:
        if not isinstance(raw, dict):
            continue
        label = str(raw.get("label", section_id))
        phrase = raw.get("phrase")
        role = str(raw.get("role", "normal"))
        bars = [
            _parse_bar(
                raw_bar,
                default_ts,
                section_id=section_id,
                section_label=label,
                phrase=str(phrase) if phrase is not None else None,
                role=role,
                source_bar_index=bar_index,
            )
            for bar_index, raw_bar in enumerate(list(raw.get("bars", [])))
        ]
        sections[section_id] = SectionBlock(
            id=section_id,
            label=label,
            phrase=str(phrase) if phrase is not None else None,
            role=role,
            bars=bars,
            metadata=dict(raw.get("metadata", {})),
        )
    return sections


def _parse_written_form(data: dict[str, Any], sections: dict[str, SectionBlock]) -> list[WrittenFormItem]:
    raw_form = data.get("written_form", data.get("form"))
    if raw_form is None and sections:
        raw_form = list(sections.keys())
    form: list[WrittenFormItem] = []
    for raw_item in list(raw_form or []):
        form.extend(_parse_form_item(raw_item))
    return [item for item in form if item.section_id in sections]


def _parse_form_item(raw_item: Any) -> list[WrittenFormItem]:
    return _parse_form_item_with_context(raw_item, inherited_metadata={})


def _parse_form_item_with_context(raw_item: Any, *, inherited_metadata: dict[str, Any]) -> list[WrittenFormItem]:
    if isinstance(raw_item, str):
        return [WrittenFormItem(section_id=raw_item, metadata=dict(inherited_metadata))]
    if not isinstance(raw_item, dict):
        return []

    item_type = raw_item.get("type")
    if item_type in {"tag", "ending", "final_ending"}:
        return _parse_role_body_form_item(raw_item, inherited_metadata=inherited_metadata, form_role=str(item_type))
    if item_type == "repeat" or ("body" in raw_item and "section" not in raw_item):
        return _parse_repeat_form_item(raw_item, inherited_metadata=inherited_metadata)

    if "section" in raw_item:
        repeat = max(1, int(raw_item.get("repeat", raw_item.get("times", 1))))
        metadata = {**dict(inherited_metadata), **dict(raw_item.get("metadata", {}))}
        for token in ("form_role", "repeat_group", "repeat_pass", "ending_number", "ending_passes"):
            if token in raw_item and token not in metadata:
                metadata[token] = raw_item[token]
        return [
            WrittenFormItem(
                section_id=str(raw_item.get("section")),
                repeat=repeat,
                label=raw_item.get("label"),
                metadata=metadata,
            )
        ]
    if item_type == "block" or "label" in raw_item:
        metadata = {**dict(inherited_metadata), **dict(raw_item.get("metadata", {}))}
        return [WrittenFormItem(section_id=str(raw_item.get("label", "")), metadata=metadata)]
    return []


def _parse_repeat_form_item(raw_item: dict[str, Any], *, inherited_metadata: dict[str, Any]) -> list[WrittenFormItem]:
    endings = list(raw_item.get("endings", []))
    inferred_times = len(endings) if endings else 1
    times = max(1, int(raw_item.get("times", raw_item.get("repeat", inferred_times))))
    repeat_group = str(raw_item.get("id", raw_item.get("label", "repeat")))
    base_metadata = {
        **dict(inherited_metadata),
        **dict(raw_item.get("metadata", {})),
        "form_role": "repeat",
        "repeat_group": repeat_group,
    }

    items: list[WrittenFormItem] = []
    for repeat_pass in range(1, times + 1):
        pass_metadata = {**base_metadata, "repeat_pass": repeat_pass, "repeat_times": times}
        for body_item in list(raw_item.get("body", [])):
            items.extend(_parse_form_item_with_context(body_item, inherited_metadata=pass_metadata))
        for ending in _matching_endings_for_pass(endings, repeat_pass):
            items.extend(_parse_ending_form_item(ending, repeat_pass=repeat_pass, inherited_metadata=pass_metadata))
    return items


def _parse_role_body_form_item(raw_item: dict[str, Any], *, inherited_metadata: dict[str, Any], form_role: str) -> list[WrittenFormItem]:
    metadata = {**dict(inherited_metadata), **dict(raw_item.get("metadata", {})), "form_role": form_role}
    label = raw_item.get("label")
    if label is not None:
        metadata.setdefault("form_label", label)
    body = raw_item.get("body")
    if body is None and "section" in raw_item:
        body = [{"section": raw_item.get("section"), "label": label, "metadata": metadata}]
    items: list[WrittenFormItem] = []
    for body_item in list(body or []):
        items.extend(_parse_form_item_with_context(body_item, inherited_metadata=metadata))
    return items


def _parse_ending_form_item(ending: Any, *, repeat_pass: int, inherited_metadata: dict[str, Any]) -> list[WrittenFormItem]:
    if not isinstance(ending, dict):
        return []
    ending_number = ending.get("number", ending.get("ending", repeat_pass))
    ending_passes = _ending_passes(ending)
    metadata = {
        **dict(inherited_metadata),
        **dict(ending.get("metadata", {})),
        "form_role": "ending",
        "ending_number": ending_number,
        "ending_passes": ending_passes,
    }
    body = ending.get("body")
    if body is None and "section" in ending:
        body = [{"section": ending.get("section"), "label": ending.get("label"), "metadata": metadata}]
    items: list[WrittenFormItem] = []
    for body_item in list(body or []):
        items.extend(_parse_form_item_with_context(body_item, inherited_metadata=metadata))
    return items


def _matching_endings_for_pass(endings: list[Any], repeat_pass: int) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for index, ending in enumerate(endings, start=1):
        if not isinstance(ending, dict):
            continue
        passes = _ending_passes(ending, fallback=index)
        if repeat_pass in passes:
            matches.append(ending)
    return matches


def _ending_passes(ending: dict[str, Any], fallback: int | None = None) -> list[int]:
    raw_passes = ending.get("passes", ending.get("repeat_passes", ending.get("pass")))
    if raw_passes is None:
        number = ending.get("number", ending.get("ending", fallback))
        raw_passes = [number] if number is not None else []
    if not isinstance(raw_passes, list):
        raw_passes = [raw_passes]
    passes: list[int] = []
    for value in raw_passes:
        try:
            passes.append(int(value))
        except (TypeError, ValueError):
            continue
    return passes


def _compile_written_form_bars(sections: dict[str, SectionBlock], form: list[WrittenFormItem]) -> list[Bar]:
    bars: list[Bar] = []
    written_index = 0
    for form_index, item in enumerate(form):
        section = sections.get(item.section_id)
        if section is None:
            continue
        for _ in range(max(1, int(item.repeat))):
            for section_bar_index, bar in enumerate(section.bars):
                bars.append(
                    Bar(
                        chords=list(bar.chords),
                        time_signature=bar.time_signature,
                        section_id=section.id,
                        section_label=section.label,
                        phrase=section.phrase,
                        role=section.role,
                        source_bar_index=section_bar_index,
                        written_bar_index=written_index,
                        form_index=form_index,
                        metadata={**dict(bar.metadata), **dict(item.metadata), "form_item_label": item.label},
                    )
                )
                written_index += 1
    return bars


def _parse_bar(
    raw_bar: Any,
    default_ts: tuple[int, int],
    *,
    section_id: str | None = None,
    section_label: str | None = None,
    phrase: str | None = None,
    role: str | None = None,
    source_bar_index: int | None = None,
    written_bar_index: int | None = None,
    form_index: int | None = None,
) -> Bar:
    if isinstance(raw_bar, str):
        return Bar(
            chords=[ChordCell(symbol=raw_bar, beats=float(default_ts[0]), beat=1.0)],
            time_signature=default_ts,
            section_id=section_id,
            section_label=section_label,
            phrase=phrase,
            role=role,
            source_bar_index=source_bar_index,
            written_bar_index=written_bar_index,
            form_index=form_index,
        )

    time_signature = _parse_time_signature(raw_bar.get("time_signature"), fallback=default_ts) if isinstance(raw_bar, dict) else default_ts
    total_beats = float(time_signature[0])
    raw_chords = list(raw_bar.get("chords", [])) if isinstance(raw_bar, dict) else []
    metadata = dict(raw_bar.get("metadata", {})) if isinstance(raw_bar, dict) else {}
    if not raw_chords:
        return Bar(
            chords=[ChordCell(symbol="C", beats=total_beats, beat=1.0)],
            time_signature=time_signature,
            section_id=section_id,
            section_label=section_label,
            phrase=phrase,
            role=role,
            source_bar_index=source_bar_index,
            written_bar_index=written_bar_index,
            form_index=form_index,
            metadata=metadata,
        )

    chord_starts: list[tuple[float, str, float | None, dict[str, Any]]] = []
    for chord in raw_chords:
        symbol = str(chord.get("symbol", "C"))
        start_beat = float(chord.get("beat", 1.0))
        explicit_beats = chord.get("beats")
        chord_meta = dict(chord.get("metadata", {}))
        chord_starts.append((max(1.0, min(start_beat, total_beats)), symbol, float(explicit_beats) if explicit_beats is not None else None, chord_meta))
    chord_starts.sort(key=lambda item: item[0])

    chords: list[ChordCell] = []
    for index, (start_beat, symbol, explicit_beats, chord_meta) in enumerate(chord_starts):
        if explicit_beats is not None:
            duration = explicit_beats
        else:
            next_start = chord_starts[index + 1][0] if index + 1 < len(chord_starts) else total_beats + 1.0
            duration = max(0.25, next_start - start_beat)
        chords.append(ChordCell(symbol=symbol, beats=duration, beat=start_beat, metadata=chord_meta))
    return Bar(
        chords=chords,
        time_signature=time_signature,
        section_id=section_id,
        section_label=section_label,
        phrase=phrase,
        role=role,
        source_bar_index=source_bar_index,
        written_bar_index=written_bar_index,
        form_index=form_index,
        metadata=metadata,
    )


def _parse_time_signature(raw: Any, fallback: tuple[int, int] = (4, 4)) -> tuple[int, int]:
    if not isinstance(raw, dict):
        return fallback
    numerator = int(raw.get("numerator", fallback[0]))
    denominator = int(raw.get("denominator", fallback[1]))
    return (numerator, denominator)
