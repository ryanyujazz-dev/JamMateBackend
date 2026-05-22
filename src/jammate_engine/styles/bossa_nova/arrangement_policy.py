from __future__ import annotations


BOSSA_NOVA_STYLE_BASELINE_AUDIT_VERSION = "v2_6_90"
BOSSA_NOVA_NON_CORE_RHYTHM_CELL_VOCABULARY_VERSION = "v2_6_91"
BOSSA_NOVA_CONTEXT_ARCHETYPE_POLICY_VERSION = "v2_6_92"
BOSSA_NOVA_ANTICIPATION_TAIL_POLICY_VERSION = "v2_6_93"
BOSSA_NOVA_DISTANCE_AWARE_EXPRESSION_VERSION = "v2_6_94"
BOSSA_NOVA_HARMONIC_RHYTHM_REGION_CLARITY_AND_VOICING_INTENT_VERSION = "v2_6_103"
BOSSA_NOVA_BASS_AND_DRUMS_IDENTITY_AUDIT_VERSION = "v2_6_96"
BOSSA_NOVA_REPEAT_COUNT_ARRANGEMENT_ARC_POLICY_VERSION = "v2_6_97"
BOSSA_NOVA_FULL_BAND_ARRANGEMENT_ARC_LISTENING_REFINEMENT_VERSION = "v2_6_98"
BOSSA_NOVA_STYLE_BASELINE_PHASE_COMPLETION_CHECKPOINT_VERSION = "v2_6_99"
BOSSA_NOVA_DRUM_SHAKER_MICRODYNAMICS_AND_PULSE_SHAPE_VERSION = "v2_6_100"
BOSSA_NOVA_DRUM_CROSS_STICK_PHRASE_LOCAL_CONTOUR_VERSION = "v2_6_101"
BOSSA_NOVA_OPEN_METHOD_POLICY_CORRECTION_VERSION = "v2_6_104"
BOSSA_NOVA_KICK_BASS_LOCK_AND_LOW_FREQUENCY_SHADOW_VERSION = "v2_6_105"
BOSSA_NOVA_LIGHT_MARKER_FILL_POLICY_VERSION = "v2_6_106"
BOSSA_NOVA_DRUM_BASELINE_CHECKPOINT_VERSION = "v2_6_107"
BOSSA_NOVA_BASS_PICKUP_AND_NEXT_ROOT_ANTICIPATION_VERSION = "v2_6_108"
BOSSA_NOVA_BASS_ARTICULATION_AND_REGISTER_POLICY_VERSION = "v2_6_109"
BOSSA_NOVA_TWO_BEAT_PHRASE_PAIR_POLICY_VERSION = "v2_6_120"
BOSSA_NOVA_LONG_SUSTAIN_PATTERN_WEIGHT_CALIBRATION_VERSION = "v2_6_125"


def get_arrangement_policy() -> dict:
    """Bossa Nova style-level arrangement policy and audit metadata.

    v2_6_92 keeps the v2_6_91 non-core Class A/Class B rhythm-cell vocabulary
    and overwrites the earlier simple Bossa weighting with context archetype
    and rolling history metadata inside the existing ChordRegion-first style
    path.  This is not a parallel selector and does not move expression,
    voicing, API, Agent, or HarmonyOS responsibilities.
    """

    return {
        "default_feel": "bossa_nova",
        "opening_core_batida_bars": 2,
        "core_batida_identity_anchor": True,
        "core_batida_identity_anchor_contract": "Opening/pickup identity should be anchored by the style-owned 1,2,3& core_batida cell. Non-core vocabulary must not dilute the first-two-bars identity reset rule.",
        "avoid_immediate_pattern_repeat": True,
        "avoid_immediate_pattern_category_repeat": False,
        "bossa_nova_style_baseline_audit": True,
        "bossa_nova_style_baseline_audit_version": BOSSA_NOVA_STYLE_BASELINE_AUDIT_VERSION,
        "bossa_nova_style_baseline_audit_milestone": "v2_6_90_engine_bossa_nova_style_baseline_audit_from_latest_v2_10_28",
        "bossa_nova_style_baseline_audit_superseded_by": BOSSA_NOVA_CONTEXT_ARCHETYPE_POLICY_VERSION,
        "bossa_nova_non_core_rhythm_cell_vocabulary_active": True,
        "bossa_nova_non_core_rhythm_cell_vocabulary_version": BOSSA_NOVA_NON_CORE_RHYTHM_CELL_VOCABULARY_VERSION,
        "bossa_nova_non_core_rhythm_cell_vocabulary_milestone": "v2_6_91_engine_bossa_nova_non_core_rhythm_cell_vocabulary",
        "bossa_nova_non_core_rhythm_cell_vocabulary_behavior_change": True,
        "bossa_nova_non_core_rhythm_cell_vocabulary_replaces_core_only_runtime": True,
        "bossa_nova_non_core_rhythm_cell_vocabulary_no_parallel_selector": True,
        "bossa_nova_non_core_rhythm_cell_vocabulary_no_bar_first_restore": True,
        "bossa_nova_non_core_rhythm_cell_vocabulary_no_core_voicing_change": True,
        "bossa_nova_non_core_rhythm_cell_vocabulary_no_api_agent_harmonyos_change": True,
        "bossa_nova_non_core_rhythm_cell_vocabulary_expression_numeric_calibration_change": False,
        "bossa_nova_non_core_rhythm_cell_vocabulary_expression_aliases_only": True,
        "bossa_nova_non_core_rhythm_cell_vocabulary_scope": (
            "Activate V2-native Bossa piano non-core rhythm cells in the existing comping_patterns path: "
            "one sole core_batida identity anchor, Class A beat-1-start cells as the ordinary body, Class B 1&-start cells as occasional color, "
            "rare native 4& current-chord cells, and context/history weighting to avoid mechanical repetition."
        ),
        "bossa_nova_non_core_rhythm_cell_vocabulary_contract": (
            "Pattern remains pitchless and ChordRegion-first. Pattern may name semantic expression profile IDs but does not write final velocity, duration, pedal, release, concrete pitch, voicing family, or texture. "
            "Opening first two full bars expose only core_batida; ordinary body excludes mechanical core looping and balances Class A/Class B in-place."
        ),
        "bossa_nova_non_core_rhythm_cell_vocabulary_recommended_next_task": "v2_6_92_engine_bossa_nova_context_archetype_policy_and_history_scorer_refinement",
        "bossa_nova_non_core_rhythm_cell_vocabulary_superseded_by": BOSSA_NOVA_CONTEXT_ARCHETYPE_POLICY_VERSION,
        "bossa_nova_non_core_rhythm_cell_vocabulary_known_next_gap": "Non-core rhythm cells are now active and superseded by v2_6_92 context archetype weighting; articulation remains profile-alias based rather than true distance-sensitive Bossa articulation.",
        "bossa_nova_context_archetype_policy_active": True,
        "bossa_nova_context_archetype_policy_version": BOSSA_NOVA_CONTEXT_ARCHETYPE_POLICY_VERSION,
        "bossa_nova_context_archetype_policy_milestone": "v2_6_92_engine_bossa_nova_context_archetype_policy_and_history_scorer_refinement",
        "bossa_nova_context_archetype_policy_behavior_change": True,
        "bossa_nova_context_archetype_policy_replaces_simple_v2_6_91_weighting": True,
        "bossa_nova_context_archetype_policy_no_parallel_selector": True,
        "bossa_nova_context_archetype_policy_no_bar_first_restore": True,
        "bossa_nova_context_archetype_policy_no_new_pattern_vocabulary": True,
        "bossa_nova_context_archetype_policy_no_core_voicing_change": True,
        "bossa_nova_context_archetype_policy_no_expression_numeric_change": True,
        "bossa_nova_context_archetype_policy_archetypes": (
            "core_batida_anchor",
            "steady_batida_flow",
            "breath_space",
            "response_comping",
            "transition_lift",
            "release",
            "dense_harmonic_marks",
        ),
        "bossa_nova_context_archetype_policy_scope": (
            "Shape the existing Bossa candidate pool through V2-native context archetype multipliers and rolling history metadata: "
            "core_batida_anchor for openings/resets, steady_batida_flow for ordinary body, breath_space for bridge or dense recent history, "
            "response_comping for light answers, transition_lift for cadential/phrase-end push, release for final landing, and dense_harmonic_marks for short ChordRegions."
        ),
        "bossa_nova_context_archetype_policy_contract": (
            "The context archetype policy is an in-place candidate weight rewrite inside styles/bossa_nova/comping_patterns.py. "
            "It preserves the single core_batida and the v2_6_91 Class A/B cell set, does not add a selector, does not restore two_chord_bar/bar-first logic, "
            "does not write final expression values, and does not choose voicing."
        ),
        "bossa_nova_context_archetype_policy_recommended_next_task": "v2_6_93_engine_bossa_nova_anticipation_tail_policy_and_native_4and_audit",
        "bossa_nova_context_archetype_policy_known_next_gap": "Context/history weighting is active and superseded for anticipation-tail behavior by v2_6_93; next pass should do distance-aware expression calibration.",
        "bossa_nova_context_archetype_policy_superseded_for_anticipation_by": BOSSA_NOVA_ANTICIPATION_TAIL_POLICY_VERSION,
        "piano_comping_two_beat_phrase_pair_policy": True,
        "piano_comping_two_beat_phrase_pair_policy_version": BOSSA_NOVA_TWO_BEAT_PHRASE_PAIR_POLICY_VERSION,
        "piano_comping_two_beat_phrase_pair_policy_milestone": "v2_6_120_engine_bossa_nova_two_beat_phrase_pair_local1and_hold",
        "piano_comping_two_beat_phrase_pair_policy_contract": (
            "v2_6_120 enables the shared two-2-beat-ChordRegion phrase-pair weighting for Bossa: "
            "one 2-beat Bossa chord region may use local 1+2, and the following 2-beat region may answer on local 1& with a hold, corresponding to full-bar beat 3&. "
            "The phrase remains pattern-layer, pitchless, ChordRegion-local vocabulary plus history-aware weighting; it does not restore bar-first/two-chord-bar routing or touch voicing/expression internals/API/Agent/HarmonyOS."
        ),
        "bossa_nova_two_beat_phrase_pair_policy_active": True,
        "bossa_nova_two_beat_phrase_pair_policy_version": BOSSA_NOVA_TWO_BEAT_PHRASE_PAIR_POLICY_VERSION,
        "bossa_nova_two_beat_phrase_pair_policy_behavior_change": True,
        "bossa_nova_two_beat_phrase_pair_policy_tracks": ("piano",),
        "bossa_nova_two_beat_phrase_pair_policy_no_parallel_selector": True,
        "bossa_nova_two_beat_phrase_pair_policy_no_bar_first_restore": True,
        "bossa_nova_two_beat_phrase_pair_policy_no_voicing_change": True,
        "bossa_nova_two_beat_phrase_pair_policy_no_expression_numeric_change": True,
        "bossa_nova_two_beat_phrase_pair_policy_no_api_agent_harmonyos_change": True,
        "bossa_nova_two_beat_phrase_pair_policy_recommended_next_task": "v2_6_121_engine_bossa_nova_two_beat_phrase_pair_listening_calibration",

        "bossa_nova_long_sustain_pattern_weight_calibration_active": True,
        "bossa_nova_long_sustain_pattern_weight_calibration_version": BOSSA_NOVA_LONG_SUSTAIN_PATTERN_WEIGHT_CALIBRATION_VERSION,
        "bossa_nova_long_sustain_pattern_weight_calibration_milestone": "v2_6_125_engine_bossa_nova_long_sustain_pattern_weight_calibration",
        "bossa_nova_long_sustain_pattern_weight_calibration_scope": (
            "Reduce the frequency of Bossa long-hold rhythm cells by adjusting style-owned piano comping pattern weights only. "
            "This preserves core_batida, Class A/Class B vocabulary, two-beat phrase-pair vocabulary, expression numeric profiles, voicing, OPEN/SPREAD routing, bass/drums, API, Agent, and HarmonyOS."
        ),
        "bossa_nova_long_sustain_pattern_weight_calibration_no_voicing_change": True,
        "bossa_nova_long_sustain_pattern_weight_calibration_no_expression_numeric_change": True,
        "bossa_nova_long_sustain_pattern_weight_calibration_no_new_pattern_vocabulary": True,
        "bossa_nova_long_sustain_pattern_weight_calibration_no_open_or_generic_change": True,
        "bossa_nova_anticipation_tail_policy_active": True,
        "bossa_nova_anticipation_tail_policy_version": BOSSA_NOVA_ANTICIPATION_TAIL_POLICY_VERSION,
        "bossa_nova_anticipation_tail_policy_milestone": "v2_6_93_engine_bossa_nova_anticipation_tail_policy_and_native_4and_audit",
        "bossa_nova_anticipation_tail_policy_behavior_change": True,
        "bossa_nova_anticipation_tail_policy_no_parallel_engine": True,
        "bossa_nova_anticipation_tail_policy_no_pattern_embedded_anticipation": True,
        "bossa_nova_anticipation_tail_policy_no_bar_first_restore": True,
        "bossa_nova_anticipation_tail_policy_no_core_voicing_change": True,
        "bossa_nova_anticipation_tail_policy_no_expression_numeric_change": True,
        "bossa_nova_anticipation_tail_policy_requires_previous_beat4_empty": True,
        "bossa_nova_anticipation_tail_policy_requires_previous_4and_empty": True,
        "bossa_nova_anticipation_tail_policy_preserves_native_4and": True,
        "bossa_nova_anticipation_tail_policy_min_previous_region_duration_beats": 3.75,
        "bossa_nova_anticipation_tail_policy_scope": (
            "Use the shared core AnticipationResolver with a Bossa-specific full-region tail gate: "
            "the previous piano harmonic tail must have both beat 4 and 4& empty, native 4& current-chord cells must occupy the 4& slot and block anticipation, "
            "and short/dense ChordRegions should not receive Bossa piano anticipation."
        ),
        "bossa_nova_anticipation_tail_policy_contract": (
            "This is an in-place style policy refinement, not a new anticipation engine. Pattern candidates remain pitchless and only expose beat-1 movability; "
            "the shared AnticipationResolver performs the timeline rewrite before Expression and Voicing."
        ),
        "bossa_nova_anticipation_tail_policy_recommended_next_task": "v2_6_94_engine_bossa_nova_distance_aware_expression_calibration",
        "bossa_nova_anticipation_tail_policy_known_next_gap": "Anticipation tail/native-4& separation is audited and superseded for expression behavior by v2_6_94 distance-aware calibration.",
        "bossa_nova_anticipation_tail_policy_superseded_for_expression_by": BOSSA_NOVA_DISTANCE_AWARE_EXPRESSION_VERSION,
        "bossa_nova_distance_aware_expression_active": True,
        "bossa_nova_distance_aware_expression_version": BOSSA_NOVA_DISTANCE_AWARE_EXPRESSION_VERSION,
        "bossa_nova_distance_aware_expression_milestone": "v2_6_94_engine_bossa_nova_distance_aware_expression_calibration",
        "bossa_nova_distance_aware_expression_behavior_change": True,
        "bossa_nova_distance_aware_expression_no_parallel_resolver": True,
        "bossa_nova_distance_aware_expression_no_style_specific_runtime": True,
        "bossa_nova_distance_aware_expression_no_pattern_numeric_values": True,
        "bossa_nova_distance_aware_expression_no_new_pattern_vocabulary": True,
        "bossa_nova_distance_aware_expression_no_core_voicing_change": True,
        "bossa_nova_distance_aware_expression_no_api_agent_harmonyos_change": True,
        "bossa_nova_distance_aware_expression_resolver_hook": "ExpressionResolver.policy_driven_distance_articulation",
        "bossa_nova_distance_aware_expression_threshold_beats": 1.0,
        "bossa_nova_distance_aware_expression_scope": (
            "Replace the v2_6_91 alias-only non-core Bossa cell expression with policy-driven distance articulation: "
            "after anticipation rewrites the pitchless timeline, the shared core ExpressionResolver makes close gaps short and wider gaps sustain, "
            "then keeps durations clamped to the next piano touch and current ChordRegion boundary."
        ),
        "bossa_nova_distance_aware_expression_contract": (
            "This is an in-place expression policy calibration. Pattern candidates still only carry semantic expression hints and do not write final MIDI velocity, duration, pedal, release, pitch, or voicing. "
            "No Bossa-specific resolver or parallel runtime is introduced."
        ),
        "bossa_nova_distance_aware_expression_profiles": (
            "cell_close_gap_short",
            "cell_soft_hold",
            "anticipation_light",
            "dense_light_mark",
            "release_soft",
        ),
        "bossa_nova_distance_aware_expression_recommended_next_task": "v2_6_95_engine_bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_audit",
        "bossa_nova_distance_aware_expression_known_next_gap": "Bossa non-core piano touch is distance-aware; the earlier v2_6_95 forced low-density short-region voicing intent is superseded by v2_6_102.",
        "bossa_nova_distance_aware_expression_superseded_for_voicing_intent_by": BOSSA_NOVA_HARMONIC_RHYTHM_REGION_CLARITY_AND_VOICING_INTENT_VERSION,
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_active": True,
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_version": BOSSA_NOVA_HARMONIC_RHYTHM_REGION_CLARITY_AND_VOICING_INTENT_VERSION,
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_milestone": "v2_6_103_engine_bossa_nova_open_voicing_and_retire_4note_grouping_metadata",
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_behavior_change": True,
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_parallel_selector": True,
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_bar_first_restore": True,
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_new_pattern_vocabulary": True,
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_expression_numeric_change": True,
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_core_voicing_change": True,
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_forced_2_note_voicing": True,
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_forced_3_note_voicing": True,
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_ordinary_voicing_policy_for_short_regions": True,
        "bossa_nova_open_voicing_main_policy_active": True,
        "bossa_nova_open_voicing_main_policy_version": BOSSA_NOVA_HARMONIC_RHYTHM_REGION_CLARITY_AND_VOICING_INTENT_VERSION,
        "bossa_nova_open_voicing_main_policy_preferred_disposition": "open",
        "bossa_nova_open_voicing_main_policy_ordinary_body_no_spread_grouping": True,
        "bossa_nova_spread_5note_low_weight_policy_active": True,
        "bossa_nova_spread_5note_low_weight_policy_version": "v2_6_123",
        "bossa_nova_spread_5note_low_weight_policy_scope": "low-frequency event-scoped grouped-SPREAD 2+3 color; ordinary Bossa body remains OPEN/drop-family 4-note; generic_open remains fallback-only",
        "bossa_nova_retired_ordinary_4note_grouping_metadata": True,
        "bossa_nova_retired_ordinary_4note_grouping_metadata_version": BOSSA_NOVA_HARMONIC_RHYTHM_REGION_CLARITY_AND_VOICING_INTENT_VERSION,
        "bossa_nova_open_method_policy_correction_active": True,
        "bossa_nova_open_method_policy_correction_version": BOSSA_NOVA_OPEN_METHOD_POLICY_CORRECTION_VERSION,
        "bossa_nova_open_method_policy_correction_milestone": "v2_6_104_engine_bossa_nova_drop_family_open_method_policy_correction",
        "bossa_nova_open_method_policy_correction_scope": "Remove generic_open from ordinary Bossa OPEN method pool and return method priority to the shared drop-family consensus: drop2 primary, drop3 secondary, drop2&4 very low, generic_open fallback-only.",
        "bossa_nova_open_method_policy_correction_no_projection_algorithm_change": True,
        "bossa_nova_open_method_policy_correction_no_source_inventory_change": True,
        "bossa_nova_open_method_policy_correction_no_parallel_selector": True,
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_api_agent_harmonyos_change": True,
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_dense_short_region_threshold_beats": 2.25,
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_scope": (
            "Audit and refine Bossa dense harmonic-rhythm / short ChordRegion clarity in place: short regions must stay ChordRegion-first, "
            "use normal 4-to-5-note Bossa voicing, avoid forced 2-note/3-note density, make OPEN the runtime-main voicing family, "
            "and retire ordinary 4-note 1+3/2+2 grouping metadata from core taxonomy."
        ),
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_contract": (
            "This is a style-level VoicingPolicy intent plus core taxonomy cleanup. It does not add pattern vocabulary, restore two_chord_bar/bar-first routing, "
            "write expression values in patterns, create a Bossa selector, or introduce SPREAD grouped voicing as the ordinary body. v2_6_123 allows only low-frequency event-scoped SPREAD 2+3 five-note color through existing capability. The realization adapter only attaches event-scoped policy metadata; "
            "ordinary 4-note CLOSED/OPEN stacks are no longer reported as 1+3/2+2 grouped voicings."
        ),
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_recommended_next_task": "v2_6_105_engine_bossa_nova_kick_bass_lock_and_low_frequency_shadow_refinement",
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_known_next_gap": "Bossa now uses OPEN as the normal 4-to-5-note voicing family and no longer reports ordinary 4-note stacks as grouped voicings; next Bossa drum task can return to kick/bass lock and low-frequency shadow refinement.",
        "bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_superseded_for_full_band_identity_by": BOSSA_NOVA_BASS_AND_DRUMS_IDENTITY_AUDIT_VERSION,
        "bossa_nova_bass_and_drums_identity_audit_active": True,
        "bossa_nova_bass_and_drums_identity_audit_version": BOSSA_NOVA_BASS_AND_DRUMS_IDENTITY_AUDIT_VERSION,
        "bossa_nova_bass_and_drums_identity_audit_milestone": "v2_6_96_engine_bossa_nova_bass_and_drums_identity_audit",
        "bossa_nova_bass_and_drums_identity_audit_behavior_change": True,
        "bossa_nova_bass_and_drums_identity_audit_no_parallel_selector": True,
        "bossa_nova_bass_and_drums_identity_audit_no_bar_first_restore": True,
        "bossa_nova_bass_and_drums_identity_audit_no_piano_pattern_change": True,
        "bossa_nova_bass_and_drums_identity_audit_no_expression_numeric_change": True,
        "bossa_nova_bass_and_drums_identity_audit_no_core_voicing_change": True,
        "bossa_nova_bass_and_drums_identity_audit_no_api_agent_harmonyos_change": True,
        "bossa_nova_bass_identity": "root_fifth_support_not_walking",
        "bossa_nova_drums_identity": "shaker_cross_stick_light_kick",
        "bossa_nova_bass_and_drums_identity_audit_scope": (
            "Replace the old Bossa one-size bass root/fifth candidate and drums hihat placeholder in place. "
            "Bass stays ChordRegion-first: full regions use root/fifth support, while split/short regions state root only and do not walk. "
            "Drums use region-local shaker, cross-stick, and light kick semantic voices instead of swing ride or rock backbeat placeholders."
        ),
        "bossa_nova_bass_and_drums_identity_audit_contract": (
            "This is a style-owned bass/percussion identity pass. Pattern candidates remain pitchless/semantic and do not write concrete MIDI pitches; "
            "realization only maps existing abstract drum/length/dynamic profiles to MIDI. No Bossa parallel engine, piano vocabulary change, core voicing change, API, Agent, or HarmonyOS change is introduced."
        ),
        "bossa_nova_bass_and_drums_identity_audit_recommended_next_task": "v2_6_97_engine_bossa_nova_repeat_count_arrangement_arc_policy",
        "bossa_nova_bass_and_drums_identity_audit_superseded_for_arrangement_arc_by": BOSSA_NOVA_REPEAT_COUNT_ARRANGEMENT_ARC_POLICY_VERSION,
        "bossa_nova_repeat_count_arrangement_arc_policy_active": True,
        "bossa_nova_repeat_count_arrangement_arc_policy_version": BOSSA_NOVA_REPEAT_COUNT_ARRANGEMENT_ARC_POLICY_VERSION,
        "bossa_nova_repeat_count_arrangement_arc_policy_milestone": "v2_6_97_engine_bossa_nova_repeat_count_arrangement_arc_policy",
        "bossa_nova_repeat_count_arrangement_arc_policy_behavior_change": True,
        "bossa_nova_repeat_count_arrangement_arc_policy_no_parallel_selector": True,
        "bossa_nova_repeat_count_arrangement_arc_policy_no_bar_first_restore": True,
        "bossa_nova_repeat_count_arrangement_arc_policy_no_new_pattern_vocabulary": True,
        "bossa_nova_repeat_count_arrangement_arc_policy_no_expression_numeric_change": True,
        "bossa_nova_repeat_count_arrangement_arc_policy_no_core_voicing_change": True,
        "bossa_nova_repeat_count_arrangement_arc_policy_no_api_agent_harmonyos_change": True,
        "bossa_nova_repeat_count_arrangement_arc_policy_not_medium_swing_clone": True,
        "bossa_nova_repeat_count_arrangement_arc_policy_repeat_counts_audited": (1, 2, 3, 5, 10, 50),
        "bossa_nova_repeat_count_arrangement_arc_policy_scope": (
            "Add a Bossa-owned repeat-count-aware arrangement arc in place. The policy maps arbitrary user-selected chorus counts "
            "to light Bossa phases such as core identity, warm flow, breath, gentle lift, soft release, and long-loop wave reset. "
            "It only shapes existing piano comping candidates through small semantic multipliers and event metadata."
        ),
        "bossa_nova_repeat_count_arrangement_arc_policy_contract": (
            "This is a style-level arrangement intent policy, not a new selector or runtime. It does not add Bossa rhythm vocabulary, "
            "restore two_chord_bar/bar-first routing, write expression numbers, choose voicing sources, or touch API/Agent/HarmonyOS. "
            "Long loops are explicitly non-monotonic and must not become a Medium Swing-style energy ramp."
        ),
        "bossa_nova_repeat_count_arrangement_arc_policy_recommended_next_task": "v2_6_98_engine_bossa_nova_full_band_arrangement_arc_listening_refinement",
        "bossa_nova_repeat_count_arrangement_arc_policy_superseded_for_full_band_refinement_by": BOSSA_NOVA_FULL_BAND_ARRANGEMENT_ARC_LISTENING_REFINEMENT_VERSION,
        "bossa_nova_full_band_arrangement_arc_listening_refinement_active": True,
        "bossa_nova_full_band_arrangement_arc_listening_refinement_version": BOSSA_NOVA_FULL_BAND_ARRANGEMENT_ARC_LISTENING_REFINEMENT_VERSION,
        "bossa_nova_full_band_arrangement_arc_listening_refinement_milestone": "v2_6_98_engine_bossa_nova_full_band_arrangement_arc_listening_refinement",
        "bossa_nova_full_band_arrangement_arc_listening_refinement_behavior_change": True,
        "bossa_nova_full_band_arrangement_arc_listening_refinement_no_parallel_selector": True,
        "bossa_nova_full_band_arrangement_arc_listening_refinement_no_bar_first_restore": True,
        "bossa_nova_full_band_arrangement_arc_listening_refinement_no_new_pattern_vocabulary": True,
        "bossa_nova_full_band_arrangement_arc_listening_refinement_no_core_voicing_change": True,
        "bossa_nova_full_band_arrangement_arc_listening_refinement_no_api_agent_harmonyos_change": True,
        "bossa_nova_full_band_arrangement_arc_listening_refinement_scope": (
            "Refine the user-facing full-band result of the Bossa repeat-count arc in place: piano already receives arc candidate metadata, "
            "and v2_6_98 now lets bass and drums read the same style arc intent so breath/release phases become lighter and gentle-lift phases breathe forward without becoming swing/rock or walking."
        ),
        "bossa_nova_full_band_arrangement_arc_listening_refinement_contract": (
            "This is a style-owned full-band arc refinement. It directly updates existing Bossa bass/percussion pattern metadata and semantic dynamic profiles. "
            "It does not add rhythm vocabulary, create a selector, restore bar-first routing, alter core voicing, or touch API/Agent/HarmonyOS."
        ),
        "bossa_nova_full_band_arrangement_arc_listening_refinement_tracks": ("piano", "bass", "drums"),
        "bossa_nova_full_band_arrangement_arc_listening_refinement_recommended_next_task": "v2_6_99_engine_bossa_nova_style_baseline_phase_completion_checkpoint",
        "bossa_nova_full_band_arrangement_arc_listening_refinement_superseded_for_phase_completion_by": BOSSA_NOVA_STYLE_BASELINE_PHASE_COMPLETION_CHECKPOINT_VERSION,
        "bossa_nova_style_baseline_phase_completion_checkpoint": True,
        "bossa_nova_style_baseline_phase_completion_checkpoint_version": BOSSA_NOVA_STYLE_BASELINE_PHASE_COMPLETION_CHECKPOINT_VERSION,
        "bossa_nova_style_baseline_phase_completion_checkpoint_milestone": "v2_6_99_engine_bossa_nova_style_baseline_phase_completion_checkpoint",
        "bossa_nova_style_baseline_phase_completion_checkpoint_behavior_change": False,
        "bossa_nova_style_baseline_phase_completion_checkpoint_no_parallel_selector": True,
        "bossa_nova_style_baseline_phase_completion_checkpoint_no_bar_first_restore": True,
        "bossa_nova_style_baseline_phase_completion_checkpoint_no_new_pattern_vocabulary": True,
        "bossa_nova_style_baseline_phase_completion_checkpoint_no_expression_numeric_change": True,
        "bossa_nova_style_baseline_phase_completion_checkpoint_no_core_voicing_change": True,
        "bossa_nova_style_baseline_phase_completion_checkpoint_no_api_agent_harmonyos_change": True,
        "bossa_nova_style_baseline_phase_completion_checkpoint_tracks": ("piano", "bass", "drums"),
        "bossa_nova_style_baseline_phase_completion_checkpoint_completed_versions": (
            BOSSA_NOVA_STYLE_BASELINE_AUDIT_VERSION,
            BOSSA_NOVA_NON_CORE_RHYTHM_CELL_VOCABULARY_VERSION,
            BOSSA_NOVA_CONTEXT_ARCHETYPE_POLICY_VERSION,
            BOSSA_NOVA_ANTICIPATION_TAIL_POLICY_VERSION,
            BOSSA_NOVA_DISTANCE_AWARE_EXPRESSION_VERSION,
            BOSSA_NOVA_HARMONIC_RHYTHM_REGION_CLARITY_AND_VOICING_INTENT_VERSION,
            BOSSA_NOVA_BASS_AND_DRUMS_IDENTITY_AUDIT_VERSION,
            BOSSA_NOVA_REPEAT_COUNT_ARRANGEMENT_ARC_POLICY_VERSION,
            BOSSA_NOVA_FULL_BAND_ARRANGEMENT_ARC_LISTENING_REFINEMENT_VERSION,
        ),
        "bossa_nova_style_baseline_phase_completion_checkpoint_scope": (
            "Summarize and freeze the Bossa Nova v2_6_90-v2_6_98 full-band baseline: sole core_batida identity anchor, Class A/B piano cells, "
            "context/history weighting, strict native-4&/anticipation tail policy, distance-aware expression, ChordRegion-first dense-region rhythm clarity with normal 4-to-5-note voicing, "
            "root/fifth bass support, shaker/cross-stick/light-kick drums, and Bossa-owned repeat-count full-band arc."
        ),
        "bossa_nova_style_baseline_phase_completion_checkpoint_contract": (
            "v2_6_99 is a metadata/audit/demo checkpoint only. It does not add pattern vocabulary, change candidate weights, alter expression numeric calibration, "
            "modify core voicing, restore bar-first/two_chord_bar routing, create a parallel selector, or touch API/Agent/HarmonyOS."
        ),
        "bossa_nova_style_baseline_phase_completion_checkpoint_recommended_next_task": "v2_6_100_engine_bossa_nova_drum_shaker_microdynamics_and_pulse_shape",
        "bossa_nova_drum_shaker_microdynamics_and_pulse_shape_active": True,
        "bossa_nova_drum_shaker_microdynamics_and_pulse_shape_version": BOSSA_NOVA_DRUM_SHAKER_MICRODYNAMICS_AND_PULSE_SHAPE_VERSION,
        "bossa_nova_drum_shaker_microdynamics_and_pulse_shape_milestone": "v2_6_100_engine_bossa_nova_drum_shaker_microdynamics_and_pulse_shape",
        "bossa_nova_drum_shaker_microdynamics_and_pulse_shape_behavior_change": True,
        "bossa_nova_drum_shaker_microdynamics_and_pulse_shape_no_parallel_selector": True,
        "bossa_nova_drum_shaker_microdynamics_and_pulse_shape_no_bar_first_restore": True,
        "bossa_nova_drum_shaker_microdynamics_and_pulse_shape_no_new_pattern_vocabulary": True,
        "bossa_nova_drum_shaker_microdynamics_and_pulse_shape_no_piano_bass_voicing_change": True,
        "bossa_nova_drum_shaker_microdynamics_and_pulse_shape_no_api_agent_harmonyos_change": True,
        "bossa_nova_drum_shaker_microdynamics_and_pulse_shape_tracks": ("drums",),
        "bossa_nova_drum_shaker_microdynamics_and_pulse_shape_scope": (
            "Refine the existing Bossa shaker/hi-hat proxy in place by adding semantic straight-8th pulse slots and a shared percussion-realizer microdynamic velocity shape. "
            "The pattern candidate shape remains shaker/cross-stick/light-kick identity; the pattern layer does not write MIDI velocity values."
        ),
        "bossa_nova_drum_shaker_microdynamics_and_pulse_shape_contract": (
            "This is a drum expression/realization refinement only. It does not add drum pattern vocabulary, create a parallel selector, restore bar-first routing, "
            "change piano/bass/voicing/API/Agent/HarmonyOS, or turn Bossa drums into swing/rock fills."
        ),
        "bossa_nova_drum_shaker_microdynamics_and_pulse_shape_recommended_next_task": "v2_6_101_engine_bossa_nova_cross_stick_phrase_local_contour_refinement",
        "bossa_nova_drum_cross_stick_phrase_local_contour_active": True,
        "bossa_nova_drum_cross_stick_phrase_local_contour_version": BOSSA_NOVA_DRUM_CROSS_STICK_PHRASE_LOCAL_CONTOUR_VERSION,
        "bossa_nova_drum_cross_stick_phrase_local_contour_milestone": "v2_6_101_engine_bossa_nova_cross_stick_phrase_local_contour_refinement",
        "bossa_nova_drum_cross_stick_phrase_local_contour_behavior_change": True,
        "bossa_nova_drum_cross_stick_phrase_local_contour_no_parallel_selector": True,
        "bossa_nova_drum_cross_stick_phrase_local_contour_no_bar_first_restore": True,
        "bossa_nova_drum_cross_stick_phrase_local_contour_no_new_pattern_vocabulary": True,
        "bossa_nova_drum_cross_stick_phrase_local_contour_no_piano_bass_voicing_change": True,
        "bossa_nova_drum_cross_stick_phrase_local_contour_no_api_agent_harmonyos_change": True,
        "bossa_nova_drum_cross_stick_phrase_local_contour_tracks": ("drums",),
        "bossa_nova_drum_cross_stick_phrase_local_contour_scope": (
            "Refine the existing Bossa cross-stick layer in place. Keep the same shaker/cross-stick/light-kick percussion candidate, "
            "derive A/B from phrase-local source-bar position, attach semantic phrase slots to cross-stick events, and use arc-aware light subtraction so breath/release phases stop pushing the tail."
        ),
        "bossa_nova_drum_cross_stick_phrase_local_contour_contract": (
            "This is a drum phrase-contour refinement only. It does not add percussion vocabulary, create a parallel selector, restore bar-first templates, "
            "change piano/bass/voicing/API/Agent/HarmonyOS, or turn Bossa drums into swing/rock fills. Pattern events carry semantic slots only; the shared percussion realizer maps them to velocity shape."
        ),
        "bossa_nova_drum_cross_stick_phrase_local_contour_recommended_next_task": "v2_6_102_engine_bossa_nova_no_forced_2_or_3_note_voicing_policy",

        "bossa_nova_kick_bass_lock_and_low_frequency_shadow_active": True,
        "bossa_nova_kick_bass_lock_and_low_frequency_shadow_version": BOSSA_NOVA_KICK_BASS_LOCK_AND_LOW_FREQUENCY_SHADOW_VERSION,
        "bossa_nova_kick_bass_lock_and_low_frequency_shadow_milestone": "v2_6_105_engine_bossa_nova_kick_bass_lock_and_low_frequency_shadow_refinement",
        "bossa_nova_kick_bass_lock_and_low_frequency_shadow_behavior_change": True,
        "bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_parallel_selector": True,
        "bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_bar_first_restore": True,
        "bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_new_drum_vocabulary": True,
        "bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_piano_voicing_change": True,
        "bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_core_voicing_change": True,
        "bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_api_agent_harmonyos_change": True,
        "bossa_nova_kick_bass_lock_and_low_frequency_shadow_tracks": ("bass", "drums"),
        "bossa_nova_kick_bass_lock_and_low_frequency_shadow_scope": (
            "Refine the existing Bossa low-frequency layer in place. Bass remains root/fifth support and kick remains a low-velocity shadow locked to the bass root/fifth beats; "
            "split/short ChordRegions stay root-only and do not add fifth or four-on-floor drive. Pattern events carry semantic lock/shadow metadata only; the shared percussion realizer maps those slots to tiny velocity shape."
        ),
        "bossa_nova_kick_bass_lock_and_low_frequency_shadow_contract": (
            "This is a bass/drum relationship refinement only. It does not add a percussion selector, restore bar-first templates, add swing/rock kick patterns, "
            "change piano rhythm, change voicing, or touch API/Agent/HarmonyOS. The kick is a shadow under the bass, not a dance/rock low-frequency driver."
        ),
        "bossa_nova_kick_bass_lock_and_low_frequency_shadow_recommended_next_task": "v2_6_106_engine_bossa_nova_light_marker_fill_policy",
        "bossa_nova_light_marker_fill_policy_active": True,
        "bossa_nova_light_marker_fill_policy_version": BOSSA_NOVA_LIGHT_MARKER_FILL_POLICY_VERSION,
        "bossa_nova_light_marker_fill_policy_milestone": "v2_6_106_engine_bossa_nova_light_marker_fill_policy",
        "bossa_nova_light_marker_fill_policy_behavior_change": True,
        "bossa_nova_light_marker_fill_policy_no_parallel_selector": True,
        "bossa_nova_light_marker_fill_policy_no_bar_first_restore": True,
        "bossa_nova_light_marker_fill_policy_no_new_drum_selector": True,
        "bossa_nova_light_marker_fill_policy_no_tom_crash_roll_fill": True,
        "bossa_nova_light_marker_fill_policy_no_swing_or_rock_fill": True,
        "bossa_nova_light_marker_fill_policy_no_piano_bass_voicing_change": True,
        "bossa_nova_light_marker_fill_policy_no_api_agent_harmonyos_change": True,
        "bossa_nova_light_marker_fill_policy_tracks": ("drums",),
        "bossa_nova_light_marker_fill_policy_allowed_marker_kinds": ("phrase_end_micro", "turnaround_light", "ending_soft"),
        "bossa_nova_light_marker_fill_policy_scope": (
            "Add extremely sparse Bossa rim-click markers for phrase-end, turnaround/gentle-lift, and final release contexts inside the existing percussion candidate. "
            "Markers remain semantic cross-stick events; they are not tom/crash/roll fills and they do not create a parallel selector."
        ),
        "bossa_nova_light_marker_fill_policy_contract": (
            "This is a drum marker refinement only. It does not add a drum selector, restore bar-first templates, change piano/bass/voicing, "
            "or touch API/Agent/HarmonyOS. Pattern events carry marker slots only; the shared percussion realizer maps them to light rim-click velocities."
        ),
        "bossa_nova_light_marker_fill_policy_recommended_next_task": "v2_6_107_engine_bossa_nova_drum_baseline_checkpoint_or_listening_refinement",
        "bossa_nova_drum_baseline_checkpoint_active": True,
        "bossa_nova_drum_baseline_checkpoint_version": BOSSA_NOVA_DRUM_BASELINE_CHECKPOINT_VERSION,
        "bossa_nova_drum_baseline_checkpoint_milestone": "v2_6_107_engine_bossa_nova_drum_baseline_checkpoint_or_listening_refinement",
        "bossa_nova_drum_baseline_checkpoint_behavior_change": False,
        "bossa_nova_drum_baseline_checkpoint_no_parallel_selector": True,
        "bossa_nova_drum_baseline_checkpoint_no_bar_first_restore": True,
        "bossa_nova_drum_baseline_checkpoint_no_new_drum_vocabulary": True,
        "bossa_nova_drum_baseline_checkpoint_no_piano_bass_voicing_change": True,
        "bossa_nova_drum_baseline_checkpoint_no_core_voicing_change": True,
        "bossa_nova_drum_baseline_checkpoint_no_api_agent_harmonyos_change": True,
        "bossa_nova_drum_baseline_checkpoint_tracks": ("drums",),
        "bossa_nova_drum_baseline_checkpoint_completed_versions": (
            BOSSA_NOVA_DRUM_SHAKER_MICRODYNAMICS_AND_PULSE_SHAPE_VERSION,
            BOSSA_NOVA_DRUM_CROSS_STICK_PHRASE_LOCAL_CONTOUR_VERSION,
            BOSSA_NOVA_KICK_BASS_LOCK_AND_LOW_FREQUENCY_SHADOW_VERSION,
            BOSSA_NOVA_LIGHT_MARKER_FILL_POLICY_VERSION,
        ),
        "bossa_nova_drum_baseline_checkpoint_scope": (
            "Checkpoint and freeze the Bossa drum baseline after shaker microdynamics, cross-stick phrase-local contour, kick/bass lock, and sparse light marker policy. "
            "This is a metadata/audit/demo pass only and does not add new drum behavior."
        ),
        "bossa_nova_drum_baseline_checkpoint_contract": (
            "Bossa drums remain shaker/cross-stick/light-kick with sparse rim-click markers. This checkpoint does not add a selector, restore bar-first templates, "
            "write pattern-layer MIDI values, change piano/bass/voicing, or touch API/Agent/HarmonyOS."
        ),
        "bossa_nova_drum_baseline_checkpoint_recommended_next_task": "v2_6_108_engine_bossa_nova_bass_pickup_and_next_root_anticipation_policy",
        "bossa_nova_bass_pickup_and_next_root_anticipation_active": True,
        "bossa_nova_bass_pickup_and_next_root_anticipation_version": BOSSA_NOVA_BASS_PICKUP_AND_NEXT_ROOT_ANTICIPATION_VERSION,
        "bossa_nova_bass_pickup_and_next_root_anticipation_milestone": "v2_6_108_engine_bossa_nova_bass_pickup_and_next_root_anticipation_policy",
        "bossa_nova_bass_pickup_and_next_root_anticipation_behavior_change": True,
        "bossa_nova_bass_pickup_and_next_root_anticipation_no_parallel_selector": True,
        "bossa_nova_bass_pickup_and_next_root_anticipation_no_bar_first_restore": True,
        "bossa_nova_bass_pickup_and_next_root_anticipation_no_walking_bass": True,
        "bossa_nova_bass_pickup_and_next_root_anticipation_no_piano_pattern_change": True,
        "bossa_nova_bass_pickup_and_next_root_anticipation_no_core_voicing_change": True,
        "bossa_nova_bass_pickup_and_next_root_anticipation_no_api_agent_harmonyos_change": True,
        "bossa_nova_bass_pickup_and_next_root_anticipation_tracks": ("bass",),
        "bossa_nova_bass_pickup_and_next_root_anticipation_scope": (
            "Refine the existing Bossa bass foundation in place: keep root/fifth support as the skeleton, "
            "allow occasional 2& fifth pickup and controlled 4& next-root anticipation only on full ChordRegions, "
            "keep split/short ChordRegions root-only, and keep kick as a root/fifth shadow rather than following pickup events."
        ),
        "bossa_nova_bass_pickup_and_next_root_anticipation_contract": (
            "This is a Bossa bass pattern-policy and semantic-realization refinement only. Pattern events carry degree tokens and semantic length/dynamic profiles; "
            "they do not write concrete MIDI pitch, velocity, or duration. The change does not create a parallel selector, restore bar-first templates, "
            "turn Bossa bass into walking, alter piano/voicing/API/Agent/HarmonyOS, or make kick follow every pickup."
        ),
        "bossa_nova_bass_pickup_and_next_root_anticipation_recommended_next_task": "v2_6_109_engine_bossa_nova_bass_articulation_and_register_policy",
        "bossa_nova_bass_articulation_and_register_policy_active": True,
        "bossa_nova_bass_articulation_and_register_policy_version": BOSSA_NOVA_BASS_ARTICULATION_AND_REGISTER_POLICY_VERSION,
        "bossa_nova_bass_articulation_and_register_policy_milestone": "v2_6_109_engine_bossa_nova_bass_articulation_and_register_policy",
        "bossa_nova_bass_articulation_and_register_policy_behavior_change": True,
        "bossa_nova_bass_articulation_and_register_policy_no_parallel_selector": True,
        "bossa_nova_bass_articulation_and_register_policy_no_new_bass_engine": True,
        "bossa_nova_bass_articulation_and_register_policy_no_bar_first_restore": True,
        "bossa_nova_bass_articulation_and_register_policy_no_walking_bass": True,
        "bossa_nova_bass_articulation_and_register_policy_no_piano_pattern_change": True,
        "bossa_nova_bass_articulation_and_register_policy_no_core_voicing_change": True,
        "bossa_nova_bass_articulation_and_register_policy_no_api_agent_harmonyos_change": True,
        "bossa_nova_bass_articulation_and_register_policy_tracks": ("bass",),
        "bossa_nova_bass_articulation_and_register_policy_scope": (
            "Refine the existing Bossa bass foundation in place after v2_6_108 pickup/next-root policy: "
            "keep the same root/fifth/pickup/next-root candidate set, calibrate semantic length/dynamic profiles for close pickups, "
            "and attach register policy intent so fifth projection can stay smooth or repeat root when a fifth would leap or muddy the low register."
        ),
        "bossa_nova_bass_articulation_and_register_policy_contract": (
            "This does not create a new bass engine, selector, or bar-first template. Pattern events still carry only pitchless degree tokens plus semantic length/dynamic/register profile IDs; "
            "the existing BassFoundationRealizer maps those profiles to concrete note durations and register choices. No piano, voicing, API, Agent, or HarmonyOS behavior is changed."
        ),
        "bossa_nova_bass_articulation_and_register_policy_recommended_next_task": "v2_6_110_engine_bossa_nova_bass_listening_refinement_or_checkpoint",
    }



def resolve_repeat_count_arrangement_arc(chorus_index: int, total_choruses: int) -> dict:
    """Return a Bossa-owned repeat-count-aware macro arrangement intent.

    The policy is intentionally lighter than Medium Swing.  It keeps Bossa as a
    warm, steady, non-walking, non-swing comping style and uses repeat waves for
    long practice loops instead of a monotonic build.
    """

    total = max(1, int(total_choruses or 1))
    idx = max(0, min(int(chorus_index or 0), total - 1))
    position = 0.0 if total <= 1 else idx / float(total - 1)
    loop_block_index = idx // 4
    loop_block_position = idx % 4

    if total == 1:
        phase = "single_pass_clear_light"
        energy_band = "clear_light"
        density_bias = "light_medium"
        piano_comping_bias = "core_identity_then_warm_flow"
        breath_bias = "medium"
        lift_bias = "very_low"
    elif idx == 0:
        phase = "head_in_core_identity"
        energy_band = "clear_light"
        density_bias = "light_medium"
        piano_comping_bias = "core_identity_reset"
        breath_bias = "low"
        lift_bias = "very_low"
    elif idx == total - 1:
        phase = "final_soft_release"
        energy_band = "soft_release"
        density_bias = "light"
        piano_comping_bias = "settled_release"
        breath_bias = "high"
        lift_bias = "none"
    elif total == 2:
        phase = "second_pass_soft_release"
        energy_band = "soft_release"
        density_bias = "light"
        piano_comping_bias = "settled_release"
        breath_bias = "high"
        lift_bias = "none"
    elif total <= 4:
        if position < 0.5:
            phase = "warm_flow"
            energy_band = "warm_medium"
            density_bias = "medium_light"
            piano_comping_bias = "warm_batida_flow"
            breath_bias = "medium"
            lift_bias = "low"
        else:
            phase = "gentle_lift"
            energy_band = "medium_lift"
            density_bias = "medium"
            piano_comping_bias = "gentle_transition_lift"
            breath_bias = "low_medium"
            lift_bias = "low_medium"
    else:
        if loop_block_position == 0:
            phase = "loop_wave_reset"
            energy_band = "clear_light"
            density_bias = "light_medium"
            piano_comping_bias = "core_identity_reset"
            breath_bias = "medium"
            lift_bias = "very_low"
        elif loop_block_position == 1:
            phase = "loop_wave_warm_flow"
            energy_band = "warm_medium"
            density_bias = "medium_light"
            piano_comping_bias = "warm_batida_flow"
            breath_bias = "medium"
            lift_bias = "low"
        elif loop_block_position == 2:
            phase = "loop_wave_breath_space"
            energy_band = "soft_breath"
            density_bias = "light"
            piano_comping_bias = "breath_space"
            breath_bias = "high"
            lift_bias = "very_low"
        else:
            phase = "loop_wave_gentle_lift"
            energy_band = "medium_lift"
            density_bias = "medium"
            piano_comping_bias = "gentle_transition_lift"
            breath_bias = "low_medium"
            lift_bias = "low_medium"

    return {
        "version": BOSSA_NOVA_REPEAT_COUNT_ARRANGEMENT_ARC_POLICY_VERSION,
        "chorus_index": idx,
        "total_choruses": total,
        "normalized_position": round(position, 4),
        "loop_block_index": loop_block_index,
        "loop_block_position": loop_block_position,
        "phase": phase,
        "energy_band": energy_band,
        "density_bias": density_bias,
        "piano_comping_bias": piano_comping_bias,
        "breath_bias": breath_bias,
        "lift_bias": lift_bias,
        "long_loop_safe": total >= 8,
        "monotonic_ramp_allowed": False,
        "not_medium_swing_clone": True,
        "source": "bossa_nova_repeat_count_aware_arrangement_arc_policy",
    }


def simulate_repeat_count_arrangement_arc(total_choruses: int) -> list[dict]:
    """Return the Bossa per-chorus macro arc for an arbitrary repeat count."""

    total = max(1, int(total_choruses or 1))
    return [resolve_repeat_count_arrangement_arc(i, total) for i in range(total)]


def resolve_runtime_arrangement_arc_intent(chorus_index: int, total_choruses: int) -> dict:
    """Return runtime-consumable Bossa arrangement intent metadata."""

    arc = resolve_repeat_count_arrangement_arc(chorus_index, total_choruses)
    bias = str(arc.get("piano_comping_bias") or "warm_batida_flow")
    if bias == "core_identity_reset":
        comping_intent = "core_identity_reset"
    elif bias == "breath_space":
        comping_intent = "breath_space"
    elif bias == "gentle_transition_lift":
        comping_intent = "gentle_transition_lift"
    elif bias == "settled_release":
        comping_intent = "settled_release"
    elif bias == "core_identity_then_warm_flow":
        comping_intent = "single_pass_clear_light"
    else:
        comping_intent = "warm_batida_flow"

    return {
        **arc,
        "runtime_intent_enabled": True,
        "runtime_intent_usage_version": BOSSA_NOVA_REPEAT_COUNT_ARRANGEMENT_ARC_POLICY_VERSION,
        "runtime_intent_source": "bossa_nova_repeat_count_aware_arrangement_arc",
        "piano_comping_runtime_intent": comping_intent,
        "piano_comping_density_bias": arc.get("density_bias"),
        "piano_comping_breath_bias": arc.get("breath_bias"),
        "piano_comping_lift_bias": arc.get("lift_bias"),
        "runtime_usage_boundary": "style_intent_metadata_and_candidate_weighting_only",
        "no_pattern_vocabulary_change": True,
        "no_core_voicing_change": True,
        "no_expression_numeric_change": True,
        "not_three_chorus_hardcoded": True,
        "not_medium_swing_clone": True,
    }


def resolve_full_band_arrangement_arc_listening_refinement(intent: dict | None) -> dict:
    """Return bass/drums semantic profile overrides for the Bossa repeat arc.

    This helper is consumed by existing Bossa bass/percussion pattern sources.
    It does not select notes or create a separate full-band engine; it only
    maps the already-resolved Bossa arc phase to semantic dynamic profile names
    that existing realizers understand.
    """

    intent = dict(intent or {})
    runtime_intent = str(intent.get("piano_comping_runtime_intent") or "warm_batida_flow")
    phase = str(intent.get("phase") or "unknown")

    band = "warm_flow"
    if runtime_intent in {"breath_space"} or "breath" in phase:
        band = "breath_space"
    elif runtime_intent in {"settled_release"} or "release" in phase:
        band = "soft_release"
    elif runtime_intent in {"gentle_transition_lift"} or "lift" in phase:
        band = "gentle_lift"
    elif runtime_intent in {"core_identity_reset", "single_pass_clear_light"}:
        band = "clear_identity"

    if band == "breath_space":
        bass_root = "bossa_root_soft"
        bass_fifth = "bossa_fifth_soft"
        bass_split_root = "bossa_split_root_soft"
        bass_short_root = "bossa_short_root_soft"
        shaker = "shaker_breath"
        cross_main = "bossa_cross_breath"
        cross_light = "bossa_cross_breath_light"
        kick_root = "bossa_kick_root_breath"
        kick_fifth = "bossa_kick_fifth_breath"
    elif band == "soft_release":
        bass_root = "bossa_root_release"
        bass_fifth = "bossa_fifth_release"
        bass_split_root = "bossa_split_root_release"
        bass_short_root = "bossa_short_root_release"
        shaker = "shaker_release"
        cross_main = "bossa_cross_release"
        cross_light = "bossa_cross_release_light"
        kick_root = "bossa_kick_root_release"
        kick_fifth = "bossa_kick_fifth_release"
    elif band == "gentle_lift":
        bass_root = "bossa_root_lift"
        bass_fifth = "bossa_fifth_lift"
        bass_split_root = "bossa_split_root_lift"
        bass_short_root = "bossa_short_root_lift"
        shaker = "shaker_lift"
        cross_main = "bossa_cross_lift"
        cross_light = "bossa_cross_lift_light"
        kick_root = "bossa_kick_root_lift"
        kick_fifth = "bossa_kick_fifth_lift"
    else:
        bass_root = "bossa_root"
        bass_fifth = "bossa_fifth"
        bass_split_root = "bossa_split_root"
        bass_short_root = "bossa_short_root"
        shaker = "shaker_light"
        cross_main = "bossa_cross_main"
        cross_light = "bossa_cross_light"
        kick_root = "bossa_kick_root"
        kick_fifth = "bossa_kick_fifth"

    return {
        "version": BOSSA_NOVA_FULL_BAND_ARRANGEMENT_ARC_LISTENING_REFINEMENT_VERSION,
        "active": True,
        "phase": phase,
        "runtime_intent": runtime_intent,
        "full_band_arc_band": band,
        "bass_root_dynamic_profile": bass_root,
        "bass_fifth_dynamic_profile": bass_fifth,
        "bass_split_root_dynamic_profile": bass_split_root,
        "bass_short_root_dynamic_profile": bass_short_root,
        "drum_shaker_dynamic_profile": shaker,
        "drum_cross_main_dynamic_profile": cross_main,
        "drum_cross_light_dynamic_profile": cross_light,
        "drum_kick_root_dynamic_profile": kick_root,
        "drum_kick_fifth_dynamic_profile": kick_fifth,
        "no_parallel_selector": True,
        "boundary": "style_arc_metadata_and_semantic_dynamic_profiles_only",
    }


def arrangement_arc_runtime_candidate_multiplier(candidate_metadata: dict, intent: dict) -> tuple[float, tuple[str, ...], str]:
    """Return a small Bossa-specific arrangement arc multiplier.

    The function consumes only candidate metadata and style intent.  It does not
    emit notes, choose voicing, write expression values, or inspect bar-first
    templates.
    """

    metadata = dict(candidate_metadata or {})
    intent = dict(intent or {})
    runtime_intent = str(intent.get("piano_comping_runtime_intent") or "warm_batida_flow")
    phase = str(intent.get("phase") or "unknown")
    rhythm_class = str(metadata.get("rhythm_class") or "")
    rhythmic_cell = str(metadata.get("rhythmic_cell") or "")
    archetype = str(metadata.get("bossa_context_archetype") or "")
    hit_count = int(metadata.get("hit_count") or 0)
    native_4and = bool(metadata.get("native_4and"))
    is_core = rhythm_class == "core_batida" or "core_batida" in str(metadata.get("category") or "")
    is_class_a = rhythm_class == "class_A"
    is_class_b = rhythm_class == "class_B"
    is_short_region = str(metadata.get("region_shape") or "") == "two_beat_region" or archetype == "dense_harmonic_marks"

    multiplier = 1.0
    reasons: list[str] = []
    status = "bossa_arc_neutral"

    if is_short_region:
        # Dense/short regions keep their harmonic clarity handling.  The chorus
        # arc should not make split regions busier.
        multiplier *= 1.0
        reasons.append(f"{phase}_dense_region_clarity_passthrough")
        status = "bossa_arc_dense_region_passthrough"
    elif runtime_intent == "core_identity_reset":
        if is_core:
            multiplier *= 1.28
            reasons.append(f"{phase}_core_identity_bonus")
            status = "bossa_arc_core_identity_bonus"
        if is_class_b:
            multiplier *= 0.42
            reasons.append(f"{phase}_class_B_reset_guard")
            status = "bossa_arc_reset_color_guard"
        if native_4and:
            multiplier *= 0.48
            reasons.append(f"{phase}_native_4and_reset_guard")
            status = "bossa_arc_reset_tail_guard"
    elif runtime_intent == "single_pass_clear_light":
        if is_core or (is_class_a and hit_count <= 2):
            multiplier *= 1.08
            reasons.append("single_pass_clear_anchor_or_light_A")
            status = "bossa_arc_single_pass_clear"
        if is_class_b:
            multiplier *= 0.58
            reasons.append("single_pass_class_B_guard")
            status = "bossa_arc_single_pass_color_guard"
        if hit_count >= 3:
            multiplier *= 0.82
            reasons.append("single_pass_three_hit_light_guard")
    elif runtime_intent == "warm_batida_flow":
        if is_class_a:
            multiplier *= 1.08
            reasons.append(f"{phase}_class_A_warm_flow_bonus")
            status = "bossa_arc_warm_flow_A"
        if is_class_b:
            multiplier *= 0.86
            reasons.append(f"{phase}_class_B_kept_as_color")
            status = "bossa_arc_warm_flow_color"
        if native_4and:
            multiplier *= 0.72
            reasons.append(f"{phase}_native_4and_still_rare")
    elif runtime_intent == "breath_space":
        if is_class_a and hit_count <= 1:
            multiplier *= 1.22
            reasons.append(f"{phase}_one_hit_breath_bonus")
            status = "bossa_arc_breath_space"
        elif is_class_a and hit_count == 2:
            multiplier *= 1.04
            reasons.append(f"{phase}_two_hit_breath_allowed")
            status = "bossa_arc_breath_space"
        if is_core or hit_count >= 3:
            multiplier *= 0.56
            reasons.append(f"{phase}_dense_or_core_breath_guard")
            status = "bossa_arc_breath_density_guard"
        if is_class_b:
            multiplier *= 0.92
            reasons.append(f"{phase}_class_B_air_color_limited")
        if native_4and:
            multiplier *= 0.54
            reasons.append(f"{phase}_native_4and_breath_guard")
    elif runtime_intent == "gentle_transition_lift":
        if is_class_a and hit_count >= 2:
            multiplier *= 1.14
            reasons.append(f"{phase}_two_or_three_hit_gentle_lift")
            status = "bossa_arc_gentle_lift"
        if is_class_b:
            multiplier *= 0.72
            reasons.append(f"{phase}_class_B_lift_limited")
            status = "bossa_arc_lift_color_guard"
        if native_4and:
            multiplier *= 0.82
            reasons.append(f"{phase}_native_4and_lift_limited")
    elif runtime_intent == "settled_release":
        if is_class_a and hit_count <= 1:
            multiplier *= 1.20
            reasons.append(f"{phase}_single_hit_release_bonus")
            status = "bossa_arc_release_settle"
        if is_core:
            multiplier *= 0.72
            reasons.append(f"{phase}_core_repetition_release_guard")
            status = "bossa_arc_release_core_guard"
        if is_class_b or native_4and or hit_count >= 3:
            multiplier *= 0.38
            reasons.append(f"{phase}_color_or_busy_release_guard")
            status = "bossa_arc_release_activity_guard"

    if not reasons:
        reasons.append(f"{phase}_neutral")
    return max(0.0, float(multiplier)), tuple(reasons), status
