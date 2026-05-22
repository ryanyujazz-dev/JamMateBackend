from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
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
from jammate_engine.realization.percussion_realizer import PercussionRealizer
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.bossa_nova import arrangement_policy, percussion_patterns
from jammate_engine.styles.registry import get_style

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_101"
MILESTONE_LABEL = "v2_6_101 — Engine Bossa Nova Cross-stick Phrase-local Contour Refinement"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 23101, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 23106, "slug": "blue_bossa_5x"},
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    runtime_audits = [_generate_runtime_audit(spec) for spec in DEMO_SPECS]
    acceptance = _acceptance(static_audit, runtime_audits)
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": (
            "Refine the existing Bossa cross-stick layer in place. The same shaker/cross-stick/light-kick percussion candidate remains active, "
            "but cross-stick events now carry phrase-local A/B slots and arc-aware contour-density metadata. The shared percussion realizer maps those semantic slots to small velocity-shape offsets. "
            "No piano, bass, core voicing, API, Agent, HarmonyOS, or parallel percussion selector change."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
        "acceptance": acceptance,
        "recommended_next_task": static_audit.get("recommended_next_task"),
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_cross_stick_phrase_local_contour_refinement_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_cross_stick_phrase_local_contour_refinement_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()
    full_a = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "region_source_bar_index": 0})[0]
    full_b = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "region_source_bar_index": 1})[0]
    breath_a = percussion_patterns.get_pattern_candidates(
        {
            "region_duration_beats": 4.0,
            "region_source_bar_index": 2,
            "bossa_nova_arrangement_arc_intent": {"phase": "loop_wave_breath_space", "piano_comping_runtime_intent": "breath_space"},
        }
    )[0]
    release_a = percussion_patterns.get_pattern_candidates(
        {
            "region_duration_beats": 4.0,
            "region_source_bar_index": 0,
            "bossa_nova_arrangement_arc_intent": {"phase": "final_soft_release", "piano_comping_runtime_intent": "settled_release"},
        }
    )[0]
    release_b = percussion_patterns.get_pattern_candidates(
        {
            "region_duration_beats": 4.0,
            "region_source_bar_index": 1,
            "bossa_nova_arrangement_arc_intent": {"phase": "final_soft_release", "piano_comping_runtime_intent": "settled_release"},
        }
    )[0]
    split = percussion_patterns.get_pattern_candidates({"region_duration_beats": 2.0, "region_source_bar_index": 1})[0]
    all_cross = [_cross_events(item) for item in (full_a, full_b, breath_a, release_a, release_b, split)]
    flat_cross = [event for events in all_cross for event in events]
    forbidden_numeric_keys = sorted(
        {
            key
            for event in flat_cross
            for key in event.metadata
            if key in {"velocity", "duration", "duration_beats", "pedal", "midi_note", "note"}
        }
    )
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "style_registered": getattr(style, "name", None) == "bossa_nova",
        "policy_active": policy.get("bossa_nova_drum_cross_stick_phrase_local_contour_active"),
        "policy_version": policy.get("bossa_nova_drum_cross_stick_phrase_local_contour_version"),
        "no_parallel_selector": policy.get("bossa_nova_drum_cross_stick_phrase_local_contour_no_parallel_selector"),
        "no_bar_first_restore": policy.get("bossa_nova_drum_cross_stick_phrase_local_contour_no_bar_first_restore"),
        "no_new_pattern_vocabulary": policy.get("bossa_nova_drum_cross_stick_phrase_local_contour_no_new_pattern_vocabulary"),
        "no_piano_bass_voicing_change": policy.get("bossa_nova_drum_cross_stick_phrase_local_contour_no_piano_bass_voicing_change"),
        "no_api_agent_harmonyos_change": policy.get("bossa_nova_drum_cross_stick_phrase_local_contour_no_api_agent_harmonyos_change"),
        "tracks": list(policy.get("bossa_nova_drum_cross_stick_phrase_local_contour_tracks") or ()),
        "full_A_cross_slots": _cross_slots(full_a),
        "full_B_cross_slots": _cross_slots(full_b),
        "breath_A_cross_slots": _cross_slots(breath_a),
        "release_A_cross_slots": _cross_slots(release_a),
        "release_B_cross_slots": _cross_slots(release_b),
        "split_cross_slots": _cross_slots(split),
        "full_A_cross_beats": _cross_beats(full_a),
        "full_B_cross_beats": _cross_beats(full_b),
        "cross_contour_versions": sorted({str(event.metadata.get("bossa_drum_cross_stick_phrase_local_contour_version")) for event in flat_cross}),
        "cross_contour_density_values": sorted({str(event.metadata.get("cross_stick_contour_density")) for event in flat_cross}),
        "forbidden_pattern_numeric_keys": forbidden_numeric_keys,
        "recommended_next_task": policy.get("bossa_nova_drum_cross_stick_phrase_local_contour_recommended_next_task"),
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_cross_stick_phrase_local_contour_refinement_demo.mid"
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
    drum_events = []
    for region in timeline.regions:
        plan = style.plan_region(
            region,
            context={"tempo": int(score.get("tempo", 140)), "rng": rng, "style_pattern_history": history, "ensemble": {"bass_present": True}},
        )
        drum_events.extend([event for event in plan.events if event.track == "drums"])

    realized = PercussionRealizer().realize(drum_events)
    cross_events = [event for event in drum_events if event.metadata.get("drum") == "cross_stick"]
    cross_notes = [note for event, note in zip(drum_events, realized) if event.metadata.get("drum") == "cross_stick"]
    slot_velocities: dict[str, list[int]] = defaultdict(list)
    density_velocities: dict[str, list[int]] = defaultdict(list)
    for event, note in zip(drum_events, realized):
        if event.metadata.get("drum") != "cross_stick":
            continue
        slot_velocities[str(event.metadata.get("cross_stick_phrase_slot"))].append(int(note.velocity))
        density_velocities[str(event.metadata.get("cross_stick_contour_density"))].append(int(note.velocity))

    slot_average = {slot: round(sum(values) / len(values), 2) for slot, values in sorted(slot_velocities.items()) if values}
    density_minmax = {density: [min(values), max(values)] for density, values in sorted(density_velocities.items()) if values}
    versioned = [event for event in cross_events if event.metadata.get("bossa_drum_cross_stick_phrase_local_contour_version") == MILESTONE_ID]
    phrase_patterns = sorted({str(event.metadata.get("cross_stick_phrase_pattern")) for event in cross_events})
    contour_counts = Counter(str(event.metadata.get("cross_stick_contour_density")) for event in cross_events)
    slot_counts = Counter(str(event.metadata.get("cross_stick_phrase_slot")) for event in cross_events)

    return {
        "planned_drum_event_count": len(drum_events),
        "planned_cross_stick_event_count": len(cross_events),
        "planned_cross_stick_contour_event_count": len(versioned),
        "planned_cross_stick_contour_coverage_ratio": round(len(versioned) / max(1, len(cross_events)), 4),
        "cross_stick_phrase_patterns_present": phrase_patterns,
        "cross_stick_phrase_slot_counts": dict(slot_counts),
        "cross_stick_contour_density_counts": dict(contour_counts),
        "realized_cross_stick_velocity_set": sorted({int(note.velocity) for note in cross_notes}),
        "realized_cross_stick_velocity_unique_count": len({int(note.velocity) for note in cross_notes}),
        "realized_cross_stick_slot_average_velocity": slot_average,
        "realized_cross_stick_density_minmax_velocity": density_minmax,
        "breath_A_tail_push_events": sum(1 for event in cross_events if event.metadata.get("cross_stick_contour_density") == "breath_space_reduced" and event.metadata.get("cross_stick_phrase_slot") == "A_beat4_phrase_tail"),
        "release_tail_push_events": sum(1 for event in cross_events if event.metadata.get("cross_stick_contour_density") == "settled_release_sparse" and event.metadata.get("cross_stick_phrase_slot") in {"A_beat4_phrase_tail", "B_3and_light_answer"}),
        "split_cross_mark_events": sum(1 for event in cross_events if event.metadata.get("cross_stick_phrase_pattern") == "split"),
        "drum_swing_or_rock_events": sum(1 for event in drum_events if event.metadata.get("swing_ride_pattern") is not False or event.metadata.get("rock_backbeat_pattern") is not False),
        "cross_stick_timing_intents": sorted({str(event.metadata.get("cross_stick_contour_timing_intent")) for event in cross_events}),
    }


def _cross_events(candidate: Any) -> list[Any]:
    return [event for event in candidate.events if event.metadata.get("drum") == "cross_stick"]


def _cross_slots(candidate: Any) -> list[str]:
    return [str(event.metadata.get("cross_stick_phrase_slot")) for event in _cross_events(candidate)]


def _cross_beats(candidate: Any) -> list[float]:
    return [float(event.local_beat) for event in _cross_events(candidate)]


def _acceptance(static_audit: dict[str, Any], runtime_audits: list[dict[str, Any]]) -> dict[str, Any]:
    checks = {
        "style_and_policy_registered": static_audit.get("style_registered") is True
        and static_audit.get("policy_active") is True
        and static_audit.get("policy_version") == MILESTONE_ID,
        "boundary_preserved": static_audit.get("no_parallel_selector") is True
        and static_audit.get("no_bar_first_restore") is True
        and static_audit.get("no_new_pattern_vocabulary") is True
        and static_audit.get("no_piano_bass_voicing_change") is True
        and static_audit.get("no_api_agent_harmonyos_change") is True,
        "pattern_layer_stays_semantic": not static_audit.get("forbidden_pattern_numeric_keys"),
        "full_region_A_B_slots_are_phrase_local": static_audit.get("full_A_cross_slots") == ["A_beat1_phrase_anchor", "A_2and_syncopated_answer", "A_beat4_phrase_tail"]
        and static_audit.get("full_B_cross_slots") == ["B_beat2_response_anchor", "B_3and_light_answer"],
        "breath_and_release_remove_forward_tail": "A_beat4_phrase_tail" not in (static_audit.get("breath_A_cross_slots") or [])
        and "A_beat4_phrase_tail" not in (static_audit.get("release_A_cross_slots") or [])
        and "B_3and_light_answer" not in (static_audit.get("release_B_cross_slots") or []),
        "runtime_blue_bossa_cross_stick_contour_passes": bool(runtime_audits) and all(_runtime_accepts(item) for item in runtime_audits),
    }
    return {"checks": checks, "passed": all(checks.values())}


def _runtime_accepts(item: dict[str, Any]) -> bool:
    slots = dict(item.get("cross_stick_phrase_slot_counts") or {})
    averages = dict(item.get("realized_cross_stick_slot_average_velocity") or {})
    patterns = set(item.get("cross_stick_phrase_patterns_present") or [])
    return (
        bool(item.get("ok"))
        and int(item.get("drums_notes") or 0) > 0
        and float(item.get("planned_cross_stick_contour_coverage_ratio") or 0.0) == 1.0
        and patterns >= {"A", "B", "split"}
        and int(slots.get("A_beat1_phrase_anchor", 0)) > 0
        and int(slots.get("A_2and_syncopated_answer", 0)) > 0
        and int(slots.get("B_beat2_response_anchor", 0)) > 0
        and int(slots.get("B_3and_light_answer", 0)) > 0
        and float(averages.get("A_beat1_phrase_anchor", 0)) > float(averages.get("A_2and_syncopated_answer", 99))
        and int(item.get("breath_A_tail_push_events") or 0) == 0
        and int(item.get("release_tail_push_events") or 0) == 0
        and int(item.get("drum_swing_or_rock_events") or 0) == 0
        and item.get("cross_stick_timing_intents") == ["straight_even_not_swing"]
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
        f"- policy version: `{static.get('policy_version')}`",
        f"- no parallel selector: `{static.get('no_parallel_selector')}`",
        f"- no new pattern vocabulary: `{static.get('no_new_pattern_vocabulary')}`",
        f"- full A cross slots: `{static.get('full_A_cross_slots')}`",
        f"- full B cross slots: `{static.get('full_B_cross_slots')}`",
        f"- breath A cross slots: `{static.get('breath_A_cross_slots')}`",
        f"- release A/B cross slots: `{static.get('release_A_cross_slots')}` / `{static.get('release_B_cross_slots')}`",
        f"- forbidden pattern numeric keys: `{static.get('forbidden_pattern_numeric_keys')}`",
        "",
        "## Runtime audits",
        "",
    ]
    for runtime in summary["runtime_audits"]:
        lines.extend(
            [
                f"### Blue Bossa {runtime['choruses']}x",
                "",
                f"- MIDI: `{runtime['midi_path']}`",
                f"- notes piano/bass/drums: `{runtime.get('piano_notes')}` / `{runtime.get('bass_notes')}` / `{runtime.get('drums_notes')}`",
                f"- cross-stick contour coverage: `{runtime.get('planned_cross_stick_contour_coverage_ratio')}`",
                f"- cross-stick phrase patterns: `{runtime.get('cross_stick_phrase_patterns_present')}`",
                f"- cross-stick slot counts: `{runtime.get('cross_stick_phrase_slot_counts')}`",
                f"- cross-stick contour density counts: `{runtime.get('cross_stick_contour_density_counts')}`",
                f"- cross-stick slot average velocity: `{runtime.get('realized_cross_stick_slot_average_velocity')}`",
                f"- breath A tail push events: `{runtime.get('breath_A_tail_push_events')}`",
                f"- release tail push events: `{runtime.get('release_tail_push_events')}`",
                f"- drum swing/rock events: `{runtime.get('drum_swing_or_rock_events')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Acceptance",
            "",
            f"```json\n{json.dumps(summary['acceptance'], indent=2, ensure_ascii=False)}\n```",
            "",
            f"Recommended next task: `{summary.get('recommended_next_task')}`",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
