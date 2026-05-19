from __future__ import annotations

# harness token: test_v2_6_25_engine_voicing_request_orchestration_cache_boundary_audit

import ast
from collections import Counter
import json
from pathlib import Path

from jammate_engine.core.expression.expression_plan import EventExpression
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing.runtime.plan import VoicedNote, VoicingPlan
from jammate_engine.realization.realizer_voicing_request_orchestration import (
    REALIZER_VOICING_REQUEST_ORCHESTRATION_FORBIDDEN_RESPONSIBILITIES,
    REALIZER_VOICING_REQUEST_ORCHESTRATION_OWNED_RESPONSIBILITIES,
    REALIZER_VOICING_REQUEST_ORCHESTRATION_VERSION,
    RealizerVoicingRequestOrchestrator,
    base_voicing_policy_from_style_input,
    event_requests_fresh_voicing,
    realizer_voicing_request_orchestration_profile,
    region_voicing_cache_key,
    reuse_region_voicing,
)
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile

ROOT = Path(__file__).resolve().parents[1]
HARMONIC_REALIZER = ROOT / "src" / "jammate_engine" / "realization" / "harmonic_realizer.py"
REQUEST_ORCHESTRATION = ROOT / "src" / "jammate_engine" / "realization" / "realizer_voicing_request_orchestration.py"
DOC = ROOT / "docs" / "ENGINE_VOICING_REQUEST_ORCHESTRATION_CACHE_BOUNDARY_AUDIT_V2_6_25.md"
MISTY = ROOT / "examples" / "leadsheets" / "misty.json"


def _defined_symbols(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in module.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))}


def _imported_modules(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    return imports


def _event(event_id: str = "ev1", region_id: str = "r1", chord_symbol: str = "Cmaj7", metadata: dict | None = None) -> PatternEvent:
    return PatternEvent(
        event_id=event_id,
        track="piano",
        region_id=region_id,
        chord_symbol=chord_symbol,
        onset_beat=0.0,
        local_beat=1.0,
        role="comping",
        metadata=metadata or {},
    )


def _expr(event_id: str = "ev1") -> EventExpression:
    return EventExpression(event_id=event_id, duration_beats=1.0, velocity=64, articulation="sustain", pedal="none")


def _plan(event_id: str = "source_ev") -> VoicingPlan:
    return VoicingPlan(
        event_id=event_id,
        chord_symbol="Cmaj7",
        notes=[
            VoicedNote(midi_note=60, degree="1", voice_role="lowest", group_id="support_group"),
            VoicedNote(midi_note=64, degree="3", voice_role="inner_1", group_id="support_group"),
            VoicedNote(midi_note=67, degree="5", voice_role="inner_2", group_id="projection_group"),
            VoicedNote(midi_note=71, degree="7", voice_role="top", group_id="projection_group"),
        ],
    )


class StaticResolver:
    def __init__(self) -> None:
        self.calls = 0
        self.requests = []

    def resolve(self, request):  # noqa: ANN001 - test double mirrors runtime protocol
        self.calls += 1
        self.requests.append(request)
        return _plan(event_id=request.event_id)


def test_v2_6_25_request_orchestration_contract_is_explicit() -> None:
    assert REALIZER_VOICING_REQUEST_ORCHESTRATION_VERSION == "v2_6_25"
    assert "event_scoped_voicing_request_construction" in REALIZER_VOICING_REQUEST_ORCHESTRATION_OWNED_RESPONSIBILITIES
    assert "one_default_voicing_selection_per_chord_region_cache" in REALIZER_VOICING_REQUEST_ORCHESTRATION_OWNED_RESPONSIBILITIES
    assert "does_not_construct_degree_sources" in REALIZER_VOICING_REQUEST_ORCHESTRATION_FORBIDDEN_RESPONSIBILITIES
    assert "does_not_build_piano_audit_payloads" in REALIZER_VOICING_REQUEST_ORCHESTRATION_FORBIDDEN_RESPONSIBILITIES

    profile = realizer_voicing_request_orchestration_profile()
    debug = profile.to_debug_dict()
    assert debug["realizer_voicing_request_orchestration_version"] == "v2_6_25"
    assert debug["implementation_owner"] == "jammate_engine.realization.realizer_voicing_request_orchestration"
    assert debug["cache_contract"] == "one_default_voicing_selection_per_chord_region_until_explicit_gesture_revoices"
    assert debug["request_orchestration_only"] is True
    assert debug["no_source_construction_or_projection"] is True
    assert debug["no_audit_or_note_realization"] is True


def test_v2_6_25_harmonic_realizer_delegates_request_and_cache_orchestration() -> None:
    realizer_symbols = _defined_symbols(HARMONIC_REALIZER)
    assert "_event_requests_fresh_voicing" not in realizer_symbols
    assert "_reuse_region_voicing" not in realizer_symbols
    assert "region_voicing_cache_key" not in realizer_symbols

    text = HARMONIC_REALIZER.read_text(encoding="utf-8")
    assert "RealizerVoicingRequestOrchestrator" in text
    assert "base_voicing_policy_from_style_input" in text
    assert "VoicingRequest(" not in text
    assert "VoicingResolver(" not in text
    assert "policy_with_event_voicing_context(" not in text
    assert "region_voicing_cache" not in text


def test_v2_6_25_request_orchestration_module_owns_cache_and_request_without_source_projection_or_audit_imports() -> None:
    symbols = _defined_symbols(REQUEST_ORCHESTRATION)
    for expected in (
        "RealizerVoicingRequestOrchestrator",
        "base_voicing_policy_from_style_input",
        "region_voicing_cache_key",
        "event_requests_fresh_voicing",
        "reuse_region_voicing",
        "RealizerVoicingRequestOrchestrationProfile",
    ):
        assert expected in symbols

    imports = _imported_modules(REQUEST_ORCHESTRATION)
    forbidden_imports = {
        "jammate_engine.core.voicing.sources.content_planner",
        "jammate_engine.core.voicing.sources.content_source_inventory",
        "jammate_engine.core.voicing.sources.color_permission",
        "jammate_engine.core.voicing.sources.source_balance",
        "jammate_engine.core.voicing.disposition.projection",
        "jammate_engine.core.voicing.selection.selector",
        "jammate_engine.core.voicing.selection.scorer",
        "jammate_engine.realization.realizer_note_audit",
        "jammate_engine.realization.note_event_builder",
        "jammate_engine.realization.gesture_realizer",
        "jammate_engine.core.midi",
    }
    assert not (imports & forbidden_imports)

    text = REQUEST_ORCHESTRATION.read_text(encoding="utf-8")
    assert "VoicingRequest(" in text
    assert "policy_with_event_voicing_context(base_policy, event)" in text
    for forbidden_token in (
        "generate_candidates(",
        "project_basic_spread_candidates(",
        "select_voicing(",
        "piano_audit_event(",
        "NoteEvent(",
        "write_midi(",
    ):
        assert forbidden_token not in text


def test_v2_6_25_region_cache_reuses_until_explicit_fresh_revoicing() -> None:
    policy = base_voicing_policy_from_style_input(JazzBalladProfile().voicing_policy)
    orchestrator = RealizerVoicingRequestOrchestrator()
    resolver = StaticResolver()
    orchestrator.voicing_resolver = resolver
    orchestrator.begin_realization_pass()

    first = _event(event_id="ev1")
    second = _event(event_id="ev2")
    fresh = _event(event_id="ev3", metadata={"revoice_within_region": True})

    assert region_voicing_cache_key(first) == ("r1", "Cmaj7", "piano")
    assert event_requests_fresh_voicing(first) is False
    assert event_requests_fresh_voicing(fresh) is True

    first_plan = orchestrator.resolve_event_voicing(event=first, expression=_expr("ev1"), base_policy=policy, ensemble={"bass_present": True})
    second_plan = orchestrator.resolve_event_voicing(event=second, expression=_expr("ev2"), base_policy=policy, ensemble={"bass_present": True})
    fresh_plan = orchestrator.resolve_event_voicing(event=fresh, expression=_expr("ev3"), base_policy=policy, ensemble={"bass_present": True})

    assert resolver.calls == 2
    assert first_plan.event_id == "ev1"
    assert second_plan.event_id == "ev2"
    assert second_plan.metadata["region_voicing_reused"] is True
    assert second_plan.metadata["region_voicing_source_event_id"] == "ev1"
    assert second_plan.metadata["realizer_voicing_request_orchestration_version"] == "v2_6_25"
    assert fresh_plan.event_id == "ev3"

    reused = reuse_region_voicing(_plan("original"), "copy")
    assert reused.event_id == "copy"
    assert reused.metadata["region_voicing_source_event_id"] == "original"


def test_v2_6_25_doc_records_request_orchestration_cache_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_25_engine_voicing_request_orchestration_cache_boundary_audit",
        "harmonic_realizer.py",
        "realizer_voicing_request_orchestration.py",
        "RealizerVoicingRequestOrchestrator",
        "VoicingRequest",
        "one_default_voicing_selection_per_chord_region_until_explicit_gesture_revoices",
        "explicit fresh revoicing escape hatch",
        "does not construct degree sources",
        "does not decide color permission",
        "does not project closed/open/spread voicings",
        "does not build piano audit payloads",
        "5-note:6-note ~= 6:4",
        "maj7#11 remains off by default",
        "v2_6_26_engine_voicing_realization_surface_final_cleanup",
    ):
        assert token in text


def test_v2_6_25_misty_audit_density_and_cache_metadata_remain_stable(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_25.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    events = result.debug.get("piano_musical_audit_events", [])
    assert events
    voicings = [event.get("voicing") or {} for event in events]
    densities = Counter(int(voicing.get("density", 0)) for voicing in voicings)
    groupings = Counter(str(voicing.get("functional_grouping")) for voicing in voicings)

    assert densities[4] == 0
    assert "1+3" not in groupings
    assert "2+2" not in groupings
    five = densities[5]
    six = densities[6]
    ratio = five / float(five + six)
    assert 0.58 <= ratio <= 0.64
    assert densities[7] <= 3

    reused = [voicing for voicing in voicings if voicing.get("metadata", {}).get("region_voicing_reused")]
    assert reused
    assert all(
        voicing.get("metadata", {}).get("realizer_voicing_request_orchestration_version") == "v2_6_25"
        for voicing in reused
    )

    maj7_sharp11 = [
        voicing
        for voicing in voicings
        if "maj7" in str(voicing.get("chord_symbol"))
        and any(str(degree) == "#11" for degree in voicing.get("degrees", []))
    ]
    assert maj7_sharp11 == []
