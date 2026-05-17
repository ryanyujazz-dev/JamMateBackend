from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MelodicVocabularyEntry:
    """Future solo/melodic-foreground vocabulary entry.

    This package is intentionally solo-only. Accompaniment vocabulary remains in
    style-owned pattern files.
    """

    name: str
    degrees: tuple[str, ...]
    tags: tuple[str, ...] = field(default_factory=tuple)
    weight: float = 1.0
