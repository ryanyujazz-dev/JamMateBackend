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

LEADSHEET = PROJECT_ROOT / "examples" / "leadsheets" / "misty.json"
DEMOS_DIR = PROJECT_ROOT / "demos"
UNEXPANDED_OUTPUT = DEMOS_DIR / "v2_2_77_voicing_cleanup_misty_spread_3plus4_reference_demo.mid"
UNEXPANDED_AUDIT_OUTPUT = DEMOS_DIR / "v2_2_77_voicing_cleanup_misty_spread_3plus4_reference_audit_summary.json"
EXPANDED_OUTPUT = DEMOS_DIR / "v2_2_77_voicing_cleanup_misty_spread_3plus4_expanded_flag_demo.mid"
EXPANDED_AUDIT_OUTPUT = DEMOS_DIR / "v2_2_77_voicing_cleanup_misty_spread_3plus4_expanded_flag_audit_summary.json"


_CONTRACT_ID = "spread_3plus4_contract"
_VERSION = "v2_2_76"


def _listening_voicing_override(*, expanded: bool) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "style": "jazz_ballad",
        "primary_family": "spread",
        "allowed_families": ["spread"],
        "spread_selector_enabled": True,
        "ballad_spread_3plus4_pilot": {
            "version": _VERSION,
            "enabled": True,
            "required_recipe_id": _CONTRACT_ID,
            "dual_demo_required": True,
            "upper_color_required_ratio": 1.0,
            "upper_rootless_color_preferred_for_seventh_chords": True,
            "target": "explicit_ballad_spread_3plus4_musical_closure_isolation_only",
            "style_runtime_default_enabled": False,
            "runtime_enabled": False,
        },
        "ballad_spread_runtime_pilot": {
            "version": _VERSION,
            "enabled": True,
            "scene": "warm_spread_phrase",
            "contract_ids": [_CONTRACT_ID],
            "preferred_contract_ids": [_CONTRACT_ID],
            "runtime_boundary": "first_listening_isolation_only",
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
        "ballad_spread_pilot_selection_weight_fallback_audit": {
            "version": _VERSION,
            "audit_enabled": True,
            "fallback_required": True,
            "max_spread_candidate_share": 1.0,
            "max_spread_score_margin": 0.15,
            "candidate_order_is_selection_priority": False,
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
        "spread_contract_true_isolation": {
            "version": _VERSION,
            "enabled": True,
            "required_recipe_id": _CONTRACT_ID,
            "fallback_only_when_missing": True,
            "candidate_pool_mode": "spread_only_when_available",
        },
        "spread_lower_3note_foundation_mode": "rooted",
        "spread_lower_3note_rootless_is_separate_mode": True,
        "spread_lower_3note_rooted_equal_weight_cycle_enabled": False,
        "spread_lower_3note_foundation_lock_enabled": True,
        "spread_lower_3note_recipe_change_penalty": 6.0,
        "spread_lower_3note_rooted_recipe_weights": {
            "lower_3note_root_7_upper3": 1,
            "lower_3note_root_5_upper3": 1,
        },
        "spread_lower_foundation_quality_gate_enabled": True,
        "spread_rooted_bass_anchor_enabled": True,
        "spread_root_bass_anchor_low": 33,
        "spread_root_bass_anchor_high": 48,
        "spread_root_bass_anchor_target": 39,
        "spread_root_bass_anchor_high_tail_semitones": 4,
        "spread_root_bass_anchor_high_tail_max_lower_span": 12,
        "spread_whole_register_low": 33,
        "spread_whole_register_high": 79,
        "spread_whole_register_target_span": 34,
        "spread_lower_2note_low": 36,
        "spread_lower_2note_high": 83,
        "spread_lower_2note_target_low": 36,
        "spread_lower_2note_min_top": 0,
        "spread_upper_low": 52,
        "spread_upper_high": 79,
        "spread_upper_target_low": 57,
        "spread_min_group_gap": 1,
        "spread_max_group_gap": 7,
        "spread_max_overall_span": 39,
        "spread_upper_4note_emit_all_parent_projections": True,
        "spread_upper_4note_allow_octave_shift_candidates": True,
        "spread_runtime_adapter_emit_all_candidates": True,
        "spread_emit_all_candidates_for_groupwise_selection": True,
        "spread_groupwise_voice_leading_runtime_enabled": True,
    }
    if expanded:
        metadata.update(
            {
                "harmonic_expansion_enabled": True,
                "color_policy_mode": "style_safe_extensions",
                "spread_3plus4_expanded_flag_demo": True,
            }
        )
    return {
        "enabled": True,
        "pattern_mode": "region_start_anchor_only",
        "disable_anticipation": True,
        "mute_bass": False,
        "expression_hint": "sustain",
        "harmonic_expansion_enabled": bool(expanded),
        "color_policy_mode": "style_safe_extensions" if expanded else "chord_symbol_only",
        "metadata": metadata,
    }


def _counter_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: int(value) for key, value in sorted(counter.items())}


def _avg(values: list[int | float]) -> float:
    return round(float(mean(values)), 3) if values else 0.0


def _is_actual_expanded_upper(degrees: list[str]) -> bool:
    stable = {"R", "1", "3", "b3", "5", "b5", "#5", "7", "b7", "bb7", "6"}
    return any(str(degree) not in stable for degree in degrees)


def _spread_3plus4_audit(debug: dict[str, Any], *, expanded_demo: bool) -> dict[str, Any]:
    events = list(debug.get("piano_musical_audit_events") or [])
    methods: Counter[str] = Counter()
    source_families: Counter[str] = Counter()
    source_degree_orders: Counter[str] = Counter()
    lower_recipes: Counter[str] = Counter()
    groupings: Counter[str] = Counter()
    ratio_slots: Counter[str] = Counter()
    gaps: list[int] = []
    spans: list[int] = []
    top_notes: list[int] = []
    illegal_count = 0
    integrity_preserved = 0
    integrity_rejected = 0
    actual_expanded = 0
    lower_min_notes: list[int] = []
    lower_max_notes: list[int] = []
    root_anchor_targets: Counter[str] = Counter()
    upper_min_notes: list[int] = []
    upper_spans: list[int] = []
    upper_shell_plus_one_events = 0
    rootless_lower_events = 0
    root_not_lowest_events = 0
    root_anchor_out_of_window_events = 0
    whole_register_violations = 0
    root_anchor_tail_span_guard_failures = 0
    upper_color_failed_events = 0
    top_ceiling_violations = 0
    lower_register_compression_events = 0
    upper_root_degree_events = 0
    upper_rootless_color_events = 0
    upper_rooted_color_events = 0
    upper_nonroot_color_fallback_events = 0
    chord_symbols: Counter[str] = Counter()
    compression_chords: Counter[str] = Counter()
    top_note_distribution: Counter[str] = Counter()
    lower_max_note_distribution: Counter[str] = Counter()
    upper_min_note_distribution: Counter[str] = Counter()
    gap_distribution: Counter[str] = Counter()
    span_distribution: Counter[str] = Counter()

    for event in events:
        voicing = dict(event.get("voicing") or {})
        metadata = dict(voicing.get("metadata") or {})
        chord_symbol = str(metadata.get("chord_symbol") or event.get("chord_symbol") or "unknown")
        chord_symbols[chord_symbol] += 1
        groupings[str(voicing.get("functional_grouping") or metadata.get("grouping") or "unknown")] += 1
        methods[str(metadata.get("upper_projection_method") or "unknown")] += 1
        source_families[str(metadata.get("upper_source_family") or voicing.get("content_family") or "unknown")] += 1
        upper_degrees = [str(item) for item in metadata.get("upper_source_degrees") or []]
        source_degree_orders["-".join(upper_degrees)] += 1
        if any(item in {"R", "1"} for item in upper_degrees):
            upper_root_degree_events += 1
        if metadata.get("spread_3plus4_upper_rootless_color_passed") is True:
            upper_rootless_color_events += 1
        elif str(metadata.get("upper_source_family")) == "rooted_color":
            upper_rooted_color_events += 1
        elif metadata.get("spread_3plus4_upper_source_color_passed") is True:
            upper_nonroot_color_fallback_events += 1
        lower_recipe_id = str(metadata.get("lower_group_recipe_id") or "unknown")
        lower_recipes[lower_recipe_id] += 1
        lower_degrees = [str(item) for item in metadata.get("lower_group_degrees") or []]
        lower_notes = [int(item) for item in metadata.get("lower_group_notes") or []]
        if lower_notes:
            lower_min_notes.append(min(lower_notes))
            lower_max_notes.append(max(lower_notes))
            lower_max_note_distribution[str(max(lower_notes))] += 1
        if lower_recipe_id in {"lower_2note_3_7", "lower_3note_3_7"}:
            rootless_lower_events += 1
        root_note = metadata.get("root_bass_anchor_note")
        midi_notes = [int(note) for note in voicing.get("midi_notes") or []]
        if root_note is None or (midi_notes and int(root_note) != min(midi_notes)):
            root_not_lowest_events += 1
        root_low = int(metadata.get("root_bass_anchor_low") or 36)
        root_high = int(metadata.get("root_bass_anchor_high") or 48)
        root_anchor_targets[str(metadata.get("root_bass_anchor_target") or 39)] += 1
        if root_note is None or int(root_note) < root_low or int(root_note) > root_high:
            root_anchor_out_of_window_events += 1
        whole_low = int(metadata.get("whole_register_low") or 36)
        whole_high = int(metadata.get("whole_register_high") or 79)
        if midi_notes and any(note < whole_low or note > whole_high for note in midi_notes):
            whole_register_violations += 1
        if metadata.get("lower_group_anchor_tail_span_guard_passed") is False:
            root_anchor_tail_span_guard_failures += 1
        upper_notes = [int(item) for item in metadata.get("upper_group_notes") or []]
        if upper_notes:
            upper_min_notes.append(min(upper_notes))
            upper_spans.append(max(upper_notes) - min(upper_notes))
            upper_min_note_distribution[str(min(upper_notes))] += 1
        if str(metadata.get("upper_source_family")) in {"shell_plus_5", "shell_plus_color"} and any(item in {"R", "1"} for item in upper_degrees):
            upper_shell_plus_one_events += 1
        gap = int(metadata.get("group_gap_semitones") or 0)
        span = int(metadata.get("overall_span_semitones") or 0)
        gaps.append(gap)
        spans.append(span)
        gap_distribution[str(gap)] += 1
        span_distribution[str(span)] += 1
        if metadata.get("spread_3plus4_upper_source_color_passed") is not True:
            upper_color_failed_events += 1
        if metadata.get("spread_3plus4_lower_upper3_compressed_within_root_octave") is True:
            lower_register_compression_events += 1
            compression_chords[chord_symbol] += 1
        if midi_notes:
            top_note = max(midi_notes)
            top_notes.append(top_note)
            top_note_distribution[str(top_note)] += 1
            if top_note > 79:
                top_ceiling_violations += 1
        if metadata.get("is_legal") is False:
            illegal_count += 1
        if metadata.get("source_preserves_seventh_chord_identity") is True:
            integrity_preserved += 1
        if metadata.get("legality_reason") == "spread_candidate_rejected_by_global_seventh_chord_source_integrity_gate":
            integrity_rejected += 1
        if _is_actual_expanded_upper(upper_degrees):
            actual_expanded += 1
        if "spread_upper_4note_expanded_color_ratio_slot" in metadata:
            ratio_slots[str(metadata.get("spread_upper_4note_expanded_color_ratio_slot"))] += 1

    top_motions = [abs(top_notes[index] - top_notes[index - 1]) for index in range(1, len(top_notes))]
    return {
        "audit_version": _VERSION,
        "scope": "Ballad SPREAD 3+4 musical closure audit; 3+4 lower gate uses root+7+upper3 for seventh chords and root+5+upper3 for triad-family chords; upper 4-note is contract-local color-only and now prefers rootless color upper blocks for seventh-family chords; root anchor is A1-C3 with Eb2 target; 3+4 whole-register guard is A1-G5; high-root lower compression keeps upper3 content in the root octave when required; anchor-tail span guard is disabled only for 3+4.",
        "expanded_demo": bool(expanded_demo),
        "target_expanded_ratio": 1.0,
        "events": len(events),
        "actual_expanded_events": int(actual_expanded),
        "actual_non_expanded_events": int(len(events) - actual_expanded),
        "actual_expanded_ratio": round(actual_expanded / len(events), 3) if events else 0.0,
        "groupings": _counter_dict(groupings),
        "upper_projection_methods": _counter_dict(methods),
        "upper_source_families": _counter_dict(source_families),
        "upper_source_degree_orders": _counter_dict(source_degree_orders),
        "upper_root_degree_events": int(upper_root_degree_events),
        "upper_rootless_color_events": int(upper_rootless_color_events),
        "upper_rootless_color_ratio": round(upper_rootless_color_events / len(events), 3) if events else 0.0,
        "upper_rooted_color_events": int(upper_rooted_color_events),
        "upper_nonroot_color_fallback_events": int(upper_nonroot_color_fallback_events),
        "chord_symbols": _counter_dict(chord_symbols),
        "lower_group_recipes": _counter_dict(lower_recipes),
        "rooted_bass_anchor_policy": {
            "enabled": True,
            "root_bass_low": "A1",
            "root_bass_high": "C3",
            "root_bass_target": "Eb2",
            "root_bass_low_midi": 33,
            "root_bass_high_midi": 48,
            "root_bass_target_midi": 39,
            "root_must_be_lowest_note": True,
            "whole_register_low": "A1",
            "whole_register_high": "G5",
            "whole_register_low_midi": 33,
            "whole_register_high_midi": 79,
            "lower_foundation_mode": "rooted",
            "lower_foundation_lock_enabled": True,
            "rooted_recipe_weights": {
                "lower_3note_root_7_upper3": 1,
                "lower_3note_root_5_upper3": 1,
            },
            "rootless_separate_mode": True,
        },
        "root_anchor_targets": _counter_dict(root_anchor_targets),
        "lower_min_note_midi": min(lower_min_notes) if lower_min_notes else None,
        "lower_max_note_midi": max(lower_max_notes) if lower_max_notes else None,
        "avg_lower_max_note_midi": _avg(lower_max_notes),
        "rootless_lower_events": rootless_lower_events,
        "root_not_lowest_events": root_not_lowest_events,
        "root_anchor_out_of_window_events": root_anchor_out_of_window_events,
        "whole_register_violations": whole_register_violations,
        "root_anchor_tail_span_guard_failures": root_anchor_tail_span_guard_failures,
        "upper_shell_plus_one_events": upper_shell_plus_one_events,
        "upper_color_failed_events": upper_color_failed_events,
        "lower_register_compression_events": lower_register_compression_events,
        "lower_register_compression_chords": _counter_dict(compression_chords),
        "top_ceiling_violations": top_ceiling_violations,
        "upper_4note_policy": {
            "placement": "drop_family_upper_block",
            "projection_methods_allowed": ["drop2", "drop3"],
            "drop2_and_4_allowed": False,
            "source_owner": "same upper 4-note source/projection logic as spread_2plus4_contract / spread_1plus4_contract",
            "selection": "color-only upper 4-note, then emit_all_parent_projections, then groupwise nearest plus whole-voicing scorer",
            "upper_color_required_ratio": 1.0,
            "ceiling": "G5",
            "ceiling_midi": 79,
        },
        "upper_min_note_midi": min(upper_min_notes) if upper_min_notes else None,
        "note_distributions": {
            "top_note_midi": _counter_dict(top_note_distribution),
            "lower_max_note_midi": _counter_dict(lower_max_note_distribution),
            "upper_min_note_midi": _counter_dict(upper_min_note_distribution),
            "group_gap_semitones": _counter_dict(gap_distribution),
            "overall_span_semitones": _counter_dict(span_distribution),
        },
        "drop2_and_4_events": int(methods.get("drop2_and_4", 0)),
        "max_upper_span_semitones": max(upper_spans) if upper_spans else None,
        "ratio_slots": _counter_dict(ratio_slots),
        "source_integrity_preserved_events": integrity_preserved,
        "source_integrity_rejected_events": integrity_rejected,
        "avg_group_gap_semitones": _avg(gaps),
        "min_group_gap_semitones": min(gaps) if gaps else None,
        "max_group_gap_semitones": max(gaps) if gaps else None,
        "avg_overall_span_semitones": _avg(spans),
        "min_overall_span_semitones": min(spans) if spans else None,
        "max_overall_span_semitones": max(spans) if spans else None,
        "avg_top_voice_abs_motion_semitones": _avg(top_motions),
        "max_top_voice_abs_motion_semitones": max(top_motions) if top_motions else None,
        "illegal_candidate_events": illegal_count,
        "musical_closure_flags": {
            "all_events_are_3plus4": groupings.get("3+4", 0) == len(events),
            "upper_color_only_passed": upper_color_failed_events == 0,
            "rootless_upper_used_when_available": upper_rootless_color_events > 0 and upper_rooted_color_events == 0,
            "whole_register_a1_g5_passed": whole_register_violations == 0 and top_ceiling_violations == 0,
            "drop2_and_4_absent": int(methods.get("drop2_and_4", 0)) == 0,
            "source_integrity_passed": integrity_rejected == 0,
        },
        "content_families": debug.get("piano_musical_audit", {}).get("content_families", {}),
        "densities": debug.get("piano_musical_audit", {}).get("densities", {}),
        "functional_groupings": debug.get("piano_musical_audit", {}).get("functional_groupings", {}),
    }


def _render(score: dict[str, Any], *, expanded: bool, output: Path, audit_output: Path) -> dict[str, Any]:
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "jazz_ballad",
            "tempo": int(score.get("tempo", 82)),
            "choruses": 3,
            "seed": 2250,
            "output_path": str(output),
            "ensemble": {"bass_present": True},
            "voicing_override": _listening_voicing_override(expanded=expanded),
        }
    )
    debug = dict(result.debug)
    audit = _spread_3plus4_audit(debug, expanded_demo=expanded)
    audit_output.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    if not result.ok:
        raise SystemExit(1)
    return {
        "ok": bool(result.ok),
        "version": result.version,
        "title": score.get("title"),
        "style": result.style,
        "expanded_demo": bool(expanded),
        "midi_path": str(output.relative_to(PROJECT_ROOT)),
        "audit_path": str(audit_output.relative_to(PROJECT_ROOT)),
        "audit": audit,
    }


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    score = json.loads(LEADSHEET.read_text(encoding="utf-8"))
    summaries = [
        _render(score, expanded=False, output=UNEXPANDED_OUTPUT, audit_output=UNEXPANDED_AUDIT_OUTPUT),
        _render(score, expanded=True, output=EXPANDED_OUTPUT, audit_output=EXPANDED_AUDIT_OUTPUT),
    ]
    print(json.dumps({"ok": True, "version": _VERSION, "summaries": summaries}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
