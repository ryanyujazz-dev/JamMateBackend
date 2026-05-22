from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.bossa_nova import arrangement_policy, comping_patterns
from jammate_engine.styles.registry import get_style

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_92"
MILESTONE_LABEL = "v2_6_92 — Engine Bossa Nova Context Archetype Policy + History Scorer Refinement"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 22702, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 22752, "slug": "blue_bossa_5x"},
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
            "Overwrite the previous simple v2_6_91 Bossa weighting in place with context archetype multipliers "
            "and rolling history metadata inside the existing ChordRegion-first comping pattern path. No new selector, "
            "no new rhythm vocabulary, no bar-first route, no expression numeric change, and no core voicing change."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
        "acceptance": acceptance,
        "recommended_next_task": static_audit.get("recommended_next_task"),
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_context_archetype_policy_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_context_archetype_policy_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()
    full_library = comping_patterns.describe_pattern_library({"region_duration_beats": 4.0})
    half_library = comping_patterns.describe_pattern_library({"region_duration_beats": 2.0})
    full_candidates = [dict(candidate) for candidate in full_library["candidates"]]
    all_candidates = [*full_candidates, *[dict(candidate) for candidate in half_library["candidates"]]]
    all_tags = [str(tag) for candidate in all_candidates for tag in candidate.get("tags", [])]
    legacy_tags = sorted({tag for tag in all_tags if tag in {"two_chord_bar", "bar_first", "split_bar"}})
    context_probes = _build_context_probes()
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "style_registered": getattr(style, "name", None) == "bossa_nova",
        "arrangement_policy_version": policy.get("bossa_nova_context_archetype_policy_version"),
        "behavior_change": policy.get("bossa_nova_context_archetype_policy_behavior_change"),
        "replaces_simple_v2_6_91_weighting": policy.get("bossa_nova_context_archetype_policy_replaces_simple_v2_6_91_weighting"),
        "no_parallel_selector": policy.get("bossa_nova_context_archetype_policy_no_parallel_selector"),
        "no_bar_first_restore": policy.get("bossa_nova_context_archetype_policy_no_bar_first_restore"),
        "no_new_pattern_vocabulary": policy.get("bossa_nova_context_archetype_policy_no_new_pattern_vocabulary"),
        "no_core_voicing_change": policy.get("bossa_nova_context_archetype_policy_no_core_voicing_change"),
        "no_expression_numeric_change": policy.get("bossa_nova_context_archetype_policy_no_expression_numeric_change"),
        "archetypes": list(policy.get("bossa_nova_context_archetype_policy_archetypes") or ()),
        "pattern_library_version": full_library.get("version"),
        "full_region_candidate_count": full_library.get("candidate_count"),
        "half_region_candidate_count": half_library.get("candidate_count"),
        "class_A_candidate_count": full_library.get("class_A_candidate_count"),
        "class_B_candidate_count": full_library.get("class_B_candidate_count"),
        "core_candidate_count": full_library.get("core_candidate_count"),
        "legacy_bar_first_tags": legacy_tags,
        "chord_region_first_tags_present": "chord_region_first" in all_tags,
        "context_probes": context_probes,
        "recommended_next_task": policy.get("bossa_nova_context_archetype_policy_recommended_next_task"),
        "known_next_gap": policy.get("bossa_nova_context_archetype_policy_known_next_gap"),
    }


def _region(**overrides: Any) -> SimpleNamespace:
    data = {
        "chorus_index": 0,
        "total_choruses": 3,
        "performance_bar_index": 4,
        "source_bar_index": 4,
        "duration_beats": 4.0,
        "is_first_bar_of_section": False,
        "is_first_bar_of_chorus": False,
        "is_last_bar_of_section": False,
        "is_last_bar_of_chorus": False,
        "section_role": "normal",
        "phrase": "A",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _build_context_probes() -> dict[str, dict[str, Any]]:
    scenarios = {
        "opening": _region(chorus_index=0, performance_bar_index=0, source_bar_index=0, is_first_bar_of_section=True, is_first_bar_of_chorus=True),
        "steady": _region(performance_bar_index=4, source_bar_index=4),
        "bridge_breath": _region(performance_bar_index=10, source_bar_index=2, section_role="bridge", phrase="B"),
        "transition_lift": _region(performance_bar_index=7, source_bar_index=7, is_last_bar_of_section=True),
        "release": _region(chorus_index=2, total_choruses=3, performance_bar_index=47, source_bar_index=15, is_last_bar_of_chorus=True, is_last_bar_of_section=True),
        "short_region": _region(performance_bar_index=15, source_bar_index=15, duration_beats=2.0),
        "recent_class_B_guard": _region(performance_bar_index=6, source_bar_index=6),
    }
    history = {
        "bossa_nova:0:jammate_engine.styles.bossa_nova.comping_patterns.get_pattern_candidates": "bossa_piano_cell_B_1and_3",
        "bossa_nova:0:jammate_engine.styles.bossa_nova.comping_patterns.get_pattern_candidates:category": "bossa_cell_B",
        "bossa_nova:0:jammate_engine.styles.bossa_nova.comping_patterns.get_pattern_candidates:recent_bossa_comping": [
            {"name": "bossa_piano_cell_B_1and_3", "category": "bossa_cell_B", "rhythm_class": "class_B", "hit_count": 2, "native_4and": False},
            {"name": "bossa_piano_cell_A_1_2_3and", "category": "bossa_cell_A", "rhythm_class": "class_A", "hit_count": 3, "native_4and": False},
            {"name": "bossa_piano_cell_B_1and", "category": "bossa_cell_B", "rhythm_class": "class_B", "hit_count": 1, "native_4and": False},
        ],
    }
    probes: dict[str, dict[str, Any]] = {}
    for name, region in scenarios.items():
        context = {"region": region, "region_duration_beats": float(region.duration_beats)}
        if name == "recent_class_B_guard":
            context["style_pattern_history"] = history
        candidates = comping_patterns.get_pattern_candidates(context)
        archetypes = sorted({str(candidate.metadata.get("bossa_context_archetype")) for candidate in candidates})
        class_b_multipliers = [float(candidate.metadata.get("bossa_context_weighting_multiplier") or 0.0) for candidate in candidates if candidate.metadata.get("rhythm_class") == "class_B"]
        probes[name] = {
            "candidate_count": len(candidates),
            "candidate_names": [candidate.name for candidate in candidates],
            "archetypes": archetypes,
            "min_class_B_multiplier": min(class_b_multipliers) if class_b_multipliers else None,
            "max_class_B_multiplier": max(class_b_multipliers) if class_b_multipliers else None,
            "has_core": any(candidate.name == CORE_BATIDA_PATTERN for candidate in candidates),
            "has_only_core": len(candidates) == 1 and candidates[0].name == CORE_BATIDA_PATTERN,
        }
    return probes


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_context_archetype_policy_demo.mid"
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
    debug = dict(result.debug)
    return _summarize_runtime(debug, midi_path=midi_path, ok=bool(result.ok), choruses=choruses, seed=seed)


def _summarize_runtime(debug: dict[str, Any], *, midi_path: Path, ok: bool, choruses: int, seed: int) -> dict[str, Any]:
    piano_rows = [row for row in debug.get("piano_musical_audit_events", []) if _pattern_event(row).get("track") == "piano"]
    active_piano = [row for row in piano_rows if _pattern_event(row).get("status") == "active"]
    pattern_counts = Counter(str(_pattern_event(row).get("pattern_id")) for row in active_piano)
    archetype_counts = Counter(str(_source_metadata(row).get("bossa_context_archetype")) for row in active_piano if _source_metadata(row).get("bossa_context_archetype"))
    weighting_status_counts = Counter(str(_source_metadata(row).get("bossa_context_weighting_status")) for row in active_piano if _source_metadata(row).get("bossa_context_weighting_status"))
    class_a_event_count = sum(count for pattern, count in pattern_counts.items() if "_cell_A_" in pattern)
    class_b_event_count = sum(count for pattern, count in pattern_counts.items() if "_cell_B_" in pattern)
    native_4and_event_count = sum(count for pattern, count in pattern_counts.items() if "4and" in pattern)
    non_core_event_count = sum(count for pattern, count in pattern_counts.items() if pattern not in {CORE_BATIDA_PATTERN, HALF_REGION_PATTERN})
    expression_summary = dict(debug.get("expression_foundation_audit") or {})
    pedal_audit = dict(debug.get("pedal_realization_audit") or {})
    piano_audit = dict(debug.get("piano_musical_audit") or {})
    anticipations = [_anticipation_metadata(row) for row in active_piano if _anticipation_metadata(row).get("kind") == "next_beat1_to_previous_tail"]
    terminal_ending_anticipations = [
        row
        for row in active_piano
        if _anticipation_metadata(row).get("kind") == "next_beat1_to_previous_tail"
        and _source_metadata(row).get("region_chorus_index") == int(_source_metadata(row).get("region_total_choruses", 0) or 0) - 1
        and bool(_source_metadata(row).get("region_is_last_bar_of_chorus"))
    ]
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
        "piano_archetype_counts": dict(archetype_counts),
        "piano_weighting_status_counts": dict(weighting_status_counts),
        "piano_non_core_pattern_event_count": non_core_event_count,
        "piano_class_A_event_count": class_a_event_count,
        "piano_class_B_event_count": class_b_event_count,
        "piano_native_4and_event_count": native_4and_event_count,
        "piano_class_B_ratio_of_non_core_events": round(class_b_event_count / non_core_event_count, 4) if non_core_event_count else 0.0,
        "opening_first_two_bars_patterns": opening_patterns,
        "opening_first_two_bars_core_only": bool(opening_rows) and all(pattern in {CORE_BATIDA_PATTERN, HALF_REGION_PATTERN} for pattern in opening_patterns),
        "active_anticipation_count": len(anticipations),
        "terminal_ending_anticipation_count": len(terminal_ending_anticipations),
        "anticipation_timing_grids": sorted({str(item.get("timing_grid")) for item in anticipations}),
        "anticipation_expected_upbeat_fractions": sorted({str(item.get("expected_upbeat_fraction")) for item in anticipations}),
        "expression_warning_count": expression_summary.get("warning_count"),
        "expression_missing_count": expression_summary.get("missing_expression_count"),
        "expression_cross_region_count": expression_summary.get("cross_region_count"),
        "expression_cross_next_event_count": expression_summary.get("cross_next_event_count"),
        "pedal_cc64_event_count": pedal_audit.get("cc64_event_count"),
        "piano_content_families": piano_audit.get("content_families"),
        "piano_densities": piano_audit.get("densities"),
        "piano_dispositions": piano_audit.get("dispositions"),
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
    probes = dict(static_audit.get("context_probes") or {})
    runtime_ok = bool(runtime_audits) and all(_runtime_accepts(item) for item in runtime_audits)
    checks = {
        "style_and_policy_registered": static_audit.get("style_registered") is True and static_audit.get("arrangement_policy_version") == MILESTONE_ID,
        "in_place_replacement_boundaries": static_audit.get("behavior_change") is True
        and static_audit.get("replaces_simple_v2_6_91_weighting") is True
        and static_audit.get("no_parallel_selector") is True
        and static_audit.get("no_bar_first_restore") is True
        and static_audit.get("no_new_pattern_vocabulary") is True
        and static_audit.get("no_core_voicing_change") is True
        and static_audit.get("no_expression_numeric_change") is True,
        "same_vocabulary_preserved": static_audit.get("pattern_library_version") == MILESTONE_ID
        and static_audit.get("full_region_candidate_count") == 13
        and static_audit.get("half_region_candidate_count") == 1
        and static_audit.get("class_A_candidate_count") == 6
        and static_audit.get("class_B_candidate_count") == 6
        and static_audit.get("core_candidate_count") == 1,
        "archetype_context_probes_work": probes.get("opening", {}).get("has_only_core") is True
        and probes.get("steady", {}).get("archetypes") == ["steady_batida_flow"]
        and probes.get("bridge_breath", {}).get("archetypes") == ["breath_space"]
        and probes.get("transition_lift", {}).get("archetypes") == ["transition_lift"]
        and probes.get("release", {}).get("archetypes") == ["release"]
        and probes.get("short_region", {}).get("archetypes") == ["dense_harmonic_marks"],
        "history_guard_probe_downweights_class_B": (probes.get("recent_class_B_guard", {}).get("max_class_B_multiplier") or 1.0) < 0.2,
        "boundaries_preserved": static_audit.get("legacy_bar_first_tags") == [] and static_audit.get("chord_region_first_tags_present") is True,
        "runtime_blue_bossa_full_band_passes": runtime_ok,
    }
    return {"passed": all(checks.values()), "checks": checks}


def _runtime_accepts(item: dict[str, Any]) -> bool:
    note_counts = dict(item.get("note_events_by_track") or {})
    non_core = int(item.get("piano_non_core_pattern_event_count") or 0)
    class_a = int(item.get("piano_class_A_event_count") or 0)
    class_b = int(item.get("piano_class_B_event_count") or 0)
    archetype_counts = dict(item.get("piano_archetype_counts") or {})
    return (
        item.get("ok") is True
        and int(note_counts.get("piano", 0)) > 0
        and int(note_counts.get("bass", 0)) > 0
        and int(note_counts.get("drums", 0)) > 0
        and non_core > 0
        and class_a > class_b >= 0
        and float(item.get("piano_class_B_ratio_of_non_core_events") or 0.0) <= 0.22
        and item.get("opening_first_two_bars_core_only") is True
        and len(archetype_counts) >= 4
        and "core_batida_anchor" in archetype_counts
        and "steady_batida_flow" in archetype_counts
        and int(item.get("active_anticipation_count") or 0) > 0
        and int(item.get("terminal_ending_anticipation_count") or 0) == 0
        and item.get("anticipation_timing_grids") == ["straight_upbeat"]
        and item.get("anticipation_expected_upbeat_fractions") == ["0.5"]
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
        "## Static Bossa policy audit",
        "",
        f"- Arrangement policy version: `{static.get('arrangement_policy_version')}`",
        f"- Candidate count: `{static.get('full_region_candidate_count')}` full-region / `{static.get('half_region_candidate_count')}` half-region",
        f"- Class A / Class B / Core counts: `{static.get('class_A_candidate_count')}` / `{static.get('class_B_candidate_count')}` / `{static.get('core_candidate_count')}`",
        f"- Archetypes: `{static.get('archetypes')}`",
        f"- Legacy bar-first tags: `{static.get('legacy_bar_first_tags')}`",
        "",
        "## Context probes",
        "",
    ]
    for name, item in dict(static.get("context_probes") or {}).items():
        lines.append(f"- `{name}`: archetypes=`{item.get('archetypes')}`, candidate_count=`{item.get('candidate_count')}`, has_only_core=`{item.get('has_only_core')}`, max_class_B_multiplier=`{item.get('max_class_B_multiplier')}`")
    lines.extend(["", "## Runtime Blue Bossa audits", ""])
    for item in summary.get("runtime_audits") or []:
        lines.extend(
            [
                f"### {item.get('choruses')} choruses / seed `{item.get('seed')}`",
                "",
                f"- MIDI: `{item.get('midi_path')}`",
                f"- Notes by track: `{item.get('note_events_by_track')}`",
                f"- Piano pattern counts: `{item.get('piano_pattern_counts')}`",
                f"- Piano archetype counts: `{item.get('piano_archetype_counts')}`",
                f"- Weighting status counts: `{item.get('piano_weighting_status_counts')}`",
                f"- Non-core / Class A / Class B event counts: `{item.get('piano_non_core_pattern_event_count')}` / `{item.get('piano_class_A_event_count')}` / `{item.get('piano_class_B_event_count')}`",
                f"- Class B ratio: `{item.get('piano_class_B_ratio_of_non_core_events')}`",
                f"- Opening first two bars patterns: `{item.get('opening_first_two_bars_patterns')}`",
                f"- Active anticipations: `{item.get('active_anticipation_count')}`",
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
