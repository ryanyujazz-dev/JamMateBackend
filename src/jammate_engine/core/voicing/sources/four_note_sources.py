from __future__ import annotations

from jammate_engine.core.harmony.material import degree_to_semitone


def role_order_token(source: tuple[str, ...]) -> str:
    """Return a stable metadata token for functional source roles."""

    return "_".join(str(role).replace("-", "_") for role in source)


def degree_order_token(source: tuple[str, ...]) -> str:
    """Return a stable metadata token for resolved degree order."""

    return "_".join(str(degree).replace("#", "sharp").replace("b", "flat") for degree in source)


def degree_pair(degree: str) -> tuple[str, int]:
    """Convert a resolved degree token into the common voicing degree tuple."""

    return (degree, degree_to_semitone(degree, stacked=True))


def rotations(source: tuple[str, ...]) -> list[tuple[str, ...]]:
    """Return canonical source rotations used by compact 4-note families."""

    return [tuple(source[index:] + source[:index]) for index in range(len(source))]


def functional_source_rotation_options(
    *,
    source: tuple[str, ...],
    source_roles: tuple[str, ...],
    note_prefix: str,
    family_notes: tuple[str, ...],
) -> list[tuple[list[tuple[str, int]], tuple[str, ...]]]:
    """Create canonical closed-position rotations with functional metadata."""

    out: list[tuple[list[tuple[str, int]], tuple[str, ...]]] = []
    role_rotations = rotations(source_roles)
    for inversion_index, rotated in enumerate(rotations(source)):
        rotated_roles = role_rotations[inversion_index]
        variant_notes = (
            *family_notes,
            f"{note_prefix}_inversion_index_{inversion_index}",
            f"{note_prefix}_source_role_order_{role_order_token(source_roles)}",
            f"{note_prefix}_degree_role_order_{role_order_token(rotated_roles)}",
            f"{note_prefix}_source_order_{degree_order_token(source)}",
            f"{note_prefix}_degree_order_{degree_order_token(rotated)}",
            f"{note_prefix}_from_canonical_inversion_family",
        )
        out.append(([degree_pair(degree) for degree in _dedupe(list(rotated))], variant_notes))
    return out


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out
