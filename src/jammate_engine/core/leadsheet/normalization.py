from __future__ import annotations

from .models import Leadsheet


def normalize_leadsheet(leadsheet: Leadsheet) -> Leadsheet:
    # v2_0_6 keeps normalization minimal.
    return leadsheet
