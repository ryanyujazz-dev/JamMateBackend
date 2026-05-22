from __future__ import annotations

import importlib.util
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

from jammate_engine.core.expression.expression_plan import EventExpression
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing.runtime.plan import VoicedNote, VoicingPlan
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.realization.realizer_voicing_request_orchestration import (
    STYLE_NEUTRAL_FOUR_NOTE_ORIENTATION_ALIGNMENT_WIRING_VERSION,
    RealizerVoicingRequestOrchestrator,
)
from jammate_engine.styles.bossa_nova.voicing_policy import get_voicing_policy as get_bossa_voicing_policy
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy as get_ballad_voicing_policy
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as get_swing_voicing_policy

MILESTONE_ID = "v2_6_117"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_style_neutral_four_note_orientation_alignment_audit.py"
    spec = importlib.util.spec_from_file_location("generate_engine_style_neutral_four_note_orientation_alignment_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _event(index: int, chord: str, *, previous: str | None = None, next_: str | None = None, section: str = "A") -> PatternEvent:
    return PatternEvent(
        event_id=f"ev{index}",
        track="piano",
        region_id=f"c0_b{index}_ch0_{chord}",
        chord_symbol=chord,
        onset_beat=float(index * 4),
        local_beat=0.0,
        role="comp",
        metadata={
            "previous_chord_symbol": previous,
            "next_chord_symbol": next_,
            "region_section_id": section,
            "region_section_label": section,
            "region_phrase": section,
            "region_section_role": "normal",
            "region_chorus_index": 0,
            "region_total_choruses": 1,
            "region_performance_bar_index": index,
            "region_chord_index": 0,
        },
    )


def _expr(event_id: str) -> EventExpression:
    return EventExpression(event_id=event_id, duration_beats=0.5, velocity=64, articulation="short", pedal="none")


def _rootless_plan(event_id: str, chord: str, method: str, orientation: str, *, content: str = "with_5", source: str = "third_fifth_seventh_ninth") -> VoicingPlan:
    return VoicingPlan(
        event_id=event_id,
        chord_symbol=chord,
        notes=[
            VoicedNote(midi_note=57, degree="3", voice_role="lowest"),
            VoicedNote(midi_note=60, degree="5", voice_role="inner_1"),
            VoicedNote(midi_note=64, degree="7", voice_role="inner_2"),
            VoicedNote(midi_note=67, degree="9", voice_role="top"),
        ],
        content_family="rootless_A" if orientation == "A" else "rootless_B",
        disposition="open",
        metadata={
            "disposition_projection_family": "open",
            "disposition_projection_method": method,
            "four_note_rotation_family": "rootless_ab",
            "four_note_rotation_content_type": content,
            "four_note_rotation_source_family": source,
            "four_note_rotation_ab_side": orientation,
            "four_note_rotation_ab_pair_index": 0,
            "four_note_rotation_inversion_index": 0,
            "four_note_rotation_follow_inversion_index": 0,
            "four_note_rotation_ab_eligible": True,
            "rootless_ab_orientation_family": orientation,
            "rootless_ab_content_type": content,
            "rootless_ab_inversion_index": 0,
            "rootless_ab_functional_source_type": source,
        },
    )


class SequenceResolver:
    def __init__(self, plans: list[VoicingPlan]) -> None:
        self.plans: Iterator[VoicingPlan] = iter(plans)
        self.requests = []

    def resolve(self, request):  # noqa: ANN001 - test double mirrors runtime resolver protocol
        self.requests.append(request)
        plan = next(self.plans)
        return replace(plan, event_id=request.event_id, chord_symbol=request.chord_symbol)


def test_v2_6_117_style_policies_expose_style_neutral_orientation_continuity_contract() -> None:
    for style, policy in {
        "bossa_nova": get_bossa_voicing_policy(),
        "medium_swing": get_swing_voicing_policy(),
        "jazz_ballad": get_ballad_voicing_policy(),
    }.items():
        metadata = dict(policy.metadata or {})
        assert metadata["progression_four_note_orientation_alignment_policy_version"] == MILESTONE_ID
        assert metadata["progression_four_note_orientation_alignment_policy_enabled"] is True
        assert metadata["progression_four_note_orientation_alignment_policy_target"]["orientation_motion"] == "A_to_B__B_to_A"
        assert metadata["progression_four_note_orientation_alignment_policy_target"]["does_not_apply_post_voicing_note_alteration"] is True
        assert "Medium Swing" not in metadata["progression_four_note_orientation_alignment_policy_contract"] or style == "medium_swing"


def test_v2_6_117_bossa_orchestrator_requests_neutral_ab_flip_without_medium_swing_style_gate() -> None:
    orchestrator = RealizerVoicingRequestOrchestrator()
    resolver = SequenceResolver([
        _rootless_plan("ev1", "Dm9", "drop2", "A", content="with_5", source="third_fifth_seventh_ninth"),
        _rootless_plan("ev2", "G7b9b13", "drop2", "B", content="altered_dominant_rootless", source="altered_dominant_rootless"),
    ])
    orchestrator.voicing_resolver = resolver
    orchestrator.begin_realization_pass()
    policy = replace(get_bossa_voicing_policy(), harmonic_expansion_enabled=True, color_policy_mode="altered_dominant")

    orchestrator.resolve_event_voicing(event=_event(1, "Dm7b5", next_="G7b9"), expression=_expr("ev1"), base_policy=policy, ensemble={"bass_present": True})
    orchestrator.resolve_event_voicing(event=_event(2, "G7b9", previous="Dm7b5", next_="Cm7"), expression=_expr("ev2"), base_policy=policy, ensemble={"bass_present": True})

    second_meta = resolver.requests[1].policy.metadata
    assert second_meta["style"] == "bossa_nova"
    assert second_meta["progression_voicing_method_lock_policy_applied"] is True
    assert second_meta["progression_four_note_orientation_alignment_policy_version"] == STYLE_NEUTRAL_FOUR_NOTE_ORIENTATION_ALIGNMENT_WIRING_VERSION
    assert second_meta["progression_four_note_orientation_alignment_policy_applied"] is True
    assert second_meta["progression_four_note_orientation_alignment_policy_previous_ab_side"] == "A"
    assert second_meta["progression_four_note_orientation_alignment_policy_desired_ab_side"] == "B"
    assert second_meta["style_neutral_four_note_orientation_alignment_no_voicing_projection_change"] is True
    assert "medium_swing_four_note_rotation_alignment_policy_applied" not in second_meta


def test_v2_6_117_neutral_candidate_filter_allows_altered_dominant_source_change_while_enforcing_ab_side() -> None:
    policy = replace(get_bossa_voicing_policy(), harmonic_expansion_enabled=True, color_policy_mode="altered_dominant")
    metadata = dict(policy.metadata or {})
    metadata.update(
        {
            "progression_four_note_orientation_alignment_policy_runtime_enabled": True,
            "progression_four_note_orientation_alignment_policy_applied": True,
            "progression_four_note_orientation_alignment_policy_runtime_filtering_enabled": True,
            "progression_four_note_orientation_alignment_policy_desired_family": "rootless_ab",
            "progression_four_note_orientation_alignment_policy_desired_ab_side": "B",
            # These previous-source audit anchors intentionally do not hard-block
            # the altered dominant source chosen earlier by expansion/alter policy.
            "progression_four_note_orientation_alignment_policy_desired_content_type": "with_5",
            "progression_four_note_orientation_alignment_policy_desired_source_family": "third_fifth_seventh_ninth",
            "progression_four_note_orientation_alignment_policy_desired_ab_pair_index": 0,
            "progression_four_note_orientation_alignment_policy_desired_inversion_index": 0,
        }
    )
    candidates = generate_candidates("G7b9b13", replace(policy, metadata=metadata))

    assert candidates
    assert {candidate.metadata.get("four_note_rotation_family") for candidate in candidates} == {"rootless_ab"}
    assert {candidate.metadata.get("four_note_rotation_ab_side") for candidate in candidates} == {"B"}
    assert {candidate.metadata.get("four_note_rotation_source_family") for candidate in candidates} == {"altered_dominant_rootless"}
    assert all(candidate.metadata.get("progression_four_note_orientation_alignment_policy_filter_applied") is True for candidate in candidates)
    assert all(candidate.metadata.get("progression_four_note_orientation_alignment_policy_candidate_matches") is True for candidate in candidates)


def test_v2_6_117_acceptance_passes_for_style_neutral_orientation_alignment_audit() -> None:
    module = _load_script_module()
    audits = [module.generate_style_audit(style, spec) for style, spec in module.SPEC_BY_STYLE.items()]
    summary = {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": "test",
        "styles": audits,
    }
    summary["global_findings"] = module.build_global_findings(audits)
    acceptance = module.acceptance(summary)

    assert acceptance["passed"] is True
