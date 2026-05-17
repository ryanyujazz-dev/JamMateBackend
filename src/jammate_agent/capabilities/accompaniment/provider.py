from __future__ import annotations

from typing import Protocol

from .models import AccompanimentAsset, AccompanimentRequest


class AccompanimentProvider(Protocol):
    def generate(self, request: AccompanimentRequest) -> AccompanimentAsset:
        ...
