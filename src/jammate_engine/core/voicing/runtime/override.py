from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from ..policy import ColorPolicyMode, ContentFamily, Disposition, RootSupportPolicy, VoicingPolicy


VOICING_OVERRIDE_CONTRACT_VERSION = "v2_1_43"


VOICING_OVERRIDE_PRESETS: dict[str, dict[str, Any]] = {
    "2_note_shell": {
        "root_support": RootSupportPolicy.ROOTLESS_ALLOWED.value,
        "allowed_content": [ContentFamily.SHELL.value],
        "preferred_content": ContentFamily.SHELL.value,
        "content_family_weights": {},
        "preferred_disposition": Disposition.CLOSED.value,
        "allowed_dispositions": [Disposition.CLOSED.value, Disposition.OPEN.value],
        "preferred_density": 2,
        "min_density": 2,
        "max_density": 2,
        "register_low": 55,
        "register_high": 72,
        "right_hand_low": 55,
        "right_hand_high": 72,
        "top_voice_low": 58,
        "top_voice_high": 72,
        "comfort_register_low": 55,
        "comfort_register_high": 68,
        "max_voicing_span": 16,
        "max_top_voice_leap": 12,
        "selector_temperature": 0.0,
        "selection_pool_size": 1,
    },
    "shell_plus_5": {
        "root_support": RootSupportPolicy.ROOTLESS_ALLOWED.value,
        "allowed_content": [ContentFamily.SHELL_PLUS_5.value],
        "preferred_content": ContentFamily.SHELL_PLUS_5.value,
        "content_family_weights": {ContentFamily.SHELL_PLUS_5.value: 0.6},
        "preferred_disposition": Disposition.CLOSED.value,
        "allowed_dispositions": [Disposition.CLOSED.value],
        "preferred_density": 3,
        "min_density": 3,
        "max_density": 3,
        "register_low": 51,
        "register_high": 74,
        "right_hand_low": 51,
        "right_hand_high": 74,
        "top_voice_low": 56,
        "top_voice_high": 74,
        "comfort_register_low": 53,
        "comfort_register_high": 69,
        "max_voicing_span": 16,
        "max_top_voice_leap": 12,
        "selector_temperature": 0.0,
        "selection_pool_size": 1,
        "metadata": {
            "tuning_target": "shell_plus_1or5",
            "strict_closed_compact_pitch_class_layout": True,
            "strict_closed_max_span": 12,
            "closed_voicing_lowest_note_floor": 53,
            "closed_3note_per_source_minimum_motion": True,
            "closed_3note_closed_legality_then_nearest_motion": True,
            "legacy_alias": "shell_plus_5",
            "voicing_class": "3-note rootless guide-tone shell plus 5, with very-low-weight optional root/1 variant",
            "standalone_review_target": True,
            "rooted_foundation_component": False,
            "root_component_role": "occasional low-weight cluster accent, not rooted foundation",
        },
    },
    "shell_plus_specified_color": {
        "root_support": RootSupportPolicy.ROOTLESS_ALLOWED.value,
        "allowed_content": [ContentFamily.SHELL_PLUS_COLOR.value],
        "preferred_content": ContentFamily.SHELL_PLUS_COLOR.value,
        "content_family_weights": {ContentFamily.SHELL_PLUS_COLOR.value: 0.65},
        "harmonic_expansion_enabled": False,
        "color_policy_mode": ColorPolicyMode.CHORD_SYMBOL_ONLY.value,
        "preferred_disposition": Disposition.CLOSED.value,
        "allowed_dispositions": [Disposition.CLOSED.value],
        "preferred_density": 3,
        "min_density": 3,
        "max_density": 3,
        "register_low": 51,
        "register_high": 74,
        "right_hand_low": 51,
        "right_hand_high": 74,
        "top_voice_low": 56,
        "top_voice_high": 74,
        "comfort_register_low": 53,
        "comfort_register_high": 69,
        "max_voicing_span": 16,
        "max_top_voice_leap": 12,
        "selector_temperature": 0.0,
        "selection_pool_size": 1,
        "metadata": {
            "tuning_target": "shell_plus_specified_color",
            "strict_closed_compact_pitch_class_layout": True,
            "strict_closed_max_span": 12,
            "closed_voicing_lowest_note_floor": 53,
            "closed_3note_per_source_minimum_motion": True,
            "closed_3note_closed_legality_then_nearest_motion": True,
            "voicing_class": "3-note rootless guide-tone shell plus explicitly allowed color",
            "standalone_review_target": True,
            "rooted_foundation_component": False,
            "default_color_policy": "chord_symbol_only",
        },
    },

    "basic_4note_1357": {
        "root_support": RootSupportPolicy.ROOT_OPTIONAL.value,
        "allowed_content": [ContentFamily.SEVENTH_BASIC.value],
        "preferred_content": ContentFamily.SEVENTH_BASIC.value,
        "content_family_weights": {ContentFamily.SEVENTH_BASIC.value: 0.45},
        "harmonic_expansion_enabled": False,
        "color_policy_mode": ColorPolicyMode.CHORD_SYMBOL_ONLY.value,
        "preferred_disposition": Disposition.CLOSED.value,
        "allowed_dispositions": [Disposition.CLOSED.value, Disposition.OPEN.value],
        "preferred_density": 4,
        "min_density": 4,
        "max_density": 4,
        "register_low": 50,
        "register_high": 74,
        "right_hand_low": 54,
        "right_hand_high": 74,
        "top_voice_low": 59,
        "top_voice_high": 74,
        "comfort_register_low": 56,
        "comfort_register_high": 68,
        "max_voicing_span": 18,
        "max_top_voice_leap": 12,
        "selector_temperature": 0.20,
        "selection_pool_size": 8,
        "metadata": {
            "tuning_target": "basic_4note_root_third_fifth_seventh",
            "voicing_class": "4-note conservative rooted seventh functional-degree source-rotation family",
            "standalone_review_target": True,
            "rooted_foundation_component": True,
            "harmonic_expansion_gate": "not required; root-third-fifth-seventh is chord-symbol material for ordinary seventh chords",
            "source_rotation_weight_rule": "prefer root-third-fifth-seventh and fifth-seventh-root-third source-like rotations over secondary rotations with an 8:2 prior",
            "color_boundary_rule": "rootless third-fifth-seventh-ninth / third-thirteenth-seventh-ninth still requires explicit chord-symbol color or expansion intent",
            "primary_disposition_family": "compact_vertical_source",
            "canonical_source_contract": "VoicingTexturePlan -> ContentRecipe -> CanonicalClosedSource -> compact vertical source rotations -> VoiceLeadingScorer",
        },
    },

    "rootless_ab_safe": {
        "root_support": RootSupportPolicy.ROOTLESS_ALLOWED.value,
        "allowed_content": [ContentFamily.ROOTLESS_A.value, ContentFamily.ROOTLESS_B.value],
        "preferred_content": ContentFamily.ROOTLESS_A.value,
        "content_family_weights": {ContentFamily.ROOTLESS_A.value: 0.28, ContentFamily.ROOTLESS_B.value: 0.20},
        "harmonic_expansion_enabled": True,
        "color_policy_mode": ColorPolicyMode.STYLE_SAFE_EXTENSIONS.value,
        "preferred_disposition": Disposition.CLOSED.value,
        "allowed_dispositions": [Disposition.CLOSED.value, Disposition.OPEN.value],
        "preferred_density": 4,
        "min_density": 4,
        "max_density": 4,
        "register_low": 52,
        "register_high": 74,
        "right_hand_low": 52,
        "right_hand_high": 74,
        "top_voice_low": 60,
        "top_voice_high": 74,
        "comfort_register_low": 58,
        "comfort_register_high": 68,
        "max_voicing_span": 18,
        "max_top_voice_leap": 12,
        "selector_temperature": 0.20,
        "selection_pool_size": 8,
        "metadata": {
            "tuning_target": "rootless_ab_safe",
            "voicing_class": "4-note rootless A/B safe color-comping family",
            "standalone_review_target": True,
            "rooted_foundation_component": False,
            "gate": "uses global HarmonicExpansionPolicy / VoicingColorPolicy; explicit chord-symbol color is allowed without unnotated expansion",
            "explicit_color_rule": "when chord-symbol color is the only color source, use only that specified color and do not add extra unnotated tensions",
            "orientation_rule": "A/B orientation is separate from content type; with_5 uses canonical rotations from third-fifth-seventh-ninth / seventh-ninth-third-fifth and with_13 uses rotations from third-thirteenth-seventh-ninth / seventh-ninth-third-thirteenth; same ii-V or V-I motion prefers the same content type and A/B inversion index",
            "source_rotation_weight_rule": "prefer third-fifth-seventh-ninth and seventh-ninth-third-fifth source-like rotations over the other two rotations with an 8:2 prior; with_13 mirrors this with third-thirteenth-seventh-ninth and seventh-ninth-third-thirteenth",
            "register_center_rule": "v2_1_17 keeps compact rootless A/B in a controlled middle-register band: hard register 52-74, soft lowest-note floor 54, top voice 60-74, comfort average 58-68, compact span <=18",
            "rootless_ab_average_pitch_target_low": 59,
            "rootless_ab_average_pitch_target_high": 66,
            "rootless_ab_top_voice_soft_high": 72,
            "rootless_ab_top_voice_hard_high": 74,
            "rootless_ab_lowest_note_floor": 54,
            "primary_disposition_family": "compact_rootless",
            "canonical_source_contract": "VoicingTexturePlan -> ContentRecipe -> CanonicalClosedSource -> compact-rootless disposition/orientation -> VoiceLeadingScorer",
        },
    },
    "shell_plus_expanded_color": {
        "root_support": RootSupportPolicy.ROOTLESS_ALLOWED.value,
        "allowed_content": [ContentFamily.SHELL_PLUS_COLOR.value],
        "preferred_content": ContentFamily.SHELL_PLUS_COLOR.value,
        "content_family_weights": {ContentFamily.SHELL_PLUS_COLOR.value: 0.65},
        "harmonic_expansion_enabled": True,
        "color_policy_mode": ColorPolicyMode.STYLE_SAFE_EXTENSIONS.value,
        "preferred_disposition": Disposition.CLOSED.value,
        "allowed_dispositions": [Disposition.CLOSED.value],
        "preferred_density": 3,
        "min_density": 3,
        "max_density": 3,
        "register_low": 51,
        "register_high": 74,
        "right_hand_low": 51,
        "right_hand_high": 74,
        "top_voice_low": 56,
        "top_voice_high": 74,
        "comfort_register_low": 53,
        "comfort_register_high": 69,
        "max_voicing_span": 16,
        "max_top_voice_leap": 12,
        "selector_temperature": 0.34,
        "selection_pool_size": 20,
        "metadata": {
            "tuning_target": "shell_plus_expanded_color",
            "strict_closed_compact_pitch_class_layout": True,
            "strict_closed_max_span": 12,
            "closed_voicing_lowest_note_floor": 53,
            "closed_3note_per_source_minimum_motion": True,
            "closed_3note_closed_legality_then_nearest_motion": True,
            "voicing_class": "3-note functional closed source with expansion-enabled color pool plus reduced internal 5/root fallback; no color-note octave-shift spacing rule",
            "standalone_review_target": True,
            "rooted_foundation_component": False,
            "default_color_policy": "style_safe_extensions",
            "root_component_role": "very low-weight cluster accent, not rooted foundation",
            "internal_5_component_role": "stable non-expanded fallback inside expanded color mode",
        },
    },
}



# Product-facing alias: a 2-note shell is specifically the guide-tone shell
# family in the current tuning workflow. Keep the original preset id stable,
# while allowing requests to name the musical concept explicitly.
VOICING_OVERRIDE_PRESETS["2_note_guide_tone_shell"] = dict(VOICING_OVERRIDE_PRESETS["2_note_shell"])
VOICING_OVERRIDE_PRESETS["3_note_shell_5"] = dict(VOICING_OVERRIDE_PRESETS["shell_plus_5"])
VOICING_OVERRIDE_PRESETS["shell_plus_1or5"] = dict(VOICING_OVERRIDE_PRESETS["shell_plus_5"])
VOICING_OVERRIDE_PRESETS["3_note_shell_1or5"] = dict(VOICING_OVERRIDE_PRESETS["shell_plus_5"])
VOICING_OVERRIDE_PRESETS["3_note_guide_shell_with_5"] = dict(VOICING_OVERRIDE_PRESETS["shell_plus_5"])
VOICING_OVERRIDE_PRESETS["shell_plus_color"] = dict(VOICING_OVERRIDE_PRESETS["shell_plus_specified_color"])
VOICING_OVERRIDE_PRESETS["shell_plus_one_color_note"] = dict(VOICING_OVERRIDE_PRESETS["shell_plus_specified_color"])
VOICING_OVERRIDE_PRESETS["3_note_shell_color"] = dict(VOICING_OVERRIDE_PRESETS["shell_plus_specified_color"])
VOICING_OVERRIDE_PRESETS["3_note_guide_shell_with_color"] = dict(VOICING_OVERRIDE_PRESETS["shell_plus_specified_color"])

VOICING_OVERRIDE_PRESETS["4_note_basic_1357"] = dict(VOICING_OVERRIDE_PRESETS["basic_4note_1357"])
VOICING_OVERRIDE_PRESETS["basic_1357"] = dict(VOICING_OVERRIDE_PRESETS["basic_4note_1357"])
VOICING_OVERRIDE_PRESETS["1357"] = dict(VOICING_OVERRIDE_PRESETS["basic_4note_1357"])
VOICING_OVERRIDE_PRESETS["seventh_basic_1357"] = dict(VOICING_OVERRIDE_PRESETS["basic_4note_1357"])

VOICING_OVERRIDE_PRESETS["basic_4note_root_third_fifth_seventh"] = dict(VOICING_OVERRIDE_PRESETS["basic_4note_1357"])
VOICING_OVERRIDE_PRESETS["root_third_fifth_seventh"] = dict(VOICING_OVERRIDE_PRESETS["basic_4note_1357"])
VOICING_OVERRIDE_PRESETS["rootless_third_fifth_seventh_ninth"] = dict(VOICING_OVERRIDE_PRESETS["rootless_ab_safe"])
VOICING_OVERRIDE_PRESETS["4_note_rootless_ab_safe"] = dict(VOICING_OVERRIDE_PRESETS["rootless_ab_safe"])
VOICING_OVERRIDE_PRESETS["rootless_ab"] = dict(VOICING_OVERRIDE_PRESETS["rootless_ab_safe"])
VOICING_OVERRIDE_PRESETS["4_note_rootless_ab"] = dict(VOICING_OVERRIDE_PRESETS["rootless_ab_safe"])
VOICING_OVERRIDE_PRESETS["shell_plus_expansion_color"] = dict(VOICING_OVERRIDE_PRESETS["shell_plus_expanded_color"])
VOICING_OVERRIDE_PRESETS["3_note_shell_expanded_color"] = dict(VOICING_OVERRIDE_PRESETS["shell_plus_expanded_color"])


VOICING_OVERRIDE_PRESETS["3_note_closed_functional"] = dict(VOICING_OVERRIDE_PRESETS["shell_plus_specified_color"])
VOICING_OVERRIDE_PRESETS["3_note_functional_closed"] = dict(VOICING_OVERRIDE_PRESETS["shell_plus_specified_color"])
VOICING_OVERRIDE_PRESETS["3_note_third_seventh_fifth"] = dict(VOICING_OVERRIDE_PRESETS["shell_plus_5"])
VOICING_OVERRIDE_PRESETS["third_seventh_fifth"] = dict(VOICING_OVERRIDE_PRESETS["shell_plus_5"])
VOICING_OVERRIDE_PRESETS["3_note_third_seventh_ninth"] = dict(VOICING_OVERRIDE_PRESETS["shell_plus_specified_color"])
VOICING_OVERRIDE_PRESETS["third_seventh_ninth"] = dict(VOICING_OVERRIDE_PRESETS["shell_plus_specified_color"])

VOICING_OVERRIDE_POLICY_KEYS = frozenset(VoicingPolicy().to_debug_dict().keys()) - {"metadata"}


def voicing_override_enabled(override: Mapping[str, Any] | None) -> bool:
    data = dict(override or {})
    if not data:
        return False
    return bool(data.get("enabled", True))


def voicing_isolation_enabled(override: Mapping[str, Any] | None) -> bool:
    data = dict(override or {})
    if not voicing_override_enabled(data):
        return False
    mode = str(data.get("pattern_mode", data.get("mode", ""))).strip().lower()
    return mode in {"region_start_anchor_only", "region_start_only", "anchor_only", "voicing_isolation"}


def isolation_mutes_bass(override: Mapping[str, Any] | None) -> bool:
    data = dict(override or {})
    if not voicing_isolation_enabled(data):
        return False
    return bool(data.get("mute_bass", False))


def isolation_disables_anticipation(override: Mapping[str, Any] | None) -> bool:
    data = dict(override or {})
    if not voicing_isolation_enabled(data):
        return False
    return bool(data.get("disable_anticipation", True))


def isolation_expression_hint(override: Mapping[str, Any] | None) -> str:
    data = dict(override or {})
    return str(data.get("expression_hint", "sustain"))


def build_voicing_override_policy(
    base_policy: VoicingPolicy | Mapping[str, Any] | None,
    override: Mapping[str, Any] | None,
    *,
    style_name: str,
) -> VoicingPolicy:
    """Apply a user/runtime voicing override on top of a style policy.

    The override is intentionally global and style-independent. Styles still own
    rhythm patterns, expression policies, timing feel, and arrangement behavior;
    this helper only replaces the vertical voicing-policy axes when the request
    explicitly asks for it.
    """

    if isinstance(base_policy, VoicingPolicy):
        policy = base_policy
    else:
        policy = VoicingPolicy.from_legacy_dict(dict(base_policy or {}))
    data = dict(override or {})
    if not voicing_override_enabled(data):
        return policy

    preset_id = str(data.get("preset", data.get("target", ""))).strip()
    override_policy: dict[str, Any] = {}
    if preset_id:
        if preset_id not in VOICING_OVERRIDE_PRESETS:
            raise ValueError(f"Unknown voicing override preset: {preset_id}")
        override_policy.update(VOICING_OVERRIDE_PRESETS[preset_id])

    # Allow direct policy keys at top level for simple API calls, and a nested
    # ``policy`` object for callers that prefer a clean schema.
    override_policy.update({key: value for key, value in data.items() if key in VOICING_OVERRIDE_POLICY_KEYS})
    override_policy.update(dict(data.get("policy", {}) or {}))

    merged_metadata = {
        **dict(policy.metadata or {}),
        # Direct top-level override metadata is part of the public tuning
        # surface.  Earlier passes only merged preset/nested-policy metadata,
        # which meant listening-only flags such as strict closed compactness
        # could be present in the request object but absent from the effective
        # VoicingPolicy.
        **dict(data.get("metadata", {}) or {}),
        **dict(override_policy.get("metadata", {}) or {}),
        "voicing_override_enabled": True,
        "voicing_override_contract_version": VOICING_OVERRIDE_CONTRACT_VERSION,
        "voicing_override_style": style_name,
        "voicing_override_preset": preset_id or None,
        "voicing_override_pattern_mode": data.get("pattern_mode", data.get("mode")),
        "normal_style_default": False,
    }
    override_policy["metadata"] = merged_metadata
    return policy.merge(override_policy)


def voicing_override_debug(override: Mapping[str, Any] | None, effective_policy: VoicingPolicy) -> dict[str, Any]:
    data = dict(override or {})
    return {
        "enabled": voicing_override_enabled(data),
        "preset": data.get("preset", data.get("target")),
        "pattern_mode": data.get("pattern_mode", data.get("mode")),
        "isolation_enabled": voicing_isolation_enabled(data),
        "mute_bass": isolation_mutes_bass(data),
        "disable_anticipation": isolation_disables_anticipation(data),
        "expression_hint": isolation_expression_hint(data),
        "effective_policy": effective_policy.to_debug_dict(),
    }
