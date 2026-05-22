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
from jammate_engine.core.voicing import ColorPolicyMode, ContentFamily, VoicingPolicy
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.bossa_nova.voicing_policy import get_voicing_policy as get_bossa_voicing_policy
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy as get_ballad_voicing_policy
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as get_swing_voicing_policy

MILESTONE_ID = "v2_6_118"
MILESTONE_LABEL = "v2_6_118 — Engine Additive Unnotated Altered Dominant Source Pool"
DEMOS_DIR = PROJECT_ROOT / "demos"
LEADSHEETS_DIR = PROJECT_ROOT / "examples" / "leadsheets"
EXPECTED_STYLES = ("bossa_nova", "medium_swing", "jazz_ballad")
SPEC_BY_STYLE: dict[str, dict[str, Any]] = {
    "bossa_nova": {"score": "blue_bossa.json", "choruses": 3, "seed": 26120, "tempo_fallback": 140},
    "medium_swing": {"score": "all_the_things_you_are.json", "choruses": 3, "seed": 26121, "tempo_fallback": 132},
    "jazz_ballad": {"score": "misty.json", "choruses": 3, "seed": 26122, "tempo_fallback": 78},
}
POLICY_BY_STYLE = {
    "bossa_nova": get_bossa_voicing_policy,
    "medium_swing": get_swing_voicing_policy,
    "jazz_ballad": get_ballad_voicing_policy,
}


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    audits = [generate_style_audit(style, spec) for style, spec in SPEC_BY_STYLE.items()]
    summary = {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "scope": (
            "Style-neutral source-pool correction for unnotated altered dominants. Explicit altered symbols remain altered-only "
            "chart fidelity; plain dominants authorized by harmonic expansion + altered policy keep ordinary 9/13 sources and add "
            "altered sources before AB/method/projection. This milestone does not change projection, rhythm, expression, bass, drums, API, or Agent."
        ),
        "styles": audits,
    }
    summary["global_findings"] = build_global_findings(audits)
    summary["acceptance"] = acceptance(summary)
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_additive_unnotated_altered_dominant_source_pool_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_additive_unnotated_altered_dominant_source_pool_report.md"
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
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{style}_additive_unnotated_altered_dominant_source_pool_demo.mid"
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
                    "intensity": "medium",
                    "scopes": ["resolving_v7", "secondary_dominants", "functional_dominants", "llm_selected"],
                    "source_weight_biases": {
                        "rootless_ab": 0.08,
                        "rooted_color": 0.08,
                        "upper_structure": 0.04,
                    },
                },
                "additive_unnotated_altered_dominant_source_pool_audit": True,
                "no_voicing_projection_change_requested": True,
            },
        },
    }
    result = generate_accompaniment(request)
    rows = [_piano_row(row) for row in list(result.debug.get("piano_musical_audit_events") or [])]
    rows = [row for row in rows if row]
    note_counts = dict(result.debug.get("note_events_by_track") or {})
    candidate_plain = candidate_pool_audit(style, "G7")
    candidate_explicit = candidate_pool_audit(style, "G7b9b13")
    source_counts = Counter(row["source_family"] for row in rows if row["source_family"])
    content_counts = Counter(row["content_family"] for row in rows if row["content_family"])
    altered_selected = [row for row in rows if row["altered_source"]]
    safe_rootless_selected = [row for row in rows if row["source_family"] in {"third_fifth_seventh_ninth", "third_thirteenth_seventh_ninth"}]
    return {
        "style": style,
        "ok": bool(result.ok),
        "score": str(score_path.relative_to(PROJECT_ROOT)),
        "choruses": choruses,
        "seed": seed,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "piano_notes": int(note_counts.get("piano", 0)),
        "bass_notes": int(note_counts.get("bass", 0)),
        "drums_notes": int(note_counts.get("drums", 0)),
        "piano_harmonic_event_count": len(rows),
        "candidate_plain_g7": candidate_plain,
        "candidate_explicit_g7b9b13": candidate_explicit,
        "selected_source_family_counts": dict(source_counts),
        "selected_content_family_counts": dict(content_counts),
        "selected_altered_source_events": len(altered_selected),
        "selected_safe_rootless_9_13_events": len(safe_rootless_selected),
        "rows_sample": rows[:12],
    }


def candidate_pool_audit(style: str, symbol: str) -> dict[str, Any]:
    policy = _candidate_policy(style)
    recipes = [
        recipe
        for recipe in plan_content_recipes(symbol, policy)
        if recipe.family in {ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B, ContentFamily.ROOTED_COLOR}
    ]
    source_type = Counter(_source_type(recipe.validity_notes) for recipe in recipes)
    family = Counter(str(recipe.family.value) for recipe in recipes)
    side = Counter("A" if recipe.family == ContentFamily.ROOTLESS_A else "B" if recipe.family == ContentFamily.ROOTLESS_B else "rooted" for recipe in recipes)
    altered = [recipe for recipe in recipes if _is_altered_source(recipe.validity_notes)]
    safe_9 = [recipe for recipe in recipes if "rootless_ab_content_type_with_5" in recipe.validity_notes]
    safe_13 = [recipe for recipe in recipes if "rootless_ab_content_type_with_13" in recipe.validity_notes]
    ordinary = [recipe for recipe in recipes if not _is_altered_source(recipe.validity_notes)]
    natural_five_in_altered = [recipe.degree_names for recipe in altered if "5" in recipe.degree_names]
    return {
        "symbol": symbol,
        "candidate_recipe_count": len(recipes),
        "source_type_counts": dict(source_type),
        "content_family_counts": dict(family),
        "ab_side_counts": dict(side),
        "has_ordinary_source": bool(ordinary),
        "has_safe_with_5": bool(safe_9),
        "has_safe_with_13": bool(safe_13),
        "has_altered_source": bool(altered),
        "has_altered_rootless": any("rootless_ab_content_type_altered_dominant_rootless" in recipe.validity_notes for recipe in altered),
        "has_altered_rooted": any("rooted_color_4note_altered_dominant_rooted_source" in recipe.validity_notes for recipe in altered),
        "natural_five_in_altered_count": len(natural_five_in_altered),
        "sample_degree_orders": [list(recipe.degree_names) for recipe in recipes[:8]],
    }


def _candidate_policy(style: str) -> VoicingPolicy:
    policy = POLICY_BY_STYLE[style]()
    metadata = dict(policy.metadata or {})
    metadata.update(
        {
            "harmonic_expansion_enabled": True,
            "color_policy_mode": ColorPolicyMode.STYLE_SAFE_EXTENSIONS.value,
            "previous_chord_symbol": "Dm7",
            "next_chord_symbol": "Cmaj7",
            "home_key": "C",
            "key": "C",
            "altered_dominant_policy": {
                "enabled": True,
                "intensity": "light",
                "scopes": ["resolving_v7"],
            },
        }
    )
    return replace(
        policy,
        allowed_content=(ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B, ContentFamily.ROOTED_COLOR),
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
        min_density=4,
        preferred_density=4,
        max_density=4,
        metadata=metadata,
    )


def _source_type(validity_notes: tuple[str, ...]) -> str:
    notes = set(validity_notes)
    if "rootless_ab_content_type_altered_dominant_rootless" in notes:
        return "altered_dominant_rootless"
    if "rooted_color_4note_altered_dominant_rooted_source" in notes:
        return "altered_dominant_rooted"
    if "rootless_ab_content_type_with_13" in notes:
        return "ordinary_with_13"
    if "rootless_ab_content_type_with_5" in notes:
        return "ordinary_with_5"
    if "rooted_color_4note_harmonic_expansion_source_family" in notes:
        return "ordinary_rooted_harmonic_expansion"
    if "rooted_color_4note_explicit_9_source_family" in notes or "rooted_color_4note_explicit_13_source_family" in notes:
        return "ordinary_rooted_explicit_color"
    marker = next((note for note in validity_notes if note.startswith("rootless_ab_content_type_")), "")
    return marker.removeprefix("rootless_ab_content_type_") if marker else "unknown"


def _is_altered_source(validity_notes: tuple[str, ...]) -> bool:
    notes = set(validity_notes)
    return bool(
        "rootless_ab_content_type_altered_dominant_rootless" in notes
        or "rootless_ab_altered_dominant_rootless_source" in notes
        or "rooted_color_4note_altered_dominant_rooted_source" in notes
    )


def _piano_row(row: dict[str, Any]) -> dict[str, Any] | None:
    voicing = dict(row.get("voicing") or {})
    if not voicing:
        return None
    metadata = dict(voicing.get("metadata") or {})
    recipe = dict(metadata.get("content_recipe") or {})
    validity = [str(item) for item in (recipe.get("validity_notes") or [])]
    validity_text = " ".join(validity).lower()
    pattern = dict(row.get("pattern_event") or {})
    return {
        "event_id": str(pattern.get("event_id") or row.get("event_id") or ""),
        "region_id": str(pattern.get("region_id") or ""),
        "original_chord_symbol": str(pattern.get("chord_symbol") or ""),
        "effective_chord_symbol": str(metadata.get("voicing_request_effective_chord_symbol") or voicing.get("chord_symbol") or ""),
        "content_family": str(voicing.get("content_family") or ""),
        "density": int(voicing.get("density") or 0),
        "method": str(metadata.get("active_open_projection_method") or metadata.get("disposition_projection_method") or ""),
        "source_family": str(metadata.get("four_note_rotation_source_family") or metadata.get("rootless_ab_functional_source_type") or metadata.get("rooted_color_4note_functional_content_type") or ""),
        "ab_side": str(metadata.get("four_note_rotation_ab_side") or metadata.get("rootless_ab_orientation_family") or ""),
        "altered_source": "altered_dominant_rootless_source" in validity_text or "altered_dominant_rooted_source" in validity_text,
    }


def build_global_findings(audits: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "styles_audited": [audit["style"] for audit in audits],
        "all_runtime_ok": all(audit["ok"] for audit in audits),
        "plain_g7_source_pool_by_style": {
            audit["style"]: audit["candidate_plain_g7"]["source_type_counts"] for audit in audits
        },
        "explicit_g7b9b13_source_pool_by_style": {
            audit["style"]: audit["candidate_explicit_g7b9b13"]["source_type_counts"] for audit in audits
        },
        "principle": "Altered dominant augments source candidates for unnotated/plain dominants; explicit altered symbols remain altered-only; AB/method/projection consume the chosen source without post-voicing note mutation.",
        "next_recommended_step": "v2_6_119_engine_style_level_expansion_alter_weight_calibration_by_functional_context",
    }


def acceptance(summary: dict[str, Any]) -> dict[str, Any]:
    audits = list(summary.get("styles") or [])
    checks = {
        "all_expected_styles_audited": set(audit.get("style") for audit in audits) == set(EXPECTED_STYLES),
        "all_runtime_ok": all(bool(audit.get("ok")) for audit in audits),
        "plain_g7_keeps_ordinary_source_in_all_styles": all(bool(audit["candidate_plain_g7"]["has_ordinary_source"]) for audit in audits),
        "plain_g7_adds_altered_source_in_all_styles": all(bool(audit["candidate_plain_g7"]["has_altered_source"]) for audit in audits),
        "bossa_and_swing_plain_g7_keep_rootless_9_13_sources": all(
            bool(audit["candidate_plain_g7"]["has_safe_with_5"]) and bool(audit["candidate_plain_g7"]["has_safe_with_13"])
            for audit in audits
            if audit.get("style") in {"bossa_nova", "medium_swing"}
        ),
        "explicit_g7b9b13_stays_altered_only_in_all_styles": all(
            bool(audit["candidate_explicit_g7b9b13"]["has_altered_source"])
            and not bool(audit["candidate_explicit_g7b9b13"]["has_ordinary_source"])
            for audit in audits
        ),
        "altered_rootless_omits_natural_five": all(
            int(audit["candidate_plain_g7"]["natural_five_in_altered_count"]) == 0
            and int(audit["candidate_explicit_g7b9b13"]["natural_five_in_altered_count"]) == 0
            for audit in audits
        ),
        "demos_written": all(bool(audit.get("midi_path")) for audit in audits),
    }
    return {"passed": all(checks.values()), "checks": checks}


def render_report(summary: dict[str, Any]) -> str:
    lines = [f"# {MILESTONE_LABEL}", "", f"Engine tag: `{summary['engine_version_tag']}`", ""]
    lines.append("## Acceptance")
    for key, value in summary["acceptance"]["checks"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    lines.append("## Principle")
    lines.append(summary["global_findings"]["principle"])
    lines.append("")
    for audit in summary["styles"]:
        lines.extend([
            f"## {audit['style']}",
            "",
            f"- MIDI: `{audit['midi_path']}`",
            f"- piano / bass / drums: `{audit['piano_notes']} / {audit['bass_notes']} / {audit['drums_notes']}`",
            f"- plain G7 candidate pool: `{audit['candidate_plain_g7']['source_type_counts']}`",
            f"- explicit G7b9b13 candidate pool: `{audit['candidate_explicit_g7b9b13']['source_type_counts']}`",
            f"- selected source families: `{audit['selected_source_family_counts']}`",
            f"- selected altered / safe-rootless events: `{audit['selected_altered_source_events']} / {audit['selected_safe_rootless_9_13_events']}`",
            "",
        ])
    lines.append(f"Recommended next step: `{summary['global_findings']['next_recommended_step']}`")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
