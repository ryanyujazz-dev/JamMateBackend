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
from jammate_engine.styles.bossa_nova import arrangement_policy, bass_foundation_patterns, percussion_patterns
from jammate_engine.styles.registry import get_style

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_96"
MILESTONE_LABEL = "v2_6_96 — Engine Bossa Nova Bass + Drums Identity Audit"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 22706, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 22756, "slug": "blue_bossa_5x"},
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
            "Replace the old Bossa bass one-size root/fifth pattern and drums hihat placeholder in place. "
            "Bass now declares root/fifth support for full regions and root-only support for split/short ChordRegions; drums now declare region-local shaker/cross-stick/light-kick identity. "
            "No piano vocabulary change, no parallel selector, no core voicing, API, Agent, or HarmonyOS change."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
        "acceptance": acceptance,
        "recommended_next_task": static_audit.get("recommended_next_task"),
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_bass_and_drums_identity_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_bass_and_drums_identity_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()
    full_bass = bass_foundation_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "bar_index": 0})[0]
    split_bass = bass_foundation_patterns.get_pattern_candidates({"region_duration_beats": 2.0, "bar_index": 0})[0]
    short_bass = bass_foundation_patterns.get_pattern_candidates({"region_duration_beats": 1.0, "bar_index": 0})[0]
    full_drums = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "bar_index": 0})[0]
    split_drums = percussion_patterns.get_pattern_candidates({"region_duration_beats": 2.0, "bar_index": 0})[0]
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "style_registered": getattr(style, "name", None) == "bossa_nova",
        "arrangement_policy_version": policy.get("bossa_nova_bass_and_drums_identity_audit_version"),
        "behavior_change": policy.get("bossa_nova_bass_and_drums_identity_audit_behavior_change"),
        "no_parallel_selector": policy.get("bossa_nova_bass_and_drums_identity_audit_no_parallel_selector"),
        "no_bar_first_restore": policy.get("bossa_nova_bass_and_drums_identity_audit_no_bar_first_restore"),
        "no_piano_pattern_change": policy.get("bossa_nova_bass_and_drums_identity_audit_no_piano_pattern_change"),
        "no_expression_numeric_change": policy.get("bossa_nova_bass_and_drums_identity_audit_no_expression_numeric_change"),
        "no_core_voicing_change": policy.get("bossa_nova_bass_and_drums_identity_audit_no_core_voicing_change"),
        "no_api_agent_harmonyos_change": policy.get("bossa_nova_bass_and_drums_identity_audit_no_api_agent_harmonyos_change"),
        "bass_identity": policy.get("bossa_nova_bass_identity"),
        "drums_identity": policy.get("bossa_nova_drums_identity"),
        "full_bass_candidate": _candidate_summary(full_bass),
        "split_bass_candidate": _candidate_summary(split_bass),
        "short_bass_candidate": _candidate_summary(short_bass),
        "full_drums_candidate": _candidate_summary(full_drums),
        "split_drums_candidate": _candidate_summary(split_drums),
        "recommended_next_task": policy.get("bossa_nova_bass_and_drums_identity_audit_recommended_next_task"),
    }


def _candidate_summary(candidate: Any) -> dict[str, Any]:
    return {
        "name": candidate.name,
        "category": candidate.category,
        "rhythm_beats": list(candidate.rhythm_beats),
        "tags": list(candidate.tags),
        "metadata": dict(candidate.metadata),
        "event_metadata": [dict(event.metadata) for event in candidate.events],
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_bass_and_drums_identity_demo.mid"
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
    history: dict[str, str] = {}
    bass_events = []
    drum_events = []
    for region in timeline.regions:
        plan = style.plan_region(region, context={"tempo": int(score.get("tempo", 140)), "rng": rng, "style_pattern_history": history})
        bass_events.extend([event for event in plan.events if event.track == "bass"])
        drum_events.extend([event for event in plan.events if event.track == "drums"])
    bass_degrees = Counter(str(event.metadata.get("degree")) for event in bass_events)
    bass_length_profiles = Counter(str(event.metadata.get("length_profile")) for event in bass_events)
    bass_dynamic_profiles = Counter(str(event.metadata.get("dynamic_profile")) for event in bass_events)
    bass_identity_versions = Counter(str(event.metadata.get("bossa_bass_and_drums_identity_audit_version")) for event in bass_events)
    walking_like_events = [event for event in bass_events if bool(event.metadata.get("walking_bass")) or str(event.metadata.get("length_profile")) == "walking_quarter"]
    short_region_non_root_events = [
        event
        for event in bass_events
        if str(event.metadata.get("bass_region_duration_family")) in {"split_region", "very_short_region"}
        and str(event.metadata.get("degree")) != "root"
    ]
    drum_voices = Counter(str(event.metadata.get("bossa_drum_voice")) for event in drum_events)
    drum_kinds = Counter(str(event.metadata.get("drum")) for event in drum_events)
    drum_identity_versions = Counter(str(event.metadata.get("bossa_bass_and_drums_identity_audit_version")) for event in drum_events)
    swing_ride_or_rock_events = [
        event
        for event in drum_events
        if bool(event.metadata.get("swing_ride_pattern"))
        or bool(event.metadata.get("rock_backbeat_pattern"))
        or str(event.metadata.get("drum")) in {"ride", "ride_bell"}
    ]
    return {
        "planned_bass_event_count": len(bass_events),
        "planned_bass_degree_counts": dict(bass_degrees),
        "planned_bass_length_profile_counts": dict(bass_length_profiles),
        "planned_bass_dynamic_profile_counts": dict(bass_dynamic_profiles),
        "planned_bass_identity_versions": dict(bass_identity_versions),
        "planned_bass_walking_like_event_count": len(walking_like_events),
        "planned_bass_short_region_non_root_event_count": len(short_region_non_root_events),
        "planned_drum_event_count": len(drum_events),
        "planned_drum_voice_counts": dict(drum_voices),
        "planned_drum_kind_counts": dict(drum_kinds),
        "planned_drum_identity_versions": dict(drum_identity_versions),
        "planned_drum_swing_ride_or_rock_event_count": len(swing_ride_or_rock_events),
    }


def _acceptance(static_audit: dict[str, Any], runtime_audits: list[dict[str, Any]]) -> dict[str, Any]:
    runtime_ok = bool(runtime_audits) and all(_runtime_accepts(item) for item in runtime_audits)
    full_bass = static_audit["full_bass_candidate"]
    split_bass = static_audit["split_bass_candidate"]
    full_drums = static_audit["full_drums_candidate"]
    checks = {
        "style_and_policy_registered": static_audit.get("style_registered") is True
        and static_audit.get("arrangement_policy_version") == MILESTONE_ID,
        "in_place_boundaries_preserved": static_audit.get("behavior_change") is True
        and static_audit.get("no_parallel_selector") is True
        and static_audit.get("no_bar_first_restore") is True
        and static_audit.get("no_piano_pattern_change") is True
        and static_audit.get("no_expression_numeric_change") is True
        and static_audit.get("no_core_voicing_change") is True
        and static_audit.get("no_api_agent_harmonyos_change") is True,
        "bass_static_identity_declared": static_audit.get("bass_identity") == "root_fifth_support_not_walking"
        and full_bass["rhythm_beats"] == [0.0, 2.0]
        and split_bass["rhythm_beats"] == [0.0]
        and all(event.get("walking_bass") is False for event in full_bass["event_metadata"]),
        "drums_static_identity_declared": static_audit.get("drums_identity") == "shaker_cross_stick_light_kick"
        and "shaker" in full_drums["tags"]
        and "cross_stick" in full_drums["tags"]
        and "light_kick" in full_drums["tags"],
        "runtime_blue_bossa_full_band_identity_passes": runtime_ok,
    }
    return {"passed": all(checks.values()), "checks": checks}


def _runtime_accepts(item: dict[str, Any]) -> bool:
    drum_voices = dict(item.get("planned_drum_voice_counts") or {})
    bass_degrees = dict(item.get("planned_bass_degree_counts") or {})
    bass_versions = dict(item.get("planned_bass_identity_versions") or {})
    drum_versions = dict(item.get("planned_drum_identity_versions") or {})
    return (
        item.get("ok") is True
        and int(item.get("piano_notes") or 0) > 0
        and int(item.get("bass_notes") or 0) > 0
        and int(item.get("drums_notes") or 0) > 0
        and int(item.get("planned_bass_event_count") or 0) > 0
        and int(item.get("planned_drum_event_count") or 0) > 0
        and int(bass_degrees.get("root", 0)) > 0
        and int(bass_degrees.get("fifth", 0)) > 0
        and int(item.get("planned_bass_walking_like_event_count") or 0) == 0
        and int(item.get("planned_bass_short_region_non_root_event_count") or 0) == 0
        and bass_versions.get(MILESTONE_ID, 0) == item.get("planned_bass_event_count")
        and any(key.startswith("shaker") for key in drum_voices)
        and any(key.startswith("cross_stick") for key in drum_voices)
        and int(drum_voices.get("soft_kick_root_shadow", 0)) > 0
        and int(item.get("planned_drum_swing_ride_or_rock_event_count") or 0) == 0
        and drum_versions.get(MILESTONE_ID, 0) == item.get("planned_drum_event_count")
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
        f"- Bass identity: `{static.get('bass_identity')}`",
        f"- Drums identity: `{static.get('drums_identity')}`",
        f"- Full-region bass candidate: `{static.get('full_bass_candidate', {}).get('name')}`",
        f"- Split-region bass candidate: `{static.get('split_bass_candidate', {}).get('name')}`",
        f"- Full-region drums candidate: `{static.get('full_drums_candidate', {}).get('name')}`",
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
                f"- Planned bass degrees: `{item.get('planned_bass_degree_counts')}`",
                f"- Planned bass length profiles: `{item.get('planned_bass_length_profile_counts')}`",
                f"- Bass walking-like / short-region non-root events: `{item.get('planned_bass_walking_like_event_count')}` / `{item.get('planned_bass_short_region_non_root_event_count')}`",
                f"- Planned drum voices: `{item.get('planned_drum_voice_counts')}`",
                f"- Planned drum kinds: `{item.get('planned_drum_kind_counts')}`",
                f"- Drum swing/rock placeholder events: `{item.get('planned_drum_swing_ride_or_rock_event_count')}`",
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
