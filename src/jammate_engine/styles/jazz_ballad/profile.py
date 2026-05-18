from __future__ import annotations

from jammate_engine.styles.base import StylePolicyBundle, StyleProfile

from . import anticipation_policy, bass_foundation_patterns, percussion_patterns, expression_policy, comping_patterns, voicing_policy, gesture_policy


class JazzBalladProfile(StyleProfile):
    def __init__(self) -> None:
        super().__init__(
            name="jazz_ballad",
            policies=StylePolicyBundle(
                expression_policy=expression_policy.get_expression_policy(),
                anticipation_policy=anticipation_policy.get_anticipation_policy(),
                voicing_policy=voicing_policy.get_voicing_policy(),
                gesture_policy=gesture_policy.get_gesture_policy(),
                timing_policy={
                    "version": "v2_0_43",
                    "feel": "swing",
                    "humanization": {"enabled": False, "profile_name": "jazz_ballad_swing8_disabled_default"},
                    "boundary": "timing_policy_only_no_pattern_voicing_expression_content",
                    "metadata": {"style": "jazz_ballad", "stage": "v2_5_9_ballad_default_swing8_timing"},
                },
                arrangement_policy={"default_feel": "jazz_ballad", "avoid_full_bar_silence": True},
            ),
            pattern_sources=(
                comping_patterns.get_pattern_candidates,
                bass_foundation_patterns.get_pattern_candidates,
                percussion_patterns.get_pattern_candidates,
            ),
        )
