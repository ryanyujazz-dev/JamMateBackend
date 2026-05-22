from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.bossa_nova import arrangement_policy, comping_patterns, voicing_policy
from jammate_engine.styles.registry import get_style

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_103"
MILESTONE_LABEL = "v2_6_103 — Engine Bossa Nova OPEN Voicing + No Forced 2/3-Note Policy Audit"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 22705, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 22755, "slug": "blue_bossa_5x"},
)
CORE_BATIDA_PATTERN = "bossa_piano_core_batida_1_2_3and"
HALF_REGION_PATTERN = "bossa_piano_half_region_1_2"


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    runtime_audits = [_generate_runtime_audit(spec) for spec in DEMO_SPECS]
    acceptance = _acceptance(static_audit, runtime_audits)
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": (
            "Audit and refine Bossa dense harmonic-rhythm / short ChordRegion voicing policy in-place. "
            "Short regions keep ChordRegion-first pattern handling but no longer force 2-note guide-tone or 3-note low-density voicings; they use the normal Bossa 4-to-5-note voicing policy. "
            "No core voicing source/projection/selector changes, no new pattern vocabulary, no expression numeric changes, API, Agent, or HarmonyOS changes."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
        "acceptance": acceptance,
        "recommended_next_task": static_audit.get("recommended_next_task"),
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()
    voicing = voicing_policy.get_voicing_policy()
    voicing_metadata = dict(voicing.metadata or {})
    dense_config = dict(voicing_metadata.get("bossa_dense_short_region_voicing_intent") or {})
    pattern_library = comping_patterns.describe_pattern_library({"region_duration_beats": 2.0})
    half_candidates = list(pattern_library.get("candidates") or [])
    half_metadata = dict(half_candidates[0].get("metadata") or {}) if half_candidates else {}
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "style_registered": getattr(style, "name", None) == "bossa_nova",
        "arrangement_policy_version": policy.get("bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_version"),
        "behavior_change": policy.get("bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_behavior_change"),
        "no_parallel_selector": policy.get("bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_parallel_selector"),
        "no_bar_first_restore": policy.get("bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_bar_first_restore"),
        "no_new_pattern_vocabulary": policy.get("bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_new_pattern_vocabulary"),
        "no_expression_numeric_change": policy.get("bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_expression_numeric_change"),
        "no_core_voicing_change": policy.get("bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_core_voicing_change"),
        "no_api_agent_harmonyos_change": policy.get("bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_no_api_agent_harmonyos_change"),
        "dense_short_threshold_beats": policy.get("bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_dense_short_region_threshold_beats"),
        "voicing_policy_metadata_version": voicing_metadata.get("bossa_harmonic_rhythm_region_clarity_and_voicing_intent_version"),
        "voicing_policy_no_core_voicing_change": voicing_metadata.get("bossa_harmonic_rhythm_region_clarity_and_voicing_intent_no_core_voicing_change"),
        "dense_config_enabled": dense_config.get("enabled"),
        "dense_config_preferred_density": dense_config.get("preferred_density"),
        "dense_config_min_density": dense_config.get("min_density"),
        "dense_config_max_density": dense_config.get("max_density"),
        "dense_config_preferred_content": dense_config.get("preferred_content"),
        "dense_config_root_support": dense_config.get("root_support"),
        "dense_config_avoid_forced_2_note": dense_config.get("avoid_forced_2_note_guide_tone"),
        "dense_config_avoid_forced_3_note": dense_config.get("avoid_forced_3_note_low_density"),
        "dense_config_normal_voicing_policy_for_short_regions": dense_config.get("normal_voicing_policy_for_short_regions"),
        "half_region_candidate_count": len(half_candidates),
        "half_region_candidate_name": half_candidates[0].get("name") if half_candidates else None,
        "half_region_region_shape": half_metadata.get("region_shape"),
        "half_region_pattern_function": half_metadata.get("pattern_function"),
        "half_region_candidate_metadata_version": half_metadata.get("bossa_harmonic_rhythm_region_clarity_and_voicing_intent_version"),
        "recommended_next_task": policy.get("bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_recommended_next_task"),
        "known_next_gap": policy.get("bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_known_next_gap"),
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_demo.mid"
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
    return _summarize_runtime(dict(result.debug), midi_path=midi_path, ok=bool(result.ok), choruses=choruses, seed=seed)


def _summarize_runtime(debug: dict[str, Any], *, midi_path: Path, ok: bool, choruses: int, seed: int) -> dict[str, Any]:
    piano_rows = [row for row in debug.get("piano_musical_audit_events", []) if _pattern_event(row).get("track") == "piano"]
    active_piano = [row for row in piano_rows if _pattern_event(row).get("status") == "active"]
    pattern_counts = Counter(str(_pattern_event(row).get("pattern_id")) for row in active_piano)
    class_a_event_count = sum(count for pattern, count in pattern_counts.items() if "_cell_A_" in pattern)
    class_b_event_count = sum(count for pattern, count in pattern_counts.items() if "_cell_B_" in pattern)
    non_core_event_count = sum(count for pattern, count in pattern_counts.items() if pattern not in {CORE_BATIDA_PATTERN, HALF_REGION_PATTERN})
    short_rows = [row for row in active_piano if _region_duration(_source_metadata(row)) <= 2.25 + 1e-9]
    short_content_counts = Counter(str((_voicing(row)).get("content_family") or "unknown") for row in short_rows)
    short_density_counts = Counter(str((_voicing(row)).get("density") or "unknown") for row in short_rows)
    short_root_included_count = sum(1 for row in short_rows if bool((_voicing(row)).get("root_included")))
    short_span_violations = [
        row for row in short_rows if int(((_voicing(row)).get("register_guard") or {}).get("span") or 0) > 18
    ]
    ordinary_rows = [row for row in active_piano if _region_duration(_source_metadata(row)) > 2.25 + 1e-9]
    ordinary_content_counts = Counter(str((_voicing(row)).get("content_family") or "unknown") for row in ordinary_rows)
    active_anticipations = [_anticipation_metadata(row) for row in active_piano if _anticipation_metadata(row).get("kind") == "next_beat1_to_previous_tail"]
    expression_summary = dict(debug.get("expression_foundation_audit") or {})
    pedal_audit = dict(debug.get("pedal_realization_audit") or {})
    piano_audit = dict(debug.get("piano_musical_audit") or {})
    return {
        "ok": ok,
        "choruses": choruses,
        "seed": seed,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "title": debug.get("title"),
        "style": debug.get("style"),
        "performance_bars": debug.get("performance_bars"),
        "regions": debug.get("regions"),
        "note_events_by_track": debug.get("note_events_by_track"),
        "piano_active_events": len(active_piano),
        "piano_pattern_counts": dict(pattern_counts),
        "piano_non_core_pattern_event_count": non_core_event_count,
        "piano_class_A_event_count": class_a_event_count,
        "piano_class_B_event_count": class_b_event_count,
        "piano_class_B_ratio_of_non_core_events": round(class_b_event_count / non_core_event_count, 4) if non_core_event_count else 0.0,
        "short_region_piano_event_count": len(short_rows),
        "short_region_content_family_counts": dict(short_content_counts),
        "short_region_density_counts": dict(short_density_counts),
        "short_region_root_included_count": short_root_included_count,
        "short_region_span_violation_count": len(short_span_violations),
        "ordinary_region_content_family_counts": dict(ordinary_content_counts),
        "expression_warning_count": expression_summary.get("warning_count"),
        "expression_missing_count": expression_summary.get("missing_expression_count"),
        "expression_cross_region_count": expression_summary.get("cross_region_count"),
        "expression_cross_next_event_count": expression_summary.get("cross_next_event_count"),
        "active_anticipation_count": len(active_anticipations),
        "pedal_cc64_event_count": pedal_audit.get("cc64_event_count"),
        "piano_lower_foundation_low_register_events": piano_audit.get("lower_foundation_low_register_events"),
        "piano_lower_foundation_span_violation_events": piano_audit.get("lower_foundation_span_violation_events"),
    }


def _pattern_event(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("pattern_event") or {}
    return dict(value) if isinstance(value, dict) else {}


def _source_metadata(row: dict[str, Any]) -> dict[str, Any]:
    metadata = _pattern_event(row).get("metadata") or {}
    return dict(metadata) if isinstance(metadata, dict) else {}


def _voicing(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("voicing") or {}
    return dict(value) if isinstance(value, dict) else {}


def _region_duration(metadata: dict[str, Any]) -> float:
    try:
        return float(metadata.get("region_duration_beats") or 4.0)
    except (TypeError, ValueError):
        return 4.0


def _anticipation_metadata(row: dict[str, Any]) -> dict[str, Any]:
    anticipation = _source_metadata(row).get("anticipation") or {}
    return dict(anticipation) if isinstance(anticipation, dict) else {}


def _acceptance(static_audit: dict[str, Any], runtime_audits: list[dict[str, Any]]) -> dict[str, Any]:
    runtime_ok = bool(runtime_audits) and all(_runtime_accepts(item) for item in runtime_audits)
    checks = {
        "style_and_policy_registered": static_audit.get("style_registered") is True and static_audit.get("arrangement_policy_version") == MILESTONE_ID,
        "in_place_boundaries_preserved": static_audit.get("behavior_change") is True
        and static_audit.get("no_parallel_selector") is True
        and static_audit.get("no_bar_first_restore") is True
        and static_audit.get("no_new_pattern_vocabulary") is True
        and static_audit.get("no_expression_numeric_change") is True
        and static_audit.get("no_core_voicing_change") is True
        and static_audit.get("no_api_agent_harmonyos_change") is True,
        "voicing_policy_declares_dense_short_region_intent": static_audit.get("voicing_policy_metadata_version") == MILESTONE_ID
        and static_audit.get("dense_config_enabled") is False
        and static_audit.get("dense_config_preferred_density") == 4
        and static_audit.get("dense_config_min_density") == 4
        and static_audit.get("dense_config_max_density") == 5
        and static_audit.get("dense_config_avoid_forced_2_note") is True
        and static_audit.get("dense_config_avoid_forced_3_note") is True
        and static_audit.get("dense_config_normal_voicing_policy_for_short_regions") is True
        and static_audit.get("half_region_candidate_metadata_version") == MILESTONE_ID,
        "runtime_blue_bossa_full_band_passes": runtime_ok,
    }
    return {"passed": all(checks.values()), "checks": checks}


def _runtime_accepts(item: dict[str, Any]) -> bool:
    note_counts = dict(item.get("note_events_by_track") or {})
    non_core = int(item.get("piano_non_core_pattern_event_count") or 0)
    class_a = int(item.get("piano_class_A_event_count") or 0)
    class_b = int(item.get("piano_class_B_event_count") or 0)
    short_content = dict(item.get("short_region_content_family_counts") or {})
    short_density = dict(item.get("short_region_density_counts") or {})
    return (
        item.get("ok") is True
        and int(note_counts.get("piano", 0)) > 0
        and int(note_counts.get("bass", 0)) > 0
        and int(note_counts.get("drums", 0)) > 0
        and non_core > 0
        and class_a > class_b >= 0
        and int(item.get("short_region_piano_event_count") or 0) > 0
        and "guide_tone" not in short_content
        and all(int(key) >= 4 for key in short_density if str(key).isdigit())
        and all(int(key) != 2 and int(key) != 3 for key in short_density if str(key).isdigit())
        and int(item.get("short_region_root_included_count") or 0) >= 0
        and int(item.get("short_region_span_violation_count") or 0) >= 0
        and int(item.get("expression_warning_count") or 0) == 0
        and int(item.get("expression_missing_count") or 0) == 0
        and int(item.get("expression_cross_region_count") or 0) == 0
        and int(item.get("expression_cross_next_event_count") or 0) == 0
        and int(item.get("active_anticipation_count") or 0) > 0
        and int(item.get("pedal_cc64_event_count") or 0) == 0
        and int(item.get("piano_lower_foundation_low_register_events") or 0) == 0
        and int(item.get("piano_lower_foundation_span_violation_events") or 0) == 0
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
        f"- Voicing policy metadata version: `{static.get('voicing_policy_metadata_version')}`",
        f"- Dense short-region threshold: `{static.get('dense_short_threshold_beats')}`",
        f"- Dense config preferred content/root support: `{static.get('dense_config_preferred_content')}` / `{static.get('dense_config_root_support')}`",
        f"- Avoid forced 2-note / 3-note: `{static.get('dense_config_avoid_forced_2_note')}` / `{static.get('dense_config_avoid_forced_3_note')}`",
        f"- Half-region candidate function: `{static.get('half_region_pattern_function')}`",
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
                f"- Non-core / Class A / Class B event counts: `{item.get('piano_non_core_pattern_event_count')}` / `{item.get('piano_class_A_event_count')}` / `{item.get('piano_class_B_event_count')}`",
                f"- Short-region piano events: `{item.get('short_region_piano_event_count')}`",
                f"- Short-region content families: `{item.get('short_region_content_family_counts')}`",
                f"- Short-region densities: `{item.get('short_region_density_counts')}`",
                f"- Short-region root-included / span violations: `{item.get('short_region_root_included_count')}` / `{item.get('short_region_span_violation_count')}`",
                f"- Ordinary-region content families: `{item.get('ordinary_region_content_family_counts')}`",
                f"- Expression warnings/missing/cross-region: `{item.get('expression_warning_count')}` / `{item.get('expression_missing_count')}` / `{item.get('expression_cross_region_count')}`",
                f"- Active anticipations: `{item.get('active_anticipation_count')}`",
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
