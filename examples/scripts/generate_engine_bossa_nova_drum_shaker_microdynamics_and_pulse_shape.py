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
MILESTONE_ID = "v2_6_100"
MILESTONE_LABEL = "v2_6_100 — Engine Bossa Nova Drum Shaker Microdynamics + Pulse Shape"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 23100, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 23105, "slug": "blue_bossa_5x"},
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
            "Refine the existing Bossa shaker/hi-hat proxy in place. Pattern candidates keep the same shaker/cross-stick/light-kick identity shape "
            "and only annotate semantic straight-8th pulse slots; the shared percussion realizer maps those slots to microdynamic velocity shape. "
            "No piano, bass, voicing, API, Agent, or HarmonyOS change."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
        "acceptance": acceptance,
        "recommended_next_task": static_audit.get("recommended_next_task"),
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_drum_shaker_microdynamics_and_pulse_shape_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_drum_shaker_microdynamics_and_pulse_shape_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()
    full = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "bar_index": 0})[0]
    split = percussion_patterns.get_pattern_candidates({"region_duration_beats": 2.0, "bar_index": 0})[0]
    shaker_events = [event for event in full.events if event.metadata.get("drum") == "shaker"]
    slots = [str(event.metadata.get("shaker_pulse_slot")) for event in shaker_events]
    forbidden_numeric_keys = [
        key
        for event in shaker_events
        for key in event.metadata
        if key in {"velocity", "duration", "duration_beats", "pedal", "midi_note", "note"}
    ]
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "style_registered": getattr(style, "name", None) == "bossa_nova",
        "policy_active": policy.get("bossa_nova_drum_shaker_microdynamics_and_pulse_shape_active"),
        "policy_version": policy.get("bossa_nova_drum_shaker_microdynamics_and_pulse_shape_version"),
        "behavior_change": policy.get("bossa_nova_drum_shaker_microdynamics_and_pulse_shape_behavior_change"),
        "no_parallel_selector": policy.get("bossa_nova_drum_shaker_microdynamics_and_pulse_shape_no_parallel_selector"),
        "no_bar_first_restore": policy.get("bossa_nova_drum_shaker_microdynamics_and_pulse_shape_no_bar_first_restore"),
        "no_new_pattern_vocabulary": policy.get("bossa_nova_drum_shaker_microdynamics_and_pulse_shape_no_new_pattern_vocabulary"),
        "no_piano_bass_voicing_change": policy.get("bossa_nova_drum_shaker_microdynamics_and_pulse_shape_no_piano_bass_voicing_change"),
        "no_api_agent_harmonyos_change": policy.get("bossa_nova_drum_shaker_microdynamics_and_pulse_shape_no_api_agent_harmonyos_change"),
        "tracks": list(policy.get("bossa_nova_drum_shaker_microdynamics_and_pulse_shape_tracks") or ()),
        "full_candidate_name": full.name,
        "full_candidate_category": full.category,
        "full_event_count": len(full.events),
        "full_shaker_event_count": len(shaker_events),
        "full_shaker_pulse_slots": slots,
        "full_shaker_pulse_slot_counts": dict(Counter(slots)),
        "full_shaker_microdynamic_versions": sorted({str(event.metadata.get("bossa_drum_shaker_microdynamics_and_pulse_shape_version")) for event in shaker_events}),
        "forbidden_pattern_numeric_keys": forbidden_numeric_keys,
        "split_max_beat": max(float(event.local_beat) for event in split.events),
        "split_shaker_event_count": sum(1 for event in split.events if event.metadata.get("drum") == "shaker"),
        "recommended_next_task": policy.get("bossa_nova_drum_shaker_microdynamics_and_pulse_shape_recommended_next_task"),
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_drum_shaker_microdynamics_and_pulse_shape_demo.mid"
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
    shaker_events = [event for event in drum_events if event.metadata.get("drum") == "shaker"]
    shaker_notes = [note for event, note in zip(drum_events, realized) if event.metadata.get("drum") == "shaker"]
    # zip(drum_events, realized) is safe because PercussionRealizer emits one active drum note per active drum event.
    slot_velocities: dict[str, list[int]] = defaultdict(list)
    profile_velocities: dict[str, list[int]] = defaultdict(list)
    for event, note in zip(drum_events, realized):
        if event.metadata.get("drum") != "shaker":
            continue
        slot_velocities[str(event.metadata.get("shaker_pulse_slot"))].append(int(note.velocity))
        profile_velocities[str(event.metadata.get("dynamic_profile"))].append(int(note.velocity))

    slot_average = {slot: round(sum(values) / len(values), 2) for slot, values in sorted(slot_velocities.items()) if values}
    profile_minmax = {profile: [min(values), max(values)] for profile, values in sorted(profile_velocities.items()) if values}
    shaker_velocity_set = sorted({int(note.velocity) for note in shaker_notes})
    pulse_versioned = [event for event in shaker_events if event.metadata.get("bossa_drum_shaker_microdynamics_and_pulse_shape_version") == MILESTONE_ID]
    return {
        "planned_drum_event_count": len(drum_events),
        "planned_shaker_event_count": len(shaker_events),
        "planned_shaker_microdynamic_event_count": len(pulse_versioned),
        "planned_shaker_microdynamic_coverage_ratio": round(len(pulse_versioned) / max(1, len(shaker_events)), 4),
        "planned_shaker_pulse_slot_counts": dict(Counter(str(event.metadata.get("shaker_pulse_slot")) for event in shaker_events)),
        "planned_shaker_dynamic_profile_counts": dict(Counter(str(event.metadata.get("dynamic_profile")) for event in shaker_events)),
        "realized_shaker_velocity_set": shaker_velocity_set,
        "realized_shaker_velocity_unique_count": len(shaker_velocity_set),
        "realized_shaker_slot_average_velocity": slot_average,
        "realized_shaker_profile_minmax_velocity": profile_minmax,
        "drum_swing_or_rock_events": sum(1 for event in drum_events if event.metadata.get("swing_ride_pattern") is not False or event.metadata.get("rock_backbeat_pattern") is not False),
        "shaker_timing_intents": sorted({str(event.metadata.get("shaker_microdynamic_timing_intent")) for event in shaker_events}),
        "split_region_shaker_overflow_events": sum(1 for event in shaker_events if float(event.local_beat or 0.0) >= float(event.metadata.get("region_duration_beats", 4.0)) + 1e-9),
    }


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
        "pattern_layer_stays_semantic": not static_audit.get("forbidden_pattern_numeric_keys")
        and static_audit.get("full_candidate_category") == "bossa_shaker_cross_stick_light_kick_identity",
        "full_region_has_shaker_pulse_slots": static_audit.get("full_shaker_event_count") == 8
        and set(static_audit.get("full_shaker_pulse_slots") or []) == {"primary_clear", "secondary_mid", "offbeat_light", "offbeat_feather"},
        "split_region_stays_region_local": float(static_audit.get("split_max_beat") or 99.0) < 2.0,
        "runtime_blue_bossa_shaker_microdynamics_passes": bool(runtime_audits) and all(_runtime_accepts(item) for item in runtime_audits),
    }
    return {"checks": checks, "passed": all(checks.values())}


def _runtime_accepts(item: dict[str, Any]) -> bool:
    slots = dict(item.get("planned_shaker_pulse_slot_counts") or {})
    averages = dict(item.get("realized_shaker_slot_average_velocity") or {})
    return (
        bool(item.get("ok"))
        and int(item.get("drums_notes") or 0) > 0
        and float(item.get("planned_shaker_microdynamic_coverage_ratio") or 0.0) == 1.0
        and int(item.get("realized_shaker_velocity_unique_count") or 0) >= 4
        and int(slots.get("primary_clear", 0)) > 0
        and int(slots.get("secondary_mid", 0)) > 0
        and int(slots.get("offbeat_light", 0)) > 0
        and int(slots.get("offbeat_feather", 0)) > 0
        and float(averages.get("primary_clear", 0)) > float(averages.get("offbeat_feather", 99))
        and int(item.get("drum_swing_or_rock_events") or 0) == 0
        and int(item.get("split_region_shaker_overflow_events") or 0) == 0
        and item.get("shaker_timing_intents") == ["straight_even_not_swing"]
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
        f"- full shaker pulse slots: `{static.get('full_shaker_pulse_slots')}`",
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
                f"- shaker microdynamic coverage: `{runtime.get('planned_shaker_microdynamic_coverage_ratio')}`",
                f"- shaker unique velocities: `{runtime.get('realized_shaker_velocity_unique_count')}`",
                f"- shaker slot average velocity: `{runtime.get('realized_shaker_slot_average_velocity')}`",
                f"- shaker profile min/max: `{runtime.get('realized_shaker_profile_minmax_velocity')}`",
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
