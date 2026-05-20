from __future__ import annotations


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
        "piano_comping_harmonic_function_policy": True,
        "piano_comping_harmonic_function_policy_version": "v2_6_60",
        "piano_comping_progression_specific_subset_policy": True,
        "piano_comping_progression_specific_subset_policy_version": "v2_6_65",
        "piano_comping_no_4and_delayed_tail_idiom_policy": True,
        "piano_comping_no_4and_delayed_tail_idiom_policy_version": "v2_6_66",
        "piano_region_first_anticipation_compatibility_checkpoint": True,
        "piano_region_first_anticipation_compatibility_checkpoint_version": "v2_6_61",
        "piano_region_first_coverage_guard": True,
        "piano_region_first_coverage_guard_version": "v2_6_62",
        "piano_region_length_pattern_vocabulary_contract": "Medium Swing piano comping is selected from ChordRegion-local 1/2/4-beat pitchless rhythm cells; no bar-level two-chord-bar pattern path is used.",
        "piano_region_length_candidate_lookup_contract": "ChordRegion duration routes candidate lookup to 1/2/4-beat region-local pattern families before weighted sampling; inactive v2_6_56 vocabulary is activated only inside its matching region-length family.",
        "piano_region_length_weight_calibration_contract": "Medium Swing piano comping keeps stable cells primary, offbeat conversation secondary, active cells controlled, and native tail-push cells rare; calibration is applied inside the existing region-length pattern library, not through a parallel selector.",
        "piano_comping_history_continuity_contract": "Medium Swing piano comping applies a lightweight history scorer to the existing region-length candidate pool, penalizing exact repeat, non-stable family repeat, consecutive offbeat/active/tail-push, and rewarding stable reset after active/offbeat; no parallel selector is introduced.",
        "piano_comping_harmonic_function_contract": "Medium Swing piano comping reweights the existing ChordRegion-length candidate pool by functional motion labels such as predominant_to_dominant, dominant_resolution, tonic_resolution, section_start, section_end, and ending; this remains a multiplier policy before the normal history scorer, not a bar-first/two-chord-bar or parallel selector path.",
        "piano_comping_progression_specific_subset_contract": "Medium Swing piano comping translates V1 major_251/minor_251/two_five/ii_setup priority into a ChordRegion-first preferred subset inside the existing region-length candidate pool; it never restores bar-first/two-chord-bar templates, never chooses voicing, and never writes final expression values.",
        "piano_comping_no_4and_delayed_tail_idiom_contract": "Medium Swing piano comping translates V1 no-4& / delayed-tail preference as region-local candidate reweighting: native 4& tail-push remains available as rare lift, delayed/tail/backbeat cells get only modest bonuses, and routing remains ChordRegion-first.",
        "piano_region_first_anticipation_compatibility_contract": "Medium Swing anticipation remains region-first: the previous ChordRegion tail slot is computed from region duration, so 4-beat regions use local 4&/3.5, 2-beat regions use local 2&/1.5, and short regions are never forced through a bar-first 4& assumption.",
        "piano_region_first_coverage_guard_contract": "Medium Swing CoverageGuard is region-first and backup-only: it checks selected ChordRegion-local piano comping plans after pattern policy, stamps coverage audit metadata when the region already has piano presence, and inserts a single pitchless region-start fallback anchor only when a ChordRegion would otherwise be uncovered; it never replaces region-length pattern policy or uses bar-first/two-chord-bar routing.",
        "milestone": "v2_6_66_no_4and_delayed_tail_boundary_guard_policy",
    }
