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
UNEXPANDED_OUTPUT = DEMOS_DIR / "v2_2_73_misty_jazz_ballad_spread_2plus3_root_anchor_e2_e3_gap_p5_unexpanded_demo.mid"
UNEXPANDED_AUDIT_OUTPUT = DEMOS_DIR / "v2_2_73_misty_jazz_ballad_spread_2plus3_root_anchor_e2_e3_gap_p5_unexpanded_audit_summary.json"
EXPANDED_OUTPUT = DEMOS_DIR / "v2_2_73_misty_jazz_ballad_spread_2plus3_root_anchor_e2_e3_gap_p5_expanded_60pct_demo.mid"
EXPANDED_AUDIT_OUTPUT = DEMOS_DIR / "v2_2_73_misty_jazz_ballad_spread_2plus3_root_anchor_e2_e3_gap_p5_expanded_60pct_audit_summary.json"


_CONTRACT_ID = "spread_2plus3_contract"
_VERSION = "v2_2_73"


def _listening_voicing_override(*, expanded: bool) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "style": "jazz_ballad",
        "primary_family": "spread",
        "allowed_families": ["spread"],
        "spread_selector_enabled": True,
        "ballad_spread_2plus3_pilot": {
            "version": _VERSION,
            "enabled": True,
            "required_recipe_id": _CONTRACT_ID,
            "dual_demo_required": True,
            "expanded_demo_target_ratio": 0.60,
            "target": "explicit_ballad_spread_2plus3_listening_isolation_only",
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
        "spread_lower_2note_foundation_mode": "rooted",
        "spread_lower_2note_rootless_is_separate_mode": True,
        "spread_lower_2note_rooted_equal_weight_cycle_enabled": False,
        "spread_lower_2note_foundation_lock_enabled": True,
        "spread_lower_2note_recipe_change_penalty": 6.0,
        "spread_lower_2note_rooted_recipe_weights": {
            "lower_2note_root_3": 1,
            "lower_2note_root_5": 1,
            "lower_2note_root_7": 1,
        },
        "spread_lower_foundation_quality_gate_enabled": True,
        "spread_rooted_bass_anchor_enabled": True,
        "spread_root_bass_anchor_low": 40,
        "spread_root_bass_anchor_high": 52,
        "spread_root_bass_anchor_target": 47,
        "spread_root_bass_anchor_high_tail_semitones": 4,
        "spread_root_bass_anchor_high_tail_max_lower_span": 12,
        "spread_whole_register_low": 40,
        "spread_whole_register_high": 73,
        "spread_whole_register_target_span": 27,
        "spread_lower_2note_low": 40,
        "spread_lower_2note_high": 68,
        "spread_lower_2note_target_low": 40,
        "spread_lower_2note_min_top": 0,
        "spread_upper_low": 52,
        "spread_upper_target_low": 61,
        "spread_upper_3note_min_note_floor": 52,
        "spread_upper_3note_shell_plus_1_allowed": False,
        "spread_min_group_gap": 1,
        "spread_max_group_gap": 7,
        "spread_max_overall_span": 33,
        "spread_runtime_adapter_emit_all_candidates": True,
        "spread_emit_all_candidates_for_groupwise_selection": True,
        "spread_groupwise_voice_leading_runtime_enabled": True,
    }
    if expanded:
        metadata.update(
            {
                "harmonic_expansion_enabled": True,
                "color_policy_mode": "style_safe_extensions",
                "spread_upper_3note_expanded_color_target_ratio": 0.60,
                "spread_upper_3note_expanded_color_ratio_cycle": 5,
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


def _spread_2plus3_audit(debug: dict[str, Any], *, expanded_demo: bool) -> dict[str, Any]:
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
    upper_min_notes: list[int] = []
    upper_spans: list[int] = []
    upper_shell_plus_one_events = 0
    rootless_lower_events = 0
    root_not_lowest_events = 0
    root_anchor_out_of_window_events = 0
    whole_register_violations = 0
    root_anchor_tail_span_guard_failures = 0

    for event in events:
        voicing = dict(event.get("voicing") or {})
        metadata = dict(voicing.get("metadata") or {})
        groupings[str(voicing.get("functional_grouping") or metadata.get("grouping") or "unknown")] += 1
        methods[str(metadata.get("upper_projection_method") or "unknown")] += 1
        source_families[str(metadata.get("upper_source_family") or voicing.get("content_family") or "unknown")] += 1
        upper_degrees = [str(item) for item in metadata.get("upper_source_degrees") or []]
        source_degree_orders["-".join(upper_degrees)] += 1
        lower_recipe_id = str(metadata.get("lower_group_recipe_id") or "unknown")
        lower_recipes[lower_recipe_id] += 1
        lower_degrees = [str(item) for item in metadata.get("lower_group_degrees") or []]
        lower_notes = [int(item) for item in metadata.get("lower_group_notes") or []]
        if lower_notes:
            lower_min_notes.append(min(lower_notes))
            lower_max_notes.append(max(lower_notes))
        if lower_recipe_id == "lower_2note_3_7":
            rootless_lower_events += 1
        root_note = metadata.get("root_bass_anchor_note")
        midi_notes = [int(note) for note in voicing.get("midi_notes") or []]
        if root_note is None or (midi_notes and int(root_note) != min(midi_notes)):
            root_not_lowest_events += 1
        root_low = int(metadata.get("root_bass_anchor_low") or 36)
        root_high = int(metadata.get("root_bass_anchor_high") or 48)
        if root_note is None or int(root_note) < root_low or int(root_note) > root_high:
            root_anchor_out_of_window_events += 1
        whole_low = int(metadata.get("whole_register_low") or 36)
        whole_high = int(metadata.get("whole_register_high") or 69)
        if midi_notes and any(note < whole_low or note > whole_high for note in midi_notes):
            whole_register_violations += 1
        if metadata.get("lower_group_anchor_tail_span_guard_passed") is False:
            root_anchor_tail_span_guard_failures += 1
        upper_notes = [int(item) for item in metadata.get("upper_group_notes") or []]
        if upper_notes:
            upper_min_notes.append(min(upper_notes))
            upper_spans.append(max(upper_notes) - min(upper_notes))
        if str(metadata.get("upper_source_family")) in {"shell_plus_5", "shell_plus_color"} and any(item in {"R", "1"} for item in upper_degrees):
            upper_shell_plus_one_events += 1
        gaps.append(int(metadata.get("group_gap_semitones") or 0))
        spans.append(int(metadata.get("overall_span_semitones") or 0))
        if midi_notes:
            top_notes.append(max(midi_notes))
        if metadata.get("is_legal") is False:
            illegal_count += 1
        if metadata.get("source_preserves_seventh_chord_identity") is True:
            integrity_preserved += 1
        if metadata.get("legality_reason") == "spread_candidate_rejected_by_global_seventh_chord_source_integrity_gate":
            integrity_rejected += 1
        if _is_actual_expanded_upper(upper_degrees):
            actual_expanded += 1
        if "spread_upper_3note_expanded_color_ratio_slot" in metadata:
            ratio_slots[str(metadata.get("spread_upper_3note_expanded_color_ratio_slot"))] += 1

    top_motions = [abs(top_notes[index] - top_notes[index - 1]) for index in range(1, len(top_notes))]
    return {
        "audit_version": _VERSION,
        "scope": "Ballad SPREAD 2+3 dual-demo audit; rooted bass anchor + lower foundation lock + closed upper 3-note; expanded demo targets ~60% actual color.",
        "expanded_demo": bool(expanded_demo),
        "target_expanded_ratio": 0.60 if expanded_demo else 0.0,
        "events": len(events),
        "actual_expanded_events": int(actual_expanded),
        "actual_non_expanded_events": int(len(events) - actual_expanded),
        "actual_expanded_ratio": round(actual_expanded / len(events), 3) if events else 0.0,
        "groupings": _counter_dict(groupings),
        "upper_projection_methods": _counter_dict(methods),
        "upper_source_families": _counter_dict(source_families),
        "upper_source_degree_orders": _counter_dict(source_degree_orders),
        "lower_group_recipes": _counter_dict(lower_recipes),
        "rooted_bass_anchor_policy": {
            "enabled": True,
            "root_bass_low": "E2",
            "root_bass_high": "E3",
            "root_bass_low_midi": 40,
            "root_bass_high_midi": 52,
            "root_must_be_lowest_note": True,
            "whole_register_low": "E2",
            "whole_register_high": "C#5",
            "whole_register_low_midi": 40,
            "whole_register_high_midi": 73,
            "lower_foundation_mode": "rooted",
            "lower_foundation_lock_enabled": True,
            "rooted_recipe_weights": {
                "lower_2note_root_3": 1,
                "lower_2note_root_5": 1,
                "lower_2note_root_7": 1,
            },
            "rootless_separate_mode": True,
        },
        "lower_min_note_midi": min(lower_min_notes) if lower_min_notes else None,
        "lower_max_note_midi": max(lower_max_notes) if lower_max_notes else None,
        "rootless_lower_events": rootless_lower_events,
        "root_not_lowest_events": root_not_lowest_events,
        "root_anchor_out_of_window_events": root_anchor_out_of_window_events,
        "whole_register_violations": whole_register_violations,
        "root_anchor_tail_span_guard_failures": root_anchor_tail_span_guard_failures,
        "upper_shell_plus_one_events": upper_shell_plus_one_events,
        "upper_3note_policy": {
            "placement": "closed_upper_stack",
            "hard_floor_removed_in_v2_2_73": True,
            "selection": "groupwise_nearest_plus_whole_voicing_scorer",
        },
        "upper_min_note_midi": min(upper_min_notes) if upper_min_notes else None,
        "upper_min_below_whole_register_events": sum(1 for note in upper_min_notes if note < 36),
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
    audit = _spread_2plus3_audit(debug, expanded_demo=expanded)
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
