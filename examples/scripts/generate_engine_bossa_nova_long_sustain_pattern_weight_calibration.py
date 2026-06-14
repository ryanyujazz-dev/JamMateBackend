from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.bossa_nova import arrangement_policy, comping_patterns

DEMOS_DIR = PROJECT_ROOT / "demos"
LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
MILESTONE_ID = "v2_6_125"
MILESTONE_LABEL = "v2_6_125 — Engine Bossa Nova Long-Sustain Pattern Weight Calibration"

# Same seed/output configuration as the v2_6_124 Blue Bossa runtime audit, kept as
# an explicit listening baseline for this weight-only pass.
BASELINE_V2_6_124_BLUE_BOSSA = {
    "piano_harmonic_event_count": 95,
    "pattern_counts": {
        "bossa_piano_cell_A_1_3and": 28,
        "bossa_piano_cell_A_1": 13,
        "bossa_piano_cell_A_1_2and": 10,
        "bossa_piano_core_batida_1_2_3and": 21,
        "bossa_piano_cell_A_1_3": 6,
        "bossa_piano_cell_A_1_2_3and": 6,
        "bossa_piano_half_region_1_2": 6,
        "bossa_piano_half_region_1and_hold": 3,
        "bossa_piano_cell_B_1and_3and": 2,
    },
    "extreme_long_duration_event_count_ge_3_beats": 17,
    "long_hold_weighted_exposure_patterns": {
        "bossa_piano_cell_A_1_3and": 54.76,
        "bossa_piano_cell_A_1": 50.50,
    },
}


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static = _static_pattern_weight_audit()
    runtime = _generate_blue_bossa_runtime_demo()
    summary = {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "label": MILESTONE_LABEL,
        "scope": (
            "Reduce slightly excessive Bossa long-sustain feeling through style-owned piano comping pattern weights only. "
            "No voicing, source inventory, OPEN/SPREAD routing, generic_open fallback, expression numeric profile, bass/drums, API, Agent, or HarmonyOS logic is changed."
        ),
        "baseline_v2_6_124_blue_bossa": BASELINE_V2_6_124_BLUE_BOSSA,
        "static_pattern_weight_audit": static,
        "runtime_audit": runtime,
    }
    summary["acceptance"] = _acceptance(summary)
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_long_sustain_pattern_weight_calibration_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_long_sustain_pattern_weight_calibration_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": summary["acceptance"]}, indent=2, ensure_ascii=False))
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def _static_pattern_weight_audit() -> dict[str, Any]:
    policy = arrangement_policy.get_arrangement_policy()
    candidates = tuple(comping_patterns.get_pattern_candidates({}, apply_context_policy=False))
    by_name = {candidate.name: candidate for candidate in candidates}
    watched = (
        "bossa_piano_cell_A_1",
        "bossa_piano_cell_A_1_2and",
        "bossa_piano_cell_A_1_3and",
        "bossa_piano_cell_A_1_3",
        "bossa_piano_cell_A_1_2_3and",
        "bossa_piano_cell_B_1and",
        "bossa_piano_cell_B_1and_3and",
    )
    return {
        "pattern_library_version": comping_patterns.PATTERN_LIBRARY_VERSION,
        "long_sustain_calibration_version": comping_patterns.BOSSA_LONG_SUSTAIN_WEIGHT_CALIBRATION_VERSION,
        "arrangement_policy_declares_calibration": bool(policy.get("bossa_nova_long_sustain_pattern_weight_calibration_active")),
        "arrangement_policy_no_voicing_change": bool(policy.get("bossa_nova_long_sustain_pattern_weight_calibration_no_voicing_change")),
        "arrangement_policy_no_expression_numeric_change": bool(policy.get("bossa_nova_long_sustain_pattern_weight_calibration_no_expression_numeric_change")),
        "candidate_weights": {name: float(by_name[name].weight) for name in watched if name in by_name},
        "boundary_notes": list(comping_patterns.BOUNDARY_NOTES),
    }


def _generate_blue_bossa_runtime_demo() -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / "blue_bossa.json").read_text(encoding="utf-8"))
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_blue_bossa_bossa_nova_long_sustain_pattern_weight_demo.mid"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "bossa_nova",
            "tempo": int(score.get("tempo", 140)),
            "choruses": 3,
            "seed": 6124,
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
            "voicing_override": {
                "enabled": True,
                "harmonic_expansion_enabled": True,
                "color_policy_mode": "style_safe_extensions",
                "metadata": {
                    "harmonic_expansion_enabled": True,
                    "color_policy_mode": "style_safe_extensions",
                    "bossa_long_sustain_pattern_weight_calibration_demo": True,
                },
            },
        }
    )
    rows = list(result.debug.get("piano_musical_audit_events") or [])
    pattern_counts: Counter[str] = Counter()
    cell_counts: Counter[str] = Counter()
    expression_counts: Counter[str] = Counter()
    duration_counts: Counter[str] = Counter()
    duration_by_pattern: defaultdict[str, float] = defaultdict(float)
    voicing_rows: list[dict[str, Any]] = []
    core_front_velocities: list[int] = []

    for row in rows:
        pattern_event = dict(row.get("pattern_event") or {})
        pattern_metadata = dict(pattern_event.get("metadata") or {})
        expression = dict(row.get("expression") or {})
        voicing = dict(row.get("voicing") or {})
        voicing_metadata = dict(voicing.get("metadata") or {})
        pattern_id = str(pattern_event.get("pattern_id") or "")
        rhythmic_cell = str(pattern_metadata.get("rhythmic_cell") or "")
        duration = float(expression.get("duration_beats") or 0.0)
        pattern_counts[pattern_id] += 1
        cell_counts[rhythmic_cell] += 1
        expression_counts[str(pattern_event.get("expression_hint") or "")] += 1
        duration_counts[f"{round(duration, 2):.2f}"] += 1
        duration_by_pattern[pattern_id] += duration
        if voicing:
            voicing_rows.append(
                {
                    "density": int(voicing.get("density") or 0),
                    "disposition": voicing.get("disposition") or voicing_metadata.get("disposition"),
                    "method": voicing_metadata.get("active_open_projection_method") or voicing_metadata.get("disposition_projection_method"),
                    "recipe_id": voicing.get("recipe_id") or voicing_metadata.get("recipe_id"),
                }
            )
        if pattern_id == "bossa_piano_core_batida_1_2_3and" and pattern_event.get("local_beat") in {0.0, 1.0}:
            core_front_velocities.append(int(expression.get("velocity") or 0))

    baseline = BASELINE_V2_6_124_BLUE_BOSSA
    current_long_hold_exposure = {
        "bossa_piano_cell_A_1_3and": round(duration_by_pattern["bossa_piano_cell_A_1_3and"], 2),
        "bossa_piano_cell_A_1": round(duration_by_pattern["bossa_piano_cell_A_1"], 2),
    }
    baseline_long_hold_exposure = baseline["long_hold_weighted_exposure_patterns"]
    return {
        "ok": bool(result.ok),
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "piano_harmonic_event_count": len(rows),
        "pattern_counts": dict(pattern_counts),
        "cell_counts": dict(cell_counts),
        "expression_counts": dict(expression_counts),
        "duration_counts": dict(duration_counts),
        "extreme_long_duration_event_count_ge_3_beats": sum(count for duration, count in duration_counts.items() if float(duration) >= 3.0),
        "current_long_hold_weighted_exposure_patterns": current_long_hold_exposure,
        "baseline_long_hold_weighted_exposure_patterns": baseline_long_hold_exposure,
        "a1_3and_count_delta_vs_v2_6_124": int(pattern_counts["bossa_piano_cell_A_1_3and"]) - int(baseline["pattern_counts"]["bossa_piano_cell_A_1_3and"]),
        "a1_count_delta_vs_v2_6_124": int(pattern_counts["bossa_piano_cell_A_1"]) - int(baseline["pattern_counts"]["bossa_piano_cell_A_1"]),
        "a1_2and_count_delta_vs_v2_6_124": int(pattern_counts["bossa_piano_cell_A_1_2and"]) - int(baseline["pattern_counts"]["bossa_piano_cell_A_1_2and"]),
        "long_exposure_delta_vs_v2_6_124": {
            key: round(float(current_long_hold_exposure[key]) - float(baseline_long_hold_exposure[key]), 2)
            for key in current_long_hold_exposure
        },
        "five_note_spread_1plus4_selected_count": sum(1 for row in voicing_rows if row["density"] == 5 and row["disposition"] == "spread" and row["recipe_id"] == "spread_1plus4_contract"),
        "open_5note_selected_count": sum(1 for row in voicing_rows if row["density"] == 5 and row["disposition"] == "open"),
        "generic_open_selected_count": sum(1 for row in voicing_rows if row["method"] == "generic_open"),
        "four_note_open_selected_count": sum(1 for row in voicing_rows if row["density"] == 4 and row["disposition"] == "open"),
        "core_batida_front_velocities_first_four": core_front_velocities[:4],
    }


def _acceptance(summary: dict[str, Any]) -> dict[str, Any]:
    static = summary["static_pattern_weight_audit"]
    runtime = summary["runtime_audit"]
    weights = static["candidate_weights"]
    checks = {
        "pattern_weight_only_boundary_declared": static["arrangement_policy_declares_calibration"] and static["arrangement_policy_no_voicing_change"] and static["arrangement_policy_no_expression_numeric_change"],
        "long_hold_base_weights_reduced": weights["bossa_piano_cell_A_1"] <= 108.0 and weights["bossa_piano_cell_A_1_3and"] <= 198.0 and weights["bossa_piano_cell_A_1_3"] <= 56.0,
        "shorter_split_cells_lifted": weights["bossa_piano_cell_A_1_2and"] >= 216.0 and weights["bossa_piano_cell_A_1_2_3and"] >= 236.0,
        "runtime_reduces_sparse_long_hold_cells": runtime["a1_3and_count_delta_vs_v2_6_124"] <= -4 and runtime["a1_count_delta_vs_v2_6_124"] <= -2,
        "runtime_lifts_shorter_split_cell": runtime["a1_2and_count_delta_vs_v2_6_124"] >= 6,
        "runtime_reduces_extreme_long_duration_events": runtime["extreme_long_duration_event_count_ge_3_beats"] <= 13,
        "voicing_route_unchanged": runtime["five_note_spread_1plus4_selected_count"] >= 2 and runtime["open_5note_selected_count"] == 0 and runtime["generic_open_selected_count"] == 0,
        "core_batida_velocity_48_retained": bool(runtime["core_batida_front_velocities_first_four"]) and set(runtime["core_batida_front_velocities_first_four"]) == {48},
    }
    return {"passed": all(checks.values()), "checks": checks}


def _render_report(summary: dict[str, Any]) -> str:
    runtime = summary["runtime_audit"]
    static = summary["static_pattern_weight_audit"]
    acceptance = summary["acceptance"]
    weights = static["candidate_weights"]
    return f"""# {MILESTONE_LABEL}

## Scope

{summary['scope']}

## Pattern weight calibration

| Pattern | Weight |
|---|---:|
| A_1 sparse hold | {weights.get('bossa_piano_cell_A_1')} |
| A_1_3& long-gap hold | {weights.get('bossa_piano_cell_A_1_3and')} |
| A_1_3 square hold | {weights.get('bossa_piano_cell_A_1_3')} |
| A_1_2& split cell | {weights.get('bossa_piano_cell_A_1_2and')} |
| A_1_2_3& split/core-like ordinary cell | {weights.get('bossa_piano_cell_A_1_2_3and')} |

## Blue Bossa runtime audit

- MIDI: `{runtime['midi_path']}`
- Piano harmonic events: {runtime['piano_harmonic_event_count']}
- `A_1_3&` count delta vs v2_6_124: {runtime['a1_3and_count_delta_vs_v2_6_124']}
- `A_1` count delta vs v2_6_124: {runtime['a1_count_delta_vs_v2_6_124']}
- `A_1_2&` count delta vs v2_6_124: {runtime['a1_2and_count_delta_vs_v2_6_124']}
- Extreme long duration events (>= 3 beats): {runtime['extreme_long_duration_event_count_ge_3_beats']}
- 5-note SPREAD 1+4 selected: {runtime['five_note_spread_1plus4_selected_count']}
- OPEN 5-note selected: {runtime['open_5note_selected_count']}
- generic_open selected: {runtime['generic_open_selected_count']}
- Core batida front velocities: {runtime['core_batida_front_velocities_first_four']}

## Pattern counts

```json
{json.dumps(runtime['pattern_counts'], indent=2, ensure_ascii=False)}
```

## Acceptance

```json
{json.dumps(acceptance, indent=2, ensure_ascii=False)}
```
"""


if __name__ == "__main__":
    main()
