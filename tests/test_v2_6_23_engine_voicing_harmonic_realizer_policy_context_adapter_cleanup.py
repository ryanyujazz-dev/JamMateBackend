from __future__ import annotations

# harness token: test_v2_6_23_engine_voicing_harmonic_realizer_policy_context_adapter_cleanup

import ast
from collections import Counter
import json
from pathlib import Path

from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.realization.voicing_policy_context_adapter import (
    HARMONIC_REALIZER_POLICY_CONTEXT_ADAPTER_FORBIDDEN_RESPONSIBILITIES,
    HARMONIC_REALIZER_POLICY_CONTEXT_ADAPTER_OWNED_RESPONSIBILITIES,
    HARMONIC_REALIZER_POLICY_CONTEXT_ADAPTER_VERSION,
    harmonic_realizer_policy_context_adapter_profile,
    policy_with_event_voicing_context,
)
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile

ROOT = Path(__file__).resolve().parents[1]
HARMONIC_REALIZER = ROOT / "src" / "jammate_engine" / "realization" / "harmonic_realizer.py"
ADAPTER = ROOT / "src" / "jammate_engine" / "realization" / "voicing_policy_context_adapter.py"
DOC = ROOT / "docs" / "ENGINE_VOICING_HARMONIC_REALIZER_POLICY_CONTEXT_ADAPTER_CLEANUP_V2_6_23.md"
MISTY = ROOT / "examples" / "leadsheets" / "misty.json"


def _imported_modules(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    return imports


def _defined_symbols(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in module.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))}


def _voicing_events(debug: dict) -> list[dict]:
    return [event.get("voicing") or {} for event in debug.get("piano_musical_audit_events", [])]


def test_v2_6_23_policy_context_adapter_contract_is_explicit() -> None:
    assert HARMONIC_REALIZER_POLICY_CONTEXT_ADAPTER_VERSION == "v2_6_23"
    assert "event_scoped_voicing_policy_metadata_bridge" in HARMONIC_REALIZER_POLICY_CONTEXT_ADAPTER_OWNED_RESPONSIBILITIES
    assert "does_not_project_closed_open_or_spread_voicings" in HARMONIC_REALIZER_POLICY_CONTEXT_ADAPTER_FORBIDDEN_RESPONSIBILITIES

    profile = harmonic_realizer_policy_context_adapter_profile()
    debug = profile.to_debug_dict()
    assert debug["harmonic_realizer_policy_context_adapter_version"] == "v2_6_23"
    assert debug["implementation_owner"] == "jammate_engine.realization.voicing_policy_context_adapter"
    assert debug["policy_context_only"] is True
    assert debug["no_projection_or_selector"] is True
    assert "does_not_construct_degree_sources" in debug["forbidden_responsibilities"]


def test_v2_6_23_harmonic_realizer_no_longer_owns_event_policy_context_helpers() -> None:
    realizer_symbols = _defined_symbols(HARMONIC_REALIZER)
    retired_realizer_helpers = {
        "_policy_with_event_texture_scope",
        "_policy_with_event_harmonic_context",
        "_policy_with_ballad_spread_grouping_mix_policy",
        "_policy_with_spread_upper_3note_expansion_ratio",
        "_policy_with_spread_upper_4note_expansion_ratio",
        "_policy_with_spread_lower_2note_rooted_equal_cycle",
        "_spread_expansion_ratio_slot",
        "_texture_contrast_plan_metadata",
    }
    assert retired_realizer_helpers.isdisjoint(realizer_symbols)

    text = HARMONIC_REALIZER.read_text(encoding="utf-8")
    assert "RealizerVoicingRequestOrchestrator" in text
    request_orchestration = (ROOT / "src" / "jammate_engine" / "realization" / "realizer_voicing_request_orchestration.py").read_text(encoding="utf-8")
    assert "policy_with_event_voicing_context(base_policy, event)" in request_orchestration
    assert "resolve_ballad_spread_grouping_mix_policy" not in text
    assert "ColorPolicyMode" not in text
    assert "parse_chord" not in text


def test_v2_6_23_adapter_owns_context_helpers_without_projection_selection_or_source_imports() -> None:
    adapter_symbols = _defined_symbols(ADAPTER)
    assert "policy_with_event_voicing_context" in adapter_symbols
    assert "HarmonicRealizerPolicyContextAdapterProfile" in adapter_symbols
    assert "_policy_with_event_harmonic_context" in adapter_symbols
    assert "_policy_with_ballad_spread_grouping_mix_policy" in adapter_symbols

    imports = _imported_modules(ADAPTER)
    forbidden_imports = {
        "jammate_engine.core.voicing.sources.content_planner",
        "jammate_engine.core.voicing.sources.content_source_inventory",
        "jammate_engine.core.voicing.sources.color_permission",
        "jammate_engine.core.voicing.sources.source_balance",
        "jammate_engine.core.voicing.disposition.projection",
        "jammate_engine.core.voicing.selection.selector",
        "jammate_engine.core.voicing.selection.scorer",
        "jammate_engine.core.voicing.selection.candidate_generator",
        "jammate_engine.core.midi",
        "jammate_engine.realization.gesture_realizer",
    }
    assert not (imports & forbidden_imports)

    text = ADAPTER.read_text(encoding="utf-8")
    for forbidden_token in (
        "VoicingResolver(",
        "VoicingRequest(",
        "generate_candidates(",
        "project_basic_spread_candidates(",
        "select_voicing(",
        "write_midi(",
        "NoteEvent(",
    ):
        assert forbidden_token not in text


def test_v2_6_23_policy_context_adapter_preserves_ballad_grouping_metadata_bridge() -> None:
    policy = JazzBalladProfile().voicing_policy
    event = PatternEvent(
        event_id="piano-test-event",
        track="piano",
        region_id="c0_b4_ch0",
        chord_symbol="Cmaj7",
        onset_beat=16.0,
        local_beat=1.0,
        role="comping",
        metadata={
            "region_id": "c0_b4_ch0",
            "region_performance_bar_index": 4,
            "region_bar_index": 4,
            "region_chord_index": 0,
            "region_section_id": "A",
            "region_section_label": "A",
            "region_phrase": "A",
            "region_section_role": "normal",
            "region_chorus_index": 0,
            "region_total_choruses": 3,
            "home_key": "Eb",
            "previous_chord_symbol": "G7",
            "next_chord_symbol": "F7",
        },
    )

    adapted = policy_with_event_voicing_context(policy, event)
    metadata = dict(adapted.metadata or {})
    assert metadata["chord_symbol"] == "Cmaj7"
    assert metadata["previous_chord_symbol"] == "G7"
    assert metadata["next_chord_symbol"] == "F7"
    assert metadata["altered_dominant_functional_scope_context_version"] == "v2_2_85"
    assert metadata["ballad_spread_grouping_mix_policy_version"] == "v2_6_22"
    assert metadata["primary_family"] == "spread"
    assert metadata["allowed_families"] == ["spread"]
    assert metadata["spread_grouping_mix_candidate_pool"]["version"] == "v2_6_22"
    assert metadata["spread_runtime_adapter"]["adapter_conversion_allowed"] is True
    assert metadata["retired_ballad_spread_pilot_metadata_removed"] is True


def test_v2_6_23_doc_records_harmonic_realizer_adapter_cleanup() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_23_engine_voicing_harmonic_realizer_policy_context_adapter_cleanup",
        "harmonic_realizer.py",
        "voicing_policy_context_adapter.py",
        "policy_with_event_voicing_context",
        "does not construct degree sources",
        "does not decide color permission",
        "does not project closed/open/spread voicings",
        "does not score or select candidates",
        "5-note:6-note ~= 6:4",
        "maj7#11 remains off by default",
        "v2_6_24_engine_voicing_realizer_note_audit_cleanup",
    ):
        assert token in text


def test_v2_6_23_misty_density_and_color_guardrails_remain_unchanged(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_23.mid"),
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
    assert 0.58 <= ratio <= 0.63
    assert densities[7] <= 3

    maj7_sharp11 = [
        voicing
        for voicing in voicings
        if "maj7" in str(voicing.get("chord_symbol"))
        and any(str(degree) == "#11" for degree in voicing.get("degrees", []))
    ]
    assert maj7_sharp11 == []
