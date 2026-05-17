from __future__ import annotations

from typing import Any

from jammate_engine.core.harmony.material import degree_to_semitone

Degree = tuple[str, int]
PlacedDegree = tuple[str, int]


def effective_closed_register_low(policy: Any) -> int:
    """Return the effective low-register floor for compact closed projection.

    v2_1.x tuned closed 3/4-note voicings with an optional lowest-note floor
    stored in policy metadata.  The logic now lives with the closed disposition
    projection layer so candidate generation no longer owns closed-specific
    placement rules.
    """

    metadata = dict(getattr(policy, "metadata", None) or {})
    register_low = int(getattr(policy, "register_low"))
    if "closed_voicing_lowest_note_floor" in metadata:
        return max(register_low, int(metadata["closed_voicing_lowest_note_floor"]))
    if "closed_voicing_lowest_note_floor_offset_semitones" in metadata:
        return register_low + int(metadata["closed_voicing_lowest_note_floor_offset_semitones"])
    return register_low


def strict_closed_compact_layout_enabled(policy: Any) -> bool:
    """Whether the tuned strict closed pitch-class layout should be used."""

    return bool(dict(getattr(policy, "metadata", None) or {}).get("strict_closed_compact_pitch_class_layout", False))


def closed_compactness_metadata(notes: list[int], policy: Any) -> dict[str, object]:
    """Return closed-only debug metadata for candidate audits."""

    span = max(notes) - min(notes) if notes else 0
    return {
        "closed_voicing_lowest_note_floor": effective_closed_register_low(policy),
        "closed_voicing_actual_span": span,
        "strict_closed_compact_pitch_class_layout": strict_closed_compact_layout_enabled(policy),
        "closed_projection_layer": "core.voicing.disposition.closed",
    }


def place_compact_closed_seed_layout(
    root_pc: int,
    degrees: list[Degree],
    policy: Any,
) -> list[PlacedDegree]:
    """Return a closed pitch-class seed layout for strict closed generation.

    Source family selection decides the eligible functional tones.  Strict
    closed mode first builds legal closed circular pitch-class layouts; later the
    selector chooses the nearest realization to the previous voicing inside each
    semantic source.  This seed only preserves pitch-class/degree pairing for the
    generic variant generator and must not impose a final spacing preference.
    """

    if not degrees:
        return []
    compact_offsets: list[tuple[str, int]] = []
    for degree, semitone in degrees:
        offset = _ordered_compact_offset(str(degree), int(semitone)) % 12
        compact_offsets.append((str(degree), offset))
    if len({offset for _, offset in compact_offsets}) != len(compact_offsets):
        return []

    sorted_offsets = sorted(compact_offsets, key=lambda item: item[1])
    layouts: list[list[tuple[str, int]]] = []
    count = len(sorted_offsets)
    for start in range(count):
        base_offset = sorted_offsets[start][1]
        layout: list[tuple[str, int]] = []
        previous: int | None = None
        for step in range(count):
            degree, offset = sorted_offsets[(start + step) % count]
            actual = int(offset)
            while actual < base_offset:
                actual += 12
            while previous is not None and actual <= previous:
                actual += 12
            layout.append((degree, actual))
            previous = actual
        layouts.append(layout)

    closed_low = effective_closed_register_low(policy)
    placed_candidates: list[list[PlacedDegree]] = []
    register_high = int(getattr(policy, "register_high"))
    max_span = int(getattr(policy, "max_voicing_span"))
    for layout in layouts:
        for root_octave in range(24, 85, 12):
            root_ref = root_octave + int(root_pc)
            placed = [(degree, root_ref + offset) for degree, offset in layout]
            notes = [note for _, note in placed]
            if not all(closed_low <= note <= register_high for note in notes):
                continue
            if max(notes) - min(notes) > max_span:
                continue
            placed_candidates.append(placed)
    if not placed_candidates:
        return []

    def placement_cost(placed: list[PlacedDegree]) -> tuple[float, float, int]:
        notes = [note for _, note in placed]
        avg = sum(notes) / len(notes)
        center = (max(int(getattr(policy, "comfort_register_low")), closed_low) + int(getattr(policy, "comfort_register_high"))) / 2
        top = max(notes)
        top_center = (int(getattr(policy, "top_voice_low")) + int(getattr(policy, "top_voice_high"))) / 2
        span = max(notes) - min(notes)
        return (abs(avg - center) + 0.20 * abs(top - top_center), span, top)

    return min(placed_candidates, key=placement_cost)


def strict_closed_register_variants(placed: list[PlacedDegree], policy: Any) -> list[list[PlacedDegree]]:
    """Generate all strict closed circular pitch-class placements for one source.

    This is the candidate supply side for per-source nearest selection.  It is
    density-agnostic for the current closed work: 3-note and 4-note both first
    pass through the same closed-legality filter, then the selector chooses the
    nearest realization to the previous voicing.
    """

    metadata = dict(getattr(policy, "metadata", None) or {})
    low = effective_closed_register_low(policy)
    high = int(getattr(policy, "register_high"))
    span_cap = min(int(getattr(policy, "max_voicing_span")), int(metadata.get("strict_closed_max_span", 12)))
    pc_pairs = [(str(degree), int(note) % 12) for degree, note in placed]
    if len({pc for _, pc in pc_pairs}) != len(pc_pairs):
        return []

    ordered_pcs = sorted(pc_pairs, key=lambda item: item[1])
    layouts: list[list[tuple[str, int]]] = []
    count = len(ordered_pcs)
    for start in range(count):
        layout: list[tuple[str, int]] = []
        previous: int | None = None
        base_pc = ordered_pcs[start][1]
        for step in range(count):
            degree, pc = ordered_pcs[(start + step) % count]
            actual = int(pc)
            while actual < base_pc:
                actual += 12
            while previous is not None and actual <= previous:
                actual += 12
            layout.append((degree, actual))
            previous = actual
        span = layout[-1][1] - layout[0][1]
        if span <= span_cap:
            layouts.append(layout)

    variants: list[list[PlacedDegree]] = []
    for layout in layouts:
        for octave_base in range(24, 85, 12):
            placed_variant = [(degree, octave_base + offset) for degree, offset in layout]
            notes = [note for _, note in placed_variant]
            if not all(low <= note <= high for note in notes):
                continue
            if max(notes) - min(notes) > span_cap:
                continue
            variants.append(placed_variant)
    return variants


def compact_closed_parent_candidates_for_projection(
    root_pc: int,
    degrees: list[Degree],
    policy: Any,
) -> list[list[PlacedDegree]]:
    """Return compact closed parent candidates for named OPEN projections.

    DROP2 / DROP3 are projections of compact closed parents.  This helper keeps
    parent construction in the closed disposition layer so callers such as OPEN
    and SPREAD can reuse the same compact pitch-class parent contract instead of
    locally stacking extension offsets like 9/11/13 above the octave.
    """

    seed = place_compact_closed_seed_layout(root_pc, degrees, policy)
    if not seed:
        return []
    variants = strict_closed_register_variants(seed, policy) or [seed]
    out: list[list[PlacedDegree]] = []
    seen: set[tuple[tuple[str, int], ...]] = set()
    for variant in variants:
        normalized = tuple((str(degree), int(note)) for degree, note in sorted(variant, key=lambda item: item[1]))
        if normalized in seen:
            continue
        seen.add(normalized)
        out.append(list(normalized))
    return out


def _ordered_compact_offset(degree: str, fallback_stacked_semitone: int) -> int:
    try:
        return int(degree_to_semitone(degree, stacked=False))
    except Exception:
        return int(fallback_stacked_semitone)
