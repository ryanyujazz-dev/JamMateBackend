from __future__ import annotations

from enum import Enum


SPREAD_RECIPE_CONTRACT_VERSION = "v2_2_40"


class SpreadGrouping(str, Enum):
    """Abstract SPREAD grouping shapes, expressed as lower+upper roles.

    These values mirror core voicing ``FunctionalGrouping`` strings but live in
    the SPREAD projection module so the notes/projection contract can be audited
    without importing higher-level policy objects and creating a circular import.
    """

    ONE_PLUS_THREE = "1+3"
    TWO_PLUS_TWO = "2+2"
    ONE_PLUS_FOUR = "1+4"
    TWO_PLUS_THREE = "2+3"
    TWO_PLUS_FOUR = "2+4"
    THREE_PLUS_THREE = "3+3"
    THREE_PLUS_FOUR = "3+4"


class SpreadUpperSourceKind(str, Enum):
    """Kind of reusable upper material referenced by a SPREAD recipe."""

    TWO_NOTE_CONTENT_SOURCE = "two_note_content_source"
    THREE_NOTE_CONTENT_SOURCE = "three_note_content_source"
    FOUR_NOTE_CONTENT_SOURCE = "four_note_content_source"
    DROP_FAMILY_DERIVED_PROJECTION_BLOCK = "drop_family_derived_projection_block"


class SpreadReuseStatus(str, Enum):
    """Audit status for source/projection reuse before new construction."""

    REUSE_READY = "reuse_ready"
    ADAPTER_REQUIRED = "adapter_required"
    NOT_REUSABLE = "not_reusable"


