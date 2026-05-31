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
from jammate_engine.styles.bossa_nova import arrangement_policy, comping_patterns
from jammate_engine.styles.registry import get_style

DEMOS_DIR = PROJECT_ROOT / "demos"
LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
MILESTONE_ID = "v2_6_120"
MILESTONE_LABEL = "v2_6_120 — Engine Bossa Nova Two-beat Phrase Pair Local 1& Hold"
RESPONSE_PATTERN = "bossa_piano_half_region_1and_hold"
CALL_PATTERN = "bossa_piano_half_region_1_2"


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static = build_static_audit()
    runtime = [
        _generate_runtime_audit(_focus_score(), slug="bossa_nova_two_beat_phrase_focus", choruses=3, seed=120, tempo=132),
        _generate_runtime_audit(_blue_bossa_score(), slug="blue_bossa_bossa_nova_two_beat_phrase_pair", choruses=3, seed=12020, tempo=None),
    ]
    acceptance = _acceptance(static, runtime)
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": (
            "Add the user-requested Bossa two-beat phrase as style-owned, pitchless, ChordRegion-local piano comping vocabulary: "
            "one 2-beat region states local 1+2, and the following 2-beat region may answer on local 1& with a hold. "
            "The shared phrase-pair weighting now reads style metadata rather than hard-coding a Medium Swing cell name."
        ),
        "static_audit": static,
        "runtime_audits": runtime,
        "acceptance": acceptance,
        "recommended_next_task": "v2_6_121_engine_bossa_nova_two_beat_phrase_pair_listening_calibration",
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_two_beat_phrase_pair_local1and_hold_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_two_beat_phrase_pair_local1and_hold_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()
    half_candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 2.0})
    by_name = {candidate.name: candidate for candidate in half_candidates}
    call = by_name.get(CALL_PATTERN)
    response = by_name.get(RESPONSE_PATTERN)
    base_source = (PROJECT_ROOT / "src" / "jammate_engine" / "styles" / "base.py").read_text(encoding="utf-8")
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "style_registered": getattr(style, "name", None) == "bossa_nova",
        "policy_enabled": policy.get("piano_comping_two_beat_phrase_pair_policy") is True,
        "policy_version": policy.get("piano_comping_two_beat_phrase_pair_policy_version"),
        "bossa_policy_active": policy.get("bossa_nova_two_beat_phrase_pair_policy_active") is True,
        "candidate_names": sorted(by_name),
        "call_candidate_present": call is not None,
        "call_beats": list(call.rhythm_beats) if call else [],
        "call_role": (call.metadata.get("two_beat_phrase_pair_role") if call else None),
        "call_triggers": list(call.metadata.get("two_beat_phrase_pair_triggers_response_cells") or ()) if call else [],
        "response_candidate_present": response is not None,
        "response_beats": list(response.rhythm_beats) if response else [],
        "response_role": (response.metadata.get("two_beat_phrase_pair_role") if response else None),
        "response_responds_to": response.metadata.get("two_beat_phrase_pair_responds_to_cell") if response else None,
        "response_expression_hint": response.events[0].expression_hint if response and response.events else None,
        "response_semantic_hint": response.events[0].metadata.get("semantic_expression_hint") if response and response.events else None,
        "response_voicing_boundary": response.metadata.get("voicing_boundary") if response else None,
        "legacy_bar_first_terms_in_response": _legacy_terms(response) if response else [],
        "base_policy_no_medium_swing_cell_hardcode": "previous_cell == \"start_local2\"" not in base_source,
        "base_policy_records_history_when_phrase_policy_enabled": "piano_history_scorer or piano_two_beat_phrase_pair_policy" in base_source,
    }


def _legacy_terms(candidate: Any) -> list[str]:
    text = " ".join([candidate.name, candidate.category, str(candidate.metadata), " ".join(candidate.tags)]).lower()
    return sorted(term for term in ("two_chord_bar", "bar_first", "split_bar") if term in text)


def _focus_score() -> dict[str, Any]:
    bars = [
        {"chords": [{"beat": 1.0, "symbol": "Dm7"}, {"beat": 3.0, "symbol": "G7"}]},
        {"chords": [{"beat": 1.0, "symbol": "Cmaj7"}, {"beat": 3.0, "symbol": "A7"}]},
        {"chords": [{"beat": 1.0, "symbol": "Dm7"}, {"beat": 3.0, "symbol": "G7"}]},
        {"chords": [{"beat": 1.0, "symbol": "Cmaj7"}, {"beat": 3.0, "symbol": "Cmaj7"}]},
    ]
    return {
        "schema_version": "jammate_leadsheet_v2",
        "title": "Bossa Two-Beat Phrase Focus",
        "key": "C",
        "tempo": 132,
        "default_time_signature": {"numerator": 4, "denominator": 4},
        "metadata": {"melody_not_included": True, "fixture_role": "v2_6_120_two_beat_phrase_focus"},
        "sections": {"A": {"label": "A", "phrase": "A", "role": "normal", "bars": bars}},
        "written_form": [{"section": "A", "repeats": 4}],
    }


def _blue_bossa_score() -> dict[str, Any]:
    return json.loads((LEADSHEET_DIR / "blue_bossa.json").read_text(encoding="utf-8"))


def _generate_runtime_audit(score: dict[str, Any], *, slug: str, choruses: int, seed: int, tempo: int | None) -> dict[str, Any]:
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_demo.mid"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "bossa_nova",
            "tempo": int(tempo or score.get("tempo", 132)),
            "choruses": choruses,
            "seed": seed,
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
        }
    )
    return _summarize_runtime(dict(result.debug), midi_path=midi_path, ok=bool(result.ok), choruses=choruses, seed=seed)


def _summarize_runtime(debug: dict[str, Any], *, midi_path: Path, ok: bool, choruses: int, seed: int) -> dict[str, Any]:
    piano_rows = [row for row in debug.get("piano_musical_audit_events", []) if _pattern_event(row).get("track") == "piano"]
    active = [row for row in piano_rows if _pattern_event(row).get("status") == "active"]
    pattern_counts = Counter(str(_pattern_event(row).get("pattern_id")) for row in active)
    statuses = Counter(str((_pattern_event(row).get("metadata") or {}).get("two_beat_phrase_pair_policy_status")) for row in active if (_pattern_event(row).get("metadata") or {}).get("two_beat_phrase_pair_policy_status"))
    response_rows = [row for row in active if _pattern_event(row).get("pattern_id") == RESPONSE_PATTERN]
    response_onsets = [float(_pattern_event(row).get("local_beat") or -1.0) for row in response_rows]
    expression_summary = dict(debug.get("expression_foundation_audit") or {})
    return {
        "ok": ok,
        "choruses": choruses,
        "seed": seed,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "title": debug.get("title"),
        "style": debug.get("style"),
        "performance_bars": debug.get("performance_bars"),
        "note_events_by_track": debug.get("note_events_by_track"),
        "piano_pattern_counts": dict(pattern_counts),
        "phrase_policy_status_counts": dict(statuses),
        "call_event_count": int(pattern_counts.get(CALL_PATTERN, 0)),
        "response_event_count": int(pattern_counts.get(RESPONSE_PATTERN, 0)),
        "response_local_beats": sorted(set(response_onsets)),
        "expression_warning_count": expression_summary.get("warning_count"),
        "expression_missing_count": expression_summary.get("missing_expression_count"),
        "expression_cross_region_count": expression_summary.get("cross_region_count"),
        "expression_cross_next_event_count": expression_summary.get("cross_next_event_count"),
    }


def _pattern_event(row: dict[str, Any]) -> dict[str, Any]:
    event = row.get("pattern_event")
    return event if isinstance(event, dict) else {}


def _acceptance(static: dict[str, Any], runtime: list[dict[str, Any]]) -> dict[str, Any]:
    focus = runtime[0] if runtime else {}
    blue = runtime[1] if len(runtime) > 1 else {}
    checks = {
        "style_policy_and_candidates_present": static.get("style_registered") is True
        and static.get("policy_enabled") is True
        and static.get("policy_version") == MILESTONE_ID
        and static.get("bossa_policy_active") is True
        and static.get("call_candidate_present") is True
        and static.get("response_candidate_present") is True,
        "phrase_shape_is_region_local": static.get("call_beats") == [0.0, 1.0]
        and static.get("response_beats") == [0.5]
        and static.get("response_responds_to") == "half_region_1_2"
        and static.get("response_expression_hint") == "cell_soft_hold"
        and static.get("response_semantic_hint") == "soft_hold",
        "boundaries_preserved": static.get("response_voicing_boundary") == "pattern_is_pitchless"
        and static.get("legacy_bar_first_terms_in_response") == [],
        "shared_policy_is_not_medium_swing_cell_hardcoded": static.get("base_policy_no_medium_swing_cell_hardcode") is True
        and static.get("base_policy_records_history_when_phrase_policy_enabled") is True,
        "focus_demo_contains_phrase_response": focus.get("ok") is True
        and int(focus.get("call_event_count") or 0) > 0
        and int(focus.get("response_event_count") or 0) > 0
        and focus.get("response_local_beats") == [0.5]
        and int((focus.get("phrase_policy_status_counts") or {}).get("phrase_response_preferred_after_call", 0)) > 0,
        "blue_bossa_demo_still_generates": blue.get("ok") is True
        and int((blue.get("note_events_by_track") or {}).get("piano", 0)) > 0
        and int((blue.get("note_events_by_track") or {}).get("bass", 0)) > 0
        and int((blue.get("note_events_by_track") or {}).get("drums", 0)) > 0,
        "expression_boundary_clean": all(int(item.get("expression_warning_count") or 0) == 0 and int(item.get("expression_missing_count") or 0) == 0 and int(item.get("expression_cross_region_count") or 0) == 0 and int(item.get("expression_cross_next_event_count") or 0) == 0 for item in runtime),
    }
    return {"passed": all(checks.values()), "checks": checks}


def _render_report(summary: dict[str, Any]) -> str:
    static = summary["static_audit"]
    acceptance = summary["acceptance"]
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
        f"- Policy version: `{static.get('policy_version')}`",
        f"- Call pattern: `{CALL_PATTERN}` beats `{static.get('call_beats')}` role `{static.get('call_role')}`",
        f"- Response pattern: `{RESPONSE_PATTERN}` beats `{static.get('response_beats')}` role `{static.get('response_role')}`",
        f"- Response expression hint: `{static.get('response_expression_hint')}` / semantic `{static.get('response_semantic_hint')}`",
        f"- Shared policy no Medium Swing cell hard-code: `{static.get('base_policy_no_medium_swing_cell_hardcode')}`",
        "",
        "## Runtime demos",
        "",
    ]
    for item in summary["runtime_audits"]:
        lines.extend(
            [
                f"### {item.get('title')}",
                "",
                f"- MIDI: `{item.get('midi_path')}`",
                f"- Pattern counts: `{item.get('piano_pattern_counts')}`",
                f"- Phrase policy status counts: `{item.get('phrase_policy_status_counts')}`",
                f"- Response local beats: `{item.get('response_local_beats')}`",
                "",
            ]
        )
    lines.extend(["## Acceptance", "", f"Passed: `{acceptance.get('passed')}`", "", "```json", json.dumps(acceptance.get("checks"), indent=2, ensure_ascii=False), "```", "", f"Recommended next task: `{summary.get('recommended_next_task')}`", ""])
    return "\n".join(lines)


if __name__ == "__main__":
    main()
