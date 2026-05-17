from __future__ import annotations

import math
import random
from dataclasses import replace

from .candidate import VoicingCandidate
from ..policy import VoicingPolicy
from .scorer import score_candidate
from ..runtime.state import VoicingState
from .voice_leading import common_tone_count, set_based_voice_leading_distance, top_note, voice_leading_distance


def select_candidate(
    candidates: list[VoicingCandidate],
    *,
    policy: VoicingPolicy | None = None,
    state: VoicingState | None = None,
    rng: random.Random | None = None,
) -> VoicingCandidate:
    if not candidates:
        raise ValueError("No voicing candidates available")
    policy = policy or VoicingPolicy()
    state = state or VoicingState.empty()

    candidates = _collapse_to_per_source_nearest_closed_candidates(candidates, policy=policy, state=state)
    candidates = _collapse_rescue_candidates_to_nearest_motion(candidates, policy=policy, state=state)
    candidates = _collapse_spread_candidates_to_groupwise_nearest(candidates, policy=policy, state=state)
    candidates = _filter_register_continuity_candidates(candidates, policy=policy, state=state)

    scored: list[VoicingCandidate] = []
    for candidate in candidates:
        breakdown = score_candidate(candidate, policy, state)
        profile = dict(breakdown.details.get("voice_leading_profile", {}))
        scored.append(
            replace(
                candidate,
                score=breakdown.total,
                voice_leading_profile=profile,
                metadata={
                    **dict(candidate.metadata),
                    "score_breakdown": breakdown.to_metadata(),
                    "voice_leading_profile": profile,
                },
            )
        )
    scored.sort(key=lambda c: c.score, reverse=True)

    if rng is None or policy.selector_temperature <= 0:
        selected = scored[0]
        decision = _selector_decision_metadata(
            selected=selected,
            scored=scored,
            policy=policy,
            state=state,
            mode="deterministic_top_score",
            pool_size=1,
            weights=[1.0],
            selected_rank=1,
        )
        return replace(
            selected,
            selector_decision=decision,
            metadata={**dict(selected.metadata), "selector_decision": decision},
        )

    pool_size = max(1, min(policy.selection_pool_size, len(scored)))
    pool = scored[:pool_size]
    temperature = max(0.05, policy.selector_temperature)
    max_score = max(candidate.score for candidate in pool)
    weights = [math.exp((candidate.score - max_score) / temperature) for candidate in pool]
    total = sum(weights)
    if total <= 0:
        selected = pool[0]
        selected_rank = 1
    else:
        needle = rng.random() * total
        acc = 0.0
        selected = pool[-1]
        selected_rank = pool_size
        for index, (candidate, weight) in enumerate(zip(pool, weights), start=1):
            acc += weight
            if needle <= acc:
                selected = candidate
                selected_rank = index
                break

    decision = _selector_decision_metadata(
        selected=selected,
        scored=scored,
        policy=policy,
        state=state,
        mode="weighted_pool",
        pool_size=pool_size,
        weights=weights if total > 0 else [1.0] + [0.0] * (pool_size - 1),
        selected_rank=selected_rank,
    )
    return replace(
        selected,
        selector_decision=decision,
        metadata={**dict(selected.metadata), "selector_decision": decision},
    )



def _filter_register_continuity_candidates(
    candidates: list[VoicingCandidate],
    *,
    policy: VoicingPolicy,
    state: VoicingState,
) -> list[VoicingCandidate]:
    """Prefer candidates that do not leap out of the current register lane.

    The ordinary scorer already prices register and voice-leading.  v2_3_3 adds
    this small pre-score filter for the specific listening regression where a
    legal candidate pool contained both warm nearby choices and far high/low
    choices, yet source priors could still pick the high/low option.  It is soft:
    if no candidate survives, the full pool is retained.
    """

    if not candidates or not state.has_previous:
        return candidates
    metadata = dict(policy.metadata or {})
    enabled = _coerce_bool(
        metadata.get("voicing_register_continuity_guard_enabled")
        or metadata.get("register_continuity_guard_enabled"),
        default=False,
    )
    if not enabled or state.previous_top_note is None:
        return candidates

    top_limit = float(metadata.get("voicing_register_top_motion_filter_limit", metadata.get("voicing_register_top_motion_soft_limit", 4.0)) or 4.0)
    avg_limit = float(metadata.get("voicing_register_average_motion_filter_limit", metadata.get("voicing_register_average_motion_soft_limit", 3.5)) or 3.5)
    hard_top = float(metadata.get("voicing_register_top_hard_high", policy.register_high) or policy.register_high)
    prev_avg = sum(state.previous_notes) / len(state.previous_notes) if state.previous_notes else None
    strict: list[VoicingCandidate] = []
    relaxed: list[VoicingCandidate] = []
    for candidate in candidates:
        notes = tuple(sorted(int(note) for note in candidate.notes))
        if not notes:
            continue
        current_top = top_note(notes)
        if current_top is None:
            continue
        top_motion = abs(float(current_top) - float(state.previous_top_note))
        avg = sum(notes) / len(notes)
        avg_motion = abs(avg - prev_avg) if prev_avg is not None else 0.0
        if current_top <= hard_top and top_motion <= top_limit and avg_motion <= avg_limit + 1.0:
            strict.append(candidate)
        elif current_top <= hard_top and top_motion <= top_limit + 2.0:
            relaxed.append(candidate)
    chosen = strict or relaxed
    if not chosen:
        return candidates
    return [
        replace(
            candidate,
            metadata={
                **dict(candidate.metadata),
                "voicing_register_continuity_filter_version": "v2_3_3",
                "voicing_register_continuity_filter_applied": True,
                "voicing_register_continuity_filter_original_count": len(candidates),
                "voicing_register_continuity_filter_kept_count": len(chosen),
                "voicing_register_continuity_filter_top_motion_limit": top_limit,
                "voicing_register_continuity_filter_average_motion_limit": avg_limit,
            },
        )
        for candidate in chosen
    ]


def _collapse_to_per_source_nearest_closed_candidates(
    candidates: list[VoicingCandidate],
    *,
    policy: VoicingPolicy,
    state: VoicingState,
) -> list[VoicingCandidate]:
    """Collapse strict closed candidates to one nearest realization per source.

    Source/content planning decides *what* harmonic material is available.  This
    pass decides *where* each source is placed before source-level weighted
    selection.  It currently applies only to strict closed 3-note / 4-note tuning
    modes so open, spread, drop2, and future 5/6-note behavior are not changed.
    """

    enabled_densities = _closed_minimum_motion_enabled_densities(policy)
    if not enabled_densities:
        return candidates

    eligible: dict[tuple[object, ...], list[VoicingCandidate]] = {}
    passthrough: list[VoicingCandidate] = []
    for candidate in candidates:
        density = int(candidate.density or 0)
        if density not in enabled_densities or not _is_minimum_motion_closed_candidate(candidate):
            passthrough.append(candidate)
            continue
        eligible.setdefault(_semantic_source_key(candidate), []).append(candidate)

    collapsed: list[VoicingCandidate] = []
    for source_key, group in eligible.items():
        best = min(group, key=lambda candidate: _source_realization_cost(candidate, policy=policy, state=state))
        density = int(best.density or 0)
        best_distance = voice_leading_distance(state.previous_notes, tuple(best.notes)) if state.has_previous else None
        best_total_motion = (best_distance * max(1, min(len(state.previous_notes), len(best.notes)))) if best_distance is not None else None
        best_top_motion = None
        if state.previous_top_note is not None and best.notes:
            best_top = top_note(best.notes)
            if best_top is not None:
                best_top_motion = best_top - state.previous_top_note
        prefix = f"closed_{density}note"
        collapsed.append(
            replace(
                best,
                metadata={
                    **dict(best.metadata),
                    "closed_per_source_minimum_motion": True,
                    "closed_per_source_minimum_motion_density": density,
                    f"{prefix}_per_source_minimum_motion": True,
                    f"{prefix}_source_collapse_candidate_count": len(group),
                    f"{prefix}_source_collapse_key": list(source_key),
                    f"{prefix}_source_collapse_has_previous": bool(state.has_previous),
                    f"{prefix}_source_collapse_selected_distance": round(best_distance, 3) if best_distance is not None else None,
                    f"{prefix}_source_collapse_selected_total_motion": round(best_total_motion, 3) if best_total_motion is not None else None,
                    f"{prefix}_source_collapse_selected_top_motion": best_top_motion,
                },
            )
        )

    return passthrough + collapsed


def _collapse_rescue_candidates_to_nearest_motion(
    candidates: list[VoicingCandidate],
    *,
    policy: VoicingPolicy,
    state: VoicingState,
) -> list[VoicingCandidate]:
    """Collapse explicit rescue pools to the nearest legal realization.

    Rescue should not mean "pick any legal fallback."  When a strict method lock
    or texture-family runtime path has already had to break its preferred
    projection language, the safest musical behavior is to keep the fallback as
    close as possible to the previous voicing.  This reuses the existing
    source-realization continuity cost instead of introducing a parallel
    voice-leading engine.
    """

    if not candidates or not _rescue_nearest_motion_enabled(candidates, policy):
        return candidates

    rescue_candidates = [candidate for candidate in candidates if _is_rescue_candidate(candidate)]
    if not rescue_candidates:
        return candidates

    if not state.has_previous:
        return [
            replace(
                candidate,
                metadata={
                    **dict(candidate.metadata),
                    "texture_state_rescue_nearest_motion_contract": "v2_2_29",
                    "texture_state_rescue_nearest_motion_applied": False,
                    "texture_state_rescue_nearest_motion_reason": "no_previous_voicing_state",
                    "texture_state_rescue_nearest_motion_candidate_count": len(rescue_candidates),
                },
            )
            for candidate in candidates
        ]

    best = min(rescue_candidates, key=lambda candidate: _source_realization_cost(candidate, policy=policy, state=state))
    best_notes = tuple(sorted(int(note) for note in best.notes))
    best_distance = voice_leading_distance(state.previous_notes, best_notes)
    best_total_motion = best_distance * max(1, min(len(state.previous_notes), len(best_notes)))
    best_top = top_note(best_notes)
    best_top_motion = None
    if best_top is not None and state.previous_top_note is not None:
        best_top_motion = best_top - state.previous_top_note

    passthrough = [candidate for candidate in candidates if not _is_rescue_candidate(candidate)]
    annotated_best = replace(
        best,
        metadata={
            **dict(best.metadata),
            "texture_state_rescue_nearest_motion_contract": "v2_2_29",
            "texture_state_rescue_nearest_motion_applied": True,
            "texture_state_rescue_nearest_motion_reason": "explicit_rescue_pool_collapsed_to_nearest_previous_voicing",
            "texture_state_rescue_nearest_motion_candidate_count": len(rescue_candidates),
            "texture_state_rescue_nearest_motion_selected_distance": round(best_distance, 3),
            "texture_state_rescue_nearest_motion_selected_total_motion": round(best_total_motion, 3),
            "texture_state_rescue_nearest_motion_selected_top_motion": best_top_motion,
            "texture_state_rescue_nearest_motion_previous_notes": list(state.previous_notes),
        },
    )
    return passthrough + [annotated_best]



def _collapse_spread_candidates_to_groupwise_nearest(
    candidates: list[VoicingCandidate],
    *,
    policy: VoicingPolicy,
    state: VoicingState,
) -> list[VoicingCandidate]:
    """Collapse explicit SPREAD pilot candidates by lower/upper continuity.

    SPREAD groupings should not be voiced by treating all notes as one undivided
    stack.  When an isolation policy opts in, compare lower/foundation notes and
    upper/projection notes separately, then keep the closest SPREAD realization
    for the normal selector.  Default style paths are unchanged because the pass
    is gated by policy metadata.
    """

    metadata = dict(policy.metadata or {})
    if not _coerce_bool(metadata.get("spread_groupwise_voice_leading_runtime_enabled"), default=False):
        return candidates

    eligible = [candidate for candidate in candidates if _is_spread_groupwise_candidate(candidate)]
    if len(eligible) <= 1:
        return candidates

    passthrough = [candidate for candidate in candidates if candidate not in eligible]
    best = min(eligible, key=lambda candidate: _spread_groupwise_realization_cost(candidate, policy=policy, state=state))
    cost = _spread_groupwise_realization_cost(best, policy=policy, state=state)
    annotated = replace(
        best,
        metadata={
            **dict(best.metadata),
            "spread_groupwise_voice_leading_runtime_version": "v2_2_68",
            "spread_groupwise_whole_voicing_scorer_version": "v2_2_68",
            "spread_groupwise_voice_leading_runtime_applied": True,
            "spread_groupwise_voice_leading_candidate_count": len(eligible),
            "spread_groupwise_voice_leading_selected_cost": [round(float(value), 3) for value in cost[:4]],
            "spread_groupwise_voice_leading_selected_notes": list(cost[4]) if len(cost) > 4 else list(best.notes),
            "spread_groupwise_voice_leading_previous_lower_group_notes": list(_previous_group_notes(state, "lower")),
            "spread_groupwise_voice_leading_previous_upper_group_notes": list(_previous_group_notes(state, "upper")),
            "spread_set_based_voice_leading_version": "v2_2_81",
            "spread_set_based_voice_leading_runtime_applied": True,
            "spread_top_voice_continuity_version": "v2_2_84",
            "spread_top_voice_continuity_runtime_applied": True,
            "spread_top_voice_continuity_profile": _spread_top_voice_continuity_profile(best, policy=policy, state=state),
            "spread_lower_assignment_profile": _group_assignment_profile(_previous_group_notes(state, "lower"), tuple(sorted(int(note) for note in dict(best.metadata or {}).get("lower_group_notes") or ()))),
            "spread_upper_assignment_profile": _group_assignment_profile(_previous_group_notes(state, "upper"), tuple(sorted(int(note) for note in dict(best.metadata or {}).get("upper_group_notes") or ()))),
            "spread_upper_assignment_handles_unequal_note_counts": True,
        },
    )
    return passthrough + [annotated]


def _is_spread_groupwise_candidate(candidate: VoicingCandidate) -> bool:
    metadata = dict(candidate.metadata or {})
    return (
        getattr(candidate.disposition, "value", str(candidate.disposition)) == "spread"
        and bool(metadata.get("lower_group_notes"))
        and bool(metadata.get("upper_group_notes"))
    )


def _spread_groupwise_realization_cost(
    candidate: VoicingCandidate,
    *,
    policy: VoicingPolicy,
    state: VoicingState,
) -> tuple[float, float, float, float, tuple[int, ...]]:
    metadata = dict(candidate.metadata or {})
    lower = tuple(sorted(int(note) for note in metadata.get("lower_group_notes") or ()))
    upper = tuple(sorted(int(note) for note in metadata.get("upper_group_notes") or ()))
    previous_lower = _previous_group_notes(state, "lower")
    previous_upper = _previous_group_notes(state, "upper")

    if previous_lower or previous_upper:
        lower_motion = _paired_group_motion(previous_lower, lower)
        upper_motion = _paired_group_motion(previous_upper, upper)
        top_profile = _spread_top_voice_continuity_profile(candidate, policy=policy, state=state)
        top_continuity_cost = float(top_profile["cost"])
        gap_change = 0.0
        previous_gap = _previous_group_gap(state)
        current_gap = metadata.get("group_gap_semitones")
        if previous_gap is not None and current_gap is not None:
            gap_change = abs(float(current_gap) - float(previous_gap))
        recipe_change_cost = _spread_lower_recipe_change_cost(state, candidate, policy)
        current_gap_cost = _spread_current_group_gap_cost(candidate, policy)
        whole_cost = _spread_whole_voicing_cost(candidate, policy)
        top_weight = float(dict(policy.metadata or {}).get("spread_top_voice_continuity_weight", 2.2) or 2.2)
        primary = (
            lower_motion * 1.05
            + upper_motion * 0.85
            + top_continuity_cost * top_weight
            + recipe_change_cost
            + current_gap_cost
        )
        # v2_2_82: full top-line continuity is an explicit sort key.  It is
        # deliberately independent of lower/upper note count, so 3-note ↔
        # 4-note upper transitions can keep a smooth audible soprano line.
        return (primary, top_continuity_cost, gap_change * 0.25, whole_cost, tuple(candidate.notes))

    return (_spread_whole_voicing_cost(candidate, policy), _spread_span_cost(candidate), -float(candidate.score), 0.0, tuple(candidate.notes))


def _previous_group_notes(state: VoicingState, group: str) -> tuple[int, ...]:
    metadata = dict(state.metadata or {})
    key = "lower_group_notes" if group == "lower" else "upper_group_notes"
    return tuple(sorted(int(note) for note in metadata.get(key) or ()))


def _previous_group_gap(state: VoicingState) -> float | None:
    metadata = dict(state.metadata or {})
    value = metadata.get("group_gap_semitones")
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _paired_group_motion(previous_notes: tuple[int, ...], current_notes: tuple[int, ...]) -> float:
    if not previous_notes or not current_notes:
        return 0.0
    return float(set_based_voice_leading_distance(previous_notes, current_notes, birth_death_penalty=3.0).distance)


def _group_assignment_profile(previous_notes: tuple[int, ...], current_notes: tuple[int, ...]) -> dict[str, object]:
    if not previous_notes and not current_notes:
        return {"distance": 0.0, "handles_unequal_note_counts": True, "does_not_zip_by_index": True}
    return set_based_voice_leading_distance(previous_notes, current_notes, birth_death_penalty=3.0).to_debug_dict()


def _spread_top_voice_continuity_profile(
    candidate: VoicingCandidate,
    *,
    policy: VoicingPolicy,
    state: VoicingState,
) -> dict[str, object]:
    """Return a Ballad SPREAD top-line continuity profile.

    For mixed SPREAD groupings, upper note counts can change between events
    (3-note upper ↔ 4-note upper).  The highest sounding pitch remains a stable
    musical anchor across those density changes, so score it directly instead
    of relying on index-aligned note motion.
    """

    current_top = top_note(tuple(int(note) for note in candidate.notes))
    previous_top = state.previous_top_note
    motion = None if current_top is None or previous_top is None else int(current_top) - int(previous_top)
    abs_motion = abs(motion) if motion is not None else None
    thresholds = dict(policy.metadata or {})
    close_limit = int(thresholds.get("spread_top_voice_close_motion", 2) or 2)
    acceptable_limit = int(thresholds.get("spread_top_voice_acceptable_motion", 5) or 5)
    soft_limit = int(thresholds.get("spread_top_voice_soft_limit", 7) or 7)
    large_limit = int(thresholds.get("spread_top_voice_large_jump", 12) or 12)
    if abs_motion is None:
        cost = 0.0
        label = "no_previous_top"
    elif abs_motion <= close_limit:
        cost = 0.0
        label = "close"
    elif abs_motion <= acceptable_limit:
        cost = (abs_motion - close_limit) * 0.25
        label = "acceptable"
    elif abs_motion <= soft_limit:
        cost = 0.75 + (abs_motion - acceptable_limit) * 0.75
        label = "moderate"
    elif abs_motion <= large_limit:
        cost = 2.25 + (abs_motion - soft_limit) * 1.35
        label = "large"
    else:
        cost = 9.0 + (abs_motion - large_limit) * 3.5
        label = "extreme"
    return {
        "version": "v2_2_84",
        "previous_top_voice": previous_top,
        "current_top_voice": current_top,
        "top_voice_motion": motion,
        "top_voice_abs_motion": abs_motion,
        "cost": round(float(cost), 3),
        "label": label,
        "thresholds": {
            "close": close_limit,
            "acceptable": acceptable_limit,
            "soft": soft_limit,
            "large": large_limit,
        },
    }


def _spread_current_group_gap_cost(candidate: VoicingCandidate, policy: VoicingPolicy) -> float:
    metadata = dict(candidate.metadata or {})
    try:
        group_gap = float(metadata.get("group_gap_semitones"))
    except (TypeError, ValueError):
        return 0.0
    policy_metadata = dict(policy.metadata or {})
    comfort_gap = float(policy_metadata.get("spread_comfort_group_gap_max", 12) or 12)
    target_gap = float(policy_metadata.get("spread_target_group_gap", 7) or 7)
    penalty = abs(group_gap - target_gap) * float(policy_metadata.get("spread_group_gap_target_penalty", 0.08) or 0.08)
    if group_gap > comfort_gap:
        penalty += (group_gap - comfort_gap) * float(policy_metadata.get("spread_large_group_gap_penalty", 6.0) or 6.0)
    return float(penalty)

def _spread_lower_recipe_change_cost(state: VoicingState, candidate: VoicingCandidate, policy: VoicingPolicy) -> float:
    metadata = dict(candidate.metadata or {})
    policy_metadata = dict(policy.metadata or {})
    if not _coerce_bool(policy_metadata.get("spread_lower_2note_foundation_lock_enabled"), default=False):
        return 0.0
    previous_recipe = dict(state.metadata or {}).get("lower_group_recipe_id")
    current_recipe = metadata.get("lower_group_recipe_id")
    if not previous_recipe or not current_recipe or previous_recipe == current_recipe:
        return 0.0
    # This is a soft continuity cost, not an inventory weight.  It keeps
    # root+3/root+5/root+7 equally available while discouraging event-level
    # identity flicker inside one rooted foundation texture.
    return float(policy_metadata.get("spread_lower_2note_recipe_change_penalty", 6.0) or 6.0)


def _spread_whole_voicing_cost(candidate: VoicingCandidate, policy: VoicingPolicy) -> float:
    metadata = dict(candidate.metadata or {})
    notes = tuple(sorted(int(note) for note in candidate.notes))
    if not notes:
        return 999.0
    cost = _spread_register_center_cost(candidate, policy)
    if _coerce_bool(metadata.get("rooted_bass_anchor_enabled"), default=False):
        root_note = metadata.get("root_bass_anchor_note")
        try:
            root_note_int = int(root_note)
        except (TypeError, ValueError):
            cost += 250.0
        else:
            if root_note_int != min(notes):
                cost += 250.0
            root_low = int(metadata.get("root_bass_anchor_low", min(notes)) or min(notes))
            root_high = int(metadata.get("root_bass_anchor_high", min(notes)) or min(notes))
            root_target = float(dict(policy.metadata or {}).get("spread_root_bass_anchor_target", (root_low + root_high) / 2.0) or ((root_low + root_high) / 2.0))
            if root_note_int < root_low or root_note_int > root_high:
                cost += 100.0 + abs(root_note_int - max(root_low, min(root_high, root_note_int)))
            cost += abs(root_note_int - root_target) * 0.08
    whole_low = int(metadata.get("whole_register_low", min(notes)) or min(notes))
    whole_high = int(metadata.get("whole_register_high", max(notes)) or max(notes))
    for note in notes:
        if note < whole_low:
            cost += (whole_low - note) * 5.0
        elif note > whole_high:
            cost += (note - whole_high) * 5.0
    span = max(notes) - min(notes)
    target_span = float(dict(policy.metadata or {}).get("spread_whole_register_target_span", 30) or 30)
    cost += abs(span - target_span) * 0.015

    # v2_2_81: SPREAD should not solve continuity by leaving a large empty
    # hole between foundation and projection groups.  Keep this as a soft
    # realization cost rather than a hard legality rule so thick/climax shapes
    # can still rescue when no closer legal candidate exists.
    try:
        group_gap = float(metadata.get("group_gap_semitones"))
    except (TypeError, ValueError):
        group_gap = None
    if group_gap is not None:
        policy_metadata = dict(policy.metadata or {})
        comfort_gap = float(policy_metadata.get("spread_comfort_group_gap_max", 12) or 12)
        target_gap = float(policy_metadata.get("spread_target_group_gap", 7) or 7)
        if group_gap > comfort_gap:
            cost += (group_gap - comfort_gap) * float(policy_metadata.get("spread_large_group_gap_penalty", 6.0) or 6.0)
        cost += abs(group_gap - target_gap) * float(policy_metadata.get("spread_group_gap_target_penalty", 0.08) or 0.08)
    return float(cost)


def _spread_register_center_cost(candidate: VoicingCandidate, policy: VoicingPolicy) -> float:
    metadata = dict(candidate.metadata or {})
    lower = [int(note) for note in metadata.get("lower_group_notes") or ()]
    upper = [int(note) for note in metadata.get("upper_group_notes") or ()]
    lower_center = float(metadata.get("spread_lower_2note_target_low", 40) or 40)
    upper_floor = float(metadata.get("upper_3note_min_note_floor", metadata.get("spread_upper_3note_min_note_floor", 53)) or 53)
    lower_cost = abs((sum(lower) / len(lower)) - (lower_center + 7.0)) * 0.05 if lower else 0.0
    upper_floor_cost = max(0.0, upper_floor - min(upper)) * 5.0 if upper else 99.0
    span = (max(candidate.notes) - min(candidate.notes)) if candidate.notes else 0
    return lower_cost + upper_floor_cost + span * 0.01


def _spread_span_cost(candidate: VoicingCandidate) -> float:
    notes = tuple(int(note) for note in candidate.notes)
    return float(max(notes) - min(notes)) if notes else 0.0

def _rescue_nearest_motion_enabled(candidates: list[VoicingCandidate], policy: VoicingPolicy) -> bool:
    metadata = dict(policy.metadata or {})
    if _coerce_bool(metadata.get("texture_state_rescue_nearest_motion_enabled"), default=False):
        return True
    return any(_is_rescue_candidate(candidate) for candidate in candidates)


def _is_rescue_candidate(candidate: VoicingCandidate) -> bool:
    metadata = dict(candidate.metadata or {})
    return bool(
        metadata.get("voicing_method_lock_rescue_runtime_executed")
        or metadata.get("voicing_texture_state_rescue_runtime_executed")
        or (metadata.get("fallback") and metadata.get("voicing_method_lock_rescue_needed"))
    )


def _coerce_bool(value, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on", "enabled"}:
        return True
    if text in {"0", "false", "no", "off", "disabled"}:
        return False
    return default


def _closed_minimum_motion_enabled_densities(policy: VoicingPolicy) -> set[int]:
    metadata = dict(policy.metadata or {})
    densities: set[int] = set()
    if metadata.get("closed_3note_per_source_minimum_motion", False):
        densities.add(3)
    if metadata.get("closed_4note_per_source_minimum_motion", False):
        densities.add(4)
    for value in metadata.get("closed_per_source_minimum_motion_densities", ()) or ():
        try:
            densities.add(int(value))
        except (TypeError, ValueError):
            continue
    return densities


def _is_minimum_motion_closed_candidate(candidate: VoicingCandidate) -> bool:
    return (
        getattr(candidate.disposition, "value", str(candidate.disposition)) == "closed"
        and bool(dict(candidate.metadata or {}).get("strict_closed_compact_pitch_class_layout", False))
    )


def _semantic_source_key(candidate: VoicingCandidate) -> tuple[object, ...]:
    metadata = dict(candidate.metadata or {})
    recipe = dict(metadata.get("content_recipe") or {})
    validity_notes = tuple(str(note) for note in recipe.get("validity_notes", ()) or ())

    source_markers = tuple(
        note
        for note in validity_notes
        if note.startswith((
            "three_note_functional_source_type_",
            "three_note_source_role_order_",
            "three_note_degree_role_order_",
            "three_note_source_component_",
            "rootless_ab_functional_source_type_",
            "rootless_ab_source_role_order_",
            "rootless_ab_inversion_index_",
            "rootless_ab_ab_pair_key_",
            "basic_4note_functional_content_type_",
            "basic_4note_source_role_order_",
            "basic_4note_inversion_index_",
            "rooted_color_4note_functional_content_type_",
            "rooted_color_4note_source_role_order_",
            "rooted_color_4note_inversion_index_",
            "triad_4note_functional_content_type_",
            "triad_4note_source_role_order_",
            "triad_4note_inversion_index_",
        ))
    )
    if source_markers:
        return (
            metadata.get("symbol"),
            getattr(candidate.content_family, "value", str(candidate.content_family or "")),
            candidate.recipe_id,
            source_markers,
        )
    return (
        metadata.get("symbol"),
        getattr(candidate.content_family, "value", str(candidate.content_family or "")),
        candidate.recipe_id,
        tuple(str(degree) for degree in recipe.get("degrees", ()) or ()),
    )



def _source_realization_cost(candidate: VoicingCandidate, *, policy: VoicingPolicy, state: VoicingState) -> tuple[float, float, float, float, float]:
    notes = tuple(sorted(int(note) for note in candidate.notes))
    span = float((max(notes) - min(notes)) if len(notes) > 1 else 0)
    avg = sum(notes) / len(notes) if notes else 0.0
    comfort_center = (policy.comfort_register_low + policy.comfort_register_high) / 2.0
    top = top_note(notes)
    top_center = (policy.top_voice_low + policy.top_voice_high) / 2.0
    top_center_cost = abs(float(top) - top_center) if top is not None else 99.0

    if state.has_previous:
        distance = voice_leading_distance(state.previous_notes, notes)
        total_motion = distance * max(1, min(len(state.previous_notes), len(notes)))
        top_motion = abs((top or 0) - state.previous_top_note) if top is not None and state.previous_top_note is not None else 99.0
        common_tone_bonus = -float(common_tone_count(state.previous_notes, notes)) * 0.35
        # Primary key is total voice motion.  Tie-breakers keep exact/common-tone
        # continuity, avoid unnecessary top leaps, and prefer compact/register-safe
        # shapes without overriding the minimum-motion decision.
        return (total_motion, common_tone_bonus, float(top_motion), span * 0.04, abs(avg - comfort_center) * 0.03 + top_center_cost * 0.01)

    # First voiced event has no previous state; choose the best centered compact
    # realization per source so the later source-level selector is not polluted by
    # multiple octave/register copies of the same source.
    return (abs(avg - comfort_center), top_center_cost * 0.25, span * 0.05, -float(candidate.score), 0.0)


def _selector_decision_metadata(
    *,
    selected: VoicingCandidate,
    scored: list[VoicingCandidate],
    policy: VoicingPolicy,
    state: VoicingState,
    mode: str,
    pool_size: int,
    weights: list[float],
    selected_rank: int,
) -> dict:
    pool = scored[: max(1, min(pool_size, len(scored)))]
    total_weight = sum(weights) or 1.0
    probabilities = [weight / total_weight for weight in weights]
    selected_key = _candidate_key(selected)
    return {
        "mode": mode,
        "candidate_count": len(scored),
        "pool_size": len(pool),
        "selected_rank": int(selected_rank),
        "selected_score": round(float(selected.score), 4),
        "top_score": round(float(scored[0].score), 4),
        "score_margin_from_top": round(float(scored[0].score - selected.score), 4),
        "selector_temperature": float(policy.selector_temperature),
        "selection_pool_size_policy": int(policy.selection_pool_size),
        "has_previous_state": bool(state.has_previous),
        "previous_event_id": state.previous_event_id,
        "selected_candidate_key": selected_key,
        "pool": [
            {
                "rank": index,
                "candidate_key": _candidate_key(candidate),
                "score": round(float(candidate.score), 4),
                "weight": round(float(weights[index - 1]), 6) if index - 1 < len(weights) else None,
                "probability": round(float(probabilities[index - 1]), 6) if index - 1 < len(probabilities) else None,
                "voice_leading_distance": (candidate.voice_leading_profile or {}).get("voice_leading_distance"),
                "top_voice_motion": (candidate.voice_leading_profile or {}).get("top_voice_motion"),
                "smoothness_label": (candidate.voice_leading_profile or {}).get("smoothness_label"),
            }
            for index, candidate in enumerate(pool, start=1)
        ],
    }


def _candidate_key(candidate: VoicingCandidate) -> dict:
    return {
        "notes": list(candidate.notes),
        "degrees": list(candidate.degrees),
        "content_family": candidate.content_family.value if candidate.content_family else None,
        "disposition": candidate.disposition.value,
        "recipe_id": candidate.recipe_id,
    }
