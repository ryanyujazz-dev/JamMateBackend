from __future__ import annotations

from dataclasses import dataclass, replace
import re
from typing import Any

from jammate_engine.core.harmony.chord_parser import parse_chord
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing import ColorPolicyMode, Disposition, VoicingPolicy


HARMONIC_REALIZER_POLICY_CONTEXT_ADAPTER_VERSION = "v2_6_23"
MEDIUM_SWING_EXISTING_VOICING_CAPABILITY_USAGE_POLICY_VERSION = "v2_6_77"
MEDIUM_SWING_EXISTING_VOICING_CAPABILITY_LOW_REGISTER_CLARITY_GUARD_VERSION = "v2_6_78"
MEDIUM_SWING_BASS_PIANO_INTERACTION_GUARD_VERSION = "v2_6_82"

HARMONIC_REALIZER_POLICY_CONTEXT_ADAPTER_OWNED_RESPONSIBILITIES = (
    "event_scoped_voicing_policy_metadata_bridge",
    "harmonic_region_context_attachment",
    "texture_scope_context_attachment",
    "ballad_spread_grouping_mix_context_attachment",
    "spread_lower_upper_ratio_context_attachment",
    "no_source_construction_no_projection_no_selector",
)

HARMONIC_REALIZER_POLICY_CONTEXT_ADAPTER_FORBIDDEN_RESPONSIBILITIES = (
    "does_not_construct_degree_sources",
    "does_not_choose_content_family",
    "does_not_decide_color_permission",
    "does_not_project_closed_open_or_spread_voicings",
    "does_not_score_or_select_voicing_candidates",
    "does_not_realize_midi_notes_or_expression",
)


@dataclass(frozen=True)
class HarmonicRealizerPolicyContextAdapterProfile:
    version: str = HARMONIC_REALIZER_POLICY_CONTEXT_ADAPTER_VERSION
    implementation_owner: str = "jammate_engine.realization.voicing_policy_context_adapter"
    consumed_by: str = "jammate_engine.realization.realizer_voicing_request_orchestration"
    output_boundary: str = "VoicingPolicy with event-scoped metadata only"
    owned_responsibilities: tuple[str, ...] = HARMONIC_REALIZER_POLICY_CONTEXT_ADAPTER_OWNED_RESPONSIBILITIES
    forbidden_responsibilities: tuple[str, ...] = HARMONIC_REALIZER_POLICY_CONTEXT_ADAPTER_FORBIDDEN_RESPONSIBILITIES

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "harmonic_realizer_policy_context_adapter_version": self.version,
            "implementation_owner": self.implementation_owner,
            "consumed_by": self.consumed_by,
            "output_boundary": self.output_boundary,
            "owned_responsibilities": list(self.owned_responsibilities),
            "forbidden_responsibilities": list(self.forbidden_responsibilities),
            "source_only": False,
            "policy_context_only": True,
            "no_projection_or_selector": True,
        }


def harmonic_realizer_policy_context_adapter_profile() -> HarmonicRealizerPolicyContextAdapterProfile:
    return HarmonicRealizerPolicyContextAdapterProfile()


def policy_with_event_voicing_context(policy: VoicingPolicy, event: PatternEvent) -> VoicingPolicy:
    """Attach event-scoped voicing context before core voicing resolution.

    This adapter is the only place where realization-layer event metadata is
    translated into ``VoicingPolicy.metadata``. It deliberately does not choose
    sources, decide color permission, project voicings, rank candidates, apply
    expression, or write MIDI.
    """

    return _policy_with_event_texture_scope(policy, event)


def _policy_with_event_texture_scope(policy: VoicingPolicy, event: PatternEvent) -> VoicingPolicy:
    """Attach phrase/section/chorus texture-scope metadata for one voicing request.

    Styles may opt in through policy metadata.  The helper does not choose notes
    or methods; it only resolves the runtime scope identity consumed by
    VoicingTextureState so family-level texture is no longer an anonymous
    style-global flag.
    """

    policy = _policy_with_event_harmonic_context(policy, event)
    policy = _policy_with_medium_swing_existing_voicing_capability_usage_policy(policy, event)
    policy = _policy_with_ballad_spread_grouping_mix_policy(policy, event)
    policy = _policy_with_spread_upper_3note_expansion_ratio(policy, event)
    policy = _policy_with_spread_upper_4note_expansion_ratio(policy, event)
    policy = _policy_with_spread_lower_2note_rooted_equal_cycle(policy, event)
    metadata = dict(policy.metadata or {})
    if not _coerce_bool(metadata.get("voicing_texture_scope_runtime_enabled"), default=False):
        return policy

    event_metadata = dict(getattr(event, "metadata", {}) or {})
    scope_type = str(metadata.get("voicing_texture_runtime_scope_type") or metadata.get("texture_scope_type") or "section")
    scope_id = _texture_scope_id(event_metadata, scope_type)
    contrast_metadata = _texture_contrast_plan_metadata(metadata, event_metadata, scope_type=scope_type, scope_id=scope_id)
    scoped_metadata = {
        **metadata,
        **contrast_metadata,
        "texture_scope_id": scope_id,
        "scope_type": scope_type,
        "voicing_texture_scope_runtime_contract": "v2_2_38_medium_swing_phrase_section_texture_scope_lock",
        "voicing_texture_scope_runtime_enabled": True,
        "voicing_texture_runtime_scope_type": scope_type,
        "voicing_texture_runtime_scope_id": scope_id,
        "voicing_texture_scope_region_context": {
            "section_id": event_metadata.get("region_section_id"),
            "section_label": event_metadata.get("region_section_label"),
            "phrase": event_metadata.get("region_phrase"),
            "section_role": event_metadata.get("region_section_role"),
            "chorus_index": event_metadata.get("region_chorus_index"),
            "performance_bar_index": event_metadata.get("region_performance_bar_index"),
            "is_first_bar_of_section": bool(event_metadata.get("region_is_first_bar_of_section")),
            "is_last_bar_of_section": bool(event_metadata.get("region_is_last_bar_of_section")),
        },
    }
    return replace(policy, metadata=scoped_metadata)



def _policy_with_event_harmonic_context(policy: VoicingPolicy, event: PatternEvent) -> VoicingPolicy:
    """Attach chord-region harmonic context metadata for source-level policy gates.

    v2_2_85 uses this lightweight event-scoped bridge so altered-dominant source
    gates can distinguish resolving V7, secondary dominant, static/blues
    dominant, backdoor dominant, and LLM-selected regions without moving
    progression analysis into the source planner.
    """

    metadata = dict(policy.metadata or {})
    event_metadata = dict(getattr(event, "metadata", {}) or {})
    harmonic_metadata = {
        "altered_dominant_functional_scope_context_version": "v2_2_85",
        "chord_symbol": getattr(event, "chord_symbol", ""),
        "previous_chord_symbol": event_metadata.get("previous_chord_symbol"),
        "next_chord_symbol": event_metadata.get("next_chord_symbol"),
        "home_key": event_metadata.get("home_key"),
        "key": event_metadata.get("home_key"),
        "region_id": getattr(event, "region_id", ""),
        "section_id": event_metadata.get("region_section_id"),
        "section_label": event_metadata.get("region_section_label"),
        "phrase": event_metadata.get("region_phrase"),
        "section_role": event_metadata.get("region_section_role"),
        "chorus_index": event_metadata.get("region_chorus_index"),
        "bar_index": event_metadata.get("region_bar_index"),
        "source_bar_index": event_metadata.get("region_source_bar_index"),
        "written_bar_index": event_metadata.get("region_written_bar_index"),
        "performance_bar_index": event_metadata.get("region_performance_bar_index"),
    }
    return replace(policy, metadata={**metadata, **harmonic_metadata})


def _policy_with_medium_swing_existing_voicing_capability_usage_policy(policy: VoicingPolicy, event: PatternEvent) -> VoicingPolicy:
    """Request existing 5/6-note SPREAD capability for sparse Medium Swing support scenes.

    v2_6_77 is intentionally a style/intention selection layer, not a voicing
    implementation change.  It only rewrites event-scoped policy metadata so
    the existing grouped-SPREAD runtime candidate pool can be used for a small
    set of Medium Swing support/climax contexts.  It does not construct degree
    sources, project SPREAD voicings, rank candidates, apply expression, or
    write MIDI.
    """

    metadata = dict(policy.metadata or {})
    if str(metadata.get("style") or "") != "medium_swing":
        return policy

    nested = metadata.get("medium_swing_existing_voicing_capability_usage_policy") or {}
    if not isinstance(nested, dict):
        nested = {"enabled": nested}
    if not _coerce_bool(nested.get("enabled"), default=False):
        return policy

    event_metadata = dict(getattr(event, "metadata", {}) or {})
    if getattr(event, "track", "") != "piano" or getattr(event, "role", "") != "harmonic":
        return _medium_swing_existing_voicing_capability_policy_debug(
            policy,
            applied=False,
            scene="non_piano_harmonic",
            reason="event_is_not_piano_harmonic_comping",
        )

    scene = _medium_swing_existing_voicing_capability_scene(event_metadata)
    if scene == "ordinary_open_drop":
        return _medium_swing_existing_voicing_capability_policy_debug(
            policy,
            applied=False,
            scene=scene,
            reason="ordinary_medium_swing_keeps_existing_open_drop_policy",
        )

    if scene == "final_ending_climax":
        selected_contract_id = "spread_3plus3_contract"
        compatible_contract_ids = ("spread_2plus4_contract", "spread_3plus3_contract")
        preferred_density = 6
        policy_reason = "final_chorus_ending_requests_existing_6note_grouped_spread_support"
    elif scene == "final_chorus_section_tail_support":
        selected_contract_id = "spread_2plus3_contract"
        compatible_contract_ids = ("spread_2plus3_contract",)
        preferred_density = 5
        policy_reason = "final_chorus_section_tail_requests_existing_5note_grouped_spread_support"
    else:
        return _medium_swing_existing_voicing_capability_policy_debug(
            policy,
            applied=False,
            scene=scene,
            reason="scene_not_authorized_for_medium_swing_thick_support",
        )

    scoped = {
        **metadata,
        "medium_swing_existing_voicing_capability_usage_policy_version": MEDIUM_SWING_EXISTING_VOICING_CAPABILITY_USAGE_POLICY_VERSION,
        "medium_swing_existing_voicing_capability_usage_policy_applied": True,
        "medium_swing_existing_voicing_capability_usage_scene": scene,
        "medium_swing_existing_voicing_capability_usage_reason": policy_reason,
        "medium_swing_existing_voicing_capability_boundary": "style_event_scoped_policy_requests_existing_grouped_spread_runtime_candidates_only",
        "medium_swing_existing_voicing_capability_no_core_voicing_change": True,
        "medium_swing_existing_voicing_capability_selected_contract_id": selected_contract_id,
        "medium_swing_existing_voicing_capability_compatible_contract_ids": list(compatible_contract_ids),
        "medium_swing_existing_voicing_capability_low_register_clarity_guard_version": MEDIUM_SWING_EXISTING_VOICING_CAPABILITY_LOW_REGISTER_CLARITY_GUARD_VERSION,
        "medium_swing_existing_voicing_capability_low_register_clarity_guard_enabled": True,
        "medium_swing_existing_voicing_capability_low_register_clarity_guard_contract": "optional Medium Swing 5/6-note grouped SPREAD support must not place more than one piano note below C3 in bass-present/full-band usage; this is an event-scoped metadata guard over existing spread candidates, not a core voicing implementation change",
        "medium_swing_existing_voicing_capability_low_register_clarity_threshold": int(nested.get("spread_low_register_density_threshold", 48) or 48),
        "medium_swing_existing_voicing_capability_low_register_clarity_max_notes_below": int(nested.get("spread_low_register_density_max_notes_below", 1) or 1),
        "medium_swing_bass_piano_interaction_guard_version": str(nested.get("bass_piano_interaction_guard_version") or MEDIUM_SWING_BASS_PIANO_INTERACTION_GUARD_VERSION),
        "medium_swing_bass_piano_interaction_guard_enabled": _coerce_bool(nested.get("bass_piano_interaction_guard_enabled"), default=False),
        "medium_swing_bass_piano_interaction_guard_contract": str(nested.get("bass_piano_interaction_guard_contract") or "optional Medium Swing 5/6-note grouped SPREAD may request C3+ foundation registers in bass-present/full-band demos so piano does not duplicate the bass walking foundation; this is event-scoped style metadata only"),
        "ballad_spread_grouping_mix_selected_contract_id": selected_contract_id,
        "spread_grouping_mix_selected_contract_id": selected_contract_id,
        "primary_family": "spread",
        "allowed_families": ["spread"],
        "voicing_texture_primary_family": "spread",
        "voicing_texture_allowed_families": ["spread"],
        "spread_selector_enabled": True,
        "spread_groupwise_voice_leading_runtime_enabled": True,
        "spread_runtime_adapter_emit_all_candidates": True,
        "spread_emit_all_candidates_for_groupwise_selection": True,
        "spread_lower_foundation_quality_gate_enabled": True,
        "spread_grouping_mix_candidate_pool": {
            "version": MEDIUM_SWING_EXISTING_VOICING_CAPABILITY_USAGE_POLICY_VERSION,
            "style": "medium_swing",
            "use_compatible_contracts": True,
            "selected_contract_id": selected_contract_id,
            "compatible_contract_ids": list(compatible_contract_ids),
            "selection_boundary": "existing_grouped_spread_runtime_candidate_pool",
        },
        "spread_runtime_adapter": {
            **dict(metadata.get("spread_runtime_adapter") or {}),
            "version": MEDIUM_SWING_EXISTING_VOICING_CAPABILITY_USAGE_POLICY_VERSION,
            "adapter_conversion_allowed": True,
            "request_source": "medium_swing_existing_voicing_capability_usage_policy",
        },
        "spread_rooted_bass_anchor_enabled": True,
        "spread_root_bass_anchor_low": int(nested.get("bass_piano_interaction_spread_root_bass_anchor_low", nested.get("spread_root_bass_anchor_low", 40)) or 40),
        "spread_root_bass_anchor_high": int(nested.get("bass_piano_interaction_spread_root_bass_anchor_high", nested.get("spread_root_bass_anchor_high", 52)) or 52),
        "spread_root_bass_anchor_target": int(nested.get("bass_piano_interaction_spread_root_bass_anchor_target", nested.get("spread_root_bass_anchor_target", 47)) or 47),
        "spread_whole_register_low": int(nested.get("bass_piano_interaction_register_floor", nested.get("spread_whole_register_low", 40)) or 40),
        "spread_whole_register_high": int(nested.get("spread_whole_register_high", 76) or 76),
        "spread_upper_low": int(nested.get("spread_upper_low", 50) or 50),
        "spread_upper_high": int(nested.get("spread_upper_high", 73) or 73),
        "spread_upper_target_low": int(nested.get("spread_upper_target_low", 55) or 55),
        "spread_min_group_gap": int(nested.get("spread_min_group_gap", 1) or 1),
        "spread_max_group_gap": int(nested.get("spread_max_group_gap", 7) or 7),
        "spread_low_register_density_guard_enabled": True,
        "spread_low_register_density_threshold": int(nested.get("spread_low_register_density_threshold", 48) or 48),
        "spread_low_register_density_max_notes_below": int(nested.get("spread_low_register_density_max_notes_below", 1) or 1),
        "spread_lower_2note_low": int(nested.get("bass_piano_interaction_spread_root_bass_anchor_low", nested.get("spread_lower_2note_low", 40)) or 40),
        "spread_lower_2note_high": int(nested.get("bass_piano_interaction_spread_root_bass_anchor_high", nested.get("spread_lower_2note_high", 58)) or 58),
        "spread_lower_2note_target_low": int(nested.get("bass_piano_interaction_register_floor", nested.get("spread_lower_2note_target_low", 40)) or 40),
        "spread_upper_4note_emit_all_parent_projections": True,
        "spread_upper_4note_allow_octave_shift_candidates": True,
    }
    return replace(
        policy,
        preferred_disposition=Disposition.SPREAD,
        allowed_dispositions=(Disposition.SPREAD, Disposition.OPEN),
        preferred_density=preferred_density,
        min_density=min(4, preferred_density),
        max_density=max(6, int(policy.max_density)),
        register_low=min(int(policy.register_low), 40),
        register_high=min(int(policy.register_high), 74),
        top_voice_high=min(int(policy.top_voice_high), 72),
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
        metadata=scoped,
    )


def _medium_swing_existing_voicing_capability_scene(event_metadata: dict[str, Any]) -> str:
    total_choruses = _safe_int(event_metadata.get("region_total_choruses"), default=0)
    chorus_index = _safe_int(event_metadata.get("region_chorus_index"), default=0)
    final_chorus = total_choruses <= 0 or chorus_index >= max(0, total_choruses - 1)
    last_bar_of_chorus = _coerce_bool(event_metadata.get("region_is_last_bar_of_chorus"), default=False)
    last_bar_of_section = _coerce_bool(event_metadata.get("region_is_last_bar_of_section"), default=False)
    if final_chorus and last_bar_of_chorus:
        return "final_ending_climax"
    if final_chorus and last_bar_of_section:
        return "final_chorus_section_tail_support"
    return "ordinary_open_drop"


def _medium_swing_existing_voicing_capability_policy_debug(
    policy: VoicingPolicy,
    *,
    applied: bool,
    scene: str,
    reason: str,
) -> VoicingPolicy:
    metadata = dict(policy.metadata or {})
    debug = {
        **metadata,
        "medium_swing_existing_voicing_capability_usage_policy_version": MEDIUM_SWING_EXISTING_VOICING_CAPABILITY_USAGE_POLICY_VERSION,
        "medium_swing_existing_voicing_capability_usage_policy_applied": bool(applied),
        "medium_swing_existing_voicing_capability_usage_scene": scene,
        "medium_swing_existing_voicing_capability_usage_reason": reason,
        "medium_swing_existing_voicing_capability_boundary": "style_event_scoped_policy_requests_existing_grouped_spread_runtime_candidates_only",
        "medium_swing_existing_voicing_capability_no_core_voicing_change": True,
    }
    return replace(policy, metadata=debug)


def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _policy_with_ballad_spread_grouping_mix_policy(policy: VoicingPolicy, event: PatternEvent) -> VoicingPolicy:
    """Apply the current Ballad SPREAD grouping mix policy per event.

    This helper only writes event-scoped metadata for the grouped-SPREAD runtime
    candidate pool. It does not choose notes, project voicings, apply
    expression, or write MIDI.
    """

    metadata = dict(policy.metadata or {})
    nested = metadata.get("ballad_spread_grouping_mix_policy") or metadata.get("ballad_spread_grouping_mix") or {}
    enabled = _coerce_bool(nested.get("enabled") if isinstance(nested, dict) else nested, default=False)
    if not enabled:
        return policy

    try:
        from jammate_engine.core.voicing.disposition import resolve_ballad_spread_grouping_mix_policy
    except Exception:
        return policy

    event_metadata = dict(getattr(event, "metadata", {}) or {})
    context = {
        **event_metadata,
        "region_id": getattr(event, "region_id", ""),
        "local_beat": getattr(event, "local_beat", 0.0),
        "chord_symbol": getattr(event, "chord_symbol", ""),
    }
    decision = resolve_ballad_spread_grouping_mix_policy(policy, event_context=context, explicit_enable=True)
    if not decision.selected_contract_id:
        scoped = {
            **metadata,
            "ballad_spread_grouping_mix_policy_decision": decision.to_debug_dict(),
        }
        return replace(policy, metadata=scoped)

    selected = str(decision.selected_contract_id)
    compatible_contract_ids = [str(item) for item in decision.compatible_contract_ids if str(item)]
    if selected in {"spread_2plus3_contract", "spread_1plus4_contract"} and "spread_2plus4_contract" not in compatible_contract_ids:
        compatible_contract_ids = [*compatible_contract_ids, "spread_2plus4_contract"]
    if selected == "spread_1plus4_contract" and "spread_3plus3_contract" not in compatible_contract_ids:
        compatible_contract_ids = [*compatible_contract_ids, "spread_3plus3_contract"]
    if selected == "spread_2plus3_contract" and _spread_extra_six_note_support_slot(event_metadata) and "spread_3plus3_contract" not in compatible_contract_ids:
        compatible_contract_ids = [*compatible_contract_ids, "spread_3plus3_contract"]
    if selected == "spread_2plus3_contract" and _spread_extra_six_note_support_slot(event_metadata):
        selected = "spread_2plus4_contract"
    if selected and selected not in compatible_contract_ids:
        compatible_contract_ids = [selected, *compatible_contract_ids]
    scoped = {
        **metadata,
        "ballad_spread_grouping_mix_policy_version": "v2_6_22",
        "ballad_spread_grouping_mix_policy_decision": decision.to_debug_dict(),
        "ballad_spread_grouping_mix_selected_contract_id": selected,
        "ballad_spread_grouping_mix_selected_grouping": decision.selected_grouping,
        "primary_family": "spread",
        "allowed_families": ["spread"],
        "spread_selector_enabled": True,
        "spread_grouping_mix_candidate_pool": {
            "version": "v2_6_22",
            "use_compatible_contracts": True,
            "compatible_contract_ids": compatible_contract_ids,
            "selected_contract_id": selected,
            "selection_boundary": "top_voice_continuity_full_candidate_scorer",
        },
        "spread_runtime_adapter": {
            **dict(metadata.get("spread_runtime_adapter") or {}),
            "version": "v2_6_22",
            "adapter_conversion_allowed": True,
        },
        "spread_runtime_adapter_emit_all_candidates": True,
        "spread_emit_all_candidates_for_groupwise_selection": True,
        "spread_groupwise_voice_leading_runtime_enabled": True,
        "spread_lower_foundation_quality_gate_enabled": True,
        "retired_ballad_spread_pilot_metadata_removed": True,
    }
    if selected in {"spread_2plus3_contract", "spread_2plus4_contract", "spread_3plus3_contract"}:
        scoped.update(
            {
                "spread_rooted_bass_anchor_enabled": True,
                "spread_root_bass_anchor_low": 40,
                "spread_root_bass_anchor_high": 52,
                "spread_root_bass_anchor_target": 47,
                "spread_root_bass_anchor_high_tail_semitones": 4,
                "spread_root_bass_anchor_high_tail_max_lower_span": 12,
                "spread_whole_register_low": 40,
                # v2_3_3: keep Ballad SPREAD grouping-mix in a warm
                # playable band.  The previous hardcoded high ceiling (83) let
                # 2+4 / 3+3 candidates climb to G#5/B5-like tops even when
                # local voice-leading looked smooth.
                "spread_whole_register_high": int(metadata.get("spread_whole_register_high", 78 if selected != "spread_2plus3_contract" else 76)),
                "spread_whole_register_target_span": int(metadata.get("spread_whole_register_target_span", 30 if selected != "spread_2plus3_contract" else 25)),
                "spread_lower_2note_low": 40,
                "spread_lower_2note_high": int(metadata.get("spread_lower_2note_high", 58)),
                "spread_lower_2note_target_low": 40,
                "spread_lower_2note_min_top": 0,
                "spread_upper_low": int(metadata.get("spread_upper_low", 50)),
                "spread_upper_high": int(metadata.get("spread_upper_high", 77)),
                "spread_upper_target_low": int(metadata.get("spread_upper_target_low", 57)),
                "spread_min_group_gap": 1,
                "spread_max_group_gap": 7,
            }
        )
    if selected == "spread_3plus4_contract":
        scoped.update(
            {
                "spread_rooted_bass_anchor_enabled": True,
                "spread_root_bass_anchor_low": 33,
                "spread_root_bass_anchor_high": 48,
                "spread_root_bass_anchor_target": 39,
                "spread_whole_register_low": 33,
                "spread_whole_register_high": int(metadata.get("spread_whole_register_high", 77)),
                "spread_upper_low": int(metadata.get("spread_upper_low", 50)),
                "spread_upper_high": int(metadata.get("spread_upper_high", 76)),
                "spread_upper_target_low": int(metadata.get("spread_upper_target_low", 56)),
                "spread_min_group_gap": 1,
                "spread_max_group_gap": 7,
                "spread_max_overall_span": 39,
                "spread_lower_2note_low": int(nested.get("bass_piano_interaction_spread_root_bass_anchor_low", nested.get("spread_lower_2note_low", 40)) or 40),
        "spread_lower_2note_high": int(nested.get("bass_piano_interaction_spread_root_bass_anchor_high", nested.get("spread_lower_2note_high", 58)) or 58),
        "spread_lower_2note_target_low": int(nested.get("bass_piano_interaction_register_floor", nested.get("spread_lower_2note_target_low", 40)) or 40),
        "spread_upper_4note_emit_all_parent_projections": True,
                "spread_upper_4note_allow_octave_shift_candidates": True,
            }
        )
    if selected == "spread_1plus4_contract":
        scoped.update(
            {
                # v2_2_82: keep the single-root foundation in its natural root
                # register and let upper 4-note DROP2/DROP3 variants provide
                # the close placement candidates.  This replaces the rejected
                # v2_2_82 symptom patch that raised the lower root target.
                "spread_upper_low": 45,
                "spread_upper_target_low": 50,
                "spread_min_group_gap": 1,
                "spread_max_group_gap": 12,
            }
        )
    if selected in {"spread_1plus4_contract", "spread_2plus4_contract"}:
        scoped.setdefault("spread_upper_4note_emit_all_parent_projections", True)
        scoped.setdefault("spread_upper_4note_allow_octave_shift_candidates", True)
    return replace(policy, metadata=scoped)


def _spread_extra_six_note_support_slot(event_metadata: dict[str, object]) -> bool:
    """Small deterministic lift slot used to preserve the Ballad 5:6 calibration.

    v2_6_27 keeps this slot sparse enough that removing 1+4 from ordinary
    runtime does not push the Ballad texture into a 6-note-heavy body. This only
    broadens the existing grouped-SPREAD candidate pool; it does not construct
    sources, project notes, apply expression, or write MIDI.
    """

    try:
        bar = int(event_metadata.get("region_performance_bar_index", event_metadata.get("region_bar_index", 0)) or 0)
        chord_index = int(event_metadata.get("region_chord_index", 0) or 0)
    except (TypeError, ValueError):
        return False
    return (bar + chord_index) % 6 == 0


def _policy_with_spread_lower_2note_rooted_equal_cycle(policy: VoicingPolicy, event: PatternEvent) -> VoicingPolicy:
    """Optionally cycle rooted lower 2-note recipes with equal default weight.

    This is used by SPREAD 2+3/2+4 listening demos so root+3, root+5, and
    root+7 are heard as one rooted foundation family instead of being biased by
    deterministic candidate sorting. Rootless 3+7 remains a separate explicit
    mode and is never mixed into this rooted cycle.
    """

    metadata = dict(policy.metadata or {})
    if not _coerce_bool(metadata.get("spread_lower_2note_rooted_equal_weight_cycle_enabled"), default=False):
        return policy

    if _coerce_bool(metadata.get("spread_lower_foundation_quality_gate_enabled"), default=True):
        cycle_values = _quality_aware_lower_2note_cycle(event.chord_symbol)
    else:
        cycle_values = metadata.get("spread_lower_2note_rooted_recipe_cycle") or (
            "lower_2note_root_3",
            "lower_2note_root_5",
            "lower_2note_root_7",
        )
    if not isinstance(cycle_values, (list, tuple)) or not cycle_values:
        cycle_values = ("lower_2note_root_3", "lower_2note_root_5", "lower_2note_root_7")
    cycle = tuple(str(item) for item in cycle_values if str(item)) or (
        "lower_2note_root_3",
        "lower_2note_root_5",
        "lower_2note_root_7",
    )
    slot = _spread_expansion_ratio_slot(event, len(cycle))
    preferred = cycle[slot % len(cycle)]
    scoped = {
        **metadata,
        "spread_lower_2note_foundation_mode": "rooted",
        "spread_lower_2note_rooted_equal_weight_cycle_enabled": True,
        "spread_lower_2note_rooted_equal_weight_cycle_slot": slot,
        "spread_lower_2note_preferred_recipe_id": preferred,
        "spread_lower_2note_preferred_recipe_strict": False,
        "spread_lower_2note_rootless_is_separate_mode": True,
    }
    return replace(policy, metadata=scoped)



def _quality_aware_lower_2note_cycle(chord_symbol: str) -> tuple[str, ...]:
    try:
        chord = parse_chord(chord_symbol)
    except Exception:
        return ("lower_2note_root_3", "lower_2note_root_5", "lower_2note_root_7")
    if chord.has_seventh or chord.extensions or chord.alterations or chord.is_dominant or chord.is_half_diminished or chord.is_fully_diminished:
        return ("lower_2note_root_3", "lower_2note_root_7")
    return ("lower_2note_root_3", "lower_2note_root_5")



def _policy_with_spread_upper_4note_expansion_ratio(policy: VoicingPolicy, event: PatternEvent) -> VoicingPolicy:
    """Apply an explicit listening-demo ratio for SPREAD upper 4-note color.

    This mirrors the upper 3-note audit helper but targets 1+4/2+4/3+4
    upper blocks that reuse the OPEN DROP2/DROP3 projection resource.  It keeps
    the ratio event-scoped, so the expanded listening demo can aim for roughly
    60% color without changing default Jazz Ballad runtime behavior.
    """

    metadata = dict(policy.metadata or {})
    if "spread_upper_4note_expanded_color_target_ratio" not in metadata:
        return policy

    ratio = _clamp_float(metadata.get("spread_upper_4note_expanded_color_target_ratio"), default=0.60, low=0.0, high=1.0)
    cycle = max(1, int(metadata.get("spread_upper_4note_expanded_color_ratio_cycle", 5) or 5))
    expanded_slots = max(0, min(cycle, round(ratio * cycle)))
    slot = _spread_expansion_ratio_slot(event, cycle)
    use_expanded = slot < expanded_slots

    scoped = {
        **metadata,
        "spread_upper_4note_expanded_color_ratio_runtime": True,
        "spread_upper_4note_expanded_color_target_ratio": ratio,
        "spread_upper_4note_expanded_color_ratio_cycle": cycle,
        "spread_upper_4note_expanded_color_ratio_slot": slot,
        "spread_upper_4note_expanded_color_ratio_use_expanded": use_expanded,
        "spread_upper_4note_prefer_expanded_color": use_expanded,
        "spread_upper_4note_expanded_color_only": use_expanded,
    }
    if use_expanded:
        scoped["harmonic_expansion_enabled"] = True
        scoped["color_policy_mode"] = ColorPolicyMode.STYLE_SAFE_EXTENSIONS.value
        return replace(
            policy,
            harmonic_expansion_enabled=True,
            color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
            metadata=scoped,
        )

    scoped["harmonic_expansion_enabled"] = False
    scoped["color_policy_mode"] = ColorPolicyMode.CHORD_SYMBOL_ONLY.value
    return replace(
        policy,
        harmonic_expansion_enabled=False,
        color_policy_mode=ColorPolicyMode.CHORD_SYMBOL_ONLY,
        metadata=scoped,
    )


def _policy_with_spread_upper_3note_expansion_ratio(policy: VoicingPolicy, event: PatternEvent) -> VoicingPolicy:
    """Apply an explicit listening-demo ratio for SPREAD upper 3-note color.

    This is intentionally event-scoped and opt-in. It lets SPREAD grouping
    audit demos hear an expansion-enabled version at a controlled approximate
    ratio, without changing ordinary Jazz Ballad runtime defaults or creating a
    new voicing selector. When the slot is not selected for expansion, the
    event falls back to chord-symbol-only material so the expanded demo can mix
    stable and color events instead of forcing 100% color.
    """

    metadata = dict(policy.metadata or {})
    if "spread_upper_3note_expanded_color_target_ratio" not in metadata:
        return policy

    ratio = _clamp_float(metadata.get("spread_upper_3note_expanded_color_target_ratio"), default=0.60, low=0.0, high=1.0)
    cycle = max(1, int(metadata.get("spread_upper_3note_expanded_color_ratio_cycle", 5) or 5))
    expanded_slots = max(0, min(cycle, round(ratio * cycle)))
    slot = _spread_expansion_ratio_slot(event, cycle)
    use_expanded = slot < expanded_slots

    scoped = {
        **metadata,
        "spread_upper_3note_expanded_color_ratio_runtime": True,
        "spread_upper_3note_expanded_color_target_ratio": ratio,
        "spread_upper_3note_expanded_color_ratio_cycle": cycle,
        "spread_upper_3note_expanded_color_ratio_slot": slot,
        "spread_upper_3note_expanded_color_ratio_use_expanded": use_expanded,
        "spread_upper_3note_prefer_expanded_color": use_expanded,
        "spread_upper_3note_expanded_color_only": use_expanded,
    }
    if use_expanded:
        scoped["harmonic_expansion_enabled"] = True
        scoped["color_policy_mode"] = ColorPolicyMode.STYLE_SAFE_EXTENSIONS.value
        return replace(
            policy,
            harmonic_expansion_enabled=True,
            color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
            metadata=scoped,
        )

    scoped["harmonic_expansion_enabled"] = False
    scoped["color_policy_mode"] = ColorPolicyMode.CHORD_SYMBOL_ONLY.value
    return replace(
        policy,
        harmonic_expansion_enabled=False,
        color_policy_mode=ColorPolicyMode.CHORD_SYMBOL_ONLY,
        metadata=scoped,
    )


def _spread_expansion_ratio_slot(event: PatternEvent, cycle: int) -> int:
    event_metadata = dict(getattr(event, "metadata", {}) or {})
    region_id = str(getattr(event, "region_id", "") or event_metadata.get("region_id") or "")
    match = re.search(r"c(\d+)_b(\d+)_ch(\d+)", region_id)
    if match:
        chorus, bar, chord_index = (int(item) for item in match.groups())
        # Most standards in this project use up to two chord regions per bar;
        # this index gives a stable per-region slot and hits exactly 90/150 for
        # the current Misty 3-chorus SPREAD listening audits at a 3-of-5 ratio.
        return int((chorus * 100 + bar * 2 + chord_index) % max(1, cycle))
    performance_bar = int(event_metadata.get("region_performance_bar_index") or 0)
    local_beat = int(float(getattr(event, "local_beat", 0.0) or 0.0) * 2)
    return int((performance_bar * 2 + local_beat) % max(1, cycle))


def _clamp_float(value: Any, *, default: float, low: float, high: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = float(default)
    return max(float(low), min(float(high), parsed))

def _texture_contrast_plan_metadata(
    policy_metadata: dict[str, Any],
    event_metadata: dict[str, Any],
    *,
    scope_type: str,
    scope_id: str,
) -> dict[str, Any]:
    """Attach section/chorus texture-contrast intent without choosing notes.

    This is an adapter on the existing event-scoped policy path, not a new
    planner.  v2_2_38 uses it for Medium Swing only: A sections, bridge, and
    final chorus can now expose different semantic texture intent while keeping
    the concrete runtime family filtered to OPEN.
    """

    if not _coerce_bool(policy_metadata.get("voicing_texture_contrast_planning_enabled"), default=False):
        return {}
    if str(policy_metadata.get("style") or "").strip().lower() != "medium_swing":
        return {}

    section_id = str(event_metadata.get("region_section_id") or event_metadata.get("region_section_label") or "")
    phrase = str(event_metadata.get("region_phrase") or "")
    role = str(event_metadata.get("region_section_role") or "normal").strip().lower()
    chorus_index = _safe_int(event_metadata.get("region_chorus_index"), default=0)
    total_choruses = _safe_int(event_metadata.get("region_total_choruses"), default=0)
    is_bridge = role == "bridge" or phrase.upper() == "B" or section_id.upper() == "B"
    is_final_chorus = total_choruses > 0 and chorus_index == total_choruses - 1

    contrast_role = "baseline_open_swing"
    continuity = "stable"
    energy = 0.50
    density = 0.55
    width = 0.65

    if is_bridge:
        contrast_role = "bridge_open_contrast"
        continuity = "contrast"
        energy = 0.56
        density = 0.56
        width = 0.72
    elif is_final_chorus:
        contrast_role = "final_chorus_open_lift"
        continuity = "gradual"
        energy = 0.60
        density = 0.58
        width = 0.70

    shaped_method_metadata = _texture_method_weight_shaping_metadata(
        policy_metadata,
        contrast_role=contrast_role,
    )

    intent = {
        "scope_id": scope_id,
        "scope_type": scope_type,
        "character": "open_swing",
        "energy": energy,
        "density": density,
        "width": width,
        "continuity": continuity,
        "method_uniformity": "progression_locked",
        "allow_family_switch": "boundary_only",
        "preferred_family": "open",
        "source": "policy_metadata",
    }
    return {
        **shaped_method_metadata,
        "voicing_texture_intent": intent,
        "voicing_texture_contrast_role": contrast_role,
        "voicing_texture_contrast_planning_contract": "v2_2_38_medium_swing_generic_open_fallback_only",
        "voicing_texture_contrast_plan": {
            "contract": "v2_2_38_medium_swing_generic_open_fallback_only",
            "style": "medium_swing",
            "contrast_role": contrast_role,
            "section_id": section_id,
            "phrase": phrase,
            "section_role": role,
            "chorus_index": chorus_index,
            "total_choruses": total_choruses,
            "is_bridge": is_bridge,
            "is_final_chorus": is_final_chorus,
            "runtime_family_remains": "open",
            "method_weight_shaping": shaped_method_metadata.get("voicing_texture_method_weight_shaping"),
            "behavior_scope": "runtime_open_method_weight_shaping_without_family_switch",
        },
    }


def _texture_method_weight_shaping_metadata(
    policy_metadata: dict[str, Any],
    *,
    contrast_role: str,
) -> dict[str, Any]:
    """Return small Medium Swing OPEN-method weight shaping metadata.

    This remains an event-scoped adapter on the existing texture-state path.  It
    does not introduce a separate planner and it never changes the runtime
    family: Medium Swing stays in OPEN family while bridge/final-chorus intent
    slightly reshapes the OPEN method priors consumed by the existing selector.
    """

    if not _coerce_bool(policy_metadata.get("voicing_texture_method_weight_shaping_enabled"), default=False):
        return {}

    base_raw = policy_metadata.get("disposition_method_weights")
    if not isinstance(base_raw, dict):
        return {}

    shaped_weights = {
        "family": dict(base_raw.get("family") or {}),
        "open": dict(base_raw.get("open") or {}),
        "spread": dict(base_raw.get("spread") or {}),
    }
    role = str(contrast_role or "baseline_open_swing")

    if role == "bridge_open_contrast":
        open_weights = {
            "generic_open": 0.0,
            "drop2": 0.35,
            "drop3": 0.53,
            "drop2_and_4": 0.10,
        }
    elif role == "final_chorus_open_lift":
        open_weights = {
            "generic_open": 0.0,
            "drop2": 0.43,
            "drop3": 0.48,
            "drop2_and_4": 0.08,
        }
    else:
        open_weights = dict(shaped_weights.get("open") or {})

    shaped_weights["open"] = open_weights
    return {
        "disposition_method_weights": shaped_weights,
        "voicing_texture_method_weight_shaping_enabled": True,
        "voicing_texture_method_weight_shaping_contract": "v2_2_38_medium_swing_generic_open_fallback_only",
        "voicing_texture_method_weight_shaping": {
            "contract": "v2_2_38_medium_swing_generic_open_fallback_only",
            "contrast_role": role,
            "family_remains": "open",
            "open_method_weights": dict(open_weights),
            "shaping_strength": "drop_family_runtime_prior_only_generic_open_fallback_only",
        },
    }


def _texture_scope_id(event_metadata: dict[str, Any], scope_type: str) -> str:
    chorus = event_metadata.get("region_chorus_index")
    section_id = event_metadata.get("region_section_id") or event_metadata.get("region_section_label")
    phrase = event_metadata.get("region_phrase")
    role = event_metadata.get("region_section_role")

    if scope_type == "chorus":
        return f"chorus:{_safe_scope_part(chorus, '0')}"
    if scope_type == "phrase":
        return "|".join(
            (
                f"chorus:{_safe_scope_part(chorus, '0')}",
                f"phrase:{_safe_scope_part(phrase or section_id or role, 'unknown')}",
            )
        )
    if scope_type == "arrangement_segment":
        return "|".join(
            (
                f"chorus:{_safe_scope_part(chorus, '0')}",
                f"segment:{_safe_scope_part(role or section_id or phrase, 'main')}",
            )
        )
    return "|".join(
        (
            f"chorus:{_safe_scope_part(chorus, '0')}",
            f"section:{_safe_scope_part(section_id or phrase or role, 'unknown')}",
        )
    )


def _safe_scope_part(value: Any, default: str) -> str:
    if value is None or value == "":
        return default
    return str(value).replace(" ", "_").replace("|", "_").replace(":", "_")


def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}
    return default



