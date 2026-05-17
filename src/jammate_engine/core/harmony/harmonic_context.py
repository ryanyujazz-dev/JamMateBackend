from __future__ import annotations

from dataclasses import dataclass

from .chord_parser import ParsedChord, parse_chord
from .scale_resolver import ResolvedScalePolicy, resolve_scale_policy_detail

CYCLE_UP_FOURTH = 5
BACKDOOR_UP_WHOLE_STEP = 2
TURNAROUND_I_TO_VI = 9


@dataclass(frozen=True)
class FunctionalMotion:
    """Reusable, style-neutral harmonic motion facts for a three-chord window.

    Harmony may classify local function and root motion, but it must not choose
    style weights, voicing layouts, BassFoundation patterns, or realization
    details.  The labels here are intentionally conservative metadata for later
    BassFoundation / Voicing / Comping / Fill / Solo consumers.
    """

    previous_symbol: str | None
    current_symbol: str
    next_symbol: str | None
    previous_function: str | None
    current_function: str
    next_function: str | None
    root_interval_from_previous: int | None
    root_interval_to_next: int | None
    previous_to_current_type: str
    current_to_next_type: str
    window_type: str
    tags: tuple[str, ...] = ()

    @property
    def is_current_next_ii_v(self) -> bool:
        return self.current_to_next_type in {"ii_v", "minor_ii_v"}

    @property
    def is_current_next_v_i(self) -> bool:
        return self.current_to_next_type in {"v_i_major", "v_i_minor", "dominant_to_tonic"}

    @property
    def is_ii_v_i(self) -> bool:
        return self.window_type in {"major_ii_v_i", "minor_ii_v_i", "ii_v_i"}

    @property
    def is_minor_ii_v(self) -> bool:
        return self.previous_to_current_type == "minor_ii_v" or self.current_to_next_type == "minor_ii_v"

    @property
    def is_minor_ii_v_i(self) -> bool:
        return self.window_type == "minor_ii_v_i"

    @property
    def is_dominant_resolution(self) -> bool:
        return "dominant_resolution" in self.tags

    @property
    def is_tonic_prolongation(self) -> bool:
        return self.current_to_next_type == "tonic_prolongation"

    @property
    def is_turnaround_like(self) -> bool:
        return "turnaround_like" in self.tags

    @property
    def is_backdoor_dominant(self) -> bool:
        return self.current_to_next_type == "backdoor_dominant" or "backdoor_dominant" in self.tags

    @property
    def is_static_blues_dominant(self) -> bool:
        return self.current_to_next_type == "static_blues_dominant" or "static_blues_dominant" in self.tags

    @property
    def is_non_functional(self) -> bool:
        return self.current_to_next_type == "non_functional"

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags


@dataclass(frozen=True)
class HarmonicContext:
    chord_symbol: str
    next_chord_symbol: str | None
    scale_policy: str
    previous_chord_symbol: str | None = None

    @classmethod
    def from_symbols(
        cls,
        *,
        chord_symbol: str,
        next_chord_symbol: str | None = None,
        previous_chord_symbol: str | None = None,
    ) -> "HarmonicContext":
        detail = resolve_scale_policy_detail(chord_symbol)
        return cls(
            chord_symbol=chord_symbol,
            next_chord_symbol=next_chord_symbol,
            scale_policy=detail.mode,
            previous_chord_symbol=previous_chord_symbol,
        )

    @property
    def current_chord(self) -> ParsedChord:
        return parse_chord(self.chord_symbol)

    @property
    def next_chord(self) -> ParsedChord | None:
        return parse_chord(self.next_chord_symbol) if self.next_chord_symbol else None

    @property
    def previous_chord(self) -> ParsedChord | None:
        return parse_chord(self.previous_chord_symbol) if self.previous_chord_symbol else None

    @property
    def scale_detail(self) -> ResolvedScalePolicy:
        return resolve_scale_policy_detail(self.chord_symbol)

    @property
    def functional_motion(self) -> FunctionalMotion:
        return classify_functional_motion(
            chord_symbol=self.chord_symbol,
            next_chord_symbol=self.next_chord_symbol,
            previous_chord_symbol=self.previous_chord_symbol,
        )

    def has_functional_motion_tag(self, tag: str) -> bool:
        return self.functional_motion.has_tag(tag)


def classify_functional_motion(
    *,
    chord_symbol: str,
    next_chord_symbol: str | None = None,
    previous_chord_symbol: str | None = None,
) -> FunctionalMotion:
    """Classify style-neutral functional motion around the current chord.

    The classifier is keyless by design.  It recognizes root-cycle facts and
    chord-quality relationships that later style layers can use as context.
    It does not decide whether to play a particular bass pattern, voicing, fill,
    or rhythmic figure.
    """

    previous = parse_chord(previous_chord_symbol) if previous_chord_symbol else None
    current = parse_chord(chord_symbol)
    next_chord = parse_chord(next_chord_symbol) if next_chord_symbol else None

    previous_pair_type, previous_pair_tags = _classify_pair(previous, current)
    current_pair_type, current_pair_tags = _classify_pair(current, next_chord)
    window_type, window_tags = _classify_window(previous, current, next_chord, previous_pair_type, current_pair_type)

    tags = _dedupe((*previous_pair_tags, *current_pair_tags, *window_tags))
    return FunctionalMotion(
        previous_symbol=previous.symbol if previous else None,
        current_symbol=current.symbol,
        next_symbol=next_chord.symbol if next_chord else None,
        previous_function=_local_function(previous) if previous else None,
        current_function=_local_function(current),
        next_function=_local_function(next_chord) if next_chord else None,
        root_interval_from_previous=_root_interval(previous, current),
        root_interval_to_next=_root_interval(current, next_chord),
        previous_to_current_type=previous_pair_type,
        current_to_next_type=current_pair_type,
        window_type=window_type,
        tags=tags,
    )


def _classify_pair(current: ParsedChord | None, next_chord: ParsedChord | None) -> tuple[str, tuple[str, ...]]:
    if current is None or next_chord is None:
        return "none", ()

    interval = _root_interval(current, next_chord)
    if interval is None:
        return "none", ()

    if interval == 0 and _is_tonic_candidate(current) and _is_tonic_candidate(next_chord):
        return "tonic_prolongation", ("tonic_prolongation",)

    tags: list[str] = []
    if interval == CYCLE_UP_FOURTH:
        tags.append("cycle_of_fourths")

        if _is_predominant_minor(current) and next_chord.is_dominant:
            if current.is_half_diminished:
                return "minor_ii_v", tuple(_dedupe((*tags, "minor_ii_v", "predominant_to_dominant")))
            return "ii_v", tuple(_dedupe((*tags, "ii_v", "predominant_to_dominant")))

        if current.is_dominant and _is_tonic_candidate(next_chord):
            tonic_flavor = _tonic_flavor(next_chord)
            pair_type = "v_i_minor" if tonic_flavor == "minor" else "v_i_major"
            return pair_type, tuple(_dedupe((*tags, "dominant_resolution", "dominant_to_tonic")))

        if current.is_dominant:
            return "secondary_dominant_motion", tuple(_dedupe((*tags, "dominant_resolution", "secondary_dominant_motion")))

        return "cycle_motion", tuple(tags)

    if current.is_dominant and _is_tonic_candidate(next_chord) and interval == BACKDOOR_UP_WHOLE_STEP:
        return "backdoor_dominant", ("dominant_resolution", "backdoor_dominant", "backdoor_resolution")

    if current.is_dominant and interval == 0:
        return "static_blues_dominant", ("static_blues_dominant", "static_dominant")

    return "non_functional", ()


def _classify_window(
    previous: ParsedChord | None,
    current: ParsedChord,
    next_chord: ParsedChord | None,
    previous_pair_type: str,
    current_pair_type: str,
) -> tuple[str, tuple[str, ...]]:
    if previous is None or next_chord is None:
        return "none", ()

    if previous_pair_type in {"ii_v", "minor_ii_v"} and current_pair_type in {"v_i_major", "v_i_minor"}:
        if previous_pair_type == "minor_ii_v" and current_pair_type == "v_i_minor":
            return "minor_ii_v_i", ("ii_v_i", "minor_ii_v_i", "dominant_resolution")
        if previous_pair_type == "ii_v" and current_pair_type == "v_i_major":
            return "major_ii_v_i", ("ii_v_i", "major_ii_v_i", "dominant_resolution")
        return "ii_v_i", ("ii_v_i", "dominant_resolution")

    if _is_turnaround_like_window(previous, current, next_chord, previous_pair_type, current_pair_type):
        return "turnaround_like", ("turnaround_like",)

    return "none", ()


def _is_turnaround_like_window(
    previous: ParsedChord,
    current: ParsedChord,
    next_chord: ParsedChord,
    previous_pair_type: str,
    current_pair_type: str,
) -> bool:
    # Common I -> VI -> II / I -> VI7 -> II turnaround opening.
    if (
        _is_tonic_candidate(previous)
        and _root_interval(previous, current) == TURNAROUND_I_TO_VI
        and _root_interval(current, next_chord) == CYCLE_UP_FOURTH
        and (current.is_dominant or _is_predominant_minor(current))
        and (_is_predominant_minor(next_chord) or next_chord.is_dominant or _is_tonic_candidate(next_chord))
    ):
        return True

    # Middle of a cycle turnaround, for example A7 -> Dm7 -> G7.
    if previous_pair_type in {"secondary_dominant_motion", "v_i_minor", "cycle_motion"} and current_pair_type in {
        "ii_v",
        "minor_ii_v",
        "cycle_motion",
    }:
        return True

    return False


def _root_interval(a: ParsedChord | None, b: ParsedChord | None) -> int | None:
    if a is None or b is None:
        return None
    return (b.root_pc - a.root_pc) % 12


def _local_function(chord: ParsedChord) -> str:
    if chord.is_half_diminished:
        return "predominant_half_diminished"
    if _is_predominant_minor(chord):
        return "predominant_minor_or_minor_tonic"
    if chord.is_dominant:
        return "dominant"
    flavor = _tonic_flavor(chord)
    if flavor:
        return f"tonic_{flavor}_candidate"
    if chord.quality == "diminished":
        return "diminished_color"
    if chord.is_suspended:
        return "suspended_color"
    return "color_or_nonfunctional"


def _is_predominant_minor(chord: ParsedChord) -> bool:
    return chord.is_half_diminished or (chord.quality == "minor" and not chord.is_fully_diminished)


def _is_tonic_candidate(chord: ParsedChord) -> bool:
    return _tonic_flavor(chord) is not None


def _tonic_flavor(chord: ParsedChord) -> str | None:
    if chord.quality == "major" and not chord.is_dominant and not chord.is_suspended:
        return "major"
    if chord.quality == "minor" and not chord.is_half_diminished and not chord.is_fully_diminished:
        return "minor"
    return None


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return tuple(out)
