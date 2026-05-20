from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.generation.piano_audit import build_piano_musical_audit, format_piano_musical_audit_report
from jammate_engine.runtime.generate import generate_accompaniment

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"

VOICING_MILESTONE_ID = "v2_6_55"
VOICING_MILESTONE_LABEL = "v2_6_55 — Medium Swing OPEN/DROP Deliberate Revoice Micro-Motion Policy Probe"

SPECS: tuple[dict[str, Any], ...] = (
    {"slug": "all_the_things_you_are", "leadsheet": "all_the_things_you_are.json", "seed": 3300},
    {"slug": "autumn_leaves", "leadsheet": "autumn_leaves.json", "seed": 3301},
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    outputs = [_generate_and_audit(spec) for spec in SPECS]
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": VOICING_MILESTONE_LABEL,
        "scope": "Audit actual Medium Swing OPEN drop-family method selections after the conservative v2_6_49 runtime method-lock policy and the v2_6_51 generic 4-note rotation-alignment wiring plus the v2_6_52 same-chord reattack/comping-reuse checkpoint; verify local ii-V/V-I/ii-V-I follow regions keep DROP2/DROP3 method continuity, preserve DROP2&4 as phrase-internal color, ensure repeated hits inside one chord region reuse the cached region voicing, and confirm top register plus major-seventh safe-extension guardrails remain calm after generic 4-note rotation alignment, and verify deliberate same-chord revoicing remains explicit-intent only and that the new micro-motion policy is probe-only unless explicitly triggered.",
        "outputs": outputs,
        "acceptance": _acceptance(outputs),
    }
    summary_path = DEMOS_DIR / f"{VOICING_MILESTONE_ID}_medium_swing_deliberate_revoice_micro_motion_policy_audit_summary.json"
    report_path = DEMOS_DIR / f"{VOICING_MILESTONE_ID}_medium_swing_deliberate_revoice_micro_motion_policy_audit_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_format_report(summary), encoding="utf-8")
    print({"ok": summary["acceptance"]["passed"], "summary_path": str(summary_path), "report_path": str(report_path), "outputs": outputs})
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def _generate_and_audit(spec: Mapping[str, Any]) -> dict[str, Any]:
    score_path = LEADSHEET_DIR / str(spec["leadsheet"])
    score = json.loads(score_path.read_text(encoding="utf-8"))
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{VOICING_MILESTONE_ID}_{slug}_medium_swing_deliberate_revoice_micro_motion_policy_demo.mid"
    audit_path = DEMOS_DIR / f"{VOICING_MILESTONE_ID}_{slug}_medium_swing_deliberate_revoice_micro_motion_policy_piano_audit.md"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": int(score.get("tempo", 132)),
            "choruses": 3,
            "seed": int(spec["seed"]),
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
        }
    )
    audit = build_piano_musical_audit(result.debug)
    audit_path.write_text(format_piano_musical_audit_report(result.debug, max_events=80), encoding="utf-8")
    return {
        "ok": bool(result.ok),
        "title": score.get("title"),
        "slug": slug,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "audit_path": str(audit_path.relative_to(PROJECT_ROOT)),
        "events": audit.summary.get("events"),
        "methods": audit.summary.get("disposition_projection_methods"),
        "families": audit.summary.get("disposition_projection_families"),
        "contrast_roles": audit.summary.get("voicing_texture_contrast_roles"),
        "methods_by_contrast_role": audit.summary.get("voicing_texture_methods_by_contrast_role"),
        "method_percentages_by_contrast_role": audit.summary.get("voicing_texture_method_percentages_by_contrast_role"),
        "open_method_weight_plans_by_contrast_role": audit.summary.get("voicing_texture_open_method_weight_plans_by_contrast_role"),
        "failed_register_guard_count": audit.summary.get("failed_register_guard_count"),
        "missing_note_events": audit.summary.get("missing_note_events"),
        "voice_leading_transition_events": audit.summary.get("medium_swing_open_drop_voice_leading_continuity_transition_events"),
        "voice_leading_method_switch_events": audit.summary.get("medium_swing_open_drop_voice_leading_continuity_method_switch_events"),
        "voice_leading_section_boundary_events": audit.summary.get("medium_swing_open_drop_voice_leading_continuity_section_boundary_events"),
        "voice_leading_warning_events": audit.summary.get("medium_swing_open_drop_voice_leading_continuity_warning_events"),
        "voice_leading_method_switch_warning_events": audit.summary.get("medium_swing_open_drop_voice_leading_continuity_method_switch_warning_events"),
        "voice_leading_section_boundary_warning_events": audit.summary.get("medium_swing_open_drop_voice_leading_continuity_section_boundary_warning_events"),
        "voice_leading_top_motion_max_abs": audit.summary.get("medium_swing_open_drop_voice_leading_continuity_top_motion_max_abs"),
        "voice_leading_low_motion_max_abs": audit.summary.get("medium_swing_open_drop_voice_leading_continuity_low_motion_max_abs"),
        "voice_leading_avg_motion_max": audit.summary.get("medium_swing_open_drop_voice_leading_continuity_avg_motion_max"),
        "voice_leading_avg_motion_average": audit.summary.get("medium_swing_open_drop_voice_leading_continuity_avg_motion_average"),
        "voice_leading_span_jump_max_abs": audit.summary.get("medium_swing_open_drop_voice_leading_continuity_span_jump_max_abs"),
        "voice_leading_checkpoint_passed": audit.summary.get("medium_swing_open_drop_voice_leading_continuity_checkpoint_passed"),
        "section_boundary_review_events": audit.summary.get("medium_swing_open_drop_section_boundary_review_events"),
        "section_boundary_review_method_switch_events": audit.summary.get("medium_swing_open_drop_section_boundary_review_method_switch_events"),
        "section_boundary_review_drop2_and_4_entry_events": audit.summary.get("medium_swing_open_drop_section_boundary_review_drop2_and_4_entry_events"),
        "section_boundary_review_warning_events": audit.summary.get("medium_swing_open_drop_section_boundary_review_warning_events"),
        "section_boundary_review_primary_entry_alignment_events": audit.summary.get("medium_swing_open_drop_section_boundary_review_primary_entry_alignment_events"),
        "section_boundary_review_entry_methods_by_role": audit.summary.get("medium_swing_open_drop_section_boundary_review_entry_methods_by_role"),
        "section_boundary_review_role_pairs": audit.summary.get("medium_swing_open_drop_section_boundary_review_role_pairs"),
        "section_boundary_review_method_pairs": audit.summary.get("medium_swing_open_drop_section_boundary_review_method_pairs"),
        "section_boundary_review_avg_motion_max": audit.summary.get("medium_swing_open_drop_section_boundary_review_avg_motion_max"),
        "section_boundary_review_top_motion_max_abs": audit.summary.get("medium_swing_open_drop_section_boundary_review_top_motion_max_abs"),
        "section_boundary_review_low_motion_max_abs": audit.summary.get("medium_swing_open_drop_section_boundary_review_low_motion_max_abs"),
        "section_boundary_review_checkpoint_passed": audit.summary.get("medium_swing_open_drop_section_boundary_review_checkpoint_passed"),
        "phrase_scope_events": audit.summary.get("medium_swing_phrase_scope_events"),
        "phrase_scope_count": audit.summary.get("medium_swing_phrase_scope_count"),
        "phrase_scope_method_switch_events": audit.summary.get("medium_swing_phrase_scope_method_switch_events"),
        "phrase_scope_method_switch_ratio": audit.summary.get("medium_swing_phrase_scope_method_switch_ratio"),
        "phrase_scope_drop2_and_4_run_events": audit.summary.get("medium_swing_phrase_scope_drop2_and_4_run_events"),
        "phrase_scope_drop2_and_4_run_max": audit.summary.get("medium_swing_phrase_scope_drop2_and_4_run_max"),
        "phrase_scope_ii_v_events": audit.summary.get("medium_swing_phrase_scope_ii_v_events"),
        "phrase_scope_v_i_events": audit.summary.get("medium_swing_phrase_scope_v_i_events"),
        "phrase_scope_ii_v_i_events": audit.summary.get("medium_swing_phrase_scope_ii_v_i_events"),
        "phrase_scope_ii_v_i_method_consistent_events": audit.summary.get("medium_swing_phrase_scope_ii_v_i_method_consistent_events"),
        "phrase_scope_ii_v_i_method_switch_events": audit.summary.get("medium_swing_phrase_scope_ii_v_i_method_switch_events"),
        "phrase_scope_progression_method_consistent_events": audit.summary.get("medium_swing_phrase_scope_progression_method_consistent_events"),
        "phrase_scope_progression_method_switch_events": audit.summary.get("medium_swing_phrase_scope_progression_method_switch_events"),
        "phrase_scope_high_motion_switch_events": audit.summary.get("medium_swing_phrase_scope_high_motion_switch_events"),
        "phrase_scope_warning_events": audit.summary.get("medium_swing_phrase_scope_warning_events"),
        "phrase_scope_checkpoint_passed": audit.summary.get("medium_swing_phrase_scope_checkpoint_passed"),
        "phrase_scope_method_lock_runtime_enabled_events": audit.summary.get("medium_swing_phrase_scope_method_lock_policy_runtime_enabled_events"),
        "phrase_scope_method_lock_applied_events": audit.summary.get("medium_swing_phrase_scope_method_lock_policy_applied_events"),
        "phrase_scope_method_lock_candidate_match_events": audit.summary.get("medium_swing_phrase_scope_method_lock_policy_candidate_match_events"),
        "phrase_scope_method_lock_candidate_mismatch_events": audit.summary.get("medium_swing_phrase_scope_method_lock_policy_candidate_mismatch_events"),
        "phrase_scope_method_lock_runtime_filtering_events": audit.summary.get("medium_swing_phrase_scope_method_lock_policy_runtime_filtering_events"),
        "phrase_scope_method_lock_pair_types": audit.summary.get("medium_swing_phrase_scope_method_lock_policy_pair_types"),
        "phrase_scope_method_lock_locked_methods": audit.summary.get("medium_swing_phrase_scope_method_lock_policy_locked_methods"),
        "phrase_scope_method_lock_skip_reasons": audit.summary.get("medium_swing_phrase_scope_method_lock_policy_skip_reasons"),
        "phrase_scope_method_lock_checkpoint_passed": audit.summary.get("medium_swing_phrase_scope_method_lock_policy_checkpoint_passed"),
        "four_note_rotation_alignment_runtime_enabled_events": audit.summary.get("medium_swing_four_note_rotation_alignment_runtime_enabled_events"),
        "four_note_rotation_alignment_policy_applied_events": audit.summary.get("medium_swing_four_note_rotation_alignment_policy_applied_events"),
        "four_note_rotation_alignment_filter_applied_events": audit.summary.get("medium_swing_four_note_rotation_alignment_filter_applied_events"),
        "four_note_rotation_alignment_candidate_match_events": audit.summary.get("medium_swing_four_note_rotation_alignment_candidate_match_events"),
        "four_note_rotation_alignment_candidate_mismatch_events": audit.summary.get("medium_swing_four_note_rotation_alignment_candidate_mismatch_events"),
        "four_note_rotation_alignment_pair_types": audit.summary.get("medium_swing_four_note_rotation_alignment_pair_types"),
        "four_note_rotation_alignment_desired_families": audit.summary.get("medium_swing_four_note_rotation_alignment_desired_families"),
        "four_note_rotation_alignment_selected_families": audit.summary.get("medium_swing_four_note_rotation_alignment_selected_families"),
        "four_note_rotation_alignment_desired_sides": audit.summary.get("medium_swing_four_note_rotation_alignment_desired_sides"),
        "four_note_rotation_alignment_selected_sides": audit.summary.get("medium_swing_four_note_rotation_alignment_selected_sides"),
        "four_note_rotation_alignment_skip_reasons": audit.summary.get("medium_swing_four_note_rotation_alignment_skip_reasons"),
        "four_note_rotation_alignment_filter_reasons": audit.summary.get("medium_swing_four_note_rotation_alignment_filter_reasons"),
        "four_note_rotation_alignment_checkpoint_passed": audit.summary.get("medium_swing_four_note_rotation_alignment_checkpoint_passed"),
        "rootless_ab_orientation_alignment_runtime_enabled_events": audit.summary.get("medium_swing_rootless_ab_orientation_alignment_runtime_enabled_events"),
        "rootless_ab_orientation_alignment_policy_applied_events": audit.summary.get("medium_swing_rootless_ab_orientation_alignment_policy_applied_events"),
        "rootless_ab_orientation_alignment_filter_applied_events": audit.summary.get("medium_swing_rootless_ab_orientation_alignment_filter_applied_events"),
        "rootless_ab_orientation_alignment_candidate_match_events": audit.summary.get("medium_swing_rootless_ab_orientation_alignment_candidate_match_events"),
        "rootless_ab_orientation_alignment_candidate_mismatch_events": audit.summary.get("medium_swing_rootless_ab_orientation_alignment_candidate_mismatch_events"),
        "rootless_ab_orientation_alignment_pair_types": audit.summary.get("medium_swing_rootless_ab_orientation_alignment_pair_types"),
        "rootless_ab_orientation_alignment_desired_orientations": audit.summary.get("medium_swing_rootless_ab_orientation_alignment_desired_orientations"),
        "rootless_ab_orientation_alignment_selected_orientations": audit.summary.get("medium_swing_rootless_ab_orientation_alignment_selected_orientations"),
        "rootless_ab_orientation_alignment_skip_reasons": audit.summary.get("medium_swing_rootless_ab_orientation_alignment_skip_reasons"),
        "rootless_ab_orientation_alignment_filter_reasons": audit.summary.get("medium_swing_rootless_ab_orientation_alignment_filter_reasons"),
        "rootless_ab_orientation_alignment_checkpoint_passed": audit.summary.get("medium_swing_rootless_ab_orientation_alignment_checkpoint_passed"),
        "same_chord_reattack_comping_reuse_version": audit.summary.get("medium_swing_same_chord_reattack_comping_reuse_version"),
        "same_chord_reattack_comping_reuse_events": audit.summary.get("medium_swing_same_chord_reattack_comping_reuse_events"),
        "same_chord_reattack_comping_reuse_region_voicing_reused_events": audit.summary.get("medium_swing_same_chord_reattack_comping_reuse_region_voicing_reused_events"),
        "same_chord_reattack_comping_reuse_exact_voicing_reuse_events": audit.summary.get("medium_swing_same_chord_reattack_comping_reuse_exact_voicing_reuse_events"),
        "same_chord_reattack_comping_reuse_foundation_stable_events": audit.summary.get("medium_swing_same_chord_reattack_comping_reuse_foundation_stable_events"),
        "same_chord_reattack_comping_reuse_fresh_revoicing_events": audit.summary.get("medium_swing_same_chord_reattack_comping_reuse_fresh_revoicing_events"),
        "same_chord_reattack_comping_reuse_warning_events": audit.summary.get("medium_swing_same_chord_reattack_comping_reuse_warning_events"),
        "same_chord_reattack_comping_reuse_checkpoint_passed": audit.summary.get("medium_swing_same_chord_reattack_comping_reuse_checkpoint_passed"),
        "safe_extension_top_register_checkpoint_version": audit.summary.get("medium_swing_open_drop_safe_extension_top_register_checkpoint_version"),
        "safe_extension_top_register_checkpoint_passed": audit.summary.get("medium_swing_open_drop_safe_extension_top_register_checkpoint_passed"),
        "deliberate_revoice_gesture_boundary_version": audit.summary.get("medium_swing_deliberate_revoice_gesture_boundary_version"),
        "deliberate_revoice_gesture_boundary_default_reuse_events": audit.summary.get("medium_swing_deliberate_revoice_gesture_boundary_default_reuse_events"),
        "deliberate_revoice_gesture_boundary_explicit_revoice_events": audit.summary.get("medium_swing_deliberate_revoice_gesture_boundary_explicit_revoice_events"),
        "deliberate_revoice_gesture_boundary_implicit_revoice_events": audit.summary.get("medium_swing_deliberate_revoice_gesture_boundary_implicit_revoice_events"),
        "deliberate_revoice_gesture_boundary_warning_events": audit.summary.get("medium_swing_deliberate_revoice_gesture_boundary_warning_events"),
        "deliberate_revoice_gesture_boundary_escape_hatches": audit.summary.get("medium_swing_deliberate_revoice_gesture_boundary_escape_hatches"),
        "deliberate_revoice_gesture_boundary_checkpoint_passed": audit.summary.get("medium_swing_deliberate_revoice_gesture_boundary_checkpoint_passed"),
        "deliberate_revoice_micro_motion_policy_version": audit.summary.get("medium_swing_deliberate_revoice_micro_motion_policy_version"),
        "deliberate_revoice_micro_motion_policy_runtime_enabled_events": audit.summary.get("medium_swing_deliberate_revoice_micro_motion_policy_runtime_enabled_events"),
        "deliberate_revoice_micro_motion_policy_explicit_revoice_events": audit.summary.get("medium_swing_deliberate_revoice_micro_motion_policy_explicit_revoice_events"),
        "deliberate_revoice_micro_motion_policy_filter_applied_events": audit.summary.get("medium_swing_deliberate_revoice_micro_motion_policy_filter_applied_events"),
        "deliberate_revoice_micro_motion_policy_candidate_match_events": audit.summary.get("medium_swing_deliberate_revoice_micro_motion_policy_candidate_match_events"),
        "deliberate_revoice_micro_motion_policy_fallback_events": audit.summary.get("medium_swing_deliberate_revoice_micro_motion_policy_fallback_events"),
        "deliberate_revoice_micro_motion_policy_warning_events": audit.summary.get("medium_swing_deliberate_revoice_micro_motion_policy_warning_events"),
        "deliberate_revoice_micro_motion_policy_filter_reasons": audit.summary.get("medium_swing_deliberate_revoice_micro_motion_policy_filter_reasons"),
        "deliberate_revoice_micro_motion_policy_motion_maxima": audit.summary.get("medium_swing_deliberate_revoice_micro_motion_policy_motion_maxima"),
        "deliberate_revoice_micro_motion_policy_checkpoint_passed": audit.summary.get("medium_swing_deliberate_revoice_micro_motion_policy_checkpoint_passed"),
        "medium_swing_open_drop_top_note_max": audit.summary.get("medium_swing_open_drop_top_note_max"),
        "medium_swing_open_drop_low_note_min": audit.summary.get("medium_swing_open_drop_low_note_min"),
        "medium_swing_open_drop_top_note_ge_75_events": audit.summary.get("medium_swing_open_drop_top_note_ge_75_events"),
        "medium_swing_open_drop_register_guard_failed_events": audit.summary.get("medium_swing_open_drop_register_guard_failed_events"),
        "medium_swing_open_drop_missing_note_events": audit.summary.get("medium_swing_open_drop_missing_note_events"),
        "medium_swing_open_drop_voice_leading_warning_events": audit.summary.get("medium_swing_open_drop_voice_leading_warning_events"),
        "medium_swing_open_drop_major_seventh_events": audit.summary.get("medium_swing_open_drop_major_seventh_events"),
        "medium_swing_open_drop_major_seventh_color_events": audit.summary.get("medium_swing_open_drop_major_seventh_color_events"),
        "medium_swing_open_drop_major_seventh_warm_color_events": audit.summary.get("medium_swing_open_drop_major_seventh_warm_color_events"),
        "medium_swing_open_drop_major_seventh_degree_counts": audit.summary.get("medium_swing_open_drop_major_seventh_degree_counts"),
        "medium_swing_open_drop_major_seventh_non_safe_color_events_by_chord": audit.summary.get("medium_swing_open_drop_major_seventh_non_safe_color_events_by_chord"),
        "medium_swing_open_drop_major_seventh_unnotated_sharp11_events": audit.summary.get("medium_swing_open_drop_major_seventh_unnotated_sharp11_events"),
        "medium_swing_open_drop_major_seventh_explicit_sharp11_events": audit.summary.get("medium_swing_open_drop_major_seventh_explicit_sharp11_events"),
    }


def _acceptance(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for item in outputs:
        slug = str(item.get("slug"))
        methods = dict(item.get("methods") or {})
        families = dict(item.get("families") or {})
        roles = dict(item.get("contrast_roles") or {})
        percentages = dict(item.get("method_percentages_by_contrast_role") or {})
        baseline = dict(percentages.get("baseline_open_swing") or {})
        bridge = dict(percentages.get("bridge_open_contrast") or {})
        final = dict(percentages.get("final_chorus_open_lift") or {})
        checks.extend(
            [
                _check(f"{slug}: generated", bool(item.get("ok")), {"ok": item.get("ok")}),
                _check(f"{slug}: enough three-chorus piano events", int(item.get("events") or 0) >= 100, {"events": item.get("events")}),
                _check(f"{slug}: open family only", set(families.keys()) == {"open"}, {"families": families}),
                _check(
                    f"{slug}: all texture contrast roles present",
                    all(roles.get(role, 0) > 0 for role in ("baseline_open_swing", "bridge_open_contrast", "final_chorus_open_lift")),
                    {"roles": roles},
                ),
                _check(f"{slug}: multiple open methods realized", len(methods) >= 3, {"methods": methods}),
                _check(
                    f"{slug}: bridge increases drop3 share over baseline",
                    _ratio(bridge, "drop3") > _ratio(baseline, "drop3"),
                    {"baseline_drop3": _ratio(baseline, "drop3"), "bridge_drop3": _ratio(bridge, "drop3")},
                ),
                _check(
                    f"{slug}: final chorus increases drop3 share over baseline after generic-open removal",
                    _ratio(final, "drop3") > _ratio(baseline, "drop3"),
                    {"baseline_drop3": _ratio(baseline, "drop3"), "final_drop3": _ratio(final, "drop3")},
                ),
                _check(
                    f"{slug}: drop2_and_4 remains controlled",
                    _ratio_sum(_total_percentages(methods), ("drop2_and_4",)) <= 0.20,
                    {"methods": methods, "drop2_and_4_total_ratio": _ratio_sum(_total_percentages(methods), ("drop2_and_4",))},
                ),
                _check(f"{slug}: no failed register guards", int(item.get("failed_register_guard_count") or 0) == 0, {"failed": item.get("failed_register_guard_count")}),
                _check(f"{slug}: no missing piano note events", int(item.get("missing_note_events") or 0) == 0, {"missing": item.get("missing_note_events")}),
                _check(
                    f"{slug}: open/drop cross-region voice-leading checkpoint passes",
                    ("voice_leading_checkpoint_passed" not in item) or bool(item.get("voice_leading_checkpoint_passed")),
                    {
                        "transitions": item.get("voice_leading_transition_events"),
                        "warnings": item.get("voice_leading_warning_events"),
                        "top_motion_max_abs": item.get("voice_leading_top_motion_max_abs"),
                        "avg_motion_max": item.get("voice_leading_avg_motion_max"),
                        "legacy_output_without_v2_6_46_fields": "voice_leading_checkpoint_passed" not in item,
                    },
                ),
                _check(
                    f"{slug}: method switches remain smooth",
                    ("voice_leading_method_switch_warning_events" not in item) or int(item.get("voice_leading_method_switch_warning_events") or 0) == 0,
                    {
                        "method_switch_events": item.get("voice_leading_method_switch_events"),
                        "method_switch_warnings": item.get("voice_leading_method_switch_warning_events"),
                    },
                ),
                _check(
                    f"{slug}: section boundaries remain smooth",
                    ("voice_leading_section_boundary_warning_events" not in item) or int(item.get("voice_leading_section_boundary_warning_events") or 0) == 0,
                    {
                        "section_boundary_events": item.get("voice_leading_section_boundary_events"),
                        "section_boundary_warnings": item.get("voice_leading_section_boundary_warning_events"),
                    },
                ),
                _check(
                    f"{slug}: section-boundary method-lock readability passes",
                    ("section_boundary_review_checkpoint_passed" not in item) or bool(item.get("section_boundary_review_checkpoint_passed")),
                    {
                        "boundary_events": item.get("section_boundary_review_events"),
                        "warnings": item.get("section_boundary_review_warning_events"),
                        "drop2_and_4_entry_events": item.get("section_boundary_review_drop2_and_4_entry_events"),
                        "entry_methods_by_role": item.get("section_boundary_review_entry_methods_by_role"),
                        "legacy_output_without_v2_6_47_fields": "section_boundary_review_checkpoint_passed" not in item,
                    },
                ),
                _check(
                    f"{slug}: phrase-scope method continuity checkpoint passes",
                    ("phrase_scope_checkpoint_passed" not in item) or bool(item.get("phrase_scope_checkpoint_passed")),
                    {
                        "phrase_scope_events": item.get("phrase_scope_events"),
                        "method_switch_ratio": item.get("phrase_scope_method_switch_ratio"),
                        "drop2_and_4_run_max": item.get("phrase_scope_drop2_and_4_run_max"),
                        "high_motion_switch_events": item.get("phrase_scope_high_motion_switch_events"),
                        "warnings": item.get("phrase_scope_warning_events"),
                        "legacy_output_without_v2_6_48_fields": "phrase_scope_checkpoint_passed" not in item,
                    },
                ),
                _check(
                    f"{slug}: DROP2&4 stays phrase-internal color",
                    ("phrase_scope_drop2_and_4_run_max" not in item) or int(item.get("phrase_scope_drop2_and_4_run_max") or 0) <= 2,
                    {
                        "drop2_and_4_run_events": item.get("phrase_scope_drop2_and_4_run_events"),
                        "drop2_and_4_run_max": item.get("phrase_scope_drop2_and_4_run_max"),
                    },
                ),
                _check(
                    f"{slug}: phrase-scope method lock policy applies to local progressions",
                    int(item.get("phrase_scope_method_lock_applied_events") or 0) > 0,
                    {
                        "applied_events": item.get("phrase_scope_method_lock_applied_events"),
                        "pair_types": item.get("phrase_scope_method_lock_pair_types"),
                    },
                ),
                _check(
                    f"{slug}: all locked follow candidates match their method lock",
                    bool(item.get("phrase_scope_method_lock_checkpoint_passed")),
                    {
                        "candidate_match_events": item.get("phrase_scope_method_lock_candidate_match_events"),
                        "candidate_mismatch_events": item.get("phrase_scope_method_lock_candidate_mismatch_events"),
                        "runtime_filtering_events": item.get("phrase_scope_method_lock_runtime_filtering_events"),
                    },
                ),
                _check(
                    f"{slug}: generic 4-note rotation alignment checkpoint passes",
                    bool(item.get("four_note_rotation_alignment_checkpoint_passed")),
                    {
                        "policy_applied_events": item.get("four_note_rotation_alignment_policy_applied_events"),
                        "filter_applied_events": item.get("four_note_rotation_alignment_filter_applied_events"),
                        "candidate_match_events": item.get("four_note_rotation_alignment_candidate_match_events"),
                        "candidate_mismatch_events": item.get("four_note_rotation_alignment_candidate_mismatch_events"),
                        "desired_families": item.get("four_note_rotation_alignment_desired_families"),
                        "selected_families": item.get("four_note_rotation_alignment_selected_families"),
                    },
                ),
                _check(
                    f"{slug}: rootless A/B orientation alignment checkpoint passes",
                    bool(item.get("rootless_ab_orientation_alignment_checkpoint_passed")),
                    {
                        "policy_applied_events": item.get("rootless_ab_orientation_alignment_policy_applied_events"),
                        "filter_applied_events": item.get("rootless_ab_orientation_alignment_filter_applied_events"),
                        "candidate_match_events": item.get("rootless_ab_orientation_alignment_candidate_match_events"),
                        "candidate_mismatch_events": item.get("rootless_ab_orientation_alignment_candidate_mismatch_events"),
                        "skip_reasons": item.get("rootless_ab_orientation_alignment_skip_reasons"),
                    },
                ),
                _check(
                    f"{slug}: same-chord comping reattacks reuse cached region voicing",
                    bool(item.get("same_chord_reattack_comping_reuse_checkpoint_passed")),
                    {
                        "reattack_events": item.get("same_chord_reattack_comping_reuse_events"),
                        "region_voicing_reused_events": item.get("same_chord_reattack_comping_reuse_region_voicing_reused_events"),
                        "exact_voicing_reuse_events": item.get("same_chord_reattack_comping_reuse_exact_voicing_reuse_events"),
                        "foundation_stable_events": item.get("same_chord_reattack_comping_reuse_foundation_stable_events"),
                        "fresh_revoicing_events": item.get("same_chord_reattack_comping_reuse_fresh_revoicing_events"),
                        "warnings": item.get("same_chord_reattack_comping_reuse_warning_events"),
                    },
                ),
                _check(
                    f"{slug}: safe-extension and top-register checkpoint passes",
                    bool(item.get("safe_extension_top_register_checkpoint_passed")),
                    {
                        "version": item.get("safe_extension_top_register_checkpoint_version"),
                        "top_note_max": item.get("medium_swing_open_drop_top_note_max"),
                        "top_note_ge_75_events": item.get("medium_swing_open_drop_top_note_ge_75_events"),
                        "unnotated_sharp11_events": item.get("medium_swing_open_drop_major_seventh_unnotated_sharp11_events"),
                        "major_seventh_degree_counts": item.get("medium_swing_open_drop_major_seventh_degree_counts"),
                        "register_guard_failed_events": item.get("medium_swing_open_drop_register_guard_failed_events"),
                        "voice_leading_warning_events": item.get("medium_swing_open_drop_voice_leading_warning_events"),
                    },
                ),
                _check(
                    f"{slug}: deliberate same-chord revoice remains explicit-intent only",
                    bool(item.get("deliberate_revoice_gesture_boundary_checkpoint_passed"))
                    and int(item.get("deliberate_revoice_gesture_boundary_implicit_revoice_events") or 0) == 0
                    and int(item.get("deliberate_revoice_gesture_boundary_warning_events") or 0) == 0,
                    {
                        "version": item.get("deliberate_revoice_gesture_boundary_version"),
                        "default_reuse_events": item.get("deliberate_revoice_gesture_boundary_default_reuse_events"),
                        "explicit_revoice_events": item.get("deliberate_revoice_gesture_boundary_explicit_revoice_events"),
                        "implicit_revoice_events": item.get("deliberate_revoice_gesture_boundary_implicit_revoice_events"),
                        "warnings": item.get("deliberate_revoice_gesture_boundary_warning_events"),
                        "escape_hatches": item.get("deliberate_revoice_gesture_boundary_escape_hatches"),
                    },
                ),
                _check(
                    f"{slug}: deliberate revoice micro-motion policy remains probe-only in default demos",
                    bool(item.get("deliberate_revoice_micro_motion_policy_checkpoint_passed"))
                    and int(item.get("deliberate_revoice_micro_motion_policy_runtime_enabled_events") or 0) == 0
                    and int(item.get("deliberate_revoice_micro_motion_policy_warning_events") or 0) == 0,
                    {
                        "version": item.get("deliberate_revoice_micro_motion_policy_version"),
                        "runtime_enabled_events": item.get("deliberate_revoice_micro_motion_policy_runtime_enabled_events"),
                        "filter_applied_events": item.get("deliberate_revoice_micro_motion_policy_filter_applied_events"),
                        "candidate_match_events": item.get("deliberate_revoice_micro_motion_policy_candidate_match_events"),
                        "fallback_events": item.get("deliberate_revoice_micro_motion_policy_fallback_events"),
                        "warnings": item.get("deliberate_revoice_micro_motion_policy_warning_events"),
                    },
                ),
            ]
        )
    return {"passed": all(check["passed"] for check in checks), "check_count": len(checks), "failed_checks": [check for check in checks if not check["passed"]], "checks": checks}


def _ratio(mapping: Mapping[str, Any], key: str) -> float:
    try:
        return float(mapping.get(key, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _ratio_sum(mapping: Mapping[str, Any], keys: tuple[str, ...]) -> float:
    return sum(_ratio(mapping, key) for key in keys)


def _total_percentages(methods: Mapping[str, Any]) -> dict[str, float]:
    total = sum(int(value or 0) for value in methods.values()) or 1
    return {str(key): float(value or 0) / float(total) for key, value in methods.items()}


def _check(name: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "details": details}


def _format_report(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Medium Swing OPEN/DROP Safe Extension + Top Register Checkpoint Audit")
    lines.append("")
    lines.append(f"- Contract version: `{summary['contract_version']}`")
    lines.append(f"- Milestone: `{summary['milestone']}`")
    lines.append(f"- Acceptance passed: `{summary['acceptance']['passed']}`")
    lines.append("")
    for item in summary["outputs"]:
        lines.append(f"## {item['title']}")
        lines.append("")
        lines.append(f"- MIDI: `{item['midi_path']}`")
        lines.append(f"- Events: `{item['events']}`")
        lines.append(f"- Families: `{item['families']}`")
        lines.append(f"- Methods: `{item['methods']}`")
        lines.append(f"- Contrast roles: `{item['contrast_roles']}`")
        lines.append(f"- Methods by contrast role: `{item['methods_by_contrast_role']}`")
        lines.append(f"- Percentages by contrast role: `{item['method_percentages_by_contrast_role']}`")
        lines.append(f"- OPEN method weight plans: `{item['open_method_weight_plans_by_contrast_role']}`")
        lines.append(f"- Voice-leading transitions: `{item.get('voice_leading_transition_events')}`")
        lines.append(f"- Voice-leading warnings: `{item.get('voice_leading_warning_events')}`")
        lines.append(f"- Method-switch / section-boundary warnings: `{item.get('voice_leading_method_switch_warning_events')}` / `{item.get('voice_leading_section_boundary_warning_events')}`")
        lines.append(f"- Top / low / avg-motion max: `{item.get('voice_leading_top_motion_max_abs')}` / `{item.get('voice_leading_low_motion_max_abs')}` / `{item.get('voice_leading_avg_motion_max')}`")
        lines.append(f"- Section-boundary review events / warnings: `{item.get('section_boundary_review_events')}` / `{item.get('section_boundary_review_warning_events')}`")
        lines.append(f"- Section-boundary entry methods by role: `{item.get('section_boundary_review_entry_methods_by_role')}`")
        lines.append(f"- Section-boundary method pairs: `{item.get('section_boundary_review_method_pairs')}`")
        lines.append(f"- Phrase-scope events / switches / ratio: `{item.get('phrase_scope_events')}` / `{item.get('phrase_scope_method_switch_events')}` / `{item.get('phrase_scope_method_switch_ratio')}`")
        lines.append(f"- Phrase-scope DROP2&4 run events / max: `{item.get('phrase_scope_drop2_and_4_run_events')}` / `{item.get('phrase_scope_drop2_and_4_run_max')}`")
        lines.append(f"- Phrase-scope ii-V / V-I / ii-V-I events: `{item.get('phrase_scope_ii_v_events')}` / `{item.get('phrase_scope_v_i_events')}` / `{item.get('phrase_scope_ii_v_i_events')}`")
        lines.append(f"- Phrase-scope ii-V-I method consistent / switch: `{item.get('phrase_scope_ii_v_i_method_consistent_events')}` / `{item.get('phrase_scope_ii_v_i_method_switch_events')}`")
        lines.append(f"- Phrase-scope high-motion switches / warnings / checkpoint: `{item.get('phrase_scope_high_motion_switch_events')}` / `{item.get('phrase_scope_warning_events')}` / `{item.get('phrase_scope_checkpoint_passed')}`")
        lines.append(f"- Method-lock applied / matched / mismatched / checkpoint: `{item.get('phrase_scope_method_lock_applied_events')}` / `{item.get('phrase_scope_method_lock_candidate_match_events')}` / `{item.get('phrase_scope_method_lock_candidate_mismatch_events')}` / `{item.get('phrase_scope_method_lock_checkpoint_passed')}`")
        lines.append(f"- Generic 4-note rotation runtime-enabled / applied / filtered / checkpoint: `{item.get('four_note_rotation_alignment_runtime_enabled_events')}` / `{item.get('four_note_rotation_alignment_policy_applied_events')}` / `{item.get('four_note_rotation_alignment_filter_applied_events')}` / `{item.get('four_note_rotation_alignment_checkpoint_passed')}`")
        lines.append(f"- Generic 4-note rotation families / sides: desired `{item.get('four_note_rotation_alignment_desired_families')}` / selected `{item.get('four_note_rotation_alignment_selected_families')}`; desired sides `{item.get('four_note_rotation_alignment_desired_sides')}` / selected `{item.get('four_note_rotation_alignment_selected_sides')}`")
        lines.append(f"- Rootless A/B orientation runtime-enabled / applied / filtered / checkpoint: `{item.get('rootless_ab_orientation_alignment_runtime_enabled_events')}` / `{item.get('rootless_ab_orientation_alignment_policy_applied_events')}` / `{item.get('rootless_ab_orientation_alignment_filter_applied_events')}` / `{item.get('rootless_ab_orientation_alignment_checkpoint_passed')}`")
        lines.append(f"- Rootless A/B orientation desired / selected / skip reasons: `{item.get('rootless_ab_orientation_alignment_desired_orientations')}` / `{item.get('rootless_ab_orientation_alignment_selected_orientations')}` / `{item.get('rootless_ab_orientation_alignment_skip_reasons')}`")
        lines.append(f"- Same-chord reattack comping reuse events / reused / exact / warnings / checkpoint: `{item.get('same_chord_reattack_comping_reuse_events')}` / `{item.get('same_chord_reattack_comping_reuse_region_voicing_reused_events')}` / `{item.get('same_chord_reattack_comping_reuse_exact_voicing_reuse_events')}` / `{item.get('same_chord_reattack_comping_reuse_warning_events')}` / `{item.get('same_chord_reattack_comping_reuse_checkpoint_passed')}`")
        lines.append(f"- Safe-extension/top-register checkpoint: `{item.get('safe_extension_top_register_checkpoint_passed')}`; top max / >=75 events: `{item.get('medium_swing_open_drop_top_note_max')}` / `{item.get('medium_swing_open_drop_top_note_ge_75_events')}`")
        lines.append(f"- Deliberate revoice boundary default reuse / explicit / implicit / warnings / checkpoint: `{item.get('deliberate_revoice_gesture_boundary_default_reuse_events')}` / `{item.get('deliberate_revoice_gesture_boundary_explicit_revoice_events')}` / `{item.get('deliberate_revoice_gesture_boundary_implicit_revoice_events')}` / `{item.get('deliberate_revoice_gesture_boundary_warning_events')}` / `{item.get('deliberate_revoice_gesture_boundary_checkpoint_passed')}`")
        lines.append(f"- Deliberate revoice micro-motion runtime / filtered / fallback / warnings / checkpoint: `{item.get('deliberate_revoice_micro_motion_runtime_enabled_events')}` / `{item.get('deliberate_revoice_micro_motion_filter_applied_events')}` / `{item.get('deliberate_revoice_micro_motion_fallback_events')}` / `{item.get('deliberate_revoice_micro_motion_warning_events')}` / `{item.get('deliberate_revoice_micro_motion_checkpoint_passed')}`")
        lines.append(f"- Maj7 color counts / unnotated #11 events: `{item.get('medium_swing_open_drop_major_seventh_degree_counts')}` / `{item.get('medium_swing_open_drop_major_seventh_unnotated_sharp11_events')}`")
        lines.append("")
    lines.append("## Acceptance checks")
    lines.append("")
    for check in summary["acceptance"]["checks"]:
        lines.append(f"- `{check['name']}`: `{check['passed']}` — `{check['details']}`")
    lines.append("")
    lines.append("## Reading note")
    lines.append("")
    lines.append("This is an observational audit: it verifies actual selected projection methods, cross-region voice-leading, local method-lock filtering, generic 4-note rotation alignment, same-chord comping reattack reuse metadata, top-register calmness, major-seventh safe-extension guardrails, explicit revoice boundary metadata, and the v2_6_55 deliberate revoice micro-motion policy probe from runtime debug. Medium Swing still stays in OPEN family; generic_open has zero normal runtime weight and remains available only for explicit rescue/fallback. DROP2 is the baseline body, DROP3 is bridge/final lift, and DROP2&4 is controlled low-frequency color. The v2_6_55 checkpoint is probe-only for explicit same-chord revoice intent: default demos keep the micro-motion runtime inactive, and it does not alter pattern, anticipation, expression, MIDI, or the default cached region-voicing reuse path.")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
