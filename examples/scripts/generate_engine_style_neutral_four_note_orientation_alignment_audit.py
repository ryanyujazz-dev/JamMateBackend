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
from jammate_engine.core.harmony.harmonic_context import classify_functional_motion
from jammate_engine.runtime.generate import generate_accompaniment

MILESTONE_ID = "v2_6_117"
MILESTONE_LABEL = "v2_6_117 — Engine Style-Neutral Four-Note AB Orientation Alignment Wiring"
DEMOS_DIR = PROJECT_ROOT / "demos"
LEADSHEETS_DIR = PROJECT_ROOT / "examples" / "leadsheets"
LOCAL_FUNCTIONAL_PAIR_TYPES = {"ii_v", "minor_ii_v", "v_i_major", "v_i_minor", "dominant_to_tonic"}
DROP_FAMILY_METHODS = {"drop2", "drop3", "drop2_and_4"}
PROPAGATED_METHODS = {"drop2", "drop3"}
EXPECTED_STYLES = ("bossa_nova", "medium_swing", "jazz_ballad")
SPEC_BY_STYLE: dict[str, dict[str, Any]] = {
    "bossa_nova": {"score": "blue_bossa.json", "choruses": 3, "seed": 26119, "tempo_fallback": 140},
    "medium_swing": {"score": "all_the_things_you_are.json", "choruses": 1, "seed": 26118, "tempo_fallback": 132},
    "jazz_ballad": {"score": "misty.json", "choruses": 1, "seed": 26119, "tempo_fallback": 78},
}


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    audits = [generate_style_audit(style, spec) for style, spec in SPEC_BY_STYLE.items()]
    summary = {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "scope": (
            "Style-neutral runtime wiring for four-note AB orientation continuity after source/color selection and after "
            "progression method-lock scope establishment. This milestone intentionally does not change voicing projection, "
            "source inventory, style rhythm, expression, bass, drums, API, or Agent runtime."
        ),
        "styles": audits,
    }
    summary["global_findings"] = build_global_findings(audits)
    summary["acceptance"] = acceptance(summary)
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_style_neutral_four_note_orientation_alignment_audit_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_style_neutral_four_note_orientation_alignment_audit_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(render_report(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def generate_style_audit(style: str, spec: dict[str, Any]) -> dict[str, Any]:
    score_path = LEADSHEETS_DIR / str(spec["score"])
    score = json.loads(score_path.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{style}_style_neutral_four_note_orientation_alignment_audit_demo.mid"
    request = {
        "leadsheet": score,
        "style": style,
        "tempo": int(score.get("tempo") or spec.get("tempo_fallback") or 120),
        "choruses": choruses,
        "seed": seed,
        "output_path": str(midi_path),
        "ensemble": {"bass_present": True},
        "voicing_override": {
            "enabled": True,
            "harmonic_expansion_enabled": True,
            "color_policy_mode": "altered_dominant",
            "metadata": {
                "harmonic_expansion_enabled": True,
                "color_policy_mode": "altered_dominant",
                "altered_dominant_enabled": True,
                "altered_dominant_policy": {
                    "enabled": True,
                    "intensity": "high",
                    "scopes": ["resolving_v7", "secondary_dominant", "tritone_sub", "llm_selected"],
                    "source_weight_biases": {
                        "rootless_ab": 0.16,
                        "rooted_color": 0.10,
                        "upper_structure": 0.06,
                    },
                },
                "style_neutral_four_note_orientation_alignment_audit": True,
                "no_voicing_projection_change_requested": True,
            },
        },
    }
    result = generate_accompaniment(request)
    rows = [_piano_row(row) for row in list(result.debug.get("piano_musical_audit_events") or [])]
    rows = [row for row in rows if row]
    first_rows = _first_harmonic_event_per_region(rows)
    progression = _progression_audit(first_rows)
    note_counts = dict(result.debug.get("note_events_by_track") or {})
    methods = Counter(row["method"] for row in rows)
    disposition = Counter(row["disposition"] for row in rows)
    density = Counter(str(row["density"]) for row in rows)
    content_family = Counter(row["content_family"] for row in rows)
    source_family = Counter(row["rotation_source_family"] for row in rows if row["rotation_source_family"])
    ab_family = Counter(row["rotation_family"] for row in rows if row["rotation_family"])
    effective_symbols = Counter(row["effective_chord_symbol"] for row in rows if row["effective_chord_symbol"])
    altered_rows = [row for row in rows if row["altered_source"]]
    ab_eligible_rows = [row for row in rows if row["rotation_ab_eligible"]]
    return {
        "style": style,
        "ok": bool(result.ok),
        "score": str(score_path.relative_to(PROJECT_ROOT)),
        "choruses": choruses,
        "seed": seed,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "note_events_by_track": note_counts,
        "piano_notes": int(note_counts.get("piano", 0)),
        "bass_notes": int(note_counts.get("bass", 0)),
        "drums_notes": int(note_counts.get("drums", 0)),
        "piano_harmonic_event_count": len(rows),
        "first_event_region_count": len(first_rows),
        "harmonic_expansion_enabled": bool((result.debug.get("effective_voicing_policy") or {}).get("harmonic_expansion_enabled")),
        "color_policy_mode": (result.debug.get("effective_voicing_policy") or {}).get("color_policy_mode"),
        "method_counts": dict(methods),
        "disposition_counts": dict(disposition),
        "density_counts": dict(density),
        "content_family_counts": dict(content_family),
        "source_family_counts": dict(source_family),
        "rotation_family_counts": dict(ab_family),
        "effective_symbol_counts_sample": dict(effective_symbols.most_common(20)),
        "non_drop_family_event_count": sum(count for method, count in methods.items() if method not in DROP_FAMILY_METHODS and disposition.get("open", 0)),
        "generic_open_event_count": int(methods.get("generic_open", 0)),
        "low_density_event_count": sum(int(count) for d, count in density.items() if d in {"2", "3"}),
        "altered_source_event_count": len(altered_rows),
        "ab_eligible_event_count": len(ab_eligible_rows),
        "ab_eligible_ratio": round(len(ab_eligible_rows) / max(1, len(rows)), 4),
        "altered_source_ab_eligible_count": sum(1 for row in altered_rows if row["rotation_ab_eligible"]),
        "altered_source_without_ab_metadata_count": sum(1 for row in altered_rows if not row["rotation_ab_eligible"]),
        "method_lock_runtime_wiring_enabled_count": sum(1 for row in rows if row["method_lock_wiring_enabled"]),
        "method_lock_filtering_enabled_count": sum(1 for row in rows if row["method_lock_filtering_enabled"]),
        "four_note_rotation_filter_applied_count": sum(1 for row in rows if row["rotation_filter_applied"]),
        "four_note_rotation_policy_applied_count": sum(1 for row in rows if row["rotation_policy_applied"]),
        "progression_audit": progression,
        "rows_sample": rows[:12],
    }


def _piano_row(row: dict[str, Any]) -> dict[str, Any] | None:
    voicing = dict(row.get("voicing") or {})
    if not voicing:
        return None
    metadata = dict(voicing.get("metadata") or {})
    pattern = dict(row.get("pattern_event") or {})
    recipe = dict(metadata.get("content_recipe") or {})
    validity = [str(item) for item in (recipe.get("validity_notes") or [])]
    method = str(metadata.get("active_open_projection_method") or metadata.get("disposition_projection_method") or "")
    effective = str(metadata.get("voicing_request_effective_chord_symbol") or voicing.get("chord_symbol") or "")
    original = str(pattern.get("chord_symbol") or "")
    validity_text = " ".join(validity).lower()
    return {
        "event_id": str(pattern.get("event_id") or row.get("event_id") or ""),
        "region_id": str(pattern.get("region_id") or ""),
        "original_chord_symbol": original,
        "effective_chord_symbol": effective,
        "next_chord_symbol": str((pattern.get("metadata") or {}).get("next_chord_symbol") or metadata.get("next_chord_symbol") or ""),
        "method": method or "unknown",
        "disposition": str(voicing.get("disposition") or ""),
        "density": int(voicing.get("density") or 0),
        "content_family": str(voicing.get("content_family") or ""),
        "recipe_id": str(voicing.get("recipe_id") or ""),
        "notes": list(voicing.get("midi_notes") or []),
        "rotation_family": str(metadata.get("four_note_rotation_family") or ""),
        "rotation_source_family": str(metadata.get("four_note_rotation_source_family") or ""),
        "rotation_content_type": str(metadata.get("four_note_rotation_content_type") or ""),
        "rotation_ab_side": str(metadata.get("four_note_rotation_ab_side") or ""),
        "rotation_ab_eligible": _coerce_bool(metadata.get("four_note_rotation_ab_eligible"), default=False),
        "rootless_ab_side": str(metadata.get("rootless_ab_orientation_family") or ""),
        "altered_source": "altered_dominant" in validity_text or "b9" in effective.lower() or "b13" in effective.lower() or "alt" in effective.lower(),
        "altered_source_kind": _altered_source_kind(validity, effective),
        "method_lock_wiring_enabled": _coerce_bool(metadata.get("voicing_method_lock_scope_runtime_wiring_enabled"), default=False),
        "method_lock_filtering_enabled": _coerce_bool(metadata.get("voicing_method_lock_runtime_filtering_enabled"), default=False),
        "method_lock_candidate_matches": _coerce_bool(metadata.get("voicing_method_lock_candidate_matches"), default=False),
        "method_lock_runtime_action": str(metadata.get("voicing_method_lock_runtime_action") or ""),
        "rotation_policy_applied": _coerce_bool(
            metadata.get("progression_four_note_orientation_alignment_policy_applied")
            or metadata.get("medium_swing_four_note_rotation_alignment_policy_applied"),
            default=False,
        ),
        "rotation_filter_applied": _coerce_bool(
            metadata.get("progression_four_note_orientation_alignment_policy_filter_applied")
            or metadata.get("medium_swing_four_note_rotation_alignment_filter_applied"),
            default=False,
        ),
        "rotation_candidate_matches": _coerce_bool(
            metadata.get("progression_four_note_orientation_alignment_policy_candidate_matches")
            or metadata.get("medium_swing_four_note_rotation_alignment_candidate_matches"),
            default=False,
        ),
        "orientation_policy_reason": str(metadata.get("progression_four_note_orientation_alignment_policy_reason") or metadata.get("medium_swing_four_note_rotation_alignment_reason") or ""),
        "orientation_filter_reason": str(metadata.get("progression_four_note_orientation_alignment_policy_filter_reason") or metadata.get("medium_swing_four_note_rotation_alignment_filter_reason") or ""),
        "medium_swing_method_lock_applied": _coerce_bool(metadata.get("medium_swing_phrase_scope_method_lock_policy_applied"), default=False),
        "validity_markers": [note for note in validity if any(token in note for token in ("altered_dominant", "rootless_ab", "four_note", "harmonic_expansion"))][:18],
    }


def _altered_source_kind(validity: list[str], effective: str) -> str:
    text = " ".join(validity).lower() + " " + effective.lower()
    if "b9" in text and "b13" in text:
        return "b9_b13"
    if "sharp11" in text or "#11" in text:
        return "sharp11"
    if "#9" in text or "sharp9" in text:
        return "sharp9"
    if "b13" in text or "flat13" in text:
        return "flat13"
    if "b9" in text or "flat9" in text:
        return "flat9"
    if "altered_dominant" in text:
        return "altered_other"
    return ""


def _first_harmonic_event_per_region(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        region_id = row["region_id"]
        if not region_id or region_id in seen:
            continue
        seen.add(region_id)
        out.append(row)
    return out


def _progression_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pair_rows: list[dict[str, Any]] = []
    for idx in range(1, len(rows)):
        previous = rows[idx - 1]
        current = rows[idx]
        next_symbol = rows[idx + 1]["original_chord_symbol"] if idx + 1 < len(rows) else ""
        motion = classify_functional_motion(
            previous_chord_symbol=previous["original_chord_symbol"],
            chord_symbol=current["original_chord_symbol"],
            next_chord_symbol=next_symbol or None,
        )
        pair_type = str(getattr(motion, "previous_to_current_type", "") or "")
        if pair_type not in LOCAL_FUNCTIONAL_PAIR_TYPES:
            continue
        previous_method = previous["method"]
        current_method = current["method"]
        previous_side = previous["rotation_ab_side"]
        current_side = current["rotation_ab_side"]
        ab_follow_expected = "B" if previous_side == "A" else ("A" if previous_side == "B" else "")
        method_pair_eligible = previous_method in PROPAGATED_METHODS and current_method in DROP_FAMILY_METHODS
        ab_pair_eligible = previous["rotation_ab_eligible"] and current["rotation_ab_eligible"] and previous_side in {"A", "B"}
        pair_rows.append(
            {
                "pair_type": pair_type,
                "previous_region_id": previous["region_id"],
                "current_region_id": current["region_id"],
                "previous_chord_symbol": previous["original_chord_symbol"],
                "current_chord_symbol": current["original_chord_symbol"],
                "previous_effective_symbol": previous["effective_chord_symbol"],
                "current_effective_symbol": current["effective_chord_symbol"],
                "previous_method": previous_method,
                "current_method": current_method,
                "method_pair_eligible": method_pair_eligible,
                "method_continuity_ok": bool(method_pair_eligible and previous_method == current_method),
                "previous_ab_side": previous_side,
                "current_ab_side": current_side,
                "ab_pair_eligible": ab_pair_eligible,
                "ab_follow_expected": ab_follow_expected,
                "ab_follow_ok": bool(ab_pair_eligible and current_side == ab_follow_expected),
                "previous_rotation_family": previous["rotation_family"],
                "current_rotation_family": current["rotation_family"],
                "previous_rotation_source_family": previous["rotation_source_family"],
                "current_rotation_source_family": current["rotation_source_family"],
                "previous_altered_source_kind": previous["altered_source_kind"],
                "current_altered_source_kind": current["altered_source_kind"],
                "current_method_lock_wiring_enabled": current["method_lock_wiring_enabled"],
                "current_method_lock_filtering_enabled": current["method_lock_filtering_enabled"],
                "current_rotation_filter_applied": current["rotation_filter_applied"],
                "current_rotation_policy_applied": current["rotation_policy_applied"],
            }
        )
    pair_type_counts = Counter(row["pair_type"] for row in pair_rows)
    method_eligible = [row for row in pair_rows if row["method_pair_eligible"]]
    ab_eligible = [row for row in pair_rows if row["ab_pair_eligible"]]
    return {
        "local_functional_pair_count": len(pair_rows),
        "pair_type_counts": dict(pair_type_counts),
        "method_pair_eligible_count": len(method_eligible),
        "method_continuity_ok_count": sum(1 for row in method_eligible if row["method_continuity_ok"]),
        "method_continuity_ratio": round(sum(1 for row in method_eligible if row["method_continuity_ok"]) / max(1, len(method_eligible)), 4),
        "ab_pair_eligible_count": len(ab_eligible),
        "ab_follow_ok_count": sum(1 for row in ab_eligible if row["ab_follow_ok"]),
        "ab_follow_ratio": round(sum(1 for row in ab_eligible if row["ab_follow_ok"]) / max(1, len(ab_eligible)), 4),
        "method_lock_runtime_wiring_enabled_pair_count": sum(1 for row in pair_rows if row["current_method_lock_wiring_enabled"]),
        "method_lock_runtime_filtering_enabled_pair_count": sum(1 for row in pair_rows if row["current_method_lock_filtering_enabled"]),
        "rotation_filter_applied_pair_count": sum(1 for row in pair_rows if row["current_rotation_filter_applied"]),
        "rotation_policy_applied_pair_count": sum(1 for row in pair_rows if row["current_rotation_policy_applied"]),
        "method_switch_samples": [row for row in pair_rows if row["method_pair_eligible"] and not row["method_continuity_ok"]][:12],
        "ab_mismatch_samples": [row for row in pair_rows if row["ab_pair_eligible"] and not row["ab_follow_ok"]][:12],
        "pair_samples": pair_rows[:16],
    }


def build_global_findings(audits: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "styles_audited": [audit["style"] for audit in audits],
        "all_runtime_ok": all(audit["ok"] for audit in audits),
        "all_harmonic_expansion_enabled": all(audit["harmonic_expansion_enabled"] for audit in audits),
        "all_altered_mode_requested": all(audit["color_policy_mode"] == "altered_dominant" for audit in audits),
        "styles_with_method_lock_wiring_pairs": [
            audit["style"] for audit in audits if audit["progression_audit"]["method_lock_runtime_wiring_enabled_pair_count"] > 0
        ],
        "styles_missing_method_lock_wiring_pairs": [
            audit["style"] for audit in audits if audit["progression_audit"]["local_functional_pair_count"] > 0 and audit["progression_audit"]["method_lock_runtime_wiring_enabled_pair_count"] == 0
        ],
        "styles_with_ab_rotation_filter_pairs": [
            audit["style"] for audit in audits if audit["progression_audit"]["rotation_filter_applied_pair_count"] > 0
        ],
        "styles_missing_ab_rotation_filter_pairs": [
            audit["style"] for audit in audits if audit["progression_audit"]["ab_pair_eligible_count"] > 0 and audit["progression_audit"]["rotation_filter_applied_pair_count"] == 0
        ],
        "altered_sources_without_ab_metadata_by_style": {
            audit["style"]: audit["altered_source_without_ab_metadata_count"] for audit in audits
        },
        "next_recommended_step": "v2_6_118_engine_source_metadata_audit_or_expansion_alter_weighting",
        "principle": "Expansion/alter choose source color before voicing; method lock and AB orientation continuity are style-neutral progression policies; drop-family projection remains unchanged.",
    }


def acceptance(summary: dict[str, Any]) -> dict[str, Any]:
    audits = list(summary.get("styles") or [])
    findings = dict(summary.get("global_findings") or {})
    by_style = {audit.get("style"): audit for audit in audits}
    bossa_pairs = int((by_style.get("bossa_nova", {}).get("progression_audit") or {}).get("local_functional_pair_count") or 0)
    bossa_wired = int((by_style.get("bossa_nova", {}).get("progression_audit") or {}).get("method_lock_runtime_wiring_enabled_pair_count") or 0)
    swing_pairs = int((by_style.get("medium_swing", {}).get("progression_audit") or {}).get("local_functional_pair_count") or 0)
    swing_wired = int((by_style.get("medium_swing", {}).get("progression_audit") or {}).get("method_lock_runtime_wiring_enabled_pair_count") or 0)
    ballad = by_style.get("jazz_ballad", {})
    ballad_progression = ballad.get("progression_audit") or {}
    ballad_methods = set((ballad.get("method_counts") or {}).keys())
    checks = {
        "all_expected_styles_audited": set(findings.get("styles_audited") or []) == set(EXPECTED_STYLES),
        "all_runtime_ok": bool(findings.get("all_runtime_ok")),
        "all_harmonic_expansion_enabled": bool(findings.get("all_harmonic_expansion_enabled")),
        "all_altered_mode_requested": bool(findings.get("all_altered_mode_requested")),
        "bossa_method_lock_wiring_enabled_for_all_local_pairs": bossa_pairs > 0 and bossa_wired == bossa_pairs,
        "medium_swing_method_lock_wiring_preserved_for_all_local_pairs": swing_pairs > 0 and swing_wired == swing_pairs,
        "bossa_method_continuity_full_ratio": float((by_style.get("bossa_nova", {}).get("progression_audit") or {}).get("method_continuity_ratio") or 0) >= 0.999,
        "medium_swing_method_continuity_full_ratio": float((by_style.get("medium_swing", {}).get("progression_audit") or {}).get("method_continuity_ratio") or 0) >= 0.999,
        "bossa_orientation_filtering_applies_to_every_ab_eligible_pair": (
            int((by_style.get("bossa_nova", {}).get("progression_audit") or {}).get("ab_pair_eligible_count") or 0) > 0
            and int((by_style.get("bossa_nova", {}).get("progression_audit") or {}).get("rotation_filter_applied_pair_count") or 0)
            == int((by_style.get("bossa_nova", {}).get("progression_audit") or {}).get("ab_pair_eligible_count") or 0)
        ),
        "medium_swing_orientation_filtering_applies_to_every_ab_eligible_pair": (
            int((by_style.get("medium_swing", {}).get("progression_audit") or {}).get("ab_pair_eligible_count") or 0) > 0
            and int((by_style.get("medium_swing", {}).get("progression_audit") or {}).get("rotation_filter_applied_pair_count") or 0)
            == int((by_style.get("medium_swing", {}).get("progression_audit") or {}).get("ab_pair_eligible_count") or 0)
        ),
        "bossa_ab_follow_full_ratio": float((by_style.get("bossa_nova", {}).get("progression_audit") or {}).get("ab_follow_ratio") or 0) >= 0.999,
        "medium_swing_ab_follow_full_ratio": float((by_style.get("medium_swing", {}).get("progression_audit") or {}).get("ab_follow_ratio") or 0) >= 0.999,
        "ballad_policy_does_not_force_drop_family_when_no_drop_runtime": (
            int(ballad_progression.get("method_lock_runtime_wiring_enabled_pair_count") or 0) == 0
            and not bool(ballad_methods & DROP_FAMILY_METHODS)
        ),
        "no_generic_open_regression_in_bossa_or_swing": all(int((audit.get("method_counts") or {}).get("generic_open") or 0) == 0 for audit in audits if audit.get("style") in {"bossa_nova", "medium_swing"}),
        "altered_sources_keep_ab_metadata": all(int(audit.get("altered_source_without_ab_metadata_count") or 0) == 0 for audit in audits),
    }
    return {"passed": all(checks.values()), "checks": checks}


def render_report(summary: dict[str, Any]) -> str:
    lines = [f"# {MILESTONE_LABEL}", "", f"Engine tag: `{summary['engine_version_tag']}`", ""]
    lines.append("## Acceptance")
    for key, value in summary["acceptance"]["checks"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    lines.append("## Global findings")
    findings = summary["global_findings"]
    lines.append(f"- Styles audited: `{findings['styles_audited']}`")
    lines.append(f"- Styles with method-lock runtime wiring pairs: `{findings['styles_with_method_lock_wiring_pairs']}`")
    lines.append(f"- Styles missing method-lock wiring pairs: `{findings['styles_missing_method_lock_wiring_pairs']}`")
    lines.append(f"- Styles with AB rotation filter pairs: `{findings['styles_with_ab_rotation_filter_pairs']}`")
    lines.append(f"- Styles missing AB rotation filter pairs: `{findings['styles_missing_ab_rotation_filter_pairs']}`")
    lines.append("- AB filtering gap note: `historical v2_6_116 audit; v2_6_117 may supersede this gap when present in the same baseline`")
    lines.append(f"- Altered sources without AB metadata by style: `{findings['altered_sources_without_ab_metadata_by_style']}`")
    lines.append(f"- Next recommended step: `{findings['next_recommended_step']}`")
    lines.append("")
    for audit in summary["styles"]:
        progression = audit["progression_audit"]
        lines.extend([
            f"## {audit['style']}",
            "",
            f"- MIDI: `{audit['midi_path']}`",
            f"- piano / bass / drums: `{audit['piano_notes']} / {audit['bass_notes']} / {audit['drums_notes']}`",
            f"- color mode: `{audit['color_policy_mode']}`",
            f"- local functional pairs: `{progression['local_functional_pair_count']}` `{progression['pair_type_counts']}`",
            f"- method continuity: `{progression['method_continuity_ok_count']} / {progression['method_pair_eligible_count']}` ratio `{progression['method_continuity_ratio']}`",
            f"- AB follow: `{progression['ab_follow_ok_count']} / {progression['ab_pair_eligible_count']}` ratio `{progression['ab_follow_ratio']}`",
            f"- method-lock runtime wiring pairs: `{progression['method_lock_runtime_wiring_enabled_pair_count']}`",
            f"- AB rotation filter-applied pairs: `{progression['rotation_filter_applied_pair_count']}`",
            f"- altered source events / AB-missing: `{audit['altered_source_event_count']} / {audit['altered_source_without_ab_metadata_count']}`",
            f"- method counts: `{audit['method_counts']}`",
            f"- source family counts: `{audit['source_family_counts']}`",
            "",
        ])
    return "\n".join(lines)


def _coerce_bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}
    return default


if __name__ == "__main__":
    main()
