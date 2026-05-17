from __future__ import annotations

import json
import sys
from collections import Counter
from statistics import mean
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.core.harmony.chord_parser import parse_chord

LEADSHEET = PROJECT_ROOT / "examples" / "leadsheets" / "misty.json"
DEMOS_DIR = PROJECT_ROOT / "demos"
NO_EXPANSION_OUTPUT = DEMOS_DIR / "v2_2_88_misty_jazz_ballad_upper_structure_no_expansion_no_altered_demo.mid"
NO_EXPANSION_AUDIT_OUTPUT = DEMOS_DIR / "v2_2_88_misty_jazz_ballad_upper_structure_no_expansion_no_altered_audit_summary.json"
EXPANSION_OUTPUT = DEMOS_DIR / "v2_2_88_misty_jazz_ballad_upper_structure_expansion_only_demo.mid"
EXPANSION_AUDIT_OUTPUT = DEMOS_DIR / "v2_2_88_misty_jazz_ballad_upper_structure_expansion_only_audit_summary.json"
ALTERED_OUTPUT = DEMOS_DIR / "v2_2_88_misty_jazz_ballad_upper_structure_expansion_plus_altered_dominant_demo.mid"
ALTERED_AUDIT_OUTPUT = DEMOS_DIR / "v2_2_88_misty_jazz_ballad_upper_structure_expansion_plus_altered_dominant_audit_summary.json"

_VERSION = "v2_2_88"


def _mix_voicing_override(*, expanded: bool, altered: bool = False, intensity: str = "high") -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "style": "jazz_ballad",
        "primary_family": "spread",
        "allowed_families": ["spread"],
        "spread_selector_enabled": True,
        "ballad_spread_grouping_mix_policy": {
            "version": _VERSION,
            "enabled": True,
            "weight_cycle": 100,
            "scene_strategy": "chorus_aware_normal_lift_ending_climax",
            "style_runtime_default_enabled": False,
            "runtime_enabled": False,
        },
        "ballad_spread_runtime_safe_dry_run": {
            "version": _VERSION,
            "dry_run_enabled": True,
            "candidate_conversion_allowed": True,
            "style_runtime_wiring_enabled": False,
        },
        "spread_runtime_adapter_skeleton": {
            "version": _VERSION,
            "adapter_conversion_allowed": True,
        },
        "ballad_spread_runtime_candidate_pool": {
            "version": _VERSION,
            "candidate_pool_enabled": True,
            "adapter_conversion_allowed": True,
            "candidate_pool_merge_allowed": True,
            "candidate_generator_wiring_allowed": True,
            "fallback_to_existing_pool": True,
            "style_runtime_default_enabled": False,
        },
        "ballad_spread_pilot_runtime_enablement_guard": {
            "version": _VERSION,
            "runtime_guard_enabled": True,
            "listening_isolation_enabled": True,
            "first_listening_isolation_only": True,
            "fallback_required": True,
            "style_runtime_default_enabled": False,
            "default_style_runtime_unchanged": True,
            "runtime_pilot_enabled": True,
            "runtime_enabled": True,
        },
        "ballad_spread_pilot_selection_weight_fallback_audit": {
            "version": _VERSION,
            "audit_enabled": True,
            "fallback_required": True,
            "max_spread_candidate_share": 1.0,
            "max_spread_score_margin": 0.15,
            "candidate_order_is_selection_priority": False,
        },
        "spread_lower_foundation_quality_gate_enabled": True,
        "spread_lower_2note_rooted_equal_weight_cycle_enabled": True,
        "spread_lower_2note_rootless_is_separate_mode": True,
        "spread_lower_3note_rootless_is_separate_mode": True,
        "spread_lower_3note_foundation_lock_enabled": True,
        "spread_upper_3note_shell_plus_1_allowed": False,
        "spread_upper_4note_emit_all_parent_projections": True,
        "spread_upper_4note_allow_octave_shift_candidates": True,
        "spread_runtime_adapter_emit_all_candidates": True,
        "spread_runtime_adapter_max_upper_options": 36,
        "spread_emit_all_candidates_for_groupwise_selection": True,
        "spread_groupwise_voice_leading_runtime_enabled": True,
        "spread_min_group_gap": 1,
        "spread_max_group_gap": 28,
        "spread_max_overall_span": 43,
        "spread_target_group_gap": 7,
        "spread_comfort_group_gap_max": 12,
        "spread_large_group_gap_penalty": 6.0,
        "spread_group_gap_target_penalty": 0.08,
        "spread_top_voice_continuity_version": _VERSION,
        "spread_top_voice_continuity_weight": 2.7,
        "spread_top_voice_close_motion": 2,
        "spread_top_voice_acceptable_motion": 5,
        "spread_top_voice_soft_limit": 7,
        "spread_top_voice_large_jump": 12,
    }
    metadata.update(
        {
            "spread_upper_structure_enabled": True,
            "spread_upper_structure_prefer": bool(altered),
            "spread_upper_structure_only": False,
            "spread_upper_structure_policy_gate_version": _VERSION,
            "spread_upper_structure_lower_gate_enabled": True,
            "spread_low_register_density_guard_enabled": True,
            "spread_low_register_density_threshold": 40,
            "spread_low_register_density_max_notes_below": 1,
            "altered_dominant_enabled": bool(altered),
            "altered_dominant_policy": {
                "enabled": bool(altered),
                "intensity": str(intensity) if altered else "off",
                "scopes": ["resolving_v7", "secondary_dominants", "backdoor_dominants", "llm_selected"],
                "llm_selected": {"region_ids": ["c0_b7_ch1", "c1_b7_ch1", "c2_b7_ch1"]},
                "llm_controllable": True,
                "source_weight_biases_by_intensity": {
                    "medium": {"rooted_color": 0.14, "rootless_ab": 0.04, "upper_structure": 0.06},
                    "high": {"rooted_color": 0.22, "rootless_ab": 0.10, "upper_structure": 0.14},
                    "full": {"rooted_color": 0.30, "rootless_ab": 0.18, "upper_structure": 0.22},
                },
            },
            "weights_by_scene": {
                "normal_comping": {
                    "spread_1plus4_contract": 0,
                    "spread_2plus3_contract": 40,
                    "spread_2plus4_contract": 30,
                    "spread_3plus3_contract": 30,
                    "spread_3plus4_contract": 0,
                },
                "chorus_lift": {
                    "spread_1plus4_contract": 0,
                    "spread_2plus3_contract": 10,
                    "spread_2plus4_contract": 35,
                    "spread_3plus3_contract": 45,
                    "spread_3plus4_contract": 10,
                },
                "ending_climax": {
                    "spread_1plus4_contract": 0,
                    "spread_2plus3_contract": 0,
                    "spread_2plus4_contract": 30,
                    "spread_3plus3_contract": 50,
                    "spread_3plus4_contract": 20,
                },
            },
        }
    )

    if expanded:
        metadata.update(
            {
                "harmonic_expansion_enabled": True,
                "color_policy_mode": "altered_dominant" if altered else "style_safe_extensions",
                "spread_upper_3note_expanded_color_target_ratio": 0.60,
                "spread_upper_3note_expanded_color_ratio_cycle": 5,
                "spread_upper_4note_expanded_color_target_ratio": 0.60,
                "spread_upper_4note_expanded_color_ratio_cycle": 5,
            }
        )
    return {
        "enabled": True,
        "pattern_mode": "region_start_anchor_only",
        "disable_anticipation": True,
        "mute_bass": False,
        "expression_hint": "sustain",
        "harmonic_expansion_enabled": bool(expanded),
        "color_policy_mode": "altered_dominant" if altered else ("style_safe_extensions" if expanded else "chord_symbol_only"),
        "metadata": metadata,
    }


def _counter_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: int(value) for key, value in sorted(counter.items())}


def _avg(values: list[int | float]) -> float:
    return round(float(mean(values)), 3) if values else 0.0


def _is_color_degree_sequence(degrees: list[str]) -> bool:
    stable = {"R", "1", "3", "b3", "5", "b5", "#5", "7", "b7", "bb7", "6"}
    return any(str(degree) not in stable for degree in degrees)


def _mix_audit(debug: dict[str, Any], *, expanded_demo: bool, altered_demo: bool) -> dict[str, Any]:
    events = list(debug.get("piano_musical_audit_events") or [])
    selected_contracts: Counter[str] = Counter()
    selected_groupings: Counter[str] = Counter()
    scenes: Counter[str] = Counter()
    scene_groupings: dict[str, Counter[str]] = {}
    methods: Counter[str] = Counter()
    source_families: Counter[str] = Counter()
    texture_families: Counter[str] = Counter()
    texture_state_ids: Counter[str] = Counter()
    compatible_group_sets: Counter[str] = Counter()
    lower_recipes: Counter[str] = Counter()
    illegal = 0
    fallback_non_spread = 0
    source_integrity_rejected = 0
    drop24 = 0
    actual_color_upper = 0
    upper_rootless_color_3plus4 = 0
    upper_root_degree_3plus4 = 0
    register_violations = 0
    top_ceiling_violations = 0
    gaps: list[int] = []
    large_group_gap_gt12 = 0
    spans: list[int] = []
    tops: list[int] = []
    set_based_vl_events = 0
    unequal_upper_assignment_events = 0
    top_voice_continuity_events = 0
    top_voice_profile_motions: list[int] = []
    top_voice_labels: Counter[str] = Counter()
    upper_structure_events = 0
    upper_structure_density: Counter[str] = Counter()
    upper_structure_sources: Counter[str] = Counter()
    upper_structure_lower_modes: Counter[str] = Counter()
    low_register_density_guard_enabled_events = 0
    low_register_density_guard_violations = 0
    upper_structure_profile_kind: Counter[str] = Counter()
    upper_structure_quality_gates: Counter[str] = Counter()
    altered_functional_scopes: Counter[str] = Counter()
    altered_authorization_reasons: Counter[str] = Counter()
    llm_selected_altered_events = 0
    dominant_events = 0
    dominant_upper_structure_events = 0
    dominant_upper_structure_altered_events = 0
    explicit_altered_dominant_events = 0
    altered_intensities: Counter[str] = Counter()
    altered_source_weight_biases: Counter[str] = Counter()
    altered_source_weight_bias_values: list[float] = []

    for event in events:
        voicing = dict(event.get("voicing") or {})
        metadata = dict(voicing.get("metadata") or {})
        decision = dict(metadata.get("ballad_spread_grouping_mix_policy_decision") or {})
        chord_symbol = str(metadata.get("chord_symbol") or voicing.get("chord_symbol") or event.get("chord_symbol") or "")
        parsed = parse_chord(chord_symbol) if chord_symbol else None
        is_dominant = bool(parsed and parsed.is_dominant)
        if is_dominant:
            dominant_events += 1
            alterations = set(parsed.alterations or ()) if parsed else set()
            if "alt" in chord_symbol.lower() or "alt" in alterations or alterations & {"b9", "#9", "#11", "b13", "#5", "b5"}:
                explicit_altered_dominant_events += 1
        # v2_2_82: the policy may open a compatible texture-family pool; the
        # actual selected candidate can differ from the initial policy slot.
        # Audit actual realized grouping first, then keep the policy decision
        # visible through scene/texture fields.
        selected_contract = str(metadata.get("recipe_id") or metadata.get("ballad_spread_true_isolation_required_recipe_id") or decision.get("selected_contract_id") or "unknown")
        selected_grouping = str(voicing.get("functional_grouping") or metadata.get("grouping") or decision.get("selected_grouping") or "unknown")
        scene = str(decision.get("scene") or "unknown")
        texture_family = str(decision.get("texture_family") or "unknown")
        texture_id = str(decision.get("texture_state_id") or "unknown")
        compatible = tuple(str(item) for item in decision.get("compatible_contract_ids") or [])
        texture_families[texture_family] += 1
        texture_state_ids[texture_id] += 1
        compatible_group_sets["|".join(compatible) if compatible else "unknown"] += 1
        selected_contracts[selected_contract] += 1
        selected_groupings[selected_grouping] += 1
        scenes[scene] += 1
        scene_groupings.setdefault(scene, Counter())[selected_grouping] += 1
        methods[str(metadata.get("upper_projection_method") or "unknown")] += 1
        source_families[str(metadata.get("upper_source_family") or voicing.get("content_family") or "unknown")] += 1
        lower_recipes[str(metadata.get("lower_group_recipe_id") or "unknown")] += 1
        all_source_notes = tuple(str(item) for item in metadata.get("source_metadata") or []) + tuple(str(item) for item in metadata.get("upper_source_metadata") or [])
        for note in all_source_notes:
            if note.startswith("altered_dominant_functional_scope_"):
                scope = note.removeprefix("altered_dominant_functional_scope_")
                altered_functional_scopes[scope] += 1
                if scope == "llm_selected":
                    llm_selected_altered_events += 1
            if note.startswith("altered_dominant_authorization_reason_"):
                altered_authorization_reasons[note.removeprefix("altered_dominant_authorization_reason_")] += 1
            if note.startswith("altered_dominant_intensity_"):
                altered_intensities[note.removeprefix("altered_dominant_intensity_")] += 1
            if "altered_dominant_source_weight_bias_" in note or note.startswith("upper_structure_altered_dominant_intensity_bias_"):
                altered_source_weight_biases[note] += 1
                raw = note.rsplit("_", 1)[-1]
                try:
                    altered_source_weight_bias_values.append(float(raw))
                except ValueError:
                    pass
        if metadata.get("upper_structure_source_enabled") is True:
            upper_structure_events += 1
            if is_dominant:
                dominant_upper_structure_events += 1
            upper_structure_density[str(metadata.get("upper_structure_density") or "unknown")] += 1
            upper_structure_sources[str(metadata.get("upper_structure_source_id") or "unknown")] += 1
            upper_structure_lower_modes[str(metadata.get("upper_structure_lower_mode") or "unknown")] += 1
            metadata_notes = tuple(str(item) for item in metadata.get("upper_source_metadata") or metadata.get("source_metadata") or [])
            for note in metadata_notes:
                if note.startswith("upper_structure_profile_kind_"):
                    kind = note.removeprefix("upper_structure_profile_kind_")
                    upper_structure_profile_kind[kind] += 1
                    if is_dominant and kind == "altered":
                        dominant_upper_structure_altered_events += 1
                if note.startswith("upper_structure_quality_gate_"):
                    upper_structure_quality_gates[note.removeprefix("upper_structure_quality_gate_")] += 1
        low_guard = dict(metadata.get("low_register_density_guard") or {})
        if low_guard.get("enabled") is True:
            low_register_density_guard_enabled_events += 1
            if int(low_guard.get("actual_notes_below") or 0) > int(low_guard.get("max_notes_below") or 1):
                low_register_density_guard_violations += 1
        if metadata.get("spread_set_based_voice_leading_runtime_applied") is True:
            set_based_vl_events += 1
            profile = dict(metadata.get("spread_upper_assignment_profile") or {})
            if int(profile.get("previous_count") or 0) != int(profile.get("current_count") or 0):
                unequal_upper_assignment_events += 1
        if metadata.get("spread_top_voice_continuity_runtime_applied") is True:
            top_voice_continuity_events += 1
            top_profile = dict(metadata.get("spread_top_voice_continuity_profile") or {})
            label = str(top_profile.get("label") or "unknown")
            top_voice_labels[label] += 1
            abs_motion = top_profile.get("top_voice_abs_motion")
            if abs_motion is not None:
                try:
                    top_voice_profile_motions.append(int(abs_motion))
                except (TypeError, ValueError):
                    pass
        upper_degrees = [str(item) for item in metadata.get("upper_source_degrees") or []]
        if _is_color_degree_sequence(upper_degrees):
            actual_color_upper += 1
        if selected_grouping == "3+4":
            if metadata.get("spread_3plus4_upper_rootless_color_passed") is True:
                upper_rootless_color_3plus4 += 1
            if any(item in {"R", "1"} for item in upper_degrees):
                upper_root_degree_3plus4 += 1
            midi_notes = [int(note) for note in voicing.get("midi_notes") or []]
            if midi_notes and max(midi_notes) > 79:
                top_ceiling_violations += 1
        if metadata.get("is_legal") is False:
            illegal += 1
        if str(voicing.get("disposition") or "").lower() != "spread":
            fallback_non_spread += 1
        if metadata.get("legality_reason") == "spread_candidate_rejected_by_global_seventh_chord_source_integrity_gate":
            source_integrity_rejected += 1
        if str(metadata.get("upper_projection_method") or "") == "drop2_and_4":
            drop24 += 1
        midi_notes = [int(note) for note in voicing.get("midi_notes") or []]
        whole_low = int(metadata.get("whole_register_low") or 0)
        whole_high = int(metadata.get("whole_register_high") or 127)
        if midi_notes and any(note < whole_low or note > whole_high for note in midi_notes):
            register_violations += 1
        if midi_notes:
            tops.append(max(midi_notes))
        if metadata.get("group_gap_semitones") is not None:
            gap_value = int(metadata.get("group_gap_semitones") or 0)
            gaps.append(gap_value)
            if gap_value > 12:
                large_group_gap_gt12 += 1
        if metadata.get("overall_span_semitones") is not None:
            spans.append(int(metadata.get("overall_span_semitones") or 0))

    top_motions = [abs(tops[index] - tops[index - 1]) for index in range(1, len(tops))]
    return {
        "audit_version": _VERSION,
        "scope": "Ballad SPREAD Upper Structure policy gate plus v2_2_88 Altered Dominant Intensity / Source Weight Calibration; default runtime remains unchanged.",
        "expanded_demo": bool(expanded_demo),
        "altered_dominant_demo": bool(altered_demo),
        "upper_structure_policy_gate_version": _VERSION,
        "upper_structure_pilot": bool(expanded_demo or altered_demo),
        "events": len(events),
        "selected_contracts": _counter_dict(selected_contracts),
        "selected_groupings": _counter_dict(selected_groupings),
        "deprecated_1plus3_selected_events": int(selected_groupings.get("1+3", 0)),
        "scenes": _counter_dict(scenes),
        "scene_groupings": {scene: _counter_dict(counter) for scene, counter in sorted(scene_groupings.items())},
        "texture_state_mix_version": _VERSION,
        "texture_families": _counter_dict(texture_families),
        "texture_state_ids": _counter_dict(texture_state_ids),
        "compatible_group_sets": _counter_dict(compatible_group_sets),
        "set_based_voice_leading_events": int(set_based_vl_events),
        "unequal_upper_assignment_events": int(unequal_upper_assignment_events),
        "top_voice_continuity_version": _VERSION,
        "top_voice_continuity_events": int(top_voice_continuity_events),
        "top_voice_continuity_labels": _counter_dict(top_voice_labels),
        "top_voice_profile_avg_abs_motion_semitones": _avg(top_voice_profile_motions),
        "top_voice_profile_max_abs_motion_semitones": max(top_voice_profile_motions) if top_voice_profile_motions else None,
        "large_top_jump_gt7_events": sum(1 for value in top_voice_profile_motions if value > 7),
        "extreme_top_jump_gt12_events": sum(1 for value in top_voice_profile_motions if value > 12),
        "top_voice_profile_motion_distribution": _counter_dict(Counter(str(value) for value in top_voice_profile_motions)),
        "upper_projection_methods": _counter_dict(methods),
        "upper_source_families": _counter_dict(source_families),
        "lower_group_recipes": _counter_dict(lower_recipes),
        "upper_structure_events": int(upper_structure_events),
        "upper_structure_density": _counter_dict(upper_structure_density),
        "upper_structure_sources": _counter_dict(upper_structure_sources),
        "upper_structure_profile_kind": _counter_dict(upper_structure_profile_kind),
        "upper_structure_quality_gates": _counter_dict(upper_structure_quality_gates),
        "upper_structure_lower_modes": _counter_dict(upper_structure_lower_modes),
        "altered_dominant_functional_scopes": _counter_dict(altered_functional_scopes),
        "altered_dominant_authorization_reasons": _counter_dict(altered_authorization_reasons),
        "altered_dominant_intensities": _counter_dict(altered_intensities),
        "altered_dominant_source_weight_bias_notes": _counter_dict(altered_source_weight_biases),
        "altered_dominant_source_weight_bias_avg": _avg(altered_source_weight_bias_values),
        "llm_selected_altered_events": int(llm_selected_altered_events),
        "dominant_events": int(dominant_events),
        "dominant_upper_structure_events": int(dominant_upper_structure_events),
        "dominant_upper_structure_altered_events": int(dominant_upper_structure_altered_events),
        "dominant_upper_structure_altered_ratio": round(float(dominant_upper_structure_altered_events) / float(max(1, dominant_upper_structure_events)), 3),
        "explicit_altered_dominant_events": int(explicit_altered_dominant_events),
        "low_register_density_guard_enabled_events": int(low_register_density_guard_enabled_events),
        "low_register_density_guard_violations": int(low_register_density_guard_violations),
        "actual_color_upper_events": actual_color_upper,
        "upper_rootless_color_3plus4_events": upper_rootless_color_3plus4,
        "upper_root_degree_3plus4_events": upper_root_degree_3plus4,
        "illegal_candidate_events": illegal,
        "fallback_non_spread_events": fallback_non_spread,
        "source_integrity_rejected_events": source_integrity_rejected,
        "drop2_and_4_events": drop24,
        "whole_register_violations": register_violations,
        "top_ceiling_violations_3plus4_g5": top_ceiling_violations,
        "avg_group_gap_semitones": _avg(gaps),
        "min_group_gap_semitones": min(gaps) if gaps else None,
        "max_group_gap_semitones": max(gaps) if gaps else None,
        "large_group_gap_gt12_events": large_group_gap_gt12,
        "group_gap_distribution": _counter_dict(Counter(str(gap) for gap in gaps)),
        "avg_overall_span_semitones": _avg(spans),
        "min_overall_span_semitones": min(spans) if spans else None,
        "max_overall_span_semitones": max(spans) if spans else None,
        "avg_top_voice_abs_motion_semitones": _avg(top_motions),
        "max_top_voice_abs_motion_semitones": max(top_motions) if top_motions else None,
        "style_runtime_default_enabled": False,
        "candidate_conversion_allowed_only_in_explicit_demo_override": True,
        "default_ballad_runtime_unchanged": True,
        "content_families": debug.get("piano_musical_audit", {}).get("content_families", {}),
        "densities": debug.get("piano_musical_audit", {}).get("densities", {}),
        "functional_groupings": debug.get("piano_musical_audit", {}).get("functional_groupings", {}),
    }


def _run_one(*, expanded: bool, altered: bool, output: Path, audit_output: Path) -> dict[str, Any]:
    score = json.loads(LEADSHEET.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "jazz_ballad",
            "tempo": int(score.get("tempo", 82)),
            "choruses": 3,
            "seed": 2278,
            "output_path": str(output),
            "ensemble": {"bass_present": True},
            "voicing_override": _mix_voicing_override(expanded=expanded, altered=altered, intensity="high"),
        }
    )
    debug = dict(result.debug)
    audit = _mix_audit(debug, expanded_demo=expanded, altered_demo=altered)
    audit_output.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    if not result.ok:
        raise SystemExit(1)
    return {
        "ok": bool(result.ok),
        "midi_path": str(output.relative_to(PROJECT_ROOT)),
        "audit_path": str(audit_output.relative_to(PROJECT_ROOT)),
        "audit": audit,
    }


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    no_expansion = _run_one(
        expanded=False,
        altered=False,
        output=NO_EXPANSION_OUTPUT,
        audit_output=NO_EXPANSION_AUDIT_OUTPUT,
    )
    expansion_only = _run_one(
        expanded=True,
        altered=False,
        output=EXPANSION_OUTPUT,
        audit_output=EXPANSION_AUDIT_OUTPUT,
    )
    expansion_plus_altered = _run_one(
        expanded=True,
        altered=True,
        output=ALTERED_OUTPUT,
        audit_output=ALTERED_AUDIT_OUTPUT,
    )
    print(json.dumps({
        "no_expansion_no_altered": no_expansion,
        "expansion_only": expansion_only,
        "expansion_plus_altered_dominant": expansion_plus_altered,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
