from __future__ import annotations

from typing import Any

from jammate_engine.core.gestures import GestureKind, GestureRequest, rolled_onset
from jammate_engine.core.gestures.gesture import normalize_gesture_kind

STYLE_ID = "jazz_ballad"
GESTURE_POLICY_VERSION = "v2_5_4"

ALLOWED_GESTURE_KINDS = (
    GestureKind.SIMULTANEOUS_ONSET.value,
    GestureKind.INNER_MOVEMENT.value,
    GestureKind.ROLLED_ONSET.value,
)

ALLOWED_PROJECTION_REFS = (
    "all_voices",
    "lowest",
    "inner",
    "inner_1",
    "inner_2",
    "top",
    "support_group",
    "foundation_group",
    "projection_group",
    "color_group",
    "motion_group",
)

# Gesture metadata may describe abstract musical/projection intent only.  It may
# not smuggle V1-style voicing texture decisions, final expression values, or
# concrete MIDI data into the gesture layer.
ALLOWED_METADATA_KEYS = (
    "gesture_family",
    "phrase_function",
    "ballad_role",
    "motion_shape",
    "movement_level",
    "target_voice_class",
    "attack_scope",
    "held_voice_policy",
    "rearticulation_scope",
    "roll_shape",
    "boundary",
)

FORBIDDEN_METADATA_KEYS = (
    "midi_note",
    "midi_notes",
    "note",
    "notes",
    "pitch",
    "pitches",
    "frequency",
    "frequencies",
    "velocity",
    "duration",
    "duration_beats",
    "pedal",
    "voicing",
    "voicing_texture",
    "voicing_texture_id",
    "compatible_textures",
    "texture_weights",
    "rootless_texture",
    "source_degrees",
    "midi_repair",
)


def get_gesture_policy() -> dict:
    """Pitchless gesture policy for Jazz Ballad comping.

    v2_5_4 retains the Ballad style gate for ``inner_movement`` and
    ``rolled_onset`` as V2-native gesture contracts.  This policy still does not
    choose pitches, voicings, durations, velocities, pedal values, or V1 texture
    bundles.
    """

    return {
        "style_id": STYLE_ID,
        "version": GESTURE_POLICY_VERSION,
        "default_onset_mode": GestureKind.SIMULTANEOUS_ONSET.value,
        "allowed_gesture_kinds": ALLOWED_GESTURE_KINDS,
        "allowed_projection_refs": ALLOWED_PROJECTION_REFS,
        "allowed_metadata_keys": ALLOWED_METADATA_KEYS,
        "forbidden_metadata_keys": FORBIDDEN_METADATA_KEYS,
        "boundary": "gesture_policy_is_pitchless_projection_and_motion_intent_only",
        "v2_5_2_contract": {
            "inner_movement_owner": "core.gestures + jazz_ballad.gesture_policy",
            "pattern_boundary": "patterns_may_request_gesture_slots_but_must_not_choose_notes",
            "voicing_boundary": "voicing_remains_the_only_vertical_pitch_selector",
            "expression_boundary": "duration_velocity_pedal_remain_expression_policy_responsibilities",
            "v1_absorption_rule": "learn_musical_behavior_not_v1_code_or_texture_bundles",
        },
        "v2_5_4_contract": {
            "phrase_intent_boundary": "phrase_candidates_may_request_approved_gestures_only",
            "voicing_boundary": "voicing_remains_the_only_vertical_pitch_selector",
            "expression_boundary": "duration_velocity_pedal_remain_expression_policy_responsibilities",
            "no_partial_reattack_yet": True,
            "realization_boundary": "held_foundation_partial_reattack_is_deferred_to_v2_5_4",
        },
    }


def inner_movement_request(
    *,
    motion_shape: str = "inner_voice_breath",
    target_voice_class: str = "inner",
    attack_scope: str = "inner_motion",
    held_voice_policy: str = "hold_foundation_common_tones",
    rearticulation_scope: str = "inner_or_color_group_only",
    phrase_function: str = "ballad_inner_movement",
) -> GestureRequest:
    """Create a V2-native Ballad inner-movement request.

    The request is intentionally pitchless. It names an abstract motion shape and
    projection target only; concrete notes must come from the selected VoicingPlan
    and later realization.
    """

    request = GestureRequest(
        kind=GestureKind.INNER_MOVEMENT,
        voice_order=(_normalize_projection_ref(target_voice_class),),
        metadata={
            "gesture_family": "ballad_inner_movement",
            "phrase_function": phrase_function,
            "motion_shape": motion_shape,
            "target_voice_class": _normalize_projection_ref(target_voice_class),
            "attack_scope": attack_scope,
            "held_voice_policy": held_voice_policy,
            "rearticulation_scope": rearticulation_scope,
            "boundary": "pitchless_gesture_request_no_voicing_or_expression_values",
        },
    )
    return validate_gesture_request(request)


def rolled_cadence_request(
    *,
    voice_order: tuple[str, ...] = ("foundation_group", "projection_group"),
    onset_offsets_beats: tuple[float, ...] = (),
    roll_shape: str = "low_to_high_cadence_roll",
    phrase_function: str = "ballad_rolled_cadence_release",
) -> GestureRequest:
    """Create a Ballad rolled-onset request without selecting notes.

    This is a contract helper for future phrase candidates.  It remains a
    projection gesture and does not imply a specific voicing texture or cadence
    color.
    """

    request = rolled_onset(
        voice_order=tuple(_normalize_projection_ref(ref) for ref in voice_order),
        onset_offsets_beats=onset_offsets_beats,
        metadata={
            "gesture_family": "ballad_rolled_onset",
            "phrase_function": phrase_function,
            "roll_shape": roll_shape,
            "attack_scope": "rolled_projection_over_selected_voicing",
            "boundary": "pitchless_gesture_request_no_voicing_or_expression_values",
        },
    )
    return validate_gesture_request(request)


def validate_gesture_request(request: GestureRequest) -> GestureRequest:
    """Validate that a request conforms to the Jazz Ballad gesture contract."""

    kind = normalize_gesture_kind(request.kind)
    if kind.value not in ALLOWED_GESTURE_KINDS:
        raise ValueError(f"Jazz Ballad gesture kind is not style-approved: {kind.value}")

    for raw_ref in request.projection_refs:
        ref = _normalize_projection_ref(raw_ref)
        if ref not in ALLOWED_PROJECTION_REFS:
            raise ValueError(f"Jazz Ballad gesture projection ref is not style-approved: {raw_ref!r}")

    forbidden_paths = _find_keys(request.metadata, FORBIDDEN_METADATA_KEYS)
    if forbidden_paths:
        raise ValueError(
            "Jazz Ballad gesture metadata must remain pitchless/expressionless/voicingless; "
            f"forbidden keys: {', '.join(forbidden_paths)}"
        )

    unknown_paths = _find_unknown_metadata_keys(request.metadata, ALLOWED_METADATA_KEYS)
    if unknown_paths:
        raise ValueError(
            "Jazz Ballad gesture metadata must use V2-native abstract keys only; "
            f"unknown keys: {', '.join(unknown_paths)}"
        )
    return request


def _normalize_projection_ref(value: str) -> str:
    text = str(value).strip().lower()
    for separator in (":", "."):
        if separator in text:
            prefix, payload = text.split(separator, 1)
            if prefix in {"voice_ref", "voice", "group_ref", "group"}:
                return payload.strip()
    return text


def _find_keys(value: Any, forbidden: tuple[str, ...], path: str = "metadata") -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in forbidden:
                found.append(child_path)
            found.extend(_find_keys(child, forbidden, child_path))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            found.extend(_find_keys(child, forbidden, f"{path}[{index}]"))
    return tuple(found)


def _find_unknown_metadata_keys(value: Any, allowed: tuple[str, ...], path: str = "metadata") -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text not in allowed:
                found.append(child_path)
            found.extend(_find_unknown_metadata_keys(child, allowed, child_path))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            found.extend(_find_unknown_metadata_keys(child, allowed, f"{path}[{index}]"))
    return tuple(found)
