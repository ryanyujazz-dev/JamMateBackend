from __future__ import annotations

from jammate_engine.styles.base import StylePolicyBundle, StyleProfile

from . import anticipation_policy, arrangement_policy, bass_foundation_patterns, percussion_patterns, expression_policy, comping_patterns, voicing_policy, gesture_policy


class BossaNovaProfile(StyleProfile):
    def __init__(self) -> None:
        super().__init__(
            name="bossa_nova",
            policies=StylePolicyBundle(
                expression_policy=expression_policy.get_expression_policy(),
                anticipation_policy=anticipation_policy.get_anticipation_policy(),
                voicing_policy=voicing_policy.get_voicing_policy(),
                gesture_policy=gesture_policy.get_gesture_policy(),
                timing_policy={
                    "version": "v2_0_43",
                    "feel": "straight",
                    "humanization": {"enabled": False, "profile_name": "bossa_nova_disabled_default"},
                    "boundary": "timing_policy_only_no_pattern_voicing_expression_content",
                    "metadata": {"style": "bossa_nova", "stage": "v2_0_43_timing_policy_contract"},
                },
                arrangement_policy=arrangement_policy.get_arrangement_policy(),
            ),
            pattern_sources=(
                comping_patterns.get_pattern_candidates,
                bass_foundation_patterns.get_pattern_candidates,
                percussion_patterns.get_pattern_candidates,
            ),
        )
