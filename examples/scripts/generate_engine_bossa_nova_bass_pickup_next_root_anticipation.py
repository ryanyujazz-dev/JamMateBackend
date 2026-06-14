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
from jammate_engine.realization.bass_foundation_realizer import BassFoundationRealizer
from jammate_engine.realization.percussion_realizer import PercussionRealizer
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.bossa_nova import arrangement_policy, bass_foundation_patterns
from jammate_engine.styles.registry import get_style

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_108"
MILESTONE_LABEL = "v2_6_108 — Engine Bossa Nova Bass Pickup + Next-Root Anticipation Policy"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 23108, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 23109, "slug": "blue_bossa_5x"},
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    runtime_audits = [_generate_runtime_audit(spec) for spec in DEMO_SPECS]
    summary = {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "scope": (
            "Bossa bass refinement after drum checkpoint: keep root/fifth support, add occasional 2& fifth pickup "
            "and controlled 4& next-root anticipation on full ChordRegions only, while keeping split/short regions root-only "
            "and keeping kick as a main-beat shadow rather than following pickups."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
    }
    summary["acceptance"] = _acceptance(static_audit, runtime_audits)
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_bass_pickup_next_root_anticipation_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_bass_pickup_next_root_anticipation_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    policy = arrangement_policy.get_arrangement_policy()
    full_candidates = bass_foundation_patterns.get_pattern_candidates(
        {
            "region_duration_beats": 4.0,
            "chord_symbol": "Cm7",
            "next_chord_symbol": "F7",
            "bossa_nova_arrangement_arc_intent": {
                "phase": "loop_wave_gentle_lift",
                "runtime_intent": "gentle_transition_lift",
                "full_band_arc_band": "gentle_lift",
            },
        }
    )
    split_candidate = bass_foundation_patterns.get_pattern_candidates({"region_duration_beats": 2.0, "chord_symbol": "Dm7b5", "next_chord_symbol": "G7b9"})[0]
    short_candidate = bass_foundation_patterns.get_pattern_candidates({"region_duration_beats": 1.0, "chord_symbol": "G7b9", "next_chord_symbol": "Cm7"})[0]
    events = [event for candidate in full_candidates for event in candidate.events]
    forbidden_numeric_keys = sorted(
        {
            key
            for event in events
            for key in event.metadata
            if key in {"velocity", "duration", "duration_beats", "pedal", "midi_note", "note"}
        }
    )
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "policy_active": policy.get("bossa_nova_bass_pickup_and_next_root_anticipation_active"),
        "policy_version": policy.get("bossa_nova_bass_pickup_and_next_root_anticipation_version"),
        "policy_behavior_change": policy.get("bossa_nova_bass_pickup_and_next_root_anticipation_behavior_change"),
        "no_parallel_selector": policy.get("bossa_nova_bass_pickup_and_next_root_anticipation_no_parallel_selector"),
        "no_bar_first_restore": policy.get("bossa_nova_bass_pickup_and_next_root_anticipation_no_bar_first_restore"),
        "no_walking_bass": policy.get("bossa_nova_bass_pickup_and_next_root_anticipation_no_walking_bass"),
        "no_piano_pattern_change": policy.get("bossa_nova_bass_pickup_and_next_root_anticipation_no_piano_pattern_change"),
        "no_core_voicing_change": policy.get("bossa_nova_bass_pickup_and_next_root_anticipation_no_core_voicing_change"),
        "no_api_agent_harmonyos_change": policy.get("bossa_nova_bass_pickup_and_next_root_anticipation_no_api_agent_harmonyos_change"),
        "full_candidate_names": [candidate.name for candidate in full_candidates],
        "full_candidate_variants": [candidate.metadata.get("bossa_bass_pickup_variant") for candidate in full_candidates],
        "full_candidate_count": len(full_candidates),
        "has_2and_pickup_candidate": any(event.local_beat == 1.5 and event.metadata.get("degree") == "fifth" for event in events),
        "has_4and_next_root_candidate": any(event.local_beat == 3.5 and event.metadata.get("degree") == "next_root" for event in events),
        "split_region_degrees": [event.metadata.get("degree") for event in split_candidate.events],
        "short_region_degrees": [event.metadata.get("degree") for event in short_candidate.events],
        "forbidden_pattern_numeric_keys": forbidden_numeric_keys,
        "recommended_next_task": policy.get("bossa_nova_bass_pickup_and_next_root_anticipation_recommended_next_task"),
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_bass_pickup_next_root_anticipation_demo.mid"
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
    bass_events = []
    drum_events = []
    for region in timeline.regions:
        plan = style.plan_region(
            region,
            context={"tempo": int(score.get("tempo", 140)), "rng": rng, "style_pattern_history": history, "ensemble": {"bass_present": True}},
        )
        bass_events.extend([event for event in plan.events if event.track == "bass"])
        drum_events.extend([event for event in plan.events if event.track == "drums"])

    bass_notes = BassFoundationRealizer().realize(bass_events)
    drum_notes = PercussionRealizer().realize(drum_events)
    pickup_events = [event for event in bass_events if event.local_beat == 1.5 and event.metadata.get("degree") == "fifth"]
    next_root_events = [event for event in bass_events if event.local_beat == 3.5 and event.metadata.get("degree") == "next_root"]
    split_short_non_root = [
        event
        for event in bass_events
        if float(event.metadata.get("region_duration_beats", 4.0)) <= 2.25 and event.metadata.get("degree") != "root"
    ]
    terminal_next_root = [
        event
        for event in next_root_events
        if event.metadata.get("region_is_last_bar_of_chorus")
        and int(event.metadata.get("region_chorus_index") or 0) >= int(event.metadata.get("region_total_choruses") or 1) - 1
    ]
    kick_pickup_follow = [event for event in drum_events if event.metadata.get("drum") == "kick" and event.local_beat in {1.5, 3.5}]
    walking_like = [
        event
        for event in bass_events
        if event.metadata.get("walking_bass") is not False
        or event.metadata.get("degree") not in {"root", "fifth", "next_root"}
        or event.local_beat not in {0.0, 1.5, 2.0, 3.5}
    ]
    velocities_by_degree: dict[str, list[int]] = {"root": [], "fifth": [], "next_root": []}
    durations_by_role: dict[str, list[float]] = {"main": [], "pickup_2and": [], "next_root_4and": []}
    for event, note in zip(bass_events, bass_notes):
        degree = str(event.metadata.get("degree"))
        if degree in velocities_by_degree:
            velocities_by_degree[degree].append(int(note.velocity))
        role = str(event.metadata.get("bossa_bass_pickup_role") or "main_support")
        if role == "two_and_fifth_pickup":
            durations_by_role["pickup_2and"].append(float(note.duration_beats))
        elif role == "four_and_next_root_anticipation":
            durations_by_role["next_root_4and"].append(float(note.duration_beats))
        else:
            durations_by_role["main"].append(float(note.duration_beats))

    return {
        "planned_bass_event_count": len(bass_events),
        "planned_drum_event_count": len(drum_events),
        "bass_degree_counts": dict(Counter(str(event.metadata.get("degree")) for event in bass_events)),
        "bass_local_beat_counts": {str(k): v for k, v in Counter(float(event.local_beat or 0.0) for event in bass_events).items()},
        "bass_candidate_counts": dict(Counter(str(event.metadata.get("candidate")) for event in bass_events)),
        "bass_pickup_variant_counts": dict(Counter(str(event.metadata.get("bossa_bass_pickup_variant")) for event in bass_events)),
        "pickup_2and_event_count": len(pickup_events),
        "next_root_4and_event_count": len(next_root_events),
        "split_short_non_root_events": len(split_short_non_root),
        "terminal_next_root_events": len(terminal_next_root),
        "kick_pickup_follow_events": len(kick_pickup_follow),
        "walking_like_bass_events": len(walking_like),
        "bass_velocity_ranges": {degree: [min(values), max(values)] if values else [0, 0] for degree, values in velocities_by_degree.items()},
        "bass_duration_ranges": {role: [round(min(values), 3), round(max(values), 3)] if values else [0, 0] for role, values in durations_by_role.items()},
        "drum_kick_event_count": sum(1 for event in drum_events if event.metadata.get("drum") == "kick"),
        "drum_kick_velocity_range": [min([note.velocity for event, note in zip(drum_events, drum_notes) if event.metadata.get("drum") == "kick"] or [0]), max([note.velocity for event, note in zip(drum_events, drum_notes) if event.metadata.get("drum") == "kick"] or [0])],
    }


def _acceptance(static: dict[str, Any], runtime_audits: list[dict[str, Any]]) -> dict[str, Any]:
    runtime_ok = bool(runtime_audits) and all(
        audit.get("ok") is True
        and int(audit.get("pickup_2and_event_count") or 0) > 0
        and int(audit.get("next_root_4and_event_count") or 0) > 0
        and int(audit.get("split_short_non_root_events") or 0) == 0
        and int(audit.get("terminal_next_root_events") or 0) == 0
        and int(audit.get("kick_pickup_follow_events") or 0) == 0
        and int(audit.get("walking_like_bass_events") or 0) == 0
        for audit in runtime_audits
    )
    checks = {
        "policy_declares_bass_pickup": static.get("policy_active") is True and static.get("policy_version") == MILESTONE_ID,
        "no_parallel_or_bar_first_or_walking": static.get("no_parallel_selector") is True and static.get("no_bar_first_restore") is True and static.get("no_walking_bass") is True,
        "no_cross_track_or_voicing_change": static.get("no_piano_pattern_change") is True and static.get("no_core_voicing_change") is True and static.get("no_api_agent_harmonyos_change") is True,
        "full_region_candidates_include_pickup_and_nextroot": static.get("has_2and_pickup_candidate") is True and static.get("has_4and_next_root_candidate") is True,
        "split_short_regions_root_only": static.get("split_region_degrees") == ["root"] and static.get("short_region_degrees") == ["root"],
        "no_pattern_numeric_values": static.get("forbidden_pattern_numeric_keys") == [],
        "runtime_blue_bossa_bass_pickup_pass": runtime_ok,
    }
    return {"passed": all(checks.values()), "checks": checks}


def _render_report(summary: dict[str, Any]) -> str:
    static = summary["static_audit"]
    lines = [
        f"# {MILESTONE_LABEL}",
        "",
        "## Scope",
        str(summary["scope"]),
        "",
        "## Static audit",
        f"- Policy active/version: {static.get('policy_active')} / {static.get('policy_version')}",
        f"- Behavior change: {static.get('policy_behavior_change')}",
        f"- Full candidate variants: {static.get('full_candidate_variants')}",
        f"- Split/short region degrees: {static.get('split_region_degrees')} / {static.get('short_region_degrees')}",
        f"- Forbidden numeric pattern keys: {static.get('forbidden_pattern_numeric_keys')}",
        "",
        "## Runtime audits",
    ]
    for audit in summary["runtime_audits"]:
        lines.extend(
            [
                f"### Blue Bossa {audit.get('choruses')}x",
                f"- note_events_by_track: {audit.get('note_events_by_track')}",
                f"- planned bass/drum events: {audit.get('planned_bass_event_count')} / {audit.get('planned_drum_event_count')}",
                f"- bass degree counts: {audit.get('bass_degree_counts')}",
                f"- bass local beat counts: {audit.get('bass_local_beat_counts')}",
                f"- pickup 2& / next-root 4& events: {audit.get('pickup_2and_event_count')} / {audit.get('next_root_4and_event_count')}",
                f"- split/short non-root events: {audit.get('split_short_non_root_events')}",
                f"- terminal next-root events: {audit.get('terminal_next_root_events')}",
                f"- kick pickup-follow events: {audit.get('kick_pickup_follow_events')}",
                f"- walking-like bass events: {audit.get('walking_like_bass_events')}",
                f"- bass velocity ranges: {audit.get('bass_velocity_ranges')}",
                f"- bass duration ranges: {audit.get('bass_duration_ranges')}",
                f"- MIDI: `{audit.get('midi_path')}`",
                "",
            ]
        )
    lines.extend(["## Acceptance", json.dumps(summary["acceptance"], indent=2, ensure_ascii=False)])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
