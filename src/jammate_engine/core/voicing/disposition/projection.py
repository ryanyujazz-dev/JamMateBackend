from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import TYPE_CHECKING

from .closed import place_compact_closed_seed_layout, strict_closed_compact_layout_enabled
from .models import (
    Disposition,
    DispositionFamily,
    DispositionProjectionResult,
    OpenProjectionMethod,
    coerce_open_projection_method,
    projection_spec_from_legacy_disposition,
)
from .open import named_open_projection_metadata, place_named_open_projection_from_closed_parent, place_named_open_projection_from_closed_parents

if TYPE_CHECKING:
    from jammate_engine.core.voicing.policy import VoicingPolicy

Degree = tuple[str, int]
PlacedDegree = tuple[str, int]
LegacyPlacementCallback = Callable[[], list[PlacedDegree]]


def project_source_to_disposition(
    *,
    disposition: Disposition | str,
    policy: "VoicingPolicy",
    legacy_placement_callback: LegacyPlacementCallback,
    closed_parent_placement_callback: LegacyPlacementCallback | None = None,
    closed_parent_placement_candidates_callback: Callable[[], list[list[PlacedDegree]]] | None = None,
    root_pc: int | None = None,
    degrees: list[Degree] | None = None,
) -> DispositionProjectionResult:
    """Project one source/orientation request through the normalized entry point.

    This is intentionally a facade in v2_2_1.  The old placement code is still
    called through ``legacy_placement_callback`` so the musical output remains
    unchanged, but the caller no longer branches directly on raw legacy
    disposition values without also receiving a normalized
    ``DispositionProjectionSpec``.

    Later passes should move closed/open/spread algorithms behind this function
    and then delete the legacy callback path step by step.
    """

    legacy_disposition = disposition if isinstance(disposition, Disposition) else Disposition(str(disposition))
    spec = _resolve_projection_spec(legacy_disposition, policy)

    placed: list[PlacedDegree]
    legacy_callback_used = True
    migrated_projection_path = ""
    if (
        spec.family == DispositionFamily.CLOSED
        and root_pc is not None
        and degrees is not None
        and strict_closed_compact_layout_enabled(policy)
        and len(degrees) in {3, 4}
    ):
        placed = place_compact_closed_seed_layout(root_pc, degrees, policy)
        if placed:
            legacy_callback_used = False
            migrated_projection_path = "core.voicing.disposition.closed.place_compact_closed_seed_layout"
        else:
            # Preserve the v2_1.x no-behavior contract: doubled closed triads
            # such as 1351 intentionally repeat a pitch class, so the strict
            # pitch-class seed returns empty and the ordered-source legacy path
            # must still supply the 4-note rotation rather than falling back to
            # a partial candidate.
            placed = legacy_placement_callback()
    elif spec.family == DispositionFamily.OPEN and spec.open_method in {
        OpenProjectionMethod.DROP2,
        OpenProjectionMethod.DROP3,
        OpenProjectionMethod.DROP2_AND_4,
    }:
        parent_closed: list[PlacedDegree] = []
        parent_closed_candidates: list[list[PlacedDegree]] = []
        if closed_parent_placement_candidates_callback is not None:
            parent_closed_candidates = closed_parent_placement_candidates_callback()
        if not parent_closed_candidates and closed_parent_placement_callback is not None:
            parent_closed = closed_parent_placement_callback()
            if parent_closed:
                parent_closed_candidates = [parent_closed]
        if (
            not parent_closed_candidates
            and root_pc is not None
            and degrees is not None
            and strict_closed_compact_layout_enabled(policy)
            and len(degrees) == 4
        ):
            parent_closed = place_compact_closed_seed_layout(root_pc, degrees, policy)
            if parent_closed:
                parent_closed_candidates = [parent_closed]
        named_open_selection = (
            place_named_open_projection_from_closed_parents(parent_closed_candidates, policy, spec.open_method)
            if parent_closed_candidates and spec.open_method is not None
            else None
        )
        placed = named_open_selection.placed if named_open_selection is not None else []
        parent_closed = named_open_selection.parent_closed if named_open_selection is not None else parent_closed
        if placed:
            legacy_callback_used = False
            migrated_projection_path = (
                "core.voicing.disposition.open."
                f"place_{spec.open_method.value}_projection_project_then_filter"
            )
        else:
            placed = []
    else:
        placed = legacy_placement_callback()

    # Local import avoids a runtime cycle: policy.py imports the public
    # disposition taxonomy, while this facade still delegates non-migrated
    # placement/debug helpers until later v2_2_x passes remove those paths.
    from jammate_engine.core.voicing.disposition.facade import describe_disposition_placement

    disposition_guard = (
        describe_disposition_placement(placed, legacy_disposition, policy)
        if placed
        else {
            "disposition": legacy_disposition.value,
            "placed_degrees": [],
            "placed_notes": [],
            "projection_empty": True,
        }
    )
    if migrated_projection_path:
        disposition_guard["migrated_projection_path"] = migrated_projection_path
    projection_debug = spec.to_debug_dict()
    metadata: dict[str, object] = {
        "disposition_projection_spec": projection_debug,
        "disposition_projection_family": spec.family.value,
        "disposition_projection_method": spec.method_value,
        "disposition_projection_entry": "core.voicing.disposition.projection.project_source_to_disposition",
        "legacy_projection_callback_used": legacy_callback_used,
        "legacy_projection_cleanup_required": legacy_callback_used,
    }
    if migrated_projection_path:
        metadata["migrated_projection_path"] = migrated_projection_path
        if spec.family == DispositionFamily.CLOSED:
            metadata["closed_projection_migrated"] = True
        if spec.family == DispositionFamily.OPEN and spec.open_method in {
            OpenProjectionMethod.DROP2,
            OpenProjectionMethod.DROP3,
            OpenProjectionMethod.DROP2_AND_4,
        }:
            metadata["open_named_projection_migrated"] = True
            metadata[f"open_{spec.open_method.value}_projection_migrated"] = True
            if spec.open_method == OpenProjectionMethod.DROP2:
                metadata["open_drop2_projection_migrated"] = True
            metadata.update(
                named_open_projection_metadata(
                    placed,
                    spec.open_method,
                    parent_closed if 'parent_closed' in locals() else None,
                    parent_index=(named_open_selection.parent_index if 'named_open_selection' in locals() and named_open_selection is not None else None),
                    parent_candidate_count=(named_open_selection.candidate_count if 'named_open_selection' in locals() and named_open_selection is not None else None),
                    projected_candidate_count=(named_open_selection.projected_candidate_count if 'named_open_selection' in locals() and named_open_selection is not None else None),
                    legal_candidate_count=(named_open_selection.legal_candidate_count if 'named_open_selection' in locals() and named_open_selection is not None else None),
                    policy=policy,
                )
            )
    return DispositionProjectionResult(
        placed=tuple((str(degree), int(note)) for degree, note in placed),
        spec=spec,
        disposition_guard=disposition_guard,
        metadata=metadata,
    )


def _resolve_projection_spec(
    legacy_disposition: Disposition,
    policy: "VoicingPolicy",
):
    """Return the active projection spec for one request.

    v2_2_5 keeps legacy Disposition.OPEN as GENERIC_OPEN by default.  DROP2 is
    available only through explicit policy metadata so listening/isolation tests
    can exercise the parent-closed-derived open method without changing style defaults.
    """

    spec = projection_spec_from_legacy_disposition(legacy_disposition)
    metadata = dict(getattr(policy, "metadata", None) or {})
    requested = metadata.get("active_open_projection_method")
    if requested is None:
        requested = metadata.get("open_projection_method") or metadata.get("disposition_open_projection_method")
    method = coerce_open_projection_method(requested)
    if legacy_disposition == Disposition.OPEN and method is not None:
        runtime_path = "core.voicing.disposition.open.place_generic_open_projection"
        if method in {OpenProjectionMethod.DROP2, OpenProjectionMethod.DROP3, OpenProjectionMethod.DROP2_AND_4}:
            runtime_path = f"core.voicing.disposition.open.place_{method.value}_projection_from_closed_parent"
        return replace(
            spec,
            open_method=method,
            legacy_runtime_path=runtime_path,
            migration_note=(
                "v2_2_7 explicit OPEN method route: active method is selected "
                "from policy metadata or the OPEN method candidate pool; default OPEN remains GENERIC_OPEN."
            ),
        )
    return spec
