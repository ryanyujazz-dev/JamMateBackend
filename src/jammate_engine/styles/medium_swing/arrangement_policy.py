from __future__ import annotations



def resolve_repeat_count_arrangement_arc(chorus_index: int, total_choruses: int) -> dict:
    """Return a repeat-count-aware Medium Swing macro-energy intent.

    This is a style-owned semantic policy helper. It does not emit notes, choose
    rhythm cells, write expression values, or modify voicings.  The design is
    intentionally normalized around the user's selected repeat count so callers
    can reason about 1x, 2x, 3x, 5x, 10x, or long practice loops such as 50x
    without hard-coding a 3-chorus arc.
    """

    total = max(1, int(total_choruses or 1))
    idx = max(0, min(int(chorus_index or 0), total - 1))
    position = 0.0 if total <= 1 else idx / float(total - 1)

    # Long practice loops should not grow forever.  They cycle through compact
    # four-chorus waves while preserving first/final chorus semantics.
    loop_block_index = idx // 4
    loop_block_position = idx % 4

    if total == 1:
        phase = "single_pass_balanced"
        energy_band = "balanced"
        density_bias = "medium"
        piano_comping_bias = "clear_stable"
        fill_bias = "very_low"
        thick_voicing_bias = "ending_only"
    elif idx == 0:
        phase = "head_in_clear"
        energy_band = "low_medium"
        density_bias = "light_medium"
        piano_comping_bias = "stable_anchor_first"
        fill_bias = "very_low"
        thick_voicing_bias = "off"
    elif idx == total - 1:
        phase = "final_head_out_release"
        energy_band = "medium_high"
        density_bias = "medium_high_but_not_max"
        piano_comping_bias = "settled_with_section_tail_support"
        fill_bias = "section_tail_only"
        thick_voicing_bias = "ending_and_section_tail_only"
    elif total == 2:
        phase = "second_pass_build_without_final_climax"
        energy_band = "medium"
        density_bias = "medium"
        piano_comping_bias = "stable_with_light_conversation"
        fill_bias = "low"
        thick_voicing_bias = "off"
    elif total <= 4:
        if position < 0.5:
            phase = "development_lift"
            energy_band = "medium"
            density_bias = "medium"
            piano_comping_bias = "light_conversation"
            fill_bias = "low"
            thick_voicing_bias = "off"
        else:
            phase = "late_build"
            energy_band = "medium_high"
            density_bias = "medium"
            piano_comping_bias = "controlled_activity"
            fill_bias = "low_medium_section_tail"
            thick_voicing_bias = "section_tail_optional"
    else:
        # For 5+ and especially 10+/50+ loops, use repeat waves rather than a
        # monotonic ramp.  This keeps long practice playback from sounding as if
        # every chorus must be more intense than the previous one.
        if loop_block_position == 0:
            phase = "loop_wave_reset"
            energy_band = "low_medium"
            density_bias = "light_medium"
            piano_comping_bias = "stable_reset"
            fill_bias = "very_low"
            thick_voicing_bias = "off"
        elif loop_block_position == 1:
            phase = "loop_wave_develop"
            energy_band = "medium"
            density_bias = "medium"
            piano_comping_bias = "light_conversation"
            fill_bias = "low"
            thick_voicing_bias = "off"
        elif loop_block_position == 2:
            phase = "loop_wave_peak"
            energy_band = "medium_high"
            density_bias = "medium_high_limited"
            piano_comping_bias = "controlled_activity"
            fill_bias = "low_medium_section_tail"
            thick_voicing_bias = "section_tail_optional"
        else:
            phase = "loop_wave_release"
            energy_band = "medium_low"
            density_bias = "medium_low"
            piano_comping_bias = "settle_and_breathe"
            fill_bias = "very_low"
            thick_voicing_bias = "off"

    return {
        "version": "v2_6_84",
        "chorus_index": idx,
        "total_choruses": total,
        "normalized_position": round(position, 4),
        "loop_block_index": loop_block_index,
        "loop_block_position": loop_block_position,
        "phase": phase,
        "energy_band": energy_band,
        "density_bias": density_bias,
        "piano_comping_bias": piano_comping_bias,
        "fill_bias": fill_bias,
        "thick_voicing_bias": thick_voicing_bias,
        "long_loop_safe": total >= 8,
        "monotonic_ramp_allowed": False,
        "source": "medium_swing_repeat_count_aware_arrangement_arc_policy",
    }


def simulate_repeat_count_arrangement_arc(total_choruses: int) -> list[dict]:
    """Return the per-chorus macro arc for an arbitrary repeat count."""

    total = max(1, int(total_choruses or 1))
    return [resolve_repeat_count_arrangement_arc(i, total) for i in range(total)]


ARRANGEMENT_ARC_RUNTIME_INTENT_USAGE_VERSION = "v2_6_85"


def resolve_runtime_arrangement_arc_intent(chorus_index: int, total_choruses: int) -> dict:
    """Return the runtime-consumable Medium Swing arrangement intent.

    v2_6_85 turns the v2_6_84 repeat-count-aware arc from an audit-only
    declaration into event-scoped style intent metadata.  It still does not emit
    notes, choose voicings, write expression values, or hard-code a 3-chorus
    behavior.
    """

    arc = resolve_repeat_count_arrangement_arc(chorus_index, total_choruses)
    phase = str(arc.get("phase") or "unknown")
    density_bias = str(arc.get("density_bias") or "medium")
    fill_bias = str(arc.get("fill_bias") or "low")
    thick_bias = str(arc.get("thick_voicing_bias") or "off")

    if phase in {"head_in_clear", "loop_wave_reset"}:
        comping_intent = "stable_clear_head_or_reset"
    elif phase in {"loop_wave_develop", "development_lift", "second_pass_build_without_final_climax"}:
        comping_intent = "light_conversation"
    elif phase in {"loop_wave_peak", "late_build"}:
        comping_intent = "controlled_activity"
    elif phase in {"loop_wave_release", "final_head_out_release"}:
        comping_intent = "settled_release"
    elif phase == "single_pass_balanced":
        comping_intent = "single_pass_balanced"
    else:
        comping_intent = "neutral"

    return {
        **arc,
        "runtime_intent_usage_version": ARRANGEMENT_ARC_RUNTIME_INTENT_USAGE_VERSION,
        "runtime_intent_enabled": True,
        "runtime_intent_source": "medium_swing_repeat_count_aware_arrangement_arc",
        "piano_comping_runtime_intent": comping_intent,
        "piano_comping_density_bias": density_bias,
        "piano_comping_fill_bias": fill_bias,
        "piano_comping_thick_voicing_bias": thick_bias,
        "runtime_usage_boundary": "style_intent_metadata_and_candidate_weighting_only",
        "no_pattern_vocabulary_change": True,
        "no_core_voicing_change": True,
        "no_expression_numeric_change": True,
        "not_three_chorus_hardcoded": True,
    }


def arrangement_arc_runtime_candidate_multiplier(candidate_metadata: dict, intent: dict) -> tuple[float, tuple[str, ...], str]:
    """Return a small style-owned multiplier for one piano comping candidate.

    The function intentionally consumes only candidate metadata and the
    repeat-count-aware arc intent.  It does not know about MIDI, voicing
    projection, expression values, or any bar-first phrase template.
    """

    metadata = dict(candidate_metadata or {})
    intent = dict(intent or {})
    phase = str(intent.get("phase") or "unknown")
    comping_intent = str(intent.get("piano_comping_runtime_intent") or "neutral")
    fill_bias = str(intent.get("piano_comping_fill_bias") or intent.get("fill_bias") or "low")
    density_bias = str(intent.get("piano_comping_density_bias") or intent.get("density_bias") or "medium")
    calibration_class = str(metadata.get("weight_calibration_class") or "stable")
    density = str(metadata.get("density") or metadata.get("density_class") or "medium")
    rhythm_family = str(metadata.get("rhythm_family") or "")
    phrase_role = str(metadata.get("phrase_role") or "")
    optional = bool(metadata.get("optional_fill_variation_vocabulary_candidate") or metadata.get("optional_fill_variation_candidate"))
    optional_role = str(metadata.get("optional_fill_variation_role") or metadata.get("optional_fill_variation_role_runtime") or "")
    has_start_anchor = bool(metadata.get("requires_region_start_anchor"))
    is_active = calibration_class in {"active", "fill", "busy"} or optional_role in {"transition_fill", "busy_fill"}
    is_offbeat = calibration_class == "offbeat" or "offbeat" in rhythm_family or "charleston" in rhythm_family
    is_fill = optional_role == "transition_fill" or "fill" in phrase_role or "fill" in rhythm_family
    is_busy = optional_role == "busy_fill" or calibration_class == "busy" or "busy" in rhythm_family
    is_stable = calibration_class == "stable" or rhythm_family == "stable"

    multiplier = 1.0
    reasons: list[str] = []
    status = "arc_neutral"

    if comping_intent in {"stable_clear_head_or_reset", "settled_release"}:
        if is_stable and has_start_anchor:
            multiplier *= 1.08
            reasons.append(f"{phase}_stable_anchor_bonus")
            status = "arc_prefers_stable_anchor"
        if is_offbeat and not has_start_anchor:
            multiplier *= 0.82
            reasons.append(f"{phase}_offbeat_space_guard")
            status = "arc_space_guard"
        if is_active or is_fill or is_busy or optional:
            multiplier *= 0.72 if not is_busy else 0.34
            reasons.append(f"{phase}_activity_or_optional_guard")
            status = "arc_activity_guard"
        if density == "dense":
            multiplier *= 0.80
            reasons.append(f"{phase}_dense_candidate_guard")
    elif comping_intent == "light_conversation":
        if is_offbeat and not is_busy:
            multiplier *= 1.04
            reasons.append(f"{phase}_light_conversation_bonus")
            status = "arc_light_conversation"
        if is_busy:
            multiplier *= 0.22
            reasons.append(f"{phase}_busy_still_guarded")
            status = "arc_busy_guard"
        if is_fill and fill_bias in {"very_low", "low"}:
            multiplier *= 0.70
            reasons.append(f"{phase}_fill_bias_low_guard")
    elif comping_intent == "controlled_activity":
        if optional_role == "variation" or (is_offbeat and has_start_anchor):
            multiplier *= 1.06
            reasons.append(f"{phase}_controlled_activity_micro_bonus")
            status = "arc_controlled_activity"
        if is_fill and fill_bias in {"low_medium_section_tail", "section_tail_only"}:
            multiplier *= 1.04
            reasons.append(f"{phase}_section_tail_fill_micro_bonus")
        if is_busy:
            multiplier *= 0.45
            reasons.append(f"{phase}_busy_remains_guarded")
            status = "arc_busy_guard"
    elif comping_intent == "single_pass_balanced":
        if is_stable and has_start_anchor:
            multiplier *= 1.03
            reasons.append("single_pass_stable_anchor_micro_bonus")
            status = "arc_single_pass_balance"
        if is_busy:
            multiplier *= 0.30
            reasons.append("single_pass_busy_guard")
            status = "arc_busy_guard"

    if density_bias in {"light_medium", "medium_low"} and density == "dense":
        multiplier *= 0.72
        reasons.append(f"density_bias_{density_bias}_dense_guard")
    if density_bias in {"medium_high_limited", "medium_high_but_not_max"} and optional_role == "variation":
        multiplier *= 1.03
        reasons.append(f"density_bias_{density_bias}_variation_micro_bonus")
    if fill_bias == "very_low" and (is_fill or optional_role in {"transition_fill", "busy_fill"}):
        multiplier *= 0.58
        reasons.append("fill_bias_very_low_guard")
    if fill_bias == "section_tail_only" and is_fill:
        multiplier *= 0.88
        reasons.append("fill_bias_section_tail_only_runtime_guard")

    if not reasons:
        reasons.append("arc_runtime_intent_neutral_passthrough")
    return max(0.0, float(multiplier)), tuple(reasons), status


def get_arrangement_policy() -> dict:
    """Medium swing arrangement-level guards.

    The policy remains style-owned, but it only declares guard preferences. The
    default StyleProfile planner applies the guards without letting style files
    emit notes, velocities, durations, or voicings.
    """

    return {
        "default_feel": "medium_swing",
        "avoid_immediate_pattern_repeat": True,
        "avoid_immediate_pattern_category_repeat": True,
        "piano_comping_density_guard": True,
        "piano_region_length_pattern_vocabulary_version": "v2_6_56",
        "piano_region_length_candidate_lookup_policy_version": "v2_6_57",
        "piano_region_length_weight_calibration_policy_version": "v2_6_58",
        "piano_comping_history_continuity_scorer": True,
        "piano_comping_history_continuity_scorer_version": "v2_6_59",
        "piano_comping_active_fill_busy_multi_region_history_scorer": True,
        "piano_comping_active_fill_busy_multi_region_history_scorer_version": "v2_6_67",
        "piano_comping_harmonic_function_policy": True,
        "piano_comping_harmonic_function_policy_version": "v2_6_60",
        "piano_comping_progression_specific_subset_policy": True,
        "piano_comping_progression_specific_subset_policy_version": "v2_6_65",
        "piano_comping_no_4and_delayed_tail_idiom_policy": True,
        "piano_comping_no_4and_delayed_tail_idiom_policy_version": "v2_6_66",
        "piano_expression_policy_v1_numeric_calibration": True,
        "piano_expression_policy_v1_numeric_calibration_version": "v2_6_68",
        "piano_standard_tune_listening_checkpoint": True,
        "piano_standard_tune_listening_checkpoint_version": "v2_6_69",
        "piano_comping_ending_specific_subset_policy": True,
        "piano_comping_ending_specific_subset_policy_version": "v2_6_70",
        "piano_comping_optional_fill_variation_vocabulary_policy": True,
        "piano_comping_optional_fill_variation_vocabulary_policy_version": "v2_6_71",
        "piano_comping_optional_fill_variation_listening_refinement_policy": True,
        "piano_comping_optional_fill_variation_listening_refinement_policy_version": "v2_6_72",
        "piano_comping_phrase_end_fill_context_precision_policy": True,
        "piano_comping_phrase_end_fill_context_precision_policy_version": "v2_6_73",
        "piano_comping_standard_tune_fill_frequency_checkpoint": True,
        "piano_comping_standard_tune_fill_frequency_checkpoint_version": "v2_6_74",
        "medium_swing_piano_comping_phase_completion_checkpoint": True,
        "medium_swing_piano_comping_phase_completion_checkpoint_version": "v2_6_76",
        "medium_swing_existing_voicing_capability_usage_policy": True,
        "medium_swing_existing_voicing_capability_usage_policy_version": "v2_6_77",
        "medium_swing_existing_voicing_capability_low_register_clarity_guard": True,
        "medium_swing_existing_voicing_capability_low_register_clarity_guard_version": "v2_6_78",
        "medium_swing_full_band_listening_checkpoint": True,
        "medium_swing_full_band_listening_checkpoint_version": "v2_6_79",
        "piano_comping_two_beat_region_density_relief_policy": True,
        "piano_comping_two_beat_region_density_relief_policy_version": "v2_6_80",
        "piano_comping_two_beat_phrase_pair_policy": True,
        "piano_comping_two_beat_phrase_pair_policy_version": "v2_6_119",
        "medium_swing_full_band_post_density_relief_checkpoint": True,
        "medium_swing_full_band_post_density_relief_checkpoint_version": "v2_6_81",
        "medium_swing_bass_piano_interaction_audit": True,
        "medium_swing_bass_piano_interaction_audit_version": "v2_6_82",
        "medium_swing_drum_piano_interaction_audit": True,
        "medium_swing_drum_piano_interaction_audit_version": "v2_6_83",
        "medium_swing_repeat_count_aware_arrangement_arc_checkpoint": True,
        "medium_swing_repeat_count_aware_arrangement_arc_checkpoint_version": "v2_6_84",
        "medium_swing_arrangement_arc_runtime_intent_usage": True,
        "medium_swing_arrangement_arc_runtime_intent_usage_version": "v2_6_85",
        "medium_swing_arrangement_arc_runtime_listening_refinement": True,
        "medium_swing_arrangement_arc_runtime_listening_refinement_version": "v2_6_86",
        "medium_swing_full_band_ending_realization_checkpoint": True,
        "medium_swing_full_band_ending_realization_checkpoint_version": "v2_6_87",
        "medium_swing_style_baseline_phase_completion_checkpoint": True,
        "medium_swing_style_baseline_phase_completion_checkpoint_version": "v2_6_88",
        "medium_swing_baseline_handoff_or_next_style_selection": True,
        "medium_swing_baseline_handoff_or_next_style_selection_version": "v2_6_89",
        "medium_swing_baseline_handoff_freeze_condition": "freeze_medium_swing_unless_user_reports_specific_listening_issue",
        "medium_swing_baseline_handoff_recommended_next_style": "bossa_nova",
        "medium_swing_baseline_handoff_recommended_next_task": "v2_6_90_engine_bossa_nova_style_baseline_audit_from_latest_v2_10_28",
        "medium_swing_baseline_handoff_behavior_change": False,
        "medium_swing_baseline_handoff_no_pattern_change": True,
        "medium_swing_baseline_handoff_no_core_voicing_change": True,
        "medium_swing_baseline_handoff_no_expression_numeric_change": True,
        "medium_swing_baseline_handoff_no_api_agent_harmonyos_change": True,
        "piano_region_first_anticipation_compatibility_checkpoint": True,
        "piano_region_first_anticipation_compatibility_checkpoint_version": "v2_6_61",
        "piano_region_first_coverage_guard": True,
        "piano_region_first_coverage_guard_version": "v2_6_62",
        "piano_region_length_pattern_vocabulary_contract": "Medium Swing piano comping is selected from ChordRegion-local 1/2/4-beat pitchless rhythm cells; no bar-level two-chord-bar pattern path is used.",
        "piano_region_length_candidate_lookup_contract": "ChordRegion duration routes candidate lookup to 1/2/4-beat region-local pattern families before weighted sampling; inactive v2_6_56 vocabulary is activated only inside its matching region-length family.",
        "piano_region_length_weight_calibration_contract": "Medium Swing piano comping keeps stable cells primary, offbeat conversation secondary, active cells controlled, and native tail-push cells rare; calibration is applied inside the existing region-length pattern library, not through a parallel selector.",
        "piano_comping_history_continuity_contract": "Medium Swing piano comping applies a lightweight history scorer to the existing region-length candidate pool, penalizing exact repeat, non-stable family repeat, consecutive offbeat/active/tail-push, and rewarding stable reset after active/offbeat; no parallel selector is introduced.",
        "piano_comping_active_fill_busy_multi_region_history_contract": "v2_6_67 extends the existing history scorer in-place with multi-region active/fill/busy/push/tail-push memory, stable reset bonuses, and no-4& delayed-tail recovery after recent push; it remains ChordRegion-first and does not restore bar-first phrase templates.",
        "piano_comping_harmonic_function_contract": "Medium Swing piano comping reweights the existing ChordRegion-length candidate pool by functional motion labels such as predominant_to_dominant, dominant_resolution, tonic_resolution, section_start, section_end, and ending; this remains a multiplier policy before the normal history scorer, not a bar-first/two-chord-bar or parallel selector path.",
        "piano_comping_progression_specific_subset_contract": "Medium Swing piano comping translates V1 major_251/minor_251/two_five/ii_setup priority into a ChordRegion-first preferred subset inside the existing region-length candidate pool; it never restores bar-first/two-chord-bar templates, never chooses voicing, and never writes final expression values.",
        "piano_comping_no_4and_delayed_tail_idiom_contract": "Medium Swing piano comping translates V1 no-4& / delayed-tail preference as region-local candidate reweighting: native 4& tail-push remains available as rare lift, delayed/tail/backbeat cells get only modest bonuses, and routing remains ChordRegion-first.",
        "piano_expression_policy_v1_numeric_calibration_contract": "Medium Swing piano expression calibrates style-owned ExpressionProfile defaults from V1 soft_hold/light_stab/accent_stab/backbeat_hold/final_hold numeric ranges; pattern files remain semantic-only and never write velocity/duration/pedal.",
        "piano_standard_tune_listening_checkpoint_contract": "v2_6_69 is a behavior-preserving standard-tune listening checkpoint after v2_6_67 history scoring and v2_6_68 expression calibration; it adds audit/demo coverage only and does not change pattern, voicing, expression, API, Agent, or HarmonyOS runtime behavior.",
        "piano_comping_ending_specific_subset_contract": "v2_6_70 reweights final-bar Medium Swing piano comping candidates inside the existing ChordRegion-length pool toward stable region-start settling and away from active/4& push; it does not add an ending selector, new vocabulary, voicing logic, or final expression values.",
        "piano_comping_optional_fill_variation_vocabulary_contract": "v2_6_71 activates a very small optional fill/variation vocabulary inside the existing ChordRegion-length Medium Swing piano pool. These candidates stay pitchless, low-weight, context-reweighted, and guarded by the v2_6_67 active/fill/busy history scorer; no parallel fill selector, voicing logic, or final expression values are introduced.",
        "piano_comping_optional_fill_variation_listening_refinement_contract": "v2_6_72 keeps the v2_6_71 optional vocabulary unchanged and only refines context/history multipliers after user review: light variation remains low-intrusion, transition fill is more phrase/section/turnaround-aware, busy fill stays near-blocked unless explicitly high-energy and history-safe.",
        "piano_comping_phrase_end_fill_context_precision_contract": "v2_6_73 keeps the v2_6_71/v2_6_72 optional fill vocabulary unchanged and only sharpens where the existing transition-fill candidate receives support: explicit phrase ends, section tails, and 4/8-bar phrase tails are favored, while harmonic-transition-only regions are downweighted. No phrase engine, fill selector, new vocabulary, voicing logic, or final expression values are introduced.",
        "piano_comping_standard_tune_fill_frequency_checkpoint_contract": "v2_6_74 is a behavior-preserving standard-tune fill-frequency checkpoint after user approval of v2_6_71/72/73. It measures optional variation/fill frequency, phrase-tail targeting, and active/fill/busy continuity on 3-chorus standard demos without changing weights, adding vocabulary, creating a fill selector, or touching voicing/expression/API/Agent/HarmonyOS.",
        "medium_swing_piano_comping_phase_completion_checkpoint_contract": "v2_6_76 is a behavior-preserving stage-completion checkpoint for the v2_6_56 through v2_6_74 Medium Swing piano comping line. It confirms ChordRegion-first vocabulary, history continuity, expression-hint handoff, ending stability, optional fill low-intrusion, and pattern/voicing/expression separation before returning to voicing or broader listening work; it does not change weights, add vocabulary, create a selector, or touch API/Agent/HarmonyOS.",
        "medium_swing_existing_voicing_capability_usage_policy_contract": "v2_6_77 does not modify core voicing internals. Medium Swing keeps ordinary runtime comping on existing OPEN/DROP 4-note policy by default; when explicitly enabled through style intent or voicing_override metadata, event-scoped style policy may request already-existing grouped SPREAD 5/6-note support for final-chorus section tails or ending climax regions.",
        "medium_swing_existing_voicing_capability_low_register_clarity_guard_contract": "v2_6_78 keeps v2_6_77 as an explicit style-intent capability but routes optional grouped-SPREAD 5/6-note usage through the existing spread low-register density guard: in full-band/bass-present usage, no more than one piano note may sit below C3. This is a style/event metadata request, not a core voicing implementation change.",
        "medium_swing_full_band_listening_checkpoint_contract": "v2_6_79 is a behavior-preserving full-band listening checkpoint after the v2_6_78 low-register clarity guard. It generates and audits 3-chorus Medium Swing demos with piano, bass, and drums enabled to confirm whole-band track presence, piano/bass low-register clarity, optional 5/6-note intrusion, optional fill frequency, bass continuity, dry swing pedal behavior, and ending stability. It does not change pattern, voicing internals, expression numbers, API, Agent, or HarmonyOS.",
        "piano_comping_two_beat_region_density_relief_policy_contract": "v2_6_80 relaxes Medium Swing piano comping in dense 2-beat ChordRegions such as Autumn Leaves: it favors simple region-start anchors, downweights multi-touch/offbeat short-region cells, and preserves previous-region tail space so the generic AnticipationResolver can move next-region beat-1 events to the prior local 2& when probability permits. It stays inside the existing ChordRegion-local candidate weighting path and does not add vocabulary, restore bar-first/two-chord-bar routing, touch voicing/expression internals, or affect API/Agent/HarmonyOS behavior.",
        "piano_comping_two_beat_phrase_pair_policy_contract": "v2_6_119 adds a Medium Swing common 2-beat phrase as first-principles pattern vocabulary plus history-aware weighting: one 2-beat ChordRegion may use local 1+2, and the following 2-beat ChordRegion may answer on local 1& with a hold, corresponding to full-bar beat 3&. It remains ChordRegion-local/pitchless, does not restore bar-first two-chord-bar routing, and does not touch voicing/expression internals/API/Agent/HarmonyOS.",
        "medium_swing_full_band_post_density_relief_checkpoint_contract": "v2_6_81 is a behavior-preserving full-band checkpoint after v2_6_80 density relief and anticipation audit. It generates and audits 3-chorus Medium Swing demos with piano, bass, and drums enabled to confirm Autumn Leaves no longer feels over-dense in consecutive 2-beat ChordRegions, All The Things You Are is not over-thinned, generic region-first anticipation remains active, the v2_6_78 low-register clarity guard still holds, and optional 5/6-note usage remains explicit and low-intrusion. It does not change pattern, voicing internals, expression numbers, API, Agent, or HarmonyOS.",
        "medium_swing_bass_piano_interaction_audit_contract": "v2_6_82 audits Medium Swing bass walking and piano comping interaction in full-band demos after the v2_6_80 density relief: piano/bass low-register overlap, exact low unisons, 2-beat region density sharing, bass continuity, optional 5/6-note SPREAD intrusion, and dry swing pedal behavior. It may request stricter style/event-scoped register metadata for explicitly enabled 5/6-note grouped SPREAD so piano does not duplicate the bass foundation in the low register; it does not modify core voicing internals, pattern rhythm, expression numbers, API, Agent, or HarmonyOS.",
        "medium_swing_drum_piano_interaction_audit_contract": "v2_6_83 audits Medium Swing drum ride/hi-hat foundation and piano comping interaction in full-band demos after v2_6_82. It reconstructs the region-local drum time grid for audit only, checks piano hits on ride accents, hi-hat 2/4, ride-skip ghosts, optional fill/variation overlap, 2-beat density sharing, anticipation retention, and dry swing behavior. It does not add drum fills, change drum patterns, modify piano patterns, voicing internals, expression numbers, API, Agent, or HarmonyOS.",
        "medium_swing_repeat_count_aware_arrangement_arc_checkpoint_contract": "v2_6_84 declares a repeat-count-aware Medium Swing macro-energy policy for 1x, 2x, 3x, 5x, 6x, 8x, 9x, 10x, and long practice loops such as 50x. It uses normalized positions plus four-chorus wave reset/develop/peak/release cycles so long loops do not ramp forever. This checkpoint audits the policy and 3x/5x full-band demos only; it does not add new patterns, change voicing internals, expression numbers, API, Agent, or HarmonyOS.",
        "medium_swing_arrangement_arc_runtime_intent_usage_contract": "v2_6_85 connects the repeat-count-aware Medium Swing arc to runtime style intent. Each ChordRegion receives event-scoped macro-energy metadata and a small piano-comping candidate multiplier based on the user's selected chorus count, including long loops such as 50x. This stays in style/intention policy only: no new pattern vocabulary, no core voicing changes, no expression numeric changes, no API/Agent/HarmonyOS changes, and no 3-chorus hardcoding.",
        "medium_swing_arrangement_arc_runtime_listening_refinement_contract": "v2_6_86 preserves the user-approved v2_6_85 repeat-count-aware arc weighting and adds a listening-refinement checkpoint metadata/audit layer for 3x and 5x full-band demos. It intentionally makes no multiplier, pattern, core voicing, expression numeric, API, Agent, or HarmonyOS behavior change.",
        "medium_swing_full_band_ending_realization_checkpoint_contract": "v2_6_87 audits full-band Medium Swing ending realization after the repeat-count-aware arc is accepted: piano ending subset stability, bass continuity, drum/piano density, explicit 5/6-note low-intrusion, low-register clarity, and dry swing behavior are checked on 3x/5x full-band demos. It includes a generic terminal-ending anticipation guard so the final downbeat is not anticipated away; otherwise it is audit-oriented: no new ending patterns, no multiplier changes, no core voicing changes, no expression numeric changes, no API/Agent/HarmonyOS changes.",
        "medium_swing_style_baseline_phase_completion_checkpoint_contract": "v2_6_88 is a behavior-preserving phase-completion checkpoint for the Medium Swing v2_6_56-v2_6_87 full-band baseline. It summarizes ChordRegion-first piano comping, semantic expression hints, generic anticipation, 2-beat density relief, explicit low-intrusion 5/6-note voicing intent, bass-piano and drum-piano interaction, repeat-count-aware arrangement arcs, and full-band ending realization across 3x/5x demos plus repeat-count simulation. It does not add vocabulary, change weights, modify core voicing, write expression numbers, or touch API/Agent/HarmonyOS.",
        "medium_swing_baseline_handoff_or_next_style_selection_contract": "v2_6_89 is a behavior-preserving handoff checkpoint on the latest v2_10_28 integration baseline. It freezes Medium Swing v2_6_88 as the Engine-line full-band reference unless the user reports a concrete listening issue, keeps all pattern/expression/voicing/API/Agent/HarmonyOS behavior unchanged, and selects Bossa Nova as the default next style baseline audit target.",
        "piano_comping_ending_specific_subset_milestone": "v2_6_70_medium_swing_ending_specific_region_context_candidate_subset_policy",
        "piano_comping_optional_fill_variation_vocabulary_milestone": "v2_6_71_medium_swing_optional_fill_variation_vocabulary_activation",
        "piano_comping_optional_fill_variation_listening_refinement_milestone": "v2_6_72_medium_swing_fill_variation_listening_refinement_after_user_review",
        "piano_comping_phrase_end_fill_context_precision_milestone": "v2_6_73_medium_swing_phrase_end_fill_context_precision",
        "piano_comping_standard_tune_fill_frequency_checkpoint_milestone": "v2_6_74_medium_swing_standard_tune_fill_frequency_checkpoint",
        "medium_swing_piano_comping_phase_completion_checkpoint_milestone": "v2_6_76_medium_swing_piano_comping_phase_completion_checkpoint",
        "medium_swing_existing_voicing_capability_usage_policy_milestone": "v2_6_77_medium_swing_existing_voicing_capability_usage_policy",
        "medium_swing_existing_voicing_capability_low_register_clarity_guard_milestone": "v2_6_78_medium_swing_existing_voicing_capability_low_register_clarity_guard",
        "medium_swing_full_band_listening_checkpoint_milestone": "v2_6_79_medium_swing_full_band_listening_checkpoint_after_low_register_clarity_guard",
        "piano_comping_two_beat_region_density_relief_policy_milestone": "v2_6_80_medium_swing_two_beat_region_density_relief_and_anticipation_audit",
        "piano_comping_two_beat_phrase_pair_policy_milestone": "v2_6_119_medium_swing_two_beat_phrase_pair_local1and_hold",
        "medium_swing_full_band_post_density_relief_checkpoint_milestone": "v2_6_81_medium_swing_full_band_post_density_relief_checkpoint",
        "medium_swing_bass_piano_interaction_audit_milestone": "v2_6_82_medium_swing_bass_piano_interaction_audit",
        "medium_swing_drum_piano_interaction_audit_milestone": "v2_6_83_medium_swing_drum_piano_interaction_audit",
        "medium_swing_repeat_count_aware_arrangement_arc_checkpoint_milestone": "v2_6_84_medium_swing_repeat_count_aware_arrangement_arc_checkpoint",
        "medium_swing_arrangement_arc_runtime_intent_usage_milestone": "v2_6_85_medium_swing_arrangement_arc_runtime_intent_usage",
        "medium_swing_arrangement_arc_runtime_listening_refinement_milestone": "v2_6_86_medium_swing_arrangement_arc_runtime_listening_refinement_checkpoint",
        "medium_swing_full_band_ending_realization_checkpoint_milestone": "v2_6_87_medium_swing_full_band_ending_realization_checkpoint",
        "medium_swing_style_baseline_phase_completion_checkpoint_milestone": "v2_6_88_medium_swing_style_baseline_phase_completion_checkpoint",
        "medium_swing_baseline_handoff_or_next_style_selection_milestone": "v2_6_89_engine_medium_swing_baseline_handoff_or_next_style_selection",
        "piano_region_first_anticipation_compatibility_contract": "Medium Swing anticipation remains region-first: the previous ChordRegion tail slot is computed from region duration, so 4-beat regions use local 4&/3.5, 2-beat regions use local 2&/1.5, and short regions are never forced through a bar-first 4& assumption.",
        "piano_region_first_coverage_guard_contract": "Medium Swing CoverageGuard is region-first and backup-only: it checks selected ChordRegion-local piano comping plans after pattern policy, stamps coverage audit metadata when the region already has piano presence, and inserts a single pitchless region-start fallback anchor only when a ChordRegion would otherwise be uncovered; it never replaces region-length pattern policy or uses bar-first/two-chord-bar routing.",
        "milestone": "v2_6_69_medium_swing_piano_standard_tune_listening_checkpoint",
    }
