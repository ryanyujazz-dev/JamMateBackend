from __future__ import annotations

# harness token: test_v2_6_15_engine_voicing_spread_runtime_gate_adapter_cleanup

import ast
from collections import Counter
import json
from pathlib import Path
from types import SimpleNamespace

from jammate_engine.core.voicing.disposition import (
    SPREAD_RUNTIME_GATE_ADAPTER_CLEANUP_VERSION,
)
from jammate_engine.core.voicing.disposition import spread as public_spread
from jammate_engine.core.voicing.disposition import spread_runtime_adapter, spread_runtime_gate
from jammate_engine.core.voicing.disposition.spread import project_basic_spread_contract
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = Path(__file__).resolve().parents[1]
SPREAD = ROOT / "src/jammate_engine/core/voicing/disposition/spread.py"
SPREAD_GATE = ROOT / "src/jammate_engine/core/voicing/disposition/spread_runtime_gate.py"
SPREAD_ADAPTER = ROOT / "src/jammate_engine/core/voicing/disposition/spread_runtime_adapter.py"
DOC = ROOT / "docs" / "ENGINE_VOICING_SPREAD_RUNTIME_GATE_ADAPTER_CLEANUP_V2_6_15.md"
MISTY = ROOT / "examples" / "leadsheets" / "misty.json"


def _defined_symbols(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in module.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))}


def _voicing_events(debug: dict) -> list[dict]:
    return [event.get("voicing") or {} for event in debug.get("piano_musical_audit_events", [])]


def test_v2_6_15_runtime_gate_and_adapter_have_dedicated_owners() -> None:
    assert SPREAD_RUNTIME_GATE_ADAPTER_CLEANUP_VERSION == "v2_6_15"
    assert SPREAD_GATE.exists()
    assert SPREAD_ADAPTER.exists()

    gate_symbols = _defined_symbols(SPREAD_GATE)
    assert "SpreadRuntimeGateDecision" in gate_symbols
    assert "SpreadCandidateSelectorRequest" in gate_symbols
    assert "SpreadCandidateSelectorResult" in gate_symbols
    assert "spread_runtime_gate_from_policy" in gate_symbols
    assert "select_spread_candidate_with_runtime_gate" in gate_symbols

    adapter_symbols = _defined_symbols(SPREAD_ADAPTER)
    assert "SpreadRuntimeAdapterStatus" in adapter_symbols
    assert "SpreadRuntimeAdapterFieldMapping" in adapter_symbols
    assert "SpreadRuntimeAdapterResult" in adapter_symbols
    assert "spread_runtime_adapter_field_mappings" in adapter_symbols
    assert "spread_runtime_adapter_owner_debug" in adapter_symbols

    spread_symbols = _defined_symbols(SPREAD)
    assert "SpreadRuntimeGateDecision" not in spread_symbols
    assert "SpreadCandidateSelectorResult" not in spread_symbols
    assert "spread_runtime_gate_from_policy" not in spread_symbols
    assert "select_spread_candidate_with_runtime_gate" not in spread_symbols
    assert "SpreadRuntimeAdapterStatus" not in spread_symbols
    assert "SpreadRuntimeAdapterFieldMapping" not in spread_symbols
    assert "SpreadRuntimeAdapterResult" not in spread_symbols
    assert "_spread_runtime_adapter_field_mappings" not in spread_symbols


def test_v2_6_15_public_compatibility_surface_reexports_runtime_owners() -> None:
    assert public_spread.SpreadRuntimeGateDecision is spread_runtime_gate.SpreadRuntimeGateDecision
    assert public_spread.select_spread_candidate_with_runtime_gate is spread_runtime_gate.select_spread_candidate_with_runtime_gate
    assert public_spread.SpreadRuntimeAdapterResult is spread_runtime_adapter.SpreadRuntimeAdapterResult
    assert public_spread.SpreadRuntimeAdapterStatus is spread_runtime_adapter.SpreadRuntimeAdapterStatus

    closed = public_spread.spread_runtime_gate_from_policy(texture_state=SimpleNamespace(primary_family="spread"))
    assert closed.selector_gate_open is False
    assert closed.to_debug_dict()["implementation_owner"] == "core.voicing.disposition.spread_runtime_gate"

    opened = public_spread.select_spread_candidate_with_runtime_gate(
        "Cmaj7",
        explicit_enable=True,
        texture_state=SimpleNamespace(primary_family="spread"),
        contract_ids=("spread_2plus3_contract",),
    )
    debug = opened.to_debug_dict()
    assert debug["implementation_owner"] == "core.voicing.disposition.spread_runtime_gate"
    assert debug["candidate_conversion_allowed"] is False
    assert debug["style_runtime_wiring_enabled"] is False
    assert debug["notes_only"] is True
    assert opened.selected is not None


def test_v2_6_15_adapter_field_mapping_owner_does_not_change_candidate_signature() -> None:
    candidate = [item for item in project_basic_spread_contract("Cmaj7", "spread_2plus3_contract").candidates if item.is_legal][0]
    result = public_spread.spread_projection_candidate_to_voicing_candidate_adapter(
        candidate,
        allow_conversion=True,
        selector_reason="v2_6_15_runtime_adapter_owner_test",
    )
    debug = result.to_debug_dict()

    assert debug["implementation_owner"] == "core.voicing.disposition.spread_runtime_adapter"
    assert debug["converted"] is True
    assert debug["candidate_generator_wiring_allowed"] is False
    assert debug["style_runtime_wiring_enabled"] is False
    assert debug["no_expression_or_pedal"] is True
    assert debug["adapted_candidate_debug"]["notes"] == list(candidate.notes)
    assert debug["adapted_candidate_debug"]["degrees"] == list(candidate.degrees)

    owner_debug = public_spread.spread_runtime_adapter_owner_debug()
    assert owner_debug["implementation_owner"] == "core.voicing.disposition.spread_runtime_adapter"
    assert owner_debug["field_mapping_count"] >= 6


def test_v2_6_15_doc_exists_and_misty_density_ratio_regression_stays_stable(tmp_path: Path) -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_15_engine_voicing_spread_runtime_gate_and_adapter_cleanup",
        "spread_runtime_gate.py",
        "spread_runtime_adapter.py",
        "behavior-preserving",
        "5-note:6-note",
        "Pattern / Anticipation / Expression / Gesture / MIDI",
    ):
        assert token in text

    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_15.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    voicings = _voicing_events(result.debug)
    densities = Counter(int(voicing.get("density", 0)) for voicing in voicings)
    groupings = Counter(str(voicing.get("functional_grouping")) for voicing in voicings)

    assert densities[4] == 0
    assert "1+3" not in groupings
    assert "2+2" not in groupings
    five = densities[5]
    six = densities[6]
    ratio = five / float(five + six)
    assert 0.58 <= ratio <= 0.62
    assert densities[7] <= 3

    maj7_sharp11 = [
        voicing for voicing in voicings
        if "maj7" in str(voicing.get("chord_symbol"))
        and any(str(degree) == "#11" for degree in voicing.get("degrees", []))
    ]
    assert maj7_sharp11 == []
