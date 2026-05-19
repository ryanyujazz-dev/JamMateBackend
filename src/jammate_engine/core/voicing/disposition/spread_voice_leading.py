from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .spread_contracts import SPREAD_RECIPE_CONTRACT_VERSION
from .spread_register_guards import BASIC_SPREAD_PROJECTION_VERSION

GROUPWISE_SPREAD_VOICE_LEADING_VERSION = "v2_2_41"
SPREAD_GROUPWISE_VOICE_LEADING_SPLIT_VERSION = "v2_6_12"


@dataclass(frozen=True)
class SpreadGroupwiseVoiceLeadingWeights:
    """Weights for notes-only SPREAD group-wise continuity scoring.

    Lower and upper groups are scored separately so SPREAD does not collapse
    back into a single all-notes total-motion heuristic. Smaller penalties are
    better. This owner is notes-only and never changes runtime expression,
    pedal, pattern, gesture, or MIDI behavior.
    """

    lower_group_motion: float = 1.25
    upper_group_motion: float = 1.0
    top_voice_motion: float = 0.9
    group_gap_stability: float = 0.55
    span_penalty: float = 0.35
    register_penalty: float = 0.4
    legality_penalty: float = 10000.0
    runtime_enabled: bool = False

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "groupwise_spread_voice_leading_version": GROUPWISE_SPREAD_VOICE_LEADING_VERSION,
            "spread_groupwise_voice_leading_split_version": SPREAD_GROUPWISE_VOICE_LEADING_SPLIT_VERSION,
            "implementation_owner": "core.voicing.disposition.spread_voice_leading",
            "lower_group_motion": float(self.lower_group_motion),
            "upper_group_motion": float(self.upper_group_motion),
            "top_voice_motion": float(self.top_voice_motion),
            "group_gap_stability": float(self.group_gap_stability),
            "span_penalty": float(self.span_penalty),
            "register_penalty": float(self.register_penalty),
            "legality_penalty": float(self.legality_penalty),
            "runtime_enabled": self.runtime_enabled,
            "notes_only": True,
            "no_expression_or_pedal": True,
        }


@dataclass(frozen=True)
class SpreadGroupwiseVoiceLeadingScore:
    """A component score for one current SPREAD candidate.

    The score preserves separate lower/upper/top/gap/span/register components so
    selectors can inspect why a candidate ranked well. Candidates are treated as
    notes-only projection objects and are not converted into runtime voicings in
    this layer.
    """

    current: Any
    previous: Any | None
    lower_group_motion: int
    upper_group_motion: int
    top_voice_motion: int
    group_gap_change: int
    span_penalty: int
    register_penalty: int
    legality_penalty: float
    weighted_penalty: float
    weights: SpreadGroupwiseVoiceLeadingWeights
    runtime_enabled: bool = False

    @property
    def total_motion(self) -> int:
        return int(self.lower_group_motion + self.upper_group_motion)

    @property
    def continuity_score(self) -> float:
        return max(0.0, 1000.0 - float(self.weighted_penalty))

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
            "basic_spread_projection_version": BASIC_SPREAD_PROJECTION_VERSION,
            "groupwise_spread_voice_leading_version": GROUPWISE_SPREAD_VOICE_LEADING_VERSION,
            "spread_groupwise_voice_leading_split_version": SPREAD_GROUPWISE_VOICE_LEADING_SPLIT_VERSION,
            "layer": "core.voicing.disposition.spread",
            "implementation_owner": "core.voicing.disposition.spread_voice_leading",
            "current_chord_symbol": self.current.chord_symbol,
            "previous_chord_symbol": self.previous.chord_symbol if self.previous is not None else None,
            "current_recipe_id": self.current.recipe_contract.recipe_id,
            "previous_recipe_id": self.previous.recipe_contract.recipe_id if self.previous is not None else None,
            "current_grouping": self.current.recipe_contract.grouping.value,
            "previous_grouping": self.previous.recipe_contract.grouping.value if self.previous is not None else None,
            "current_lower_group_notes": list(self.current.lower_notes),
            "previous_lower_group_notes": list(self.previous.lower_notes) if self.previous is not None else [],
            "current_upper_group_notes": list(self.current.upper_notes),
            "previous_upper_group_notes": list(self.previous.upper_notes) if self.previous is not None else [],
            "current_top_voice": max(self.current.notes) if self.current.notes else None,
            "previous_top_voice": max(self.previous.notes) if self.previous is not None and self.previous.notes else None,
            "lower_group_motion": int(self.lower_group_motion),
            "upper_group_motion": int(self.upper_group_motion),
            "top_voice_motion": int(self.top_voice_motion),
            "group_gap_change": int(self.group_gap_change),
            "span_penalty": int(self.span_penalty),
            "register_penalty": int(self.register_penalty),
            "legality_penalty": float(self.legality_penalty),
            "total_motion": self.total_motion,
            "weighted_penalty": float(self.weighted_penalty),
            "continuity_score": float(self.continuity_score),
            "weights": self.weights.to_debug_dict(),
            "scored_groupwise_not_total_motion_only": True,
            "runtime_enabled": self.runtime_enabled,
            "notes_only": True,
            "no_expression_or_pedal": True,
        }


def lower_group_motion_distance(previous: Any | None, current: Any) -> int:
    """Return set-based lower/foundation group motion distance."""

    return _paired_note_motion(previous.lower_notes if previous is not None else (), current.lower_notes)


def upper_group_motion_distance(previous: Any | None, current: Any) -> int:
    """Return set-based upper/projection group motion distance."""

    return _paired_note_motion(previous.upper_notes if previous is not None else (), current.upper_notes)


def top_voice_continuity_distance(previous: Any | None, current: Any) -> int:
    """Return absolute top-voice distance for SPREAD candidates."""

    return _top_voice_motion(previous, current)


def compute_groupwise_motion_score(
    current: Any,
    previous: Any | None = None,
    weights: SpreadGroupwiseVoiceLeadingWeights | None = None,
) -> SpreadGroupwiseVoiceLeadingScore:
    """Score one SPREAD candidate with lower/upper group-wise continuity."""

    scoring_weights = weights or SpreadGroupwiseVoiceLeadingWeights()
    lower_motion = lower_group_motion_distance(previous, current)
    upper_motion = upper_group_motion_distance(previous, current)
    top_motion = top_voice_continuity_distance(previous, current)
    gap_change = _group_gap_change(previous, current)
    span_penalty = _spread_span_penalty(current)
    register_penalty = _spread_register_penalty(current)
    legality_penalty = 0.0 if current.is_legal else float(scoring_weights.legality_penalty)
    weighted_penalty = (
        float(lower_motion) * float(scoring_weights.lower_group_motion)
        + float(upper_motion) * float(scoring_weights.upper_group_motion)
        + float(top_motion) * float(scoring_weights.top_voice_motion)
        + float(gap_change) * float(scoring_weights.group_gap_stability)
        + float(span_penalty) * float(scoring_weights.span_penalty)
        + float(register_penalty) * float(scoring_weights.register_penalty)
        + legality_penalty
    )
    return SpreadGroupwiseVoiceLeadingScore(
        current=current,
        previous=previous,
        lower_group_motion=int(lower_motion),
        upper_group_motion=int(upper_motion),
        top_voice_motion=int(top_motion),
        group_gap_change=int(gap_change),
        span_penalty=int(span_penalty),
        register_penalty=int(register_penalty),
        legality_penalty=float(legality_penalty),
        weighted_penalty=float(weighted_penalty),
        weights=scoring_weights,
    )


# Public compatibility name retained from v2_2_41.
score_spread_groupwise_voice_leading = compute_groupwise_motion_score


def rank_spread_candidates_by_group_motion(
    candidates: tuple[Any, ...] | list[Any],
    previous: Any | None = None,
    weights: SpreadGroupwiseVoiceLeadingWeights | None = None,
    *,
    legal_only: bool = True,
) -> tuple[SpreadGroupwiseVoiceLeadingScore, ...]:
    """Rank SPREAD projection candidates by group-wise voice-leading penalty."""

    usable = [candidate for candidate in candidates if (candidate.is_legal or not legal_only)]
    scores = [compute_groupwise_motion_score(candidate, previous, weights) for candidate in usable]
    scores.sort(
        key=lambda score: (
            float(score.weighted_penalty),
            score.lower_group_motion,
            score.upper_group_motion,
            score.top_voice_motion,
            score.current.group_gap_semitones if score.current.group_gap_semitones is not None else 999,
            score.current.notes,
        )
    )
    return tuple(scores)


# Public compatibility name retained from v2_2_41.
rank_spread_candidates_by_groupwise_voice_leading = rank_spread_candidates_by_group_motion


def select_spread_candidate_by_groupwise_voice_leading(
    candidates: tuple[Any, ...] | list[Any],
    previous: Any | None = None,
    weights: SpreadGroupwiseVoiceLeadingWeights | None = None,
    *,
    legal_only: bool = True,
) -> Any | None:
    """Return the best candidate from the notes-only group-wise scorer."""

    ranked = rank_spread_candidates_by_group_motion(candidates, previous, weights, legal_only=legal_only)
    return ranked[0].current if ranked else None


def spread_voice_leading_debug(scores: tuple[SpreadGroupwiseVoiceLeadingScore, ...]) -> dict[str, object]:
    """Return an owner-level debug payload for a scored SPREAD candidate list."""

    return {
        "groupwise_spread_voice_leading_version": GROUPWISE_SPREAD_VOICE_LEADING_VERSION,
        "spread_groupwise_voice_leading_split_version": SPREAD_GROUPWISE_VOICE_LEADING_SPLIT_VERSION,
        "implementation_owner": "core.voicing.disposition.spread_voice_leading",
        "ranked_score_count": len(scores),
        "scores": [score.to_debug_dict() for score in scores],
        "scored_groupwise_not_total_motion_only": True,
        "runtime_enabled": False,
        "notes_only": True,
        "no_expression_or_pedal": True,
    }


def spread_groupwise_voice_leading_path_debug(
    chord_symbols: tuple[str, ...] = ("Dm7", "G7", "Cmaj7"),
    *,
    contract_id: str = "spread_2plus3_contract",
    policy: Any | None = None,
    weights: SpreadGroupwiseVoiceLeadingWeights | None = None,
    max_upper_options: int = 12,
) -> dict[str, object]:
    """Greedy notes-only debug path for SPREAD group-wise voice-leading."""

    from .spread_projection_core import project_basic_spread_contract

    selected: list[Any] = []
    score_path: list[SpreadGroupwiseVoiceLeadingScore] = []
    previous: Any | None = None
    for symbol in chord_symbols:
        result = project_basic_spread_contract(symbol, contract_id, policy, max_upper_options=max_upper_options)
        ranked = rank_spread_candidates_by_group_motion(result.candidates, previous, weights)
        if not ranked:
            continue
        score = ranked[0]
        score_path.append(score)
        selected.append(score.current)
        previous = score.current
    return {
        "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
        "basic_spread_projection_version": BASIC_SPREAD_PROJECTION_VERSION,
        "groupwise_spread_voice_leading_version": GROUPWISE_SPREAD_VOICE_LEADING_VERSION,
        "spread_groupwise_voice_leading_split_version": SPREAD_GROUPWISE_VOICE_LEADING_SPLIT_VERSION,
        "layer": "core.voicing.disposition.spread",
        "implementation_owner": "core.voicing.disposition.spread_voice_leading",
        "purpose": "Group-wise SPREAD voice-leading scorer debug path",
        "contract_id": contract_id,
        "chord_symbols": list(chord_symbols),
        "selected_candidate_count": len(selected),
        "selected_lower_group_path": [list(candidate.lower_notes) for candidate in selected],
        "selected_upper_group_path": [list(candidate.upper_notes) for candidate in selected],
        "selected_top_voice_path": [max(candidate.notes) if candidate.notes else None for candidate in selected],
        "scores": [score.to_debug_dict() for score in score_path],
        "scored_groupwise_not_total_motion_only": True,
        "runtime_enabled": False,
        "notes_only": True,
        "no_expression_or_pedal": True,
    }



def spread_grouping_mix_contract_intent_cost(candidate: Any, policy: Any | None = None) -> float:
    """Return a small notes-only cost adjustment for selected 6-note SPREAD intent.

    The Ballad grouping-mix policy can select a 6-note contract while still
    allowing a compatible 5-note neighbor in the candidate pool for continuity.
    This owner-level helper gives the selected 6-note contract a gentle,
    metadata-controlled voice-leading bias so density intent is not completely
    erased by nearest-motion collapse. It does not create notes and never
    touches Pattern, Anticipation, Expression, Pedal, Gesture, or MIDI.
    """

    metadata = dict(getattr(candidate, "metadata", None) or {})
    decision = metadata.get("ballad_spread_grouping_mix_policy_decision") or {}
    if not isinstance(decision, dict):
        decision = {}
    selected = str(
        decision.get("selected_contract_id")
        or metadata.get("ballad_spread_grouping_mix_selected_contract_id")
        or ""
    )
    if selected not in {"spread_2plus4_contract", "spread_3plus3_contract"}:
        return 0.0
    recipe_id = str(metadata.get("recipe_id") or metadata.get("spread_recipe_id") or "")
    if not recipe_id:
        return 0.0

    policy_metadata = dict(getattr(policy, "metadata", None) or {})
    try:
        bias = float(policy_metadata.get("spread_grouping_mix_selected_6note_contract_bias", 0.0) or 0.0)
    except (TypeError, ValueError):
        bias = 0.0
    if bias <= 0.0:
        return 0.0

    if recipe_id == selected:
        return -bias
    if recipe_id == "spread_2plus3_contract":
        return bias * 0.25
    return 0.0


def spread_grouping_mix_contract_intent_debug(candidate: Any, policy: Any | None = None) -> dict[str, object]:
    """Return debug data for the selected-contract density intent adjustment."""

    metadata = dict(getattr(candidate, "metadata", None) or {})
    decision = metadata.get("ballad_spread_grouping_mix_policy_decision") or {}
    if not isinstance(decision, dict):
        decision = {}
    return {
        "spread_groupwise_voice_leading_split_version": SPREAD_GROUPWISE_VOICE_LEADING_SPLIT_VERSION,
        "implementation_owner": "core.voicing.disposition.spread_voice_leading",
        "selected_contract_id": decision.get("selected_contract_id"),
        "candidate_recipe_id": metadata.get("recipe_id") or metadata.get("spread_recipe_id"),
        "contract_intent_cost": spread_grouping_mix_contract_intent_cost(candidate, policy),
        "notes_only": True,
        "no_expression_or_pedal": True,
    }

def _paired_note_motion(previous_notes: tuple[int, ...] | list[int], current_notes: tuple[int, ...] | list[int]) -> int:
    previous_values = tuple(sorted(int(note) for note in previous_notes))
    current_values = tuple(sorted(int(note) for note in current_notes))
    if not previous_values:
        return 0
    if not current_values:
        return int(len(previous_values) * 3)
    from jammate_engine.core.voicing.selection.voice_leading import set_based_voice_leading_distance

    return int(round(set_based_voice_leading_distance(previous_values, current_values, birth_death_penalty=3.0).distance))


def _top_voice_motion(previous: Any | None, current: Any) -> int:
    if previous is None or not previous.notes or not current.notes:
        return 0
    return int(abs(max(previous.notes) - max(current.notes)))


def _group_gap_change(previous: Any | None, current: Any) -> int:
    if previous is None:
        return 0
    if previous.group_gap_semitones is None or current.group_gap_semitones is None:
        return 0
    return int(abs(int(previous.group_gap_semitones) - int(current.group_gap_semitones)))


def _spread_span_penalty(candidate: Any) -> int:
    max_span = int(candidate.register_policy.max_overall_span)
    return int(max(0, candidate.overall_span_semitones - max_span))


def _outside_register_distance(notes: tuple[int, ...], low: int, high: int) -> int:
    penalty = 0
    for note in notes:
        if int(note) < int(low):
            penalty += int(low) - int(note)
        elif int(note) > int(high):
            penalty += int(note) - int(high)
    return int(penalty)


def _spread_register_penalty(candidate: Any) -> int:
    policy = candidate.register_policy
    return int(
        _outside_register_distance(candidate.lower_notes, int(policy.lower_low), int(policy.lower_high))
        + _outside_register_distance(candidate.upper_notes, int(policy.upper_low), int(policy.upper_high))
    )
