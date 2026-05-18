from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .placement_utils import PlacedDegree
from .spread_lower_groups import LowerGroupPlacement, LowerGroupRecipeId


BASIC_SPREAD_PROJECTION_VERSION = "v2_2_40"
UPPER_STRUCTURE_SPREAD_PILOT_VERSION = "v2_2_84"
LOW_REGISTER_DENSITY_GUARD_VERSION = "v2_2_84"
SPREAD_REGISTER_GUARD_SPLIT_VERSION = "v2_6_8"


@dataclass(frozen=True)
class SpreadProjectionRegisterPolicy:
    """Register/gap/span guard used by SPREAD lower/upper projection.

    This module owns only register legality: lower/upper windows, group gap,
    total span, low-register density, and rooted-bass-anchor guard behavior.
    It must not choose content, style patterns, expression, pedal, or MIDI.
    """

    lower_low: int = 36
    lower_high: int = 60
    lower_2note_low: int = 40  # E2
    lower_2note_high: int = 52  # E3
    lower_2note_target_low: int = 40  # E2
    lower_2note_min_top: int = 40  # E2
    lower_2note_foundation_mode: str = "rooted"
    rooted_bass_anchor_enabled: bool = False
    root_bass_anchor_low: int = 36  # C2
    root_bass_anchor_high: int = 48  # C3
    root_bass_anchor_target: int = 39  # Eb2-ish for ballad anchor demos
    root_bass_anchor_high_tail_semitones: int = 4
    root_bass_anchor_high_tail_max_lower_span: int = 12
    whole_register_low: int = 36
    whole_register_high: int = 84
    upper_low: int = 48
    upper_high: int = 84
    lower_target_low: int = 36
    lower_1note_target_low: int = 36
    upper_target_low: int = 60
    min_group_gap: int = 5
    max_group_gap: int = 28
    max_overall_span: int = 48
    low_register_density_guard_enabled: bool = False
    upper_structure_lower_gate_enabled: bool = False
    low_register_density_threshold: int = 40  # E2
    low_register_density_max_notes_below: int = 1
    runtime_enabled: bool = False

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "basic_spread_projection_version": BASIC_SPREAD_PROJECTION_VERSION,
            "spread_register_guard_split_version": SPREAD_REGISTER_GUARD_SPLIT_VERSION,
            "lower_low": int(self.lower_low),
            "lower_high": int(self.lower_high),
            "upper_low": int(self.upper_low),
            "upper_high": int(self.upper_high),
            "lower_target_low": int(self.lower_target_low),
            "lower_1note_target_low": int(self.lower_1note_target_low),
            "lower_2note_low": int(self.lower_2note_low),
            "lower_2note_high": int(self.lower_2note_high),
            "lower_2note_target_low": int(self.lower_2note_target_low),
            "lower_2note_min_top": int(self.lower_2note_min_top),
            "lower_2note_foundation_mode": str(self.lower_2note_foundation_mode),
            "rooted_bass_anchor_enabled": bool(self.rooted_bass_anchor_enabled),
            "root_bass_anchor_low": int(self.root_bass_anchor_low),
            "root_bass_anchor_high": int(self.root_bass_anchor_high),
            "root_bass_anchor_target": int(self.root_bass_anchor_target),
            "root_bass_anchor_high_tail_semitones": int(self.root_bass_anchor_high_tail_semitones),
            "root_bass_anchor_high_tail_max_lower_span": int(self.root_bass_anchor_high_tail_max_lower_span),
            "whole_register_low": int(self.whole_register_low),
            "whole_register_high": int(self.whole_register_high),
            "upper_target_low": int(self.upper_target_low),
            "min_group_gap": int(self.min_group_gap),
            "max_group_gap": int(self.max_group_gap),
            "max_overall_span": int(self.max_overall_span),
            "low_register_density_guard_enabled": bool(self.low_register_density_guard_enabled),
            "upper_structure_lower_gate_enabled": bool(self.upper_structure_lower_gate_enabled),
            "upper_structure_spread_pilot_version": UPPER_STRUCTURE_SPREAD_PILOT_VERSION if self.upper_structure_lower_gate_enabled else None,
            "low_register_density_threshold": int(self.low_register_density_threshold),
            "low_register_density_max_notes_below": int(self.low_register_density_max_notes_below),
            "low_register_density_guard_version": LOW_REGISTER_DENSITY_GUARD_VERSION if self.low_register_density_guard_enabled else None,
            "runtime_enabled": self.runtime_enabled,
            "notes_only": True,
            "no_expression_or_pedal": True,
        }


def spread_policy_metadata(policy: Any | None) -> dict[str, object]:
    try:
        return dict(getattr(policy, "metadata", None) or {})
    except Exception:
        return dict(policy or {}) if isinstance(policy, dict) else {}


def basic_spread_register_policy(policy: Any | None = None) -> SpreadProjectionRegisterPolicy:
    """Build the default lower/upper guard for basic SPREAD projection.

    Caller policies may provide register fields, but this helper deliberately
    converts them into a small SPREAD-specific contract rather than passing a
    whole runtime policy through the notes/projection layer.
    """

    if isinstance(policy, SpreadProjectionRegisterPolicy):
        return policy
    if policy is None:
        return SpreadProjectionRegisterPolicy()
    metadata = spread_policy_metadata(policy)
    return SpreadProjectionRegisterPolicy(
        lower_low=int(metadata.get("spread_lower_low", getattr(policy, "left_hand_low", 36))),
        lower_high=int(metadata.get("spread_lower_high", getattr(policy, "left_hand_high", 60))),
        lower_2note_low=int(metadata.get("spread_lower_2note_low", 40)),
        lower_2note_high=int(metadata.get("spread_lower_2note_high", 52)),
        lower_2note_target_low=int(metadata.get("spread_lower_2note_target_low", 40)),
        lower_2note_min_top=int(metadata.get("spread_lower_2note_min_top", 40)),
        lower_2note_foundation_mode=str(metadata.get("spread_lower_2note_foundation_mode", "rooted")),
        rooted_bass_anchor_enabled=bool(metadata.get("spread_rooted_bass_anchor_enabled", False)),
        root_bass_anchor_low=int(metadata.get("spread_root_bass_anchor_low", metadata.get("spread_whole_register_low", 36))),
        root_bass_anchor_high=int(metadata.get("spread_root_bass_anchor_high", 48)),
        root_bass_anchor_target=int(metadata.get("spread_root_bass_anchor_target", metadata.get("spread_root_bass_anchor_low", 36))),
        root_bass_anchor_high_tail_semitones=int(metadata.get("spread_root_bass_anchor_high_tail_semitones", 4)),
        root_bass_anchor_high_tail_max_lower_span=int(metadata.get("spread_root_bass_anchor_high_tail_max_lower_span", 12)),
        whole_register_low=int(metadata.get("spread_whole_register_low", 36)),
        whole_register_high=int(metadata.get("spread_whole_register_high", 84)),
        upper_low=int(metadata.get("spread_upper_low", getattr(policy, "right_hand_low", 48))),
        upper_high=int(metadata.get("spread_upper_high", getattr(policy, "right_hand_high", 84))),
        lower_target_low=int(metadata.get("spread_lower_target_low", getattr(policy, "left_hand_low", 36))),
        lower_1note_target_low=int(metadata.get("spread_lower_1note_target_low", metadata.get("spread_lower_target_low", getattr(policy, "left_hand_low", 36)))),
        upper_target_low=int(metadata.get("spread_upper_target_low", getattr(policy, "right_hand_low", 60))),
        min_group_gap=int(metadata.get("spread_min_group_gap", 5)),
        max_group_gap=int(metadata.get("spread_max_group_gap", 28)),
        max_overall_span=int(metadata.get("spread_max_overall_span", 48)),
        low_register_density_guard_enabled=bool(metadata.get("spread_low_register_density_guard_enabled", False)),
        upper_structure_lower_gate_enabled=bool(metadata.get("spread_upper_structure_lower_gate_enabled", False)),
        low_register_density_threshold=int(metadata.get("spread_low_register_density_threshold", 40)),
        low_register_density_max_notes_below=int(metadata.get("spread_low_register_density_max_notes_below", 1)),
    )


def is_spread_1plus4_contract(contract: Any) -> bool:
    return str(getattr(contract, "recipe_id", "")) == "spread_1plus4_contract"


def is_spread_3plus4_contract(contract: Any) -> bool:
    return str(getattr(contract, "recipe_id", "")) == "spread_3plus4_contract"


def spread_register_policy_for_contract(
    contract: Any,
    register_policy: SpreadProjectionRegisterPolicy,
) -> SpreadProjectionRegisterPolicy:
    if not is_spread_3plus4_contract(contract):
        return register_policy
    # v2_2_76: 3+4 is a thick/climax SPREAD texture with its own whole-voicing
    # register guard. Keep this contract-local: other SPREAD groupings still use
    # their existing lower/upper ranges.
    return replace(
        register_policy,
        lower_low=min(int(register_policy.lower_low), 33),
        root_bass_anchor_low=min(int(register_policy.root_bass_anchor_low), 33),
        whole_register_low=min(int(register_policy.whole_register_low), 33),
        upper_high=min(int(register_policy.upper_high), 79),
        whole_register_high=min(int(register_policy.whole_register_high), 79),
    )


def lower_group_register_window(
    contract: Any,
    register_policy: SpreadProjectionRegisterPolicy,
) -> tuple[int, int, int, int | None]:
    if is_spread_1plus4_contract(contract):
        return (
            int(register_policy.lower_low),
            int(register_policy.lower_high),
            int(register_policy.lower_1note_target_low),
            None,
        )
    if int(contract.lower_group.note_count) in {2, 3} and bool(register_policy.rooted_bass_anchor_enabled):
        return (
            int(register_policy.root_bass_anchor_low),
            int(register_policy.whole_register_high),
            int(register_policy.root_bass_anchor_target),
            None,
        )
    if int(contract.lower_group.note_count) == 2:
        return (
            int(register_policy.lower_2note_low),
            int(register_policy.lower_2note_high),
            int(register_policy.lower_2note_target_low),
            int(register_policy.lower_2note_min_top),
        )
    return (
        int(register_policy.lower_low),
        int(register_policy.lower_high),
        int(register_policy.lower_target_low),
        None,
    )


def root_bass_note_from_lower(lower: LowerGroupPlacement) -> int | None:
    root_notes = [int(note) for degree, note in lower.placed_degrees if str(degree) in {"R", "1"}]
    return min(root_notes) if root_notes else None


def rooted_bass_anchor_passed(
    lower: LowerGroupPlacement,
    upper_placed: list[PlacedDegree] | tuple[PlacedDegree, ...],
) -> bool:
    root_note = root_bass_note_from_lower(lower)
    if root_note is None:
        return False
    combined = [*lower.notes, *(int(note) for _, note in upper_placed)]
    return bool(combined) and int(root_note) == min(combined)


def root_anchor_tail_span_guard_enabled(contract: Any) -> bool:
    # v2_2_73: 3+4 deliberately uses a thicker lower recipe
    # (root+7+upper3 / root+5+upper3). When the root anchor is in the upper
    # tail of E2-E3, these shapes naturally exceed the 12-semitone tail span
    # guard. Keep the guard for 2+3, 2+4, and 3+3, but disable it for 3+4.
    return str(getattr(contract, "recipe_id", "")) != "spread_3plus4_contract"


def root_anchor_tail_span_guard_passed(lower: LowerGroupPlacement, register_policy: SpreadProjectionRegisterPolicy) -> bool:
    root_note = root_bass_note_from_lower(lower)
    if root_note is None:
        return False
    high_tail_start = int(register_policy.root_bass_anchor_high) - int(register_policy.root_bass_anchor_high_tail_semitones)
    if int(root_note) < high_tail_start:
        return True
    return int(lower.span_semitones) <= int(register_policy.root_bass_anchor_high_tail_max_lower_span)


def upper_structure_root_shell_tail_gate_passed(
    lower: LowerGroupPlacement,
    register_policy: SpreadProjectionRegisterPolicy,
) -> bool:
    root_note = root_bass_note_from_lower(lower)
    if root_note is None:
        return False
    high_tail_start = int(register_policy.root_bass_anchor_high) - int(register_policy.root_bass_anchor_high_tail_semitones)
    return int(root_note) >= int(high_tail_start)


def low_register_density_guard_passed(notes: list[int] | tuple[int, ...], register_policy: SpreadProjectionRegisterPolicy) -> bool:
    if not bool(register_policy.low_register_density_guard_enabled):
        return True
    below = [int(note) for note in notes if int(note) < int(register_policy.low_register_density_threshold)]
    return len(below) <= int(register_policy.low_register_density_max_notes_below)


def spread_candidate_preserves_seventh_chord_identity(chord_symbol: str, degree_names: tuple[str, ...]) -> bool:
    from jammate_engine.core.voicing.sources.content_planner import source_preserves_seventh_chord_identity

    return bool(source_preserves_seventh_chord_identity(chord_symbol, degree_names))


def basic_spread_projection_legality(
    lower: LowerGroupPlacement,
    upper_placed: list[PlacedDegree] | tuple[PlacedDegree, ...],
    register_policy: SpreadProjectionRegisterPolicy,
    contract: Any,
) -> tuple[bool, str]:
    if not lower.is_legal:
        return False, lower.legality_reason
    upper_notes = [int(note) for _, note in upper_placed]
    if len(upper_notes) != int(contract.upper_source.note_count):
        return False, "upper_source_density_mismatch"
    if any(note < int(register_policy.upper_low) or note > int(register_policy.upper_high) for note in upper_notes):
        return False, "upper_group_outside_register"
    combined_degrees = tuple((*lower.instance.degree_names, *(str(degree) for degree, _ in upper_placed)))
    if not spread_candidate_preserves_seventh_chord_identity(lower.instance.chord_symbol, combined_degrees):
        return False, "spread_candidate_rejected_by_global_seventh_chord_source_integrity_gate"
    lower_notes = list(lower.notes)
    if not lower_notes or not upper_notes:
        return False, "missing_lower_or_upper_group"
    if set(lower_notes).intersection(upper_notes):
        return False, "upper_lower_note_overlap"
    combined_notes = [*lower_notes, *upper_notes]
    if not low_register_density_guard_passed(combined_notes, register_policy):
        return False, "low_register_density_guard_failed"
    if bool(register_policy.rooted_bass_anchor_enabled):
        root_note = root_bass_note_from_lower(lower)
        shell_only_upper_structure_lower = bool(register_policy.upper_structure_lower_gate_enabled) and lower.instance.recipe.recipe_id == LowerGroupRecipeId.THIRD_SEVENTH
        if root_note is None:
            if not shell_only_upper_structure_lower:
                return False, "rooted_bass_anchor_missing_root"
        else:
            if root_note < int(register_policy.root_bass_anchor_low) or root_note > int(register_policy.root_bass_anchor_high):
                return False, "rooted_bass_anchor_outside_root_window"
            if root_note != min(combined_notes):
                return False, "rooted_bass_anchor_not_lowest_note"
            if root_anchor_tail_span_guard_enabled(contract) and not root_anchor_tail_span_guard_passed(lower, register_policy):
                return False, "root_anchor_high_tail_lower_span_too_wide"
            if bool(register_policy.upper_structure_lower_gate_enabled) and lower.instance.recipe.recipe_id == LowerGroupRecipeId.ROOT_THIRD_SEVENTH:
                if not upper_structure_root_shell_tail_gate_passed(lower, register_policy):
                    return False, "upper_structure_root_plus_shell_compact_tail_gate_failed"
        if any(note < int(register_policy.whole_register_low) or note > int(register_policy.whole_register_high) for note in combined_notes):
            return False, "whole_voicing_outside_register"
    gap = min(upper_notes) - max(lower_notes)
    if gap < int(register_policy.min_group_gap):
        return False, "group_gap_too_small"
    if gap > int(register_policy.max_group_gap):
        return False, "group_gap_too_large"
    notes = sorted({*lower_notes, *upper_notes})
    if len(notes) != int(contract.density):
        return False, "combined_density_mismatch_after_dedupe"
    span = max(notes) - min(notes)
    if span > int(register_policy.max_overall_span):
        return False, "overall_span_guard_failed"
    return True, "ok"


def spread_register_guard_debug(policy: Any | None = None) -> dict[str, object]:
    register_policy = basic_spread_register_policy(policy)
    return {
        "spread_register_guard_split_version": SPREAD_REGISTER_GUARD_SPLIT_VERSION,
        "owner": "core.voicing.disposition.spread_register_guards",
        "notes_only": True,
        "no_pattern_expression_pedal_or_midi": True,
        "register_policy": register_policy.to_debug_dict(),
    }
