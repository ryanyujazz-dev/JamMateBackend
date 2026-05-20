from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.medium_swing import arrangement_policy, comping_patterns

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_80"
MILESTONE_LABEL = "v2_6_80 — Medium Swing 2-Beat Region Density Relief + Anticipation Audit"

SPECS: tuple[dict[str, Any], ...] = (
    {"slug": "all_the_things_you_are", "leadsheet": "all_the_things_you_are.json", "seed": 3790},
    {"slug": "autumn_leaves", "leadsheet": "autumn_leaves.json", "seed": 3791},
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    outputs = [_generate_and_audit(spec) for spec in SPECS]
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": (
            "Relax Medium Swing piano in dense 2-beat ChordRegions and audit the generic region-first anticipation path on both "
            "All The Things You Are and Autumn Leaves. This stays in the style-owned candidate weighting layer and does not change "
            "core voicing internals, expression numeric values, rhythm vocabulary, API, Agent, or HarmonyOS."
        ),
        "static_audit": static_audit,
        "outputs": outputs,
        "aggregate": _aggregate(outputs),
    }
    summary["acceptance"] = _acceptance(static_audit, outputs, summary["aggregate"])
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_two_beat_density_relief_and_anticipation_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_two_beat_density_relief_and_anticipation_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": summary["acceptance"]}, indent=2, ensure_ascii=False))
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    policy = arrangement_policy.get_arrangement_policy()
    two_beat_candidates = tuple(comping_patterns.get_pattern_candidates({"region_duration_beats": 2.0}))
    return {
        "checkpoint_version": MILESTONE_ID,
        "policy_enabled": bool(policy.get("piano_comping_two_beat_region_density_relief_policy")),
        "policy_version": policy.get("piano_comping_two_beat_region_density_relief_policy_version"),
        "policy_contract": policy.get("piano_comping_two_beat_region_density_relief_policy_contract"),
        "anticipation_checkpoint_version": policy.get("piano_region_first_anticipation_compatibility_checkpoint_version"),
        "anticipation_contract": policy.get("piano_region_first_anticipation_compatibility_contract"),
        "two_beat_candidate_count": len(two_beat_candidates),
        "two_beat_candidate_names": [candidate.name for candidate in two_beat_candidates],
        "bar_first_two_chord_bar_markers": [
            candidate.name
            for candidate in two_beat_candidates
            if "two_chord_bar" in " ".join([candidate.name, candidate.category, str(candidate.metadata), " ".join(candidate.tags)])
        ],
    }


def _explicit_voicing_capability_usage_override() -> dict[str, Any]:
    return {
        "enabled": True,
        "metadata": {
            "medium_swing_existing_voicing_capability_usage_policy": {
                "version": MILESTONE_ID,
                "available": True,
                "enabled": True,
                "activation": "explicit_v2_6_80_two_beat_density_relief_audit_demo",
                "scope": "event_scoped_style_policy_only",
                "ordinary_body": "keep_open_drop_4note",
                "authorized_scenes": ["final_chorus_section_tail_support", "final_ending_climax"],
                "requested_existing_contracts": [
                    "spread_2plus3_contract",
                    "spread_2plus4_contract",
                    "spread_3plus3_contract",
                ],
                "no_core_voicing_change": True,
                "ordinary_runtime_default": False,
            },
        },
    }


def _generate_and_audit(spec: Mapping[str, Any]) -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / str(spec["leadsheet"])).read_text(encoding="utf-8"))
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_medium_swing_two_beat_density_relief_and_anticipation_demo.mid"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": int(score.get("tempo", 132)),
            "choruses": 3,
            "seed": int(spec["seed"]),
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True, "drums_present": True, "piano_present": True},
            "voicing_override": _explicit_voicing_capability_usage_override(),
        }
    )
    debug = dict(result.debug)
    piano_rows = _piano_pattern_rows(debug)
    active_rows = [row for row in piano_rows if row["status"] == "active"]
    two_beat_rows = [row for row in active_rows if row.get("region_length_family") == "two_beat_region"]
    two_beat_relief_rows = [row for row in two_beat_rows if row.get("two_beat_relief_applied")]
    multi_touch_two_beat_rows = [row for row in two_beat_relief_rows if int(row.get("two_beat_relief_event_count") or 0) > 1]
    start_anchor_two_beat_rows = [row for row in two_beat_relief_rows if row.get("two_beat_relief_status") == "simple_anchor_preferred"]
    anticipation_rows = [row for row in active_rows if row.get("anticipation_kind") == "next_beat1_to_previous_tail"]
    invalid_anticipations = [row for row in anticipation_rows if not _valid_region_first_anticipation(row)]
    two_beat_anticipations = [row for row in anticipation_rows if row.get("anticipation_previous_region_duration_beats") == 2.0]
    note_counts = dict(debug.get("note_events_by_track") or {})
    return {
        "ok": bool(result.ok),
        "title": score.get("title"),
        "slug": slug,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "note_events_by_track": note_counts,
        "piano_active_pattern_events": len(active_rows),
        "piano_two_beat_active_events": len(two_beat_rows),
        "two_beat_density_relief_applied_events": len(two_beat_relief_rows),
        "two_beat_start_anchor_events": len(start_anchor_two_beat_rows),
        "two_beat_multi_touch_events": len(multi_touch_two_beat_rows),
        "two_beat_delayed_only_events": sum(1 for row in two_beat_relief_rows if row.get("two_beat_relief_status") == "delayed_only_short_region_downweighted"),
        "two_beat_anchor_ratio": round(len(start_anchor_two_beat_rows) / max(1, len(two_beat_relief_rows)), 4),
        "two_beat_multi_touch_ratio": round(len(multi_touch_two_beat_rows) / max(1, len(two_beat_relief_rows)), 4),
        "two_beat_pattern_counts": dict(Counter(str(row.get("pattern_id")) for row in two_beat_rows)),
        "two_beat_relief_status_counts": dict(Counter(str(row.get("two_beat_relief_status")) for row in two_beat_relief_rows)),
        "active_anticipation_count": len(anticipation_rows),
        "two_beat_previous_tail_anticipation_count": len(two_beat_anticipations),
        "anticipation_target_counts": dict(Counter(f"prev_{row.get('anticipation_previous_region_duration_beats')}_target_{row.get('anticipation_target_local_beat_in_previous')}" for row in anticipation_rows)),
        "invalid_region_first_anticipations": invalid_anticipations[:10],
        "sample_anticipations": anticipation_rows[:8],
        "low_register_dense_events": sum(1 for row in _piano_voicing_rows(debug) if int(row.get("notes_below_c3") or 0) > 1),
        "voice_leading_warning_events": sum(1 for row in _piano_voicing_rows(debug) if row.get("top_voice_leap_exceeds_max")),
    }


def _piano_pattern_rows(debug: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in debug.get("piano_musical_audit_events") or []:
        event = dict((raw or {}).get("pattern_event") or {})
        if event.get("track") != "piano":
            continue
        metadata = dict(event.get("metadata") or {})
        anticipation = dict(metadata.get("anticipation") or {})
        rows.append(
            {
                "event_id": event.get("event_id"),
                "status": event.get("status"),
                "pattern_id": event.get("pattern_id"),
                "onset_beat": _to_float(event.get("onset_beat")),
                "local_beat": _to_float(event.get("local_beat")),
                "region_length_family": metadata.get("region_length_family"),
                "region_performance_bar_index": metadata.get("region_performance_bar_index"),
                "two_beat_relief_applied": bool(metadata.get("two_beat_region_density_relief_policy_applied")),
                "two_beat_relief_status": metadata.get("two_beat_region_density_relief_status"),
                "two_beat_relief_multiplier": metadata.get("two_beat_region_density_relief_multiplier"),
                "two_beat_relief_event_count": metadata.get("two_beat_region_density_relief_event_count"),
                "two_beat_relief_reasons": tuple(metadata.get("two_beat_region_density_relief_reasons") or ()),
                "anticipation_kind": anticipation.get("kind"),
                "anticipation_policy": anticipation.get("policy"),
                "anticipation_previous_region_duration_beats": _to_float(anticipation.get("previous_region_duration_beats")),
                "anticipation_current_region_duration_beats": _to_float(anticipation.get("current_region_duration_beats")),
                "anticipation_target_local_beat_in_previous": _to_float(anticipation.get("target_local_beat_in_previous")),
                "anticipation_previous_region_last_beat_local": _to_float(anticipation.get("previous_region_last_beat_local")),
                "anticipation_previous_region_last_upbeat_local": _to_float(anticipation.get("previous_region_last_upbeat_local")),
                "anticipation_tail_checked_local_beats": tuple(anticipation.get("tail_checked_local_beats") or ()),
                "anticipation_region_first_version": anticipation.get("region_first_anticipation_compatibility_checkpoint_version"),
                "anticipation_bar_first_4and_assumption": anticipation.get("bar_first_4and_assumption"),
            }
        )
    return sorted(rows, key=lambda row: (float(row.get("onset_beat") or 0.0), str(row.get("event_id"))))


def _piano_voicing_rows(debug: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in debug.get("piano_musical_audit_events") or []:
        event = dict((raw or {}).get("pattern_event") or {})
        if event.get("track") != "piano":
            continue
        voicing = dict((raw or {}).get("voicing") or {})
        notes = [int(note.get("midi_note")) for note in voicing.get("notes") or [] if note.get("midi_note") is not None]
        voice_leading = dict(voicing.get("voice_leading_profile") or {})
        rows.append(
            {
                "notes_below_c3": sum(1 for note in notes if int(note) < 48),
                "top_voice_leap_exceeds_max": bool(voice_leading.get("top_voice_leap_exceeds_max")),
            }
        )
    return rows


def _valid_region_first_anticipation(row: Mapping[str, Any]) -> bool:
    if row.get("anticipation_region_first_version") != "v2_6_61":
        return False
    if row.get("anticipation_bar_first_4and_assumption") is not False:
        return False
    previous_duration = row.get("anticipation_previous_region_duration_beats")
    target = row.get("anticipation_target_local_beat_in_previous")
    last_beat = row.get("anticipation_previous_region_last_beat_local")
    last_upbeat = row.get("anticipation_previous_region_last_upbeat_local")
    checked = tuple(row.get("anticipation_tail_checked_local_beats") or ())
    if previous_duration is None or target is None:
        return False
    expected_last_beat = round(max(0.0, float(previous_duration) - 1.0), 6)
    expected_last_upbeat = round(max(0.0, float(previous_duration) - 0.5), 6)
    return (
        round(float(target), 6) == expected_last_upbeat
        and round(float(last_beat or 0.0), 6) == expected_last_beat
        and round(float(last_upbeat or 0.0), 6) == expected_last_upbeat
        and tuple(round(float(item), 6) for item in checked) == (expected_last_beat, expected_last_upbeat)
    )


def _aggregate(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    total_piano = sum(int(output.get("piano_active_pattern_events") or 0) for output in outputs)
    total_two = sum(int(output.get("piano_two_beat_active_events") or 0) for output in outputs)
    total_two_multi = sum(int(output.get("two_beat_multi_touch_events") or 0) for output in outputs)
    total_two_anchor = sum(int(output.get("two_beat_start_anchor_events") or 0) for output in outputs)
    return {
        "piano_active_pattern_events": total_piano,
        "piano_two_beat_active_events": total_two,
        "two_beat_multi_touch_events": total_two_multi,
        "two_beat_start_anchor_events": total_two_anchor,
        "two_beat_multi_touch_ratio": round(total_two_multi / max(1, total_two), 4),
        "two_beat_anchor_ratio": round(total_two_anchor / max(1, total_two), 4),
        "active_anticipation_count": sum(int(output.get("active_anticipation_count") or 0) for output in outputs),
        "two_beat_previous_tail_anticipation_count": sum(int(output.get("two_beat_previous_tail_anticipation_count") or 0) for output in outputs),
        "low_register_dense_events": sum(int(output.get("low_register_dense_events") or 0) for output in outputs),
        "voice_leading_warning_events": sum(int(output.get("voice_leading_warning_events") or 0) for output in outputs),
    }


def _acceptance(static: Mapping[str, Any], outputs: list[dict[str, Any]], aggregate: Mapping[str, Any]) -> dict[str, Any]:
    by_slug = {str(output.get("slug")): output for output in outputs}
    autumn = by_slug.get("autumn_leaves", {})
    all_things = by_slug.get("all_the_things_you_are", {})
    checks = [
        {"name": "v2_6_80 two-beat relief policy declared", "passed": static.get("policy_version") == MILESTONE_ID and bool(static.get("policy_enabled"))},
        {"name": "no bar-first/two-chord-bar candidates", "passed": not static.get("bar_first_two_chord_bar_markers")},
        {"name": "All The Things generated and audited", "passed": bool(all_things.get("ok"))},
        {"name": "Autumn Leaves generated and audited", "passed": bool(autumn.get("ok"))},
        {"name": "Autumn Leaves two-beat comping relieved below v2_6_79 density", "passed": int(autumn.get("piano_active_pattern_events", 999)) <= 205},
        {"name": "Autumn Leaves multi-touch two-beat events are rare", "passed": int(autumn.get("two_beat_multi_touch_events", 999)) <= 8},
        {"name": "Autumn Leaves simple two-beat anchors dominate", "passed": float(autumn.get("two_beat_anchor_ratio") or 0.0) >= 0.70},
        {"name": "All The Things two-beat density also stays relaxed", "passed": int(all_things.get("two_beat_multi_touch_events", 999)) <= 4},
        {"name": "generic anticipation active on both tunes", "passed": int(all_things.get("active_anticipation_count") or 0) > 0 and int(autumn.get("active_anticipation_count") or 0) > 0},
        {"name": "2-beat previous-region anticipation observed", "passed": int(aggregate.get("two_beat_previous_tail_anticipation_count") or 0) > 0},
        {"name": "no invalid region-first anticipation rows", "passed": all(not output.get("invalid_region_first_anticipations") for output in outputs)},
        {"name": "low-register clarity preserved", "passed": int(aggregate.get("low_register_dense_events") or 0) == 0},
        {"name": "voice-leading remains calm", "passed": int(aggregate.get("voice_leading_warning_events") or 0) == 0},
    ]
    return {"passed": all(item["passed"] for item in checks), "checks": checks}


def _render_report(summary: Mapping[str, Any]) -> str:
    lines = [
        f"# {summary['milestone']}",
        "",
        str(summary["scope"]),
        "",
        f"Acceptance Passed: **{summary['acceptance']['passed']}**",
        "",
        "## Aggregate",
        "",
        "```json",
        json.dumps(summary["aggregate"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Outputs",
        "",
    ]
    for output in summary["outputs"]:
        lines.extend(
            [
                f"### {output['title']}",
                "",
                f"- MIDI: `{output['midi_path']}`",
                f"- Piano active pattern events: {output['piano_active_pattern_events']}",
                f"- 2-beat active events: {output['piano_two_beat_active_events']}",
                f"- 2-beat start anchors: {output['two_beat_start_anchor_events']}",
                f"- 2-beat multi-touch events: {output['two_beat_multi_touch_events']}",
                f"- Active anticipations: {output['active_anticipation_count']}",
                f"- 2-beat previous-tail anticipations: {output['two_beat_previous_tail_anticipation_count']}",
                f"- Invalid region-first anticipations: {len(output['invalid_region_first_anticipations'])}",
                "",
            ]
        )
    lines.extend(["## Acceptance", ""])
    for check in summary["acceptance"]["checks"]:
        mark = "✅" if check["passed"] else "❌"
        lines.append(f"- {mark} {check['name']}")
    lines.append("")
    return "\n".join(lines)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    main()
