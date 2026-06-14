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
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.bossa_nova import arrangement_policy, bass_foundation_patterns
from jammate_engine.styles.registry import get_style

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_109"
MILESTONE_LABEL = "v2_6_109 — Engine Bossa Nova Bass Articulation + Register Policy"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 23110, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 23111, "slug": "blue_bossa_5x"},
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    runtime_audits = [_generate_runtime_audit(spec) for spec in DEMO_SPECS]
    summary = {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "scope": (
            "Bossa bass articulation/register refinement after v2_6_108: keep the same root/fifth/pickup/next-root candidate set, "
            "calibrate semantic length profiles for close pickups, and use existing BassFoundationRealizer register projection metadata for smooth fifths/root-repeat fallback."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
    }
    summary["acceptance"] = _acceptance(static_audit, runtime_audits)
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_bass_articulation_register_policy_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_bass_articulation_register_policy_report.md"
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
    register_policies = sorted({str(event.metadata.get("bossa_bass_register_policy")) for event in events})
    articulation_roles = sorted({str(event.metadata.get("bossa_bass_articulation_role")) for event in events})
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "policy_active": policy.get("bossa_nova_bass_articulation_and_register_policy_active"),
        "policy_version": policy.get("bossa_nova_bass_articulation_and_register_policy_version"),
        "policy_behavior_change": policy.get("bossa_nova_bass_articulation_and_register_policy_behavior_change"),
        "no_parallel_selector": policy.get("bossa_nova_bass_articulation_and_register_policy_no_parallel_selector"),
        "no_new_bass_engine": policy.get("bossa_nova_bass_articulation_and_register_policy_no_new_bass_engine"),
        "no_bar_first_restore": policy.get("bossa_nova_bass_articulation_and_register_policy_no_bar_first_restore"),
        "no_walking_bass": policy.get("bossa_nova_bass_articulation_and_register_policy_no_walking_bass"),
        "no_piano_pattern_change": policy.get("bossa_nova_bass_articulation_and_register_policy_no_piano_pattern_change"),
        "no_core_voicing_change": policy.get("bossa_nova_bass_articulation_and_register_policy_no_core_voicing_change"),
        "no_api_agent_harmonyos_change": policy.get("bossa_nova_bass_articulation_and_register_policy_no_api_agent_harmonyos_change"),
        "full_candidate_names": [candidate.name for candidate in full_candidates],
        "full_candidate_count": len(full_candidates),
        "register_policies": register_policies,
        "articulation_roles": articulation_roles,
        "all_events_have_v2_6_109_metadata": all(event.metadata.get("bossa_bass_articulation_and_register_policy_version") == MILESTONE_ID for event in events),
        "has_pickup_register_policy": "pickup_fifth_nearest_continuity" in register_policies,
        "has_main_fifth_register_policy": "main_fifth_nearest_with_root_repeat_fallback" in register_policies,
        "has_next_root_register_policy": "next_root_light_nearest_continuity" in register_policies,
        "split_region_degrees": [event.metadata.get("degree") for event in split_candidate.events],
        "short_region_degrees": [event.metadata.get("degree") for event in short_candidate.events],
        "forbidden_pattern_numeric_keys": forbidden_numeric_keys,
        "recommended_next_task": policy.get("bossa_nova_bass_articulation_and_register_policy_recommended_next_task"),
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_bass_articulation_register_policy_demo.mid"
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

    active_bass = sorted([event for event in bass_events if event.status == "active"], key=lambda event: (event.onset_beat, event.event_id))
    bass_notes = BassFoundationRealizer().realize(active_bass)
    by_role: dict[str, list[float]] = defaultdict(list)
    by_degree: Counter[str] = Counter()
    notes_by_degree: dict[str, list[int]] = defaultdict(list)
    register_policies: Counter[str] = Counter()
    versioned = 0
    for event, note in zip(active_bass, bass_notes):
        role = str(event.metadata.get("bossa_bass_articulation_role") or "unknown")
        degree = str(event.metadata.get("degree") or "unknown")
        by_role[role].append(float(note.duration_beats))
        by_degree[degree] += 1
        notes_by_degree[degree].append(int(note.note))
        register_policies[str(event.metadata.get("bossa_bass_register_policy") or "unknown")] += 1
        if event.metadata.get("bossa_bass_articulation_and_register_policy_version") == MILESTONE_ID:
            versioned += 1

    consecutive_leaps = [abs(bass_notes[index].note - bass_notes[index - 1].note) for index in range(1, len(bass_notes))]
    pickup_events = [event for event in active_bass if event.local_beat == 1.5 and event.metadata.get("degree") == "fifth"]
    next_root_events = [event for event in active_bass if event.local_beat == 3.5 and event.metadata.get("degree") == "next_root"]
    split_short_non_root = [
        event
        for event in active_bass
        if float(event.metadata.get("region_duration_beats", 4.0)) <= 2.25 and event.metadata.get("degree") != "root"
    ]
    terminal_next_root = [
        event
        for event in next_root_events
        if event.metadata.get("region_is_last_bar_of_chorus")
        and int(event.metadata.get("region_chorus_index") or 0) >= int(event.metadata.get("region_total_choruses") or 1) - 1
    ]
    walking_like = [
        event
        for event in active_bass
        if event.metadata.get("walking_bass") is not False
        or event.metadata.get("degree") not in {"root", "fifth", "next_root"}
        or event.local_beat not in {0.0, 1.5, 2.0, 3.5}
    ]
    kick_pickup_follow = [event for event in drum_events if event.metadata.get("drum") == "kick" and event.local_beat in {1.5, 3.5}]

    def _range(values: list[float]) -> list[float]:
        return [round(min(values), 3), round(max(values), 3)] if values else [0, 0]

    return {
        "bass_event_count": len(active_bass),
        "bass_degree_counts": dict(by_degree),
        "bass_articulation_version_coverage": f"{versioned}/{len(active_bass)}",
        "bass_articulation_version_coverage_ratio": round(versioned / max(1, len(active_bass)), 4),
        "bass_duration_ranges_by_articulation_role": {role: _range(values) for role, values in sorted(by_role.items())},
        "bass_register_policy_counts": dict(register_policies),
        "bass_note_ranges_by_degree": {degree: [min(values), max(values)] if values else [0, 0] for degree, values in sorted(notes_by_degree.items())},
        "max_consecutive_bass_leap": max(consecutive_leaps or [0]),
        "pickup_2and_event_count": len(pickup_events),
        "next_root_4and_event_count": len(next_root_events),
        "split_short_non_root_events": len(split_short_non_root),
        "terminal_next_root_events": len(terminal_next_root),
        "walking_like_bass_events": len(walking_like),
        "kick_pickup_follow_events": len(kick_pickup_follow),
    }


def _acceptance(static: dict[str, Any], runtime_audits: list[dict[str, Any]]) -> dict[str, Any]:
    runtime_ok = bool(runtime_audits) and all(
        audit.get("ok") is True
        and float(audit.get("bass_articulation_version_coverage_ratio") or 0.0) == 1.0
        and int(audit.get("pickup_2and_event_count") or 0) > 0
        and int(audit.get("next_root_4and_event_count") or 0) > 0
        and int(audit.get("split_short_non_root_events") or 0) == 0
        and int(audit.get("terminal_next_root_events") or 0) == 0
        and int(audit.get("walking_like_bass_events") or 0) == 0
        and int(audit.get("kick_pickup_follow_events") or 0) == 0
        and int(audit.get("max_consecutive_bass_leap") or 0) <= 12
        for audit in runtime_audits
    )
    checks = {
        "policy_declares_bass_articulation_register": static.get("policy_active") is True and static.get("policy_version") == MILESTONE_ID,
        "no_new_parallel_bass_engine_or_bar_first": static.get("no_parallel_selector") is True and static.get("no_new_bass_engine") is True and static.get("no_bar_first_restore") is True,
        "no_walking_or_cross_track_change": static.get("no_walking_bass") is True and static.get("no_piano_pattern_change") is True and static.get("no_core_voicing_change") is True and static.get("no_api_agent_harmonyos_change") is True,
        "pattern_metadata_declares_articulation_and_register": static.get("all_events_have_v2_6_109_metadata") is True and static.get("has_pickup_register_policy") is True and static.get("has_main_fifth_register_policy") is True and static.get("has_next_root_register_policy") is True,
        "split_short_regions_root_only": static.get("split_region_degrees") == ["root"] and static.get("short_region_degrees") == ["root"],
        "no_pattern_numeric_values": static.get("forbidden_pattern_numeric_keys") == [],
        "runtime_blue_bossa_bass_articulation_register_pass": runtime_ok,
    }
    return {"passed": all(checks.values()), "checks": checks}


def _render_report(summary: dict[str, Any]) -> str:
    lines = [
        f"# {MILESTONE_LABEL}",
        "",
        f"Engine tag: `{summary.get('engine_version_tag')}`",
        "",
        "## Scope",
        "",
        str(summary.get("scope")),
        "",
        "## Acceptance",
        "",
        f"Passed: `{summary['acceptance']['passed']}`",
        "",
        "## Runtime audits",
        "",
    ]
    for audit in summary.get("runtime_audits", []):
        lines.extend(
            [
                f"### Blue Bossa {audit.get('choruses')}x",
                "",
                f"- MIDI: `{audit.get('midi_path')}`",
                f"- Notes piano/bass/drums: `{audit.get('piano_notes')}` / `{audit.get('bass_notes')}` / `{audit.get('drums_notes')}`",
                f"- Bass articulation coverage: `{audit.get('bass_articulation_version_coverage')}`",
                f"- Bass degree counts: `{audit.get('bass_degree_counts')}`",
                f"- Duration ranges by role: `{audit.get('bass_duration_ranges_by_articulation_role')}`",
                f"- Register policy counts: `{audit.get('bass_register_policy_counts')}`",
                f"- Note ranges by degree: `{audit.get('bass_note_ranges_by_degree')}`",
                f"- Max consecutive bass leap: `{audit.get('max_consecutive_bass_leap')}`",
                f"- split/short non-root: `{audit.get('split_short_non_root_events')}`; terminal next-root: `{audit.get('terminal_next_root_events')}`; walking-like: `{audit.get('walking_like_bass_events')}`; kick pickup-follow: `{audit.get('kick_pickup_follow_events')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Recommendation",
            "",
            str(summary.get("static_audit", {}).get("recommended_next_task")),
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
