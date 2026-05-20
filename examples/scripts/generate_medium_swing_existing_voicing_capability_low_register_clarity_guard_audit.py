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
from jammate_engine.styles.medium_swing import arrangement_policy, comping_patterns, voicing_policy

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_78"
MILESTONE_LABEL = "v2_6_78 — Medium Swing Existing Voicing Capability Low Register Clarity Guard"
FORBIDDEN_PATTERN_EXPRESSION_KEYS = {"velocity", "duration", "duration_beats", "pedal", "release_beats", "accent", "midi_note"}
FORBIDDEN_PATTERN_VOICING_KEYS = {
    "midi_notes",
    "notes",
    "degrees",
    "chord_tones",
    "voicing",
    "voicing_degrees",
    "content_family",
    "disposition",
    "projection_method",
}
SPECS: tuple[dict[str, Any], ...] = (
    {"slug": "all_the_things_you_are", "leadsheet": "all_the_things_you_are.json", "seed": 3710},
    {"slug": "autumn_leaves", "leadsheet": "autumn_leaves.json", "seed": 3711},
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    outputs = [_generate_and_audit(spec) for spec in SPECS]
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": (
            "Medium Swing keeps v2_6_77 as an explicit style/event policy using existing grouped SPREAD 5/6-note capability, "
            "but v2_6_78 routes that optional support through the existing spread low-register density guard so full-band piano "
            "does not stack more than one note below C3. The task does not modify core voicing source, projection, selector, "
            "expression, pattern, API, Agent, or HarmonyOS behavior."
        ),
        "static_audit": static_audit,
        "outputs": outputs,
        "aggregate": _aggregate(outputs),
        "acceptance": _acceptance(static_audit, outputs),
        "recommended_next_task": "medium_swing_full_band_listening_checkpoint_after_low_register_clarity_guard",
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_existing_voicing_capability_low_register_clarity_guard_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_existing_voicing_capability_low_register_clarity_guard_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": summary["acceptance"]}, indent=2, ensure_ascii=False))


def build_static_audit() -> dict[str, Any]:
    arrangement = arrangement_policy.get_arrangement_policy()
    policy = voicing_policy.get_voicing_policy()
    nested = dict(policy.metadata.get("medium_swing_existing_voicing_capability_usage_policy") or {})
    candidate_rows = _candidate_rows()
    return {
        "checkpoint_version": MILESTONE_ID,
        "arrangement_policy_enabled": bool(arrangement.get("medium_swing_existing_voicing_capability_usage_policy")),
        "arrangement_policy_version": arrangement.get("medium_swing_existing_voicing_capability_usage_policy_version"),
        "arrangement_policy_contract": arrangement.get("medium_swing_existing_voicing_capability_usage_policy_contract"),
        "voicing_policy_version": policy.metadata.get("medium_swing_existing_voicing_capability_usage_policy_version"),
        "low_register_clarity_guard_version": policy.metadata.get("medium_swing_existing_voicing_capability_low_register_clarity_guard_version"),
        "low_register_clarity_guard_enabled": bool(policy.metadata.get("medium_swing_existing_voicing_capability_low_register_clarity_guard_enabled")),
        "arrangement_low_register_clarity_guard_version": arrangement.get("medium_swing_existing_voicing_capability_low_register_clarity_guard_version"),
        "arrangement_low_register_clarity_guard_enabled": bool(arrangement.get("medium_swing_existing_voicing_capability_low_register_clarity_guard")),
        "voicing_policy_available": bool(nested.get("available")),
        "voicing_policy_default_enabled": bool(nested.get("enabled")),
        "voicing_policy_activation": nested.get("activation"),
        "ordinary_runtime_default": bool(nested.get("ordinary_runtime_default")),
        "ordinary_body": nested.get("ordinary_body"),
        "authorized_scenes": list(nested.get("authorized_scenes") or []),
        "requested_existing_contracts": list(nested.get("requested_existing_contracts") or []),
        "no_core_voicing_change": bool(nested.get("no_core_voicing_change")),
        "base_preferred_density": policy.preferred_density,
        "base_max_density": policy.max_density,
        "base_preferred_disposition": policy.preferred_disposition.value,
        "base_allowed_dispositions": [item.value for item in policy.allowed_dispositions],
        "pattern_forbidden_expression_candidates": [row for row in candidate_rows if row["forbidden_pattern_expression_keys"]],
        "pattern_forbidden_voicing_candidates": [row for row in candidate_rows if row["forbidden_pattern_voicing_keys"]],
        "bar_first_two_chord_bar_candidates": [row for row in candidate_rows if row["has_bar_first_two_chord_bar_marker"]],
    }


def _candidate_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for duration in (1.0, 2.0, 3.0, 4.0, 5.0):
        for candidate in comping_patterns.get_pattern_candidates({"region_duration_beats": duration}):
            forbidden_expression: set[str] = set(FORBIDDEN_PATTERN_EXPRESSION_KEYS & set(candidate.metadata))
            forbidden_voicing: set[str] = set(FORBIDDEN_PATTERN_VOICING_KEYS & set(candidate.metadata))
            for event in candidate.events:
                forbidden_expression.update(FORBIDDEN_PATTERN_EXPRESSION_KEYS & set(event.metadata))
                forbidden_voicing.update(FORBIDDEN_PATTERN_VOICING_KEYS & set(event.metadata))
            text_blob = " ".join([candidate.name, candidate.category, str(candidate.metadata), " ".join(candidate.tags)])
            rows.append(
                {
                    "name": candidate.name,
                    "duration_probe": duration,
                    "forbidden_pattern_expression_keys": tuple(sorted(forbidden_expression)),
                    "forbidden_pattern_voicing_keys": tuple(sorted(forbidden_voicing)),
                    "has_bar_first_two_chord_bar_marker": "two_chord_bar" in text_blob or "split_bar" in text_blob,
                }
            )
    return rows


def _explicit_voicing_capability_usage_override() -> dict[str, Any]:
    return {
        "enabled": True,
        "metadata": {
            "medium_swing_existing_voicing_capability_usage_policy": {
                "version": MILESTONE_ID,
                "available": True,
                "enabled": True,
                "activation": "explicit_v2_6_78_low_register_clarity_audit_demo",
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
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_medium_swing_existing_voicing_capability_low_register_clarity_guard_demo.mid"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": int(score.get("tempo", 132)),
            "choruses": 3,
            "seed": int(spec["seed"]),
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
            "voicing_override": _explicit_voicing_capability_usage_override(),
        }
    )
    debug = dict(result.debug)
    rows = _piano_voicing_rows(debug)
    density_counts = Counter(str(row["density"]) for row in rows)
    recipe_counts = Counter(str(row["recipe_id"]) for row in rows)
    grouped_spread_rows = [row for row in rows if str(row.get("recipe_id") or "").startswith("spread_")]
    five_six = [row for row in rows if int(row.get("density") or 0) in {5, 6}]
    return {
        "ok": bool(result.ok),
        "title": score.get("title"),
        "slug": slug,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "written_bars": debug.get("written_bars"),
        "performance_choruses": debug.get("performance_choruses"),
        "performance_bars": debug.get("performance_bars"),
        "piano_voicing_events": len(rows),
        "density_counts": dict(density_counts),
        "recipe_counts": dict(recipe_counts),
        "grouped_spread_events": len(grouped_spread_rows),
        "five_note_events": sum(1 for row in rows if int(row.get("density") or 0) == 5),
        "six_note_events": sum(1 for row in rows if int(row.get("density") or 0) == 6),
        "max_top_note": max((int(row.get("top_note") or 0) for row in rows), default=0),
        "voice_leading_warning_events": sum(1 for row in rows if row.get("top_voice_leap_exceeds_max")),
        "section_tail_5_6_events": sum(1 for row in five_six if row.get("region_is_last_bar_of_section")),
        "ending_5_6_events": sum(1 for row in five_six if row.get("region_is_last_bar_of_chorus")),
        "ordinary_body_5_6_events": sum(1 for row in five_six if not row.get("region_is_last_bar_of_section") and not row.get("region_is_last_bar_of_chorus")),
        "low_register_dense_rows": [row for row in rows if int(row.get("notes_below_c3") or 0) > 1],
        "bar_88_rows": [row for row in rows if slug == "all_the_things_you_are" and int(row.get("region_performance_bar_index") or -1) == 87],
        "sample_5_6_rows": five_six[:12],
    }


def _piano_voicing_rows(debug: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in debug.get("piano_musical_audit_events") or []:
        event = dict((raw or {}).get("pattern_event") or {})
        if event.get("track") != "piano":
            continue
        event_metadata = dict(event.get("metadata") or {})
        voicing = dict((raw or {}).get("voicing") or {})
        notes = [int(note.get("midi_note")) for note in voicing.get("notes") or [] if note.get("midi_note") is not None]
        voice_leading = dict(voicing.get("voice_leading_profile") or {})
        rows.append(
            {
                "event_id": event.get("event_id"),
                "region_id": event.get("region_id"),
                "chord_symbol": event.get("chord_symbol"),
                "pattern_id": event.get("pattern_id"),
                "density": voicing.get("density"),
                "disposition": voicing.get("disposition"),
                "recipe_id": voicing.get("recipe_id"),
                "functional_grouping": voicing.get("functional_grouping"),
                "midi_notes": notes,
                "notes_below_c3": sum(1 for note in notes if int(note) < 48),
                "low_register_clarity_guard_violation": sum(1 for note in notes if int(note) < 48) > 1,
                "top_note": max(notes) if notes else None,
                "region_chorus_index": event_metadata.get("region_chorus_index"),
                "region_total_choruses": event_metadata.get("region_total_choruses"),
                "region_is_last_bar_of_section": bool(event_metadata.get("region_is_last_bar_of_section")),
                "region_is_last_bar_of_chorus": bool(event_metadata.get("region_is_last_bar_of_chorus")),
                "region_performance_bar_index": event_metadata.get("region_performance_bar_index"),
                "top_voice_leap_exceeds_max": bool(voice_leading.get("top_voice_leap_exceeds_max")),
                "top_voice_abs_motion": voice_leading.get("top_voice_abs_motion"),
            }
        )
    return rows


def _aggregate(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    total_events = sum(int(out.get("piano_voicing_events") or 0) for out in outputs)
    five_note = sum(int(out.get("five_note_events") or 0) for out in outputs)
    six_note = sum(int(out.get("six_note_events") or 0) for out in outputs)
    grouped = sum(int(out.get("grouped_spread_events") or 0) for out in outputs)
    return {
        "piano_voicing_events": total_events,
        "grouped_spread_events": grouped,
        "five_note_events": five_note,
        "six_note_events": six_note,
        "five_six_ratio": round((five_note + six_note) / max(1, total_events), 4),
        "ordinary_body_5_6_events": sum(int(out.get("ordinary_body_5_6_events") or 0) for out in outputs),
        "voice_leading_warning_events": sum(int(out.get("voice_leading_warning_events") or 0) for out in outputs),
        "low_register_dense_events": sum(len(out.get("low_register_dense_rows") or []) for out in outputs),
        "bar_88_low_register_dense_events": sum(1 for out in outputs for row in (out.get("bar_88_rows") or []) if int(row.get("notes_below_c3") or 0) > 1),
        "max_top_note": max((int(out.get("max_top_note") or 0) for out in outputs), default=0),
    }


def _acceptance(static_audit: dict[str, Any], outputs: list[dict[str, Any]]) -> dict[str, Any]:
    aggregate = _aggregate(outputs)
    checks = {
        "policy_version_declared": static_audit.get("arrangement_policy_version") == "v2_6_77" and static_audit.get("voicing_policy_version") == "v2_6_77",
        "low_register_clarity_guard_declared": static_audit.get("arrangement_low_register_clarity_guard_version") == MILESTONE_ID and static_audit.get("low_register_clarity_guard_version") == MILESTONE_ID and bool(static_audit.get("low_register_clarity_guard_enabled")),
        "policy_available_but_default_opt_in": (
            bool(static_audit.get("arrangement_policy_enabled"))
            and bool(static_audit.get("voicing_policy_available"))
            and not bool(static_audit.get("voicing_policy_default_enabled"))
            and static_audit.get("ordinary_runtime_default") is False
        ),
        "no_core_voicing_change_declared": bool(static_audit.get("no_core_voicing_change")),
        "ordinary_base_policy_still_open_4note": static_audit.get("base_preferred_density") == 4 and static_audit.get("base_max_density") == 5 and static_audit.get("base_preferred_disposition") == "open",
        "patterns_still_no_expression_or_voicing_leakage": not static_audit.get("pattern_forbidden_expression_candidates") and not static_audit.get("pattern_forbidden_voicing_candidates"),
        "patterns_still_region_first": not static_audit.get("bar_first_two_chord_bar_candidates"),
        "existing_5note_capability_used": aggregate["five_note_events"] > 0,
        "existing_6note_capability_used": aggregate["six_note_events"] > 0,
        "ordinary_body_not_thickened": aggregate["ordinary_body_5_6_events"] == 0,
        "voice_leading_guard_ok": aggregate["voice_leading_warning_events"] == 0,
        "low_register_clarity_guard_ok": aggregate["low_register_dense_events"] == 0,
        "bar_88_clarity_regression_fixed": aggregate["bar_88_low_register_dense_events"] == 0,
        "top_register_ok": aggregate["max_top_note"] <= 74,
    }
    return {"passed": all(checks.values()), "checks": checks, "aggregate": aggregate}


def _render_report(summary: Mapping[str, Any]) -> str:
    acc = summary["acceptance"]
    agg = summary["aggregate"]
    lines = [
        f"# {MILESTONE_LABEL}",
        "",
        f"Acceptance Passed: **{acc['passed']}**",
        "",
        "## Scope",
        str(summary["scope"]),
        "",
        "## Aggregate",
        f"- Piano voicing events: {agg['piano_voicing_events']}",
        f"- Grouped SPREAD events: {agg['grouped_spread_events']}",
        f"- 5-note events: {agg['five_note_events']}",
        f"- 6-note events: {agg['six_note_events']}",
        f"- 5/6 ratio: {agg['five_six_ratio']}",
        f"- Ordinary-body 5/6 events: {agg['ordinary_body_5_6_events']}",
        f"- Voice-leading warnings: {agg['voice_leading_warning_events']}",
        f"- Low-register dense events (>1 note below C3): {agg['low_register_dense_events']}",
        f"- Bar 88 low-register dense events: {agg['bar_88_low_register_dense_events']}",
        f"- Max top note: {agg['max_top_note']}",
        "",
        "## Per Tune",
    ]
    for out in summary["outputs"]:
        lines.extend(
            [
                f"### {out['title']}",
                f"- MIDI: `{out['midi_path']}`",
                f"- Piano voicing events: {out['piano_voicing_events']}",
                f"- Density counts: `{out['density_counts']}`",
                f"- Recipe counts: `{out['recipe_counts']}`",
                f"- 5-note / 6-note: {out['five_note_events']} / {out['six_note_events']}",
                f"- Section-tail 5/6 events: {out['section_tail_5_6_events']}",
                f"- Ending 5/6 events: {out['ending_5_6_events']}",
                f"- Voice-leading warnings: {out['voice_leading_warning_events']}",
                f"- Low-register dense rows: {len(out.get('low_register_dense_rows') or [])}",
                f"- Bar 88 rows: `{out.get('bar_88_rows')}`",
                "",
            ]
        )
    lines.extend(["## Acceptance Checks", ""])
    for key, value in acc["checks"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
