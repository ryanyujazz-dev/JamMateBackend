from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import (
    ClosedProjectionMethod,
    DispositionFamily,
    OpenProjectionMethod,
    SpreadProjectionMethod,
    coerce_open_projection_method,
)


DEFAULT_STYLE_DISPOSITION_METHOD_WEIGHTS: dict[str, dict[str, dict[str, float]]] = {
    "medium_swing": {
        # v2_2_19 runtime pilot: OPEN drop-family methods are now real
        # selector priors for Medium Swing.  DROP2 is the primary idiomatic
        # open sound; DROP3 is useful but slightly lower; GENERIC_OPEN remains
        # available only as an explicit rescue/fallback safe method; normal
        # Medium Swing OPEN texture should use the named drop-family methods.
        "family": {"closed": 0.30, "open": 0.70, "spread": 0.00},
        "open": {"generic_open": 0.0, "drop2": 0.52, "drop3": 0.38, "drop2_and_4": 0.10},
        "spread": {"lower_upper_grouped": 0.55, "foundation_projection": 0.20, "root_anchored": 0.15, "root_10th_projection": 0.10},
    },
    "bossa_nova": {
        "family": {"closed": 0.62, "open": 0.33, "spread": 0.05},
        "open": {"generic_open": 0.58, "drop2": 0.30, "drop3": 0.09, "drop2_and_4": 0.03},
        "spread": {"lower_upper_grouped": 0.65, "foundation_projection": 0.20, "root_anchored": 0.10, "root_10th_projection": 0.05},
    },
    "jazz_ballad": {
        "family": {"closed": 0.20, "open": 0.35, "spread": 0.45},
        "open": {"generic_open": 0.30, "drop2": 0.34, "drop3": 0.25, "drop2_and_4": 0.11},
        "spread": {"lower_upper_grouped": 0.36, "foundation_projection": 0.32, "root_anchored": 0.22, "root_10th_projection": 0.10},
    },
}


@dataclass(frozen=True)
class DispositionMethodWeightSpec:
    """Style-level disposition method weight contract.

    The spec started as a planning contract in v2_2_10.  v2_2_19 allows a
    style to opt in to selector consumption via metadata, first for Medium
    Swing's OPEN drop-family runtime pilot.  Styles that do not opt in still
    expose weights only for audit/planning.
    """

    family_weights: dict[str, float] = field(default_factory=dict)
    open_method_weights: dict[str, float] = field(default_factory=dict)
    spread_method_weights: dict[str, float] = field(default_factory=dict)
    source: str = "default"
    enabled_for_scoring: bool = False
    contract: str = "style_disposition_method_weight_contract"

    def family_weight(self, family: DispositionFamily | str | None) -> float:
        if family is None:
            return 1.0
        key = family.value if isinstance(family, DispositionFamily) else str(family)
        return float(self.family_weights.get(key, 1.0))

    def open_method_weight(self, method: OpenProjectionMethod | str | None) -> float:
        if method is None:
            return 1.0
        key = method.value if isinstance(method, OpenProjectionMethod) else str(method)
        return float(self.open_method_weights.get(key, 1.0))

    def spread_method_weight(self, method: SpreadProjectionMethod | str | None) -> float:
        if method is None:
            return 1.0
        key = method.value if isinstance(method, SpreadProjectionMethod) else str(method)
        return float(self.spread_method_weights.get(key, 1.0))

    def method_weight(
        self,
        *,
        family: DispositionFamily | str | None,
        closed_method: ClosedProjectionMethod | str | None = None,
        open_method: OpenProjectionMethod | str | None = None,
        spread_method: SpreadProjectionMethod | str | None = None,
    ) -> float:
        family_weight = self.family_weight(family)
        family_value = family.value if isinstance(family, DispositionFamily) else str(family or "")
        if family_value == DispositionFamily.OPEN.value:
            return family_weight * self.open_method_weight(open_method)
        if family_value == DispositionFamily.SPREAD.value:
            return family_weight * self.spread_method_weight(spread_method)
        if family_value == DispositionFamily.CLOSED.value and closed_method is not None:
            return family_weight
        return family_weight

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "source": self.source,
            "enabled_for_scoring": bool(self.enabled_for_scoring),
            "family_weights": dict(self.family_weights),
            "open_method_weights": dict(self.open_method_weights),
            "spread_method_weights": dict(self.spread_method_weights),
        }


def disposition_method_weight_spec_from_metadata(metadata: dict[str, Any] | None) -> DispositionMethodWeightSpec:
    """Resolve style-level disposition/projection-method weights from metadata.

    Accepted shapes:
      metadata["disposition_method_weights"] = {
        "family": {"closed": 0.3, "open": 0.5, "spread": 0.2},
        "open": {"drop2": 0.45, ...},
        "spread": {"foundation_projection": 0.3, ...},
      }

    If no explicit map is provided, a style-name default contract is returned
    for documentation/audit.  It affects selection only when metadata explicitly
    sets ``disposition_method_weights_enabled_for_scoring``.
    """

    metadata = dict(metadata or {})
    style = str(metadata.get("style") or "").strip().lower()
    raw = metadata.get("disposition_method_weights") or metadata.get("voicing_disposition_method_weights")
    source = "metadata"
    if not isinstance(raw, dict):
        raw = DEFAULT_STYLE_DISPOSITION_METHOD_WEIGHTS.get(style, {})
        source = f"style_default:{style}" if raw else "default"

    return DispositionMethodWeightSpec(
        family_weights=_normalize_family_weights(raw.get("family") or raw.get("families") or raw.get("disposition_family_weights")),
        open_method_weights=_normalize_open_method_weights(raw.get("open") or raw.get("open_methods") or raw.get("open_projection_methods")),
        spread_method_weights=_normalize_spread_method_weights(raw.get("spread") or raw.get("spread_methods") or raw.get("spread_projection_methods")),
        source=source,
        enabled_for_scoring=bool(metadata.get("disposition_method_weights_enabled_for_scoring", False)),
    )


def _normalize_family_weights(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, float] = {}
    aliases = {
        "compact": DispositionFamily.CLOSED,
        "closed": DispositionFamily.CLOSED,
        "open": DispositionFamily.OPEN,
        "spread": DispositionFamily.SPREAD,
        "foundation_projection": DispositionFamily.SPREAD,
    }
    for key, raw_weight in value.items():
        family = aliases.get(str(key).strip().lower().replace("-", "_"))
        if family is None:
            try:
                family = DispositionFamily(str(key).strip().lower().replace("-", "_"))
            except ValueError:
                continue
        out[family.value] = _safe_float(raw_weight, default=1.0)
    return out


def _normalize_open_method_weights(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, float] = {}
    for key, raw_weight in value.items():
        method = coerce_open_projection_method(key)
        if method is None:
            continue
        out[method.value] = _safe_float(raw_weight, default=1.0)
    return out


def _normalize_spread_method_weights(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, float] = {}
    aliases = {
        "lower_upper": SpreadProjectionMethod.LOWER_UPPER_GROUPED,
        "lower_upper_grouped": SpreadProjectionMethod.LOWER_UPPER_GROUPED,
        "foundation": SpreadProjectionMethod.FOUNDATION_PROJECTION,
        "foundation_projection": SpreadProjectionMethod.FOUNDATION_PROJECTION,
        "root_anchored": SpreadProjectionMethod.ROOT_ANCHORED,
        "root_anchor": SpreadProjectionMethod.ROOT_ANCHORED,
        "root_10th": SpreadProjectionMethod.ROOT_10TH_PROJECTION,
        "root_10th_projection": SpreadProjectionMethod.ROOT_10TH_PROJECTION,
    }
    for key, raw_weight in value.items():
        text = str(key).strip().lower().replace("-", "_")
        method = aliases.get(text)
        if method is None:
            try:
                method = SpreadProjectionMethod(text)
            except ValueError:
                continue
        out[method.value] = _safe_float(raw_weight, default=1.0)
    return out


def _safe_float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
