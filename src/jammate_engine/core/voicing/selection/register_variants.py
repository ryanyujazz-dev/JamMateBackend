from __future__ import annotations

from dataclasses import replace

from ..disposition.closed import (
    closed_compactness_metadata,
    effective_closed_register_low,
    strict_closed_compact_layout_enabled,
    strict_closed_register_variants,
)
from ..policy import ContentFamily, Disposition, VoicingPolicy

PlacedDegree = tuple[str, int]


def policy_for_disposition_guard(policy: VoicingPolicy, disposition: Disposition) -> VoicingPolicy:
    low = effective_register_low_for_disposition(policy, disposition)
    if low == policy.register_low:
        return policy
    return replace(policy, register_low=low)


def effective_register_low_for_disposition(policy: VoicingPolicy, disposition: Disposition) -> int:
    if disposition != Disposition.CLOSED:
        return int(policy.register_low)
    return effective_closed_register_low(policy)


def closed_voicing_compactness_metadata(notes: list[int], policy: VoicingPolicy, disposition: Disposition) -> dict[str, object]:
    if disposition != Disposition.CLOSED:
        return {}
    return closed_compactness_metadata(notes, policy)


def register_variants(placed: list[PlacedDegree], policy: VoicingPolicy, disposition: Disposition = Disposition.OPEN) -> list[list[PlacedDegree]]:
    """Return octave-neighbor variants while preserving degree-note pairing.

    This is register/variant supply, not candidate orchestration.  Keeping it
    out of candidate generation makes the generation loop easier to audit while
    preserving strict-closed and shell-variant behavior.
    """

    if not placed:
        return []
    base = sorted(((str(degree), int(note)) for degree, note in placed), key=lambda item: item[1])
    low = effective_register_low_for_disposition(policy, disposition)
    high = policy.register_high
    raw_variants: list[list[PlacedDegree]] = []

    strict_closed = disposition == Disposition.CLOSED and strict_closed_compact_layout_enabled(policy) and len(base) in {3, 4}
    if strict_closed:
        strict_variants = strict_closed_register_variants(base, policy)
        if strict_variants:
            raw_variants.extend(strict_variants)
        else:
            # Doubled closed triads intentionally repeat one pitch class
            # (1351 / 3513 / 5135).  They are already a legal closed seed from
            # the ordered source placer, so supply octave-neighbor whole-shape
            # variants instead of rejecting them as duplicate pitch classes.
            for shift in (0, -12, 12):
                shifted = [(degree, note + shift) for degree, note in base]
                if all(low <= note <= high for _, note in shifted):
                    span = max(note for _, note in shifted) - min(note for _, note in shifted)
                    if span <= min(int(policy.max_voicing_span), int(dict(policy.metadata or {}).get("strict_closed_max_span", 12))):
                        raw_variants.append(shifted)
    else:
        # Preserve the old whole-shape behavior for all non-strict densities.
        for shift in (0, -12, 12):
            shifted = [(degree, note + shift) for degree, note in base]
            if all(low <= note <= high for _, note in shifted):
                raw_variants.append(shifted)

    # Add mixed-octave inversions for two-note guide tones and legacy/non-strict
    # 3-note shell families.  Strict 3-note closed mode deliberately disables the
    # old color-note octave-shift spacing rule: closed legality is handled first,
    # and per-source nearest motion decides the concrete closed layout.
    if len(base) == 2:
        shifts = (-12, 0, 12)
        for first_shift in shifts:
            for second_shift in shifts:
                shifted = [
                    (base[0][0], base[0][1] + first_shift),
                    (base[1][0], base[1][1] + second_shift),
                ]
                if not all(low <= note <= high for _, note in shifted):
                    continue
                ordered = sorted(shifted, key=lambda item: item[1])
                span = ordered[-1][1] - ordered[0][1]
                if span > max(policy.max_voicing_span, 12):
                    continue
                raw_variants.append(ordered)

    if len(base) == 3 and (not strict_closed) and _should_generate_three_note_shell_variants(policy):
        shifts = (-12, 0, 12)
        for first_shift in shifts:
            for second_shift in shifts:
                for third_shift in shifts:
                    shifted = [
                        (base[0][0], base[0][1] + first_shift),
                        (base[1][0], base[1][1] + second_shift),
                        (base[2][0], base[2][1] + third_shift),
                    ]
                    if not all(low <= note <= high for _, note in shifted):
                        continue
                    ordered = sorted(shifted, key=lambda item: item[1])
                    span = ordered[-1][1] - ordered[0][1]
                    if span > max(policy.max_voicing_span, 12):
                        continue
                    raw_variants.append(ordered)

    out: list[list[PlacedDegree]] = []
    seen: set[tuple[PlacedDegree, ...]] = set()
    for variant in raw_variants:
        ordered = sorted(variant, key=lambda item: item[1])
        key = tuple((degree, int(note)) for degree, note in ordered)
        if key in seen:
            continue
        seen.add(key)
        out.append(list(key))
    return out or [base]


def _should_generate_three_note_shell_variants(policy: VoicingPolicy) -> bool:
    families = set(policy.allowed_content or ())
    if policy.preferred_content is not None:
        families.add(policy.preferred_content)
    tuned = {ContentFamily.SHELL_PLUS_COLOR, ContentFamily.SHELL_PLUS_5}
    return bool(families.intersection(tuned))
