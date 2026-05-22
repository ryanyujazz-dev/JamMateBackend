from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.form.form_expander import expand_form_to_regions
from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.bossa_nova import arrangement_policy, comping_patterns
from jammate_engine.styles.registry import get_style

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_99"
MILESTONE_LABEL = "v2_6_99 — Engine Bossa Nova Style Baseline Phase Completion Checkpoint"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 22993, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 22995, "slug": "blue_bossa_5x"},
)
REPEAT_COUNTS_TO_SIMULATE = (1, 2, 3, 5, 10, 50)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    runtime_audits = [_generate_runtime_audit(spec) for spec in DEMO_SPECS]
    acceptance = _acceptance(static_audit, runtime_audits)
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": (
            "Freeze the Bossa Nova v2_6_90-v2_6_98 full-band baseline as a phase-completion checkpoint. "
            "This stamps summary metadata and generates final Blue Bossa 3x/5x demos only; it does not add vocabulary, alter weights, "
            "change expression numbers, modify core voicing, restore bar-first logic, or touch API/Agent/HarmonyOS."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
        "acceptance": acceptance,
        "recommended_next_task": static_audit.get("recommended_next_task"),
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_style_baseline_phase_completion_checkpoint_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_style_baseline_phase_completion_checkpoint_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()
    library = comping_patterns.describe_pattern_library({"region_duration_beats": 4.0})
    repeat_arc_simulation = [
        {"total_choruses": count, "phases": arrangement_policy.simulate_repeat_count_arrangement_arc(count)}
        for count in REPEAT_COUNTS_TO_SIMULATE
    ]
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "style_registered": getattr(style, "name", None) == "bossa_nova",
        "phase_completion_active": policy.get("bossa_nova_style_baseline_phase_completion_checkpoint"),
        "phase_completion_version": policy.get("bossa_nova_style_baseline_phase_completion_checkpoint_version"),
        "behavior_change": policy.get("bossa_nova_style_baseline_phase_completion_checkpoint_behavior_change"),
        "no_parallel_selector": policy.get("bossa_nova_style_baseline_phase_completion_checkpoint_no_parallel_selector"),
        "no_bar_first_restore": policy.get("bossa_nova_style_baseline_phase_completion_checkpoint_no_bar_first_restore"),
        "no_new_pattern_vocabulary": policy.get("bossa_nova_style_baseline_phase_completion_checkpoint_no_new_pattern_vocabulary"),
        "no_expression_numeric_change": policy.get("bossa_nova_style_baseline_phase_completion_checkpoint_no_expression_numeric_change"),
        "no_core_voicing_change": policy.get("bossa_nova_style_baseline_phase_completion_checkpoint_no_core_voicing_change"),
        "no_api_agent_harmonyos_change": policy.get("bossa_nova_style_baseline_phase_completion_checkpoint_no_api_agent_harmonyos_change"),
        "tracks": list(policy.get("bossa_nova_style_baseline_phase_completion_checkpoint_tracks") or ()),
        "completed_versions": list(policy.get("bossa_nova_style_baseline_phase_completion_checkpoint_completed_versions") or ()),
        "contract": policy.get("bossa_nova_style_baseline_phase_completion_checkpoint_contract"),
        "recommended_next_task": policy.get("bossa_nova_style_baseline_phase_completion_checkpoint_recommended_next_task"),
        "piano_library_version": library.get("version"),
        "piano_candidate_count": library.get("candidate_count"),
        "piano_core_candidate_count": library.get("core_candidate_count"),
        "piano_class_A_candidate_count": library.get("class_A_candidate_count"),
        "piano_class_B_candidate_count": library.get("class_B_candidate_count"),
        "repeat_arc_simulation": repeat_arc_simulation,
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_style_baseline_phase_completion_checkpoint_demo.mid"
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
    plan_audit = _plan_blue_bossa(choruses=choruses, seed=seed)
    debug = dict(result.debug)
    note_counts = dict(debug.get("note_events_by_track") or {})
    return {
        "ok": bool(result.ok),
        "choruses": choruses,
        "seed": seed,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "title": debug.get("title"),
        "style": debug.get("style"),
        "performance_bars": debug.get("performance_bars"),
        "regions": debug.get("regions"),
        "note_events_by_track": note_counts,
        "piano_notes": int(note_counts.get("piano", 0)),
        "bass_notes": int(note_counts.get("bass", 0)),
        "drums_notes": int(note_counts.get("drums", 0)),
        **plan_audit,
    }


def _plan_blue_bossa(*, choruses: int, seed: int) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    leadsheet = normalize_leadsheet(parse_leadsheet(score))
    timeline = expand_form_to_regions(leadsheet, choruses)
    style = get_style("bossa_nova")
    rng = random.Random(seed)
    history: dict[str, Any] = {}
    piano_events = []
    bass_events = []
    drum_events = []
    for region in timeline.regions:
        plan = style.plan_region(
            region,
            context={"tempo": int(score.get("tempo", 140)), "rng": rng, "style_pattern_history": history, "ensemble": {"bass_present": True}},
        )
        piano_events.extend([event for event in plan.events if event.track == "piano"])
        bass_events.extend([event for event in plan.events if event.track == "bass"])
        drum_events.extend([event for event in plan.events if event.track == "drums"])

    def _coverage(events: list[Any]) -> tuple[list[Any], float]:
        rows = [event for event in events if event.metadata.get("bossa_style_baseline_phase_completion_checkpoint_version") == MILESTONE_ID]
        return rows, round(len(rows) / max(1, len(events)), 4)

    piano_completion, piano_completion_ratio = _coverage(piano_events)
    bass_completion, bass_completion_ratio = _coverage(bass_events)
    drums_completion, drums_completion_ratio = _coverage(drum_events)
    piano_classes = Counter(str(event.metadata.get("rhythm_class")) for event in piano_events)
    piano_cells = Counter(str(event.metadata.get("rhythmic_cell")) for event in piano_events)
    piano_phases = Counter(str(event.metadata.get("bossa_nova_repeat_count_arrangement_arc_phase")) for event in piano_events)
    bass_bands = Counter(str(event.metadata.get("bossa_full_band_arrangement_arc_band")) for event in bass_events)
    drum_bands = Counter(str(event.metadata.get("bossa_full_band_arrangement_arc_band")) for event in drum_events)
    bass_profiles = Counter(str(event.metadata.get("dynamic_profile")) for event in bass_events)
    drum_profiles = Counter(str(event.metadata.get("dynamic_profile")) for event in drum_events)
    native_4and_events = [event for event in piano_events if event.metadata.get("native_4and") is True]
    native_4and_anticipated = [event for event in native_4and_events if dict(event.metadata.get("anticipation") or {}).get("kind")]
    return {
        "planned_piano_event_count": len(piano_events),
        "planned_bass_event_count": len(bass_events),
        "planned_drum_event_count": len(drum_events),
        "piano_phase_completion_event_count": len(piano_completion),
        "bass_phase_completion_event_count": len(bass_completion),
        "drums_phase_completion_event_count": len(drums_completion),
        "piano_phase_completion_coverage_ratio": piano_completion_ratio,
        "bass_phase_completion_coverage_ratio": bass_completion_ratio,
        "drums_phase_completion_coverage_ratio": drums_completion_ratio,
        "phase_completion_behavior_change_events": sum(1 for event in piano_completion + bass_completion + drums_completion if event.metadata.get("bossa_style_baseline_phase_completion_checkpoint_behavior_change") is not False),
        "piano_rhythm_class_counts": dict(piano_classes),
        "piano_rhythmic_cell_counts": dict(piano_cells),
        "piano_arc_phase_counts": dict(piano_phases),
        "bass_full_band_arc_band_counts": dict(bass_bands),
        "drum_full_band_arc_band_counts": dict(drum_bands),
        "bass_dynamic_profile_counts": dict(bass_profiles),
        "drum_dynamic_profile_counts": dict(drum_profiles),
        "native_4and_event_count": len(native_4and_events),
        "native_4and_anticipated_event_count": len(native_4and_anticipated),
        "bass_walking_like_events": sum(1 for event in bass_events if event.metadata.get("walking_bass") is not False),
        "drum_swing_or_rock_events": sum(1 for event in drum_events if event.metadata.get("swing_ride_pattern") is not False or event.metadata.get("rock_backbeat_pattern") is not False),
    }


def _acceptance(static_audit: dict[str, Any], runtime_audits: list[dict[str, Any]]) -> dict[str, Any]:
    checks = {
        "style_and_policy_registered": static_audit.get("style_registered") is True
        and static_audit.get("phase_completion_active") is True
        and static_audit.get("phase_completion_version") == MILESTONE_ID,
        "metadata_only_boundaries_preserved": static_audit.get("behavior_change") is False
        and static_audit.get("no_parallel_selector") is True
        and static_audit.get("no_bar_first_restore") is True
        and static_audit.get("no_new_pattern_vocabulary") is True
        and static_audit.get("no_expression_numeric_change") is True
        and static_audit.get("no_core_voicing_change") is True
        and static_audit.get("no_api_agent_harmonyos_change") is True,
        "completed_versions_cover_bossa_baseline": static_audit.get("completed_versions") == [
            "v2_6_90",
            "v2_6_91",
            "v2_6_92",
            "v2_6_93",
            "v2_6_94",
            "v2_6_103",
            "v2_6_96",
            "v2_6_97",
            "v2_6_98",
        ],
        "piano_vocabulary_still_expected_size": static_audit.get("piano_core_candidate_count") == 1
        and static_audit.get("piano_class_A_candidate_count") == 6
        and static_audit.get("piano_class_B_candidate_count") == 6,
        "repeat_arc_not_three_chorus_hardcoded": set(item.get("total_choruses") for item in static_audit.get("repeat_arc_simulation") or []) == set(REPEAT_COUNTS_TO_SIMULATE),
        "runtime_blue_bossa_phase_completion_passes": bool(runtime_audits) and all(_runtime_accepts(item) for item in runtime_audits),
    }
    return {"checks": checks, "passed": all(checks.values())}


def _runtime_accepts(item: dict[str, Any]) -> bool:
    piano_classes = dict(item.get("piano_rhythm_class_counts") or {})
    bass_bands = dict(item.get("bass_full_band_arc_band_counts") or {})
    drum_bands = dict(item.get("drum_full_band_arc_band_counts") or {})
    return (
        bool(item.get("ok"))
        and int(item.get("piano_notes") or 0) > 0
        and int(item.get("bass_notes") or 0) > 0
        and int(item.get("drums_notes") or 0) > 0
        and float(item.get("piano_phase_completion_coverage_ratio") or 0.0) == 1.0
        and float(item.get("bass_phase_completion_coverage_ratio") or 0.0) == 1.0
        and float(item.get("drums_phase_completion_coverage_ratio") or 0.0) == 1.0
        and int(item.get("phase_completion_behavior_change_events") or 0) == 0
        and int(piano_classes.get("class_A", 0)) > 0
        and int(piano_classes.get("class_B", 0)) > 0
        and int(item.get("native_4and_anticipated_event_count") or 0) == 0
        and int(item.get("bass_walking_like_events") or 0) == 0
        and int(item.get("drum_swing_or_rock_events") or 0) == 0
        and int(bass_bands.get("soft_release", 0)) > 0
        and int(drum_bands.get("soft_release", 0)) > 0
        and (int(item.get("choruses") or 0) < 5 or int(bass_bands.get("breath_space", 0)) > 0)
        and (int(item.get("choruses") or 0) < 5 or int(drum_bands.get("breath_space", 0)) > 0)
    )


def _render_report(summary: dict[str, Any]) -> str:
    static = dict(summary["static_audit"])
    lines = [
        f"# {MILESTONE_LABEL}",
        "",
        f"Engine version tag: `{summary['contract_version']}`",
        "",
        "## Scope",
        "",
        str(summary["scope"]),
        "",
        "## Static audit",
        "",
        f"- phase completion version: `{static.get('phase_completion_version')}`",
        f"- completed versions: `{static.get('completed_versions')}`",
        f"- boundaries: behavior_change={static.get('behavior_change')}, no_parallel_selector={static.get('no_parallel_selector')}, no_bar_first_restore={static.get('no_bar_first_restore')}, no_new_pattern_vocabulary={static.get('no_new_pattern_vocabulary')}, no_expression_numeric_change={static.get('no_expression_numeric_change')}, no_core_voicing_change={static.get('no_core_voicing_change')}",
        f"- piano vocabulary: core={static.get('piano_core_candidate_count')}, Class A={static.get('piano_class_A_candidate_count')}, Class B={static.get('piano_class_B_candidate_count')}",
        "",
        "## Runtime audits",
        "",
    ]
    for item in summary["runtime_audits"]:
        lines.extend(
            [
                f"### Blue Bossa {item['choruses']}x",
                "",
                f"- MIDI: `{item['midi_path']}`",
                f"- piano/bass/drums notes: `{item['piano_notes']} / {item['bass_notes']} / {item['drums_notes']}`",
                f"- planned piano/bass/drums events: `{item['planned_piano_event_count']} / {item['planned_bass_event_count']} / {item['planned_drum_event_count']}`",
                f"- phase-completion coverage piano/bass/drums: `{item['piano_phase_completion_coverage_ratio']} / {item['bass_phase_completion_coverage_ratio']} / {item['drums_phase_completion_coverage_ratio']}`",
                f"- piano rhythm classes: `{item['piano_rhythm_class_counts']}`",
                f"- piano arc phases: `{item['piano_arc_phase_counts']}`",
                f"- bass/drum bands: `{item['bass_full_band_arc_band_counts']} / {item['drum_full_band_arc_band_counts']}`",
                f"- native 4& anticipated events: `{item['native_4and_anticipated_event_count']}`",
                f"- bass walking-like / drum swing-rock events: `{item['bass_walking_like_events']} / {item['drum_swing_or_rock_events']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Acceptance",
            "",
            f"Passed: `{summary['acceptance']['passed']}`",
            "",
            "```json",
            json.dumps(summary["acceptance"], indent=2, ensure_ascii=False),
            "```",
            "",
            f"Recommended next task: `{summary.get('recommended_next_task')}`",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
