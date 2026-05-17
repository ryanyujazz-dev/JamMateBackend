from __future__ import annotations

import ast
from pathlib import Path

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.voicing import (
    VOICING_CONTRACT_VERSION,
    VOICING_CORE_PIPELINE,
    ContentFamily,
    Disposition,
    RootSupportPolicy,
    VoicingPolicy,
    VoicingRequest,
    VoicingResolver,
    choose_content_families,
    generate_candidates,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_voicing_public_contract_version_and_pipeline_are_exported() -> None:
    assert VOICING_CONTRACT_VERSION >= "v2_0_32"
    assert VOICING_CORE_PIPELINE[0] == "VoicingPolicy"
    assert VOICING_CORE_PIPELINE[-1] == "VoicingPlan"
    assert "content_family" in VOICING_CORE_PIPELINE
    assert "density_recipe" in VOICING_CORE_PIPELINE
    assert "stateful_selection" in VOICING_CORE_PIPELINE


def test_policy_effective_contract_helpers_do_not_change_selection_semantics() -> None:
    policy = VoicingPolicy(
        root_support=RootSupportPolicy.ROOT_REQUIRED,
        preferred_content=ContentFamily.SEVENTH_BASIC,
        preferred_disposition=Disposition.CLOSED,
        min_density=3,
        preferred_density=9,
        max_density=4,
    )
    assert policy.effective_density_range == (3, 4, 4)
    assert policy.effective_dispositions == (Disposition.CLOSED,)
    assert policy.is_root_required is True

    families = choose_content_families("Dm7", policy)
    assert families == [ContentFamily.SEVENTH_BASIC]
    candidate = generate_candidates("Dm7", policy)[0]
    assert set(candidate.degrees) == {"R", "b3", "5", "b7"}
    assert candidate.to_debug_dict()["root_support"] == "root_required"


def test_voicing_request_and_plan_have_stable_debug_contract() -> None:
    request = VoicingRequest(
        event_id="v2_0_30_event",
        chord_symbol="G13b9",
        track="piano",
        gesture_type="simultaneous_onset",
        gesture=simultaneous_onset(metadata={"source": "contract_test"}),
        expression_articulation="sustain",
        ensemble_context={"bass_present": True},
        policy=VoicingPolicy(
            root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
            preferred_content=ContentFamily.ROOTLESS_A,
            preferred_disposition=Disposition.OPEN,
            selector_temperature=0.0,
        ),
        onset_beat=4.0,
    )
    request_debug = request.to_debug_dict()
    assert request_debug["policy"]["root_support"] == "rootless_allowed"
    assert request_debug["gesture"]["kind"] == "simultaneous_onset"
    assert request_debug["has_rng"] is False

    plan = VoicingResolver().resolve(request)
    plan_debug = plan.to_debug_dict()
    assert plan_debug["event_id"] == "v2_0_30_event"
    assert plan_debug["midi_notes"] == plan.midi_notes
    assert plan_debug["degrees"] == plan.degrees
    assert plan_debug["projection_map"]["top"] == [len(plan.notes) - 1]
    assert plan_debug["metadata"]["voicing_contract_version"] >= "v2_0_32"
    assert "candidate_scoring" in plan_debug["metadata"]["voicing_core_pipeline"]


def test_core_voicing_keeps_dependency_boundary_clean() -> None:
    forbidden_import_roots = {
        "jammate_engine.styles",
        "jammate_engine.generation",
        "jammate_engine.realization",
        "jammate_engine.midi",
    }
    for py_file in (PROJECT_ROOT / "src/jammate_engine/core/voicing").glob("*.py"):
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            module = None
            if isinstance(node, ast.ImportFrom):
                module = node.module
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name
                    assert all(not module.startswith(root) for root in forbidden_import_roots), py_file
                continue
            if module:
                assert all(not module.startswith(root) for root in forbidden_import_roots), py_file


def test_realization_consumes_voicing_through_public_facade() -> None:
    harmonic_realizer = PROJECT_ROOT / "src/jammate_engine/realization/harmonic_realizer.py"
    gesture_realizer = PROJECT_ROOT / "src/jammate_engine/realization/gesture_realizer.py"
    assert "from jammate_engine.core.voicing import VoicingPolicy, VoicingRequest, VoicingResolver" in harmonic_realizer.read_text()
    assert "from jammate_engine.core.voicing import VoicedNote, VoicingPlan" in gesture_realizer.read_text()
