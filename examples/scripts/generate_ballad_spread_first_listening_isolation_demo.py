from __future__ import annotations

import json
import sys
from collections import Counter
from statistics import mean
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.runtime.generate import generate_accompaniment

LEADSHEET = PROJECT_ROOT / "examples" / "leadsheets" / "misty.json"
DEMOS_DIR = PROJECT_ROOT / "demos"
OUTPUT = DEMOS_DIR / "v2_2_56_misty_jazz_ballad_spread_1plus3_pilot_demo.mid"
AUDIT_OUTPUT = DEMOS_DIR / "v2_2_56_misty_jazz_ballad_spread_1plus3_pilot_audit_summary.json"


def _first_listening_voicing_override() -> dict[str, Any]:
    """Explicit-only Ballad SPREAD 1+3 pilot isolation metadata for v2_2_56.

    This is intentionally a demo/listening request, not a Jazz Ballad default
    style-policy change.  The override opens the runtime enablement guard and
    forces the selector pool to spread_1plus3_contract when it exists; fallback
    is used only if that contract cannot be built at all.
    """

    return {
        "enabled": True,
        "pattern_mode": "region_start_anchor_only",
        "disable_anticipation": True,
        "mute_bass": False,
        "expression_hint": "sustain",
        "metadata": {
            "style": "jazz_ballad",
            "primary_family": "spread",
            "allowed_families": ["spread"],
            "spread_selector_enabled": True,
            "ballad_spread_runtime_pilot": {
                "version": "v2_2_56",
                "enabled": True,
                "scene": "warm_spread_phrase",
                "contract_ids": ["spread_1plus3_contract"],
                "preferred_contract_ids": ["spread_1plus3_contract"],
                "runtime_boundary": "first_listening_isolation_only",
            },
            "ballad_spread_runtime_safe_dry_run": {
                "version": "v2_2_56",
                "dry_run_enabled": True,
                "candidate_conversion_allowed": True,
                "style_runtime_wiring_enabled": False,
            },
            "spread_runtime_adapter_skeleton": {
                "version": "v2_2_56",
                "adapter_conversion_allowed": True,
            },
            "ballad_spread_runtime_candidate_pool": {
                "version": "v2_2_56",
                "candidate_pool_enabled": True,
                "adapter_conversion_allowed": True,
                "candidate_pool_merge_allowed": True,
                "candidate_generator_wiring_allowed": True,
                "fallback_to_existing_pool": True,
                "style_runtime_default_enabled": False,
            },
            "ballad_spread_pilot_selection_weight_fallback_audit": {
                "version": "v2_2_56",
                "audit_enabled": True,
                "fallback_required": True,
                "max_spread_candidate_share": 0.35,
                "max_spread_score_margin": 0.15,
                "candidate_order_is_selection_priority": False,
            },
            "ballad_spread_pilot_runtime_enablement_guard": {
                "version": "v2_2_56",
                "runtime_guard_enabled": True,
                "listening_isolation_enabled": True,
                "first_listening_isolation_only": True,
                "fallback_required": True,
                "style_runtime_default_enabled": False,
                "default_style_runtime_unchanged": True,
                "runtime_pilot_enabled": True,
                "runtime_enabled": True,
            },
            "spread_contract_true_isolation": {
                "version": "v2_2_56",
                "enabled": True,
                "required_recipe_id": "spread_1plus3_contract",
                "fallback_only_when_missing": True,
                "candidate_pool_mode": "spread_only_when_available",
            },
        },
    }



def _counter_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: int(value) for key, value in sorted(counter.items())}


def _avg(values: list[int | float]) -> float:
    return round(float(mean(values)), 3) if values else 0.0


def _spread_1plus3_audit(debug: dict[str, Any]) -> dict[str, Any]:
    events = list(debug.get("piano_musical_audit_events") or [])
    methods: Counter[str] = Counter()
    source_families: Counter[str] = Counter()
    source_degree_orders: Counter[str] = Counter()
    lower_recipes: Counter[str] = Counter()
    groupings: Counter[str] = Counter()
    gaps: list[int] = []
    spans: list[int] = []
    top_notes: list[int] = []
    illegal_count = 0
    drop2_and_4_allowed_flags: list[bool] = []
    allowed_projection_methods: set[str] = set()
    integrity_preserved = 0
    integrity_rejected = 0

    for event in events:
        voicing = dict(event.get("voicing") or {})
        metadata = dict(voicing.get("metadata") or {})
        groupings[str(voicing.get("functional_grouping") or metadata.get("grouping") or "unknown")] += 1
        methods[str(metadata.get("upper_projection_method") or "unknown")] += 1
        source_families[str(metadata.get("upper_source_family") or voicing.get("content_family") or "unknown")] += 1
        source_degree_orders["-".join(str(item) for item in metadata.get("upper_source_degrees") or voicing.get("degrees") or [])] += 1
        lower_recipes[str(metadata.get("lower_group_recipe_id") or "unknown")] += 1
        gaps.append(int(metadata.get("group_gap_semitones") or 0))
        spans.append(int(metadata.get("overall_span_semitones") or 0))
        midi_notes = [int(note) for note in voicing.get("midi_notes") or []]
        if midi_notes:
            top_notes.append(max(midi_notes))
        if metadata.get("is_legal") is False:
            illegal_count += 1
        upper_meta = dict(metadata.get("upper_projection_metadata") or {})
        if "spread_upper_4note_drop2_and_4_allowed" in upper_meta:
            drop2_and_4_allowed_flags.append(bool(upper_meta["spread_upper_4note_drop2_and_4_allowed"]))
        if metadata.get("source_preserves_seventh_chord_identity") is True:
            integrity_preserved += 1
        if metadata.get("legality_reason") == "spread_candidate_rejected_by_global_seventh_chord_source_integrity_gate":
            integrity_rejected += 1
        for method in upper_meta.get("spread_upper_4note_allowed_projection_methods") or []:
            allowed_projection_methods.add(str(method))

    top_motions = [abs(top_notes[index] - top_notes[index - 1]) for index in range(1, len(top_notes))]
    drop24_events = int(methods.get("drop2_and_4", 0))
    return {
        "audit_version": "v2_2_56",
        "scope": "Ballad SPREAD 1+3 pilot audit; lower root + upper 3-note content source, with global seventh-chord identity preserved.",
        "events": len(events),
        "groupings": _counter_dict(groupings),
        "upper_projection_methods": _counter_dict(methods),
        "drop2_and_4_events": drop24_events,
        "source_integrity_preserved_events": integrity_preserved,
        "source_integrity_rejected_events": integrity_rejected,
        "drop2_and_4_absent": drop24_events == 0,
        "upper_4note_allowed_projection_methods": sorted(allowed_projection_methods) or ["drop2", "drop3"],
        "upper_4note_drop2_and_4_allowed_flags": drop2_and_4_allowed_flags[:8],
        "upper_4note_drop2_and_4_allowed_any": any(drop2_and_4_allowed_flags),
        "upper_source_families": _counter_dict(source_families),
        "upper_source_degree_orders": _counter_dict(source_degree_orders),
        "lower_group_recipes": _counter_dict(lower_recipes),
        "avg_group_gap_semitones": _avg(gaps),
        "min_group_gap_semitones": min(gaps) if gaps else None,
        "max_group_gap_semitones": max(gaps) if gaps else None,
        "avg_overall_span_semitones": _avg(spans),
        "min_overall_span_semitones": min(spans) if spans else None,
        "max_overall_span_semitones": max(spans) if spans else None,
        "avg_top_voice_abs_motion_semitones": _avg(top_motions),
        "max_top_voice_abs_motion_semitones": max(top_motions) if top_motions else None,
        "illegal_candidate_events": illegal_count,
        "content_families": debug.get("piano_musical_audit", {}).get("content_families", {}),
        "densities": debug.get("piano_musical_audit", {}).get("densities", {}),
        "functional_groupings": debug.get("piano_musical_audit", {}).get("functional_groupings", {}),
    }

def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    score = json.loads(LEADSHEET.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "jazz_ballad",
            "tempo": int(score.get("tempo", 82)),
            "choruses": 3,
            "seed": 2250,
            "output_path": str(OUTPUT),
            "ensemble": {"bass_present": True},
            "voicing_override": _first_listening_voicing_override(),
        }
    )
    debug = dict(result.debug)
    audit = _spread_1plus3_audit(debug)
    AUDIT_OUTPUT.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = {
        "ok": bool(result.ok),
        "version": result.version,
        "title": score.get("title"),
        "style": result.style,
        "midi_path": str(OUTPUT.relative_to(PROJECT_ROOT)),
        "audit_path": str(AUDIT_OUTPUT.relative_to(PROJECT_ROOT)),
        "written_bars": debug.get("written_bars"),
        "performance_choruses": debug.get("performance_choruses"),
        "performance_bars": debug.get("performance_bars"),
        "regions": debug.get("regions"),
        "audit": audit,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if not result.ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
