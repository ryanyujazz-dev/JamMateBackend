from __future__ import annotations

from jammate_engine.core.harmony.chord_parser import ParsedChord
from jammate_engine.core.harmony.material import degree_to_semitone

from ..disposition.facade import place_degree_notes
from ..policy import ContentFamily, Disposition, VoicingPolicy
from .register_variants import effective_register_low_for_disposition

Degree = tuple[str, int]
PlacedDegree = tuple[str, int]


def place_content_recipe_for_projection(
    chord: ParsedChord,
    degrees: list[Degree],
    family,
    disposition: Disposition,
    policy: VoicingPolicy,
    validity_notes: tuple[str, ...] = (),
) -> list[PlacedDegree]:
    """Place one content recipe before disposition projection/register variants.

    Candidate generation should orchestrate content, disposition, and scoring; it
    should not own source-order placement details.  This module keeps the few
    source families that require order-preserving placement together so rootless
    A/B, conservative 4-note seventh sources, rooted-color 4-note sources, and
    doubled-triad rotations keep the same musical behavior while the generator
    stays focused on candidate assembly.
    """

    # Strict closed 3/4-note compact seed placement has moved to
    # core.voicing.disposition.closed via project_source_to_disposition().
    if "triad_4note_doubled_closed_rotation_family" in validity_notes and disposition in {Disposition.CLOSED, Disposition.OPEN}:
        placed = _place_basic_4note_ordered_stack(chord.root_pc, degrees, policy, disposition)
        # A density-4 doubled triad must remain a real 4-note source.  If a
        # specific rotation cannot fit the closed register guard, drop that
        # rotation rather than falling back to a 3-note triad and polluting the
        # density-4 audit/listening pool.
        return placed
    if family in {ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B}:
        placed = _place_rootless_ab_ordered_stack(chord.root_pc, degrees, policy, disposition)
        if placed:
            return placed
    if (
        family == ContentFamily.SEVENTH_BASIC
        and ("basic_4note_functional_source_family" in validity_notes or "basic_4note_1357_source_family" in validity_notes)
        and disposition in {Disposition.CLOSED, Disposition.OPEN}
    ):
        placed = _place_basic_4note_ordered_stack(chord.root_pc, degrees, policy, disposition)
        if placed:
            return placed
    if (
        family == ContentFamily.ROOTED_COLOR
        and "rooted_color_4note_functional_source_family" in validity_notes
        and disposition in {Disposition.CLOSED, Disposition.OPEN}
    ):
        placed = _place_basic_4note_ordered_stack(chord.root_pc, degrees, policy, disposition)
        if placed:
            return placed
    return place_degree_notes(
        chord.root_pc,
        degrees,
        effective_register_low_for_disposition(policy, disposition),
        policy.register_high,
        disposition=disposition,
        policy=policy,
    )


def _place_rootless_ab_ordered_stack(
    root_pc: int,
    degrees: list[Degree],
    policy: VoicingPolicy,
    disposition: Disposition = Disposition.CLOSED,
) -> list[PlacedDegree]:
    """Place 4-note rootless A/B by preserving the requested degree order.

    The ordinary pitch-class placer sorts notes by nearest pitch class.  That is
    fine for generic content, but it can turn an intended A/B shape such as
    3-5-7-9 or 7-9-3-5 into the wrong inversion.  Rootless A/B orientation is a
    musical contract, so here the stacked degree order is preserved first and
    register is solved by trying whole-octave placements.
    """

    if not degrees:
        return []
    ordered_offsets: list[tuple[str, int]] = []
    previous_offset: int | None = None
    for degree, semitone in degrees:
        offset = _rootless_ab_ordered_offset(str(degree), int(semitone))
        while previous_offset is not None and offset <= previous_offset:
            offset += 12
        ordered_offsets.append((str(degree), offset))
        previous_offset = offset

    candidates: list[list[PlacedDegree]] = []
    for root_octave in range(24, 85, 12):
        root_ref = root_octave + int(root_pc)
        placed = [(degree, root_ref + offset) for degree, offset in ordered_offsets]
        notes = [note for _, note in placed]
        low = effective_register_low_for_disposition(policy, disposition)
        if not all(low <= note <= policy.register_high for note in notes):
            continue
        if max(notes) - min(notes) > policy.max_voicing_span:
            continue
        candidates.append(placed)
    if not candidates:
        return []

    def placement_cost(placed: list[PlacedDegree]) -> tuple[float, int]:
        notes = [note for _, note in placed]
        avg = sum(notes) / len(notes)
        center = (policy.comfort_register_low + policy.comfort_register_high) / 2
        top = max(notes)
        top_center = (policy.top_voice_low + policy.top_voice_high) / 2
        return (abs(avg - center) + 0.25 * abs(top - top_center), top)

    return min(candidates, key=placement_cost)


def _place_basic_4note_ordered_stack(
    root_pc: int,
    degrees: list[Degree],
    policy: VoicingPolicy,
    disposition: Disposition = Disposition.CLOSED,
) -> list[PlacedDegree]:
    """Place 4-note source rotations while preserving source order."""

    if not degrees:
        return []
    ordered_offsets: list[tuple[str, int]] = []
    previous_offset: int | None = None
    for degree, semitone in degrees:
        offset = _ordered_compact_offset(str(degree), int(semitone))
        while previous_offset is not None and offset <= previous_offset:
            offset += 12
        ordered_offsets.append((str(degree), offset))
        previous_offset = offset

    candidates: list[list[PlacedDegree]] = []
    for root_octave in range(24, 85, 12):
        root_ref = root_octave + int(root_pc)
        placed = [(degree, root_ref + offset) for degree, offset in ordered_offsets]
        notes = [note for _, note in placed]
        low = effective_register_low_for_disposition(policy, disposition)
        if not all(low <= note <= policy.register_high for note in notes):
            continue
        if max(notes) - min(notes) > policy.max_voicing_span:
            continue
        candidates.append(placed)
    if not candidates:
        return []

    def placement_cost(placed: list[PlacedDegree]) -> tuple[float, int]:
        notes = [note for _, note in placed]
        avg = sum(notes) / len(notes)
        center = (policy.comfort_register_low + policy.comfort_register_high) / 2
        top = max(notes)
        top_center = (policy.top_voice_low + policy.top_voice_high) / 2
        low = min(notes)
        # Basic 1357 contains the root, so avoid letting the whole voicing sit too
        # low/thick when bass is already present.  This is soft placement only.
        low_penalty = max(0, policy.right_hand_low - low) * 0.12
        return (abs(avg - center) + 0.22 * abs(top - top_center) + low_penalty, top)

    return min(candidates, key=placement_cost)


def _rootless_ab_ordered_offset(degree: str, fallback_stacked_semitone: int) -> int:
    # A/B orientation uses voicing-order semantics: 13 behaves like the sixth
    # inside the chord stack when it is placed before the 7th (3-13-7-9), while
    # 9 still floats above the guide-tone shell when it appears after 7.
    if degree == "13":
        return 9
    return _ordered_compact_offset(degree, fallback_stacked_semitone)


def _ordered_compact_offset(degree: str, fallback_stacked_semitone: int) -> int:
    try:
        return int(degree_to_semitone(degree, stacked=False))
    except Exception:
        return int(fallback_stacked_semitone)
