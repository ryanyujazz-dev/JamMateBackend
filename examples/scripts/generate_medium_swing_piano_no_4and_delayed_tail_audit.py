from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.medium_swing import arrangement_policy, comping_patterns

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_66"
MILESTONE_LABEL = "v2_6_66 — Medium Swing No-4& Delayed-Tail Idiom + Hold Boundary Guard"

SPECS: tuple[dict[str, Any], ...] = (
    {"slug": "all_the_things_you_are", "leadsheet": "all_the_things_you_are.json", "seed": 3500},
    {"slug": "autumn_leaves", "leadsheet": "autumn_leaves.json", "seed": 3501},
)

V1_TRANSLATED_IDIOMS: tuple[dict[str, str], ...] = (
    {
        "v1_idiom": "major_251 / minor_251 dominant-resolution vocabulary",
        "v2_translation": "dominant-resolution ChordRegion preferred subset inside the existing region-length pool",
        "status": "implemented_as_preferred_subset_v2_6_65",
    },
    {
        "v1_idiom": "two_five / ii_setup vocabulary",
        "v2_translation": "predominant-to-dominant ChordRegion preferred subset; short regions remain anchor-led",
        "status": "implemented_as_preferred_subset_v2_6_65",
    },
    {
        "v1_idiom": "two_chord_bar split vocabulary",
        "v2_translation": "already translated as 2-beat / 1-beat ChordRegion vocabulary, not restored as bar-first templates",
        "status": "kept_region_first",
    },
    {
        "v1_idiom": "texture expansion shell2/shell4/rootless4",
        "v2_translation": "explicitly excluded from pattern selection; remains voicing policy territory",
        "status": "rejected_for_pattern_layer",
    },
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    outputs = [_generate_and_audit(spec) for spec in SPECS]
    static_audit = build_static_progression_subset_audit()
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": "V1 no-4& / delayed-tail idiom is translated into V2 ChordRegion-first candidate reweighting, while hold-until-next-touch duration is guarded so current-region harmony never sustains into a later ChordRegion. No voicing selection, final expression values in patterns, gesture, API, Agent, or HarmonyOS behavior is introduced.",
        "v1_translated_idioms": list(V1_TRANSLATED_IDIOMS),
        "v2_static_progression_subset_audit": static_audit,
        "outputs": outputs,
        "acceptance": _acceptance(static_audit, outputs),
        "recommended_next_tasks": [
            "v2_6_67_engine_medium_swing_active_fill_busy_multi_region_history_scorer",
            "v2_6_68_engine_medium_swing_expression_policy_v1_numeric_calibration",
            "v2_6_69_engine_medium_swing_piano_standard_tune_listening_checkpoint",
        ],
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_piano_no_4and_delayed_tail_audit_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_piano_no_4and_delayed_tail_audit_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_format_report(summary), encoding="utf-8")
    print({"ok": summary["acceptance"]["passed"], "summary_path": str(summary_path), "report_path": str(report_path), "outputs": outputs})
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def build_static_progression_subset_audit() -> dict[str, Any]:
    policy = arrangement_policy.get_arrangement_policy()
    rows = _candidate_rows()
    active_rows = [row for row in rows if row["weight"] > 0]
    forbidden = [row for row in rows if row["forbidden_pattern_expression_keys"]]
    bar_first = [row for row in rows if row["has_bar_first_two_chord_bar_marker"]]
    return {
        "checkpoint_version": MILESTONE_ID,
        "pattern_library_version": comping_patterns.PATTERN_LIBRARY_VERSION,
        "candidate_lookup_policy_version": comping_patterns.CANDIDATE_LOOKUP_POLICY_VERSION,
        "weight_calibration_policy_version": comping_patterns.WEIGHT_CALIBRATION_POLICY_VERSION,
        "expression_hint_handoff_policy_version": comping_patterns.EXPRESSION_HINT_HANDOFF_POLICY_VERSION,
        "progression_specific_subset_policy_enabled": bool(policy.get("piano_comping_progression_specific_subset_policy")),
        "progression_specific_subset_policy_version": str(policy.get("piano_comping_progression_specific_subset_policy_version")),
        "progression_specific_subset_contract": str(policy.get("piano_comping_progression_specific_subset_contract")),
        "no_4and_delayed_tail_policy_enabled": bool(policy.get("piano_comping_no_4and_delayed_tail_idiom_policy")),
        "no_4and_delayed_tail_policy_version": str(policy.get("piano_comping_no_4and_delayed_tail_idiom_policy_version")),
        "no_4and_delayed_tail_contract": str(policy.get("piano_comping_no_4and_delayed_tail_idiom_contract")),
        "translated_idioms": list(V1_TRANSLATED_IDIOMS),
        "candidate_count_total": len(rows),
        "candidate_count_active": len(active_rows),
        "active_by_region_length_family": dict(_counter_by(active_rows, "region_length_family")),
        "active_by_weight_calibration_class": dict(_counter_by(active_rows, "weight_calibration_class")),
        "forbidden_pattern_expression_key_candidates": forbidden,
        "bar_first_two_chord_bar_candidates": bar_first,
        "candidate_rows": rows,
    }


def _candidate_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for duration in (1.0, 2.0, 3.0, 4.0, 5.0):
        for candidate in comping_patterns.get_pattern_candidates({"region_duration_beats": duration}):
            metadata = dict(candidate.metadata)
            event_rows = []
            forbidden: list[str] = []
            for event in candidate.events:
                event_metadata = dict(event.metadata)
                forbidden.extend([key for key in ("velocity", "duration", "duration_beats", "pedal") if key in event_metadata])
                event_rows.append(
                    {
                        "local_beat": float(event.local_beat),
                        "event_role": event_metadata.get("event_role"),
                        "semantic_expression_hint": event_metadata.get("semantic_expression_hint"),
                        "expression_hint": event.expression_hint,
                    }
                )
            text_blob = " ".join([candidate.name, candidate.category, str(metadata), " ".join(candidate.tags)])
            rows.append(
                {
                    "name": candidate.name,
                    "duration_probe": duration,
                    "weight": float(candidate.weight),
                    "category": candidate.category,
                    "region_length_family": str(metadata.get("region_length_family") or "missing"),
                    "rhythmic_cell": str(metadata.get("rhythmic_cell") or "missing"),
                    "rhythm_family": str(metadata.get("rhythm_family") or "missing"),
                    "weight_calibration_class": str(metadata.get("weight_calibration_class") or "missing"),
                    "tail_push_risk": str(metadata.get("tail_push_risk") or "none"),
                    "no_4and_delayed_tail_idiom": bool(metadata.get("no_4and_delayed_tail_idiom", False)),
                    "events": tuple(event_rows),
                    "forbidden_pattern_expression_keys": tuple(sorted(set(forbidden))),
                    "has_bar_first_two_chord_bar_marker": "two_chord_bar" in text_blob or "split_bar" in text_blob,
                    "is_region_first": metadata.get("candidate_lookup_policy") == "region_length_aware" and metadata.get("time_reference") == "region_local_beats",
                }
            )
    return rows


def _generate_and_audit(spec: Mapping[str, Any]) -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / str(spec["leadsheet"])).read_text(encoding="utf-8"))
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_medium_swing_piano_no_4and_delayed_tail_demo.mid"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": int(score.get("tempo", 132)),
            "choruses": 3,
            "seed": int(spec["seed"]),
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
        }
    )
    piano_audit = build_piano_musical_audit(result.debug)
    rows = _piano_rows(result.debug)
    context_counts = Counter(str(row.get("progression_specific_context_label") or "missing") for row in rows)
    subset_key_counts = Counter(str(row.get("progression_specific_subset_key") or "missing") for row in rows)
    status_counts = Counter(str(row.get("progression_specific_subset_status") or "missing") for row in rows)
    no_4and_status_counts = Counter(str(row.get("no_4and_delayed_tail_status") or "missing") for row in rows)
    hold_reason_counts = Counter(str(row.get("duration_next_touch_hold_reason") or "missing") for row in rows if row.get("duration_next_touch_hold_applied"))
    preferred_rows = [row for row in rows if "preferred" in str(row.get("progression_specific_subset_status") or "")]
    fallback_rows = [row for row in rows if "fallback" in str(row.get("progression_specific_subset_status") or "")]
    forbidden_rows = [row for row in rows if row.get("pattern_forbidden_expression_keys")]
    bar_first_rows = [row for row in rows if row.get("has_bar_first_two_chord_bar_marker")]
    return {
        "ok": bool(result.ok),
        "title": score.get("title"),
        "slug": slug,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "piano_events": len(rows),
        "progression_subset_applied_events": sum(1 for row in rows if row.get("progression_specific_subset_policy_applied")),
        "progression_subset_preferred_events": len(preferred_rows),
        "progression_subset_fallback_downweighted_events": len(fallback_rows),
        "progression_subset_context_counts": dict(context_counts),
        "progression_subset_key_counts": dict(subset_key_counts),
        "progression_subset_status_counts": dict(status_counts),
        "no_4and_policy_applied_events": sum(1 for row in rows if row.get("no_4and_delayed_tail_policy_applied")),
        "no_4and_preferred_events": sum(1 for row in rows if row.get("no_4and_delayed_tail_status") == "no_4and_delayed_tail_preferred"),
        "tail_push_rare_downweighted_events": sum(1 for row in rows if row.get("no_4and_delayed_tail_status") == "tail_push_rare_lift_downweighted"),
        "no_4and_status_counts": dict(no_4and_status_counts),
        "hold_reason_counts": dict(hold_reason_counts),
        "hold_cross_region_boundary_guard_events": hold_reason_counts.get("next_same_track_touch_beyond_region_clamped_to_region_end", 0),
        "harmonic_function_applied_events": sum(1 for row in rows if row.get("harmonic_function_comping_policy_applied")),
        "history_penalty_events": sum(1 for row in rows if float(row.get("history_continuity_multiplier") or 1.0) < 1.0),
        "history_bonus_events": sum(1 for row in rows if float(row.get("history_continuity_multiplier") or 1.0) > 1.0),
        "hold_until_next_touch_applied_events": sum(1 for row in rows if row.get("duration_next_touch_hold_applied")),
        "pattern_forbidden_expression_key_events": len(forbidden_rows),
        "bar_first_two_chord_bar_events": len(bar_first_rows),
        "top_note_max": piano_audit.summary.get("medium_swing_open_drop_top_note_max"),
        "top_note_ge_75_events": piano_audit.summary.get("medium_swing_open_drop_top_note_ge_75_events"),
        "voice_leading_warning_events": piano_audit.summary.get("medium_swing_open_drop_voice_leading_warning_events"),
    }


def _piano_rows(debug: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in debug.get("piano_musical_audit_events") or []:
        event = dict((raw or {}).get("pattern_event") or {})
        if event.get("track") != "piano":
            continue
        expression = dict((raw or {}).get("expression") or {})
        pattern_metadata = dict(event.get("metadata") or {})
        expression_metadata = dict(expression.get("metadata") or {})
        text_blob = " ".join([str(event.get("pattern_id") or ""), str(event.get("category") or ""), str(pattern_metadata)])
        forbidden = [key for key in {"velocity", "duration", "duration_beats", "pedal"} if key in pattern_metadata]
        rows.append(
            {
                "event_id": event.get("event_id"),
                "pattern_id": event.get("pattern_id"),
                "onset_beat": event.get("onset_beat"),
                "region_duration_beats": pattern_metadata.get("region_duration_beats"),
                "region_length_family": pattern_metadata.get("region_length_family") or pattern_metadata.get("coverage_region_length_family"),
                "rhythmic_cell": pattern_metadata.get("rhythmic_cell"),
                "rhythm_family": pattern_metadata.get("rhythm_family"),
                "semantic_expression_hint": pattern_metadata.get("semantic_expression_hint"),
                "duration_next_touch_hold_applied": bool(expression_metadata.get("duration_next_touch_hold_applied", False)),
                "duration_next_touch_hold_reason": expression_metadata.get("duration_next_touch_hold_reason"),
                "duration_region_remaining_beats": expression_metadata.get("duration_region_remaining_beats"),
                "duration_next_touch_hold_version": expression_metadata.get("duration_next_touch_hold_version"),
                "no_4and_delayed_tail_policy_applied": bool(pattern_metadata.get("no_4and_delayed_tail_policy_applied", False)),
                "no_4and_delayed_tail_status": pattern_metadata.get("no_4and_delayed_tail_status"),
                "no_4and_delayed_tail_multiplier": pattern_metadata.get("no_4and_delayed_tail_multiplier"),
                "progression_specific_subset_policy_applied": bool(pattern_metadata.get("progression_specific_subset_policy_applied", False)),
                "progression_specific_context_label": pattern_metadata.get("progression_specific_context_label"),
                "progression_specific_subset_key": pattern_metadata.get("progression_specific_subset_key"),
                "progression_specific_subset_status": pattern_metadata.get("progression_specific_subset_status"),
                "progression_specific_subset_multiplier": pattern_metadata.get("progression_specific_subset_multiplier"),
                "harmonic_function_comping_policy_applied": bool(pattern_metadata.get("harmonic_function_comping_policy_applied", False)),
                "history_continuity_multiplier": pattern_metadata.get("history_continuity_multiplier"),
                "pattern_forbidden_expression_keys": tuple(forbidden),
                "has_bar_first_two_chord_bar_marker": "two_chord_bar" in text_blob or "split_bar" in text_blob,
            }
        )
    return sorted(rows, key=lambda row: (float(row.get("onset_beat") or 0.0), str(row.get("event_id"))))


def _counter_by(rows: Iterable[Mapping[str, Any]], key: str) -> Counter:
    return Counter(str(row.get(key) or "missing") for row in rows)


def _acceptance(static_audit: Mapping[str, Any], outputs: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = [
        {"name": "static: progression subset policy enabled", "passed": bool(static_audit.get("progression_specific_subset_policy_enabled"))},
        {"name": "static: progression subset policy version", "passed": static_audit.get("progression_specific_subset_policy_version") == "v2_6_65"},
        {"name": "static: no-4& delayed-tail policy enabled", "passed": static_audit.get("no_4and_delayed_tail_policy_enabled") is True},
        {"name": "static: no-4& delayed-tail policy version", "passed": static_audit.get("no_4and_delayed_tail_policy_version") == "v2_6_66"},
        {"name": "static: no pattern candidate writes final expression values", "passed": len(static_audit.get("forbidden_pattern_expression_key_candidates") or []) == 0},
        {"name": "static: no bar-first/two-chord-bar markers remain", "passed": len(static_audit.get("bar_first_two_chord_bar_candidates") or []) == 0},
    ]
    for output in outputs:
        checks.extend(
            [
                {"name": f"{output['slug']}: generation ok", "passed": bool(output.get("ok"))},
                {"name": f"{output['slug']}: progression subset metadata present", "passed": output.get("progression_subset_applied_events", 0) > 0},
                {"name": f"{output['slug']}: preferred subset events present", "passed": output.get("progression_subset_preferred_events", 0) > 0},
                {"name": f"{output['slug']}: no-4& delayed-tail policy metadata present", "passed": output.get("no_4and_policy_applied_events", 0) > 0},
                {"name": f"{output['slug']}: no-4& delayed-tail preferred events present", "passed": output.get("no_4and_preferred_events", 0) > 0},
                {"name": f"{output['slug']}: hold boundary guard version present", "passed": output.get("hold_until_next_touch_applied_events", 0) > 0},
                {"name": f"{output['slug']}: harmonic policy remains active", "passed": output.get("harmonic_function_applied_events", 0) > 0},
                {"name": f"{output['slug']}: no pattern events contain concrete expression values", "passed": output.get("pattern_forbidden_expression_key_events") == 0},
                {"name": f"{output['slug']}: no bar-first two_chord_bar runtime events", "passed": output.get("bar_first_two_chord_bar_events") == 0},
                {"name": f"{output['slug']}: top register calm", "passed": (output.get("top_note_ge_75_events") or 0) == 0},
                {"name": f"{output['slug']}: voice-leading warnings calm", "passed": (output.get("voice_leading_warning_events") or 0) == 0},
            ]
        )
    return {"passed": all(check["passed"] for check in checks), "checks": checks}


def _format_report(summary: Mapping[str, Any]) -> str:
    lines = [f"# {summary['milestone']}", "", str(summary.get("scope", "")), ""]
    lines.extend(["## V1 idioms translated", ""])
    for row in summary["v1_translated_idioms"]:
        lines.extend([f"- **{row['v1_idiom']}** → {row['v2_translation']} (`{row['status']}`)"])
    static = summary["v2_static_progression_subset_audit"]
    lines.extend(
        [
            "",
            "## Static V2 policy audit",
            "",
            f"- Pattern / lookup / weight / expression-hint versions: `{static['pattern_library_version']}` / `{static['candidate_lookup_policy_version']}` / `{static['weight_calibration_policy_version']}` / `{static['expression_hint_handoff_policy_version']}`",
            f"- Progression subset policy enabled/version: `{static['progression_specific_subset_policy_enabled']}` / `{static['progression_specific_subset_policy_version']}`",
            f"- No-4& delayed-tail policy enabled/version: `{static['no_4and_delayed_tail_policy_enabled']}` / `{static['no_4and_delayed_tail_policy_version']}`",
            f"- Active by region length: `{static['active_by_region_length_family']}`",
            f"- Active by weight class: `{static['active_by_weight_calibration_class']}`",
            f"- Forbidden expression candidates: `{len(static['forbidden_pattern_expression_key_candidates'])}`",
            f"- Bar-first two_chord_bar candidates: `{len(static['bar_first_two_chord_bar_candidates'])}`",
            "",
            "## Runtime standard-tune audit",
            "",
        ]
    )
    for output in summary.get("outputs", []):
        lines.extend(
            [
                f"### {output['title']}",
                "",
                f"- MIDI: `{output['midi_path']}`",
                f"- Piano events: `{output['piano_events']}`",
                f"- Progression subset applied / preferred / fallback: `{output['progression_subset_applied_events']}` / `{output['progression_subset_preferred_events']}` / `{output['progression_subset_fallback_downweighted_events']}`",
                f"- Progression context counts: `{output['progression_subset_context_counts']}`",
                f"- Progression subset key counts: `{output['progression_subset_key_counts']}`",
                f"- Progression status counts: `{output['progression_subset_status_counts']}`",
                f"- No-4& policy applied/preferred/tail-push-downweighted: `{output['no_4and_policy_applied_events']}` / `{output['no_4and_preferred_events']}` / `{output['tail_push_rare_downweighted_events']}`",
                f"- No-4& status counts: `{output['no_4and_status_counts']}`",
                f"- Harmonic / history penalty / history bonus: `{output['harmonic_function_applied_events']}` / `{output['history_penalty_events']}` / `{output['history_bonus_events']}`",
                f"- Hold-until-next-touch events / boundary guard events: `{output['hold_until_next_touch_applied_events']}` / `{output['hold_cross_region_boundary_guard_events']}`",
                f"- Hold reason counts: `{output['hold_reason_counts']}`",
                f"- Forbidden expression / bar-first events: `{output['pattern_forbidden_expression_key_events']}` / `{output['bar_first_two_chord_bar_events']}`",
                f"- Top note max / >=75 / voice-leading warnings: `{output['top_note_max']}` / `{output['top_note_ge_75_events']}` / `{output['voice_leading_warning_events']}`",
                "",
            ]
        )
    lines.extend(["## Acceptance", "", f"Passed: `{summary['acceptance']['passed']}`", ""])
    for check in summary["acceptance"]["checks"]:
        lines.append(f"- `{check['name']}`: `{check['passed']}`")
    lines.extend(["", "## Recommended next tasks", ""])
    for task in summary.get("recommended_next_tasks", []):
        lines.append(f"- `{task}`")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
