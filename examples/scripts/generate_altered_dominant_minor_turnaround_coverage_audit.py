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

from jammate_engine.core.harmony.chord_parser import parse_chord
from jammate_engine.core.voicing import ColorPolicyMode, ContentFamily, VoicingPolicy, resolve_altered_dominant_policy
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.sources.upper_structure import plan_upper_structure_sources
from jammate_engine.runtime.generate import generate_accompaniment

_VERSION = "v2_2_88"
DEMOS_DIR = PROJECT_ROOT / "demos"
BLUE_BOSSA = PROJECT_ROOT / "examples" / "leadsheets" / "blue_bossa.json"
FIXTURE = PROJECT_ROOT / "examples" / "leadsheets" / "altered_dominant_minor_turnaround_coverage.json"

BLUE_BOSSA_MIDI = DEMOS_DIR / "v2_2_88_blue_bossa_bossa_nova_minor_v_altered_coverage_demo.mid"
BLUE_BOSSA_AUDIT = DEMOS_DIR / "v2_2_88_blue_bossa_bossa_nova_minor_v_altered_coverage_audit_summary.json"
FIXTURE_MIDI = DEMOS_DIR / "v2_2_88_minor_turnaround_altered_coverage_fixture_demo.mid"
FIXTURE_AUDIT = DEMOS_DIR / "v2_2_88_minor_turnaround_altered_coverage_fixture_audit_summary.json"
POLICY_MATRIX = DEMOS_DIR / "v2_2_88_minor_turnaround_altered_policy_matrix.json"


def _policy(
    *,
    previous: str | None,
    current: str,
    next_symbol: str | None,
    home_key: str | None,
    scopes: str | list[str] = "functional_dominants",
    intensity: str = "high",
) -> VoicingPolicy:
    return VoicingPolicy(
        allowed_content=(ContentFamily.ROOTED_COLOR, ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B),
        preferred_content=ContentFamily.ROOTED_COLOR,
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
        min_density=4,
        preferred_density=4,
        max_density=4,
        metadata={
            "harmonic_expansion_enabled": True,
            "color_policy_mode": "style_safe_extensions",
            "previous_chord_symbol": previous,
            "chord_symbol": current,
            "next_chord_symbol": next_symbol,
            "home_key": home_key,
            "key": home_key,
            "altered_dominant_policy": {
                "enabled": True,
                "intensity": intensity,
                "scopes": scopes,
            },
            "spread_upper_structure_enabled": True,
        },
    )


def _source_coverage(current: str, policy: VoicingPolicy) -> dict[str, Any]:
    rooted = plan_content_recipes(current, policy)
    rootless = plan_content_recipes(
        current,
        VoicingPolicy(
            allowed_content=(ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B),
            preferred_content=ContentFamily.ROOTLESS_A,
            harmonic_expansion_enabled=True,
            color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
            min_density=4,
            preferred_density=4,
            max_density=4,
            metadata=dict(policy.metadata),
        ),
    )
    upper = plan_upper_structure_sources(current, density=3, policy=policy)
    return {
        "rooted_color_altered_source_present": any("rooted_color_4note_altered_dominant_source_1_3_b7_X" in r.validity_notes for r in rooted),
        "rootless_ab_altered_source_present": any("rootless_ab_content_type_altered_dominant_rootless" in r.validity_notes for r in rootless),
        "upper_structure_altered_source_present": any("upper_structure_profile_kind_altered" in s.source_notes for s in upper),
        "rooted_validity_notes": sorted({note for recipe in rooted for note in recipe.validity_notes if "altered_dominant" in note}),
        "rootless_validity_notes": sorted({note for recipe in rootless for note in recipe.validity_notes if "altered_dominant" in note}),
        "upper_structure_notes": sorted({note for source in upper for note in source.source_notes if "altered_dominant" in note or "upper_structure_profile_kind_altered" in note}),
    }


def _policy_matrix() -> dict[str, Any]:
    cases = [
        {
            "id": "home_minor_resolving_v7",
            "label": "Bm7b5 → E7 → Am6 in A minor",
            "previous": "Bm7b5",
            "current": "E7",
            "next": "Am6",
            "home_key": "A minor",
            "scopes": "resolving_v7",
        },
        {
            "id": "local_minor_secondary_in_c",
            "label": "Bm7b5 → E7 → Am7 in C major",
            "previous": "Bm7b5",
            "current": "E7",
            "next": "Am7",
            "home_key": "C",
            "scopes": "secondary_dominants",
        },
        {
            "id": "turnaround_vi7_secondary",
            "label": "Cmaj7 → A7 → Dm7",
            "previous": "Cmaj7",
            "current": "A7",
            "next": "Dm7",
            "home_key": "C",
            "scopes": ["secondary_dominants", "resolving_v7"],
        },
        {
            "id": "turnaround_final_v7_resolving",
            "label": "Dm7 → G7 → Cmaj7",
            "previous": "Dm7",
            "current": "G7",
            "next": "Cmaj7",
            "home_key": "C",
            "scopes": ["secondary_dominants", "resolving_v7"],
        },
        {
            "id": "explicit_minor_v_alt_with_inferred_resolving",
            "label": "Bm7b5 → E7b9 → Am6 in A minor",
            "previous": "Bm7b5",
            "current": "E7b9",
            "next": "Am6",
            "home_key": "A minor",
            "scopes": "resolving_v7",
            "intensity": "light",
        },
    ]
    rows: list[dict[str, Any]] = []
    for case in cases:
        policy = _policy(
            previous=case["previous"],
            current=case["current"],
            next_symbol=case["next"],
            home_key=case["home_key"],
            scopes=case["scopes"],
            intensity=case.get("intensity", "high"),
        )
        decision = resolve_altered_dominant_policy(policy, parse_chord(case["current"]))
        rows.append(
            {
                **case,
                "decision": decision.to_debug_dict(),
                "source_coverage": _source_coverage(case["current"], policy),
            }
        )
    return {
        "audit_version": _VERSION,
        "scope": "Minor V→i / Turnaround Altered Coverage Audit",
        "cases": rows,
    }


def _voicing_override(*, intensity: str, scopes: list[str], isolation: bool = False) -> dict[str, Any]:
    data: dict[str, Any] = {
        "enabled": True,
        "harmonic_expansion_enabled": True,
        "color_policy_mode": "altered_dominant",
        "metadata": {
            "harmonic_expansion_enabled": True,
            "color_policy_mode": "altered_dominant",
            "altered_dominant_enabled": True,
            "altered_dominant_policy": {
                "enabled": True,
                "intensity": intensity,
                "scopes": scopes,
                "source_weight_biases_by_intensity": {
                    "light": {"rooted_color": 0.04, "rootless_ab": -0.08, "upper_structure": -0.12},
                    "medium": {"rooted_color": 0.14, "rootless_ab": 0.04, "upper_structure": 0.06},
                    "high": {"rooted_color": 0.22, "rootless_ab": 0.10, "upper_structure": 0.14},
                },
            },
        },
    }
    if isolation:
        data.update(
            {
                "pattern_mode": "region_start_anchor_only",
                "disable_anticipation": True,
                "mute_bass": False,
                "expression_hint": "sustain",
            }
        )
    return data


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _decision_for_event(event: dict[str, Any], *, scopes: list[str], intensity: str) -> dict[str, Any]:
    pattern = dict(event.get("pattern_event") or {})
    metadata = dict(pattern.get("metadata") or {})
    current = str(pattern.get("chord_symbol") or "")
    policy = _policy(
        previous=metadata.get("previous_chord_symbol"),
        current=current,
        next_symbol=metadata.get("next_chord_symbol"),
        home_key=metadata.get("home_key"),
        scopes=scopes,
        intensity=intensity,
    )
    return resolve_altered_dominant_policy(policy, parse_chord(current)).to_debug_dict()


def _runtime_audit(debug: dict[str, Any], *, intensity: str, scopes: list[str], matrix: dict[str, Any]) -> dict[str, Any]:
    events = list(debug.get("piano_musical_audit_events") or [])
    decisions = []
    functional_scopes: Counter[str] = Counter()
    inferred_scopes: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    source_kinds: Counter[str] = Counter()
    altered_degree_events = 0
    for event in events:
        pattern = dict(event.get("pattern_event") or {})
        current = str(pattern.get("chord_symbol") or "")
        chord = parse_chord(current)
        if not chord.is_dominant:
            continue
        decision = _decision_for_event(event, scopes=scopes, intensity=intensity)
        functional_scopes[decision["functional_scope"]] += 1
        inferred_scopes[decision["inferred_functional_scope"]] += 1
        reasons[decision["reason"]] += 1
        details = dict(((event.get("voicing") or {}).get("metadata") or {}).get("score_breakdown", {}).get("details", {}) or {})
        source_kind = str(details.get("altered_dominant_source_kind") or "")
        if source_kind:
            source_kinds[source_kind] += 1
        degrees = [str(d) for d in ((event.get("voicing") or {}).get("degrees") or [])]
        if any(d in {"b9", "#9", "#11", "b13", "#5", "b5"} for d in degrees):
            altered_degree_events += 1
        decisions.append(
            {
                "event_id": pattern.get("event_id"),
                "region_id": pattern.get("region_id"),
                "chord_symbol": current,
                "previous": (pattern.get("metadata") or {}).get("previous_chord_symbol"),
                "next": (pattern.get("metadata") or {}).get("next_chord_symbol"),
                "home_key": (pattern.get("metadata") or {}).get("home_key"),
                "decision": decision,
                "selected_degrees": degrees,
                "selected_content_family": (event.get("voicing") or {}).get("content_family"),
                "altered_dominant_source_kind": source_kind,
            }
        )
    return {
        "audit_version": _VERSION,
        "scope": "Minor V→i / Turnaround Altered Coverage Audit runtime summary",
        "title": debug.get("title"),
        "style": debug.get("style"),
        "events": len(events),
        "dominant_events": len(decisions),
        "altered_degree_events": altered_degree_events,
        "functional_scopes": dict(sorted(functional_scopes.items())),
        "inferred_functional_scopes": dict(sorted(inferred_scopes.items())),
        "authorization_reasons": dict(sorted(reasons.items())),
        "selected_altered_source_kinds": dict(sorted(source_kinds.items())),
        "dominant_event_decisions": decisions,
        "policy_matrix_case_ids": [case["id"] for case in matrix["cases"]],
    }


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    matrix = _policy_matrix()
    POLICY_MATRIX.write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8")

    blue = generate_accompaniment(
        {
            "leadsheet": _load(BLUE_BOSSA),
            "style": "bossa_nova",
            "tempo": 140,
            "choruses": 3,
            "seed": 2288,
            "output_path": str(BLUE_BOSSA_MIDI),
            "voicing_override": _voicing_override(intensity="light", scopes=["resolving_v7"], isolation=False),
        }
    )
    BLUE_BOSSA_AUDIT.write_text(
        json.dumps(
            _runtime_audit(blue.debug, intensity="light", scopes=["resolving_v7"], matrix=matrix),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    fixture = generate_accompaniment(
        {
            "leadsheet": _load(FIXTURE),
            "style": "jazz_ballad",
            "tempo": 84,
            "choruses": 3,
            "seed": 2288,
            "output_path": str(FIXTURE_MIDI),
            "voicing_override": _voicing_override(
                intensity="high",
                scopes=["resolving_v7", "secondary_dominants", "llm_selected"],
                isolation=True,
            ),
        }
    )
    FIXTURE_AUDIT.write_text(
        json.dumps(
            _runtime_audit(fixture.debug, intensity="high", scopes=["resolving_v7", "secondary_dominants", "llm_selected"], matrix=matrix),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(json.dumps({"blue_bossa_midi": str(BLUE_BOSSA_MIDI), "fixture_midi": str(FIXTURE_MIDI), "policy_matrix": str(POLICY_MATRIX)}, indent=2))


if __name__ == "__main__":
    main()
