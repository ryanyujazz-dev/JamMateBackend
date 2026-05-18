from __future__ import annotations

from dataclasses import asdict, replace
import re
from typing import Any

from jammate_engine.core.harmony.chord_parser import parse_chord
from jammate_engine.core.roles import EnsembleContext
from jammate_engine.core.expression.expression_plan import EventExpression, ExpressionPlan
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.gestures.gesture import GestureKind
from jammate_engine.realization.gesture_realizer import GestureRealizer
from jammate_engine.realization.note_event_builder import NoteEvent
from jammate_engine.core.voicing import VoicingPolicy, VoicingRequest, VoicingResolver, VoicingPlan, ColorPolicyMode


class HarmonicRealizer:
    def __init__(self, rng=None) -> None:
        self.voicing_resolver = VoicingResolver(rng=rng)
        self.gesture_realizer = GestureRealizer()
        self.last_piano_audit_events: list[dict[str, Any]] = []

    def realize(
        self,
        events: list[PatternEvent],
        expression: ExpressionPlan,
        style_voicing_policy: VoicingPolicy | dict | None,
        ensemble: EnsembleContext | dict,
    ) -> list[NoteEvent]:
        self.last_piano_audit_events = []
        if isinstance(style_voicing_policy, VoicingPolicy):
            policy = style_voicing_policy
        else:
            policy = VoicingPolicy.from_legacy_dict(style_voicing_policy or {})
        out: list[NoteEvent] = []
        event_by_id = {event.event_id: event for event in events}
        # Default harmonic-comping contract: one vertical voicing decision per
        # chord region. Multiple piano hits inside the same region should reuse
        # that selected source/order/register unless a future explicit gesture
        # asks for re-voicing or voice motion. This keeps source-weight listening
        # stable and prevents repeated rhythm hits from randomly changing
        # inversion within one unchanged harmony.
        region_voicing_cache: dict[tuple[str, str, str], VoicingPlan] = {}
        piano_events = sorted(
            (event for event in events if event.status == "active" and event.track == "piano"),
            key=lambda event: (event.onset_beat, event.region_id, event.event_id),
        )
        for event in piano_events:
            expr = expression.events.get(event.event_id)
            if expr is None:
                continue
            cache_key = (event.region_id, event.chord_symbol, event.track)
            cached = region_voicing_cache.get(cache_key)
            if cached is None or _event_requests_fresh_voicing(event):
                event_policy = _policy_with_event_texture_scope(policy, event)
                req = VoicingRequest(
                    event_id=event.event_id,
                    chord_symbol=event.chord_symbol,
                    track=event.track,
                    gesture_type=event.gesture_type,
                    gesture=event.gesture,
                    expression_articulation=expr.articulation,
                    ensemble_context=ensemble,
                    policy=event_policy,
                    onset_beat=event.onset_beat,
                )
                voicing = self.voicing_resolver.resolve(req)
                region_voicing_cache[cache_key] = voicing
            else:
                voicing = _reuse_region_voicing(cached, event.event_id)
            realized = self.gesture_realizer.realize_harmonic_event(event, voicing, expr)
            if _event_is_partial_reattack(event):
                out = _release_reattacked_motion_voices(
                    existing_notes=out,
                    current_event=event,
                    current_notes=realized,
                    event_by_id=event_by_id,
                )
            out.extend(realized)
            self.last_piano_audit_events.append(_piano_audit_event(event, expr, voicing, realized))
        self.last_piano_audit_events = _sync_piano_audit_realized_notes(self.last_piano_audit_events, out)
        return out


def _policy_with_event_texture_scope(policy: VoicingPolicy, event: PatternEvent) -> VoicingPolicy:
    """Attach phrase/section/chorus texture-scope metadata for one voicing request.

    Styles may opt in through policy metadata.  The helper does not choose notes
    or methods; it only resolves the runtime scope identity consumed by
    VoicingTextureState so family-level texture is no longer an anonymous
    style-global flag.
    """

    policy = _policy_with_event_harmonic_context(policy, event)
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

    This only broadens the existing grouped-SPREAD candidate pool; it does not
    construct sources, project notes, apply expression, or write MIDI.
    """

    try:
        bar = int(event_metadata.get("region_performance_bar_index", event_metadata.get("region_bar_index", 0)) or 0)
        chord_index = int(event_metadata.get("region_chord_index", 0) or 0)
    except (TypeError, ValueError):
        return False
    return (bar + chord_index) % 4 == 0


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
            "drop2_and_4": 0.12,
        }
    elif role == "final_chorus_open_lift":
        open_weights = {
            "generic_open": 0.0,
            "drop2": 0.43,
            "drop3": 0.48,
            "drop2_and_4": 0.09,
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



def _event_is_partial_reattack(event: PatternEvent) -> bool:
    gesture = getattr(event, "gesture", None)
    gesture_kind = getattr(gesture, "kind", None)
    gesture_type = str(getattr(event, "gesture_type", "") or getattr(gesture, "gesture_type", "") or "").strip().lower()
    if gesture_kind == GestureKind.INNER_MOVEMENT or gesture_type == GestureKind.INNER_MOVEMENT.value:
        metadata = dict(getattr(gesture, "metadata", {}) or {})
        held_policy = str(metadata.get("held_voice_policy") or "").strip().lower()
        scope = str(metadata.get("rearticulation_scope") or "").strip().lower()
        return held_policy in {"hold_foundation_common_tones", "hold_common_tones", "tie_foundation"} or "inner" in scope or "color" in scope
    return False


def _release_reattacked_motion_voices(
    *,
    existing_notes: list[NoteEvent],
    current_event: PatternEvent,
    current_notes: list[NoteEvent],
    event_by_id: dict[str, PatternEvent],
) -> list[NoteEvent]:
    """Trim only voices reattacked by an INNER_MOVEMENT gesture.

    The previous expression pass intentionally lets the full anchor ring through
    a partial reattack.  This realization-layer adjustment releases just the
    motion voices that are re-struck, leaving foundation/common tones held.  It
    consumes already-selected voicing projection metadata and never chooses new
    pitch content.
    """

    if not current_notes:
        return existing_notes
    current_start = min(float(note.start_beat) for note in current_notes)
    selected_keys = {_voice_identity_key(note) for note in current_notes}
    selected_pitches = {int(note.note) for note in current_notes}
    out: list[NoteEvent] = []
    for note in existing_notes:
        prior_event = event_by_id.get(str(note.expression_event_id or ""))
        if prior_event is None or prior_event.region_id != current_event.region_id or prior_event.track != current_event.track:
            out.append(note)
            continue
        if float(note.start_beat) >= current_start - 1e-9:
            out.append(note)
            continue
        note_end = float(note.start_beat) + float(note.duration_beats)
        if note_end <= current_start + 1e-9:
            out.append(note)
            continue
        if _voice_identity_key(note) not in selected_keys and int(note.note) not in selected_pitches:
            out.append(note)
            continue
        new_duration = max(0.05, current_start - float(note.start_beat))
        if new_duration >= float(note.duration_beats) - 1e-9:
            out.append(note)
            continue
        pedal_debug = dict(note.pedal_debug or {})
        pedal_debug.update(
            {
                "partial_reattack_release_version": "v2_5_4",
                "partial_reattack_release_applied": True,
                "partial_reattack_release_reason": "inner_movement_restruck_motion_voice_foundation_held",
                "partial_reattack_source_event_id": current_event.event_id,
                "partial_reattack_original_duration_beats": round(float(note.duration_beats), 6),
                "partial_reattack_trimmed_duration_beats": round(float(new_duration), 6),
            }
        )
        out.append(replace(note, duration_beats=new_duration, pedal_debug=pedal_debug))
    return out


def _voice_identity_key(note: NoteEvent) -> tuple[str | None, str | None, str | None]:
    return (note.voice_role, note.group_id, note.projection_ref)


def _sync_piano_audit_realized_notes(audit_events: list[dict[str, Any]], final_notes: list[NoteEvent]) -> list[dict[str, Any]]:
    notes_by_expression_event: dict[str, list[NoteEvent]] = {}
    for note in final_notes:
        if note.expression_event_id:
            notes_by_expression_event.setdefault(str(note.expression_event_id), []).append(note)
    synced: list[dict[str, Any]] = []
    for row in audit_events:
        event_id = str(row.get("event_id") or "")
        if event_id in notes_by_expression_event:
            row = dict(row)
            row["realized_notes"] = [_note_event_debug(note) for note in notes_by_expression_event[event_id]]
        synced.append(row)
    return synced

def _piano_audit_event(
    event: PatternEvent,
    expression: EventExpression,
    voicing: VoicingPlan,
    realized_notes: list[NoteEvent],
) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "pattern_event": {
            "event_id": event.event_id,
            "track": event.track,
            "region_id": event.region_id,
            "chord_symbol": event.chord_symbol,
            "onset_beat": event.onset_beat,
            "local_beat": event.local_beat,
            "role": event.role,
            "gesture_type": event.gesture_type,
            "gesture": _gesture_debug(event),
            "expression_hint": event.expression_hint,
            "pattern_id": event.pattern_id,
            "source_event_id": event.source_event_id,
            "status": event.status,
            "metadata": dict(event.metadata),
        },
        "expression": asdict(expression),
        "voicing": voicing.to_debug_dict(),
        "realized_notes": [_note_event_debug(note) for note in realized_notes],
    }


def _gesture_debug(event: PatternEvent) -> dict[str, Any]:
    gesture = event.gesture
    return {
        "gesture_type": gesture.gesture_type,
        "projection_refs": list(gesture.projection_refs),
        "onset_offsets_beats": list(gesture.onset_offsets_beats),
        "metadata": dict(gesture.metadata),
    }


def _note_event_debug(note: NoteEvent) -> dict[str, Any]:
    return {
        "track": note.track,
        "channel": note.channel,
        "note": note.note,
        "velocity": note.velocity,
        "start_beat": note.start_beat,
        "duration_beats": note.duration_beats,
        "timing_intent": note.timing_intent,
        "voice_role": note.voice_role,
        "group_id": note.group_id,
        "projection_ref": note.projection_ref,
        "voicing_event_id": note.voicing_event_id,
        "expression_event_id": note.expression_event_id,
        "pedal": note.pedal,
        "release_beats": note.release_beats,
        "pedal_debug": dict(note.pedal_debug),
    }


def _event_requests_fresh_voicing(event: PatternEvent) -> bool:
    """Future gesture escape hatch for deliberate re-voicing inside a region."""

    metadata = dict(getattr(event, "metadata", {}) or {})
    gesture_metadata = dict(getattr(getattr(event, "gesture", None), "metadata", {}) or {})
    return bool(
        metadata.get("force_fresh_voicing")
        or metadata.get("revoice_within_region")
        or gesture_metadata.get("force_fresh_voicing")
        or gesture_metadata.get("revoice_within_region")
    )


def _reuse_region_voicing(voicing: VoicingPlan, event_id: str) -> VoicingPlan:
    metadata = dict(voicing.metadata or {})
    metadata.update(
        {
            "region_voicing_reused": True,
            "region_voicing_source_event_id": voicing.event_id,
            "region_voicing_contract": "one_default_voicing_selection_per_chord_region_until_explicit_gesture_revoices",
        }
    )
    return replace(voicing, event_id=event_id, metadata=metadata)
