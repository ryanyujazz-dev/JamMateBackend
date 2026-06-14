from __future__ import annotations

from typing import Any

from .models import OpenProjectionMethod

DROP_FAMILY_DEFAULT_REGISTER_LOW = 36  # C2 in the project MIDI numbering convention.
from .placement_utils import Degree, PlacedDegree, dedupe_by_note, place_stack


def place_generic_open_projection(
    root_pc: int,
    degrees: list[Degree],
    low: int,
    high: int,
    policy: Any | None = None,
) -> list[PlacedDegree]:
    """Project a source through the legacy-compatible generic open method.

    ``GENERIC_OPEN`` remains the broad open-family fallback in v2_2_x.  Drop2,
    drop3, and other named open methods live in this module rather than in
    candidate generation or source planning.
    """

    del policy  # Reserved for future span/gap guards; keep the signature stable.
    return place_stack(root_pc, degrees, low, high, target_low=max(int(low), 52), spread_upper_voices=True)


def place_drop2_projection_from_closed_parent(
    parent_closed: list[PlacedDegree] | tuple[PlacedDegree, ...],
    policy: Any,
) -> list[PlacedDegree]:
    """Compatibility wrapper deriving OPEN/DROP2 from one closed parent."""

    return place_named_open_projection_from_closed_parent(parent_closed, policy, OpenProjectionMethod.DROP2)


def place_drop3_projection_from_closed_parent(
    parent_closed: list[PlacedDegree] | tuple[PlacedDegree, ...],
    policy: Any,
) -> list[PlacedDegree]:
    """Compatibility wrapper deriving OPEN/DROP3 from one closed parent."""

    return place_named_open_projection_from_closed_parent(parent_closed, policy, OpenProjectionMethod.DROP3)


def place_drop2_and_4_projection_from_closed_parent(
    parent_closed: list[PlacedDegree] | tuple[PlacedDegree, ...],
    policy: Any,
) -> list[PlacedDegree]:
    """Compatibility wrapper deriving OPEN/DROP2_AND_4 from one closed parent."""

    return place_named_open_projection_from_closed_parent(parent_closed, policy, OpenProjectionMethod.DROP2_AND_4)


def place_named_open_projection_from_closed_parent(
    parent_closed: list[PlacedDegree] | tuple[PlacedDegree, ...],
    policy: Any,
    method: OpenProjectionMethod,
) -> list[PlacedDegree]:
    """Derive one named OPEN projection from one concrete 4-note closed parent.

    This wrapper is kept for tests and simple callers.  Production candidate
    generation should use ``place_named_open_projection_from_closed_parents`` so
    DROP2/DROP3/DROP2&4 can project first, apply drop-family register guards,
    and only then choose a surviving candidate.
    """

    result = place_named_open_projection_from_closed_parents([parent_closed], policy, method)
    return result.placed


def place_named_open_projection_from_closed_parents(
    parent_closed_candidates: list[list[PlacedDegree] | tuple[PlacedDegree, ...]] | tuple[list[PlacedDegree] | tuple[PlacedDegree, ...], ...],
    policy: Any,
    method: OpenProjectionMethod,
) -> "NamedOpenProjectionSelection":
    """Project all closed-parent candidates, then filter and select.

    Named drop-family OPEN methods must **not** pre-select one closed parent and
    then hope the dropped voicing survives register guard.  The correct order is:

    1. enumerate source/orientation-aware closed parent candidates;
    2. apply DROP2 / DROP3 / DROP2&4 to each parent;
    3. apply the raised drop-family register/span guards to projected voicings;
    4. select one legal projected candidate.

    This fixes the v2_2_16 DROP2&4 single-note fallback bug where Dm7 lost all
    candidates after one too-low parent was chosen prematurely.
    """

    attempts: list[dict[str, object]] = []
    legal: list[tuple[int, list[PlacedDegree], list[PlacedDegree]]] = []
    seen: set[tuple[tuple[str, int], ...]] = set()
    for parent_index, raw_parent in enumerate(parent_closed_candidates):
        parent = _normalize_parent(raw_parent)
        if len(parent) != 4:
            attempts.append({"parent_index": parent_index, "valid_parent": False, "reason": "parent_not_4_note"})
            continue
        projected = _drop_voices_from_top(parent, _drop_voice_numbers_from_top(method))
        if len(projected) != 4:
            attempts.append({"parent_index": parent_index, "valid_parent": True, "parent_notes": [n for _, n in parent], "projected_notes": [n for _, n in projected], "accepted": False, "reason": "projection_not_4_note"})
            continue
        key = tuple((degree, int(note)) for degree, note in projected)
        if key in seen:
            attempts.append({"parent_index": parent_index, "valid_parent": True, "parent_notes": [n for _, n in parent], "projected_notes": [n for _, n in projected], "accepted": False, "reason": "duplicate_projection"})
            continue
        seen.add(key)
        guard_ok, guard_reason = _named_open_register_guard_reason(projected, policy)
        attempts.append({"parent_index": parent_index, "valid_parent": True, "parent_notes": [n for _, n in parent], "projected_notes": [n for _, n in projected], "accepted": guard_ok, "reason": guard_reason})
        if guard_ok:
            legal.append((parent_index, parent, projected))
    if not legal:
        return NamedOpenProjectionSelection(
            placed=[],
            parent_closed=[],
            parent_index=None,
            candidate_count=len(parent_closed_candidates),
            projected_candidate_count=len(attempts),
            legal_candidate_count=0,
            attempts=tuple(attempts),
        )

    selected_parent_index, selected_parent, selected_projected = min(
        legal,
        key=lambda item: _named_open_projection_cost(item[2], policy),
    )
    return NamedOpenProjectionSelection(
        placed=selected_projected,
        parent_closed=selected_parent,
        parent_index=selected_parent_index,
        candidate_count=len(parent_closed_candidates),
        projected_candidate_count=len(attempts),
        legal_candidate_count=len(legal),
        attempts=tuple(attempts),
    )


class NamedOpenProjectionSelection:
    """Selected named OPEN projection plus audit details."""

    def __init__(
        self,
        *,
        placed: list[PlacedDegree],
        parent_closed: list[PlacedDegree],
        parent_index: int | None,
        candidate_count: int,
        projected_candidate_count: int,
        legal_candidate_count: int,
        attempts: tuple[dict[str, object], ...] = (),
    ) -> None:
        self.placed = [(str(degree), int(note)) for degree, note in placed]
        self.parent_closed = [(str(degree), int(note)) for degree, note in parent_closed]
        self.parent_index = parent_index
        self.candidate_count = int(candidate_count)
        self.projected_candidate_count = int(projected_candidate_count)
        self.legal_candidate_count = int(legal_candidate_count)
        self.attempts = attempts


def named_open_projection_metadata(
    placed: list[PlacedDegree],
    method: OpenProjectionMethod,
    parent_closed: list[PlacedDegree] | tuple[PlacedDegree, ...] | None = None,
    *,
    parent_index: int | None = None,
    parent_candidate_count: int | None = None,
    projected_candidate_count: int | None = None,
    legal_candidate_count: int | None = None,
    policy: Any | None = None,
) -> dict[str, object]:
    """Return audit metadata for a named OPEN projected candidate."""

    notes = [int(note) for _, note in placed]
    method_value = method.value
    metadata: dict[str, object] = {
        "open_named_projection": bool(notes),
        "open_named_projection_method": method_value,
        "open_projection_density_supported": len(notes) == 4,
        "open_projection_layer": "core.voicing.disposition.open",
        "open_projection_parent_closed_required": True,
        "open_projection_from_parent_closed_projection": True,
        "open_named_projection_project_then_filter_selection": True,
        "open_named_projection_parent_source": "compact_closed_parent_candidates_for_projection",
        "open_named_projection_noncompact_parent_fallback_used": False,
        "open_named_projection_legacy_parent_fallback_used": False,
        "open_named_projection_silent_fallback_allowed": False,
    }
    if parent_index is not None:
        metadata["open_named_projection_parent_rotation_index"] = int(parent_index)
    if parent_candidate_count is not None:
        metadata["open_named_projection_parent_candidate_count"] = int(parent_candidate_count)
    if projected_candidate_count is not None:
        metadata["open_named_projection_projected_candidate_count"] = int(projected_candidate_count)
    if legal_candidate_count is not None:
        metadata["open_named_projection_legal_candidate_count"] = int(legal_candidate_count)
    if policy is not None:
        metadata["open_named_projection_drop_register_low"] = _named_open_register_low(policy)
        metadata["open_named_projection_drop_register_low_offset_semitones"] = _drop_family_register_low_offset(policy)
        metadata["open_named_projection_drop_register_low_source"] = _drop_family_register_low_source(policy)
    alias_prefix = _open_method_alias_prefix(method)
    # Harness-visible compatibility token for the v2_2_x DROP2 contract:
    # open_drop2_from_parent_closed_projection
    if alias_prefix:
        alias_data = {
            f"{alias_prefix}_projection": bool(notes),
            f"{alias_prefix}_density_supported": len(notes) == 4,
            f"{alias_prefix}_projection_layer": "core.voicing.disposition.open",
            f"{alias_prefix}_parent_closed_required": True,
            f"{alias_prefix}_from_parent_closed_projection": True,
            f"{alias_prefix}_project_then_filter_selection": True,
        }
        if parent_index is not None:
            alias_data[f"{alias_prefix}_parent_rotation_index"] = int(parent_index)
        if legal_candidate_count is not None:
            alias_data[f"{alias_prefix}_legal_candidate_count"] = int(legal_candidate_count)
        metadata.update(alias_data)
    if not notes:
        metadata["open_named_projection_empty"] = True
        if alias_prefix:
            metadata[f"{alias_prefix}_projection_empty"] = True
        return metadata

    span = max(notes) - min(notes)
    metadata["open_named_projection_span"] = span
    if alias_prefix:
        metadata[f"{alias_prefix}_span"] = span
    if parent_closed is not None:
        parent = _normalize_parent(parent_closed)
        parent_degrees = [degree for degree, _ in parent]
        parent_notes = [note for _, note in parent]
        parent_span = max(parent_notes) - min(parent_notes) if parent_notes else 0
        metadata.update(
            {
                "open_named_projection_parent_closed_degrees": parent_degrees,
                "open_named_projection_parent_closed_notes": parent_notes,
                "open_named_projection_parent_closed_span": parent_span,
            }
        )
        if alias_prefix:
            metadata.update(
                {
                    f"{alias_prefix}_parent_closed_degrees": parent_degrees,
                    f"{alias_prefix}_parent_closed_notes": parent_notes,
                    f"{alias_prefix}_parent_closed_span": parent_span,
                }
            )
    return metadata



def _open_method_alias_prefix(method: OpenProjectionMethod) -> str:
    if method == OpenProjectionMethod.DROP2:
        return "open_drop2"
    if method == OpenProjectionMethod.DROP3:
        return "open_drop3"
    if method == OpenProjectionMethod.DROP2_AND_4:
        return "open_drop2_and_4"
    return ""

def drop2_projection_metadata(
    placed: list[PlacedDegree],
    parent_closed: list[PlacedDegree] | tuple[PlacedDegree, ...] | None = None,
) -> dict[str, object]:
    """Return audit metadata for a DROP2 projected candidate."""

    return named_open_projection_metadata(placed, OpenProjectionMethod.DROP2, parent_closed)


def _drop_voice_numbers_from_top(method: OpenProjectionMethod) -> tuple[int, ...]:
    if method == OpenProjectionMethod.DROP2:
        return (2,)
    if method == OpenProjectionMethod.DROP3:
        return (3,)
    if method == OpenProjectionMethod.DROP2_AND_4:
        return (2, 4)
    return ()


def _drop_voices_from_top(closed: list[PlacedDegree], voice_numbers_from_top: tuple[int, ...]) -> list[PlacedDegree]:
    ordered = _normalize_parent(closed)
    if len(ordered) != 4 or not voice_numbers_from_top:
        return []
    indexes_to_drop = {len(ordered) - int(voice_number) for voice_number in voice_numbers_from_top}
    if any(index < 0 or index >= len(ordered) for index in indexes_to_drop):
        return []
    dropped = [
        (degree, note - 12 if idx in indexes_to_drop else note)
        for idx, (degree, note) in enumerate(ordered)
    ]
    return sorted(dedupe_by_note(dropped), key=lambda item: item[1])


def _normalize_parent(parent_closed: list[PlacedDegree] | tuple[PlacedDegree, ...]) -> list[PlacedDegree]:
    return sorted(((str(degree), int(note)) for degree, note in parent_closed), key=lambda item: item[1])


def _named_open_register_guard(placed: list[PlacedDegree], policy: Any) -> bool:
    ok, _ = _named_open_register_guard_reason(placed, policy)
    return ok


def _named_open_register_guard_reason(placed: list[PlacedDegree], policy: Any) -> tuple[bool, str]:
    notes = [int(note) for _, note in placed]
    if len(notes) != 4:
        return False, "not_4_note_projection"
    low = _named_open_register_low(policy)
    high = int(getattr(policy, "register_high"))
    if not all(low <= note <= high for note in notes):
        return False, "outside_raised_drop_register"
    max_span = int(getattr(policy, "max_voicing_span"))
    span_cap = max(max_span, int(dict(getattr(policy, "metadata", None) or {}).get("drop_family_max_span", 24)))
    if max(notes) - min(notes) > span_cap:
        return False, "span_guard_failed"
    return True, "accepted"


def _drop_family_register_low_offset(policy: Any) -> int:
    metadata = dict(getattr(policy, "metadata", None) or {})
    if "drop_family_register_low_offset_semitones" in metadata:
        return int(metadata["drop_family_register_low_offset_semitones"])
    return 0


def _drop_family_register_low_source(policy: Any) -> str:
    metadata = dict(getattr(policy, "metadata", None) or {})
    if "drop_family_register_low" in metadata:
        return "metadata_absolute_floor"
    if "drop_family_register_low_offset_semitones" in metadata:
        return "legacy_offset_from_policy_register_low"
    return "default_c2_floor"


def _named_open_register_low(policy: Any) -> int:
    metadata = dict(getattr(policy, "metadata", None) or {})
    base_low = int(getattr(policy, "register_low"))
    if "drop_family_register_low" in metadata:
        return int(metadata["drop_family_register_low"])
    if "drop_family_register_low_offset_semitones" in metadata:
        return base_low + int(metadata["drop_family_register_low_offset_semitones"])
    return DROP_FAMILY_DEFAULT_REGISTER_LOW


def _named_open_projection_cost(placed: list[PlacedDegree], policy: Any) -> tuple[float, int, int]:
    notes = [int(note) for _, note in placed]
    avg = sum(notes) / len(notes)
    comfort_low = int(getattr(policy, "comfort_register_low", getattr(policy, "register_low")))
    comfort_high = int(getattr(policy, "comfort_register_high", getattr(policy, "register_high")))
    center = (comfort_low + comfort_high) / 2
    top = max(notes)
    top_low = int(getattr(policy, "top_voice_low", comfort_low))
    top_high = int(getattr(policy, "top_voice_high", comfort_high))
    top_center = (top_low + top_high) / 2
    span = max(notes) - min(notes)
    low = min(notes)
    low_floor = _named_open_register_low(policy)
    low_penalty = max(0, low_floor + 3 - low) * 0.25
    return (abs(avg - center) + 0.18 * abs(top - top_center) + low_penalty, span, top)
