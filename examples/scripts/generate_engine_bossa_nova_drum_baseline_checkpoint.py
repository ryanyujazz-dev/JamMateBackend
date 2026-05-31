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
from jammate_engine.realization.percussion_realizer import PercussionRealizer
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.bossa_nova import arrangement_policy, percussion_patterns
from jammate_engine.styles.registry import get_style

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_107"
MILESTONE_LABEL = "v2_6_107 — Engine Bossa Nova Drum Baseline Checkpoint"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 23107, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 23113, "slug": "blue_bossa_5x"},
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    runtime_audits = [_generate_runtime_audit(spec) for spec in DEMO_SPECS]
    summary = {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "scope": (
            "Bossa drum baseline checkpoint after shaker microdynamics, cross-stick phrase-local contour, "
            "kick/bass low-frequency shadow lock, and sparse light marker policy. Metadata/audit/demo only; no new drum behavior."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
    }
    summary["acceptance"] = _acceptance(static_audit, runtime_audits)
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_drum_baseline_checkpoint_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_drum_baseline_checkpoint_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    policy = arrangement_policy.get_arrangement_policy()
    candidate = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "region_source_bar_index": 7})[0]
    events = list(candidate.events)
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
        "policy_active": policy.get("bossa_nova_drum_baseline_checkpoint_active"),
        "policy_version": policy.get("bossa_nova_drum_baseline_checkpoint_version"),
        "policy_behavior_change": policy.get("bossa_nova_drum_baseline_checkpoint_behavior_change"),
        "no_parallel_selector": policy.get("bossa_nova_drum_baseline_checkpoint_no_parallel_selector"),
        "no_bar_first_restore": policy.get("bossa_nova_drum_baseline_checkpoint_no_bar_first_restore"),
        "no_new_drum_vocabulary": policy.get("bossa_nova_drum_baseline_checkpoint_no_new_drum_vocabulary"),
        "no_piano_bass_voicing_change": policy.get("bossa_nova_drum_baseline_checkpoint_no_piano_bass_voicing_change"),
        "no_core_voicing_change": policy.get("bossa_nova_drum_baseline_checkpoint_no_core_voicing_change"),
        "no_api_agent_harmonyos_change": policy.get("bossa_nova_drum_baseline_checkpoint_no_api_agent_harmonyos_change"),
        "completed_versions": list(policy.get("bossa_nova_drum_baseline_checkpoint_completed_versions") or ()),
        "candidate_active": candidate.metadata.get("bossa_drum_baseline_checkpoint_active"),
        "candidate_version": candidate.metadata.get("bossa_drum_baseline_checkpoint_version"),
        "candidate_behavior_change": candidate.metadata.get("bossa_drum_baseline_checkpoint_behavior_change"),
        "candidate_tags": list(candidate.tags),
        "event_count": len(events),
        "candidate_event_checkpoint_coverage_ratio": round(
            sum(1 for event in events if event.metadata.get("bossa_drum_baseline_checkpoint_version") == MILESTONE_ID) / max(1, len(events)),
            4,
        ),
        "has_shaker_microdynamic": any(event.metadata.get("shaker_microdynamic_enabled") for event in events),
        "has_cross_stick_contour": any(event.metadata.get("bossa_drum_cross_stick_phrase_local_contour_active") for event in events),
        "has_kick_bass_lock": any(event.metadata.get("bossa_kick_bass_lock_and_low_frequency_shadow_active") for event in events),
        "has_light_marker_policy": any(event.metadata.get("bossa_light_marker_fill_policy_active") for event in events),
        "forbidden_pattern_numeric_keys": forbidden_numeric_keys,
        "recommended_next_task": policy.get("bossa_nova_drum_baseline_checkpoint_recommended_next_task"),
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_drum_baseline_checkpoint_demo.mid"
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

    drum_notes = PercussionRealizer().realize(drum_events)
    velocities_by_family: dict[str, list[int]] = {"shaker": [], "cross_stick": [], "kick": [], "marker": []}
    for event, note in zip(drum_events, drum_notes):
        drum = str(event.metadata.get("drum") or "")
        if event.metadata.get("bossa_light_marker_fill_policy_active"):
            velocities_by_family["marker"].append(int(note.velocity))
        elif drum in velocities_by_family:
            velocities_by_family[drum].append(int(note.velocity))

    checkpoint_count = sum(1 for event in drum_events if event.metadata.get("bossa_drum_baseline_checkpoint_version") == MILESTONE_ID)
    marker_events = [event for event in drum_events if event.metadata.get("bossa_light_marker_fill_policy_active")]
    return {
        "planned_drum_event_count": len(drum_events),
        "checkpoint_event_count": checkpoint_count,
        "checkpoint_coverage_ratio": round(checkpoint_count / max(1, len(drum_events)), 4),
        "shaker_microdynamic_event_count": sum(1 for event in drum_events if event.metadata.get("shaker_microdynamic_enabled")),
        "cross_stick_contour_event_count": sum(1 for event in drum_events if event.metadata.get("bossa_drum_cross_stick_phrase_local_contour_active") and event.metadata.get("drum") == "cross_stick"),
        "kick_bass_lock_event_count": sum(1 for event in drum_events if event.metadata.get("bossa_kick_bass_lock_and_low_frequency_shadow_active")),
        "light_marker_event_count": len(marker_events),
        "marker_kind_counts": dict(Counter(str(event.metadata.get("bossa_light_marker_fill_policy_kind")) for event in marker_events)),
        "drum_swing_or_rock_events": sum(1 for event in drum_events if event.metadata.get("swing_ride_pattern") is not False or event.metadata.get("rock_backbeat_pattern") is not False),
        "tom_crash_roll_marker_events": sum(1 for event in marker_events if event.metadata.get("tom_fill_pattern") is not False or event.metadata.get("crash_fill_pattern") is not False or event.metadata.get("snare_roll_fill_pattern") is not False),
        "velocity_ranges": {
            family: [min(values), max(values)] if values else [0, 0]
            for family, values in sorted(velocities_by_family.items())
        },
        "unique_velocity_counts": {family: len(set(values)) for family, values in sorted(velocities_by_family.items())},
    }


def _acceptance(static: dict[str, Any], runtime_audits: list[dict[str, Any]]) -> dict[str, Any]:
    runtime_ok = bool(runtime_audits) and all(
        audit.get("ok") is True
        and float(audit.get("checkpoint_coverage_ratio") or 0.0) == 1.0
        and int(audit.get("shaker_microdynamic_event_count") or 0) > 0
        and int(audit.get("cross_stick_contour_event_count") or 0) > 0
        and int(audit.get("kick_bass_lock_event_count") or 0) > 0
        and int(audit.get("light_marker_event_count") or 0) > 0
        and int(audit.get("drum_swing_or_rock_events") or 0) == 0
        and int(audit.get("tom_crash_roll_marker_events") or 0) == 0
        for audit in runtime_audits
    )
    checks = {
        "policy_declares_drum_checkpoint": static.get("policy_active") is True and static.get("policy_version") == MILESTONE_ID,
        "checkpoint_is_metadata_only": static.get("policy_behavior_change") is False and static.get("candidate_behavior_change") is False,
        "no_parallel_or_bar_first": static.get("no_parallel_selector") is True and static.get("no_bar_first_restore") is True,
        "no_new_vocabulary_or_cross_track_change": static.get("no_new_drum_vocabulary") is True and static.get("no_piano_bass_voicing_change") is True,
        "candidate_events_stamped": static.get("candidate_event_checkpoint_coverage_ratio") == 1.0,
        "static_layers_present": all(static.get(key) for key in ("has_shaker_microdynamic", "has_cross_stick_contour", "has_kick_bass_lock", "has_light_marker_policy")),
        "no_pattern_numeric_values": static.get("forbidden_pattern_numeric_keys") == [],
        "runtime_blue_bossa_drum_checkpoint_pass": runtime_ok,
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
        f"- Completed drum versions: {static.get('completed_versions')}",
        f"- Candidate event checkpoint coverage: {static.get('candidate_event_checkpoint_coverage_ratio')}",
        f"- Layers present: shaker={static.get('has_shaker_microdynamic')}, cross={static.get('has_cross_stick_contour')}, kick={static.get('has_kick_bass_lock')}, marker={static.get('has_light_marker_policy')}",
        f"- Forbidden numeric pattern keys: {static.get('forbidden_pattern_numeric_keys')}",
        "",
        "## Runtime audits",
    ]
    for audit in summary["runtime_audits"]:
        lines.extend(
            [
                f"### Blue Bossa {audit.get('choruses')}x",
                f"- note_events_by_track: {audit.get('note_events_by_track')}",
                f"- planned drum events: {audit.get('planned_drum_event_count')}",
                f"- checkpoint coverage: {audit.get('checkpoint_coverage_ratio')}",
                f"- shaker / cross / kick / marker events: {audit.get('shaker_microdynamic_event_count')} / {audit.get('cross_stick_contour_event_count')} / {audit.get('kick_bass_lock_event_count')} / {audit.get('light_marker_event_count')}",
                f"- marker kind counts: {audit.get('marker_kind_counts')}",
                f"- velocity ranges: {audit.get('velocity_ranges')}",
                f"- drum swing/rock events: {audit.get('drum_swing_or_rock_events')}",
                f"- tom/crash/roll marker events: {audit.get('tom_crash_roll_marker_events')}",
                f"- MIDI: `{audit.get('midi_path')}`",
                "",
            ]
        )
    lines.extend(["## Acceptance", json.dumps(summary["acceptance"], indent=2, ensure_ascii=False)])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
