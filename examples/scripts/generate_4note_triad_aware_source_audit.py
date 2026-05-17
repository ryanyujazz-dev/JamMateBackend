from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.runtime.override import build_voicing_override_policy

ROOT = PROJECT_ROOT
DEMOS_DIR = ROOT / "demos"
SYMBOLS = ("C", "Cm", "Csus2", "Csus4", "Cadd9", "Cmadd9", "C6", "C6/9")


def _policy(*, expansion: bool = False):
    return build_voicing_override_policy(
        {"harmonic_expansion_enabled": expansion, "color_policy_mode": "style_safe_extensions" if expansion else "chord_symbol_only"},
        {
            "enabled": True,
            "allowed_content": ["seventh_chord_basic", "rooted_color", "rootless_A", "rootless_B"],
            "preferred_density": 4,
            "min_density": 4,
            "max_density": 4,
            "preferred_disposition": "closed",
            "allowed_dispositions": ["closed"],
            "register_low": 46,
            "register_high": 76,
            "top_voice_low": 55,
            "top_voice_high": 76,
            "comfort_register_low": 52,
            "comfort_register_high": 66,
            "max_voicing_span": 16,
            "metadata": {
                "strict_closed_compact_pitch_class_layout": True,
                "strict_closed_max_span": 12,
                "closed_voicing_lowest_note_floor": 53,
                "closed_4note_per_source_minimum_motion": True,
                "closed_register_downshift": "A3/MIDI 57 -> F3/MIDI 53",
            },
        },
        style_name="medium_swing",
    )


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    audit = {
        "version": ENGINE_VERSION_TAG,
        "contract": "v2_1_42 4-note triad-aware closed source audit",
        "closed_register_floor": "F3 / MIDI 53",
        "symbols": [_symbol_audit(symbol) for symbol in SYMBOLS],
        "plain_triad_expansion": _symbol_audit("C", expansion=True),
    }
    json_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_4note_triad_aware_source_audit.json"
    md_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_4note_triad_aware_source_audit.md"
    json_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_format_md(audit), encoding="utf-8")
    print({"ok": True, "json_path": str(json_path), "md_path": str(md_path)})


def _symbol_audit(symbol: str, *, expansion: bool = False) -> dict[str, Any]:
    policy = _policy(expansion=expansion)
    recipes = plan_content_recipes(symbol, policy)
    candidates = generate_candidates(symbol, policy)
    return {
        "symbol": symbol,
        "harmonic_expansion": expansion,
        "recipe_count": len(recipes),
        "source_types": _source_types(recipes),
        "degree_orders": [list(recipe.degree_names) for recipe in recipes],
        "candidate_count": len(candidates),
        "candidate_densities": sorted({candidate.density for candidate in candidates}),
        "candidate_dispositions": sorted({candidate.disposition.value for candidate in candidates}),
        "min_low_note": min((min(candidate.notes) for candidate in candidates), default=None),
        "max_span": max((max(candidate.notes) - min(candidate.notes) for candidate in candidates), default=None),
        "sample_candidates": [
            {"degrees": candidate.degrees, "notes": candidate.notes, "triad_4note": candidate.metadata.get("triad_4note_functional_content_type")}
            for candidate in candidates[:8]
        ],
    }


def _source_types(recipes) -> list[str]:
    out: list[str] = []
    for recipe in recipes:
        for note in recipe.validity_notes:
            for prefix in (
                "triad_4note_functional_content_type_",
                "rooted_color_4note_functional_content_type_",
                "basic_4note_functional_content_type_",
            ):
                if note.startswith(prefix):
                    value = note.removeprefix(prefix)
                    if value not in out:
                        out.append(value)
    return out


def _format_md(audit: dict[str, Any]) -> str:
    lines = [
        f"# {audit['version']} 4-note triad-aware closed source audit",
        "",
        "Closed register floor: F3 / MIDI 53.",
        "",
        "Plain triads use doubled closed rotations: 1351 / 3513 / 5135.",
        "Sus2 uses 1251 / 2512 / 5125; sus4 mirrors this as 1451 / 4514 / 5145.",
        "",
        "| Symbol | Expansion | Source types | Densities | Min low | Max span |",
        "|---|---:|---|---|---:|---:|",
    ]
    for item in [*audit["symbols"], audit["plain_triad_expansion"]]:
        lines.append(
            f"| `{item['symbol']}` | `{item['harmonic_expansion']}` | `{', '.join(item['source_types'])}` | `{item['candidate_densities']}` | `{item['min_low_note']}` | `{item['max_span']}` |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
