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
MILESTONE_ID = "v2_6_97"
MILESTONE_LABEL = "v2_6_97 — Engine Bossa Nova Repeat-Count Arrangement Arc Policy"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
REPEAT_POLICY_CASES = (1, 2, 3, 5, 10, 50)
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 22807, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 22857, "slug": "blue_bossa_5x"},
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
            "Add a Bossa-owned repeat-count-aware arrangement arc in place. The arc shapes existing piano comping candidates "
            "for arbitrary repeat counts without creating a selector, adding vocabulary, cloning Medium Swing, changing expression numbers, "
            "or touching core voicing/API/Agent/HarmonyOS."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
        "acceptance": acceptance,
        "recommended_next_task": static_audit.get("recommended_next_task"),
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_repeat_count_arrangement_arc_policy_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_repeat_count_arrangement_arc_policy_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()
    repeat_arcs = {str(count): arrangement_policy.simulate_repeat_count_arrangement_arc(count) for count in REPEAT_POLICY_CASES}
    phase_counts = {count: dict(Counter(item["phase"] for item in arc)) for count, arc in repeat_arcs.items()}
    long_arc = repeat_arcs["50"]
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "style_registered": getattr(style, "name", None) == "bossa_nova",
        "arrangement_policy_version": policy.get("bossa_nova_repeat_count_arrangement_arc_policy_version"),
        "behavior_change": policy.get("bossa_nova_repeat_count_arrangement_arc_policy_behavior_change"),
        "no_parallel_selector": policy.get("bossa_nova_repeat_count_arrangement_arc_policy_no_parallel_selector"),
        "no_bar_first_restore": policy.get("bossa_nova_repeat_count_arrangement_arc_policy_no_bar_first_restore"),
        "no_new_pattern_vocabulary": policy.get("bossa_nova_repeat_count_arrangement_arc_policy_no_new_pattern_vocabulary"),
        "no_expression_numeric_change": policy.get("bossa_nova_repeat_count_arrangement_arc_policy_no_expression_numeric_change"),
        "no_core_voicing_change": policy.get("bossa_nova_repeat_count_arrangement_arc_policy_no_core_voicing_change"),
        "no_api_agent_harmonyos_change": policy.get("bossa_nova_repeat_count_arrangement_arc_policy_no_api_agent_harmonyos_change"),
        "not_medium_swing_clone": policy.get("bossa_nova_repeat_count_arrangement_arc_policy_not_medium_swing_clone"),
        "repeat_counts_audited": list(policy.get("bossa_nova_repeat_count_arrangement_arc_policy_repeat_counts_audited") or ()),
        "repeat_policy_arc_by_count": repeat_arcs,
        "repeat_policy_phase_counts": phase_counts,
        "long_loop_50x_has_wave_reset": any(item["phase"] == "loop_wave_reset" for item in long_arc),
        "long_loop_50x_has_breath_space": any(item["phase"] == "loop_wave_breath_space" for item in long_arc),
        "long_loop_50x_final_phase": long_arc[-1]["phase"],
        "long_loop_50x_monotonic_ramp_allowed": any(bool(item.get("monotonic_ramp_allowed")) for item in long_arc),
        "long_loop_50x_all_not_medium_swing_clone": all(bool(item.get("not_medium_swing_clone")) for item in long_arc),
        "three_chorus_not_hardcoded": [item["phase"] for item in repeat_arcs["3"]] != [item["phase"] for item in repeat_arcs["5"][:3]],
        "recommended_next_task": policy.get("bossa_nova_repeat_count_arrangement_arc_policy_recommended_next_task"),
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_repeat_count_arrangement_arc_policy_demo.mid"
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
        plan = style.plan_region(region, context={"tempo": int(score.get("tempo", 140)), "rng": rng, "style_pattern_history": history, "ensemble": {"bass_present": True}})
        piano_events.extend([event for event in plan.events if event.track == "piano"])
        bass_events.extend([event for event in plan.events if event.track == "bass"])
        drum_events.extend([event for event in plan.events if event.track == "drums"])
    piano_arc_events = [event for event in piano_events if event.metadata.get("bossa_nova_repeat_count_arrangement_arc_policy_version") == MILESTONE_ID]
    phases = Counter(str(event.metadata.get("bossa_nova_repeat_count_arrangement_arc_phase")) for event in piano_arc_events)
    runtime_intents = Counter(str(event.metadata.get("bossa_nova_repeat_count_arrangement_arc_piano_comping_runtime_intent")) for event in piano_arc_events)
    statuses = Counter(str(event.metadata.get("bossa_nova_repeat_count_arrangement_arc_status")) for event in piano_arc_events)
    multipliers = [float(event.metadata.get("bossa_nova_repeat_count_arrangement_arc_multiplier") or 0.0) for event in piano_arc_events]
    return {
        "planned_piano_event_count": len(piano_events),
        "planned_bass_event_count": len(bass_events),
        "planned_drum_event_count": len(drum_events),
        "piano_arc_event_count": len(piano_arc_events),
        "piano_arc_coverage_ratio": round(len(piano_arc_events) / max(1, len(piano_events)), 4),
        "piano_arc_phase_counts": dict(phases),
        "piano_arc_runtime_intent_counts": dict(runtime_intents),
        "piano_arc_status_counts": dict(statuses),
        "piano_arc_multiplier_min": min(multipliers) if multipliers else 0.0,
        "piano_arc_multiplier_max": max(multipliers) if multipliers else 0.0,
        "piano_arc_not_medium_swing_clone_event_count": sum(1 for event in piano_arc_events if event.metadata.get("bossa_nova_repeat_count_arrangement_arc_not_medium_swing_clone") is True),
        "piano_arc_not_three_chorus_hardcoded_event_count": sum(1 for event in piano_arc_events if event.metadata.get("bossa_nova_repeat_count_arrangement_arc_not_three_chorus_hardcoded") is True),
    }


def _acceptance(static_audit: dict[str, Any], runtime_audits: list[dict[str, Any]]) -> dict[str, Any]:
    runtime_ok = bool(runtime_audits) and all(_runtime_accepts(item) for item in runtime_audits)
    checks = {
        "style_and_policy_registered": static_audit.get("style_registered") is True
        and static_audit.get("arrangement_policy_version") == MILESTONE_ID,
        "in_place_boundaries_preserved": static_audit.get("behavior_change") is True
        and static_audit.get("no_parallel_selector") is True
        and static_audit.get("no_bar_first_restore") is True
        and static_audit.get("no_new_pattern_vocabulary") is True
        and static_audit.get("no_expression_numeric_change") is True
        and static_audit.get("no_core_voicing_change") is True
        and static_audit.get("no_api_agent_harmonyos_change") is True,
        "repeat_count_policy_is_bossa_specific": static_audit.get("not_medium_swing_clone") is True
        and static_audit.get("repeat_counts_audited") == [1, 2, 3, 5, 10, 50]
        and static_audit.get("long_loop_50x_has_wave_reset") is True
        and static_audit.get("long_loop_50x_has_breath_space") is True
        and static_audit.get("long_loop_50x_final_phase") == "final_soft_release"
        and static_audit.get("long_loop_50x_monotonic_ramp_allowed") is False
        and static_audit.get("long_loop_50x_all_not_medium_swing_clone") is True
        and static_audit.get("three_chorus_not_hardcoded") is True,
        "runtime_blue_bossa_arc_metadata_passes": runtime_ok,
    }
    return {"passed": all(checks.values()), "checks": checks}


def _runtime_accepts(item: dict[str, Any]) -> bool:
    phases = dict(item.get("piano_arc_phase_counts") or {})
    intents = dict(item.get("piano_arc_runtime_intent_counts") or {})
    return (
        item.get("ok") is True
        and int(item.get("piano_notes") or 0) > 0
        and int(item.get("bass_notes") or 0) > 0
        and int(item.get("drums_notes") or 0) > 0
        and int(item.get("planned_piano_event_count") or 0) > 0
        and int(item.get("piano_arc_event_count") or 0) == int(item.get("planned_piano_event_count") or -1)
        and float(item.get("piano_arc_coverage_ratio") or 0.0) == 1.0
        and int(item.get("piano_arc_not_medium_swing_clone_event_count") or 0) == int(item.get("piano_arc_event_count") or -1)
        and int(item.get("piano_arc_not_three_chorus_hardcoded_event_count") or 0) == int(item.get("piano_arc_event_count") or -1)
        and int(phases.get("head_in_core_identity", 0)) > 0
        and int(phases.get("final_soft_release", 0)) > 0
        and (int(phases.get("gentle_lift", 0)) > 0 or int(phases.get("loop_wave_breath_space", 0)) > 0)
        and any(key in intents for key in {"core_identity_reset", "warm_batida_flow", "breath_space", "gentle_transition_lift", "settled_release"})
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
        f"- Arrangement policy version: `{static.get('arrangement_policy_version')}`",
        f"- Repeat counts audited: `{static.get('repeat_counts_audited')}`",
        f"- Long-loop 50x has reset / breath / final release: `{static.get('long_loop_50x_has_wave_reset')}` / `{static.get('long_loop_50x_has_breath_space')}` / `{static.get('long_loop_50x_final_phase')}`",
        f"- Three-chorus hardcoded: `{not bool(static.get('three_chorus_not_hardcoded'))}`",
        f"- Medium Swing clone: `{not bool(static.get('not_medium_swing_clone'))}`",
        "",
        "## Runtime Blue Bossa audits",
        "",
    ]
    for item in summary.get("runtime_audits") or []:
        lines.extend(
            [
                f"### {item.get('choruses')} choruses / seed `{item.get('seed')}`",
                "",
                f"- MIDI: `{item.get('midi_path')}`",
                f"- Notes by track: `{item.get('note_events_by_track')}`",
                f"- Piano arc coverage: `{item.get('piano_arc_event_count')}` / `{item.get('planned_piano_event_count')}` = `{item.get('piano_arc_coverage_ratio')}`",
                f"- Piano arc phases: `{item.get('piano_arc_phase_counts')}`",
                f"- Piano runtime intents: `{item.get('piano_arc_runtime_intent_counts')}`",
                f"- Piano arc status counts: `{item.get('piano_arc_status_counts')}`",
                f"- Arc multiplier min/max: `{item.get('piano_arc_multiplier_min')}` / `{item.get('piano_arc_multiplier_max')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Acceptance",
            "",
            f"Passed: `{acceptance.get('passed')}`",
            "",
            "```json",
            json.dumps(acceptance.get("checks"), indent=2, ensure_ascii=False),
            "```",
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
