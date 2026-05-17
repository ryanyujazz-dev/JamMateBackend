"""Legacy compatibility schemas.

The active public API schemas now live in `jammate_api.schemas`.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiGenerationRequest:
    payload: dict
