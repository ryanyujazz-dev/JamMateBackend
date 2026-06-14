from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace
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
from jammate_engine.styles.bossa_nova import arrangement_policy, fill_policy, percussion_patterns
from jammate_engine.styles.registry import get_style

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_106"
MILESTONE_LABEL = "v2_6_106 — Engine Bossa Nova Light Marker Fill Policy"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 23106, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 23112, "slug": "blue_bossa_5x"},
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
            "Add sparse Bossa rim-click markers inside the existing percussion candidate for phrase-end, turnaround/gentle-lift, and terminal ending contexts. "
            "This is not a tom/crash/roll fill system and does not create a parallel selector, bar-first template path, piano/bass/voicing change, API, Agent, or HarmonyOS change."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
        "acceptance": acceptance,
        "recommended_next_task": static_audit.get("recommended_next_task"),
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_light_marker_fill_policy_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_light_marker_fill_policy_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    policy = arrangement_policy.get_arrangement_policy()
    marker_policy = fill_policy.get_light_marker_fill_policy()
    phrase = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "region_source_bar_index": 7})[0]
    lift_intent = arrangement_policy.resolve_runtime_arrangement_arc_intent(1, 3)
    lift = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "region_source_bar_index": 7, "bossa_nova_arrangement_arc_intent": lift_intent})[0]
    release_intent = arrangement_policy.resolve_runtime_arrangement_arc_intent(2, 3)
    release_region = SimpleNamespace(is_last_bar_of_chorus=True, is_last_bar_of_section=True, source_bar_index=7, chorus_index=2, total_choruses=3)
    release = percussion_patterns.get_pattern_candidates({"region": release_region, "region_duration_beats": 2.0, "region_source_bar_index": 7, "bossa_nova_arrangement_arc_intent": release_intent})[0]
    all_markers = _marker_events(phrase) + _marker_events(lift) + _marker_events(release)
    forbidden_numeric_keys = sorted(
        {
            key
            for event in all_markers
            for key in event.metadata
            if key in {"velocity", "duration", "duration_beats", "pedal", "midi_note", "note"}
        }
    )
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "policy_active": policy.get("bossa_nova_light_marker_fill_policy_active"),
        "policy_version": policy.get("bossa_nova_light_marker_fill_policy_version"),
        "fill_policy_version": marker_policy.get("version"),
        "no_parallel_selector": policy.get("bossa_nova_light_marker_fill_policy_no_parallel_selector"),
        "no_bar_first_restore": policy.get("bossa_nova_light_marker_fill_policy_no_bar_first_restore"),
        "no_tom_crash_roll_fill": policy.get("bossa_nova_light_marker_fill_policy_no_tom_crash_roll_fill"),
        "no_swing_or_rock_fill": policy.get("bossa_nova_light_marker_fill_policy_no_swing_or_rock_fill"),
        "no_piano_bass_voicing_change": policy.get("bossa_nova_light_marker_fill_policy_no_piano_bass_voicing_change"),
        "no_api_agent_harmonyos_change": policy.get("bossa_nova_light_marker_fill_policy_no_api_agent_harmonyos_change"),
        "allowed_marker_kinds": list(policy.get("bossa_nova_light_marker_fill_policy_allowed_marker_kinds") or ()),
        "phrase_marker_slots": [event.metadata.get("bossa_light_marker_fill_policy_slot") for event in _marker_events(phrase)],
        "lift_marker_slots": [event.metadata.get("bossa_light_marker_fill_policy_slot") for event in _marker_events(lift)],
        "ending_short_marker_slots": [event.metadata.get("bossa_light_marker_fill_policy_slot") for event in _marker_events(release)],
        "marker_drums": sorted({str(event.metadata.get("drum")) for event in all_markers}),
        "forbidden_pattern_numeric_keys": forbidden_numeric_keys,
        "recommended_next_task": policy.get("bossa_nova_light_marker_fill_policy_recommended_next_task"),
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_light_marker_fill_policy_demo.mid"
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
    marker_pairs = [(event, note) for event, note in zip(drum_events, drum_notes) if event.metadata.get("bossa_light_marker_fill_policy_active")]
    marker_events = [event for event, _ in marker_pairs]
    marker_velocities = [int(note.velocity) for _, note in marker_pairs]
    kind_counts = Counter(str(event.metadata.get("bossa_light_marker_fill_policy_kind")) for event in marker_events)
    slot_counts = Counter(str(event.metadata.get("bossa_light_marker_fill_policy_slot")) for event in marker_events)
    marker_velocity_by_kind: dict[str, list[int]] = defaultdict(list)
    for event, note in marker_pairs:
        marker_velocity_by_kind[str(event.metadata.get("bossa_light_marker_fill_policy_kind"))].append(int(note.velocity))
    marker_kind_average_velocity = {kind: round(sum(values) / len(values), 2) for kind, values in sorted(marker_velocity_by_kind.items()) if values}
    return {
        "planned_drum_event_count": len(drum_events),
        "marker_event_count": len(marker_events),
        "marker_kind_counts": dict(kind_counts),
        "marker_slot_counts": dict(slot_counts),
        "marker_coverage_ratio": round(sum(1 for event in marker_events if event.metadata.get("bossa_light_marker_fill_policy_version") == MILESTONE_ID) / max(1, len(marker_events)), 4),
        "marker_velocity_set": sorted(set(marker_velocities)),
        "marker_min_velocity": min(marker_velocities) if marker_velocities else 0,
        "marker_max_velocity": max(marker_velocities) if marker_velocities else 0,
        "marker_kind_average_velocity": marker_kind_average_velocity,
        "tom_crash_roll_marker_events": sum(1 for event in marker_events if event.metadata.get("tom_fill_pattern") is not False or event.metadata.get("crash_fill_pattern") is not False or event.metadata.get("snare_roll_fill_pattern") is not False),
        "swing_or_rock_marker_events": sum(1 for event in marker_events if event.metadata.get("swing_ride_pattern") is not False or event.metadata.get("rock_backbeat_pattern") is not False),
        "drum_swing_or_rock_events": sum(1 for event in drum_events if event.metadata.get("swing_ride_pattern") is not False or event.metadata.get("rock_backbeat_pattern") is not False),
    }


def _marker_events(candidate: Any) -> list[Any]:
    return [event for event in candidate.events if event.metadata.get("bossa_light_marker_fill_policy_active")]


def _acceptance(static: dict[str, Any], runtime_audits: list[dict[str, Any]]) -> dict[str, Any]:
    runtime_ok = bool(runtime_audits) and all(
        audit.get("ok") is True
        and int(audit.get("marker_event_count") or 0) > 0
        and float(audit.get("marker_coverage_ratio") or 0.0) == 1.0
        and "phrase_end_micro" in dict(audit.get("marker_kind_counts") or {})
        and "ending_soft" in dict(audit.get("marker_kind_counts") or {})
        and int(audit.get("tom_crash_roll_marker_events") or 0) == 0
        and int(audit.get("swing_or_rock_marker_events") or 0) == 0
        and int(audit.get("drum_swing_or_rock_events") or 0) == 0
        and 0 < int(audit.get("marker_max_velocity") or 0) <= 45
        for audit in runtime_audits
    )
    checks = {
        "policy_declares_light_marker_fill": static.get("policy_active") is True and static.get("policy_version") == MILESTONE_ID,
        "fill_policy_version_matches": static.get("fill_policy_version") == MILESTONE_ID,
        "no_parallel_or_bar_first": static.get("no_parallel_selector") is True and static.get("no_bar_first_restore") is True,
        "no_tom_crash_roll_or_swing_rock": static.get("no_tom_crash_roll_fill") is True and static.get("no_swing_or_rock_fill") is True,
        "static_marker_slots_present": bool(static.get("phrase_marker_slots")) and bool(static.get("lift_marker_slots")) and bool(static.get("ending_short_marker_slots")),
        "markers_use_cross_stick_only": static.get("marker_drums") == ["cross_stick"],
        "no_pattern_numeric_values": static.get("forbidden_pattern_numeric_keys") == [],
        "runtime_blue_bossa_light_markers_pass": runtime_ok,
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
        f"- Fill policy version: {static.get('fill_policy_version')}",
        f"- Allowed marker kinds: {static.get('allowed_marker_kinds')}",
        f"- Phrase marker slots: {static.get('phrase_marker_slots')}",
        f"- Lift marker slots: {static.get('lift_marker_slots')}",
        f"- Ending short marker slots: {static.get('ending_short_marker_slots')}",
        f"- Forbidden numeric pattern keys: {static.get('forbidden_pattern_numeric_keys')}",
        "",
        "## Runtime audits",
    ]
    for audit in summary["runtime_audits"]:
        lines.extend(
            [
                f"### Blue Bossa {audit.get('choruses')}x",
                f"- note_events_by_track: {audit.get('note_events_by_track')}",
                f"- marker event count: {audit.get('marker_event_count')}",
                f"- marker kind counts: {audit.get('marker_kind_counts')}",
                f"- marker slot counts: {audit.get('marker_slot_counts')}",
                f"- marker velocity min/max: {audit.get('marker_min_velocity')} / {audit.get('marker_max_velocity')}",
                f"- tom/crash/roll marker events: {audit.get('tom_crash_roll_marker_events')}",
                f"- swing/rock marker events: {audit.get('swing_or_rock_marker_events')}",
                f"- MIDI: `{audit.get('midi_path')}`",
                "",
            ]
        )
    lines.extend(["## Acceptance", json.dumps(summary["acceptance"], indent=2, ensure_ascii=False)])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
