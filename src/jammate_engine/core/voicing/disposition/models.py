from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Disposition(str, Enum):
    """Legacy voicing disposition input enum.

    This enum remains the public compatibility surface for existing
    ``VoicingPolicy`` objects and style presets.  New projection code should not
    branch directly on these values.  Instead, map them to
    :class:`DispositionProjectionSpec`, then route through the new disposition
    family / projection-method taxonomy.
    """

    CLOSED = "closed"
    OPEN = "open"
    SPREAD = "spread"
    TWO_HAND_SPREAD = "two_hand_spread"
    LEFT_ROOT_RIGHT_CHORD = "left_root_right_chord"
    LEFT_ROOT_RIGHT_ROOTLESS = "left_root_right_rootless"
    OPEN_ROOT_10TH = "open_root_10th"


class DispositionFamily(str, Enum):
    """High-level layout family for the new projection layer."""

    CLOSED = "closed"
    OPEN = "open"
    SPREAD = "spread"


class ClosedProjectionMethod(str, Enum):
    """Projection methods under :class:`DispositionFamily.CLOSED`."""

    COMPACT = "compact"


class OpenProjectionMethod(str, Enum):
    """Projection methods under :class:`DispositionFamily.OPEN`.

    Drop2/drop3 are explicitly open-family methods, not disposition families
    parallel to OPEN.
    """

    GENERIC_OPEN = "generic_open"
    DROP2 = "drop2"
    DROP3 = "drop3"
    DROP2_AND_4 = "drop2_and_4"




OPEN_METHOD_POOL_METADATA_KEYS = (
    "open_projection_methods",
    "allowed_open_projection_methods",
    "disposition_open_projection_methods",
    "open_projection_method_pool",
)

OPEN_METHOD_SINGLE_METADATA_KEYS = (
    "open_projection_method",
    "disposition_open_projection_method",
)

DEFAULT_OPEN_PROJECTION_METHOD_POOL: tuple[OpenProjectionMethod, ...] = (OpenProjectionMethod.GENERIC_OPEN,)
ALL_OPEN_PROJECTION_METHOD_POOL: tuple[OpenProjectionMethod, ...] = (
    OpenProjectionMethod.GENERIC_OPEN,
    OpenProjectionMethod.DROP2,
    OpenProjectionMethod.DROP3,
    OpenProjectionMethod.DROP2_AND_4,
)


def coerce_open_projection_method(value: object) -> OpenProjectionMethod | None:
    """Return a normalized OPEN projection method from metadata input."""

    if isinstance(value, OpenProjectionMethod):
        return value
    text = str(value or "").strip().lower().replace("-", "_")
    if not text:
        return None
    aliases = {
        "generic": OpenProjectionMethod.GENERIC_OPEN,
        "open": OpenProjectionMethod.GENERIC_OPEN,
        "legacy_open": OpenProjectionMethod.GENERIC_OPEN,
        "generic_open": OpenProjectionMethod.GENERIC_OPEN,
        "drop_2": OpenProjectionMethod.DROP2,
        "drop2": OpenProjectionMethod.DROP2,
        "drop_3": OpenProjectionMethod.DROP3,
        "drop3": OpenProjectionMethod.DROP3,
        "drop_2_and_4": OpenProjectionMethod.DROP2_AND_4,
        "drop2_and_4": OpenProjectionMethod.DROP2_AND_4,
        "drop24": OpenProjectionMethod.DROP2_AND_4,
        "drop_2_4": OpenProjectionMethod.DROP2_AND_4,
        "drop2&4": OpenProjectionMethod.DROP2_AND_4,
        "drop_2&4": OpenProjectionMethod.DROP2_AND_4,
    }
    if text in aliases:
        return aliases[text]
    try:
        return OpenProjectionMethod(text)
    except ValueError:
        return None


def open_projection_method_pool_from_metadata(metadata: dict | None) -> tuple[OpenProjectionMethod, ...]:
    """Resolve the OPEN method candidate pool requested by policy metadata.

    Default behavior intentionally remains legacy-compatible: ordinary
    ``Disposition.OPEN`` means ``GENERIC_OPEN`` only.  Multiple OPEN methods are
    introduced only when metadata explicitly requests a method pool.
    """

    metadata = dict(metadata or {})
    raw: object | None = None
    for key in OPEN_METHOD_POOL_METADATA_KEYS:
        if key in metadata:
            raw = metadata.get(key)
            break
    if raw is None:
        for key in OPEN_METHOD_SINGLE_METADATA_KEYS:
            if key in metadata:
                raw = metadata.get(key)
                break
    if raw is None:
        return DEFAULT_OPEN_PROJECTION_METHOD_POOL

    if isinstance(raw, str):
        normalized_raw = raw.strip().lower().replace("-", "_")
        if normalized_raw in {"all", "candidate_pool", "open_pool", "all_open_methods"}:
            return ALL_OPEN_PROJECTION_METHOD_POOL
        values: list[object] = [part.strip() for part in raw.replace(";", ",").split(",") if part.strip()]
    elif isinstance(raw, (list, tuple, set)):
        values = list(raw)
    else:
        values = [raw]

    methods: list[OpenProjectionMethod] = []
    for value in values:
        method = coerce_open_projection_method(value)
        if method is not None and method not in methods:
            methods.append(method)
    return tuple(methods) or DEFAULT_OPEN_PROJECTION_METHOD_POOL


class SpreadProjectionMethod(str, Enum):
    """Projection methods under :class:`DispositionFamily.SPREAD`.

    These names describe abstract lower/upper or foundation/projection roles,
    not physical hands.  Piano realization may later project them to left/right
    hand registers.
    """

    LOWER_UPPER_GROUPED = "lower_upper_grouped"
    FOUNDATION_PROJECTION = "foundation_projection"
    ROOT_ANCHORED = "root_anchored"
    ROOT_10TH_PROJECTION = "root_10th_projection"


@dataclass(frozen=True)
class DispositionProjectionSpec:
    """Normalized projection taxonomy for one legacy disposition request.

    ``legacy_disposition`` is kept only so v2_2_x can migrate without changing
    external style/API inputs all at once.  Internal projection logic should use
    ``family`` plus the family-specific method field.
    """

    family: DispositionFamily
    closed_method: ClosedProjectionMethod | None = None
    open_method: OpenProjectionMethod | None = None
    spread_method: SpreadProjectionMethod | None = None
    legacy_disposition: Disposition | None = None
    legacy_runtime_path: str = ""
    migration_note: str = ""

    @property
    def method_value(self) -> str:
        method = self.closed_method or self.open_method or self.spread_method
        return method.value if method is not None else "unspecified"

    def to_debug_dict(self) -> dict[str, str | None]:
        return {
            "family": self.family.value,
            "method": self.method_value,
            "closed_method": self.closed_method.value if self.closed_method else None,
            "open_method": self.open_method.value if self.open_method else None,
            "spread_method": self.spread_method.value if self.spread_method else None,
            "legacy_disposition": self.legacy_disposition.value if self.legacy_disposition else None,
            "legacy_runtime_path": self.legacy_runtime_path,
            "migration_note": self.migration_note,
        }


@dataclass(frozen=True)
class DispositionProjectionResult:
    """Result returned by the disposition projection entry facade.

    v2_2_1 keeps the legacy placement algorithms intact, but all candidate
    generation now receives a normalized projection spec and debug contract from
    one entry point.  Later passes can replace the legacy callback internals with
    closed/open/spread modules without changing the caller contract.
    """

    placed: tuple[tuple[str, int], ...]
    spec: DispositionProjectionSpec
    disposition_guard: dict[str, object]
    metadata: dict[str, object]

    @property
    def placed_list(self) -> list[tuple[str, int]]:
        return [(str(degree), int(note)) for degree, note in self.placed]


LEGACY_DISPOSITION_PROJECTION_MAP: dict[Disposition, DispositionProjectionSpec] = {
    Disposition.CLOSED: DispositionProjectionSpec(
        family=DispositionFamily.CLOSED,
        closed_method=ClosedProjectionMethod.COMPACT,
        legacy_disposition=Disposition.CLOSED,
        legacy_runtime_path="candidate_generator strict_closed / disposition_planner closed stack",
        migration_note="Migrate compact closed placement into core.voicing.disposition.closed/projection; preserve no-behavior closed baseline.",
    ),
    Disposition.OPEN: DispositionProjectionSpec(
        family=DispositionFamily.OPEN,
        open_method=OpenProjectionMethod.GENERIC_OPEN,
        legacy_disposition=Disposition.OPEN,
        legacy_runtime_path="disposition_planner _place_stack(..., spread=True)",
        migration_note="Replace legacy generic octave-widening with explicit open projection methods after closed migration.",
    ),
    Disposition.SPREAD: DispositionProjectionSpec(
        family=DispositionFamily.SPREAD,
        spread_method=SpreadProjectionMethod.LOWER_UPPER_GROUPED,
        legacy_disposition=Disposition.SPREAD,
        legacy_runtime_path="disposition_planner _place_spread",
        migration_note="Move lower/upper grouped spread behavior into spread projection code and delete external spread branches.",
    ),
    Disposition.TWO_HAND_SPREAD: DispositionProjectionSpec(
        family=DispositionFamily.SPREAD,
        spread_method=SpreadProjectionMethod.LOWER_UPPER_GROUPED,
        legacy_disposition=Disposition.TWO_HAND_SPREAD,
        legacy_runtime_path="disposition_planner _place_spread",
        migration_note="Keep two-hand wording as legacy input only; new core taxonomy uses abstract lower/upper grouping.",
    ),
    Disposition.LEFT_ROOT_RIGHT_CHORD: DispositionProjectionSpec(
        family=DispositionFamily.SPREAD,
        spread_method=SpreadProjectionMethod.FOUNDATION_PROJECTION,
        legacy_disposition=Disposition.LEFT_ROOT_RIGHT_CHORD,
        legacy_runtime_path="disposition_planner _place_left_root_right_chord",
        migration_note="Replace hand-specific name with foundation/projection method and keep physical hand mapping in piano realization policy.",
    ),
    Disposition.LEFT_ROOT_RIGHT_ROOTLESS: DispositionProjectionSpec(
        family=DispositionFamily.SPREAD,
        spread_method=SpreadProjectionMethod.FOUNDATION_PROJECTION,
        legacy_disposition=Disposition.LEFT_ROOT_RIGHT_ROOTLESS,
        legacy_runtime_path="disposition_planner _place_left_root_right_chord",
        migration_note="Normalize to foundation/projection; rootless upper content remains a source/content decision, not a spread family.",
    ),
    Disposition.OPEN_ROOT_10TH: DispositionProjectionSpec(
        family=DispositionFamily.SPREAD,
        spread_method=SpreadProjectionMethod.ROOT_10TH_PROJECTION,
        legacy_disposition=Disposition.OPEN_ROOT_10TH,
        legacy_runtime_path="disposition_planner _place_open_root_10th",
        migration_note="Normalize to root-10th projection under spread/foundation architecture.",
    ),
}


def projection_spec_from_legacy_disposition(
    disposition: Disposition | str,
) -> DispositionProjectionSpec:
    """Return the normalized projection spec for an existing disposition input."""

    if not isinstance(disposition, Disposition):
        disposition = Disposition(str(disposition))
    return LEGACY_DISPOSITION_PROJECTION_MAP[disposition]
