from __future__ import annotations

import importlib.util
import json
from dataclasses import replace
from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION, build_voicing_override_policy
from jammate_engine.core.voicing.selection.selector import _semantic_source_key, _source_realization_cost, select_candidate
from jammate_engine.core.voicing.runtime.state import VoicingState
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = Path(__file__).resolve().parents[1]
_SCRIPT_PATH = ROOT / "examples" / "scripts" / "generate_4note_source_weight_listening_verification_demos.py"
_SCRIPT_SPEC = importlib.util.spec_from_file_location("v2137_listening_script", _SCRIPT_PATH)
assert _SCRIPT_SPEC and _SCRIPT_SPEC.loader
_SCRIPT_MODULE = importlib.util.module_from_spec(_SCRIPT_SPEC)
_SCRIPT_SPEC.loader.exec_module(_SCRIPT_MODULE)
FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE = _SCRIPT_MODULE.FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE


def test_v2_1_37_contract_versions_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_OVERRIDE_CONTRACT_VERSION == "v2_1_43"


def test_v2_1_37_override_enables_closed_only_minimum_motion() -> None:
    override = FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE
    assert override["preferred_density"] == 4
    assert override["min_density"] == 4
    assert override["max_density"] == 4
    assert override["preferred_disposition"] == "closed"
    assert override["allowed_dispositions"] == ["closed"]
    assert override["metadata"]["closed_voicing_lowest_note_floor"] == 53
    assert override["metadata"]["strict_closed_compact_pitch_class_layout"] is True
    assert override["metadata"]["strict_closed_max_span"] == 12
    assert override["metadata"]["closed_4note_per_source_minimum_motion"] is True


def test_v2_1_37_selector_keeps_nearest_realization_for_selected_source() -> None:
    policy = build_voicing_override_policy({}, FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE, style_name="jazz_ballad")
    policy = replace(policy.with_ensemble_context({"bass_present": True}), selector_temperature=0.0)
    state = VoicingState.empty().advance(
        event_id="prev",
        chord_symbol="Cmaj9",
        notes=[60, 62, 64, 67],
        degrees=["R", "9", "3", "5"],
    )
    raw_candidates = generate_candidates("Am9", policy)
    selected = select_candidate(raw_candidates, policy=policy, state=state, rng=None)

    assert selected.metadata["closed_4note_per_source_minimum_motion"] is True
    assert selected.metadata["closed_4note_source_collapse_candidate_count"] >= 2
    selected_key = _semantic_source_key(selected)
    source_candidates = [candidate for candidate in raw_candidates if _semantic_source_key(candidate) == selected_key]
    selected_cost = _source_realization_cost(selected, policy=policy, state=state)
    best_cost = min(_source_realization_cost(candidate, policy=policy, state=state) for candidate in source_candidates)
    assert selected_cost == best_cost
    assert min(selected.notes) >= 57
    assert max(selected.notes) - min(selected.notes) <= 12


def test_v2_1_37_ballad_trace_has_closed_minimum_motion_stats(tmp_path: Path) -> None:
    score = json.loads((ROOT / "examples" / "leadsheets" / "color_rich_ballad_voicing_progression.json").read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "jazz_ballad",
            "tempo": 76,
            "choruses": 1,
            "seed": 937,
            "output_path": str(tmp_path / "ballad_minimum_motion_probe.mid"),
            "ensemble": {"bass_present": True},
            "voicing_override": dict(FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE),
        }
    )
    audit = build_piano_musical_audit(result.debug)
    assert audit.event_rows
    assert audit.summary["closed_4note_minimum_motion_events"] == audit.summary["events"]
    assert audit.summary["min_closed_voicing_lowest_note"] >= 53
    assert audit.summary["max_closed_voicing_span"] <= 12
    assert audit.summary["avg_closed_4note_source_collapse_distance"] <= 2.0
    assert all(row["closed_4note_per_source_minimum_motion"] for row in audit.event_rows)


def test_v2_1_37_docs_and_future_backlog_are_synced() -> None:
    required_docs = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "VOICING_MODULE_CORE_LOGIC_V2.md",
        ROOT / "docs" / "VOICING_SYSTEM_V2_DESIGN.md",
        ROOT / "docs" / "GENERATION_RULES_SUMMARY_V2.md",
        ROOT / "docs" / "STYLE_RULE_BASELINE_V2.md",
        ROOT / "docs" / "VOICING_TUNING_WORKFLOW_V2.md",
        ROOT / "docs" / "DEVELOPMENT_HARNESS_V2.md",
        ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md",
        ROOT / "docs" / "API_CONTRACT_V2.md",
        ROOT / "docs" / "SYSTEM_CONTRACTS_V2.md",
        ROOT / "docs" / "ARCHITECTURE_V2.md",
        ROOT / "docs" / "FUTURE_IDEAS_BACKLOG_V2.md",
    ]
    for path in required_docs:
        text = path.read_text(encoding="utf-8")
        assert "v2_1_37" in text, path
    backlog = (ROOT / "docs" / "FUTURE_IDEAS_BACKLOG_V2.md").read_text(encoding="utf-8")
    assert "Top-k nearest realizations" in backlog
    assert "Gesture-driven revoicing" in backlog
    assert "Do not generalize v2_1_37 immediately" in backlog
