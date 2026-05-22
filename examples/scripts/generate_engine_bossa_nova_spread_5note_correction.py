from __future__ import annotations

import json
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing.policy import ColorPolicyMode
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.selection.scorer import score_candidate
from jammate_engine.core.voicing.runtime.state import VoicingState
from jammate_engine.midi.channel_map import CHANNELS
from jammate_engine.midi.midi_writer import write_midi
from jammate_engine.realization.note_event_builder import NoteEvent
from jammate_engine.realization.voicing_policy_context_adapter import policy_with_event_voicing_context
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.bossa_nova import expression_policy, voicing_policy

DEMOS_DIR = PROJECT_ROOT / "demos"
LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
MILESTONE_ID = "v2_6_124"
MILESTONE_LABEL = "v2_6_124 — Engine Bossa Nova SPREAD 1+4 5-note Correction"


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static = _static_audit()
    ordinary = _ordinary_candidate_audit()
    spread_probe = _spread_probe_audit()
    spread_audition = _write_spread_5note_candidate_audition_demo()
    core_velocity_demo = _write_core_batida_velocity_focus_demo()
    runtime = _generate_blue_bossa_runtime_demo()
    summary = {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "scope": "Correct Bossa 5-note routing: OPEN/drop-family remains 4-note, generic_open fallback-only, occasional 5-note uses existing grouped-SPREAD 1+4 event-scoped policy. Core batida front velocity 48 is retained.",
        "static_audit": static,
        "ordinary_candidate_audit": ordinary,
        "spread_probe_audit": spread_probe,
        "runtime_audit": runtime,
        "spread_candidate_audition_demo": spread_audition,
        "core_velocity_focus_demo": core_velocity_demo,
    }
    summary["acceptance"] = _acceptance(summary)
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_spread_5note_correction_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_spread_5note_correction_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": summary["acceptance"]}, indent=2, ensure_ascii=False))
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def _expanded_policy():
    return replace(
        voicing_policy.get_voicing_policy(),
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
    )


def _static_audit() -> dict[str, Any]:
    policy = _expanded_policy()
    metadata = dict(policy.metadata or {})
    expr = expression_policy.get_expression_policy()
    spread_policy = dict(metadata.get("bossa_spread_5note_low_weight_policy") or {})
    return {
        "preferred_disposition": policy.preferred_disposition.value,
        "preferred_density": int(policy.preferred_density),
        "max_density": int(policy.max_density),
        "open_projection_methods": list(metadata.get("open_projection_methods") or ()),
        "generic_open_in_normal_method_pool": "generic_open" in set(metadata.get("open_projection_methods") or ()),
        "has_open_density_gate": "open_projection_method_density_gate" in metadata,
        "has_selector_tail_lane": "selector_tail_candidate_lane_policy" in metadata,
        "spread_policy": spread_policy,
        "core_short_velocity": int(expr.profiles["core_short"].velocity),
        "core_sustain_velocity": int(expr.profiles["core_sustain"].velocity),
    }


def _ordinary_candidate_audit() -> dict[str, Any]:
    policy = _expanded_policy()
    result: dict[str, Any] = {}
    for symbol in ("Cmaj7", "G7", "C6"):
        candidates = generate_candidates(symbol, policy)
        counts = Counter(f"d{int(c.density or 0)}:{c.disposition.value}:{c.metadata.get('active_open_projection_method')}" for c in candidates)
        result[symbol] = {
            "candidate_count": len(candidates),
            "density_disposition_method_counts": dict(counts),
            "open_5note_count": sum(1 for c in candidates if int(c.density or 0) == 5 and c.disposition.value == "open"),
            "generic_open_count": sum(1 for c in candidates if c.metadata.get("active_open_projection_method") == "generic_open"),
        }
    return result


def _spread_probe_policy(symbol: str = "Cmaj7"):
    base = _expanded_policy()
    event = PatternEvent(
        event_id="bossa_spread_5note_probe",
        track="piano",
        region_id="probe_region",
        chord_symbol=symbol,
        onset_beat=42.5,
        role="harmonic",
        expression_hint="core_sustain",
        local_beat=2.5,
        metadata={"region_performance_bar_index": 10, "region_chord_index": 0, "region_chorus_index": 0},
    )
    return policy_with_event_voicing_context(base, event)


def _spread_probe_audit() -> dict[str, Any]:
    policy = _spread_probe_policy("Cmaj7")
    metadata = dict(policy.metadata or {})
    candidates = generate_candidates("Cmaj7", policy)
    best = _best_candidate(candidates, policy)
    return {
        "policy_applied": bool(metadata.get("bossa_spread_5note_low_weight_policy_applied")),
        "selected_contract_id": (metadata.get("spread_grouping_mix_candidate_pool") or {}).get("selected_contract_id"),
        "candidate_count": len(candidates),
        "densities": sorted({int(c.density or 0) for c in candidates}),
        "dispositions": sorted({c.disposition.value for c in candidates}),
        "recipe_ids": sorted({str(c.recipe_id) for c in candidates}),
        "candidate_pool_sources": sorted({str(c.metadata.get("candidate_pool_source")) for c in candidates}),
        "best_candidate": best,
    }


def _best_candidate(candidates: list[Any], policy) -> dict[str, Any]:
    if not candidates:
        return {}
    scored = [(score_candidate(c, policy, VoicingState.empty()).total, c) for c in candidates]
    scored.sort(key=lambda item: item[0], reverse=True)
    score, candidate = scored[0]
    return {
        "score": round(float(score), 4),
        "notes": [int(n) for n in candidate.notes],
        "degrees": list(candidate.degrees),
        "density": int(candidate.density or 0),
        "disposition": candidate.disposition.value,
        "recipe_id": candidate.recipe_id,
        "candidate_pool_source": candidate.metadata.get("candidate_pool_source"),
    }


def _best_candidate_object(candidates: list[Any], policy):
    if not candidates:
        return None
    return max(candidates, key=lambda c: score_candidate(c, policy, VoicingState.empty()).total)


def _write_spread_5note_candidate_audition_demo() -> dict[str, Any]:
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_bossa_nova_spread_5note_candidate_audition_demo.mid"
    symbols = ("Cm9", "Fm9", "Dm7b5(11)", "G7b9b13", "Cm9", "Cmaj9", "F13", "Bbmaj9")
    events: list[NoteEvent] = []
    beat = 0.0
    for symbol in symbols:
        policy = _spread_probe_policy(symbol)
        candidates = generate_candidates(symbol, policy)
        best = _best_candidate_object(candidates, policy)
        if best is not None:
            for note in best.notes:
                events.append(NoteEvent(track="piano", channel=CHANNELS["piano"], note=int(note), velocity=58, start_beat=beat, duration_beats=1.65, timing_intent="straight"))
        beat += 2.0
    write_midi(events, midi_path, tempo_bpm=132)
    return {"midi_path": str(midi_path.relative_to(PROJECT_ROOT)), "symbol_sequence": list(symbols), "note_event_count": len(events)}


def _write_core_batida_velocity_focus_demo() -> dict[str, Any]:
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_bossa_nova_core_batida_velocity_48_focus_demo.mid"
    profiles = expression_policy.get_expression_policy().profiles
    chord = [60, 64, 67, 71]
    events: list[NoteEvent] = []
    for bar in range(4):
        start = bar * 4.0
        for offset, profile_name in ((0.0, "core_short"), (1.0, "core_short"), (2.5, "core_sustain")):
            profile = profiles[profile_name]
            for note in chord:
                events.append(NoteEvent(track="piano", channel=CHANNELS["piano"], note=note, velocity=int(profile.velocity), start_beat=start + offset, duration_beats=float(profile.duration_beats), timing_intent="straight"))
    write_midi(events, midi_path, tempo_bpm=132)
    return {"midi_path": str(midi_path.relative_to(PROJECT_ROOT)), "front_two_hit_velocity": int(profiles["core_short"].velocity), "sustain_velocity": int(profiles["core_sustain"].velocity)}


def _generate_blue_bossa_runtime_demo() -> dict[str, Any]:
    score = json.loads((LEADSHEET_DIR / "blue_bossa.json").read_text(encoding="utf-8"))
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_blue_bossa_bossa_nova_spread_5note_correction_demo.mid"
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
                "metadata": {"harmonic_expansion_enabled": True, "color_policy_mode": "style_safe_extensions", "bossa_spread_5note_correction_demo": True},
            },
        }
    )
    rows = []
    velocities = []
    for row in list(result.debug.get("piano_musical_audit_events") or []):
        voicing = dict(row.get("voicing") or {})
        metadata = dict(voicing.get("metadata") or {})
        expression = dict(row.get("expression") or {})
        pattern_event = dict(row.get("pattern_event") or {})
        if voicing:
            rows.append(
                {
                    "density": int(voicing.get("density") or 0),
                    "disposition": voicing.get("disposition") or metadata.get("disposition"),
                    "method": metadata.get("active_open_projection_method") or metadata.get("disposition_projection_method"),
                    "recipe_id": voicing.get("recipe_id") or metadata.get("recipe_id"),
                    "candidate_pool_source": metadata.get("candidate_pool_source"),
                    "chord_symbol": voicing.get("chord_symbol"),
                }
            )
        if pattern_event.get("pattern_id") == "bossa_piano_core_batida_1_2_3and" and pattern_event.get("local_beat") in {0.0, 1.0}:
            velocities.append(int(expression.get("velocity") or 0))
    counts = Counter(f"d{r['density']}:{r['disposition']}:{r['method']}:{r['recipe_id']}" for r in rows)
    return {
        "ok": bool(result.ok),
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "density_method_counts": dict(counts),
        "five_note_spread_selected_count": sum(1 for r in rows if r["density"] == 5 and r["disposition"] == "spread" and r["recipe_id"] == "spread_1plus4_contract"),
        "open_5note_selected_count": sum(1 for r in rows if r["density"] == 5 and r["disposition"] == "open"),
        "generic_open_selected_count": sum(1 for r in rows if r["method"] == "generic_open"),
        "four_note_open_selected_count": sum(1 for r in rows if r["density"] == 4 and r["disposition"] == "open"),
        "piano_harmonic_event_count": len(rows),
        "core_batida_front_velocities_first_four": velocities[:4],
    }


def _acceptance(summary: dict[str, Any]) -> dict[str, Any]:
    static = summary["static_audit"]
    ordinary = summary["ordinary_candidate_audit"]
    spread = summary["spread_probe_audit"]
    runtime = summary["runtime_audit"]
    checks = {
        "no_open_density_gate_or_tail_lane": not static["has_open_density_gate"] and not static["has_selector_tail_lane"],
        "generic_open_not_in_bossa_normal_pool": not static["generic_open_in_normal_method_pool"],
        "ordinary_pool_has_no_open_5note_or_generic": all(v["open_5note_count"] == 0 and v["generic_open_count"] == 0 for v in ordinary.values()),
        "event_scoped_spread_probe_uses_1plus4_5note": spread["policy_applied"] and spread["densities"] == [5] and spread["dispositions"] == ["spread"] and spread["recipe_ids"] == ["spread_1plus4_contract"],
        "runtime_has_low_frequency_spread_5note": runtime["ok"] and runtime["five_note_spread_selected_count"] >= 2 and runtime["four_note_open_selected_count"] > runtime["five_note_spread_selected_count"],
        "runtime_has_no_open_5note_or_generic_open": runtime["open_5note_selected_count"] == 0 and runtime["generic_open_selected_count"] == 0,
        "core_batida_front_velocity_48_retained": bool(runtime["core_batida_front_velocities_first_four"]) and set(runtime["core_batida_front_velocities_first_four"]) == {48},
    }
    return {"passed": all(checks.values()), "checks": checks}


def _render_report(summary: dict[str, Any]) -> str:
    runtime = summary["runtime_audit"]
    static = summary["static_audit"]
    lines = [
        f"# {MILESTONE_LABEL}",
        "",
        "## Correction",
        "",
        "- Removed the wrong OPEN/generic_open 5-note direction.",
        "- Bossa ordinary body remains 4-note OPEN drop-family.",
        "- Low-frequency 5-note color now requests existing grouped-SPREAD `spread_1plus4_contract` event-scoped.",
        "- `generic_open` remains fallback/rescue only.",
        "",
        "## Static audit",
        "",
        f"- open methods: `{static['open_projection_methods']}`",
        f"- has open density gate: `{static['has_open_density_gate']}`",
        f"- has selector tail lane: `{static['has_selector_tail_lane']}`",
        f"- core_short velocity: `{static['core_short_velocity']}`",
        "",
        "## Runtime audit",
        "",
        f"- density/method counts: `{runtime['density_method_counts']}`",
        f"- spread 5-note selected: `{runtime['five_note_spread_selected_count']}`",
        f"- open 5-note selected: `{runtime['open_5note_selected_count']}`",
        f"- generic_open selected: `{runtime['generic_open_selected_count']}`",
        f"- core batida front velocities: `{runtime['core_batida_front_velocities_first_four']}`",
        "",
        "## Acceptance",
        "",
        f"- passed: `{summary['acceptance']['passed']}`",
        f"- checks: `{summary['acceptance']['checks']}`",
        "",
        "## Demos",
        "",
        f"- Blue Bossa runtime: `{runtime['midi_path']}`",
        f"- SPREAD 5-note audition: `{summary['spread_candidate_audition_demo']['midi_path']}`",
        f"- Core batida velocity focus: `{summary['core_velocity_focus_demo']['midi_path']}`",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
