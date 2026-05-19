from __future__ import annotations

import random

from jammate_engine.core.roles import EnsembleContext

from ..selection.candidate_generator import generate_candidates
from .plan import VoicedNote, VoicingPlan
from ..taxonomy.projection_map import ABSTRACT_GROUP_KEYS, build_projection_map, group_indices_for_projection
from .request import VoicingRequest
from ..selection.selector import select_candidate
from .state import VoicingState, state_advance_notes_and_degrees


class VoicingResolver:
    """Resolve vertical voicings with runtime continuity state.

    The resolver is intentionally stateful within one generation pass. It keeps
    the previous piano voicing so the selector can prefer smoother movement,
    top-voice continuity, and safer register placement. Styles still only send
    policies; they do not decide concrete note choices.
    """

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng
        self.state = VoicingState.empty()

    def reset_state(self) -> None:
        self.state = VoicingState.empty()

    def resolve(self, request: VoicingRequest) -> VoicingPlan:
        ensemble_context = EnsembleContext.from_dict(request.ensemble_context)
        policy = request.policy.with_ensemble_context(ensemble_context)
        candidates = generate_candidates(request.chord_symbol, policy)
        candidate = select_candidate(candidates, policy=policy, state=self.state, rng=request.rng or self.rng)
        group_indices = group_indices_for_projection(
            len(candidate.notes),
            candidate.functional_grouping,
            candidate.group_roles,
        )
        group_by_index = _group_by_voice_index(group_indices)
        voiced = []
        for idx, note in enumerate(candidate.notes):
            role = "lowest" if idx == 0 else "top" if idx == len(candidate.notes) - 1 else f"inner_{idx}"
            degree = candidate.degrees[idx] if idx < len(candidate.degrees) else "?"
            hand = "right" if policy.ensemble_role.value == "piano_rh_harmonic_comping" else "left" if note <= 54 else "right"
            voiced.append(VoicedNote(midi_note=note, degree=degree, voice_role=role, hand=hand, group_id=group_by_index.get(idx)))
        projection_map = build_projection_map(
            [n.midi_note for n in voiced],
            functional_grouping=candidate.functional_grouping,
            group_roles=candidate.group_roles,
        )
        groups = {key: list(projection_map[key]) for key in ABSTRACT_GROUP_KEYS if key in projection_map}
        plan = VoicingPlan(
            event_id=request.event_id,
            chord_symbol=request.chord_symbol,
            notes=voiced,
            projection_map=projection_map,
            groups=groups,
            content_family=candidate.content_family.value if candidate.content_family else None,
            disposition=candidate.disposition.value,
            root_support=candidate.root_support.value,
            bass_relation=candidate.bass_relation.value,
            interval_structure=candidate.interval_structure.value,
            root_included=candidate.root_included,
            density=candidate.density,
            functional_grouping=candidate.functional_grouping.value if candidate.functional_grouping else None,
            recipe_id=candidate.recipe_id,
            group_roles=[role.value for role in candidate.group_roles],
            root_support_decision=dict(candidate.root_support_decision),
            disposition_guard=dict(candidate.disposition_guard),
            register_guard=dict(candidate.register_guard),
            voice_leading_profile=dict(candidate.voice_leading_profile),
            selector_decision=dict(candidate.selector_decision),
            ensemble_role=policy.ensemble_role.value,
            metadata={
                **dict(candidate.metadata),
                "voicing_contract_version": "v2_0_41",
                "voicing_core_pipeline": [
                    "content_family",
                    "content_recipe",
                    "content_validity",
                    "root_support",
                    "root_support_decision",
                    "density_recipe",
                    "disposition",
                    "disposition_guard",
                    "register_guard",
                    "register_projection",
                    "candidate_scoring",
                    "voice_leading_profile",
                    "stateful_selection",
                    "selector_decision",
                    "projection_map",
                    "functional_group_projection",
                ],
                "ensemble_role": policy.ensemble_role.value,
                "root_support_decision": dict(candidate.root_support_decision),
                "disposition_guard": dict(candidate.disposition_guard),
                "register_guard": dict(candidate.register_guard),
                "voice_leading_profile": dict(candidate.voice_leading_profile),
                "selector_decision": dict(candidate.selector_decision),
                "ensemble_context": ensemble_context.to_dict(),
                "previous_voicing_state": self.state.to_debug_dict(),
            },
        )
        state_notes, state_degrees, state_anchor = state_advance_notes_and_degrees(
            metadata=candidate.metadata,
            realized_notes=[note.midi_note for note in voiced],
            realized_degrees=[note.degree for note in voiced],
        )
        state_metadata = {
            "score_breakdown": dict(candidate.metadata.get("score_breakdown", {})),
            "selector_decision": dict(candidate.selector_decision),
            "voice_leading_profile": dict(candidate.voice_leading_profile),
            "recipe_id": candidate.recipe_id,
            "functional_grouping": candidate.functional_grouping.value if candidate.functional_grouping else None,
            "content_family": candidate.content_family.value if candidate.content_family else None,
            "rootless_ab_content_type": candidate.metadata.get("rootless_ab_content_type"),
            "rootless_ab_orientation_family": candidate.metadata.get("rootless_ab_orientation_family"),
            # Preserve abstract SPREAD group state so later voicing selection can
            # voice-lead lower/foundation and upper/projection groups separately.
            "lower_group_notes": candidate.metadata.get("lower_group_notes"),
            "upper_group_notes": candidate.metadata.get("upper_group_notes"),
            "upper_group_degrees": candidate.metadata.get("upper_group_degrees"),
            "lower_group_placed_degrees": candidate.metadata.get("lower_group_placed_degrees"),
            "group_gap_semitones": candidate.metadata.get("group_gap_semitones"),
            "spread_recipe_id": candidate.metadata.get("recipe_id") or candidate.recipe_id,
        }
        if state_anchor is not None:
            state_metadata = state_anchor.to_state_metadata(state_metadata)
        self.state = self.state.advance(
            event_id=request.event_id,
            chord_symbol=request.chord_symbol,
            notes=state_notes,
            degrees=state_degrees,
            onset_beat=request.onset_beat,
            metadata=state_metadata,
        )
        return plan


def _group_by_voice_index(groups: dict[str, list[int]]) -> dict[int, str]:
    out: dict[int, str] = {}
    for group_id, indices in groups.items():
        for index in indices:
            out.setdefault(int(index), group_id)
    return out
