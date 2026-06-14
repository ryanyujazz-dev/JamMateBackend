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
from jammate_engine.realization.bass_foundation_realizer import BassFoundationRealizer
from jammate_engine.realization.percussion_realizer import PercussionRealizer
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.bossa_nova import arrangement_policy, bass_foundation_patterns, percussion_patterns
from jammate_engine.styles.registry import get_style

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_105"
MILESTONE_LABEL = "v2_6_105 — Engine Bossa Nova Kick/Bass Lock and Low-frequency Shadow Refinement"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 23105, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 23110, "slug": "blue_bossa_5x"},
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
            "Refine the existing Bossa low-frequency drum/bass layer in place. Bass remains root/fifth support, and kick remains a low-velocity shadow locked to the same root/fifth beats. "
            "Split/short ChordRegions stay root-only; no four-on-floor, rock backbeat, swing ride, piano, voicing, API, Agent, or HarmonyOS change."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
        "acceptance": acceptance,
        "recommended_next_task": static_audit.get("recommended_next_task"),
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_kick_bass_lock_low_frequency_shadow_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_kick_bass_lock_low_frequency_shadow_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()
    full_drums = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "region_source_bar_index": 0})[0]
    split_drums = percussion_patterns.get_pattern_candidates({"region_duration_beats": 2.0, "region_source_bar_index": 0})[0]
    short_drums = percussion_patterns.get_pattern_candidates({"region_duration_beats": 1.0, "region_source_bar_index": 0})[0]
    full_bass = bass_foundation_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "region_source_bar_index": 0})[0]
    split_bass = bass_foundation_patterns.get_pattern_candidates({"region_duration_beats": 2.0, "region_source_bar_index": 0})[0]
    all_kicks = _kick_events(full_drums) + _kick_events(split_drums) + _kick_events(short_drums)
    forbidden_numeric_keys = sorted(
        {
            key
            for event in all_kicks
            for key in event.metadata
            if key in {"velocity", "duration", "duration_beats", "pedal", "midi_note", "note"}
        }
    )
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "style_registered": getattr(style, "name", None) == "bossa_nova",
        "policy_active": policy.get("bossa_nova_kick_bass_lock_and_low_frequency_shadow_active"),
        "policy_version": policy.get("bossa_nova_kick_bass_lock_and_low_frequency_shadow_version"),
        "no_parallel_selector": policy.get("bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_parallel_selector"),
        "no_bar_first_restore": policy.get("bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_bar_first_restore"),
        "no_new_drum_vocabulary": policy.get("bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_new_drum_vocabulary"),
        "no_piano_voicing_change": policy.get("bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_piano_voicing_change"),
        "no_core_voicing_change": policy.get("bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_core_voicing_change"),
        "no_api_agent_harmonyos_change": policy.get("bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_api_agent_harmonyos_change"),
        "tracks": list(policy.get("bossa_nova_kick_bass_lock_and_low_frequency_shadow_tracks") or ()),
        "full_kick_beats": [event.local_beat for event in _kick_events(full_drums)],
        "full_kick_lock_slots": [str(event.metadata.get("kick_bass_lock_slot")) for event in _kick_events(full_drums)],
        "full_kick_locked_degrees": [str(event.metadata.get("kick_locked_to_bass_degree")) for event in _kick_events(full_drums)],
        "split_kick_beats": [event.local_beat for event in _kick_events(split_drums)],
        "split_kick_lock_slots": [str(event.metadata.get("kick_bass_lock_slot")) for event in _kick_events(split_drums)],
        "short_kick_beats": [event.local_beat for event in _kick_events(short_drums)],
        "short_kick_lock_slots": [str(event.metadata.get("kick_bass_lock_slot")) for event in _kick_events(short_drums)],
        "full_bass_degrees": [str(event.metadata.get("degree")) for event in full_bass.events],
        "full_bass_expected_kick_slots": [str(event.metadata.get("bass_kick_lock_expected_kick_slot")) for event in full_bass.events],
        "split_bass_degrees": [str(event.metadata.get("degree")) for event in split_bass.events],
        "kick_shadow_roles": sorted({str(event.metadata.get("kick_low_frequency_role")) for event in all_kicks}),
        "kick_four_on_floor_driver_flags": sorted({str(event.metadata.get("kick_four_on_floor_driver")) for event in all_kicks}),
        "forbidden_pattern_numeric_keys": forbidden_numeric_keys,
        "recommended_next_task": policy.get("bossa_nova_kick_bass_lock_and_low_frequency_shadow_recommended_next_task"),
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_kick_bass_lock_low_frequency_shadow_demo.mid"
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
    kick_pairs = [(event, note) for event, note in zip(drum_events, drum_notes) if event.metadata.get("drum") == "kick"]
    bass_pairs = list(zip(bass_events, bass_notes))
    kick_events = [event for event, _ in kick_pairs]
    kick_notes = [note for _, note in kick_pairs]
    bass_velocities = [int(note.velocity) for _, note in bass_pairs]
    kick_velocities = [int(note.velocity) for note in kick_notes]
    slot_velocities: dict[str, list[int]] = defaultdict(list)
    for event, note in kick_pairs:
        slot_velocities[str(event.metadata.get("kick_bass_lock_slot"))].append(int(note.velocity))

    slot_average = {slot: round(sum(values) / len(values), 2) for slot, values in sorted(slot_velocities.items()) if values}
    versioned = [event for event in kick_events if event.metadata.get("bossa_kick_bass_lock_and_low_frequency_shadow_version") == MILESTONE_ID]
    duration_family_by_region = {str(event.region_id): str(event.metadata.get("kick_region_duration_family")) for event in kick_events}
    short_or_split_regions = {rid for rid, family in duration_family_by_region.items() if family in {"split_region", "very_short_region"}}

    return {
        "planned_bass_event_count": len(bass_events),
        "planned_drum_event_count": len(drum_events),
        "kick_event_count": len(kick_events),
        "kick_lock_event_count": len(versioned),
        "kick_lock_coverage_ratio": round(len(versioned) / max(1, len(kick_events)), 4),
        "kick_root_events": sum(1 for event in kick_events if event.metadata.get("kick_locked_to_bass_degree") == "root"),
        "kick_fifth_events": sum(1 for event in kick_events if event.metadata.get("kick_locked_to_bass_degree") == "fifth"),
        "kick_lock_slot_counts": dict(Counter(str(event.metadata.get("kick_bass_lock_slot")) for event in kick_events)),
        "realized_kick_slot_average_velocity": slot_average,
        "kick_velocity_set": sorted(set(kick_velocities)),
        "kick_min_velocity": min(kick_velocities) if kick_velocities else 0,
        "kick_max_velocity": max(kick_velocities) if kick_velocities else 0,
        "bass_min_velocity": min(bass_velocities) if bass_velocities else 0,
        "bass_max_velocity": max(bass_velocities) if bass_velocities else 0,
        "split_or_short_fifth_kick_events": sum(1 for event in kick_events if str(event.region_id) in short_or_split_regions and event.metadata.get("kick_locked_to_bass_degree") == "fifth"),
        "four_on_floor_driver_events": sum(1 for event in kick_events if event.metadata.get("kick_four_on_floor_driver") is not False),
        "rock_backbeat_driver_events": sum(1 for event in kick_events if event.metadata.get("kick_rock_backbeat_driver") is not False),
        "drum_swing_or_rock_events": sum(1 for event in drum_events if event.metadata.get("swing_ride_pattern") is not False or event.metadata.get("rock_backbeat_pattern") is not False),
        "bass_walking_like_events": sum(1 for event in bass_events if event.metadata.get("walking_bass") is not False),
        "bass_degree_counts": dict(Counter(str(event.metadata.get("degree")) for event in bass_events)),
        "bass_kick_counterpart_coverage_ratio": round(sum(1 for event in bass_events if event.metadata.get("bossa_kick_bass_lock_and_low_frequency_shadow_version") == MILESTONE_ID) / max(1, len(bass_events)), 4),
        "kick_low_frequency_roles": sorted({str(event.metadata.get("kick_low_frequency_role")) for event in kick_events}),
        "kick_timing_intents": sorted({str(event.metadata.get("kick_bass_lock_timing_intent")) for event in kick_events}),
    }


def _kick_events(candidate: Any) -> list[Any]:
    return [event for event in candidate.events if event.metadata.get("drum") == "kick"]


def _acceptance(static: dict[str, Any], runtime_audits: list[dict[str, Any]]) -> dict[str, Any]:
    runtime_ok = bool(runtime_audits) and all(
        audit.get("ok") is True
        and audit.get("kick_lock_coverage_ratio") == 1.0
        and int(audit.get("kick_root_events") or 0) > 0
        and int(audit.get("kick_fifth_events") or 0) > 0
        and int(audit.get("split_or_short_fifth_kick_events") or 0) == 0
        and int(audit.get("four_on_floor_driver_events") or 0) == 0
        and int(audit.get("rock_backbeat_driver_events") or 0) == 0
        and int(audit.get("drum_swing_or_rock_events") or 0) == 0
        and int(audit.get("bass_walking_like_events") or 0) == 0
        and float(audit.get("bass_kick_counterpart_coverage_ratio") or 0.0) == 1.0
        and int(audit.get("kick_max_velocity") or 99) < int(audit.get("bass_min_velocity") or 0)
        for audit in runtime_audits
    )
    checks = {
        "policy_declares_kick_bass_lock": static.get("policy_active") is True and static.get("policy_version") == MILESTONE_ID,
        "no_parallel_or_bar_first": static.get("no_parallel_selector") is True and static.get("no_bar_first_restore") is True,
        "full_region_kick_locks_to_root_and_fifth": static.get("full_kick_lock_slots") == ["root_on_1_locked_shadow", "fifth_on_3_locked_shadow"],
        "split_and_short_regions_root_only": static.get("split_kick_lock_slots") == ["root_on_1_locked_shadow"] and static.get("short_kick_lock_slots") == ["root_on_1_locked_shadow"],
        "kick_shadow_not_driver": static.get("kick_shadow_roles") == ["shadow_not_driver"],
        "no_pattern_numeric_values": static.get("forbidden_pattern_numeric_keys") == [],
        "runtime_blue_bossa_kick_bass_lock_passes": runtime_ok,
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
        f"- Full-region kick slots: {static.get('full_kick_lock_slots')}",
        f"- Split kick slots: {static.get('split_kick_lock_slots')}",
        f"- Short kick slots: {static.get('short_kick_lock_slots')}",
        f"- Kick low-frequency role: {static.get('kick_shadow_roles')}",
        f"- Forbidden numeric pattern keys: {static.get('forbidden_pattern_numeric_keys')}",
        "",
        "## Runtime audits",
    ]
    for audit in summary["runtime_audits"]:
        lines.extend(
            [
                f"### Blue Bossa {audit.get('choruses')}x",
                f"- note_events_by_track: {audit.get('note_events_by_track')}",
                f"- kick lock coverage: {audit.get('kick_lock_coverage_ratio')}",
                f"- kick root/fifth events: {audit.get('kick_root_events')} / {audit.get('kick_fifth_events')}",
                f"- kick velocity min/max: {audit.get('kick_min_velocity')} / {audit.get('kick_max_velocity')}",
                f"- bass velocity min/max: {audit.get('bass_min_velocity')} / {audit.get('bass_max_velocity')}",
                f"- split/short fifth kick events: {audit.get('split_or_short_fifth_kick_events')}",
                f"- four-on-floor / rock driver events: {audit.get('four_on_floor_driver_events')} / {audit.get('rock_backbeat_driver_events')}",
                f"- bass walking-like events: {audit.get('bass_walking_like_events')}",
                f"- MIDI: `{audit.get('midi_path')}`",
                "",
            ]
        )
    lines.extend(["## Acceptance", json.dumps(summary["acceptance"], indent=2, ensure_ascii=False)])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
