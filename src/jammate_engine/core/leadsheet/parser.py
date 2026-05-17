from __future__ import annotations

from .models import Leadsheet
from .validation import validate_leadsheet_document


def parse_leadsheet(data: dict) -> Leadsheet:
    validate_leadsheet_document(data)
    return Leadsheet.from_dict(data)
