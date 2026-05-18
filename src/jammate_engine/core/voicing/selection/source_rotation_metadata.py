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


def triad_4note_metadata(family, validity_notes: tuple[str, ...]) -> dict[str, str | int | bool]:
    family_value = getattr(family, "value", str(family))
    if family_value not in {"triad_basic", "add_sus_triad"} or "triad_4note_doubled_closed_rotation_family" not in validity_notes:
        return {}
    content_type = next((note.removeprefix("triad_4note_content_type_") for note in validity_notes if note.startswith("triad_4note_content_type_")), "unknown")
    source_order = next((note.removeprefix("triad_4note_source_order_") for note in validity_notes if note.startswith("triad_4note_source_order_")), "unknown")
    degree_order = next((note.removeprefix("triad_4note_degree_order_") for note in validity_notes if note.startswith("triad_4note_degree_order_")), "unknown")
    inversion_index = triad_4note_inversion_index(validity_notes)
    return {
        "triad_4note_source_family": "doubled_closed_rotation",
        "triad_4note_content_type": content_type,
        "triad_4note_inversion_index": inversion_index,
        "triad_4note_source_order": source_order,
        "triad_4note_degree_order": degree_order,
        "triad_4note_rotation_contract": "4-note triad/add/sus voicing uses source-order rotations such as 1351, 3513, 5135",
    }


def triad_4note_inversion_index(validity_notes: tuple[str, ...]) -> int:
    marker = next((note for note in validity_notes if note.startswith("triad_4note_inversion_index_")), None)
    if not marker:
        return 0
    try:
        return int(marker.removeprefix("triad_4note_inversion_index_"))
    except ValueError:
        return 0


def rootless_ab_orientation_metadata(family, validity_notes: tuple[str, ...]) -> dict[str, str | int]:
    family_value = getattr(family, "value", str(family))
    if family_value not in {"rootless_A", "rootless_B"}:
        return {}
    content_type = next((note.removeprefix("rootless_ab_content_type_") for note in validity_notes if note.startswith("rootless_ab_content_type_")), "unknown")
    functional_source_type = next((note.removeprefix("rootless_ab_functional_source_type_") for note in validity_notes if note.startswith("rootless_ab_functional_source_type_")), "unknown")
    orientation = "A" if family_value == "rootless_A" else "B"
    inversion_index = rootless_ab_inversion_index(validity_notes)
    source_order = next((note.removeprefix("rootless_ab_source_order_") for note in validity_notes if note.startswith("rootless_ab_source_order_")), "unknown")
    degree_order = next((note.removeprefix("rootless_ab_degree_order_") for note in validity_notes if note.startswith("rootless_ab_degree_order_")), "unknown")
    source_role_order = next((note.removeprefix("rootless_ab_source_role_order_") for note in validity_notes if note.startswith("rootless_ab_source_role_order_")), "unknown")
    degree_role_order = next((note.removeprefix("rootless_ab_degree_role_order_") for note in validity_notes if note.startswith("rootless_ab_degree_role_order_")), "unknown")
    pair_key = next((note.removeprefix("rootless_ab_ab_pair_key_") for note in validity_notes if note.startswith("rootless_ab_ab_pair_key_")), f"{orientation}{inversion_index}")
    inversion_weight = rootless_ab_inversion_weight(inversion_index)
    return {
        "rootless_ab_orientation_family": orientation,
        "rootless_ab_content_type": content_type,
        "rootless_ab_functional_source_type": functional_source_type if functional_source_type != "unknown" else content_type,
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
    }


def basic_4note_metadata(family, validity_notes: tuple[str, ...]) -> dict[str, str | int | bool]:
    family_value = getattr(family, "value", str(family))
    if family_value != "seventh_chord_basic" or not ({"basic_4note_functional_source_family", "basic_4note_1357_source_family"} & set(validity_notes)):
        return {}
    content_type = next((note.removeprefix("basic_4note_content_type_") for note in validity_notes if note.startswith("basic_4note_content_type_")), "unknown")
    functional_content_type = next((note.removeprefix("basic_4note_functional_content_type_") for note in validity_notes if note.startswith("basic_4note_functional_content_type_")), "unknown")
    inversion_index = basic_4note_inversion_index(validity_notes)
    source_order = next((note.removeprefix("basic_4note_source_order_") for note in validity_notes if note.startswith("basic_4note_source_order_")), "unknown")
    degree_order = next((note.removeprefix("basic_4note_degree_order_") for note in validity_notes if note.startswith("basic_4note_degree_order_")), "unknown")
    source_role_order = next((note.removeprefix("basic_4note_source_role_order_") for note in validity_notes if note.startswith("basic_4note_source_role_order_")), "unknown")
    degree_role_order = next((note.removeprefix("basic_4note_degree_role_order_") for note in validity_notes if note.startswith("basic_4note_degree_role_order_")), "unknown")
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
    }


def rooted_color_4note_metadata(family, validity_notes: tuple[str, ...]) -> dict[str, str | int | bool]:
    family_value = getattr(family, "value", str(family))
    if family_value != "rooted_color" or "rooted_color_4note_functional_source_family" not in validity_notes:
        return {}
    content_type = next((note.removeprefix("rooted_color_4note_content_type_") for note in validity_notes if note.startswith("rooted_color_4note_content_type_")), "unknown")
    functional_content_type = next((note.removeprefix("rooted_color_4note_functional_content_type_") for note in validity_notes if note.startswith("rooted_color_4note_functional_content_type_")), "unknown")
    inversion_index = rooted_color_4note_inversion_index(validity_notes)
    source_order = next((note.removeprefix("rooted_color_4note_source_order_") for note in validity_notes if note.startswith("rooted_color_4note_source_order_")), "unknown")
    degree_order = next((note.removeprefix("rooted_color_4note_degree_order_") for note in validity_notes if note.startswith("rooted_color_4note_degree_order_")), "unknown")
    source_role_order = next((note.removeprefix("rooted_color_4note_source_role_order_") for note in validity_notes if note.startswith("rooted_color_4note_source_role_order_")), "unknown")
    degree_role_order = next((note.removeprefix("rooted_color_4note_degree_role_order_") for note in validity_notes if note.startswith("rooted_color_4note_degree_role_order_")), "unknown")
    return {
        "rooted_color_4note_source_family": source_role_order,
        "rooted_color_4note_legacy_source_family_alias": content_type,
        "rooted_color_4note_content_type": content_type,
        "rooted_color_4note_functional_content_type": functional_content_type,
        "rooted_color_4note_inversion_index": inversion_index,
        "rooted_color_4note_source_order": source_order,
        "rooted_color_4note_degree_order": degree_order,
        "rooted_color_4note_source_role_order": source_role_order,
        "rooted_color_4note_degree_role_order": degree_role_order,
        "rooted_color_4note_source_contract": "rooted color sources are named as functional roles; core harmony resolves concrete color/accidental spelling",
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
