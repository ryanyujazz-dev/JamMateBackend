from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from statistics import mean
from typing import Any, Mapping

from jammate_engine.midi.render_pipeline import performed_beat


PIANO_MUSICAL_AUDIT_CONTRACT_VERSION = "v2_2_38"
PIANO_DROP_PROJECTION_AUDIT_VERSION = "v2_6_29"
PIANO_LOWER_UPPER_GAP_AUDIT_VERSION = "v2_6_31"
PIANO_GAP_AWARE_CANDIDATE_SCOPE_MICRO_CALIBRATION_VERSION = "v2_6_33"
PIANO_WIDE_GAP_DEFERRED_OUTLIER_STRATEGY_VERSION = "v2_6_33"
PIANO_WIDE_GAP_SOURCE_INVENTORY_PLAN_VERSION = "v2_6_34"
PIANO_PHRASE_SCOPE_WIDE_GAP_CANDIDATE_AVAILABILITY_VERSION = "v2_6_35"
PIANO_PHRASE_STATE_BOUNDARY_REVIEW_VERSION = "v2_6_36"
PIANO_PHRASE_STATE_BOUNDARY_HELPER_CLEANUP_VERSION = "v2_6_37"
PIANO_POST_CONTINUITY_LISTENING_CHECKPOINT_VERSION = "v2_6_39"
PIANO_PHRASE_STATE_ANCHOR_POLICY_BOUNDARY_VERSION = "v2_6_40"
PIANO_SAME_CHORD_REATTACK_CONTINUITY_VERSION = "v2_6_41"
PIANO_SAFE_EXTENSION_FREQUENCY_CALIBRATION_VERSION = "v2_6_42"


@dataclass(frozen=True)
class PianoMusicalAudit:
    """Observational audit model for piano pattern/expression/voicing output.

    This audit consumes the runtime debug trace produced by the engine. It does
    not re-plan pattern, expression, voicing, or timing. Its job is to make the
    current piano sound inspectable before style musicality tuning begins.
    """

    summary: dict[str, Any]
    event_rows: list[dict[str, Any]]
    warnings: list[str]


def build_piano_musical_audit(debug: Mapping[str, Any]) -> PianoMusicalAudit:
    expression_rows = {
        str(row.get("event_id")): dict(row)
        for row in debug.get("expression_foundation_audit_events") or []
        if isinstance(row, Mapping)
    }
    rows = [
        _event_row(
            index,
            row,
            debug.get("timing_policy") or {},
            expression_rows.get(str((row.get("pattern_event") or {}).get("event_id", row.get("event_id", "")))),
        )
        for index, row in enumerate(debug.get("piano_musical_audit_events") or [], start=1)
    ]
    phrase_state_boundary_review = _annotate_phrase_state_boundary_review(rows)
    post_continuity_checkpoint = _annotate_post_continuity_listening_checkpoint(
        rows,
        debug.get("timing_policy") or {},
    )
    same_chord_reattack_continuity = _annotate_same_chord_reattack_continuity(rows)
    warnings: list[str] = []

    style_counter: Counter[str] = Counter()
    pattern_counter: Counter[str] = Counter()
    gesture_counter: Counter[str] = Counter()
    expression_counter: Counter[str] = Counter()
    articulation_counter: Counter[str] = Counter()
    content_counter: Counter[str] = Counter()
    density_counter: Counter[str] = Counter()
    grouping_counter: Counter[str] = Counter()
    disposition_counter: Counter[str] = Counter()
    root_support_counter: Counter[str] = Counter()
    register_reason_counter: Counter[str] = Counter()
    note_counts: list[int] = []
    durations: list[float] = []
    velocities: list[int] = []
    rootless_count = 0
    root_included_count = 0
    failed_register_guard_count = 0
    suppressed_or_missing_note_count = 0
    expression_flag_counter: Counter[str] = Counter()
    source_gate_counter: Counter[str] = Counter()
    source_key_counter: Counter[str] = Counter()
    three_note_source_type_counter: Counter[str] = Counter()
    three_note_source_role_counter: Counter[str] = Counter()
    three_note_degree_order_counter: Counter[str] = Counter()
    triad_4note_source_type_counter: Counter[str] = Counter()
    triad_4note_source_role_counter: Counter[str] = Counter()
    triad_4note_degree_order_counter: Counter[str] = Counter()
    source_scores: list[float] = []
    fidelity_scores: list[float] = []
    region_voicing_reuse_count = 0
    closed_minimum_motion_count = 0
    closed_3note_minimum_motion_count = 0
    closed_4note_minimum_motion_count = 0
    closed_3note_collapse_distances: list[float] = []
    closed_3note_collapse_total_motions: list[float] = []
    closed_4note_collapse_distances: list[float] = []
    closed_4note_collapse_total_motions: list[float] = []
    closed_spans: list[int] = []
    closed_lows: list[int] = []
    projection_family_counter: Counter[str] = Counter()
    projection_method_counter: Counter[str] = Counter()
    migrated_projection_path_counter: Counter[str] = Counter()
    legacy_projection_callback_used_count = 0
    legacy_projection_cleanup_required_count = 0
    open_named_projection_counter: Counter[str] = Counter()
    open_named_projection_spans: list[int] = []
    open_named_projection_lows: list[int] = []
    open_named_projection_parent_closed_spans: list[int] = []
    open_drop2_count = 0
    open_drop2_spans: list[int] = []
    open_drop2_lows: list[int] = []
    open_drop2_parent_closed_spans: list[int] = []
    texture_scope_counter: Counter[str] = Counter()
    texture_contrast_counter: Counter[str] = Counter()
    texture_methods_by_contrast: dict[str, Counter[str]] = {}
    texture_methods_by_scope: dict[str, Counter[str]] = {}
    texture_weight_plan_by_contrast: dict[str, dict[str, float]] = {}
    drop_projection_method_counter: Counter[str] = Counter()
    drop_projection_method_by_scope: dict[str, Counter[str]] = {}
    spread_upper_projection_method_counter: Counter[str] = Counter()
    spread_upper_drop_method_counter: Counter[str] = Counter()
    spread_upper_drop_method_by_density: dict[str, Counter[str]] = {}
    spread_upper_drop_method_by_grouping: dict[str, Counter[str]] = {}
    spread_upper_drop_method_by_recipe: dict[str, Counter[str]] = {}
    spread_upper_drop_events_by_density: Counter[str] = Counter()
    lower_foundation_notes: list[int] = []
    lower_foundation_spans: list[int] = []
    lower_foundation_note_stats_by_grouping: dict[str, list[int]] = {}
    lower_foundation_note_stats_by_density: dict[str, list[int]] = {}
    lower_foundation_span_stats_by_grouping: dict[str, list[int]] = {}
    lower_foundation_span_stats_by_density: dict[str, list[int]] = {}
    lower_foundation_recipe_counter: Counter[str] = Counter()
    lower_foundation_low_register_events_by_grouping: Counter[str] = Counter()
    lower_foundation_low_register_events_by_density: Counter[str] = Counter()
    lower_foundation_span_violation_events = 0
    lower_upper_group_gaps: list[int] = []
    lower_upper_group_gap_stats_by_grouping: dict[str, list[int]] = {}
    lower_upper_group_gap_stats_by_density: dict[str, list[int]] = {}
    lower_upper_group_gap_stats_by_recipe: dict[str, list[int]] = {}
    lower_upper_group_gap_too_tight_events_by_grouping: Counter[str] = Counter()
    lower_upper_group_gap_too_wide_events_by_grouping: Counter[str] = Counter()
    spread_gap_aware_micro_events_by_recipe: Counter[str] = Counter()
    spread_gap_aware_micro_events_by_grouping: Counter[str] = Counter()
    spread_gap_aware_original_gaps: list[int] = []
    spread_gap_aware_replacement_gaps: list[int] = []
    spread_wide_gap_deferred_events_by_recipe: Counter[str] = Counter()
    spread_wide_gap_deferred_events_by_grouping: Counter[str] = Counter()
    spread_wide_gap_deferred_original_gaps: list[int] = []
    spread_wide_gap_deferred_replacement_gaps: list[int] = []
    spread_wide_gap_source_inventory_events_by_recipe: Counter[str] = Counter()
    spread_wide_gap_source_inventory_events_by_grouping: Counter[str] = Counter()
    spread_wide_gap_source_inventory_best_replacement_gaps: list[int] = []
    spread_wide_gap_source_inventory_top_stable_replacement_gaps: list[int] = []
    spread_wide_gap_source_inventory_runtime_enabled_events = 0
    spread_wide_gap_source_inventory_recommendation_counter: Counter[str] = Counter()
    spread_phrase_scope_wide_gap_events_by_recipe: Counter[str] = Counter()
    spread_phrase_scope_wide_gap_events_by_grouping: Counter[str] = Counter()
    spread_phrase_scope_wide_gap_original_gaps: list[int] = []
    spread_phrase_scope_wide_gap_realized_gaps: list[int] = []
    spread_phrase_scope_wide_gap_state_protected_events = 0
    spread_phrase_scope_wide_gap_runtime_realization_events = 0
    spread_phrase_state_boundary_helper_cleanup_events = 0
    spread_phrase_state_boundary_helper_anchor_events = 0
    spread_phrase_state_boundary_helper_legacy_alias_match_events = 0
    spread_phrase_state_boundary_helper_previous_state_anchor_events = 0
    spread_phrase_state_anchor_policy_boundary_events = 0
    spread_phrase_state_anchor_policy_boundary_gate_required_events = 0
    spread_phrase_state_anchor_policy_boundary_scopes: Counter[str] = Counter()
    spread_phrase_state_anchor_policy_boundary_previous_gate_consumed_events = 0
    lower_upper_gap_comfort_min = 2
    lower_upper_gap_comfort_max = 7
    all_midi_notes: list[int] = []
    top_note_ge_75_events = 0
    major_seventh_events = 0
    major_seventh_color_events = 0
    major_seventh_safe_color_events = 0
    major_seventh_unnotated_sharp11_events = 0
    major_seventh_explicit_sharp11_events = 0
    major_seventh_colors: Counter[str] = Counter()
    major_seventh_colors_by_chord: dict[str, Counter[str]] = {}
    major_seventh_non_safe_color_events_by_chord: Counter[str] = Counter()

    for row in rows:
        style_counter.update([str(debug.get("style", "unknown"))])
        pattern_counter.update([row["pattern_id"] or "unknown"])
        gesture_counter.update([row["gesture_type"] or "unknown"])
        expression_counter.update([row["expression_profile"] or "unknown"])
        articulation_counter.update([row["articulation"] or "unknown"])
        content_counter.update([row["content_family"] or "unknown"])
        density_counter.update([str(row["density"] or "unknown")])
        grouping_counter.update([row["functional_grouping"] or "unknown"])
        disposition_counter.update([row["disposition"] or "unknown"])
        root_support_counter.update([row["root_support"] or "unknown"])
        projection_family_counter.update([row["disposition_projection_family"] or "unknown"])
        projection_method_counter.update([row["disposition_projection_method"] or "unknown"])
        scope_id = str(row.get("voicing_texture_scope_id") or "unknown")
        contrast_role = str(row.get("voicing_texture_contrast_role") or "unknown")
        projection_method = str(row["disposition_projection_method"] or "unknown")
        main_drop_method = row.get("main_drop_projection_method")
        spread_upper_method = row.get("spread_upper_projection_method")
        spread_upper_drop_method = row.get("spread_upper_drop_projection_method")
        if main_drop_method:
            method = str(main_drop_method)
            drop_projection_method_counter.update([method])
            drop_projection_method_by_scope.setdefault("main_voicing", Counter()).update([method])
        if spread_upper_method:
            spread_upper_projection_method_counter.update([str(spread_upper_method)])
        if spread_upper_drop_method:
            method = str(spread_upper_drop_method)
            density_key = str(row["density"] or "unknown")
            grouping_key = str(row["functional_grouping"] or "unknown")
            recipe_key = str(row["recipe_id"] or "unknown")
            drop_projection_method_counter.update([method])
            drop_projection_method_by_scope.setdefault("spread_upper_group", Counter()).update([method])
            spread_upper_drop_method_counter.update([method])
            spread_upper_drop_method_by_density.setdefault(density_key, Counter()).update([method])
            spread_upper_drop_method_by_grouping.setdefault(grouping_key, Counter()).update([method])
            spread_upper_drop_method_by_recipe.setdefault(recipe_key, Counter()).update([method])
            spread_upper_drop_events_by_density.update([density_key])
        group_gap_value = row.get("group_gap_semitones")
        if group_gap_value is not None:
            try:
                group_gap = int(group_gap_value)
            except (TypeError, ValueError):
                group_gap = None
            if group_gap is not None:
                density_key = str(row["density"] or "unknown")
                grouping_key = str(row["functional_grouping"] or "unknown")
                recipe_key = str(row["recipe_id"] or "unknown")
                lower_upper_group_gaps.append(group_gap)
                lower_upper_group_gap_stats_by_grouping.setdefault(grouping_key, []).append(group_gap)
                lower_upper_group_gap_stats_by_density.setdefault(density_key, []).append(group_gap)
                lower_upper_group_gap_stats_by_recipe.setdefault(recipe_key, []).append(group_gap)
                if group_gap < lower_upper_gap_comfort_min:
                    lower_upper_group_gap_too_tight_events_by_grouping.update([grouping_key])
                if group_gap > lower_upper_gap_comfort_max:
                    lower_upper_group_gap_too_wide_events_by_grouping.update([grouping_key])
        if row.get("spread_gap_aware_candidate_scope_micro_calibration_applied"):
            spread_gap_aware_micro_events_by_recipe.update([str(row.get("recipe_id") or "unknown")])
            spread_gap_aware_micro_events_by_grouping.update([str(row.get("functional_grouping") or "unknown")])
            try:
                spread_gap_aware_original_gaps.append(int(float(row.get("spread_gap_aware_original_gap"))))
            except (TypeError, ValueError):
                pass
            try:
                spread_gap_aware_replacement_gaps.append(int(float(row.get("spread_gap_aware_replacement_gap"))))
            except (TypeError, ValueError):
                pass
        if row.get("spread_wide_gap_deferred_outlier_strategy_deferred"):
            spread_wide_gap_deferred_events_by_recipe.update([str(row.get("recipe_id") or "unknown")])
            spread_wide_gap_deferred_events_by_grouping.update([str(row.get("functional_grouping") or "unknown")])
            try:
                spread_wide_gap_deferred_original_gaps.append(int(float(row.get("spread_wide_gap_deferred_original_gap"))))
            except (TypeError, ValueError):
                pass
            try:
                spread_wide_gap_deferred_replacement_gaps.append(int(float(row.get("spread_wide_gap_deferred_best_replacement_gap"))))
            except (TypeError, ValueError):
                pass
        if row.get("spread_wide_gap_source_inventory_plan_active"):
            spread_wide_gap_source_inventory_events_by_recipe.update([str(row.get("recipe_id") or "unknown")])
            spread_wide_gap_source_inventory_events_by_grouping.update([str(row.get("functional_grouping") or "unknown")])
            recommendation = str(row.get("spread_wide_gap_source_inventory_recommended_next_boundary") or "unknown")
            spread_wide_gap_source_inventory_recommendation_counter.update([recommendation])
            if row.get("spread_wide_gap_source_inventory_runtime_replacement_enabled"):
                spread_wide_gap_source_inventory_runtime_enabled_events += 1
            try:
                spread_wide_gap_source_inventory_best_replacement_gaps.append(int(float(row.get("spread_wide_gap_source_inventory_best_replacement_gap"))))
            except (TypeError, ValueError):
                pass
            try:
                spread_wide_gap_source_inventory_top_stable_replacement_gaps.append(int(float(row.get("spread_wide_gap_source_inventory_top_stable_replacement_gap"))))
            except (TypeError, ValueError):
                pass
        if row.get("spread_phrase_state_boundary_helper_cleanup_applied"):
            spread_phrase_state_boundary_helper_cleanup_events += 1
        if row.get("voicing_state_advance_anchor_enabled"):
            spread_phrase_state_boundary_helper_anchor_events += 1
            if tuple(row.get("voicing_state_advance_anchor_notes") or []) == tuple(row.get("spread_phrase_scope_wide_gap_state_advance_override_notes") or []):
                spread_phrase_state_boundary_helper_legacy_alias_match_events += 1
        if row.get("previous_voicing_state_state_advance_anchor_enabled"):
            spread_phrase_state_boundary_helper_previous_state_anchor_events += 1
        if row.get("spread_phrase_state_anchor_policy_boundary_applied"):
            spread_phrase_state_anchor_policy_boundary_events += 1
            spread_phrase_state_anchor_policy_boundary_scopes.update([str(row.get("spread_phrase_state_anchor_policy_boundary_scope") or "unknown")])
        if row.get("voicing_state_advance_anchor_policy_gate_required"):
            spread_phrase_state_anchor_policy_boundary_gate_required_events += 1
        if row.get("previous_voicing_state_state_advance_anchor_policy_gate_consumed"):
            spread_phrase_state_anchor_policy_boundary_previous_gate_consumed_events += 1
        if row.get("spread_phrase_scope_wide_gap_candidate_availability_applied"):
            spread_phrase_scope_wide_gap_events_by_recipe.update([str(row.get("recipe_id") or "unknown")])
            spread_phrase_scope_wide_gap_events_by_grouping.update([str(row.get("functional_grouping") or "unknown")])
            if row.get("spread_phrase_scope_wide_gap_state_advance_protected"):
                spread_phrase_scope_wide_gap_state_protected_events += 1
            if row.get("spread_phrase_scope_wide_gap_runtime_realization_enabled"):
                spread_phrase_scope_wide_gap_runtime_realization_events += 1
            try:
                spread_phrase_scope_wide_gap_original_gaps.append(int(float(row.get("spread_phrase_scope_wide_gap_original_gap"))))
            except (TypeError, ValueError):
                pass
            try:
                spread_phrase_scope_wide_gap_realized_gaps.append(int(float(row.get("spread_phrase_scope_wide_gap_realized_gap"))))
            except (TypeError, ValueError):
                pass
        lower_notes = [int(note) for note in row.get("lower_group_notes") or []]
        if lower_notes:
            density_key = str(row["density"] or "unknown")
            grouping_key = str(row["functional_grouping"] or "unknown")
            lower_foundation_notes.extend(lower_notes)
            lower_foundation_note_stats_by_grouping.setdefault(grouping_key, []).extend(lower_notes)
            lower_foundation_note_stats_by_density.setdefault(density_key, []).extend(lower_notes)
            span = max(lower_notes) - min(lower_notes)
            lower_foundation_spans.append(span)
            lower_foundation_span_stats_by_grouping.setdefault(grouping_key, []).append(span)
            lower_foundation_span_stats_by_density.setdefault(density_key, []).append(span)
            if span > int(row.get("lower_group_max_span_semitones") or 12):
                lower_foundation_span_violation_events += 1
            recipe_id = str(row.get("lower_group_recipe_id") or "unknown")
            lower_foundation_recipe_counter.update([recipe_id])
            low_register_threshold = int(row.get("lower_foundation_low_register_threshold") or 43)
            if min(lower_notes) < low_register_threshold:
                lower_foundation_low_register_events_by_grouping.update([grouping_key])
                lower_foundation_low_register_events_by_density.update([density_key])
        texture_scope_counter.update([scope_id])
        texture_contrast_counter.update([contrast_role])
        texture_methods_by_contrast.setdefault(contrast_role, Counter()).update([projection_method])
        texture_methods_by_scope.setdefault(scope_id, Counter()).update([projection_method])
        if contrast_role not in texture_weight_plan_by_contrast and row.get("voicing_texture_open_method_weights"):
            texture_weight_plan_by_contrast[contrast_role] = dict(row.get("voicing_texture_open_method_weights") or {})
        if row.get("migrated_projection_path"):
            migrated_projection_path_counter.update([str(row["migrated_projection_path"])])
        if row.get("legacy_projection_callback_used"):
            legacy_projection_callback_used_count += 1
        if row.get("legacy_projection_cleanup_required"):
            legacy_projection_cleanup_required_count += 1
        if row.get("open_named_projection"):
            open_named_projection_counter.update([str(row.get("open_named_projection_method") or "unknown")])
        if row.get("open_named_projection_span") is not None:
            open_named_projection_spans.append(int(row["open_named_projection_span"]))
        if row.get("open_named_projection_parent_closed_span") is not None:
            open_named_projection_parent_closed_spans.append(int(row["open_named_projection_parent_closed_span"]))
        if row.get("midi_notes") and row.get("open_named_projection"):
            open_named_projection_lows.append(min(int(note) for note in row["midi_notes"]))
        if row.get("open_drop2_projection"):
            open_drop2_count += 1
        if row.get("open_drop2_span") is not None:
            open_drop2_spans.append(int(row["open_drop2_span"]))
        if row.get("open_drop2_parent_closed_span") is not None:
            open_drop2_parent_closed_spans.append(int(row["open_drop2_parent_closed_span"]))
        if row.get("midi_notes") and row.get("open_drop2_projection"):
            open_drop2_lows.append(min(int(note) for note in row["midi_notes"]))
        midi_notes = [int(note) for note in row.get("midi_notes") or []]
        if midi_notes:
            all_midi_notes.extend(midi_notes)
            if max(midi_notes) >= 75:
                top_note_ge_75_events += 1
        major_color_detail = _major_seventh_color_detail(row)
        if major_color_detail["is_major_seventh"]:
            major_seventh_events += 1
            colors = tuple(major_color_detail["colors"])
            if colors:
                major_seventh_color_events += 1
            major_seventh_colors.update(colors)
            chord_key = str(row.get("chord_symbol") or "unknown")
            major_seventh_colors_by_chord.setdefault(chord_key, Counter()).update(colors)
            if major_color_detail["safe_only"]:
                major_seventh_safe_color_events += 1
            if major_color_detail["unnotated_sharp11"]:
                major_seventh_unnotated_sharp11_events += 1
                major_seventh_non_safe_color_events_by_chord.update([chord_key])
            if major_color_detail["explicit_sharp11"]:
                major_seventh_explicit_sharp11_events += 1
        note_counts.append(int(row["realized_note_count"]))
        if row["duration_beats"] is not None:
            durations.append(float(row["duration_beats"]))
        if row["velocity"] is not None:
            velocities.append(int(row["velocity"]))
        if row["root_included"]:
            root_included_count += 1
        else:
            rootless_count += 1
        expression_flag_counter.update(row.get("expression_flags") or [])
        source_gate = row.get("four_note_source_balance_gate_mode")
        source_key = row.get("four_note_source_balance_key")
        if source_gate:
            source_gate_counter.update([str(source_gate)])
        if source_key:
            source_key_counter.update([str(source_key)])
        if row.get("three_note_source_type"):
            three_note_source_type_counter.update([str(row["three_note_source_type"])])
        if row.get("three_note_source_role_order"):
            three_note_source_role_counter.update([str(row["three_note_source_role_order"])])
        if row.get("three_note_degree_order"):
            three_note_degree_order_counter.update([str(row["three_note_degree_order"])])
        if row.get("triad_4note_source_type"):
            triad_4note_source_type_counter.update([str(row["triad_4note_source_type"])])
        if row.get("triad_4note_source_role_order"):
            triad_4note_source_role_counter.update([str(row["triad_4note_source_role_order"])])
        if row.get("triad_4note_degree_order"):
            triad_4note_degree_order_counter.update([str(row["triad_4note_degree_order"])])
        if row.get("four_note_source_balance_score") is not None:
            source_scores.append(float(row["four_note_source_balance_score"]))
        if row.get("region_voicing_reused"):
            region_voicing_reuse_count += 1
        if row.get("closed_3note_per_source_minimum_motion"):
            closed_minimum_motion_count += 1
            closed_3note_minimum_motion_count += 1
        if row.get("closed_4note_per_source_minimum_motion"):
            closed_minimum_motion_count += 1
            closed_4note_minimum_motion_count += 1
        if row.get("closed_3note_source_collapse_selected_distance") is not None:
            closed_3note_collapse_distances.append(float(row["closed_3note_source_collapse_selected_distance"]))
        if row.get("closed_3note_source_collapse_selected_total_motion") is not None:
            closed_3note_collapse_total_motions.append(float(row["closed_3note_source_collapse_selected_total_motion"]))
        if row.get("closed_4note_source_collapse_selected_distance") is not None:
            closed_4note_collapse_distances.append(float(row["closed_4note_source_collapse_selected_distance"]))
        if row.get("closed_4note_source_collapse_selected_total_motion") is not None:
            closed_4note_collapse_total_motions.append(float(row["closed_4note_source_collapse_selected_total_motion"]))
        if row.get("closed_voicing_actual_span") is not None:
            closed_spans.append(int(row["closed_voicing_actual_span"]))
        if row.get("midi_notes"):
            closed_lows.append(min(int(note) for note in row["midi_notes"]))
        if row.get("chart_color_fidelity_score") is not None:
            fidelity_scores.append(float(row["chart_color_fidelity_score"]))
        if not row["register_guard_passed"]:
            failed_register_guard_count += 1
            warnings.append(f"Event {row['event_id']} register guard failed: {row['register_guard_reasons']}")
        if row["realized_note_count"] <= 0:
            suppressed_or_missing_note_count += 1
            warnings.append(f"Event {row['event_id']} produced no realized piano notes")
        if row["duration_beats"] is not None and float(row["duration_beats"]) <= 0:
            warnings.append(f"Event {row['event_id']} has non-positive expression duration")
        for reason in row["register_guard_reasons"]:
            register_reason_counter.update([reason])

    summary = {
        "contract_version": PIANO_MUSICAL_AUDIT_CONTRACT_VERSION,
        "title": debug.get("title"),
        "style": debug.get("style", "unknown"),
        "events": len(rows),
        "note_events_by_track": debug.get("note_events_by_track", {}),
        "timing_policy": debug.get("timing_policy", {}),
        "top_patterns": pattern_counter.most_common(12),
        "gestures": dict(gesture_counter),
        "expression_profiles": dict(expression_counter),
        "articulations": dict(articulation_counter),
        "content_families": dict(content_counter),
        "densities": dict(density_counter),
        "functional_groupings": dict(grouping_counter),
        "dispositions": dict(disposition_counter),
        "disposition_projection_families": dict(projection_family_counter),
        "disposition_projection_methods": dict(projection_method_counter),
        "drop_projection_audit_version": PIANO_DROP_PROJECTION_AUDIT_VERSION,
        "drop_projection_methods_total": dict(drop_projection_method_counter),
        "drop_projection_methods_by_scope": {key: dict(counter) for key, counter in drop_projection_method_by_scope.items()},
        "spread_upper_projection_methods": dict(spread_upper_projection_method_counter),
        "spread_upper_drop_projection_methods": dict(spread_upper_drop_method_counter),
        "spread_upper_drop_projection_events": sum(spread_upper_drop_method_counter.values()),
        "spread_upper_drop_projection_methods_by_density": {key: dict(counter) for key, counter in spread_upper_drop_method_by_density.items()},
        "spread_upper_drop_projection_methods_by_grouping": {key: dict(counter) for key, counter in spread_upper_drop_method_by_grouping.items()},
        "spread_upper_drop_projection_methods_by_recipe": {key: dict(counter) for key, counter in spread_upper_drop_method_by_recipe.items()},
        "spread_upper_drop_projection_events_by_density": dict(spread_upper_drop_events_by_density),
        "lower_foundation_audit_version": "v2_6_30",
        "lower_foundation_note_min": min(lower_foundation_notes) if lower_foundation_notes else None,
        "lower_foundation_note_max": max(lower_foundation_notes) if lower_foundation_notes else None,
        "lower_foundation_note_average": round(mean(lower_foundation_notes), 3) if lower_foundation_notes else 0.0,
        "lower_foundation_span_max": max(lower_foundation_spans) if lower_foundation_spans else None,
        "lower_foundation_span_average": round(mean(lower_foundation_spans), 3) if lower_foundation_spans else 0.0,
        "lower_foundation_notes_by_grouping": _numeric_stats_by_key(lower_foundation_note_stats_by_grouping),
        "lower_foundation_notes_by_density": _numeric_stats_by_key(lower_foundation_note_stats_by_density),
        "lower_foundation_spans_by_grouping": _numeric_stats_by_key(lower_foundation_span_stats_by_grouping),
        "lower_foundation_spans_by_density": _numeric_stats_by_key(lower_foundation_span_stats_by_density),
        "lower_foundation_recipe_counts": dict(lower_foundation_recipe_counter),
        "lower_foundation_low_register_events": sum(lower_foundation_low_register_events_by_grouping.values()),
        "lower_foundation_low_register_events_by_grouping": dict(lower_foundation_low_register_events_by_grouping),
        "lower_foundation_low_register_events_by_density": dict(lower_foundation_low_register_events_by_density),
        "lower_foundation_span_violation_events": lower_foundation_span_violation_events,
        "lower_upper_gap_audit_version": PIANO_LOWER_UPPER_GAP_AUDIT_VERSION,
        "lower_upper_gap_comfort_min": lower_upper_gap_comfort_min,
        "lower_upper_gap_comfort_max": lower_upper_gap_comfort_max,
        "lower_upper_group_gap_min": min(lower_upper_group_gaps) if lower_upper_group_gaps else None,
        "lower_upper_group_gap_max": max(lower_upper_group_gaps) if lower_upper_group_gaps else None,
        "lower_upper_group_gap_average": round(mean(lower_upper_group_gaps), 3) if lower_upper_group_gaps else 0.0,
        "lower_upper_group_gap_by_grouping": _numeric_stats_by_key(lower_upper_group_gap_stats_by_grouping),
        "lower_upper_group_gap_by_density": _numeric_stats_by_key(lower_upper_group_gap_stats_by_density),
        "lower_upper_group_gap_by_recipe": _numeric_stats_by_key(lower_upper_group_gap_stats_by_recipe),
        "lower_upper_group_gap_too_tight_events": sum(lower_upper_group_gap_too_tight_events_by_grouping.values()),
        "lower_upper_group_gap_too_tight_events_by_grouping": dict(lower_upper_group_gap_too_tight_events_by_grouping),
        "lower_upper_group_gap_too_wide_events": sum(lower_upper_group_gap_too_wide_events_by_grouping.values()),
        "lower_upper_group_gap_too_wide_events_by_grouping": dict(lower_upper_group_gap_too_wide_events_by_grouping),
        "spread_gap_aware_candidate_scope_micro_calibration_version": PIANO_GAP_AWARE_CANDIDATE_SCOPE_MICRO_CALIBRATION_VERSION,
        "spread_gap_aware_candidate_scope_micro_calibration_events": sum(spread_gap_aware_micro_events_by_recipe.values()),
        "spread_gap_aware_candidate_scope_micro_calibration_events_by_recipe": dict(spread_gap_aware_micro_events_by_recipe),
        "spread_gap_aware_candidate_scope_micro_calibration_events_by_grouping": dict(spread_gap_aware_micro_events_by_grouping),
        "spread_gap_aware_original_gap_min": min(spread_gap_aware_original_gaps) if spread_gap_aware_original_gaps else None,
        "spread_gap_aware_original_gap_max": max(spread_gap_aware_original_gaps) if spread_gap_aware_original_gaps else None,
        "spread_gap_aware_replacement_gap_min": min(spread_gap_aware_replacement_gaps) if spread_gap_aware_replacement_gaps else None,
        "spread_gap_aware_replacement_gap_max": max(spread_gap_aware_replacement_gaps) if spread_gap_aware_replacement_gaps else None,
        "spread_wide_gap_deferred_outlier_strategy_version": PIANO_WIDE_GAP_DEFERRED_OUTLIER_STRATEGY_VERSION,
        "spread_wide_gap_deferred_outlier_strategy_events": sum(spread_wide_gap_deferred_events_by_recipe.values()),
        "spread_wide_gap_deferred_outlier_strategy_deferred_events": sum(spread_wide_gap_deferred_events_by_recipe.values()),
        "spread_wide_gap_deferred_outlier_strategy_events_by_recipe": dict(spread_wide_gap_deferred_events_by_recipe),
        "spread_wide_gap_deferred_outlier_strategy_events_by_grouping": dict(spread_wide_gap_deferred_events_by_grouping),
        "spread_wide_gap_deferred_original_gap_min": min(spread_wide_gap_deferred_original_gaps) if spread_wide_gap_deferred_original_gaps else None,
        "spread_wide_gap_deferred_original_gap_max": max(spread_wide_gap_deferred_original_gaps) if spread_wide_gap_deferred_original_gaps else None,
        "spread_wide_gap_deferred_replacement_gap_min": min(spread_wide_gap_deferred_replacement_gaps) if spread_wide_gap_deferred_replacement_gaps else None,
        "spread_wide_gap_deferred_replacement_gap_max": max(spread_wide_gap_deferred_replacement_gaps) if spread_wide_gap_deferred_replacement_gaps else None,
        "spread_wide_gap_source_inventory_plan_version": PIANO_WIDE_GAP_SOURCE_INVENTORY_PLAN_VERSION,
        "spread_wide_gap_source_inventory_plan_events": sum(spread_wide_gap_source_inventory_events_by_recipe.values()),
        "spread_wide_gap_source_inventory_plan_events_by_recipe": dict(spread_wide_gap_source_inventory_events_by_recipe),
        "spread_wide_gap_source_inventory_plan_events_by_grouping": dict(spread_wide_gap_source_inventory_events_by_grouping),
        "spread_wide_gap_source_inventory_best_replacement_gap_min": min(spread_wide_gap_source_inventory_best_replacement_gaps) if spread_wide_gap_source_inventory_best_replacement_gaps else None,
        "spread_wide_gap_source_inventory_best_replacement_gap_max": max(spread_wide_gap_source_inventory_best_replacement_gaps) if spread_wide_gap_source_inventory_best_replacement_gaps else None,
        "spread_wide_gap_source_inventory_top_stable_replacement_gap_min": min(spread_wide_gap_source_inventory_top_stable_replacement_gaps) if spread_wide_gap_source_inventory_top_stable_replacement_gaps else None,
        "spread_wide_gap_source_inventory_top_stable_replacement_gap_max": max(spread_wide_gap_source_inventory_top_stable_replacement_gaps) if spread_wide_gap_source_inventory_top_stable_replacement_gaps else None,
        "spread_wide_gap_source_inventory_runtime_replacement_enabled_events": spread_wide_gap_source_inventory_runtime_enabled_events,
        "spread_wide_gap_source_inventory_recommended_next_boundaries": dict(spread_wide_gap_source_inventory_recommendation_counter),
        "spread_phrase_scope_wide_gap_candidate_availability_version": PIANO_PHRASE_SCOPE_WIDE_GAP_CANDIDATE_AVAILABILITY_VERSION,
        "spread_phrase_scope_wide_gap_candidate_availability_events": sum(spread_phrase_scope_wide_gap_events_by_recipe.values()),
        "spread_phrase_scope_wide_gap_candidate_availability_events_by_recipe": dict(spread_phrase_scope_wide_gap_events_by_recipe),
        "spread_phrase_scope_wide_gap_candidate_availability_events_by_grouping": dict(spread_phrase_scope_wide_gap_events_by_grouping),
        "spread_phrase_scope_wide_gap_original_gap_min": min(spread_phrase_scope_wide_gap_original_gaps) if spread_phrase_scope_wide_gap_original_gaps else None,
        "spread_phrase_scope_wide_gap_original_gap_max": max(spread_phrase_scope_wide_gap_original_gaps) if spread_phrase_scope_wide_gap_original_gaps else None,
        "spread_phrase_scope_wide_gap_realized_gap_min": min(spread_phrase_scope_wide_gap_realized_gaps) if spread_phrase_scope_wide_gap_realized_gaps else None,
        "spread_phrase_scope_wide_gap_realized_gap_max": max(spread_phrase_scope_wide_gap_realized_gaps) if spread_phrase_scope_wide_gap_realized_gaps else None,
        "spread_phrase_scope_wide_gap_state_advance_protected_events": spread_phrase_scope_wide_gap_state_protected_events,
        "spread_phrase_scope_wide_gap_runtime_realization_enabled_events": spread_phrase_scope_wide_gap_runtime_realization_events,
        "spread_phrase_state_boundary_helper_cleanup_version": PIANO_PHRASE_STATE_BOUNDARY_HELPER_CLEANUP_VERSION,
        "spread_phrase_state_boundary_helper_cleanup_events": spread_phrase_state_boundary_helper_cleanup_events,
        "spread_phrase_state_boundary_helper_state_anchor_events": spread_phrase_state_boundary_helper_anchor_events,
        "spread_phrase_state_boundary_helper_legacy_alias_match_events": spread_phrase_state_boundary_helper_legacy_alias_match_events,
        "spread_phrase_state_boundary_helper_previous_state_anchor_events": spread_phrase_state_boundary_helper_previous_state_anchor_events,
        "spread_phrase_state_anchor_policy_boundary_version": PIANO_PHRASE_STATE_ANCHOR_POLICY_BOUNDARY_VERSION,
        "spread_phrase_state_anchor_policy_boundary_events": spread_phrase_state_anchor_policy_boundary_events,
        "spread_phrase_state_anchor_policy_boundary_gate_required_events": spread_phrase_state_anchor_policy_boundary_gate_required_events,
        "spread_phrase_state_anchor_policy_boundary_scopes": dict(spread_phrase_state_anchor_policy_boundary_scopes),
        "spread_phrase_state_anchor_policy_boundary_previous_gate_consumed_events": spread_phrase_state_anchor_policy_boundary_previous_gate_consumed_events,
        "spread_phrase_state_boundary_review_version": PIANO_PHRASE_STATE_BOUNDARY_REVIEW_VERSION,
        "spread_phrase_state_boundary_review_events": int(phrase_state_boundary_review.get("review_events", 0)),
        "spread_phrase_state_boundary_review_next_events_found": int(phrase_state_boundary_review.get("next_events_found", 0)),
        "spread_phrase_state_boundary_review_state_anchor_matches_override_events": int(phrase_state_boundary_review.get("state_anchor_matches_override_events", 0)),
        "spread_phrase_state_boundary_review_realized_notes_not_used_as_state_events": int(phrase_state_boundary_review.get("realized_notes_not_used_as_state_events", 0)),
        "spread_phrase_state_boundary_review_voice_leading_previous_matches_override_events": int(phrase_state_boundary_review.get("voice_leading_previous_matches_override_events", 0)),
        "spread_phrase_state_boundary_review_warning_events": int(phrase_state_boundary_review.get("warning_events", 0)),
        "spread_phrase_state_boundary_review_next_event_top_motion_max": phrase_state_boundary_review.get("next_event_top_motion_max"),
        "spread_phrase_state_boundary_review_next_event_voice_leading_distance_max": phrase_state_boundary_review.get("next_event_voice_leading_distance_max"),
        "spread_phrase_state_boundary_review_next_event_smoothness_labels": dict(phrase_state_boundary_review.get("next_event_smoothness_labels", {})),
        "ballad_spread_post_continuity_listening_checkpoint_version": PIANO_POST_CONTINUITY_LISTENING_CHECKPOINT_VERSION,
        "post_continuity_problem_bars_checked": list(post_continuity_checkpoint.get("problem_bars_checked", [])),
        "post_continuity_problem_bars_found": list(post_continuity_checkpoint.get("problem_bars_found", [])),
        "post_continuity_problem_bar_retouch_events": int(post_continuity_checkpoint.get("retouch_events", 0)),
        "post_continuity_foundation_sustain_events": int(post_continuity_checkpoint.get("foundation_sustain_events", 0)),
        "post_continuity_projection_only_retouch_events": int(post_continuity_checkpoint.get("projection_only_retouch_events", 0)),
        "post_continuity_anchor_projection_trim_events": int(post_continuity_checkpoint.get("anchor_projection_trim_events", 0)),
        "post_continuity_warning_events": int(post_continuity_checkpoint.get("warning_events", 0)),
        "post_continuity_checkpoint_passed": bool(post_continuity_checkpoint.get("checkpoint_passed", False)),
        "ballad_spread_same_chord_reattack_continuity_version": PIANO_SAME_CHORD_REATTACK_CONTINUITY_VERSION,
        "same_chord_reattack_regions_reviewed": int(same_chord_reattack_continuity.get("regions_reviewed", 0)),
        "same_chord_reattack_events": int(same_chord_reattack_continuity.get("reattack_events", 0)),
        "same_chord_reattack_region_voicing_reused_events": int(same_chord_reattack_continuity.get("region_voicing_reused_events", 0)),
        "same_chord_reattack_exact_voicing_reuse_events": int(same_chord_reattack_continuity.get("exact_voicing_reuse_events", 0)),
        "same_chord_reattack_foundation_stable_events": int(same_chord_reattack_continuity.get("foundation_stable_events", 0)),
        "same_chord_reattack_projection_or_retouch_events": int(same_chord_reattack_continuity.get("projection_or_retouch_events", 0)),
        "same_chord_reattack_fresh_revoicing_events": int(same_chord_reattack_continuity.get("fresh_revoicing_events", 0)),
        "same_chord_reattack_changed_voicing_warning_events": int(same_chord_reattack_continuity.get("changed_voicing_warning_events", 0)),
        "same_chord_reattack_continuity_warning_events": int(same_chord_reattack_continuity.get("warning_events", 0)),
        "same_chord_reattack_continuity_checkpoint_passed": bool(same_chord_reattack_continuity.get("checkpoint_passed", False)),
        "ballad_spread_safe_extension_frequency_calibration_version": PIANO_SAFE_EXTENSION_FREQUENCY_CALIBRATION_VERSION,
        "major_seventh_safe_extension_events": major_seventh_events,
        "major_seventh_safe_extension_color_events": major_seventh_color_events,
        "major_seventh_safe_extension_warm_color_events": major_seventh_safe_color_events,
        "major_seventh_safe_extension_degree_counts": dict(major_seventh_colors),
        "major_seventh_safe_extension_degree_counts_by_chord": {key: dict(counter) for key, counter in major_seventh_colors_by_chord.items()},
        "major_seventh_safe_extension_non_safe_color_events_by_chord": dict(major_seventh_non_safe_color_events_by_chord),
        "major_seventh_unnotated_sharp11_events": major_seventh_unnotated_sharp11_events,
        "major_seventh_explicit_sharp11_events": major_seventh_explicit_sharp11_events,
        "major_seventh_safe_extension_preferred_colors": ["9", "13"],
        "major_seventh_safe_extension_checkpoint_passed": bool(
            major_seventh_events
            and major_seventh_unnotated_sharp11_events == 0
            and set(major_seventh_colors).issubset({"9", "13"})
        ),
        "low_note_min": min(all_midi_notes) if all_midi_notes else None,
        "top_note_max": max(all_midi_notes) if all_midi_notes else None,
        "top_note_ge_75_events": top_note_ge_75_events,
        "voicing_texture_scope_counts": dict(texture_scope_counter),
        "voicing_texture_contrast_roles": dict(texture_contrast_counter),
        "voicing_texture_methods_by_contrast_role": {key: dict(counter) for key, counter in texture_methods_by_contrast.items()},
        "voicing_texture_method_percentages_by_contrast_role": _counter_percentages_by_key(texture_methods_by_contrast),
        "voicing_texture_methods_by_scope": {key: dict(counter) for key, counter in texture_methods_by_scope.items()},
        "voicing_texture_open_method_weight_plans_by_contrast_role": texture_weight_plan_by_contrast,
        "migrated_projection_paths": dict(migrated_projection_path_counter),
        "legacy_projection_callback_used_count": legacy_projection_callback_used_count,
        "legacy_projection_cleanup_required_count": legacy_projection_cleanup_required_count,
        "open_named_projection_methods": dict(open_named_projection_counter),
        "open_named_projection_events": sum(open_named_projection_counter.values()),
        "avg_open_named_projection_span": round(mean(open_named_projection_spans), 3) if open_named_projection_spans else 0.0,
        "max_open_named_projection_span": max(open_named_projection_spans) if open_named_projection_spans else None,
        "min_open_named_projection_lowest_note": min(open_named_projection_lows) if open_named_projection_lows else None,
        "avg_open_named_projection_parent_closed_span": round(mean(open_named_projection_parent_closed_spans), 3) if open_named_projection_parent_closed_spans else 0.0,
        "max_open_named_projection_parent_closed_span": max(open_named_projection_parent_closed_spans) if open_named_projection_parent_closed_spans else None,
        "open_drop2_events": open_drop2_count,
        "avg_open_drop2_span": round(mean(open_drop2_spans), 3) if open_drop2_spans else 0.0,
        "max_open_drop2_span": max(open_drop2_spans) if open_drop2_spans else None,
        "min_open_drop2_lowest_note": min(open_drop2_lows) if open_drop2_lows else None,
        "avg_open_drop2_parent_closed_span": round(mean(open_drop2_parent_closed_spans), 3) if open_drop2_parent_closed_spans else 0.0,
        "max_open_drop2_parent_closed_span": max(open_drop2_parent_closed_spans) if open_drop2_parent_closed_spans else None,
        "root_support": dict(root_support_counter),
        "rootless_events": rootless_count,
        "root_included_events": root_included_count,
        "four_note_source_balance_gate_modes": dict(source_gate_counter),
        "four_note_source_balance_keys": dict(source_key_counter),
        "three_note_source_types": dict(three_note_source_type_counter),
        "three_note_source_role_orders": dict(three_note_source_role_counter),
        "three_note_degree_orders": dict(three_note_degree_order_counter),
        "triad_4note_source_types": dict(triad_4note_source_type_counter),
        "triad_4note_source_role_orders": dict(triad_4note_source_role_counter),
        "triad_4note_degree_orders": dict(triad_4note_degree_order_counter),
        "avg_four_note_source_balance_score": round(mean(source_scores), 3) if source_scores else 0.0,
        "avg_chart_color_fidelity_score": round(mean(fidelity_scores), 3) if fidelity_scores else 0.0,
        "region_voicing_reuse_count": region_voicing_reuse_count,
        "closed_minimum_motion_events": closed_minimum_motion_count,
        "closed_3note_minimum_motion_events": closed_3note_minimum_motion_count,
        "closed_4note_minimum_motion_events": closed_4note_minimum_motion_count,
        "avg_closed_3note_source_collapse_distance": round(mean(closed_3note_collapse_distances), 3) if closed_3note_collapse_distances else 0.0,
        "max_closed_3note_source_collapse_distance": round(max(closed_3note_collapse_distances), 3) if closed_3note_collapse_distances else 0.0,
        "avg_closed_3note_source_collapse_total_motion": round(mean(closed_3note_collapse_total_motions), 3) if closed_3note_collapse_total_motions else 0.0,
        "max_closed_3note_source_collapse_total_motion": round(max(closed_3note_collapse_total_motions), 3) if closed_3note_collapse_total_motions else 0.0,
        "avg_closed_4note_source_collapse_distance": round(mean(closed_4note_collapse_distances), 3) if closed_4note_collapse_distances else 0.0,
        "max_closed_4note_source_collapse_distance": round(max(closed_4note_collapse_distances), 3) if closed_4note_collapse_distances else 0.0,
        "avg_closed_4note_source_collapse_total_motion": round(mean(closed_4note_collapse_total_motions), 3) if closed_4note_collapse_total_motions else 0.0,
        "max_closed_4note_source_collapse_total_motion": round(max(closed_4note_collapse_total_motions), 3) if closed_4note_collapse_total_motions else 0.0,
        "min_closed_voicing_lowest_note": min(closed_lows) if closed_lows else None,
        "max_closed_voicing_span": max(closed_spans) if closed_spans else None,
        "avg_realized_notes_per_event": round(mean(note_counts), 3) if note_counts else 0.0,
        "avg_duration_beats": round(mean(durations), 3) if durations else 0.0,
        "avg_velocity": round(mean(velocities), 3) if velocities else 0.0,
        "failed_register_guard_count": failed_register_guard_count,
        "missing_note_events": suppressed_or_missing_note_count,
        "register_guard_reasons": dict(register_reason_counter),
        "expression_audit": debug.get("expression_foundation_audit", {}),
        "expression_flags": dict(expression_flag_counter),
    }
    return PianoMusicalAudit(summary=summary, event_rows=rows, warnings=warnings)


def format_piano_musical_audit_report(debug: Mapping[str, Any], *, max_events: int | None = None) -> str:
    audit = build_piano_musical_audit(debug)
    summary = audit.summary
    rows = audit.event_rows if max_events is None else audit.event_rows[:max_events]

    lines: list[str] = []
    lines.append("# Piano Musical Debug Audit")
    lines.append("")
    lines.append(f"- Contract version: `{summary.get('contract_version')}`")
    lines.append(f"- Title: `{summary.get('title')}`")
    lines.append(f"- Style: `{summary.get('style')}`")
    lines.append(f"- Events audited: `{summary.get('events')}`")
    lines.append(f"- Note events by track: `{summary.get('note_events_by_track')}`")
    lines.append(f"- Timing policy: `{summary.get('timing_policy')}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Top patterns: `{summary.get('top_patterns')}`")
    lines.append(f"- Gestures: `{summary.get('gestures')}`")
    lines.append(f"- Expression profiles: `{summary.get('expression_profiles')}`")
    lines.append(f"- Articulations: `{summary.get('articulations')}`")
    lines.append(f"- Content families: `{summary.get('content_families')}`")
    lines.append(f"- Densities: `{summary.get('densities')}`")
    lines.append(f"- Functional groupings: `{summary.get('functional_groupings')}`")
    lines.append(f"- Dispositions: `{summary.get('dispositions')}`")
    lines.append(f"- Disposition projection families: `{summary.get('disposition_projection_families')}`")
    lines.append(f"- Disposition projection methods: `{summary.get('disposition_projection_methods')}`")
    lines.append(f"- Drop projection methods total: `{summary.get('drop_projection_methods_total')}`")
    lines.append(f"- Drop projection methods by scope: `{summary.get('drop_projection_methods_by_scope')}`")
    lines.append(f"- SPREAD upper projection methods: `{summary.get('spread_upper_projection_methods')}`")
    lines.append(f"- SPREAD upper drop projection methods: `{summary.get('spread_upper_drop_projection_methods')}`")
    lines.append(f"- SPREAD upper drop projection methods by density: `{summary.get('spread_upper_drop_projection_methods_by_density')}`")
    lines.append(f"- SPREAD upper drop projection methods by grouping: `{summary.get('spread_upper_drop_projection_methods_by_grouping')}`")
    lines.append(f"- Lower foundation note min / max / average: `{summary.get('lower_foundation_note_min')}` / `{summary.get('lower_foundation_note_max')}` / `{summary.get('lower_foundation_note_average')}`")
    lines.append(f"- Lower foundation span max / average: `{summary.get('lower_foundation_span_max')}` / `{summary.get('lower_foundation_span_average')}`")
    lines.append(f"- Lower/upper group gap min / max / average: `{summary.get('lower_upper_group_gap_min')}` / `{summary.get('lower_upper_group_gap_max')}` / `{summary.get('lower_upper_group_gap_average')}`")
    lines.append(f"- Lower/upper group gap by grouping: `{summary.get('lower_upper_group_gap_by_grouping')}`")
    lines.append(f"- Lower/upper group gap tight / wide events: `{summary.get('lower_upper_group_gap_too_tight_events')}` / `{summary.get('lower_upper_group_gap_too_wide_events')}`")
    lines.append(f"- Phrase-scope wide-gap availability events: `{summary.get('spread_phrase_scope_wide_gap_candidate_availability_events')}`")
    lines.append(f"- Phrase-scope wide-gap original / realized gap: `{summary.get('spread_phrase_scope_wide_gap_original_gap_min')}`-`{summary.get('spread_phrase_scope_wide_gap_original_gap_max')}` / `{summary.get('spread_phrase_scope_wide_gap_realized_gap_min')}`-`{summary.get('spread_phrase_scope_wide_gap_realized_gap_max')}`")
    lines.append(f"- Phrase-scope state-protected / runtime-realized events: `{summary.get('spread_phrase_scope_wide_gap_state_advance_protected_events')}` / `{summary.get('spread_phrase_scope_wide_gap_runtime_realization_enabled_events')}`")
    lines.append(f"- Phrase state boundary review events / warnings: `{summary.get('spread_phrase_state_boundary_review_events')}` / `{summary.get('spread_phrase_state_boundary_review_warning_events')}`")
    lines.append(f"- Phrase state boundary next-event motion max: top `{summary.get('spread_phrase_state_boundary_review_next_event_top_motion_max')}`, voice-leading `{summary.get('spread_phrase_state_boundary_review_next_event_voice_leading_distance_max')}`")
    lines.append(f"- Post-continuity checkpoint pass / warnings: `{summary.get('post_continuity_checkpoint_passed')}` / `{summary.get('post_continuity_warning_events')}`")
    lines.append(f"- Post-continuity bars found: `{summary.get('post_continuity_problem_bars_found')}`")
    lines.append(f"- Same-chord reattack reuse / warnings: `{summary.get('same_chord_reattack_region_voicing_reused_events')}` / `{summary.get('same_chord_reattack_continuity_warning_events')}`")
    lines.append(f"- Same-chord reattack exact voicing / foundation stable: `{summary.get('same_chord_reattack_exact_voicing_reuse_events')}` / `{summary.get('same_chord_reattack_foundation_stable_events')}`")
    lines.append(f"- Maj7 safe extension colors: `{summary.get('major_seventh_safe_extension_degree_counts')}`; unnotated #11 events: `{summary.get('major_seventh_unnotated_sharp11_events')}`")
    lines.append(f"- Maj7 safe extension checkpoint: `{summary.get('major_seventh_safe_extension_checkpoint_passed')}`")
    lines.append(f"- Lower foundation notes by grouping: `{summary.get('lower_foundation_notes_by_grouping')}`")
    lines.append(f"- Lower foundation recipe counts: `{summary.get('lower_foundation_recipe_counts')}`")
    lines.append(f"- Lower foundation low-register events: `{summary.get('lower_foundation_low_register_events')}`")
    lines.append(f"- Lower foundation span violation events: `{summary.get('lower_foundation_span_violation_events')}`")
    lines.append(f"- Low note min / top note max / top >= 75 events: `{summary.get('low_note_min')}` / `{summary.get('top_note_max')}` / `{summary.get('top_note_ge_75_events')}`")
    lines.append(f"- Texture contrast roles: `{summary.get('voicing_texture_contrast_roles')}`")
    lines.append(f"- Texture methods by contrast role: `{summary.get('voicing_texture_methods_by_contrast_role')}`")
    lines.append(f"- Texture method percentages by contrast role: `{summary.get('voicing_texture_method_percentages_by_contrast_role')}`")
    lines.append(f"- Texture open method weight plans by contrast role: `{summary.get('voicing_texture_open_method_weight_plans_by_contrast_role')}`")
    lines.append(f"- Migrated projection paths: `{summary.get('migrated_projection_paths')}`")
    lines.append(f"- Legacy projection callback used / cleanup required: `{summary.get('legacy_projection_callback_used_count')}` / `{summary.get('legacy_projection_cleanup_required_count')}`")
    lines.append(f"- OPEN named projection methods: `{summary.get('open_named_projection_methods')}`")
    lines.append(f"- OPEN named projection events: `{summary.get('open_named_projection_events')}`")
    lines.append(f"- Avg / max OPEN named projection span: `{summary.get('avg_open_named_projection_span')}` / `{summary.get('max_open_named_projection_span')}`")
    lines.append(f"- Min OPEN named projection lowest note: `{summary.get('min_open_named_projection_lowest_note')}`")
    lines.append(f"- Avg / max OPEN named parent-closed span: `{summary.get('avg_open_named_projection_parent_closed_span')}` / `{summary.get('max_open_named_projection_parent_closed_span')}`")
    lines.append(f"- OPEN/DROP2 events: `{summary.get('open_drop2_events')}`")
    lines.append(f"- Avg / max OPEN/DROP2 span: `{summary.get('avg_open_drop2_span')}` / `{summary.get('max_open_drop2_span')}`")
    lines.append(f"- Min OPEN/DROP2 lowest note: `{summary.get('min_open_drop2_lowest_note')}`")
    lines.append(f"- Avg / max DROP2 parent-closed span: `{summary.get('avg_open_drop2_parent_closed_span')}` / `{summary.get('max_open_drop2_parent_closed_span')}`")
    lines.append(f"- Root support: `{summary.get('root_support')}`")
    lines.append(f"- Rootless / root-included events: `{summary.get('rootless_events')}` / `{summary.get('root_included_events')}`")
    lines.append(f"- 4-note source balance gates: `{summary.get('four_note_source_balance_gate_modes')}`")
    lines.append(f"- 4-note source balance keys: `{summary.get('four_note_source_balance_keys')}`")
    lines.append(f"- 3-note source types: `{summary.get('three_note_source_types')}`")
    lines.append(f"- 3-note source role orders: `{summary.get('three_note_source_role_orders')}`")
    lines.append(f"- Triad 4-note source types: `{summary.get('triad_4note_source_types')}`")
    lines.append(f"- Triad 4-note source role orders: `{summary.get('triad_4note_source_role_orders')}`")
    lines.append(f"- Avg source balance score: `{summary.get('avg_four_note_source_balance_score')}`")
    lines.append(f"- Avg chart color fidelity score: `{summary.get('avg_chart_color_fidelity_score')}`")
    lines.append(f"- Region voicing reuse count: `{summary.get('region_voicing_reuse_count')}`")
    lines.append(f"- Closed minimum-motion events: `{summary.get('closed_minimum_motion_events')}`")
    lines.append(f"- Closed 3-note minimum-motion events: `{summary.get('closed_3note_minimum_motion_events')}`")
    lines.append(f"- Closed 4-note minimum-motion events: `{summary.get('closed_4note_minimum_motion_events')}`")
    lines.append(f"- Avg / max 3-note per-source collapse distance: `{summary.get('avg_closed_3note_source_collapse_distance')}` / `{summary.get('max_closed_3note_source_collapse_distance')}`")
    lines.append(f"- Avg / max 3-note per-source collapse total motion: `{summary.get('avg_closed_3note_source_collapse_total_motion')}` / `{summary.get('max_closed_3note_source_collapse_total_motion')}`")
    lines.append(f"- Avg / max 4-note per-source collapse distance: `{summary.get('avg_closed_4note_source_collapse_distance')}` / `{summary.get('max_closed_4note_source_collapse_distance')}`")
    lines.append(f"- Avg / max 4-note per-source collapse total motion: `{summary.get('avg_closed_4note_source_collapse_total_motion')}` / `{summary.get('max_closed_4note_source_collapse_total_motion')}`")
    lines.append(f"- Min closed lowest note / max closed span: `{summary.get('min_closed_voicing_lowest_note')}` / `{summary.get('max_closed_voicing_span')}`")
    lines.append(f"- Avg realized notes per event: `{summary.get('avg_realized_notes_per_event')}`")
    lines.append(f"- Avg duration beats: `{summary.get('avg_duration_beats')}`")
    lines.append(f"- Avg velocity: `{summary.get('avg_velocity')}`")
    lines.append(f"- Failed register guard count: `{summary.get('failed_register_guard_count')}`")
    lines.append(f"- Missing note events: `{summary.get('missing_note_events')}`")
    lines.append(f"- Expression audit: `{summary.get('expression_audit')}`")
    lines.append(f"- Expression flags: `{summary.get('expression_flags')}`")
    lines.append("")
    lines.append("## Warnings")
    lines.append("")
    if audit.warnings:
        for warning in audit.warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Piano Event Trace")
    lines.append("")
    lines.append(
        "| # | Event | Region | Chord | Beat | Pattern | Gesture | Expr | Dur | Vel | ExprFlags | Voicing | SourceGate | SourceKey | SourceScore | FidelityScore | VLSource | Degrees | Notes | Root | Guard | Selector | Performed |"
    )
    lines.append(
        "|---:|---|---|---|---:|---|---|---|---:|---:|---|---|---|---|---:|---:|---|---|---|---|---|---|---|"
    )
    for row in rows:
        lines.append(
            "| {index} | `{event_id}` | `{region_id}` | `{chord}` | {beat:.3f} | `{pattern}` | `{gesture}` | `{expr}` | {duration:.3f} | {velocity} | `{expr_flags}` | `{voicing}` | `{source_gate}` | `{source_key}` | {source_score:.3f} | {fidelity_score:.3f} | `{degrees}` | `{notes}` | `{root}` | `{guard}` | `{selector}` | `{performed}` |".format(
                index=row["index"],
                event_id=row["event_id"],
                region_id=row["region_id"],
                chord=row["chord_symbol"],
                beat=float(row["onset_beat"]),
                pattern=row["pattern_id"] or "unknown",
                gesture=row["gesture_type"] or "unknown",
                expr=row["expression_profile"] or "unknown",
                duration=float(row["duration_beats"] or 0.0),
                velocity=int(row["velocity"] or 0),
                expr_flags=",".join(row.get("expression_flags") or []),
                voicing=_voicing_cell(row),
                source_gate=row.get("four_note_source_balance_gate_mode") or "",
                source_key=row.get("four_note_source_balance_key") or "",
                source_score=float(row.get("four_note_source_balance_score") or 0.0),
                fidelity_score=float(row.get("chart_color_fidelity_score") or 0.0),
                vl_source=_vl_source_cell(row),
                degrees=" ".join(row["degrees"]),
                notes=" ".join(str(note) for note in row["midi_notes"]),
                root="yes" if row["root_included"] else "no",
                guard=",".join(row["register_guard_reasons"]),
                selector=row["selector_mode"],
                performed=_performed_cell(row),
            )
        )
    if max_events is not None and len(audit.event_rows) > max_events:
        lines.append("")
        lines.append(f"Report truncated to first {max_events} events out of {len(audit.event_rows)}.")
    lines.append("")
    lines.append("## Reading Notes")
    lines.append("")
    lines.append("- This report is observational. It summarizes what the runtime already selected; it does not reselect pattern, expression, voicing, timing, or notes.")
    lines.append("- `Beat` is the logical grid beat before the renderer timing policy. `Performed` shows the style timing interpretation for the event starts.")
    lines.append("- `Voicing` compresses content family, density, functional grouping, disposition, and recipe id.")
    lines.append("- `Guard` comes from the core register/span/mud diagnostic contract. It is not yet a full musicality score.")
    lines.append("- Use this audit before style musicality tuning so every bad-sounding piano event can be traced to pattern, expression, voicing, or timing.")
    lines.append("")
    return "\n".join(lines)




def _annotate_same_chord_reattack_continuity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Audit same-chord reattack voicing stability inside one chord region.

    v2_6_41 is intentionally conservative.  The realizer already owns the
    one-default-voicing-per-chord-region cache, which is the correct boundary
    for Ballad re-touches: repeated touches should reuse the same voicing unless
    an event explicitly asks for fresh revoicing.  This audit makes that behavior
    visible before any future same-chord movement/fill exceptions are added.
    """

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (str(row.get("region_id") or ""), str(row.get("chord_symbol") or ""), str(row.get("event_id") or "").split("_")[-1] if False else "piano")
        grouped.setdefault(key, []).append(row)

    regions_reviewed = 0
    reattack_events = 0
    region_voicing_reused_events = 0
    exact_voicing_reuse_events = 0
    foundation_stable_events = 0
    projection_or_retouch_events = 0
    fresh_revoicing_events = 0
    changed_voicing_warning_events = 0
    warning_events = 0

    for group_rows in grouped.values():
        ordered = sorted(group_rows, key=lambda row: (float(row.get("onset_beat") or 0.0), int(row.get("index") or 0)))
        if len(ordered) <= 1:
            continue
        anchor = ordered[0]
        anchor_event_id = str(anchor.get("event_id") or "")
        anchor_notes = tuple(int(note) for note in anchor.get("midi_notes") or ())
        anchor_lower = tuple(int(note) for note in anchor.get("lower_group_notes") or ())
        if not anchor_notes:
            continue
        regions_reviewed += 1
        for row in ordered[1:]:
            reattack_events += 1
            notes = tuple(int(note) for note in row.get("midi_notes") or ())
            lower = tuple(int(note) for note in row.get("lower_group_notes") or ())
            reused = bool(row.get("region_voicing_reused")) and str(row.get("region_voicing_source_event_id") or "") == anchor_event_id
            exact_reuse = notes == anchor_notes
            foundation_stable = lower == anchor_lower
            projection_or_retouch = str(row.get("gesture_type") or "") in {"inner_movement", "simultaneous_onset"} and str(row.get("expression_profile") or "") in {"soft_retouch", "soft_answer", "soft_whisper"}
            warning = not reused or not exact_reuse or not foundation_stable
            if reused:
                region_voicing_reused_events += 1
            else:
                fresh_revoicing_events += 1
            if exact_reuse:
                exact_voicing_reuse_events += 1
            else:
                changed_voicing_warning_events += 1
            if foundation_stable:
                foundation_stable_events += 1
            if projection_or_retouch:
                projection_or_retouch_events += 1
            if warning:
                warning_events += 1
            row.update(
                {
                    "same_chord_reattack_continuity_version": PIANO_SAME_CHORD_REATTACK_CONTINUITY_VERSION,
                    "same_chord_reattack_continuity_applied": True,
                    "same_chord_reattack_anchor_event_id": anchor_event_id,
                    "same_chord_reattack_region_voicing_reused": reused,
                    "same_chord_reattack_exact_voicing_reuse": exact_reuse,
                    "same_chord_reattack_foundation_stable": foundation_stable,
                    "same_chord_reattack_projection_or_retouch": projection_or_retouch,
                    "same_chord_reattack_warning": warning,
                    "same_chord_reattack_scope": "same_chord_region_cached_voicing_reuse_until_explicit_fresh_revoicing",
                    "same_chord_reattack_no_density_lane_change": True,
                    "same_chord_reattack_no_selector_change": True,
                }
            )

    checkpoint_passed = reattack_events > 0 and warning_events == 0 and region_voicing_reused_events == reattack_events
    return {
        "regions_reviewed": regions_reviewed,
        "reattack_events": reattack_events,
        "region_voicing_reused_events": region_voicing_reused_events,
        "exact_voicing_reuse_events": exact_voicing_reuse_events,
        "foundation_stable_events": foundation_stable_events,
        "projection_or_retouch_events": projection_or_retouch_events,
        "fresh_revoicing_events": fresh_revoicing_events,
        "changed_voicing_warning_events": changed_voicing_warning_events,
        "warning_events": warning_events,
        "checkpoint_passed": checkpoint_passed,
    }


def _annotate_post_continuity_listening_checkpoint(
    rows: list[dict[str, Any]],
    timing_policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Review the accepted v2_6_38 Ballad 1& continuity patch.

    This is observational only.  It focuses on the three performance bars the
    user flagged before returning to voicing work.  The check verifies that the
    1& touch is a projection-group re-touch and that lower/foundation notes
    from the anchor sustain through that re-touch rather than being cut off.
    """

    problem_bars = (41, 63, 95)
    problem_bar_set = set(problem_bars)
    rows_by_region: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        rows_by_region.setdefault(str(row.get("region_id") or ""), []).append(row)

    bars_found: list[int] = []
    retouch_events = 0
    foundation_sustain_events = 0
    projection_only_retouch_events = 0
    anchor_projection_trim_events = 0
    warning_events = 0

    for row in rows:
        bar = int(float(row.get("onset_beat") or 0.0) // 4) + 1
        if bar not in problem_bar_set:
            continue
        if row.get("pattern_id") != "ballad_piano_downbeat_1and_whisper":
            continue
        if row.get("gesture_type") != "inner_movement":
            continue
        if float(row.get("local_beat") or 0.0) != 0.5:
            continue

        retouch_events += 1
        bars_found.append(bar)
        region_rows = rows_by_region.get(str(row.get("region_id") or ""), [])
        anchor_candidates = [
            candidate
            for candidate in region_rows
            if candidate.get("pattern_id") == "ballad_piano_downbeat_1and_whisper"
            and candidate.get("gesture_type") == "simultaneous_onset"
            and float(candidate.get("onset_beat") or 0.0) < float(row.get("onset_beat") or 0.0)
        ]
        anchor = anchor_candidates[-1] if anchor_candidates else None
        retouch_notes = [note for note in row.get("realized_notes") or [] if isinstance(note, Mapping)]
        anchor_notes = [note for note in (anchor or {}).get("realized_notes", []) if isinstance(note, Mapping)]

        retouch_starts = [_performed_note_start(note, timing_policy) for note in retouch_notes]
        retouch_ends = [_performed_note_end(note, timing_policy) for note in retouch_notes]
        retouch_start = min(retouch_starts) if retouch_starts else None
        retouch_end = max(retouch_ends) if retouch_ends else None
        anchor_ends = [_performed_note_end(note, timing_policy) for note in anchor_notes]

        foundation_sustain_count = 0
        projection_trim_count = 0
        if retouch_end is not None:
            foundation_sustain_count = sum(1 for end in anchor_ends if end >= retouch_end - 1e-6)
        if retouch_start is not None:
            projection_trim_count = sum(1 for end in anchor_ends if abs(end - retouch_start) < 1e-6)

        projection_only = bool(retouch_notes) and {str(note.get("projection_ref") or "") for note in retouch_notes} == {"projection_group"}
        foundation_ok = foundation_sustain_count >= 2
        trim_ok = projection_trim_count >= 3
        warning = not anchor or not projection_only or not foundation_ok or not trim_ok
        if projection_only:
            projection_only_retouch_events += 1
        if foundation_ok:
            foundation_sustain_events += 1
        if trim_ok:
            anchor_projection_trim_events += 1
        if warning:
            warning_events += 1

        row.update(
            {
                "post_continuity_listening_checkpoint_version": PIANO_POST_CONTINUITY_LISTENING_CHECKPOINT_VERSION,
                "post_continuity_listening_checkpoint_applied": True,
                "post_continuity_problem_bar": bar,
                "post_continuity_anchor_event_id": (anchor or {}).get("event_id"),
                "post_continuity_retouch_projection_only": projection_only,
                "post_continuity_foundation_notes_sustaining_through_retouch": foundation_sustain_count,
                "post_continuity_projection_notes_trimmed_to_retouch_start": projection_trim_count,
                "post_continuity_warning": warning,
                "post_continuity_scope": "accepted_ballad_1and_whisper_continuity_observational_only",
                "post_continuity_no_voicing_selector_change": True,
            }
        )

    checkpoint_passed = (
        sorted(bars_found) == list(problem_bars)
        and retouch_events == len(problem_bars)
        and foundation_sustain_events == len(problem_bars)
        and projection_only_retouch_events == len(problem_bars)
        and anchor_projection_trim_events == len(problem_bars)
        and warning_events == 0
    )
    return {
        "problem_bars_checked": list(problem_bars),
        "problem_bars_found": sorted(bars_found),
        "retouch_events": retouch_events,
        "foundation_sustain_events": foundation_sustain_events,
        "projection_only_retouch_events": projection_only_retouch_events,
        "anchor_projection_trim_events": anchor_projection_trim_events,
        "warning_events": warning_events,
        "checkpoint_passed": checkpoint_passed,
    }


def _performed_note_start(note: Mapping[str, Any], timing_policy: Mapping[str, Any]) -> float:
    return performed_beat(
        float(note.get("start_beat", 0.0) or 0.0),
        str(note.get("timing_intent") or "auto"),
        timing_policy,
    )


def _performed_note_end(note: Mapping[str, Any], timing_policy: Mapping[str, Any]) -> float:
    return _performed_note_start(note, timing_policy) + float(note.get("duration_beats", 0.0) or 0.0)


def _annotate_phrase_state_boundary_review(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Review v2_6_35 state-advance protection at the next-event boundary.

    This is observational only.  It verifies that rows realized with the
    phrase-scope wide-gap candidate still advance subsequent voicing continuity
    from the protected phrase anchor rather than from the substituted notes.
    """

    review_events = 0
    next_events_found = 0
    state_anchor_matches_override_events = 0
    realized_notes_not_used_as_state_events = 0
    voice_leading_previous_matches_override_events = 0
    warning_events = 0
    top_motions: list[float] = []
    distances: list[float] = []
    smoothness_labels: Counter[str] = Counter()

    for index, row in enumerate(rows[:-1]):
        if not row.get("spread_phrase_scope_wide_gap_candidate_availability_applied"):
            continue
        review_events += 1
        next_row = rows[index + 1]
        next_events_found += 1
        override_notes = tuple(int(note) for note in row.get("spread_phrase_scope_wide_gap_state_advance_override_notes") or [])
        realized_notes = tuple(int(note) for note in row.get("midi_notes") or [])
        next_previous_state_notes = tuple(int(note) for note in next_row.get("previous_voicing_state_previous_notes") or [])
        next_voice_leading_previous_notes = tuple(int(note) for note in next_row.get("voice_leading_previous_notes") or [])

        state_anchor_matches = bool(override_notes) and next_previous_state_notes == override_notes
        voice_leading_previous_matches = bool(override_notes) and next_voice_leading_previous_notes == override_notes
        realized_notes_not_used = bool(realized_notes) and next_previous_state_notes != realized_notes
        next_top_motion = _safe_float(next_row.get("voice_leading_top_voice_motion"))
        next_distance = _safe_float(next_row.get("voice_leading_distance"))
        next_label = str(next_row.get("voice_leading_smoothness_label") or "unknown")
        if next_top_motion is not None:
            top_motions.append(abs(next_top_motion))
        if next_distance is not None:
            distances.append(next_distance)
        smoothness_labels.update([next_label])

        # This boundary review is intentionally conservative: it should flag a
        # warning only when the protected state was not actually used or when the
        # immediate next event shows a large continuity jump.
        warning = (
            not state_anchor_matches
            or not voice_leading_previous_matches
            or not realized_notes_not_used
            or (next_top_motion is not None and abs(next_top_motion) > 2.0)
            or (next_distance is not None and next_distance > 6.0)
        )
        if state_anchor_matches:
            state_anchor_matches_override_events += 1
        if voice_leading_previous_matches:
            voice_leading_previous_matches_override_events += 1
        if realized_notes_not_used:
            realized_notes_not_used_as_state_events += 1
        if warning:
            warning_events += 1

        row.update(
            {
                "spread_phrase_state_boundary_review_version": PIANO_PHRASE_STATE_BOUNDARY_REVIEW_VERSION,
                "spread_phrase_state_boundary_review_applied": True,
                "spread_phrase_state_boundary_review_next_event_id": next_row.get("event_id"),
                "spread_phrase_state_boundary_review_next_chord_symbol": next_row.get("chord_symbol"),
                "spread_phrase_state_boundary_review_next_midi_notes": list(next_row.get("midi_notes") or []),
                "spread_phrase_state_boundary_review_state_anchor_matches_override": state_anchor_matches,
                "spread_phrase_state_boundary_review_voice_leading_previous_matches_override": voice_leading_previous_matches,
                "spread_phrase_state_boundary_review_realized_notes_not_used_as_state": realized_notes_not_used,
                "spread_phrase_state_boundary_review_next_top_motion": next_top_motion,
                "spread_phrase_state_boundary_review_next_voice_leading_distance": next_distance,
                "spread_phrase_state_boundary_review_next_smoothness_label": next_label,
                "spread_phrase_state_boundary_review_warning": warning,
                "spread_phrase_state_boundary_review_scope": "next_event_state_advance_boundary_observational_only",
                "spread_phrase_state_boundary_review_no_runtime_change": True,
            }
        )
        next_row.update(
            {
                "spread_phrase_state_boundary_review_after_protected_event": True,
                "spread_phrase_state_boundary_review_previous_protected_event_id": row.get("event_id"),
                "spread_phrase_state_boundary_review_previous_override_notes": list(override_notes),
                "spread_phrase_state_boundary_review_previous_realized_notes": list(realized_notes),
                "spread_phrase_state_boundary_review_state_anchor_matches_override": state_anchor_matches,
            }
        )

    return {
        "review_events": review_events,
        "next_events_found": next_events_found,
        "state_anchor_matches_override_events": state_anchor_matches_override_events,
        "realized_notes_not_used_as_state_events": realized_notes_not_used_as_state_events,
        "voice_leading_previous_matches_override_events": voice_leading_previous_matches_override_events,
        "warning_events": warning_events,
        "next_event_top_motion_max": max(top_motions) if top_motions else None,
        "next_event_voice_leading_distance_max": round(max(distances), 3) if distances else None,
        "next_event_smoothness_labels": dict(smoothness_labels),
    }


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def _event_row(index: int, raw: Mapping[str, Any], timing_policy: Mapping[str, Any], expression_audit_row: Mapping[str, Any] | None = None) -> dict[str, Any]:
    event = dict(raw.get("pattern_event") or {})
    expression = dict(raw.get("expression") or {})
    voicing = dict(raw.get("voicing") or {})
    realized = list(raw.get("realized_notes") or [])
    register_guard = dict(voicing.get("register_guard") or {})
    selector = dict(voicing.get("selector_decision") or {})
    voicing_metadata = dict(voicing.get("metadata") or {})
    upper_projection_metadata = dict(voicing_metadata.get("upper_projection_metadata") or {})
    expression_audit_row = dict(expression_audit_row or {})
    logical_starts = [float(note.get("start_beat", 0.0)) for note in realized if isinstance(note, Mapping)]
    performed = [performed_beat(start, str(note.get("timing_intent", "auto")), timing_policy) for start, note in zip(logical_starts, realized)]
    return {
        "index": index,
        "event_id": str(event.get("event_id", raw.get("event_id", ""))),
        "region_id": str(event.get("region_id", "")),
        "chord_symbol": str(event.get("chord_symbol", voicing.get("chord_symbol", ""))),
        "onset_beat": float(event.get("onset_beat", 0.0) or 0.0),
        "local_beat": event.get("local_beat"),
        "pattern_id": event.get("pattern_id"),
        "gesture_type": event.get("gesture_type"),
        "expression_hint": event.get("expression_hint"),
        "expression_profile": expression.get("profile_name"),
        "articulation": expression.get("articulation"),
        "duration_beats": expression.get("duration_beats"),
        "velocity": expression.get("velocity"),
        "pedal": expression.get("pedal"),
        "touch": expression.get("touch"),
        "expression_flags": list(expression_audit_row.get("flags") or []),
        "expression_gap_to_next": expression_audit_row.get("gap_to_next_same_track"),
        "expression_region_remaining": expression_audit_row.get("region_remaining_beats"),
        "content_family": voicing.get("content_family"),
        "density": voicing.get("density"),
        "functional_grouping": voicing.get("functional_grouping"),
        "recipe_id": voicing.get("recipe_id"),
        "rootless_ab_content_type": voicing_metadata.get("rootless_ab_content_type"),
        "rootless_ab_orientation_family": voicing_metadata.get("rootless_ab_orientation_family"),
        "rootless_ab_inversion_index": voicing_metadata.get("rootless_ab_inversion_index"),
        "rootless_ab_degree_order": voicing_metadata.get("rootless_ab_degree_order"),
        "four_note_source_balance_key": _score_detail(voicing_metadata, "four_note_source_balance_key"),
        "four_note_source_balance_gate_mode": _score_detail(voicing_metadata, "four_note_source_balance_gate_mode"),
        "four_note_source_balance_score": _score_detail(voicing_metadata, "four_note_source_balance_score"),
        "chart_color_fidelity_score": _score_detail(voicing_metadata, "chart_color_fidelity_score"),
        "three_note_source_type": _validity_note_suffix(voicing_metadata, "three_note_functional_source_type_"),
        "three_note_source_role_order": _validity_note_suffix(voicing_metadata, "three_note_source_role_order_"),
        "three_note_degree_order": _validity_note_suffix(voicing_metadata, "three_note_degree_order_"),
        "triad_4note_source_type": _validity_note_suffix(voicing_metadata, "triad_4note_functional_content_type_"),
        "triad_4note_source_role_order": _validity_note_suffix(voicing_metadata, "triad_4note_source_role_order_"),
        "triad_4note_degree_order": _validity_note_suffix(voicing_metadata, "triad_4note_degree_order_"),
        "triad_4note_inversion_index": _validity_note_suffix(voicing_metadata, "triad_4note_inversion_index_"),
        "triad_4note_is_doubled_rotation": bool(voicing_metadata.get("triad_4note_is_doubled_rotation", False)),
        "closed_3note_per_source_minimum_motion": bool(voicing_metadata.get("closed_3note_per_source_minimum_motion", False)),
        "closed_3note_source_collapse_candidate_count": voicing_metadata.get("closed_3note_source_collapse_candidate_count"),
        "closed_3note_source_collapse_selected_distance": voicing_metadata.get("closed_3note_source_collapse_selected_distance"),
        "closed_3note_source_collapse_selected_total_motion": voicing_metadata.get("closed_3note_source_collapse_selected_total_motion"),
        "closed_3note_source_collapse_selected_top_motion": voicing_metadata.get("closed_3note_source_collapse_selected_top_motion"),
        "closed_4note_per_source_minimum_motion": bool(voicing_metadata.get("closed_4note_per_source_minimum_motion", False)),
        "closed_4note_source_collapse_candidate_count": voicing_metadata.get("closed_4note_source_collapse_candidate_count"),
        "closed_4note_source_collapse_selected_distance": voicing_metadata.get("closed_4note_source_collapse_selected_distance"),
        "closed_4note_source_collapse_selected_total_motion": voicing_metadata.get("closed_4note_source_collapse_selected_total_motion"),
        "closed_4note_source_collapse_selected_top_motion": voicing_metadata.get("closed_4note_source_collapse_selected_top_motion"),
        "closed_voicing_actual_span": voicing_metadata.get("closed_voicing_actual_span"),
        "closed_voicing_lowest_note_floor": voicing_metadata.get("closed_voicing_lowest_note_floor"),
        "region_voicing_reused": bool(voicing_metadata.get("region_voicing_reused", False)),
        "region_voicing_source_event_id": voicing_metadata.get("region_voicing_source_event_id"),
        "same_chord_reattack_continuity_metadata_version": voicing_metadata.get("same_chord_reattack_continuity_version"),
        "same_chord_reattack_continuity_region_cache_reuse": bool(voicing_metadata.get("same_chord_reattack_continuity_region_cache_reuse", False)),
        "same_chord_reattack_continuity_contract": voicing_metadata.get("same_chord_reattack_continuity_contract"),
        "voicing_texture_scope_id": _texture_scope_id_from_metadata(voicing_metadata),
        "voicing_texture_contrast_role": _texture_contrast_role_from_metadata(voicing_metadata),
        "voicing_texture_open_method_weights": _texture_open_method_weights_from_metadata(voicing_metadata),
        "voicing_texture_state_primary_family": (dict(voicing_metadata.get("voicing_texture_state") or {}).get("primary_family")),
        "voicing_texture_state_allowed_families": list((dict(voicing_metadata.get("voicing_texture_state") or {}).get("allowed_families") or [])),
        "disposition_projection_family": voicing_metadata.get("disposition_projection_family"),
        "disposition_projection_method": voicing_metadata.get("disposition_projection_method"),
        "main_drop_projection_method": _drop_projection_method_from_metadata(voicing_metadata),
        "spread_upper_projection_method": voicing_metadata.get("upper_projection_method"),
        "spread_upper_drop_projection_method": _drop_projection_method_from_metadata(upper_projection_metadata) or _drop_projection_method_name(voicing_metadata.get("upper_projection_method")),
        "spread_upper_projection_uses_drop_family_resource": bool(upper_projection_metadata.get("spread_upper_projection_uses_drop_family_resource", False)),
        "spread_upper_projection_metadata": upper_projection_metadata,
        "lower_group_recipe_id": voicing_metadata.get("lower_group_recipe_id"),
        "lower_group_notes": [int(note) for note in voicing_metadata.get("lower_group_notes") or []],
        "group_gap_semitones": voicing_metadata.get("group_gap_semitones"),
        "lower_group_span_semitones": voicing_metadata.get("lower_group_span_semitones"),
        "lower_group_max_span_semitones": voicing_metadata.get("lower_group_max_span_semitones", 12),
        "lower_foundation_low_register_threshold": voicing_metadata.get("lower_foundation_low_register_threshold", 43),
        "voice_leading_previous_notes": list((voicing_metadata.get("voice_leading_profile") or {}).get("previous_notes") or []),
        "voice_leading_distance": (voicing_metadata.get("voice_leading_profile") or {}).get("voice_leading_distance"),
        "voice_leading_top_voice_motion": (voicing_metadata.get("voice_leading_profile") or {}).get("top_voice_motion"),
        "voice_leading_smoothness_label": (voicing_metadata.get("voice_leading_profile") or {}).get("smoothness_label"),
        "previous_voicing_state_previous_notes": list((voicing_metadata.get("previous_voicing_state") or {}).get("previous_notes") or []),
        "previous_voicing_state_previous_event_id": (voicing_metadata.get("previous_voicing_state") or {}).get("previous_event_id"),
        "previous_voicing_state_previous_chord_symbol": (voicing_metadata.get("previous_voicing_state") or {}).get("previous_chord_symbol"),
        "previous_voicing_state_lower_group_notes": list(((voicing_metadata.get("previous_voicing_state") or {}).get("metadata") or {}).get("lower_group_notes") or []),
        "previous_voicing_state_upper_group_notes": list(((voicing_metadata.get("previous_voicing_state") or {}).get("metadata") or {}).get("upper_group_notes") or []),
        "previous_voicing_state_group_gap_semitones": ((voicing_metadata.get("previous_voicing_state") or {}).get("metadata") or {}).get("group_gap_semitones"),
        "previous_voicing_state_state_advance_anchor_enabled": bool(((voicing_metadata.get("previous_voicing_state") or {}).get("metadata") or {}).get("state_advance_anchor_enabled", False)),
        "previous_voicing_state_state_advance_anchor_notes": list(((voicing_metadata.get("previous_voicing_state") or {}).get("metadata") or {}).get("state_advance_anchor_notes") or []),
        "previous_voicing_state_state_advance_anchor_policy_gate_consumed": bool(((voicing_metadata.get("previous_voicing_state") or {}).get("metadata") or {}).get("state_advance_anchor_policy_gate_consumed", False)),
        "previous_voicing_state_state_advance_anchor_policy_gate_scope": ((voicing_metadata.get("previous_voicing_state") or {}).get("metadata") or {}).get("state_advance_anchor_policy_gate_scope"),
        "spread_gap_aware_candidate_scope_micro_calibration_applied": bool(voicing_metadata.get("spread_gap_aware_candidate_scope_micro_calibration_applied", False)),
        "spread_gap_aware_candidate_scope_micro_calibration_version": voicing_metadata.get("spread_gap_aware_candidate_scope_micro_calibration_version"),
        "spread_gap_aware_original_gap": voicing_metadata.get("spread_gap_aware_original_gap"),
        "spread_gap_aware_replacement_gap": voicing_metadata.get("spread_gap_aware_replacement_gap"),
        "spread_gap_aware_original_primary_cost": voicing_metadata.get("spread_gap_aware_original_primary_cost"),
        "spread_gap_aware_replacement_primary_cost": voicing_metadata.get("spread_gap_aware_replacement_primary_cost"),
        "spread_gap_aware_same_recipe_only": bool(voicing_metadata.get("spread_gap_aware_same_recipe_only", False)),
        "spread_gap_aware_density_lane_unchanged": bool(voicing_metadata.get("spread_gap_aware_density_lane_unchanged", False)),
        "spread_gap_aware_max_primary_cost_delta_used": voicing_metadata.get("spread_gap_aware_max_primary_cost_delta_used"),
        "spread_wide_gap_deferred_outlier_strategy_deferred": bool(voicing_metadata.get("spread_wide_gap_deferred_outlier_strategy_deferred", False)),
        "spread_wide_gap_deferred_outlier_strategy_version": voicing_metadata.get("spread_wide_gap_deferred_outlier_strategy_version"),
        "spread_wide_gap_deferred_original_gap": voicing_metadata.get("spread_wide_gap_deferred_original_gap"),
        "spread_wide_gap_deferred_candidate_count": voicing_metadata.get("spread_wide_gap_deferred_candidate_count"),
        "spread_wide_gap_deferred_best_replacement_gap": voicing_metadata.get("spread_wide_gap_deferred_best_replacement_gap"),
        "spread_wide_gap_deferred_top_stable_replacement_gap": voicing_metadata.get("spread_wide_gap_deferred_top_stable_replacement_gap"),
        "spread_wide_gap_deferred_original_primary_cost": voicing_metadata.get("spread_wide_gap_deferred_original_primary_cost"),
        "spread_wide_gap_deferred_best_replacement_primary_cost": voicing_metadata.get("spread_wide_gap_deferred_best_replacement_primary_cost"),
        "spread_wide_gap_deferred_top_stable_replacement_primary_cost": voicing_metadata.get("spread_wide_gap_deferred_top_stable_replacement_primary_cost"),
        "spread_wide_gap_deferred_max_primary_cost_delta": voicing_metadata.get("spread_wide_gap_deferred_max_primary_cost_delta"),
        "spread_wide_gap_deferred_same_recipe_only": bool(voicing_metadata.get("spread_wide_gap_deferred_same_recipe_only", False)),
        "spread_wide_gap_deferred_density_lane_unchanged": bool(voicing_metadata.get("spread_wide_gap_deferred_density_lane_unchanged", False)),
        "spread_wide_gap_deferred_not_broad_scorer": bool(voicing_metadata.get("spread_wide_gap_deferred_not_broad_scorer", False)),
        "spread_wide_gap_deferred_runtime_replacement_enabled": bool(voicing_metadata.get("spread_wide_gap_deferred_runtime_replacement_enabled", False)),
        "spread_wide_gap_deferred_reason": voicing_metadata.get("spread_wide_gap_deferred_reason"),
        "spread_wide_gap_source_inventory_plan_active": bool(voicing_metadata.get("spread_wide_gap_source_inventory_plan_active", False)),
        "spread_wide_gap_source_inventory_plan_version": voicing_metadata.get("spread_wide_gap_source_inventory_plan_version"),
        "spread_wide_gap_source_inventory_plan_scope": voicing_metadata.get("spread_wide_gap_source_inventory_plan_scope"),
        "spread_wide_gap_source_inventory_original_gap": voicing_metadata.get("spread_wide_gap_source_inventory_original_gap"),
        "spread_wide_gap_source_inventory_candidate_count": voicing_metadata.get("spread_wide_gap_source_inventory_candidate_count"),
        "spread_wide_gap_source_inventory_comfort_candidate_count": voicing_metadata.get("spread_wide_gap_source_inventory_comfort_candidate_count"),
        "spread_wide_gap_source_inventory_best_replacement_gap": voicing_metadata.get("spread_wide_gap_source_inventory_best_replacement_gap"),
        "spread_wide_gap_source_inventory_top_stable_replacement_gap": voicing_metadata.get("spread_wide_gap_source_inventory_top_stable_replacement_gap"),
        "spread_wide_gap_source_inventory_original_primary_cost": voicing_metadata.get("spread_wide_gap_source_inventory_original_primary_cost"),
        "spread_wide_gap_source_inventory_best_replacement_primary_cost": voicing_metadata.get("spread_wide_gap_source_inventory_best_replacement_primary_cost"),
        "spread_wide_gap_source_inventory_top_stable_replacement_primary_cost": voicing_metadata.get("spread_wide_gap_source_inventory_top_stable_replacement_primary_cost"),
        "spread_wide_gap_source_inventory_original_lower_recipe_id": voicing_metadata.get("spread_wide_gap_source_inventory_original_lower_recipe_id"),
        "spread_wide_gap_source_inventory_original_upper_source_degrees": list(voicing_metadata.get("spread_wide_gap_source_inventory_original_upper_source_degrees") or []),
        "spread_wide_gap_source_inventory_best_replacement_lower_recipe_id": voicing_metadata.get("spread_wide_gap_source_inventory_best_replacement_lower_recipe_id"),
        "spread_wide_gap_source_inventory_best_replacement_upper_source_degrees": list(voicing_metadata.get("spread_wide_gap_source_inventory_best_replacement_upper_source_degrees") or []),
        "spread_wide_gap_source_inventory_top_stable_lower_recipe_id": voicing_metadata.get("spread_wide_gap_source_inventory_top_stable_lower_recipe_id"),
        "spread_wide_gap_source_inventory_top_stable_upper_source_degrees": list(voicing_metadata.get("spread_wide_gap_source_inventory_top_stable_upper_source_degrees") or []),
        "spread_wide_gap_source_inventory_same_recipe_only": bool(voicing_metadata.get("spread_wide_gap_source_inventory_same_recipe_only", False)),
        "spread_wide_gap_source_inventory_not_broad_scorer": bool(voicing_metadata.get("spread_wide_gap_source_inventory_not_broad_scorer", False)),
        "spread_wide_gap_source_inventory_runtime_replacement_enabled": bool(voicing_metadata.get("spread_wide_gap_source_inventory_runtime_replacement_enabled", False)),
        "spread_wide_gap_source_inventory_density_lane_unchanged": bool(voicing_metadata.get("spread_wide_gap_source_inventory_density_lane_unchanged", False)),
        "spread_wide_gap_source_inventory_recommended_next_boundary": voicing_metadata.get("spread_wide_gap_source_inventory_recommended_next_boundary"),
        "spread_wide_gap_source_inventory_reason": voicing_metadata.get("spread_wide_gap_source_inventory_reason"),
        "spread_phrase_scope_wide_gap_candidate_availability_applied": bool(voicing_metadata.get("spread_phrase_scope_wide_gap_candidate_availability_applied", False)),
        "spread_phrase_scope_wide_gap_candidate_availability_version": voicing_metadata.get("spread_phrase_scope_wide_gap_candidate_availability_version"),
        "spread_phrase_scope_wide_gap_candidate_availability_scope": voicing_metadata.get("spread_phrase_scope_wide_gap_candidate_availability_scope"),
        "spread_phrase_scope_wide_gap_original_gap": voicing_metadata.get("spread_phrase_scope_wide_gap_original_gap"),
        "spread_phrase_scope_wide_gap_realized_gap": voicing_metadata.get("spread_phrase_scope_wide_gap_realized_gap"),
        "spread_phrase_scope_wide_gap_best_replacement_gap": voicing_metadata.get("spread_phrase_scope_wide_gap_best_replacement_gap"),
        "spread_phrase_scope_wide_gap_candidate_count": voicing_metadata.get("spread_phrase_scope_wide_gap_candidate_count"),
        "spread_phrase_scope_wide_gap_original_notes": list(voicing_metadata.get("spread_phrase_scope_wide_gap_original_notes") or []),
        "spread_phrase_scope_wide_gap_realized_notes": list(voicing_metadata.get("spread_phrase_scope_wide_gap_realized_notes") or []),
        "spread_phrase_scope_wide_gap_original_upper_source_degrees": list(voicing_metadata.get("spread_phrase_scope_wide_gap_original_upper_source_degrees") or []),
        "spread_phrase_scope_wide_gap_realized_upper_source_degrees": list(voicing_metadata.get("spread_phrase_scope_wide_gap_realized_upper_source_degrees") or []),
        "spread_phrase_scope_wide_gap_best_replacement_upper_source_degrees": list(voicing_metadata.get("spread_phrase_scope_wide_gap_best_replacement_upper_source_degrees") or []),
        "spread_phrase_scope_wide_gap_original_primary_cost": voicing_metadata.get("spread_phrase_scope_wide_gap_original_primary_cost"),
        "spread_phrase_scope_wide_gap_realized_primary_cost": voicing_metadata.get("spread_phrase_scope_wide_gap_realized_primary_cost"),
        "spread_phrase_scope_wide_gap_best_replacement_primary_cost": voicing_metadata.get("spread_phrase_scope_wide_gap_best_replacement_primary_cost"),
        "spread_phrase_scope_wide_gap_max_primary_cost_delta": voicing_metadata.get("spread_phrase_scope_wide_gap_max_primary_cost_delta"),
        "spread_phrase_scope_wide_gap_state_advance_protected": bool(voicing_metadata.get("spread_phrase_scope_wide_gap_state_advance_protected", False)),
        "spread_phrase_scope_wide_gap_state_advance_override_enabled": bool(voicing_metadata.get("spread_phrase_scope_wide_gap_state_advance_override_enabled", False)),
        "spread_phrase_scope_wide_gap_state_advance_override_notes": list(voicing_metadata.get("spread_phrase_scope_wide_gap_state_advance_override_notes") or []),
        "spread_phrase_scope_wide_gap_not_broad_scorer": bool(voicing_metadata.get("spread_phrase_scope_wide_gap_not_broad_scorer", False)),
        "spread_phrase_scope_wide_gap_same_recipe_only": bool(voicing_metadata.get("spread_phrase_scope_wide_gap_same_recipe_only", False)),
        "spread_phrase_scope_wide_gap_density_lane_guarded": bool(voicing_metadata.get("spread_phrase_scope_wide_gap_density_lane_guarded", False)),
        "spread_phrase_scope_wide_gap_runtime_realization_enabled": bool(voicing_metadata.get("spread_phrase_scope_wide_gap_runtime_realization_enabled", False)),
        "spread_phrase_scope_wide_gap_reason": voicing_metadata.get("spread_phrase_scope_wide_gap_reason"),
        "voicing_state_advance_anchor_helper_version": voicing_metadata.get("voicing_state_advance_anchor_helper_version"),
        "voicing_state_advance_anchor_enabled": bool(voicing_metadata.get("voicing_state_advance_anchor_enabled", False)),
        "voicing_state_advance_anchor_policy_gate_version": voicing_metadata.get("voicing_state_advance_anchor_policy_gate_version"),
        "voicing_state_advance_anchor_policy_gate_required": bool(voicing_metadata.get("voicing_state_advance_anchor_policy_gate_required", False)),
        "voicing_state_advance_anchor_policy_gate_scope": voicing_metadata.get("voicing_state_advance_anchor_policy_gate_scope"),
        "voicing_state_advance_anchor_notes": list(voicing_metadata.get("voicing_state_advance_anchor_notes") or []),
        "voicing_state_advance_anchor_degrees": list(voicing_metadata.get("voicing_state_advance_anchor_degrees") or []),
        "voicing_state_advance_anchor_reason": voicing_metadata.get("voicing_state_advance_anchor_reason"),
        "spread_phrase_state_boundary_helper_cleanup_version": voicing_metadata.get("spread_phrase_state_boundary_helper_cleanup_version"),
        "spread_phrase_state_boundary_helper_cleanup_applied": bool(voicing_metadata.get("spread_phrase_state_boundary_helper_cleanup_applied", False)),
        "spread_phrase_state_boundary_helper_cleanup_contract": voicing_metadata.get("spread_phrase_state_boundary_helper_cleanup_contract"),
        "spread_phrase_state_boundary_helper_cleanup_state_anchor_owner": voicing_metadata.get("spread_phrase_state_boundary_helper_cleanup_state_anchor_owner"),
        "spread_phrase_state_boundary_helper_cleanup_resolver_consumes_anchor": bool(voicing_metadata.get("spread_phrase_state_boundary_helper_cleanup_resolver_consumes_anchor", False)),
        "spread_phrase_state_anchor_policy_boundary_version": voicing_metadata.get("spread_phrase_state_anchor_policy_boundary_version"),
        "spread_phrase_state_anchor_policy_boundary_applied": bool(voicing_metadata.get("spread_phrase_state_anchor_policy_boundary_applied", False)),
        "spread_phrase_state_anchor_policy_boundary_contract": voicing_metadata.get("spread_phrase_state_anchor_policy_boundary_contract"),
        "spread_phrase_state_anchor_policy_boundary_scope": voicing_metadata.get("spread_phrase_state_anchor_policy_boundary_scope"),
        "disposition_projection_spec": dict(voicing_metadata.get("disposition_projection_spec") or {}),
        "legacy_projection_callback_used": bool(voicing_metadata.get("legacy_projection_callback_used", False)),
        "legacy_projection_cleanup_required": bool(voicing_metadata.get("legacy_projection_cleanup_required", False)),
        "migrated_projection_path": voicing_metadata.get("migrated_projection_path"),
        "open_named_projection": bool(voicing_metadata.get("open_named_projection", False)),
        "open_named_projection_method": voicing_metadata.get("open_named_projection_method"),
        "open_named_projection_span": voicing_metadata.get("open_named_projection_span"),
        "open_named_projection_parent_closed_degrees": list(voicing_metadata.get("open_named_projection_parent_closed_degrees") or []),
        "open_named_projection_parent_closed_notes": list(voicing_metadata.get("open_named_projection_parent_closed_notes") or []),
        "open_named_projection_parent_closed_span": voicing_metadata.get("open_named_projection_parent_closed_span"),
        "open_drop2_projection": bool(voicing_metadata.get("open_drop2_projection", False)),
        "open_drop2_span": voicing_metadata.get("open_drop2_span"),
        "open_drop2_parent_closed_degrees": list(voicing_metadata.get("open_drop2_parent_closed_degrees") or []),
        "open_drop2_parent_closed_notes": list(voicing_metadata.get("open_drop2_parent_closed_notes") or []),
        "open_drop2_parent_closed_span": voicing_metadata.get("open_drop2_parent_closed_span"),
        "source_balance_selected_rank": selector.get("selected_rank"),
        "source_balance_selected_score": selector.get("selected_score"),
        "source_balance_candidate_count": selector.get("candidate_count"),
        "disposition": voicing.get("disposition"),
        "root_support": voicing.get("root_support"),
        "root_included": bool(voicing.get("root_included", False)),
        "degrees": list(voicing.get("degrees") or []),
        "midi_notes": list(voicing.get("midi_notes") or []),
        "voice_roles": list(voicing.get("voice_roles") or []),
        "groups": dict(voicing.get("groups") or {}),
        "projection_map": dict(voicing.get("projection_map") or {}),
        "register_guard_passed": bool(register_guard.get("passed", True)),
        "register_guard_reasons": list(register_guard.get("reasons") or []),
        "selector_mode": selector.get("mode", "unknown"),
        "selector_rank": selector.get("selected_rank"),
        "selector_score": selector.get("selected_score"),
        "realized_note_count": len(realized),
        "realized_notes": realized,
        "performed_starts": performed,
    }


def _drop_projection_method_name(value: Any) -> str | None:
    text = str(getattr(value, "value", value) or "").strip().lower().replace("-", "_")
    aliases = {
        "drop2": "drop2",
        "drop_2": "drop2",
        "drop3": "drop3",
        "drop_3": "drop3",
        "drop2_and_4": "drop2_and_4",
        "drop_2_and_4": "drop2_and_4",
        "drop24": "drop2_and_4",
        "drop_2_4": "drop2_and_4",
        "drop2&4": "drop2_and_4",
        "drop_2&4": "drop2_and_4",
    }
    return aliases.get(text)


def _drop_projection_method_from_metadata(metadata: Mapping[str, Any]) -> str | None:
    for key in (
        "open_named_projection_method",
        "active_open_projection_method",
        "disposition_projection_method",
    ):
        method = _drop_projection_method_name(metadata.get(key))
        if method:
            return method
    for method, marker in (
        ("drop2_and_4", "open_drop2_and_4_projection"),
        ("drop3", "open_drop3_projection"),
        ("drop2", "open_drop2_projection"),
    ):
        if bool(metadata.get(marker)):
            return method
    return None


def _major_seventh_color_detail(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return maj7 safe-extension audit details for an already-realized event.

    This is observational only: it does not re-plan chord material.  The
    Ballad default is intentionally warm, so ordinary major-seventh expansion
    should expose 9/13 and avoid unnotated #11 unless the chart or a later
    policy explicitly asks for Lydian/bright color.
    """

    chord = str(row.get("chord_symbol") or "")
    chord_lower = chord.lower()
    is_major_seventh = "maj7" in chord_lower or "ma7" in chord_lower or "△7" in chord
    degrees = [str(degree) for degree in row.get("degrees") or []]
    colors = [degree for degree in degrees if degree in {"9", "11", "#11", "13", "b9", "#9", "b13"}]
    explicit_sharp11 = "#11" in chord or "♯11" in chord
    return {
        "is_major_seventh": is_major_seventh,
        "colors": colors,
        "safe_only": bool(colors) and set(colors).issubset({"9", "13"}),
        "unnotated_sharp11": bool(is_major_seventh and "#11" in degrees and not explicit_sharp11),
        "explicit_sharp11": bool(is_major_seventh and "#11" in degrees and explicit_sharp11),
    }


def _counter_percentages_by_key(counters: Mapping[str, Counter[str]]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for key, counter in counters.items():
        total = sum(counter.values()) or 1
        out[str(key)] = {str(name): round(float(count) / float(total), 4) for name, count in counter.items()}
    return out


def _numeric_stats_by_key(values_by_key: Mapping[str, list[int]]) -> dict[str, dict[str, float | int | None]]:
    out: dict[str, dict[str, float | int | None]] = {}
    for key, values in values_by_key.items():
        numbers = [int(value) for value in values]
        out[str(key)] = {
            "count": len(numbers),
            "min": min(numbers) if numbers else None,
            "max": max(numbers) if numbers else None,
            "average": round(mean(numbers), 3) if numbers else 0.0,
        }
    return out


def _texture_scope_id_from_metadata(voicing_metadata: Mapping[str, Any]) -> str | None:
    state = dict(voicing_metadata.get("voicing_texture_state") or {})
    return (
        voicing_metadata.get("voicing_texture_runtime_scope_id")
        or voicing_metadata.get("texture_scope_id")
        or state.get("scope_id")
    )


def _texture_contrast_role_from_metadata(voicing_metadata: Mapping[str, Any]) -> str | None:
    state = dict(voicing_metadata.get("voicing_texture_state") or {})
    plan = dict(voicing_metadata.get("voicing_texture_contrast_plan") or {})
    return (
        voicing_metadata.get("voicing_texture_contrast_role")
        or state.get("contrast_role")
        or plan.get("contrast_role")
    )


def _texture_open_method_weights_from_metadata(voicing_metadata: Mapping[str, Any]) -> dict[str, float]:
    state = dict(voicing_metadata.get("voicing_texture_state") or {})
    shaping = dict(voicing_metadata.get("voicing_texture_method_weight_shaping") or {})
    weights = state.get("open_method_weights") or shaping.get("open_method_weights") or {}
    if not isinstance(weights, Mapping):
        return {}
    return {str(key): float(value) for key, value in weights.items()}


def _score_detail(voicing_metadata: Mapping[str, Any], key: str) -> Any:
    score_breakdown = dict(voicing_metadata.get("score_breakdown") or {})
    details = dict(score_breakdown.get("details") or {})
    return details.get(key)


def _validity_note_suffix(voicing_metadata: Mapping[str, Any], prefix: str) -> str | None:
    recipe = dict(voicing_metadata.get("content_recipe") or {})
    for note in recipe.get("validity_notes", ()) or ():
        value = str(note)
        if value.startswith(prefix):
            return value.removeprefix(prefix)
    return None


def _voicing_cell(row: Mapping[str, Any]) -> str:
    bits = [
        str(row.get("content_family") or "unknown"),
        f"d{row.get('density') or '?'}",
        str(row.get("functional_grouping") or "?"),
        str(row.get("disposition") or "?"),
    ]
    rootless_type = row.get("rootless_ab_content_type")
    rootless_orientation = row.get("rootless_ab_orientation_family")
    rootless_inversion = row.get("rootless_ab_inversion_index")
    rootless_order = row.get("rootless_ab_degree_order")
    if rootless_type or rootless_orientation:
        bits.append(f"ab:{rootless_orientation or '?'}{rootless_inversion if rootless_inversion is not None else '?'}:{rootless_type or '?'}")
    if rootless_order:
        bits.append(f"order:{rootless_order}")
    projection_method = row.get("disposition_projection_method")
    if projection_method:
        bits.append(f"projection:{projection_method}")
    if row.get("open_named_projection"):
        bits.append(f"named_open:{row.get('open_named_projection_method')}:{row.get('open_named_projection_span')}")
    elif row.get("open_drop2_projection"):
        bits.append(f"drop2_span:{row.get('open_drop2_span')}")
    recipe = row.get("recipe_id")
    if recipe:
        bits.append(str(recipe))
    return "/".join(bits)


def _vl_source_cell(row: Mapping[str, Any]) -> str:
    if row.get("closed_3note_per_source_minimum_motion"):
        prefix = "closed_3note"
    elif row.get("closed_4note_per_source_minimum_motion"):
        prefix = "closed_4note"
    else:
        return ""
    parts = [f"n={row.get(prefix + '_source_collapse_candidate_count')}"]
    distance = row.get(prefix + "_source_collapse_selected_distance")
    total = row.get(prefix + "_source_collapse_selected_total_motion")
    top_motion = row.get(prefix + "_source_collapse_selected_top_motion")
    if distance is not None:
        parts.append(f"avg={float(distance):.2f}")
    if total is not None:
        parts.append(f"total={float(total):.1f}")
    if top_motion is not None:
        parts.append(f"top={int(top_motion):+d}")
    return ",".join(parts)


def _performed_cell(row: Mapping[str, Any]) -> str:
    starts = list(row.get("performed_starts") or [])
    if not starts:
        return ""
    return " ".join(f"{float(start):.3f}" for start in starts[:6])
