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
from jammate_engine.styles.bossa_nova import voicing_policy

MILESTONE_ID = "v2_6_114"
MILESTONE_LABEL = "v2_6_114 — Engine Bossa Nova High-Color Harmonic Expansion Policy"
BLUE_BOSSA_SCORE = PROJECT_ROOT / "examples" / "leadsheets" / "blue_bossa.json"
DEMOS_DIR = PROJECT_ROOT / "demos"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 23114, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 23115, "slug": "blue_bossa_5x"},
)
ALLOWED_METHODS = {"drop2", "drop3", "drop2_and_4"}


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static = build_static_audit()
    runtime = [_generate_runtime_audit(spec) for spec in DEMO_SPECS]
    summary = {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "scope": (
            "Bossa harmonic-expansion checked demo: raise 9/11/13/b9-b13 color selection inside style harmonic-color policy "
            "while leaving core voicing source/projection/selector and drop-family behavior unchanged."
        ),
        "static_audit": static,
        "runtime_audits": runtime,
    }
    summary["acceptance"] = _acceptance(static, runtime)
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_high_color_harmonic_expansion_policy_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_high_color_harmonic_expansion_policy_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    policy = voicing_policy.get_voicing_policy()
    metadata = dict(policy.metadata or {})
    high = dict(metadata.get("bossa_high_color_harmonic_expansion_policy") or {})
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "policy_has_high_color_metadata": bool(high),
        "high_color_policy": high,
        "preferred_disposition": getattr(policy.preferred_disposition, "value", str(policy.preferred_disposition)),
        "density_range": [int(policy.min_density), int(policy.max_density)],
        "open_projection_methods": list(metadata.get("open_projection_methods") or []),
        "low_priority_degrees": list(policy.low_priority_degrees or ()),
        "source_weights_harmonic_expansion": dict((policy.source_family_weights_by_gate or {}).get("harmonic_expansion") or {}),
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_high_color_harmonic_expansion_policy_demo.mid"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "bossa_nova",
            "tempo": int(score.get("tempo", 140)),
            "choruses": choruses,
            "seed": seed,
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
            "voicing_override": {
                "enabled": True,
                "harmonic_expansion_enabled": True,
                "color_policy_mode": "style_safe_extensions",
                "metadata": {
                    "harmonic_expansion_enabled": True,
                    "color_policy_mode": "style_safe_extensions",
                    "bossa_high_color_harmonic_expansion_checked_demo": True,
                    "no_voicing_projection_change_requested": True,
                },
            },
        }
    )
    rows = [_piano_row(row) for row in list(result.debug.get("piano_musical_audit_events") or [])]
    rows = [row for row in rows if row]
    note_counts = dict(result.debug.get("note_events_by_track") or {})
    method_counts = Counter(row["method"] for row in rows)
    density_counts = Counter(str(row["density"]) for row in rows)
    content_counts = Counter(row["content_family"] for row in rows)
    family_counts = Counter(row["high_color_family"] for row in rows if row["high_color_family"])
    effective_symbols = Counter(row["effective_chord_symbol"] for row in rows if row["effective_chord_symbol"])
    high_color_rows = [row for row in rows if row["has_bossa_high_color"]]
    minor_v_rows = [row for row in rows if row["original_chord_symbol"] == "G7b9"]
    minor_v_b13_rows = [row for row in minor_v_rows if row["has_flat13"]]
    return {
        "ok": bool(result.ok),
        "choruses": choruses,
        "seed": seed,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "note_events_by_track": note_counts,
        "piano_notes": int(note_counts.get("piano", 0)),
        "bass_notes": int(note_counts.get("bass", 0)),
        "drums_notes": int(note_counts.get("drums", 0)),
        "piano_harmonic_event_count": len(rows),
        "harmonic_expansion_enabled": bool((result.debug.get("effective_voicing_policy") or {}).get("harmonic_expansion_enabled")),
        "color_policy_mode": (result.debug.get("effective_voicing_policy") or {}).get("color_policy_mode"),
        "density_counts": dict(density_counts),
        "content_family_counts": dict(content_counts),
        "open_method_counts": dict(method_counts),
        "generic_open_event_count": int(method_counts.get("generic_open", 0)),
        "non_drop_family_event_count": sum(count for method, count in method_counts.items() if method not in ALLOWED_METHODS),
        "low_density_event_count": sum(int(count) for density, count in density_counts.items() if density in {"2", "3"}),
        "high_color_event_count": len(high_color_rows),
        "high_color_ratio": round(len(high_color_rows) / max(1, len(rows)), 4),
        "source_containing_ninth_count": sum(1 for row in rows if row["has_ninth"]),
        "source_containing_thirteenth_count": sum(1 for row in rows if row["has_thirteenth"]),
        "source_containing_flat13_count": sum(1 for row in rows if row["has_flat13"]),
        "source_containing_eleventh_count": sum(1 for row in rows if row["has_eleventh"]),
        "high_color_family_counts": dict(family_counts),
        "effective_symbol_counts": dict(effective_symbols),
        "minor_cadence_dominant_event_count": len(minor_v_rows),
        "minor_cadence_dominant_flat13_count": len(minor_v_b13_rows),
        "minor_cadence_dominant_flat13_ratio": round(len(minor_v_b13_rows) / max(1, len(minor_v_rows)), 4),
        "rows_sample": rows[:16],
    }


def _piano_row(row: dict[str, Any]) -> dict[str, Any] | None:
    voicing = dict(row.get("voicing") or {})
    if not voicing:
        return None
    metadata = dict(voicing.get("metadata") or {})
    recipe = dict(metadata.get("content_recipe") or {})
    notes = [str(item) for item in recipe.get("validity_notes", []) or []]
    pattern_event = dict(row.get("pattern_event") or {})
    original = str(pattern_event.get("chord_symbol") or "")
    effective = str(metadata.get("voicing_request_effective_chord_symbol") or voicing.get("chord_symbol") or "")
    marker_text = " ".join(notes).lower()
    high_markers = (
        "rootless_ab_content_type_with_5",
        "rootless_ab_content_type_with_13",
        "rootless_ab_content_type_altered_dominant_rootless",
        "rooted_color_4note_1_3_7_9_alias",
        "rooted_color_4note_1369_alias",
        "rootless_ab_content_type_explicit_eleventh",
    )
    method = str(metadata.get("active_open_projection_method") or metadata.get("disposition_projection_method") or "unknown")
    return {
        "original_chord_symbol": original,
        "effective_chord_symbol": effective,
        "override_applied": bool(metadata.get("voicing_request_chord_symbol_override_applied")),
        "high_color_family": metadata.get("bossa_high_color_harmonic_expansion_color_family"),
        "content_family": voicing.get("content_family"),
        "disposition": voicing.get("disposition"),
        "density": int(voicing.get("density") or 0),
        "recipe_id": voicing.get("recipe_id"),
        "method": method,
        "has_bossa_high_color": any(marker in notes for marker in high_markers) or "harmonic_expansion_color_used" in notes,
        "has_ninth": "ninth" in marker_text or "_9" in marker_text or "flat9" in marker_text,
        "has_thirteenth": "thirteenth" in marker_text or "with_13" in marker_text or "13" in effective,
        "has_flat13": "flat13" in marker_text or "b13" in effective.lower(),
        "has_eleventh": "eleventh" in marker_text or "11" in effective,
        "validity_color_markers": [note for note in notes if any(token in note for token in ("harmonic", "content_type", "resolved", "altered_color", "eleventh"))][:14],
    }


def _acceptance(static: dict[str, Any], runtime: list[dict[str, Any]]) -> dict[str, Any]:
    checks: dict[str, bool] = {
        "static_declares_high_color_policy": bool(static.get("policy_has_high_color_metadata")),
        "static_keeps_open_drop_family": set(static.get("open_projection_methods") or []) == ALLOWED_METHODS,
        "runtime_ok": all(audit.get("ok") for audit in runtime),
        "expansion_enabled": all(audit.get("harmonic_expansion_enabled") for audit in runtime),
        "high_color_ratio_at_least_75_percent": all(float(audit.get("high_color_ratio") or 0.0) >= 0.75 for audit in runtime),
        "minor_v_flat13_ratio_high": all(float(audit.get("minor_cadence_dominant_flat13_ratio") or 0.0) >= 0.80 for audit in runtime),
        "no_generic_open": all(int(audit.get("generic_open_event_count") or 0) == 0 for audit in runtime),
        "no_low_density": all(int(audit.get("low_density_event_count") or 0) == 0 for audit in runtime),
        "only_drop_family_methods": all(int(audit.get("non_drop_family_event_count") or 0) == 0 for audit in runtime),
    }
    return {"passed": all(checks.values()), "checks": checks}


def _render_report(summary: dict[str, Any]) -> str:
    lines = [f"# {MILESTONE_LABEL}", "", f"Engine tag: `{summary['engine_version_tag']}`", ""]
    lines.append("## Acceptance")
    for key, value in summary["acceptance"]["checks"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    for audit in summary["runtime_audits"]:
        lines.extend(
            [
                f"## Blue Bossa {audit['choruses']}x",
                "",
                f"- MIDI: `{audit['midi_path']}`",
                f"- piano / bass / drums: `{audit['piano_notes']} / {audit['bass_notes']} / {audit['drums_notes']}`",
                f"- high-color ratio: `{audit['high_color_ratio']}`",
                f"- minor V flat13 ratio: `{audit['minor_cadence_dominant_flat13_ratio']}`",
                f"- open methods: `{audit['open_method_counts']}`",
                f"- content families: `{audit['content_family_counts']}`",
                f"- high color families: `{audit['high_color_family_counts']}`",
                "",
            ]
        )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
