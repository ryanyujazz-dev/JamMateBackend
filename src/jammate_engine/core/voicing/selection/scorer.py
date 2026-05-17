from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import math

from .candidate import VoicingCandidate
from .constraints import evaluate_register_guard
from ..policy import VoicingPolicy
from ..runtime.state import VoicingState
from jammate_engine.core.harmony.chord_parser import parse_chord
from .voice_leading import analyze_voice_leading, average_pitch, top_note
from ..sources.source_balance import (
    altered_dominant_source_kind,
    score_altered_dominant_intensity_balance,
    score_source_balance,
    source_balance_key,
    source_gate_mode,
)


UPPER_STRUCTURE_REGISTER_REFINEMENT_VERSION = "v2_2_89"
REGISTER_CONTINUITY_RECOVERY_VERSION = "v2_3_3"


@dataclass(frozen=True)
class VoicingScoreBreakdown:
    base_score: float
    voice_leading: float = 0.0
    top_voice: float = 0.0
    register_guard: float = 0.0
    register_continuity: float = 0.0
    density: float = 0.0
    orientation: float = 0.0
    disposition_method: float = 0.0
    total: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict:
        return {
            "base_score": round(self.base_score, 4),
            "voice_leading": round(self.voice_leading, 4),
            "top_voice": round(self.top_voice, 4),
            "register_guard": round(self.register_guard, 4),
            "register_continuity": round(self.register_continuity, 4),
            "density": round(self.density, 4),
            "orientation": round(self.orientation, 4),
            "disposition_method": round(self.disposition_method, 4),
            "total": round(self.total, 4),
            "details": dict(self.details),
        }


def score_candidate(candidate: VoicingCandidate, policy: VoicingPolicy, state: VoicingState | None = None) -> VoicingScoreBreakdown:
    state = state or VoicingState.empty()
    notes = tuple(sorted(candidate.notes))
    profile = analyze_voice_leading(notes, state, max_top_voice_leap=policy.max_top_voice_leap)
    base = candidate.score
    voice_score = _score_voice_leading_from_profile(profile, policy)
    top_score = _score_top_voice_from_profile(profile, policy)
    register_result = evaluate_register_guard(notes, policy)
    register_score = _score_register(notes, policy)
    rootless_ab_register_score = _score_rootless_ab_register_center(candidate, policy)
    source_balance_score = score_source_balance(candidate, policy)
    altered_dominant_intensity_score = score_altered_dominant_intensity_balance(candidate, policy)
    upper_structure_register_score = _score_upper_structure_register_refinement(candidate, policy)
    register_continuity_score = _score_register_continuity_recovery(candidate, policy, state)
    register_continuity_profile = _register_continuity_recovery_profile(candidate, policy, state)
    chart_color_fidelity_score = _score_chart_color_fidelity(candidate)
    density_score = -abs(len(notes) - policy.preferred_density) * 0.08
    rootless_ab_inversion_prior_score = _score_rootless_ab_inversion_prior(candidate, policy)
    basic_4note_rotation_prior_score = _score_basic_4note_rotation_prior(candidate, policy)
    orientation_score = (
        _score_rootless_ab_content_type_continuity(candidate, state)
        + rootless_ab_inversion_prior_score
        + basic_4note_rotation_prior_score
    )
    disposition_method_score = _score_disposition_method_weight(candidate, policy)
    total = (
        base
        + voice_score
        + top_score
        + register_score
        + rootless_ab_register_score
        + source_balance_score
        + upper_structure_register_score
        + register_continuity_score
        + chart_color_fidelity_score
        + density_score
        + orientation_score
        + disposition_method_score
    )
    profile_debug = profile.to_debug_dict()
    return VoicingScoreBreakdown(
        base_score=base,
        voice_leading=voice_score,
        top_voice=top_score,
        register_guard=register_score,
        register_continuity=register_continuity_score,
        density=density_score,
        orientation=orientation_score,
        disposition_method=disposition_method_score,
        total=total,
        details={
            "top_note": top_note(notes),
            "average_pitch": round(average_pitch(notes), 3) if notes else None,
            # Backward-compatible top-level fields from earlier score details.
            "voice_leading_distance": profile_debug["voice_leading_distance"],
            "top_voice_motion": profile_debug["top_voice_motion"],
            # v2_0_37 inspectable stateful voice-leading contract.
            "voice_leading_profile": profile_debug,
            "smoothness_label": profile.smoothness_label,
            "common_tones": profile.common_tones,
            "top_voice_repeated_recent_count": profile.top_voice_repeated_recent_count,
            "top_voice_leap_exceeds_max": profile.top_voice_leap_exceeds_max,
            "register_guard_passed": register_result.passed,
            "register_guard_reasons": list(register_result.reasons),
            "span": register_result.span,
            "muddy_low_interval_ok": register_result.muddy_low_interval_ok,
            "low_register_single_note_guard_version": register_result.to_debug_dict().get("low_register_single_note_guard_version"),
            "low_register_single_note_threshold": register_result.low_register_single_note_threshold,
            "low_register_single_note_count": register_result.low_register_single_note_count,
            "low_register_single_note_ok": register_result.low_register_single_note_ok,
            "rootless_ab_content_type": candidate.metadata.get("rootless_ab_content_type"),
            "rootless_ab_orientation_family": candidate.metadata.get("rootless_ab_orientation_family"),
            "rootless_ab_inversion_index": candidate.metadata.get("rootless_ab_inversion_index"),
            "rootless_ab_degree_order": candidate.metadata.get("rootless_ab_degree_order"),
            "rootless_ab_inversion_weight": candidate.metadata.get("rootless_ab_inversion_weight"),
            "rootless_ab_preferred_source_rotation": candidate.metadata.get("rootless_ab_preferred_source_rotation"),
            "rootless_ab_inversion_prior_score": round(rootless_ab_inversion_prior_score, 4),
            "rootless_ab_register_center_score": round(rootless_ab_register_score, 4),
            "rootless_ab_content_type_continuity_score": round(orientation_score - basic_4note_rotation_prior_score, 4),
            "source_balance_score": round(source_balance_score, 4),
            "altered_dominant_intensity_score": round(altered_dominant_intensity_score, 4),
            "altered_dominant_source_kind": altered_dominant_source_kind(candidate),
            "upper_structure_register_refinement_version": UPPER_STRUCTURE_REGISTER_REFINEMENT_VERSION if _is_upper_structure_candidate(candidate) else None,
            "upper_structure_register_score": round(upper_structure_register_score, 4),
            "upper_structure_top_note_soft_high": _upper_structure_top_soft_high(policy) if _is_upper_structure_candidate(candidate) else None,
            "voicing_register_continuity_recovery_version": REGISTER_CONTINUITY_RECOVERY_VERSION if register_continuity_profile.get("enabled") else None,
            "voicing_register_continuity_score": round(register_continuity_score, 4),
            "voicing_register_continuity_profile": register_continuity_profile,
            "source_balance_key": source_balance_key(candidate),
            "source_balance_gate_mode": source_gate_mode(candidate),
            "four_note_source_balance_score": round(source_balance_score, 4) if int(candidate.density or 0) == 4 else 0.0,
            "four_note_source_balance_key": source_balance_key(candidate) if int(candidate.density or 0) == 4 else "",
            "four_note_source_balance_gate_mode": source_gate_mode(candidate) if int(candidate.density or 0) == 4 else "",
            "three_note_source_balance_score": round(source_balance_score, 4) if int(candidate.density or 0) == 3 else 0.0,
            "three_note_source_balance_key": source_balance_key(candidate) if int(candidate.density or 0) == 3 else "",
            "three_note_source_balance_gate_mode": source_gate_mode(candidate) if int(candidate.density or 0) == 3 else "",
            "chart_color_fidelity_score": round(chart_color_fidelity_score, 4),
            "disposition_method_score": round(disposition_method_score, 4),
            "disposition_method_weight": candidate.metadata.get("disposition_method_weight"),
            "disposition_method_weight_scoring_enabled": candidate.metadata.get("disposition_method_weight_scoring_enabled"),
            "disposition_projection_family": candidate.metadata.get("disposition_projection_family"),
            "disposition_projection_method": candidate.metadata.get("disposition_projection_method"),
            "active_open_projection_method": candidate.metadata.get("active_open_projection_method"),
            "basic_4note_content_type": candidate.metadata.get("basic_4note_content_type"),
            "basic_4note_inversion_index": candidate.metadata.get("basic_4note_inversion_index"),
            "basic_4note_degree_order": candidate.metadata.get("basic_4note_degree_order"),
            "basic_4note_rotation_weight": candidate.metadata.get("basic_4note_rotation_weight"),
            "basic_4note_preferred_source_rotation": candidate.metadata.get("basic_4note_preferred_source_rotation"),
            "basic_4note_rotation_prior_score": round(basic_4note_rotation_prior_score, 4),
        },
    )



def _score_disposition_method_weight(candidate: VoicingCandidate, policy: VoicingPolicy) -> float:
    """Convert style disposition-method weights into a selector prior.

    v2_2_19 is the first runtime pilot that lets Medium Swing consume the
    disposition method weight contract.  The score is opt-in through candidate
    metadata so Bossa/Ballad and legacy default output remain stable until their
    own listening passes.  We use the same temperature-scaled log-prior pattern
    as source-rotation priors: weights influence otherwise comparable choices
    but do not override register guard, voice leading, chart fidelity, or rescue.
    """

    metadata = dict(candidate.metadata or {})
    if not bool(metadata.get("disposition_method_weight_scoring_enabled", False)):
        return 0.0
    try:
        raw_weight = float(metadata.get("disposition_method_weight", 1.0))
    except (TypeError, ValueError):
        return 0.0
    if raw_weight <= 0.0:
        method = str(metadata.get("active_open_projection_method") or metadata.get("disposition_projection_method") or "")
        is_explicit_rescue = bool(
            metadata.get("method_lock_rescue_runtime_attempt")
            or metadata.get("voicing_method_lock_rescue_runtime_executed")
            or metadata.get("method_lock_rescue_runtime_attempt_method")
        )
        if method == "generic_open" and not is_explicit_rescue:
            return -1000.0
        weight = 0.01
    else:
        weight = max(raw_weight, 0.01)
    temperature = max(float(policy.selector_temperature or 0.0), 0.20)
    return temperature * math.log(weight)


def _score_upper_structure_register_refinement(candidate: VoicingCandidate, policy: VoicingPolicy) -> float:
    """Soften Upper Structure register choices without creating a new selector.

    Upper Structure remains a source family that reuses existing closed/drop
    projection.  This v2_2_89 scorer bias only shapes otherwise comparable
    candidates so altered US color does not drift into a sharp top register or
    stack too much mass above a muddy low foundation.
    """

    if not _is_upper_structure_candidate(candidate):
        return 0.0
    metadata = dict(policy.metadata or {})
    if metadata.get("upper_structure_register_refinement_enabled") is False:
        return 0.0
    notes = tuple(sorted(int(note) for note in candidate.notes))
    if not notes:
        return -0.5
    top = max(notes)
    avg = average_pitch(notes)
    soft_high = _upper_structure_top_soft_high(policy)
    hard_high = int(metadata.get("upper_structure_top_hard_high", policy.top_voice_high))
    avg_soft_high = float(metadata.get("upper_structure_average_pitch_soft_high", policy.comfort_register_high))
    altered_multiplier = 1.25 if altered_dominant_source_kind(candidate) == "upper_structure" else 1.0
    score = 0.0
    if top <= soft_high and avg <= avg_soft_high:
        score += 0.06 * policy.register_guard_weight
    if top > soft_high:
        score -= (top - soft_high) * 0.08 * policy.register_guard_weight * altered_multiplier
    if top > hard_high:
        score -= (top - hard_high) * 0.16 * policy.register_guard_weight * altered_multiplier
    if avg > avg_soft_high:
        score -= (avg - avg_soft_high) * 0.05 * policy.register_guard_weight * altered_multiplier

    guard = dict(candidate.register_guard or candidate.metadata.get("register_guard", {}) or {})
    if guard.get("low_register_single_note_ok") is False:
        score -= 0.45 * policy.register_guard_weight
    if guard.get("muddy_low_interval_ok") is False:
        score -= 0.30 * policy.register_guard_weight
    return score


def _upper_structure_top_soft_high(policy: VoicingPolicy) -> int:
    metadata = dict(policy.metadata or {})
    return int(metadata.get("upper_structure_top_soft_high", min(int(policy.top_voice_high), 74)))


def _is_upper_structure_candidate(candidate: VoicingCandidate) -> bool:
    metadata = dict(candidate.metadata or {})
    notes = set(_candidate_validity_notes(candidate))
    notes.update(str(item) for item in metadata.get("source_metadata", []) or [])
    notes.update(str(item) for item in metadata.get("upper_source_metadata", []) or [])
    return "upper_structure_source_family" in notes or bool(metadata.get("upper_structure_source_enabled"))


def _candidate_validity_notes(candidate: VoicingCandidate) -> tuple[str, ...]:
    recipe = dict(dict(candidate.metadata or {}).get("content_recipe") or {})
    return tuple(str(note) for note in recipe.get("validity_notes", []) or ())




def _score_register_continuity_recovery(candidate: VoicingCandidate, policy: VoicingPolicy, state: VoicingState) -> float:
    """Softly keep selected voicings inside a stable phrase register band.

    v2_3_3 fixes a listening regression where individually smooth 4-note / SPREAD
    candidates could keep moving in the same direction until the whole texture
    became too high, then rescue back downward.  This remains a selector score,
    not a new voicing system: content, disposition, and projection are unchanged;
    the score only biases among already-legal candidates.
    """

    profile = _register_continuity_recovery_profile(candidate, policy, state)
    if not profile.get("enabled"):
        return 0.0
    return float(profile.get("score", 0.0) or 0.0)


def _register_continuity_recovery_profile(candidate: VoicingCandidate, policy: VoicingPolicy, state: VoicingState) -> dict[str, Any]:
    metadata = dict(policy.metadata or {})
    enabled = _coerce_bool(
        metadata.get("voicing_register_continuity_guard_enabled")
        or metadata.get("register_continuity_guard_enabled"),
        default=False,
    )
    notes = tuple(sorted(int(note) for note in candidate.notes))
    if not enabled or not notes:
        return {"enabled": False, "score": 0.0}

    avg = average_pitch(notes)
    top = top_note(notes)
    low = notes[0]
    center = float(metadata.get("voicing_register_center_target", (policy.comfort_register_low + policy.comfort_register_high) / 2.0) or ((policy.comfort_register_low + policy.comfort_register_high) / 2.0))
    tolerance = float(metadata.get("voicing_register_center_tolerance", 4.0) or 4.0)
    top_soft = float(metadata.get("voicing_register_top_soft_high", min(policy.top_voice_high, 74)) or min(policy.top_voice_high, 74))
    top_hard = float(metadata.get("voicing_register_top_hard_high", min(policy.register_high, policy.top_voice_high + 3)) or min(policy.register_high, policy.top_voice_high + 3))
    low_soft = float(metadata.get("voicing_register_low_soft_low", max(policy.register_low, 43)) or max(policy.register_low, 43))
    low_hard = float(metadata.get("voicing_register_low_hard_low", max(policy.register_low - 2, 38)) or max(policy.register_low - 2, 38))
    weight = float(metadata.get("voicing_register_continuity_weight", 1.0) or 1.0)
    score = 0.0
    reasons: list[str] = []

    high_excess = max(0.0, avg - (center + tolerance))
    low_excess = max(0.0, (center - tolerance) - avg)
    if high_excess:
        penalty = high_excess * 0.18 * weight
        score -= penalty
        reasons.append(f"average_above_center_band:{high_excess:.2f}")
    if low_excess:
        penalty = low_excess * 0.12 * weight
        score -= penalty
        reasons.append(f"average_below_center_band:{low_excess:.2f}")

    if top is not None and top > top_soft:
        excess = float(top) - top_soft
        penalty = excess * 0.28 * weight
        if top > top_hard:
            penalty += (float(top) - top_hard) * 0.48 * weight
        score -= penalty
        reasons.append(f"top_above_soft_high:{excess:.2f}")
    elif top is not None and top <= top_soft and center - tolerance <= avg <= center + tolerance:
        score += 0.08 * weight
        reasons.append("top_and_average_inside_recovery_band")

    if low < low_soft:
        excess = low_soft - float(low)
        penalty = excess * 0.08 * weight
        if low < low_hard:
            penalty += (low_hard - float(low)) * 0.25 * weight
        score -= penalty
        reasons.append(f"low_below_soft_low:{excess:.2f}")

    previous_avg = average_pitch(state.previous_notes) if state.has_previous else None
    avg_motion = avg - previous_avg if previous_avg is not None else None
    top_motion = (float(top) - float(state.previous_top_note)) if top is not None and state.previous_top_note is not None else None
    motion_limit = float(metadata.get("voicing_register_average_motion_soft_limit", 3.5) or 3.5)
    if avg_motion is not None:
        abs_avg_motion = abs(avg_motion)
        if abs_avg_motion > motion_limit:
            score -= (abs_avg_motion - motion_limit) * 0.20 * weight
            reasons.append(f"average_motion_above_limit:{avg_motion:.2f}")
        # Crucial drift brake: once the previous voicing is already above the
        # target center, do not keep rewarding another upward step merely because
        # it is locally smooth.  Symmetric lower-register brake prevents sudden
        # sagging after a high-register rescue.
        if previous_avg > center + tolerance and avg_motion > 0:
            score -= avg_motion * 0.34 * weight
            reasons.append(f"continued_upward_drift_above_center:{avg_motion:.2f}")
        if previous_avg < center - tolerance and avg_motion < 0:
            score -= abs(avg_motion) * 0.24 * weight
            reasons.append(f"continued_downward_drift_below_center:{avg_motion:.2f}")
    if top_motion is not None:
        top_motion_soft_limit = float(metadata.get("voicing_register_top_motion_soft_limit", 4.0) or 4.0)
        abs_top_motion = abs(float(top_motion))
        if abs_top_motion > top_motion_soft_limit:
            score -= (abs_top_motion - top_motion_soft_limit) * 0.40 * weight
            reasons.append(f"top_voice_motion_above_ballad_limit:{top_motion:.2f}")
        if state.previous_top_note is not None and state.previous_top_note >= top_soft - 1 and top_motion > 0:
            score -= top_motion * 0.42 * weight
            reasons.append(f"continued_top_voice_upward_drift_near_ceiling:{top_motion:.2f}")
        if top is not None and top > top_hard and top_motion >= 0:
            score -= max(1.0, top_motion) * 0.55 * weight
            reasons.append("top_voice_stays_above_hard_high")

    return {
        "enabled": True,
        "version": REGISTER_CONTINUITY_RECOVERY_VERSION,
        "score": round(float(score), 4),
        "average_pitch": round(float(avg), 3),
        "top_note": int(top) if top is not None else None,
        "low_note": int(low),
        "center_target": round(float(center), 3),
        "center_tolerance": round(float(tolerance), 3),
        "top_soft_high": round(float(top_soft), 3),
        "top_hard_high": round(float(top_hard), 3),
        "low_soft_low": round(float(low_soft), 3),
        "previous_average_pitch": round(float(previous_avg), 3) if previous_avg is not None else None,
        "average_motion": round(float(avg_motion), 3) if avg_motion is not None else None,
        "top_voice_motion": round(float(top_motion), 3) if top_motion is not None else None,
        "reasons": reasons,
    }


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

def _score_chart_color_fidelity(candidate: VoicingCandidate) -> float:
    """Prefer eligible 4-note sources that actually express chart-written color.

    This is intentionally independent from style source-family weights.  A Cmaj9
    or G13 symbol should make color-bearing candidates that contain the explicit
    color more likely, while still leaving conservative grounding candidates
    available at lower probability.  If harmonic expansion is also enabled,
    sources that add allowed style-safe colors but omit the written color are
    mildly downweighted instead of being forbidden.
    """

    if int(candidate.density or 0) != 4:
        return 0.0
    notes = [str(note) for note in dict(candidate.metadata or {}).get("content_recipe", {}).get("validity_notes", [])]
    score = 0.0
    if "chart_color_fidelity_contains_explicit_color" in notes:
        score += 0.32
    if "chart_color_fidelity_omits_explicit_color" in notes:
        score -= 0.18
    if "four_note_color_permission_blocked_unallowed_color" in notes:
        score -= 9.0
    return score


def _score_rootless_ab_register_center(candidate: VoicingCandidate, policy: VoicingPolicy) -> float:
    """Softly center compact rootless A/B voicings in the tuned piano band.

    v2_1_17 keeps the current compact-rootless texture from drifting into very
    high top notes or overly low/thick shapes.  This is deliberately a soft
    selector prior: the preset's absolute register guard supplies the hard band,
    while this score encourages the middle-register center that sounds most
    natural for 4-note A/B comping.
    """

    if candidate.metadata.get("rootless_ab_orientation_family") not in {"A", "B"}:
        return 0.0
    notes = tuple(sorted(int(note) for note in candidate.notes))
    if not notes:
        return 0.0

    metadata = dict(policy.metadata or {})
    avg_low = float(metadata.get("rootless_ab_average_pitch_target_low", policy.comfort_register_low))
    avg_high = float(metadata.get("rootless_ab_average_pitch_target_high", policy.comfort_register_high))
    top_soft_high = float(metadata.get("rootless_ab_top_voice_soft_high", policy.top_voice_high))
    top_hard_high = float(metadata.get("rootless_ab_top_voice_hard_high", policy.top_voice_high))
    lowest_floor = float(metadata.get("rootless_ab_lowest_note_floor", policy.register_low))

    avg = average_pitch(notes)
    top = top_note(notes)
    low = notes[0]
    score = 0.0

    if avg_low <= avg <= avg_high:
        score += 0.20 * policy.register_guard_weight
    elif avg < avg_low:
        score -= min((avg_low - avg) * 0.05, 0.50) * policy.register_guard_weight
    else:
        score -= min((avg - avg_high) * 0.10, 0.80) * policy.register_guard_weight

    if top is not None:
        if top <= top_soft_high:
            score += 0.10 * policy.register_guard_weight
        elif top <= top_hard_high:
            score -= (top - top_soft_high) * 0.08 * policy.register_guard_weight
        else:
            score -= (top - top_hard_high) * 0.20 * policy.register_guard_weight

    if low < lowest_floor:
        score -= (lowest_floor - low) * 0.08 * policy.register_guard_weight
    return score


def _score_rootless_ab_inversion_prior(candidate: VoicingCandidate, policy: VoicingPolicy) -> float:
    """Convert the 8:2 rootless A/B rotation prior into a selector score.

    The weighted selector uses exp(score / temperature).  By adding
    ``temperature * log(weight)`` we make otherwise equal candidates follow the
    requested 8:2 prior while still allowing voice-leading, register guard, and
    AB/ABA continuity to win when musically necessary.
    """

    weight = candidate.metadata.get("rootless_ab_inversion_weight")
    if weight is None:
        return 0.0
    try:
        weight_value = max(float(weight), 0.01)
    except (TypeError, ValueError):
        return 0.0
    temperature = max(float(policy.selector_temperature or 0.0), 0.20)
    return temperature * math.log(weight_value)


def _score_basic_4note_rotation_prior(candidate: VoicingCandidate, policy: VoicingPolicy) -> float:
    """Convert the 8:2 basic 1357 rotation prior into selector score.

    v2_1_19 gives conservative 1-3-5-7 the same source-rotation semantics as
    3579 rootless A/B.  Source-like rotations 1-3-5-7 and 5-7-1-3 are favored,
    but secondary rotations remain available for voice-leading/register rescue.
    """

    weight = candidate.metadata.get("basic_4note_rotation_weight")
    if weight is None:
        return 0.0
    try:
        weight_value = max(float(weight), 0.01)
    except (TypeError, ValueError):
        return 0.0
    temperature = max(float(policy.selector_temperature or 0.0), 0.20)
    return temperature * math.log(weight_value)


def _score_rootless_ab_content_type_continuity(candidate: VoicingCandidate, state: VoicingState) -> float:
    """Prefer AB/BAB rootless A/B movement in cycle-of-fourths motion.

    V2_1_15 upgrades the v2_1_12 content-type rule into the canonical-source
    inversion model.  Within one ii-V or V-I motion, the selector prefers:

    * same content type (with_5 stays with_5, with_13 stays with_13),
    * A/B orientation flip,
    * same canonical inversion index.

    Pairwise AB therefore makes a continuous ii-V-I read as ABA or BAB.  This is
    intentionally a strong preference rather than a hard lock so register guard
    and broader voice-leading can still rescue unusual cases.
    """

    if not _is_cycle_of_fourths_motion(state.previous_chord_symbol, candidate.metadata.get("symbol")):
        return 0.0

    score = 0.0
    current_type = candidate.metadata.get("rootless_ab_content_type")
    previous_type = state.metadata.get("rootless_ab_content_type")
    if current_type and previous_type:
        score += 0.72 if current_type == previous_type else -0.92

    current_orientation = candidate.metadata.get("rootless_ab_orientation_family")
    previous_orientation = state.metadata.get("rootless_ab_orientation_family")
    if current_orientation and previous_orientation:
        score += 0.62 if current_orientation != previous_orientation else -0.50

    current_inversion = candidate.metadata.get("rootless_ab_inversion_index")
    previous_inversion = state.metadata.get("rootless_ab_inversion_index")
    if current_inversion is not None and previous_inversion is not None:
        score += 0.46 if int(current_inversion) == int(previous_inversion) else -0.28

    return score


def _is_cycle_of_fourths_motion(previous_symbol: str | None, current_symbol: str | None) -> bool:
    if not previous_symbol or not current_symbol:
        return False
    try:
        previous = parse_chord(previous_symbol)
        current = parse_chord(current_symbol)
    except Exception:
        return False
    # D -> G and G -> C are +5 semitones modulo 12: ii-V and V-I root motion.
    return (current.root_pc - previous.root_pc) % 12 == 5


def _score_voice_leading_from_profile(profile, policy: VoicingPolicy) -> float:
    if not profile.has_previous or profile.voice_leading_distance is None:
        return 0.0
    distance = profile.voice_leading_distance
    # Close movement should win, but do not make the selector afraid of normal
    # harmonic motion. The penalty becomes noticeable only when average motion
    # gets jumpy.
    if distance <= 3.0:
        score = policy.voice_leading_weight * 0.5
    elif distance <= 6.0:
        score = policy.voice_leading_weight * 0.2
    else:
        score = -policy.voice_leading_weight * min((distance - 6.0) / 8.0, 1.4)

    # Common tones provide a tiny continuity hint. This is intentionally small
    # so the pass remains an inspectable selector refinement, not a broad
    # musical retune.
    if profile.common_tones:
        score += min(profile.common_tones, 2) * 0.05 * policy.voice_leading_weight
    return score


def _score_top_voice_from_profile(profile, policy: VoicingPolicy) -> float:
    current_top = profile.current_top_note
    if current_top is None:
        return -0.5
    score = 0.0
    if current_top < policy.top_voice_low:
        score -= (policy.top_voice_low - current_top) * 0.08 * policy.register_guard_weight
    elif current_top > policy.top_voice_high:
        score -= (current_top - policy.top_voice_high) * 0.1 * policy.register_guard_weight
    else:
        score += 0.18 * policy.register_guard_weight

    motion = profile.top_voice_motion
    smooth_common_tone_repeat = bool(
        motion == 0
        and profile.common_tones > 0
        and profile.voice_leading_distance is not None
        and profile.voice_leading_distance <= 2.0
    )
    if motion is not None:
        abs_motion = abs(motion)
        if 1 <= abs_motion <= 5:
            score += 0.45 * policy.top_voice_weight
        elif abs_motion == 0:
            # A repeated top note is normally static, but in 2-note guide-tone
            # shells it is often the correct common-tone voice-leading result
            # (e.g. Dm7 C-F -> G7 B-F).  Reward the smooth/common-tone case
            # instead of forcing an unnecessary top-line jump.
            score += (0.18 if smooth_common_tone_repeat else -0.2) * policy.top_voice_weight
        elif abs_motion > policy.max_top_voice_leap:
            score -= min((abs_motion - policy.max_top_voice_leap) / 5.0, 1.8) * policy.top_voice_weight
    if not smooth_common_tone_repeat:
        smooth_common_tone_motion = bool(
            profile.common_tones > 0
            and profile.voice_leading_distance is not None
            and profile.voice_leading_distance <= 2.0
        )
        repeat_penalty = 0.05 if smooth_common_tone_motion else 0.35
        score -= float(profile.top_voice_repeated_recent_count) * repeat_penalty * policy.top_voice_weight
    return score


def _score_register(notes: tuple[int, ...], policy: VoicingPolicy) -> float:
    if not notes:
        return -2.0
    score = 0.0
    avg = average_pitch(notes)
    if avg < policy.comfort_register_low:
        score -= (policy.comfort_register_low - avg) * 0.06 * policy.register_guard_weight
    elif avg > policy.comfort_register_high:
        score -= (avg - policy.comfort_register_high) * 0.08 * policy.register_guard_weight
    else:
        score += 0.15 * policy.register_guard_weight

    span = max(notes) - min(notes) if len(notes) > 1 else 0
    if span > policy.max_voicing_span:
        score -= (span - policy.max_voicing_span) * 0.05 * policy.register_guard_weight
    return score
