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
from jammate_engine.styles.bossa_nova import arrangement_policy
from jammate_engine.styles.registry import get_style

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_98"
MILESTONE_LABEL = "v2_6_98 — Engine Bossa Nova Full-Band Arrangement Arc Listening Refinement"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 22983, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 22985, "slug": "blue_bossa_5x"},
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
            "Refine the Bossa repeat-count arrangement arc at full-band level. Piano already uses the v2_6_97 arc; "
            "v2_6_98 lets bass and drums read the same arc to become softer in breath/release and gently lifted in transition phases, "
            "without adding vocabulary, creating a selector, changing core voicing, or touching API/Agent/HarmonyOS."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
        "acceptance": acceptance,
        "recommended_next_task": static_audit.get("recommended_next_task"),
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_full_band_arrangement_arc_listening_refinement_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_full_band_arrangement_arc_listening_refinement_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()
    breath = arrangement_policy.resolve_runtime_arrangement_arc_intent(2, 5)
    lift = arrangement_policy.resolve_runtime_arrangement_arc_intent(3, 5)
    release = arrangement_policy.resolve_runtime_arrangement_arc_intent(4, 5)
    breath_ref = arrangement_policy.resolve_full_band_arrangement_arc_listening_refinement(breath)
    lift_ref = arrangement_policy.resolve_full_band_arrangement_arc_listening_refinement(lift)
    release_ref = arrangement_policy.resolve_full_band_arrangement_arc_listening_refinement(release)
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "style_registered": getattr(style, "name", None) == "bossa_nova",
        "full_band_refinement_policy_active": policy.get("bossa_nova_full_band_arrangement_arc_listening_refinement_active"),
        "full_band_refinement_policy_version": policy.get("bossa_nova_full_band_arrangement_arc_listening_refinement_version"),
        "behavior_change": policy.get("bossa_nova_full_band_arrangement_arc_listening_refinement_behavior_change"),
        "no_parallel_selector": policy.get("bossa_nova_full_band_arrangement_arc_listening_refinement_no_parallel_selector"),
        "no_bar_first_restore": policy.get("bossa_nova_full_band_arrangement_arc_listening_refinement_no_bar_first_restore"),
        "no_new_pattern_vocabulary": policy.get("bossa_nova_full_band_arrangement_arc_listening_refinement_no_new_pattern_vocabulary"),
        "no_core_voicing_change": policy.get("bossa_nova_full_band_arrangement_arc_listening_refinement_no_core_voicing_change"),
        "no_api_agent_harmonyos_change": policy.get("bossa_nova_full_band_arrangement_arc_listening_refinement_no_api_agent_harmonyos_change"),
        "tracks": list(policy.get("bossa_nova_full_band_arrangement_arc_listening_refinement_tracks") or ()),
        "breath_refinement": breath_ref,
        "lift_refinement": lift_ref,
        "release_refinement": release_ref,
        "recommended_next_task": policy.get("bossa_nova_full_band_arrangement_arc_listening_refinement_recommended_next_task"),
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_full_band_arrangement_arc_listening_refinement_demo.mid"
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
        full = [event for event in events if event.metadata.get("bossa_full_band_arrangement_arc_listening_refinement_version") == MILESTONE_ID]
        return full, round(len(full) / max(1, len(events)), 4)

    piano_full, piano_ratio = _coverage(piano_events)
    bass_full, bass_ratio = _coverage(bass_events)
    drums_full, drums_ratio = _coverage(drum_events)

    bass_dynamic_profiles = Counter(str(event.metadata.get("dynamic_profile")) for event in bass_events)
    drum_dynamic_profiles = Counter(str(event.metadata.get("dynamic_profile")) for event in drum_events)
    bass_bands = Counter(str(event.metadata.get("bossa_full_band_arrangement_arc_band")) for event in bass_full)
    drum_bands = Counter(str(event.metadata.get("bossa_full_band_arrangement_arc_band")) for event in drums_full)
    piano_phases = Counter(str(event.metadata.get("bossa_nova_repeat_count_arrangement_arc_phase")) for event in piano_events)

    return {
        "planned_piano_event_count": len(piano_events),
        "planned_bass_event_count": len(bass_events),
        "planned_drum_event_count": len(drum_events),
        "piano_full_band_arc_event_count": len(piano_full),
        "bass_full_band_arc_event_count": len(bass_full),
        "drums_full_band_arc_event_count": len(drums_full),
        "piano_full_band_arc_coverage_ratio": piano_ratio,
        "bass_full_band_arc_coverage_ratio": bass_ratio,
        "drums_full_band_arc_coverage_ratio": drums_ratio,
        "piano_arc_phase_counts": dict(piano_phases),
        "bass_full_band_arc_band_counts": dict(bass_bands),
        "drum_full_band_arc_band_counts": dict(drum_bands),
        "bass_dynamic_profile_counts": dict(bass_dynamic_profiles),
        "drum_dynamic_profile_counts": dict(drum_dynamic_profiles),
        "bass_walking_like_events": sum(1 for event in bass_events if event.metadata.get("walking_bass") is not False),
        "drum_swing_or_rock_events": sum(1 for event in drum_events if event.metadata.get("swing_ride_pattern") is not False or event.metadata.get("rock_backbeat_pattern") is not False),
    }


def _acceptance(static_audit: dict[str, Any], runtime_audits: list[dict[str, Any]]) -> dict[str, Any]:
    runtime_ok = bool(runtime_audits) and all(_runtime_accepts(item) for item in runtime_audits)
    checks = {
        "style_and_policy_registered": static_audit.get("style_registered") is True
        and static_audit.get("full_band_refinement_policy_version") == MILESTONE_ID,
        "in_place_boundaries_preserved": static_audit.get("behavior_change") is True
        and static_audit.get("no_parallel_selector") is True
        and static_audit.get("no_bar_first_restore") is True
        and static_audit.get("no_new_pattern_vocabulary") is True
        and static_audit.get("no_core_voicing_change") is True
        and static_audit.get("no_api_agent_harmonyos_change") is True,
        "track_scope_is_full_band": set(static_audit.get("tracks") or []) == {"piano", "bass", "drums"},
        "refinement_profiles_are_distinct": static_audit.get("breath_refinement", {}).get("full_band_arc_band") == "breath_space"
        and static_audit.get("lift_refinement", {}).get("full_band_arc_band") == "gentle_lift"
        and static_audit.get("release_refinement", {}).get("full_band_arc_band") == "soft_release",
        "runtime_blue_bossa_full_band_arc_passes": runtime_ok,
    }
    return {"checks": checks, "passed": all(checks.values())}


def _runtime_accepts(item: dict[str, Any]) -> bool:
    bass_profiles = dict(item.get("bass_dynamic_profile_counts") or {})
    drum_profiles = dict(item.get("drum_dynamic_profile_counts") or {})
    bass_bands = dict(item.get("bass_full_band_arc_band_counts") or {})
    drum_bands = dict(item.get("drum_full_band_arc_band_counts") or {})
    return (
        bool(item.get("ok"))
        and int(item.get("piano_notes") or 0) > 0
        and int(item.get("bass_notes") or 0) > 0
        and int(item.get("drums_notes") or 0) > 0
        and float(item.get("piano_full_band_arc_coverage_ratio") or 0.0) == 1.0
        and float(item.get("bass_full_band_arc_coverage_ratio") or 0.0) == 1.0
        and float(item.get("drums_full_band_arc_coverage_ratio") or 0.0) == 1.0
        and int(item.get("bass_walking_like_events") or 0) == 0
        and int(item.get("drum_swing_or_rock_events") or 0) == 0
        and int(bass_bands.get("gentle_lift", 0)) > 0
        and int(bass_bands.get("soft_release", 0)) > 0
        and int(drum_bands.get("gentle_lift", 0)) > 0
        and int(drum_bands.get("soft_release", 0)) > 0
        and int(bass_profiles.get("bossa_root_lift", 0)) > 0
        and int(bass_profiles.get("bossa_root_release", 0)) > 0
        and int(drum_profiles.get("bossa_cross_lift", 0)) > 0
        and int(drum_profiles.get("shaker_release", 0)) > 0
        and (int(item.get("choruses") or 0) < 5 or int(bass_bands.get("breath_space", 0)) > 0)
        and (int(item.get("choruses") or 0) < 5 or int(drum_bands.get("breath_space", 0)) > 0)
        and (int(item.get("choruses") or 0) < 5 or int(bass_profiles.get("bossa_root_soft", 0)) > 0)
        and (int(item.get("choruses") or 0) < 5 or int(drum_profiles.get("shaker_breath", 0)) > 0)
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
        "## Static audit",
        "",
        f"- policy version: `{static.get('full_band_refinement_policy_version')}`",
        f"- boundaries: no parallel selector={static.get('no_parallel_selector')}, no bar-first restore={static.get('no_bar_first_restore')}, no new vocabulary={static.get('no_new_pattern_vocabulary')}, no core voicing change={static.get('no_core_voicing_change')}",
        f"- tracks: `{static.get('tracks')}`",
        f"- breath band: `{static.get('breath_refinement', {}).get('full_band_arc_band')}`",
        f"- lift band: `{static.get('lift_refinement', {}).get('full_band_arc_band')}`",
        f"- release band: `{static.get('release_refinement', {}).get('full_band_arc_band')}`",
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
                f"- full-band arc coverage piano/bass/drums: `{item['piano_full_band_arc_coverage_ratio']} / {item['bass_full_band_arc_coverage_ratio']} / {item['drums_full_band_arc_coverage_ratio']}`",
                f"- bass dynamic profiles: `{item['bass_dynamic_profile_counts']}`",
                f"- drum dynamic profiles: `{item['drum_dynamic_profile_counts']}`",
                f"- bass walking-like events: `{item['bass_walking_like_events']}`",
                f"- drum swing/rock events: `{item['drum_swing_or_rock_events']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Acceptance",
            "",
            f"- passed: `{acceptance.get('passed')}`",
            f"- checks: `{acceptance.get('checks')}`",
            "",
            "## Recommended next task",
            "",
            f"`{summary.get('recommended_next_task')}`",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
