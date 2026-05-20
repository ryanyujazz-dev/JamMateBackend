from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.medium_swing import comping_patterns

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_64"
MILESTONE_LABEL = "v2_6_64 — Medium Swing Piano V1 Idiom Delta Audit Checkpoint"

SPECS: tuple[dict[str, Any], ...] = (
    {"slug": "all_the_things_you_are", "leadsheet": "all_the_things_you_are.json", "seed": 3400},
    {"slug": "autumn_leaves", "leadsheet": "autumn_leaves.json", "seed": 3401},
)

V1_ROLE_COUNTS: dict[str, int] = {
    "base": 24,
    "fill": 8,
    "variation": 8,
    "major_251": 7,
    "two_five": 7,
    "minor_251": 6,
    "ii_setup": 4,
    "two_chord_bar": 4,
    "ending": 2,
}

V1_CATEGORY_COUNTS: dict[str, int] = {
    "stable": 30,
    "offbeat": 15,
    "variation": 7,
    "push": 7,
    "gentle_fill": 6,
    "busy_fill": 3,
    "ending": 2,
}

V1_EXPRESSION_TOUCH_RANGES: dict[str, dict[str, Any]] = {
    "soft_hold": {"velocity": [48, 59], "duration_ticks": [84, 140], "usage": "main support, beat-1/3 anchors, cadence release"},
    "light_stab": {"velocity": [48, 65], "duration_ticks": [62, 88], "usage": "Charleston answer and light offbeat response"},
    "accent_stab": {"velocity": [60, 70], "duration_ticks": [58, 72], "usage": "push, 4& pickup, dominant approach, busy fill"},
    "backbeat_hold": {"velocity": [51, 64], "duration_ticks": [76, 108], "usage": "2&/3& support, longer than stab"},
    "final_hold": {"velocity": [44, 45], "duration_ticks": [220, 240], "usage": "ending final sustain"},
}

V1_TO_V2_TRANSLATION_MATRIX: tuple[dict[str, str], ...] = (
    {
        "v1_idiom": "base stable/offbeat vocabulary",
        "v1_signal": "base=24, stable=30, offbeat=15",
        "v2_translation": "4-beat ChordRegion stable/offbeat pitchless cells",
        "v2_status": "covered",
        "next_action": "Keep calibrated by v2_6_58/v2_6_59 history ratios; do not add more generic cells before context subset policy.",
    },
    {
        "v1_idiom": "two_chord_bar split vocabulary",
        "v1_signal": "two_chord_bar=4",
        "v2_translation": "2-beat / 1-beat ChordRegion vocabulary; no bar-first route",
        "v2_status": "covered_as_region_first_translation",
        "next_action": "Keep name and route region-first; do not restore two_chord_bar as a selector key.",
    },
    {
        "v1_idiom": "major_251 / minor_251 / two_five / ii_setup priority",
        "v1_signal": "major_251=7, minor_251=6, two_five=7, ii_setup=4",
        "v2_translation": "ChordRegion functional context candidate subset, not bar-level pattern templates",
        "v2_status": "partial_multiplier_only",
        "next_action": "v2_6_65 should add context-specific candidate subset priority before generic fallback.",
    },
    {
        "v1_idiom": "fill / variation vocabulary",
        "v1_signal": "fill=8, variation=8, gentle_fill=6, busy_fill=3",
        "v2_translation": "Phrase-role/context-gated candidate subset with active/busy guard, not gesture or voicing",
        "v2_status": "partial_low_level_active_only",
        "next_action": "Defer until after progression subset; extend history scorer with active/fill/busy memory before enabling more fills.",
    },
    {
        "v1_idiom": "ending vocabulary",
        "v1_signal": "ending=2 with final_hold",
        "v2_translation": "ending/last-region candidate subset + final_hold semantic hint",
        "v2_status": "partial_expression_hint_only",
        "next_action": "Add ending subset later, after expression calibration; do not write MIDI durations in pattern.",
    },
    {
        "v1_idiom": "4& rare lift policy",
        "v1_signal": "has_4& downweighted; no_4and/delayed/tail rewarded",
        "v2_translation": "region-local tail-push risk + region-first anticipation compatibility",
        "v2_status": "covered_but_needs_v1_ratio_audit",
        "next_action": "v2_6_66 should reinforce no-4& / delayed-tail idioms using region-local tail slots.",
    },
    {
        "v1_idiom": "history guard",
        "v1_signal": "exact/rhythm/active/fill/push/offbeat/busy/two-phrase penalties",
        "v2_translation": "CompingHistoryScorer over ChordRegion-local pattern history",
        "v2_status": "partial_no_busy_fill_phrase_memory_yet",
        "next_action": "v2_6_67 should add active/fill/busy/multi-region phrase memory, not bar-first two-bar phrase logic.",
    },
    {
        "v1_idiom": "touch/expression numeric calibration",
        "v1_signal": "touch ranges for soft_hold/light_stab/accent_stab/backbeat_hold/final_hold",
        "v2_translation": "ExpressionPolicy ranges; pattern carries semantic_expression_hint only",
        "v2_status": "partial_handoff_done_calibration_pending",
        "next_action": "v2_6_68 should calibrate ExpressionPolicy from V1 ranges while preserving hold_until_next_touch semantics.",
    },
    {
        "v1_idiom": "texture expansion shell2/shell4/rootless4",
        "v1_signal": "V1 expands rhythm templates into texture candidates",
        "v2_translation": "Reject pattern-level texture expansion; keep voicing policy independent",
        "v2_status": "rejected_for_v2_pattern_layer",
        "next_action": "Keep shell2/rootless/drop2/drop3 in voicing policy only.",
    },
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    outputs = [_generate_and_audit(spec) for spec in SPECS]
    static_audit = build_static_idiom_delta_audit()
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": "Behavior-preserving V1→V2 Medium Swing piano idiom delta audit. This checkpoint studies V1 vocabulary/expression/history ideas and maps them to the existing V2 ChordRegion-first pattern architecture without changing runtime selection logic.",
        "v1_reference": {
            "source": "V1 Medium Swing Piano Comping Pattern Research Report",
            "pattern_templates": 70,
            "pattern_events": 182,
            "role_counts": V1_ROLE_COUNTS,
            "category_counts": V1_CATEGORY_COUNTS,
            "expression_touch_ranges": V1_EXPRESSION_TOUCH_RANGES,
        },
        "v2_static_idiom_delta_audit": static_audit,
        "outputs": outputs,
        "acceptance": _acceptance(static_audit, outputs),
        "recommended_next_tasks": [
            "v2_6_65_engine_medium_swing_progression_specific_candidate_subset_policy",
            "v2_6_66_engine_medium_swing_no_4and_delayed_tail_idiom_reinforcement",
            "v2_6_67_engine_medium_swing_active_fill_busy_multi_region_history_scorer",
            "v2_6_68_engine_medium_swing_expression_policy_v1_numeric_calibration",
            "v2_6_69_engine_medium_swing_piano_standard_tune_listening_checkpoint",
        ],
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_piano_v1_idiom_delta_audit_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_medium_swing_piano_v1_idiom_delta_audit_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_format_report(summary), encoding="utf-8")
    print({"ok": summary["acceptance"]["passed"], "summary_path": str(summary_path), "report_path": str(report_path), "outputs": outputs})
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def build_static_idiom_delta_audit() -> dict[str, Any]:
    candidate_rows = _candidate_rows()
    active_rows = [row for row in candidate_rows if row["weight"] > 0]
    forbidden = [row for row in candidate_rows if row["forbidden_pattern_expression_keys"]]
    bar_first = [row for row in candidate_rows if row["has_bar_first_two_chord_bar_marker"]]
    by_length = _counter_by(active_rows, "region_length_family")
    by_class = _counter_by(active_rows, "weight_calibration_class")
    by_rhythm_family = _counter_by(active_rows, "rhythm_family")
    semantic_hints = Counter(hint for row in active_rows for hint in row["semantic_hints"])
    tail_push = [row for row in active_rows if row["tail_push_risk"] == "high" or row["weight_calibration_class"] == "tail_push"]
    no_4and_delayed_tail = [
        row
        for row in active_rows
        if row["tail_push_risk"] != "high" and any(token in row["rhythm_family"] or token in row["rhythmic_cell"] for token in ("delayed", "tail", "backbeat"))
    ]
    return {
        "checkpoint_version": MILESTONE_ID,
        "pattern_library_version": comping_patterns.PATTERN_LIBRARY_VERSION,
        "candidate_lookup_policy_version": comping_patterns.CANDIDATE_LOOKUP_POLICY_VERSION,
        "weight_calibration_policy_version": comping_patterns.WEIGHT_CALIBRATION_POLICY_VERSION,
        "expression_hint_handoff_policy_version": comping_patterns.EXPRESSION_HINT_HANDOFF_POLICY_VERSION,
        "translation_matrix": list(V1_TO_V2_TRANSLATION_MATRIX),
        "candidate_count_total": len(candidate_rows),
        "candidate_count_active": len(active_rows),
        "active_by_region_length_family": dict(by_length),
        "active_by_weight_calibration_class": dict(by_class),
        "active_by_rhythm_family": dict(by_rhythm_family),
        "active_semantic_hint_counts": dict(semantic_hints),
        "tail_push_active_candidate_count": len(tail_push),
        "tail_push_active_weight_total": round(sum(row["weight"] for row in tail_push), 4),
        "no_4and_delayed_tail_active_candidate_count": len(no_4and_delayed_tail),
        "forbidden_pattern_expression_key_candidates": forbidden,
        "bar_first_two_chord_bar_candidates": bar_first,
        "v1_to_v2_delta_summary": {
            "covered": [row for row in V1_TO_V2_TRANSLATION_MATRIX if row["v2_status"].startswith("covered")],
            "partial": [row for row in V1_TO_V2_TRANSLATION_MATRIX if row["v2_status"].startswith("partial")],
            "rejected": [row for row in V1_TO_V2_TRANSLATION_MATRIX if row["v2_status"].startswith("rejected")],
        },
        "candidate_rows": candidate_rows,
    }


def _candidate_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for duration in (1.0, 2.0, 3.0, 4.0, 5.0):
        for candidate in comping_patterns.get_pattern_candidates({"region_duration_beats": duration}):
            metadata = dict(candidate.metadata)
            event_rows = []
            forbidden: list[str] = []
            semantic_hints: list[str] = []
            for event in candidate.events:
                event_metadata = dict(event.metadata)
                semantic_hints.append(str(event_metadata.get("semantic_expression_hint") or "missing"))
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
                    "region_length_beats": float(metadata.get("region_length_beats") or duration),
                    "rhythmic_cell": str(metadata.get("rhythmic_cell") or "missing"),
                    "rhythm_family": str(metadata.get("rhythm_family") or "missing"),
                    "phrase_role": str(metadata.get("phrase_role") or "missing"),
                    "weight_calibration_class": str(metadata.get("weight_calibration_class") or "missing"),
                    "tail_push_risk": str(metadata.get("tail_push_risk") or "none"),
                    "context_gate": str(metadata.get("context_gate") or "generic"),
                    "activation": str(metadata.get("activation") or "missing"),
                    "semantic_hints": tuple(semantic_hints),
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
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_medium_swing_piano_v1_idiom_delta_audit_demo.mid"
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
    active_tail_push_rows = [row for row in rows if row.get("tail_push_risk") == "high" or row.get("weight_calibration_class") == "tail_push"]
    active_or_busy_rows = [row for row in rows if row.get("weight_calibration_class") in {"active", "tail_push"} or "push" in str(row.get("rhythm_family"))]
    no_4and_delayed_tail_rows = [
        row
        for row in rows
        if row.get("tail_push_risk") != "high" and any(token in str(row.get("rhythm_family")) or token in str(row.get("rhythmic_cell")) for token in ("delayed", "tail", "backbeat"))
    ]
    context_counts = Counter(str(row.get("harmonic_function_context_label") or "missing") for row in rows)
    region_length_counts = Counter(str(row.get("region_length_family") or row.get("coverage_region_length_family") or "missing") for row in rows)
    class_counts = Counter(str(row.get("weight_calibration_class") or "missing") for row in rows)
    semantic_hint_counts = Counter(str(row.get("semantic_expression_hint") or "missing") for row in rows)
    forbidden_rows = [row for row in rows if row.get("pattern_forbidden_expression_keys")]
    bar_first_rows = [row for row in rows if row.get("has_bar_first_two_chord_bar_marker")]
    return {
        "ok": bool(result.ok),
        "title": score.get("title"),
        "slug": slug,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "piano_events": len(rows),
        "region_length_counts": dict(region_length_counts),
        "harmonic_function_context_counts": dict(context_counts),
        "weight_calibration_class_counts": dict(class_counts),
        "semantic_hint_counts": dict(semantic_hint_counts),
        "tail_push_events": len(active_tail_push_rows),
        "active_or_tail_push_events": len(active_or_busy_rows),
        "no_4and_delayed_tail_events": len(no_4and_delayed_tail_rows),
        "history_penalty_events": sum(1 for row in rows if float(row.get("history_continuity_multiplier") or 1.0) < 1.0),
        "history_bonus_events": sum(1 for row in rows if float(row.get("history_continuity_multiplier") or 1.0) > 1.0),
        "harmonic_function_applied_events": sum(1 for row in rows if row.get("harmonic_function_comping_policy_applied")),
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
                "local_beat": event.get("local_beat"),
                "region_duration_beats": pattern_metadata.get("region_duration_beats"),
                "region_length_family": pattern_metadata.get("region_length_family"),
                "coverage_region_length_family": pattern_metadata.get("coverage_region_length_family"),
                "rhythmic_cell": pattern_metadata.get("rhythmic_cell"),
                "rhythm_family": pattern_metadata.get("rhythm_family"),
                "phrase_role": pattern_metadata.get("phrase_role"),
                "weight_calibration_class": pattern_metadata.get("weight_calibration_class"),
                "tail_push_risk": pattern_metadata.get("tail_push_risk"),
                "semantic_expression_hint": pattern_metadata.get("semantic_expression_hint"),
                "expression_hint": event.get("expression_hint"),
                "profile_name": expression.get("profile_name"),
                "duration_beats": expression.get("duration_beats"),
                "duration_next_touch_hold_applied": bool(expression_metadata.get("duration_next_touch_hold_applied", False)),
                "harmonic_function_context_label": pattern_metadata.get("harmonic_function_context_label"),
                "harmonic_function_comping_policy_applied": bool(pattern_metadata.get("harmonic_function_comping_policy_applied", False)),
                "history_continuity_multiplier": pattern_metadata.get("history_continuity_multiplier"),
                "history_continuity_class": pattern_metadata.get("history_continuity_class"),
                "pattern_forbidden_expression_keys": tuple(forbidden),
                "has_bar_first_two_chord_bar_marker": "two_chord_bar" in text_blob or "split_bar" in text_blob,
            }
        )
    return sorted(rows, key=lambda row: (float(row.get("onset_beat") or 0.0), str(row.get("event_id"))))


def _counter_by(rows: Iterable[Mapping[str, Any]], key: str) -> Counter:
    return Counter(str(row.get(key) or "missing") for row in rows)


def _acceptance(static_audit: Mapping[str, Any], outputs: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = [
        {"name": "static: no pattern candidate writes final expression values", "passed": len(static_audit.get("forbidden_pattern_expression_key_candidates") or []) == 0},
        {"name": "static: no bar-first/two-chord-bar markers remain in V2 candidates", "passed": len(static_audit.get("bar_first_two_chord_bar_candidates") or []) == 0},
        {"name": "static: V2 has active 1/2/4-beat region candidates", "passed": all((static_audit.get("active_by_region_length_family") or {}).get(key, 0) > 0 for key in ("one_beat_region", "two_beat_region", "four_beat_region"))},
        {"name": "static: V2 keeps V1-derived expression semantic hints", "passed": all((static_audit.get("active_semantic_hint_counts") or {}).get(key, 0) > 0 for key in ("soft_hold", "light_stab", "backbeat_hold", "accent_hold"))},
        {"name": "static: V1 progression vocabulary is explicitly marked partial, not falsely accepted", "passed": any(row.get("v1_idiom", "").startswith("major_251") and row.get("v2_status") == "partial_multiplier_only" for row in static_audit.get("translation_matrix") or [])},
        {"name": "static: V1 texture expansion is explicitly rejected from V2 pattern layer", "passed": any(row.get("v1_idiom", "").startswith("texture expansion") and row.get("v2_status", "").startswith("rejected") for row in static_audit.get("translation_matrix") or [])},
    ]
    for output in outputs:
        checks.extend(
            [
                {"name": f"{output['slug']}: generation ok", "passed": bool(output.get("ok"))},
                {"name": f"{output['slug']}: harmonic policy remains active", "passed": output.get("harmonic_function_applied_events", 0) > 0},
                {"name": f"{output['slug']}: history scorer remains active", "passed": output.get("history_penalty_events", 0) + output.get("history_bonus_events", 0) > 0},
                {"name": f"{output['slug']}: no pattern events contain concrete expression values", "passed": output.get("pattern_forbidden_expression_key_events") == 0},
                {"name": f"{output['slug']}: no bar-first two_chord_bar runtime events", "passed": output.get("bar_first_two_chord_bar_events") == 0},
                {"name": f"{output['slug']}: top register calm", "passed": (output.get("top_note_ge_75_events") or 0) == 0},
                {"name": f"{output['slug']}: voice-leading warnings calm", "passed": (output.get("voice_leading_warning_events") or 0) == 0},
            ]
        )
    return {"passed": all(check["passed"] for check in checks), "checks": checks}


def _format_report(summary: Mapping[str, Any]) -> str:
    lines = [f"# {summary['milestone']}", "", str(summary.get("scope", "")), ""]
    v1 = summary["v1_reference"]
    lines.extend(
        [
            "## V1 reference signals",
            "",
            f"- Pattern templates / events: `{v1['pattern_templates']}` / `{v1['pattern_events']}`",
            f"- Role counts: `{v1['role_counts']}`",
            f"- Category counts: `{v1['category_counts']}`",
            f"- Expression touch ranges: `{v1['expression_touch_ranges']}`",
            "",
            "## V1 → V2 translation matrix",
            "",
        ]
    )
    for row in summary["v2_static_idiom_delta_audit"]["translation_matrix"]:
        lines.extend(
            [
                f"### {row['v1_idiom']}",
                "",
                f"- V1 signal: `{row['v1_signal']}`",
                f"- V2 translation: `{row['v2_translation']}`",
                f"- Status: `{row['v2_status']}`",
                f"- Next action: {row['next_action']}",
                "",
            ]
        )
    static = summary["v2_static_idiom_delta_audit"]
    lines.extend(
        [
            "## V2 static pattern audit",
            "",
            f"- Candidate count total/active: `{static['candidate_count_total']}` / `{static['candidate_count_active']}`",
            f"- Active by region length: `{static['active_by_region_length_family']}`",
            f"- Active by weight class: `{static['active_by_weight_calibration_class']}`",
            f"- Active semantic hints: `{static['active_semantic_hint_counts']}`",
            f"- Tail-push active candidate count/weight: `{static['tail_push_active_candidate_count']}` / `{static['tail_push_active_weight_total']}`",
            f"- No-4& delayed/tail candidate count: `{static['no_4and_delayed_tail_active_candidate_count']}`",
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
                f"- Region length counts: `{output['region_length_counts']}`",
                f"- Harmonic context counts: `{output['harmonic_function_context_counts']}`",
                f"- Weight class counts: `{output['weight_calibration_class_counts']}`",
                f"- Semantic hint counts: `{output['semantic_hint_counts']}`",
                f"- Tail-push / active-or-tail-push / no-4& delayed-tail events: `{output['tail_push_events']}` / `{output['active_or_tail_push_events']}` / `{output['no_4and_delayed_tail_events']}`",
                f"- History penalty / bonus events: `{output['history_penalty_events']}` / `{output['history_bonus_events']}`",
                f"- Harmonic policy / hold-until-next-touch events: `{output['harmonic_function_applied_events']}` / `{output['hold_until_next_touch_applied_events']}`",
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
