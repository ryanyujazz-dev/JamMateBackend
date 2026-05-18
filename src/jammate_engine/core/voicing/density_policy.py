from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .disposition import Disposition
from .policy import FunctionalGrouping, VoicingPolicy

VOICING_DENSITY_DISPOSITION_POLICY_VERSION = "v2_6_10"

SPREAD_RETIRED_FOUR_NOTE_GROUPINGS: tuple[str, ...] = (
    FunctionalGrouping.ONE_PLUS_THREE.value,
    FunctionalGrouping.TWO_PLUS_TWO.value,
)

SPREAD_ACTIVE_RUNTIME_CONTRACT_IDS: tuple[str, ...] = (
    "spread_1plus4_contract",
    "spread_2plus3_contract",
    "spread_2plus4_contract",
    "spread_3plus3_contract",
    "spread_3plus4_contract",
)

SPREAD_DEFAULT_BALLAD_RUNTIME_CONTRACT_IDS: tuple[str, ...] = (
    "spread_2plus3_contract",
    "spread_2plus4_contract",
    "spread_3plus3_contract",
)


@dataclass(frozen=True)
class DensityDispositionDecision:
    """Decision for whether a content source may enter one disposition path.

    This is a taxonomy guard, not a selector and not a scoring patch.  Content
    planning may still produce four-note sources for CLOSED/OPEN fallback, but
    SPREAD owns a separate grouped-density route.  Therefore 4-note SPREAD
    groupings (1+3 and 2+2) are retired from ordinary runtime.
    """

    allowed: bool
    reason: str
    version: str = VOICING_DENSITY_DISPOSITION_POLICY_VERSION

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "voicing_density_disposition_policy_version": self.version,
            "allowed": bool(self.allowed),
            "reason": self.reason,
        }


def density_disposition_decision(
    *,
    disposition: Disposition | str,
    density: int | None,
    functional_grouping: FunctionalGrouping | str | None,
    policy: VoicingPolicy | None = None,
) -> DensityDispositionDecision:
    """Return whether a source-level candidate may use a disposition.

    The first hardening rule is deliberately narrow: block legacy source-level
    4-note SPREAD, but leave CLOSED/OPEN and 5+/grouped SPREAD untouched.

    v2_6_27 only changes the ordinary Ballad default runtime contract list:
    1+4 remains an active contract for explicit upper4-color usage but is no
    longer in the default comping body.
    """

    disp_value = disposition.value if isinstance(disposition, Disposition) else str(disposition)
    grouping_value = (
        functional_grouping.value
        if isinstance(functional_grouping, FunctionalGrouping)
        else (str(functional_grouping) if functional_grouping is not None else "")
    )
    if disp_value != Disposition.SPREAD.value:
        return DensityDispositionDecision(True, "non_spread_disposition_uses_existing_density_route")
    if int(density or 0) != 4 or grouping_value not in set(SPREAD_RETIRED_FOUR_NOTE_GROUPINGS):
        return DensityDispositionDecision(True, "spread_density_is_grouped_5plus_or_non_retired")
    metadata = dict(getattr(policy, "metadata", None) or {}) if policy is not None else {}
    allow_legacy = bool(metadata.get("spread_allow_legacy_4note_groupings", False))
    if allow_legacy:
        return DensityDispositionDecision(True, "legacy_4note_spread_explicitly_allowed_for_audit")
    return DensityDispositionDecision(False, "legacy_4note_spread_grouping_retired_use_5plus_grouped_spread_contracts")


def should_skip_source_disposition_candidate(
    *,
    disposition: Disposition | str,
    density: int | None,
    functional_grouping: FunctionalGrouping | str | None,
    policy: VoicingPolicy | None = None,
) -> bool:
    return not density_disposition_decision(
        disposition=disposition,
        density=density,
        functional_grouping=functional_grouping,
        policy=policy,
    ).allowed


def spread_density_runtime_contract_ids(policy: VoicingPolicy | None = None) -> tuple[str, ...]:
    """Return the active 5+/grouped SPREAD contracts for runtime routing."""

    metadata = dict(getattr(policy, "metadata", None) or {}) if policy is not None else {}
    raw = metadata.get("spread_density_runtime_contract_ids") or metadata.get("spread_active_runtime_contract_ids")
    if isinstance(raw, str):
        raw = (raw,)
    if isinstance(raw, (list, tuple)):
        requested = tuple(str(item) for item in raw if str(item).strip())
        active = tuple(item for item in requested if item in SPREAD_ACTIVE_RUNTIME_CONTRACT_IDS)
        if active:
            return active
    return SPREAD_DEFAULT_BALLAD_RUNTIME_CONTRACT_IDS


def voicing_density_disposition_policy_debug(policy: VoicingPolicy | None = None) -> dict[str, object]:
    return {
        "voicing_density_disposition_policy_version": VOICING_DENSITY_DISPOSITION_POLICY_VERSION,
        "spread_retired_four_note_groupings": list(SPREAD_RETIRED_FOUR_NOTE_GROUPINGS),
        "spread_active_runtime_contract_ids": list(SPREAD_ACTIVE_RUNTIME_CONTRACT_IDS),
        "spread_default_ballad_runtime_contract_ids": list(spread_density_runtime_contract_ids(policy)),
        "policy_layer": "core.voicing.density_policy",
        "boundary": "density/disposition routing only; no pattern, expression, gesture, pedal, or MIDI behavior",
    }
