from __future__ import annotations

from typing import Any

from jammate_engine.core.harmony.chord_parser import parse_chord

from .spread_contracts import SPREAD_RECIPE_CONTRACT_VERSION
from .spread_lower_groups import LowerGroupRecipeId, place_lower_group_recipe
from .spread_register_guards import (
    BASIC_SPREAD_PROJECTION_VERSION,
    SpreadProjectionRegisterPolicy,
    basic_spread_projection_legality,
    basic_spread_register_policy,
    is_spread_3plus4_contract,
    lower_group_register_window,
    spread_register_policy_for_contract,
)
from .spread_upper_sources import adapt_spread_upper_source_from_ref

SPREAD_PROJECTION_CORE_SPLIT_VERSION = "v2_6_9"


def project_basic_spread_contract(
    chord_symbol: str,
    contract: Any,
    policy: Any | None = None,
    *,
    max_upper_options: int = 12,
) -> Any:
    """Project one SPREAD recipe contract into lower/upper placed candidates.

    This owner performs the notes-only lower+upper projection orchestration for
    SPREAD.  It deliberately does not select style patterns, expression,
    gesture timing, pedal, MIDI, or runtime style weights.
    """

    from . import spread as public_spread

    recipe_contract = public_spread.spread_recipe_contract_by_id(contract) if isinstance(contract, str) else contract
    runtime_policy = None if isinstance(policy, SpreadProjectionRegisterPolicy) else policy
    runtime_policy = public_spread._spread_runtime_policy_for_contract(recipe_contract, runtime_policy)
    register_source_policy = policy if isinstance(policy, SpreadProjectionRegisterPolicy) else runtime_policy
    register_policy = spread_register_policy_for_contract(recipe_contract, basic_spread_register_policy(register_source_policy))
    upper_result = adapt_spread_upper_source_from_ref(chord_symbol, recipe_contract.upper_source, runtime_policy)
    lower_recipe_ids = public_spread._lower_recipe_ids_for_contract(recipe_contract, runtime_policy, chord_symbol=chord_symbol)
    candidates: list[Any] = []
    chord = parse_chord(chord_symbol)
    for lower_recipe_id in lower_recipe_ids:
        lower_low, lower_high, lower_target, lower_min_top = lower_group_register_window(recipe_contract, register_policy)
        lower = place_lower_group_recipe(
            chord.symbol,
            lower_recipe_id,
            lower_low,
            lower_high,
            target_low=lower_target,
            min_top_note=lower_min_top,
            root_bass_anchor_enabled=(
                bool(register_policy.rooted_bass_anchor_enabled)
                and int(recipe_contract.lower_group.note_count) in {2, 3}
                and lower_recipe_id != LowerGroupRecipeId.THIRD_SEVENTH
            ),
            root_bass_anchor_low=int(register_policy.root_bass_anchor_low),
            root_bass_anchor_high=int(register_policy.root_bass_anchor_high),
            allow_rooted_anchor_upper3_compression=is_spread_3plus4_contract(recipe_contract),
            upper3_compression_root_threshold=44,
        )
        if not lower.is_legal:
            continue
        upper_options = public_spread._filter_upper_options_for_spread_contract(
            upper_result.options,
            recipe_contract,
            runtime_policy,
        )[: max(1, int(max_upper_options))]
        for upper_option in upper_options:
            for upper_placed, method, upper_metadata in public_spread._place_upper_source_for_spread(
                chord.root_pc,
                upper_option,
                register_policy,
                runtime_policy,
            ):
                is_legal, reason = basic_spread_projection_legality(lower, upper_placed, register_policy, recipe_contract)
                candidates.append(
                    public_spread.SpreadProjectionCandidate(
                        chord_symbol=chord.symbol,
                        recipe_contract=recipe_contract,
                        lower=lower,
                        upper_source=upper_option,
                        upper_placed=tuple(upper_placed),
                        upper_projection_method=method,
                        upper_projection_metadata=upper_metadata,
                        register_policy=register_policy,
                        is_legal=is_legal,
                        legality_reason=reason,
                    )
                )
    metadata = dict(getattr(runtime_policy, "metadata", None) or {})
    if bool(metadata.get("spread_upper_3note_expanded_color_only")):
        expanded_upper_candidates = [
            candidate for candidate in candidates
            if candidate.is_legal and public_spread._is_expanded_upper_3note_color(candidate.upper_source)
        ]
        if expanded_upper_candidates:
            candidates = expanded_upper_candidates
    if bool(metadata.get("spread_upper_4note_expanded_color_only")):
        expanded_upper_candidates = [
            candidate for candidate in candidates
            if candidate.is_legal and public_spread._is_expanded_upper_4note_color(candidate.upper_source)
        ]
        if expanded_upper_candidates:
            candidates = expanded_upper_candidates
    candidates = public_spread._prefer_rootless_upper_color_for_spread_3plus4(candidates, recipe_contract)
    preferred_lower_recipe = public_spread._preferred_lower_recipe_id_from_policy(recipe_contract, runtime_policy)
    if preferred_lower_recipe is not None:
        preferred_candidates = [
            candidate for candidate in candidates
            if candidate.is_legal and candidate.lower.instance.recipe.recipe_id == preferred_lower_recipe
        ]
        if preferred_candidates:
            candidates = preferred_candidates
    candidates = public_spread._dedupe_spread_projection_candidates(candidates)
    return public_spread.SpreadProjectionResult(
        chord_symbol=chord.symbol,
        recipe_contract=recipe_contract,
        candidates=tuple(candidates),
        register_policy=register_policy,
    )


def project_basic_spread_candidates(
    chord_symbol: str,
    policy: Any | None = None,
    *,
    contract_ids: tuple[str, ...] | None = None,
    max_upper_options: int = 12,
) -> tuple[Any, ...]:
    """Project all or selected SPREAD recipe contracts for one chord symbol."""

    from . import spread as public_spread

    include_retired = False
    if contract_ids is not None:
        retired = {"spread_1plus3_contract", "spread_2plus2_contract"}
        include_retired = any(str(item) in retired for item in contract_ids)
    contracts = public_spread.spread_recipe_contract_skeleton(include_retired_four_note=include_retired)
    if contract_ids is not None:
        wanted = {str(item) for item in contract_ids}
        contracts = tuple(contract for contract in contracts if contract.recipe_id in wanted)
    return tuple(
        project_basic_spread_contract(chord_symbol, contract, policy, max_upper_options=max_upper_options)
        for contract in contracts
    )


def basic_spread_projection_debug(chord_symbol: str = "Cmaj7", policy: Any | None = None) -> dict[str, object]:
    """Return a debug payload for notes-only SPREAD projection core."""

    results = project_basic_spread_candidates(chord_symbol, policy)
    return {
        "contract_version": SPREAD_RECIPE_CONTRACT_VERSION,
        "basic_spread_projection_version": BASIC_SPREAD_PROJECTION_VERSION,
        "spread_projection_core_split_version": SPREAD_PROJECTION_CORE_SPLIT_VERSION,
        "owner": "core.voicing.disposition.spread_projection_core",
        "layer": "core.voicing.disposition.spread_projection_core",
        "purpose": "Basic SPREAD Projection: lower inventory + upper source adapter + register/gap/span guards",
        "runtime_enabled": False,
        "notes_only": True,
        "no_expression_or_pedal": True,
        "no_pattern_anticipation_gesture_or_midi": True,
        "final_placed_closed_open_result_reuse_allowed": False,
        "results": [result.to_debug_dict() for result in results],
    }
