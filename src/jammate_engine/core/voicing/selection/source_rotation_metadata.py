from __future__ import annotations


def source_rotation_metadata(family, validity_notes: tuple[str, ...]) -> dict[str, str | int | bool]:
    """Return source/orientation debug metadata for one content recipe.

    These helpers used to live inside candidate generation.  Keeping them here
    makes candidate generation a coordinator and keeps source-family audit naming
    close to source-rotation semantics.
    """

    return {
        **rootless_ab_orientation_metadata(family, validity_notes),
        **basic_4note_metadata(family, validity_notes),
        **rooted_color_4note_metadata(family, validity_notes),
        **triad_4note_metadata(family, validity_notes),
    }


def _marker_value(validity_notes: tuple[str, ...], prefix: str, default: str = "unknown") -> str:
    return next((note.removeprefix(prefix) for note in validity_notes if note.startswith(prefix)), default)


def _rotation_side(inversion_index: int) -> str:
    return "A" if int(inversion_index) in {0, 1} else "B"


def _rotation_pair_index(inversion_index: int) -> int:
    return int(inversion_index) % 2


def _rotation_follow_inversion_index(inversion_index: int) -> int:
    return (int(inversion_index) + 2) % 4


def _generic_four_note_rotation_metadata(
    *,
    family_name: str,
    content_type: str,
    source_family: str,
    inversion_index: int,
    source_order: str,
    degree_order: str,
    source_role_order: str = "unknown",
    degree_role_order: str = "unknown",
    ab_side: str | None = None,
    ab_pair_index: int | None = None,
    follow_inversion_index: int | None = None,
    ab_eligible: bool = True,
    contract: str | None = None,
) -> dict[str, str | int | bool]:
    side = ab_side or _rotation_side(inversion_index)
    pair_index = _rotation_pair_index(inversion_index) if ab_pair_index is None else int(ab_pair_index)
    follow_index = _rotation_follow_inversion_index(inversion_index) if follow_inversion_index is None else int(follow_inversion_index)
    desired_side = "B" if side == "A" else "A" if side == "B" else "unknown"
    return {
        "four_note_rotation_family": family_name,
        "four_note_rotation_content_type": content_type,
        "four_note_rotation_source_family": source_family,
        "four_note_rotation_source_order": source_order,
        "four_note_rotation_degree_order": degree_order,
        "four_note_rotation_source_role_order": source_role_order,
        "four_note_rotation_degree_role_order": degree_role_order,
        "four_note_rotation_inversion_index": int(inversion_index),
        "four_note_rotation_ab_side": side,
        "four_note_rotation_ab_pair_index": int(pair_index),
        "four_note_rotation_follow_ab_side": desired_side,
        "four_note_rotation_follow_inversion_index": int(follow_index),
        "four_note_rotation_ab_eligible": bool(ab_eligible),
        "four_note_rotation_alignment_contract": contract
        or "Generic 4-note source rotations use A/B pair alignment in local ii-V and V-I method scopes; basic/rooted rotations map by inversion +2, while rootless A/B keeps the same canonical A/B inversion index.",
    }


def triad_4note_metadata(family, validity_notes: tuple[str, ...]) -> dict[str, str | int | bool]:
    family_value = getattr(family, "value", str(family))
    if family_value not in {"triad_basic", "add_sus_triad"} or "triad_4note_doubled_closed_rotation_family" not in validity_notes:
        return {}
    content_type = _marker_value(validity_notes, "triad_4note_content_type_")
    source_order = _marker_value(validity_notes, "triad_4note_source_order_")
    degree_order = _marker_value(validity_notes, "triad_4note_degree_order_")
    inversion_index = triad_4note_inversion_index(validity_notes)
    return {
        "triad_4note_source_family": "doubled_closed_rotation",
        "triad_4note_content_type": content_type,
        "triad_4note_inversion_index": inversion_index,
        "triad_4note_source_order": source_order,
        "triad_4note_degree_order": degree_order,
        "triad_4note_rotation_contract": "4-note triad/add/sus voicing uses source-order rotations such as 1351, 3513, 5135",
        **_generic_four_note_rotation_metadata(
            family_name="triad_4note",
            content_type=content_type,
            source_family="doubled_closed_rotation",
            inversion_index=inversion_index,
            source_order=source_order,
            degree_order=degree_order,
            ab_eligible=False,
            contract="Triad/add/sus doubled 4-note rotations expose generic source metadata for audit, but are not part of ii-V/V-I A/B hard alignment because they are not a four-inversion seventh/color source family.",
        ),
    }


def triad_4note_inversion_index(validity_notes: tuple[str, ...]) -> int:
    marker = next((note for note in validity_notes if note.startswith("triad_4note_inversion_index_")), None)
    if not marker:
        return 0
    try:
        return int(marker.removeprefix("triad_4note_inversion_index_"))
    except ValueError:
        return 0


def rootless_ab_orientation_metadata(family, validity_notes: tuple[str, ...]) -> dict[str, str | int | bool]:
    family_value = getattr(family, "value", str(family))
    if family_value not in {"rootless_A", "rootless_B"}:
        return {}
    content_type = _marker_value(validity_notes, "rootless_ab_content_type_")
    functional_source_type = _marker_value(validity_notes, "rootless_ab_functional_source_type_")
    orientation = "A" if family_value == "rootless_A" else "B"
    inversion_index = rootless_ab_inversion_index(validity_notes)
    source_order = _marker_value(validity_notes, "rootless_ab_source_order_")
    degree_order = _marker_value(validity_notes, "rootless_ab_degree_order_")
    source_role_order = _marker_value(validity_notes, "rootless_ab_source_role_order_")
    degree_role_order = _marker_value(validity_notes, "rootless_ab_degree_role_order_")
    pair_key = _marker_value(validity_notes, "rootless_ab_ab_pair_key_", f"{orientation}{inversion_index}")
    inversion_weight = rootless_ab_inversion_weight(inversion_index)
    source_family = functional_source_type if functional_source_type != "unknown" else content_type
    return {
        "rootless_ab_orientation_family": orientation,
        "rootless_ab_content_type": content_type,
        "rootless_ab_functional_source_type": source_family,
        "rootless_ab_inversion_index": inversion_index,
        "rootless_ab_source_order": source_order,
        "rootless_ab_degree_order": degree_order,
        "rootless_ab_source_role_order": source_role_order,
        "rootless_ab_degree_role_order": degree_role_order,
        "rootless_ab_functional_source_contract": "source names are functional roles; core harmony resolves accidentals and scale spelling",
        "rootless_ab_ab_pair_key": pair_key,
        "rootless_ab_inversion_weight": inversion_weight,
        "rootless_ab_inversion_weight_ratio": "8:2 preferred-source rotations vs secondary rotations",
        "rootless_ab_preferred_source_rotation": inversion_weight >= 8,
        "rootless_ab_orientation_contract": "A/B orientation is separate from content type; each A/B family is derived from canonical source rotations",
        "rootless_ab_ab_structure_contract": "ii-V or V-I prefers AB with same content type and inversion index; ii-V-I becomes ABA or BAB",
        **_generic_four_note_rotation_metadata(
            family_name="rootless_ab",
            content_type=content_type,
            source_family=source_family,
            inversion_index=inversion_index,
            source_order=source_order,
            degree_order=degree_order,
            source_role_order=source_role_order,
            degree_role_order=degree_role_order,
            ab_side=orientation,
            ab_pair_index=inversion_index,
            follow_inversion_index=inversion_index,
            ab_eligible=True,
            contract="Rootless A/B is a specialized generic 4-note rotation family: local ii-V or V-I flips A/B while preserving content type and canonical rootless inversion index.",
        ),
    }


def basic_4note_metadata(family, validity_notes: tuple[str, ...]) -> dict[str, str | int | bool]:
    family_value = getattr(family, "value", str(family))
    if family_value != "seventh_chord_basic" or not ({"basic_4note_functional_source_family", "basic_4note_1357_source_family"} & set(validity_notes)):
        return {}
    content_type = _marker_value(validity_notes, "basic_4note_content_type_")
    functional_content_type = _marker_value(validity_notes, "basic_4note_functional_content_type_")
    inversion_index = basic_4note_inversion_index(validity_notes)
    source_order = _marker_value(validity_notes, "basic_4note_source_order_")
    degree_order = _marker_value(validity_notes, "basic_4note_degree_order_")
    source_role_order = _marker_value(validity_notes, "basic_4note_source_role_order_")
    degree_role_order = _marker_value(validity_notes, "basic_4note_degree_role_order_")
    rotation_weight = basic_4note_rotation_weight(inversion_index)
    legacy_alias = content_type
    source_family = source_role_order if source_role_order != "unknown" else functional_content_type.removeprefix("root_")
    return {
        "basic_4note_source_family": source_family,
        "basic_4note_legacy_source_family_alias": legacy_alias,
        "basic_4note_content_type": content_type,
        "basic_4note_functional_content_type": functional_content_type,
        "basic_4note_inversion_index": inversion_index,
        "basic_4note_source_order": source_order,
        "basic_4note_degree_order": degree_order,
        "basic_4note_source_role_order": source_role_order,
        "basic_4note_degree_role_order": degree_role_order,
        "basic_4note_rotation_weight": rotation_weight,
        "basic_4note_rotation_weight_ratio": "8:2 preferred-source rotations vs secondary rotations",
        "basic_4note_preferred_source_rotation": rotation_weight >= 8,
        "basic_4note_source_contract": "root-third-fifth-seventh is conservative chord-symbol material; core harmony resolves concrete accidentals",
        "basic_4note_functional_source_contract": "source names are functional roles; core harmony resolves accidentals and scale spelling",
        **_generic_four_note_rotation_metadata(
            family_name="basic_4note",
            content_type=functional_content_type if functional_content_type != "unknown" else content_type,
            source_family=source_family,
            inversion_index=inversion_index,
            source_order=source_order,
            degree_order=degree_order,
            source_role_order=source_role_order,
            degree_role_order=degree_role_order,
            ab_eligible=True,
            contract="Basic rooted 4-note rotations align by inversion +2 in local ii-V/V-I method scopes: 1357->5713, 3571->7135, 5713->1357, 7135->3571.",
        ),
    }


def rooted_color_4note_metadata(family, validity_notes: tuple[str, ...]) -> dict[str, str | int | bool]:
    family_value = getattr(family, "value", str(family))
    if family_value != "rooted_color" or "rooted_color_4note_functional_source_family" not in validity_notes:
        return {}
    content_type = _marker_value(validity_notes, "rooted_color_4note_content_type_")
    functional_content_type = _marker_value(validity_notes, "rooted_color_4note_functional_content_type_")
    inversion_index = rooted_color_4note_inversion_index(validity_notes)
    source_order = _marker_value(validity_notes, "rooted_color_4note_source_order_")
    degree_order = _marker_value(validity_notes, "rooted_color_4note_degree_order_")
    source_role_order = _marker_value(validity_notes, "rooted_color_4note_source_role_order_")
    degree_role_order = _marker_value(validity_notes, "rooted_color_4note_degree_role_order_")
    source_family = source_role_order if source_role_order != "unknown" else functional_content_type
    return {
        "rooted_color_4note_source_family": source_family,
        "rooted_color_4note_legacy_source_family_alias": content_type,
        "rooted_color_4note_content_type": content_type,
        "rooted_color_4note_functional_content_type": functional_content_type,
        "rooted_color_4note_inversion_index": inversion_index,
        "rooted_color_4note_source_order": source_order,
        "rooted_color_4note_degree_order": degree_order,
        "rooted_color_4note_source_role_order": source_role_order,
        "rooted_color_4note_degree_role_order": degree_role_order,
        "rooted_color_4note_source_contract": "rooted color sources are named as functional roles; core harmony resolves concrete color/accidental spelling",
        **_generic_four_note_rotation_metadata(
            family_name="rooted_color_4note",
            content_type=functional_content_type if functional_content_type != "unknown" else content_type,
            source_family=source_family,
            inversion_index=inversion_index,
            source_order=source_order,
            degree_order=degree_order,
            source_role_order=source_role_order,
            degree_role_order=degree_role_order,
            ab_eligible=True,
            contract="Rooted-color 4-note rotations reuse the generic 4-note A/B alignment model; local ii-V/V-I follows the same inversion +2 pair mapping as conservative rooted 4-note sources.",
        ),
    }


def rooted_color_4note_inversion_index(validity_notes: tuple[str, ...]) -> int:
    marker = next((note for note in validity_notes if note.startswith("rooted_color_4note_inversion_index_")), None)
    if not marker:
        return 0
    try:
        return int(marker.removeprefix("rooted_color_4note_inversion_index_"))
    except ValueError:
        return 0


def basic_4note_inversion_index(validity_notes: tuple[str, ...]) -> int:
    marker = next((note for note in validity_notes if note.startswith("basic_4note_inversion_index_")), None)
    if not marker:
        return 0
    try:
        return int(marker.removeprefix("basic_4note_inversion_index_"))
    except ValueError:
        return 0


def basic_4note_rotation_weight(inversion_index: int) -> int:
    return 8 if int(inversion_index) in {0, 2} else 2


def rootless_ab_inversion_index(validity_notes: tuple[str, ...]) -> int:
    marker = next((note for note in validity_notes if note.startswith("rootless_ab_inversion_index_")), None)
    if not marker:
        return 0
    try:
        return int(marker.removeprefix("rootless_ab_inversion_index_"))
    except ValueError:
        return 0


def rootless_ab_inversion_weight(inversion_index: int) -> int:
    """Return the v2_1_16 source-rotation prior for rootless A/B."""

    return 8 if int(inversion_index) in {0, 2} else 2
