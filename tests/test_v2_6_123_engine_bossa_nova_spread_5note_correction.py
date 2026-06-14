from __future__ import annotations

import json
from collections import Counter
from dataclasses import replace
from pathlib import Path

from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing import ColorPolicyMode, Disposition
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.realization.voicing_policy_context_adapter import policy_with_event_voicing_context
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.bossa_nova import expression_policy, voicing_policy


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _expanded_bossa_policy():
    return replace(
        voicing_policy.get_voicing_policy(),
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
    )


def test_bossa_5note_policy_uses_spread_not_open_or_generic_lane() -> None:
    policy = _expanded_bossa_policy()
    metadata = dict(policy.metadata or {})

    spread_policy = metadata["bossa_spread_5note_low_weight_policy"]
    assert spread_policy["enabled"] is True
    assert spread_policy["five_note_route"] == "existing_grouped_spread_runtime_candidates"
    assert spread_policy["selected_contract_id"] == "spread_1plus4_contract"
    assert spread_policy["generic_open_role"] == "fallback_or_rescue_only_not_5note_runtime_lane"

    assert "open_projection_method_density_gate" not in metadata
    assert "selector_tail_candidate_lane_policy" not in metadata
    assert "generic_open" not in metadata["open_projection_methods"]
    assert policy.preferred_disposition is Disposition.OPEN


def test_ordinary_bossa_candidate_pool_has_no_open_5note_or_generic_open() -> None:
    policy = _expanded_bossa_policy()
    candidates = generate_candidates("Cmaj7", policy)

    assert candidates
    assert all(candidate.disposition is Disposition.OPEN for candidate in candidates)
    assert all(int(candidate.density or 0) == 4 for candidate in candidates)
    assert not any(candidate.metadata.get("active_open_projection_method") == "generic_open" for candidate in candidates)
    assert not any(candidate.disposition is Disposition.OPEN and int(candidate.density or 0) == 5 for candidate in candidates)


def test_event_scoped_bossa_5note_requests_existing_grouped_spread_1plus4_only() -> None:
    base_policy = _expanded_bossa_policy()
    event = PatternEvent(
        event_id="bossa_spread_5note_probe",
        track="piano",
        region_id="r10",
        chord_symbol="Cmaj7",
        onset_beat=42.5,
        role="harmonic",
        expression_hint="core_sustain",
        local_beat=2.5,
        metadata={
            "region_performance_bar_index": 10,
            "region_chord_index": 0,
            "region_chorus_index": 0,
        },
    )
    scoped_policy = policy_with_event_voicing_context(base_policy, event)
    metadata = dict(scoped_policy.metadata or {})

    assert metadata["bossa_spread_5note_low_weight_policy_applied"] is True
    assert metadata["spread_grouping_mix_candidate_pool"]["selected_contract_id"] == "spread_1plus4_contract"
    assert scoped_policy.preferred_disposition is Disposition.SPREAD

    candidates = generate_candidates("Cmaj7", scoped_policy)
    assert candidates
    assert {candidate.disposition for candidate in candidates} == {Disposition.SPREAD}
    assert {int(candidate.density or 0) for candidate in candidates} == {5}
    assert {candidate.recipe_id for candidate in candidates} == {"spread_1plus4_contract"}
    assert {candidate.metadata.get("candidate_pool_source") for candidate in candidates} == {"grouped_spread_runtime"}


def test_blue_bossa_runtime_gets_low_frequency_spread_5note_and_no_generic_open(tmp_path: Path) -> None:
    score = json.loads((PROJECT_ROOT / "examples" / "leadsheets" / "blue_bossa.json").read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "bossa_nova",
            "tempo": int(score.get("tempo", 140)),
            "choruses": 3,
            "seed": 6124,
            "output_path": str(tmp_path / "blue_bossa_v2_6_124.mid"),
            "ensemble": {"bass_present": True},
            "voicing_override": {
                "enabled": True,
                "harmonic_expansion_enabled": True,
                "color_policy_mode": "style_safe_extensions",
                "metadata": {"harmonic_expansion_enabled": True, "color_policy_mode": "style_safe_extensions"},
            },
        }
    )
    assert result.ok

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
                }
            )
        if pattern_event.get("pattern_id") == "bossa_piano_core_batida_1_2_3and" and pattern_event.get("local_beat") in {0.0, 1.0}:
            velocities.append(int(expression.get("velocity") or 0))

    counts = Counter(f"d{row['density']}:{row['disposition']}:{row['method']}:{row['recipe_id']}" for row in rows)
    assert sum(1 for row in rows if row["density"] == 5 and row["disposition"] == "spread" and row["recipe_id"] == "spread_1plus4_contract") >= 2
    assert all(row["method"] != "generic_open" for row in rows)
    assert not any(row["density"] == 5 and row["disposition"] == "open" for row in rows)
    assert sum(count for key, count in counts.items() if key.startswith("d4:open:")) > sum(count for key, count in counts.items() if key.startswith("d5:spread:"))
    assert velocities and set(velocities[:4]) == {48}
