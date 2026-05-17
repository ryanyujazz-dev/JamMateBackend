from __future__ import annotations

from jammate_engine.styles.base import StyleProfile
from jammate_engine.styles.medium_swing.profile import MediumSwingProfile, MediumSwingVoicingTuningProfile
from jammate_engine.styles.bossa_nova.profile import BossaNovaProfile
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile


def get_style(name: str) -> StyleProfile:
    styles = {
        "medium_swing": MediumSwingProfile(),
        "medium_swing_voicing_tuning": MediumSwingVoicingTuningProfile(),
        "bossa_nova": BossaNovaProfile(),
        "jazz_ballad": JazzBalladProfile(),
    }
    if name not in styles:
        raise ValueError(f"Unknown style: {name}")
    return styles[name]
