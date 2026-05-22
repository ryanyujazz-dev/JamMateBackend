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
from jammate_engine.core.voicing import ContentFamily, RootSupportPolicy, describe_density_recipe
from jammate_engine.core.voicing.disposition.method_weights import disposition_method_weight_spec_from_metadata
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.bossa_nova import arrangement_policy, voicing_policy
from jammate_engine.styles.registry import get_style

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"
MILESTONE_ID = "v2_6_104"
MILESTONE_LABEL = "v2_6_104 — Engine Bossa Nova Drop-Family OPEN Method Policy Correction"
BLUE_BOSSA_SCORE = LEADSHEET_DIR / "blue_bossa.json"
DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"choruses": 3, "seed": 22803, "slug": "blue_bossa_3x"},
    {"choruses": 5, "seed": 22855, "slug": "blue_bossa_5x"},
)
RETIRED_GROUPING_NAMES = {"1+3", "2+2"}


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    static_audit = build_static_audit()
    runtime_audits = [_generate_runtime_audit(spec) for spec in DEMO_SPECS]
    acceptance = _acceptance(static_audit, runtime_audits)
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": MILESTONE_LABEL,
        "scope": (
            "Correct the v2_6_103 Bossa OPEN method policy: keep OPEN-main 4-to-5-note Bossa voicing and retired ordinary 4-note grouping metadata, but remove generic_open from the ordinary runtime method pool. "
            "Bossa now requests the existing shared drop-family consensus only: drop2 primary, drop3 secondary, drop2&4 very low-frequency color; generic_open remains fallback/rescue only. "
            "No Bossa parallel selector, no projection/source algorithm change, no pattern vocabulary change, no expression numeric change, no API/Agent/HarmonyOS change."
        ),
        "static_audit": static_audit,
        "runtime_audits": runtime_audits,
        "acceptance": acceptance,
        "recommended_next_task": "v2_6_105_engine_bossa_nova_kick_bass_lock_and_low_frequency_shadow_refinement",
    }
    summary_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_open_method_policy_correction_summary.json"
    report_path = DEMOS_DIR / f"{MILESTONE_ID}_engine_bossa_nova_open_method_policy_correction_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "report": str(report_path), "acceptance": acceptance}, indent=2, ensure_ascii=False))
    if not acceptance["passed"]:
        raise SystemExit(1)


def build_static_audit() -> dict[str, Any]:
    style = get_style("bossa_nova")
    arr = arrangement_policy.get_arrangement_policy()
    policy = voicing_policy.get_voicing_policy()
    metadata = dict(policy.metadata or {})
    four_recipe = describe_density_recipe(
        ("R", "3", "5", "b7"),
        content_family=ContentFamily.SEVENTH_BASIC,
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
    )
    rootless_recipe = describe_density_recipe(
        ("3", "5", "b7", "9"),
        content_family=ContentFamily.ROOTLESS_A,
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
    )
    open_policy = dict(metadata.get("bossa_open_voicing_main_policy") or {})
    retired_policy = dict(metadata.get("retired_ordinary_4note_grouping_metadata_policy") or {})
    weight_spec = disposition_method_weight_spec_from_metadata(metadata)
    return {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": ENGINE_VERSION_TAG,
        "style_registered": getattr(style, "name", None) == "bossa_nova",
        "arrangement_policy_version": arr.get("bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_version"),
        "arrangement_open_method_policy_correction_version": arr.get("bossa_nova_open_method_policy_correction_version"),
        "arrangement_open_policy_active": arr.get("bossa_nova_open_voicing_main_policy_active"),
        "arrangement_retired_4note_grouping_metadata": arr.get("bossa_nova_retired_ordinary_4note_grouping_metadata"),
        "preferred_disposition": policy.preferred_disposition.value,
        "allowed_dispositions": [item.value for item in policy.allowed_dispositions],
        "preferred_density": policy.preferred_density,
        "min_density": policy.min_density,
        "max_density": policy.max_density,
        "texture_runtime_filtering_enabled": metadata.get("voicing_texture_state_runtime_filtering_enabled"),
        "primary_texture_family": metadata.get("primary_texture_family"),
        "allowed_texture_families": metadata.get("allowed_texture_families"),
        "open_projection_methods": metadata.get("open_projection_methods"),
        "disposition_method_weights_enabled_for_scoring": metadata.get("disposition_method_weights_enabled_for_scoring"),
        "has_style_local_disposition_method_weights": "disposition_method_weights" in metadata,
        "open_method_policy_correction": dict(metadata.get("bossa_open_method_policy_correction") or {}),
        "open_policy": open_policy,
        "retired_policy": retired_policy,
        "weight_spec_source": weight_spec.source,
        "open_method_weights": dict(weight_spec.open_method_weights),
        "four_note_recipe_id": four_recipe.recipe_id,
        "four_note_functional_grouping": four_recipe.functional_grouping.value if four_recipe.functional_grouping else None,
        "four_note_group_roles": [role.value for role in four_recipe.group_roles],
        "rootless_four_note_recipe_id": rootless_recipe.recipe_id,
        "rootless_four_note_functional_grouping": rootless_recipe.functional_grouping.value if rootless_recipe.functional_grouping else None,
        "rootless_four_note_group_roles": [role.value for role in rootless_recipe.group_roles],
    }


def _generate_runtime_audit(spec: dict[str, Any]) -> dict[str, Any]:
    score = json.loads(BLUE_BOSSA_SCORE.read_text(encoding="utf-8"))
    choruses = int(spec["choruses"])
    seed = int(spec["seed"])
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{MILESTONE_ID}_{slug}_bossa_nova_open_method_policy_correction_demo.mid"
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
    rows = [row for row in debug.get("piano_musical_audit_events", []) if _pattern_event(row).get("track") == "piano"]
    active = [row for row in rows if _pattern_event(row).get("status") == "active"]
    voicings = [_voicing(row) for row in active]
    dispositions = Counter(str(v.get("disposition") or "unknown") for v in voicings)
    densities = Counter(str(v.get("density") or "unknown") for v in voicings)
    content = Counter(str(v.get("content_family") or "unknown") for v in voicings)
    groupings = Counter(str(v.get("functional_grouping")) if v.get("functional_grouping") is not None else "none" for v in voicings)
    methods = Counter(str(_voicing_method(v)) for v in voicings)
    recipe_ids = Counter(str(v.get("recipe_id") or "unknown") for v in voicings)
    retired_grouping_rows = [v for v in voicings if str(v.get("functional_grouping") or "") in RETIRED_GROUPING_NAMES]
    spread_rows = [v for v in voicings if str(v.get("disposition") or "") in {"spread", "two_hand_spread"}]
    low_density_rows = [v for v in voicings if int(v.get("density") or 0) in {2, 3}]
    expression_summary = dict(debug.get("expression_foundation_audit") or {})
    pedal_audit = dict(debug.get("pedal_realization_audit") or {})
    return {
        "ok": ok,
        "choruses": choruses,
        "seed": seed,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "title": debug.get("title"),
        "style": debug.get("style"),
        "performance_bars": debug.get("performance_bars"),
        "note_events_by_track": debug.get("note_events_by_track"),
        "piano_active_events": len(active),
        "piano_disposition_counts": dict(dispositions),
        "piano_density_counts": dict(densities),
        "piano_content_family_counts": dict(content),
        "piano_functional_grouping_counts": dict(groupings),
        "piano_open_projection_method_counts": dict(methods),
        "piano_recipe_id_counts": dict(recipe_ids),
        "retired_4note_grouping_event_count": len(retired_grouping_rows),
        "spread_grouping_event_count": len(spread_rows),
        "low_density_2_or_3_event_count": len(low_density_rows),
        "root_included_count": sum(1 for v in voicings if bool(v.get("root_included"))),
        "expression_warning_count": expression_summary.get("warning_count"),
        "expression_missing_count": expression_summary.get("missing_expression_count"),
        "expression_cross_region_count": expression_summary.get("cross_region_count"),
        "expression_cross_next_event_count": expression_summary.get("cross_next_event_count"),
        "pedal_cc64_event_count": pedal_audit.get("cc64_event_count"),
    }


def _pattern_event(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("pattern_event") or {}
    return dict(value) if isinstance(value, dict) else {}


def _voicing(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("voicing") or {}
    return dict(value) if isinstance(value, dict) else {}


def _voicing_method(voicing: dict[str, Any]) -> str:
    metadata = dict(voicing.get("metadata") or {})
    return str(
        voicing.get("disposition_projection_method")
        or metadata.get("disposition_projection_method")
        or metadata.get("active_open_projection_method")
        or "unknown"
    )


def _acceptance(static: dict[str, Any], runtimes: list[dict[str, Any]]) -> dict[str, Any]:
    runtime_ok = bool(runtimes) and all(_runtime_accepts(item) for item in runtimes)
    checks = {
        "style_and_arrangement_registered": static.get("style_registered") is True and static.get("arrangement_open_method_policy_correction_version") == MILESTONE_ID,
        "bossa_policy_is_open_main": static.get("preferred_disposition") == "open"
        and static.get("texture_runtime_filtering_enabled") is True
        and static.get("primary_texture_family") == "open"
        and static.get("allowed_texture_families") == ["open"],
        "bossa_uses_drop_family_method_pool_without_generic_open": static.get("open_projection_methods") == ["drop2", "drop3", "drop2_and_4"]
        and static.get("has_style_local_disposition_method_weights") is False
        and static.get("weight_spec_source") == "style_default:bossa_nova"
        and static.get("open_method_weights") == {"generic_open": 0.0, "drop2": 0.52, "drop3": 0.38, "drop2_and_4": 0.10},
        "density_stays_normal_4_to_5": static.get("preferred_density") == 4
        and static.get("min_density") == 4
        and static.get("max_density") == 5,
        "ordinary_4note_grouping_metadata_retired": static.get("four_note_functional_grouping") is None
        and static.get("rootless_four_note_functional_grouping") is None
        and "1plus3" not in str(static.get("four_note_recipe_id"))
        and "2plus2" not in str(static.get("four_note_recipe_id")),
        "runtime_blue_bossa_full_band_passes": runtime_ok,
    }
    return {"passed": all(checks.values()), "checks": checks}


def _runtime_accepts(item: dict[str, Any]) -> bool:
    note_counts = dict(item.get("note_events_by_track") or {})
    dispositions = dict(item.get("piano_disposition_counts") or {})
    densities = dict(item.get("piano_density_counts") or {})
    groupings = dict(item.get("piano_functional_grouping_counts") or {})
    methods = dict(item.get("piano_open_projection_method_counts") or {})
    return (
        item.get("ok") is True
        and int(note_counts.get("piano", 0)) > 0
        and int(note_counts.get("bass", 0)) > 0
        and int(note_counts.get("drums", 0)) > 0
        and int(item.get("piano_active_events") or 0) > 0
        and set(dispositions) == {"open"}
        and all(int(key) not in {2, 3} for key in densities if str(key).isdigit())
        and int(item.get("low_density_2_or_3_event_count") or 0) == 0
        and int(item.get("retired_4note_grouping_event_count") or 0) == 0
        and int(item.get("spread_grouping_event_count") or 0) == 0
        and "1+3" not in groupings
        and "2+2" not in groupings
        and methods
        and set(methods) <= {"drop2", "drop3", "drop2_and_4"}
        and "generic_open" not in methods
        and int(item.get("expression_warning_count") or 0) == 0
        and int(item.get("expression_missing_count") or 0) == 0
        and int(item.get("expression_cross_region_count") or 0) == 0
        and int(item.get("expression_cross_next_event_count") or 0) == 0
        and int(item.get("pedal_cc64_event_count") or 0) == 0
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
        f"- Preferred disposition: `{static.get('preferred_disposition')}`",
        f"- Allowed dispositions: `{static.get('allowed_dispositions')}`",
        f"- Texture runtime family: `{static.get('primary_texture_family')}` / `{static.get('allowed_texture_families')}`",
        f"- Open methods: `{static.get('open_projection_methods')}`",
        f"- Method weight source: `{static.get('weight_spec_source')}`",
        f"- Open method weights: `{static.get('open_method_weights')}`",
        f"- Density range: `{static.get('min_density')}` / `{static.get('preferred_density')}` / `{static.get('max_density')}`",
        f"- Ordinary 4-note recipe: `{static.get('four_note_recipe_id')}`, grouping=`{static.get('four_note_functional_grouping')}`",
        f"- Rootless 4-note recipe: `{static.get('rootless_four_note_recipe_id')}`, grouping=`{static.get('rootless_four_note_functional_grouping')}`",
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
                f"- Piano active events: `{item.get('piano_active_events')}`",
                f"- Dispositions: `{item.get('piano_disposition_counts')}`",
                f"- Open methods: `{item.get('piano_open_projection_method_counts')}`",
                f"- Densities: `{item.get('piano_density_counts')}`",
                f"- Content families: `{item.get('piano_content_family_counts')}`",
                f"- Functional groupings: `{item.get('piano_functional_grouping_counts')}`",
                f"- Retired 1+3/2+2 grouping events: `{item.get('retired_4note_grouping_event_count')}`",
                f"- Spread grouping events: `{item.get('spread_grouping_event_count')}`",
                f"- Expression warnings/missing/cross-region: `{item.get('expression_warning_count')}` / `{item.get('expression_missing_count')}` / `{item.get('expression_cross_region_count')}`",
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
