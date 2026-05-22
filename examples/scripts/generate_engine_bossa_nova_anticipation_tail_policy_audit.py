from __future__ import annotations

import json
import random
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.anticipation import AnticipationResolver
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.bossa_nova import anticipation_policy, arrangement_policy, comping_patterns
from jammate_engine.styles.registry import get_style

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_93"
MILESTONE_LABEL = "v2_6_93 — Engine Bossa Nova Anticipation Tail Policy + Native 4& Audit"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 22703, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 22753, "slug": "blue_bossa_5x"},
)
CORE_BATIDA_PATTERN = "bossa_piano_core_batida_1_2_3and"
HALF_REGION_PATTERN = "bossa_piano_half_region_1_2"


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    runtime_audits = [_generate_runtime_audit(spec) for spec in DEMO_SPECS]
    acceptance = _acceptance(static_audit, runtime_audits)
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": (
            "Refine the existing Bossa style anticipation policy in place. The shared core AnticipationResolver now supports a style-configurable "
            "minimum previous-region duration, and Bossa requires a full-region tail with beat 4 and 4& empty. Native 4& cells remain current-chord "
            "events that occupy the 4& slot and block anticipation. No parallel anticipation engine, pattern-embedded anticipation, expression numeric change, or core voicing change."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
        "acceptance": acceptance,
        "recommended_next_task": static_audit.get("recommended_next_task"),
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_anticipation_tail_policy_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_anticipation_tail_policy_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()
    anticipation = anticipation_policy.get_anticipation_policy()
    full_library = comping_patterns.describe_pattern_library({"region_duration_beats": 4.0})
    half_library = comping_patterns.describe_pattern_library({"region_duration_beats": 2.0})
    candidates = [*full_library["candidates"], *half_library["candidates"]]
    all_tags = [str(tag) for candidate in candidates for tag in candidate.get("tags", [])]
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "style_registered": getattr(style, "name", None) == "bossa_nova",
        "arrangement_policy_version": policy.get("bossa_nova_anticipation_tail_policy_version"),
        "behavior_change": policy.get("bossa_nova_anticipation_tail_policy_behavior_change"),
        "no_parallel_engine": policy.get("bossa_nova_anticipation_tail_policy_no_parallel_engine"),
        "no_pattern_embedded_anticipation": policy.get("bossa_nova_anticipation_tail_policy_no_pattern_embedded_anticipation"),
        "no_bar_first_restore": policy.get("bossa_nova_anticipation_tail_policy_no_bar_first_restore"),
        "no_core_voicing_change": policy.get("bossa_nova_anticipation_tail_policy_no_core_voicing_change"),
        "no_expression_numeric_change": policy.get("bossa_nova_anticipation_tail_policy_no_expression_numeric_change"),
        "requires_previous_beat4_empty": policy.get("bossa_nova_anticipation_tail_policy_requires_previous_beat4_empty"),
        "requires_previous_4and_empty": policy.get("bossa_nova_anticipation_tail_policy_requires_previous_4and_empty"),
        "preserves_native_4and": policy.get("bossa_nova_anticipation_tail_policy_preserves_native_4and"),
        "anticipation_policy_debug_name": anticipation.debug_name,
        "anticipation_policy_metadata_version": anticipation.metadata.get("bossa_nova_anticipation_tail_policy_version"),
        "anticipation_policy_min_previous_region_duration_beats": anticipation.min_previous_region_duration_beats,
        "anticipation_policy_requires_previous_last_beat_empty": anticipation.require_previous_last_beat_empty,
        "anticipation_policy_requires_previous_last_upbeat_empty": anticipation.require_previous_last_upbeat_empty,
        "pattern_library_version": full_library.get("version"),
        "full_region_candidate_count": full_library.get("candidate_count"),
        "half_region_candidate_count": half_library.get("candidate_count"),
        "legacy_bar_first_tags": sorted({tag for tag in all_tags if tag in {"two_chord_bar", "bar_first", "split_bar"}}),
        "chord_region_first_tags_present": "chord_region_first" in all_tags,
        "native_4and_candidates_marked": _native_4and_candidates_marked(full_library),
        "native_4and_probe": _simulate_probe(previous="bossa_piano_cell_A_1_4and", current="bossa_piano_cell_A_1", previous_duration=4.0),
        "tail_free_probe": _simulate_probe(previous="bossa_piano_cell_A_1_3and", current="bossa_piano_cell_A_1", previous_duration=4.0),
        "short_region_probe": _simulate_probe(previous="bossa_piano_half_region_1_2", current="bossa_piano_cell_A_1", previous_duration=2.0),
        "recommended_next_task": policy.get("bossa_nova_anticipation_tail_policy_recommended_next_task"),
        "known_next_gap": policy.get("bossa_nova_anticipation_tail_policy_known_next_gap"),
    }


def _native_4and_candidates_marked(full_library: dict[str, Any]) -> bool:
    native_candidates = [candidate for candidate in full_library.get("candidates", []) if candidate.get("metadata", {}).get("native_4and")]
    if not native_candidates:
        return False
    for candidate in native_candidates:
        events = candidate.get("events") or []
        native_events = [event for event in events if event.get("metadata", {}).get("native_4and")]
        if not native_events:
            return False
        if not all(event.get("metadata", {}).get("native_4and_is_current_chord_event_not_anticipation") is True for event in native_events):
            return False
    return True


def _region(region_id: str, chord: str, start: float, duration: float) -> HarmonicRegion:
    return HarmonicRegion(
        region_id=region_id,
        chord_symbol=chord,
        next_chord_symbol=None,
        chorus_index=0,
        total_choruses=3,
        bar_index=int(start // 4),
        chord_index=0,
        start_beat=start,
        duration_beats=duration,
        source_bar_index=int(start // 4),
        performance_bar_index=int(start // 4),
    )


def _candidate(name: str, *, duration: float = 4.0):
    pool = comping_patterns.get_pattern_candidates({"region_duration_beats": duration}, apply_context_policy=False)
    for candidate in pool:
        if candidate.name == name:
            return candidate
    raise AssertionError(f"candidate not found: {name}")


def _simulate_probe(*, previous: str, current: str, previous_duration: float) -> dict[str, Any]:
    prev_region = _region("prev", "Cm7", 0.0, previous_duration)
    next_region = _region("next", "F7", previous_duration, 4.0)
    previous_plan = _candidate(previous, duration=previous_duration).instantiate(prev_region)
    current_plan = _candidate(current, duration=4.0).instantiate(next_region)
    policy = replace(anticipation_policy.get_anticipation_policy(), probability=1.0)
    rewritten = AnticipationResolver().resolve(
        list(previous_plan.events) + list(current_plan.events),
        policy,
        random.Random(1),
        regions=(prev_region, next_region),
        region_plans={prev_region.region_id: previous_plan, next_region.region_id: current_plan},
    )
    anticipated = [event for event in rewritten if event.source_event_id == current_plan.events[0].event_id and event.status == "active"]
    return {
        "previous_candidate": previous,
        "current_candidate": current,
        "previous_duration_beats": previous_duration,
        "allowed": bool(anticipated),
        "blocked": not bool(anticipated),
        "anticipated_onsets": [event.onset_beat for event in anticipated],
        "anticipated_local_beats": [event.local_beat for event in anticipated],
        "tail_checked_local_beats": [list(event.metadata.get("anticipation", {}).get("tail_checked_local_beats") or []) for event in anticipated],
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_anticipation_tail_policy_demo.mid"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "bossa_nova",
            "tempo": int(score.get("tempo", 140)),
            "choruses": choruses,
            "seed": seed,
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
        }
    )
    return _summarize_runtime(dict(result.debug), midi_path=midi_path, ok=bool(result.ok), choruses=choruses, seed=seed)


def _summarize_runtime(debug: dict[str, Any], *, midi_path: Path, ok: bool, choruses: int, seed: int) -> dict[str, Any]:
    piano_rows = [row for row in debug.get("piano_musical_audit_events", []) if _pattern_event(row).get("track") == "piano"]
    active_piano = [row for row in piano_rows if _pattern_event(row).get("status") == "active"]
    pattern_counts = Counter(str(_pattern_event(row).get("pattern_id")) for row in active_piano)
    class_a_event_count = sum(count for pattern, count in pattern_counts.items() if "_cell_A_" in pattern)
    class_b_event_count = sum(count for pattern, count in pattern_counts.items() if "_cell_B_" in pattern)
    non_core_event_count = sum(count for pattern, count in pattern_counts.items() if pattern not in {CORE_BATIDA_PATTERN, HALF_REGION_PATTERN})
    native_4and_rows = [row for row in active_piano if bool(_source_metadata(row).get("native_4and"))]
    anticipations = [_anticipation_metadata(row) for row in active_piano if _anticipation_metadata(row).get("kind") == "next_beat1_to_previous_tail"]
    terminal_ending_anticipations = [
        row
        for row in active_piano
        if _anticipation_metadata(row).get("kind") == "next_beat1_to_previous_tail"
        and _source_metadata(row).get("region_chorus_index") == int(_source_metadata(row).get("region_total_choruses", 0) or 0) - 1
        and bool(_source_metadata(row).get("region_is_last_bar_of_chorus"))
    ]
    expression_summary = dict(debug.get("expression_foundation_audit") or {})
    pedal_audit = dict(debug.get("pedal_realization_audit") or {})
    piano_audit = dict(debug.get("piano_musical_audit") or {})
    opening_rows = [
        row
        for row in active_piano
        if int(_source_metadata(row).get("region_chorus_index", -1)) == 0
        and int(_source_metadata(row).get("region_performance_bar_index", 9999)) in {0, 1}
    ]
    opening_patterns = sorted({str(_pattern_event(row).get("pattern_id")) for row in opening_rows})
    return {
        "ok": ok,
        "choruses": choruses,
        "seed": seed,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "title": debug.get("title"),
        "style": debug.get("style"),
        "performance_bars": debug.get("performance_bars"),
        "regions": debug.get("regions"),
        "note_events_by_track": debug.get("note_events_by_track"),
        "piano_active_events": len(active_piano),
        "piano_pattern_counts": dict(pattern_counts),
        "piano_non_core_pattern_event_count": non_core_event_count,
        "piano_class_A_event_count": class_a_event_count,
        "piano_class_B_event_count": class_b_event_count,
        "piano_class_B_ratio_of_non_core_events": round(class_b_event_count / non_core_event_count, 4) if non_core_event_count else 0.0,
        "piano_native_4and_event_count": len(native_4and_rows),
        "native_4and_anticipated_event_count": sum(1 for row in native_4and_rows if _anticipation_metadata(row).get("kind") == "next_beat1_to_previous_tail"),
        "opening_first_two_bars_patterns": opening_patterns,
        "opening_first_two_bars_core_only": bool(opening_rows) and all(pattern in {CORE_BATIDA_PATTERN, HALF_REGION_PATTERN} for pattern in opening_patterns),
        "active_anticipation_count": len(anticipations),
        "terminal_ending_anticipation_count": len(terminal_ending_anticipations),
        "anticipation_timing_grids": sorted({str(item.get("timing_grid")) for item in anticipations}),
        "anticipation_expected_upbeat_fractions": sorted({str(item.get("expected_upbeat_fraction")) for item in anticipations}),
        "anticipation_policy_versions": sorted({str((item.get("style_anticipation_policy_metadata") or {}).get("bossa_nova_anticipation_tail_policy_version")) for item in anticipations}),
        "anticipation_min_previous_region_duration_values": sorted({str(item.get("min_previous_region_duration_beats")) for item in anticipations}),
        "anticipations_from_short_previous_region": sum(1 for item in anticipations if float(item.get("previous_region_duration_beats") or 0.0) < 3.75),
        "anticipation_tail_checked_local_beats": sorted({tuple(item.get("tail_checked_local_beats") or ()) for item in anticipations}),
        "expression_warning_count": expression_summary.get("warning_count"),
        "expression_missing_count": expression_summary.get("missing_expression_count"),
        "expression_cross_region_count": expression_summary.get("cross_region_count"),
        "expression_cross_next_event_count": expression_summary.get("cross_next_event_count"),
        "pedal_cc64_event_count": pedal_audit.get("cc64_event_count"),
        "piano_lower_foundation_low_register_events": piano_audit.get("lower_foundation_low_register_events"),
        "piano_lower_foundation_span_violation_events": piano_audit.get("lower_foundation_span_violation_events"),
    }


def _pattern_event(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("pattern_event") or {}
    return dict(value) if isinstance(value, dict) else {}


def _source_metadata(row: dict[str, Any]) -> dict[str, Any]:
    metadata = _pattern_event(row).get("metadata") or {}
    return dict(metadata) if isinstance(metadata, dict) else {}


def _anticipation_metadata(row: dict[str, Any]) -> dict[str, Any]:
    anticipation = _source_metadata(row).get("anticipation") or {}
    return dict(anticipation) if isinstance(anticipation, dict) else {}


def _acceptance(static_audit: dict[str, Any], runtime_audits: list[dict[str, Any]]) -> dict[str, Any]:
    runtime_ok = bool(runtime_audits) and all(_runtime_accepts(item) for item in runtime_audits)
    checks = {
        "style_and_policy_registered": static_audit.get("style_registered") is True and static_audit.get("arrangement_policy_version") == MILESTONE_ID,
        "in_place_boundaries_preserved": static_audit.get("behavior_change") is True
        and static_audit.get("no_parallel_engine") is True
        and static_audit.get("no_pattern_embedded_anticipation") is True
        and static_audit.get("no_bar_first_restore") is True
        and static_audit.get("no_core_voicing_change") is True
        and static_audit.get("no_expression_numeric_change") is True,
        "tail_policy_declared": static_audit.get("requires_previous_beat4_empty") is True
        and static_audit.get("requires_previous_4and_empty") is True
        and static_audit.get("preserves_native_4and") is True
        and static_audit.get("anticipation_policy_min_previous_region_duration_beats") == 3.75,
        "native_4and_marked_and_blocks_tail": static_audit.get("native_4and_candidates_marked") is True and static_audit.get("native_4and_probe", {}).get("blocked") is True,
        "tail_free_full_region_allows_anticipation": static_audit.get("tail_free_probe", {}).get("allowed") is True,
        "short_region_blocks_bossa_anticipation": static_audit.get("short_region_probe", {}).get("blocked") is True,
        "boundaries_preserved": static_audit.get("legacy_bar_first_tags") == [] and static_audit.get("chord_region_first_tags_present") is True,
        "runtime_blue_bossa_full_band_passes": runtime_ok,
    }
    return {"passed": all(checks.values()), "checks": checks}


def _runtime_accepts(item: dict[str, Any]) -> bool:
    note_counts = dict(item.get("note_events_by_track") or {})
    non_core = int(item.get("piano_non_core_pattern_event_count") or 0)
    class_a = int(item.get("piano_class_A_event_count") or 0)
    class_b = int(item.get("piano_class_B_event_count") or 0)
    return (
        item.get("ok") is True
        and int(note_counts.get("piano", 0)) > 0
        and int(note_counts.get("bass", 0)) > 0
        and int(note_counts.get("drums", 0)) > 0
        and non_core > 0
        and class_a > class_b >= 0
        and float(item.get("piano_class_B_ratio_of_non_core_events") or 0.0) <= 0.22
        and item.get("opening_first_two_bars_core_only") is True
        and int(item.get("active_anticipation_count") or 0) > 0
        and int(item.get("terminal_ending_anticipation_count") or 0) == 0
        and item.get("anticipation_timing_grids") == ["straight_upbeat"]
        and item.get("anticipation_expected_upbeat_fractions") == ["0.5"]
        and item.get("anticipation_policy_versions") == [MILESTONE_ID]
        and item.get("anticipation_min_previous_region_duration_values") == ["3.75"]
        and int(item.get("anticipations_from_short_previous_region") or 0) == 0
        and int(item.get("native_4and_anticipated_event_count") or 0) == 0
        and int(item.get("expression_warning_count") or 0) == 0
        and int(item.get("expression_missing_count") or 0) == 0
        and int(item.get("expression_cross_region_count") or 0) == 0
        and int(item.get("expression_cross_next_event_count") or 0) == 0
        and int(item.get("pedal_cc64_event_count") or 0) == 0
        and int(item.get("piano_lower_foundation_low_register_events") or 0) == 0
        and int(item.get("piano_lower_foundation_span_violation_events") or 0) == 0
    )


def _render_report(summary: dict[str, Any]) -> str:
    static = dict(summary["static_audit"])
    acceptance = dict(summary["acceptance"])
    lines = [
        f"# {MILESTONE_LABEL}",
        "",
        f"Engine version tag: `{summary['contract_version']}`",
        "",
        "## Scope",
        "",
        str(summary["scope"]),
        "",
        "## Static Bossa anticipation audit",
        "",
        f"- Arrangement policy version: `{static.get('arrangement_policy_version')}`",
        f"- Anticipation policy debug name: `{static.get('anticipation_policy_debug_name')}`",
        f"- Min previous region duration: `{static.get('anticipation_policy_min_previous_region_duration_beats')}`",
        f"- Requires previous beat 4 empty: `{static.get('requires_previous_beat4_empty')}`",
        f"- Requires previous 4& empty: `{static.get('requires_previous_4and_empty')}`",
        f"- Native 4& candidates marked: `{static.get('native_4and_candidates_marked')}`",
        f"- Legacy bar-first tags: `{static.get('legacy_bar_first_tags')}`",
        "",
        "## Resolver probes",
        "",
        f"- Native 4& probe: `{static.get('native_4and_probe')}`",
        f"- Tail-free probe: `{static.get('tail_free_probe')}`",
        f"- Short-region probe: `{static.get('short_region_probe')}`",
        "",
        "## Runtime Blue Bossa audits",
        "",
    ]
    for item in summary.get("runtime_audits") or []:
        lines.extend(
            [
                f"### {item.get('choruses')} choruses / seed `{item.get('seed')}`",
                "",
                f"- MIDI: `{item.get('midi_path')}`",
                f"- Notes by track: `{item.get('note_events_by_track')}`",
                f"- Piano pattern counts: `{item.get('piano_pattern_counts')}`",
                f"- Non-core / Class A / Class B event counts: `{item.get('piano_non_core_pattern_event_count')}` / `{item.get('piano_class_A_event_count')}` / `{item.get('piano_class_B_event_count')}`",
                f"- Class B ratio: `{item.get('piano_class_B_ratio_of_non_core_events')}`",
                f"- Native 4& events / native anticipated events: `{item.get('piano_native_4and_event_count')}` / `{item.get('native_4and_anticipated_event_count')}`",
                f"- Active anticipations: `{item.get('active_anticipation_count')}`",
                f"- Anticipations from short previous regions: `{item.get('anticipations_from_short_previous_region')}`",
                f"- Anticipation policy versions: `{item.get('anticipation_policy_versions')}`",
                f"- Anticipation min previous duration values: `{item.get('anticipation_min_previous_region_duration_values')}`",
                f"- Tail checked local beats: `{item.get('anticipation_tail_checked_local_beats')}`",
                f"- Terminal-ending anticipations: `{item.get('terminal_ending_anticipation_count')}`",
                f"- Expression warnings / missing / cross-region / cross-next-event: `{item.get('expression_warning_count')}` / `{item.get('expression_missing_count')}` / `{item.get('expression_cross_region_count')}` / `{item.get('expression_cross_next_event_count')}`",
                f"- Pedal CC64 events: `{item.get('pedal_cc64_event_count')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Known next gap",
            "",
            str(static.get("known_next_gap")),
            "",
            f"Recommended next task: `{summary.get('recommended_next_task')}`",
            "",
            "## Acceptance",
            "",
            f"Passed: `{acceptance.get('passed')}`",
            "",
        ]
    )
    for name, ok in dict(acceptance.get("checks") or {}).items():
        lines.append(f"- `{name}`: `{ok}`")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
