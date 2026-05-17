from __future__ import annotations

from dataclasses import replace

from jammate_engine.core.anticipation import AnticipationPolicy
from jammate_engine.core.voicing import ContentFamily, Disposition, RootSupportPolicy
from jammate_engine.styles.base import StylePolicyBundle, StyleProfile

from . import anticipation_policy, arrangement_policy, bass_foundation_patterns, percussion_patterns, expression_policy, comping_patterns, voicing_policy, gesture_policy


class MediumSwingProfile(StyleProfile):
    def __init__(self) -> None:
        super().__init__(
            name="medium_swing",
            policies=StylePolicyBundle(
                expression_policy=expression_policy.get_expression_policy(),
                anticipation_policy=anticipation_policy.get_anticipation_policy(),
                voicing_policy=voicing_policy.get_voicing_policy(),
                gesture_policy=gesture_policy.get_gesture_policy(),
                arrangement_policy=arrangement_policy.get_arrangement_policy(),
                bass_foundation_policy=bass_foundation_patterns.get_bass_foundation_policy(),
                timing_policy={
                    "version": "v2_0_43",
                    "feel": "swing",
                    "swing_ratio": 2.0 / 3.0,
                    "half_beat_grid": 0.5,
                    "humanization": {
                        "enabled": False,
                        "max_offset_beats": 0.0,
                        "velocity_jitter": 0,
                        "affect_tracks": ["piano", "bass"],
                        "profile_name": "medium_swing_disabled_default",
                    },
                    "boundary": "timing_policy_only_no_pattern_voicing_expression_content",
                    "metadata": {"style": "medium_swing", "stage": "v2_0_43_timing_policy_contract"},
                },
            ),
            pattern_sources=(
                comping_patterns.get_pattern_candidates,
                bass_foundation_patterns.get_pattern_candidates,
                percussion_patterns.get_pattern_candidates,
            ),
            bass_foundation_source=bass_foundation_patterns.get_pattern_candidates,
        )


class MediumSwingVoicingTuningProfile(StyleProfile):
    """Temporary Medium Swing voicing-isolation profile.

    This profile freezes piano rhythm to one region-start onset and forces the
    current tuning target to 2-note shell voicings. It exists for audible
    voicing review and should not be used as the normal Medium Swing default.
    """

    def __init__(self) -> None:
        base_expression = expression_policy.get_expression_policy()
        base_voicing = voicing_policy.get_voicing_policy()
        tuning_voicing = replace(
            base_voicing,
            root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
            allowed_content=(ContentFamily.SHELL,),
            preferred_content=ContentFamily.SHELL,
            content_family_weights={},
            preferred_disposition=Disposition.CLOSED,
            allowed_dispositions=(Disposition.CLOSED, Disposition.OPEN),
            preferred_density=2,
            min_density=2,
            max_density=2,
            register_low=52,
            register_high=72,
            right_hand_low=54,
            right_hand_high=72,
            top_voice_low=56,
            top_voice_high=72,
            comfort_register_low=54,
            comfort_register_high=68,
            max_voicing_span=16,
            max_top_voice_leap=12,
            selector_temperature=0.0,
            selection_pool_size=1,
            metadata={
                **dict(base_voicing.metadata or {}),
                "style": "medium_swing_voicing_tuning",
                "tuning_mode": "voicing_isolation",
                "tuning_target": "2_note_shell",
                "pattern_rule": "one_piano_harmonic_event_at_region_start",
                "normal_style_default": False,
            },
        )
        super().__init__(
            name="medium_swing_voicing_tuning",
            policies=StylePolicyBundle(
                expression_policy=base_expression,
                anticipation_policy=AnticipationPolicy(enabled=False, debug_name="voicing_tuning_anticipation_disabled"),
                voicing_policy=tuning_voicing,
                gesture_policy=gesture_policy.get_gesture_policy(),
                arrangement_policy={
                    **arrangement_policy.get_arrangement_policy(),
                    "tuning_mode": "voicing_isolation",
                    "normal_style_default": False,
                    "pattern_selection": "region_start_only",
                    "voicing_target": "2_note_shell",
                },
                bass_foundation_policy={"enabled": False, "tuning_mode": "voicing_isolation"},
                timing_policy={
                    "version": "v2_1_0",
                    "feel": "swing",
                    "swing_ratio": 2.0 / 3.0,
                    "half_beat_grid": 0.5,
                    "humanization": {
                        "enabled": False,
                        "max_offset_beats": 0.0,
                        "velocity_jitter": 0,
                        "affect_tracks": ["piano"],
                        "profile_name": "medium_swing_voicing_tuning_disabled_default",
                    },
                    "boundary": "voicing_tuning_timing_only",
                    "metadata": {"style": "medium_swing_voicing_tuning", "stage": "v2_1_0_voicing_tuning"},
                },
            ),
            pattern_sources=(comping_patterns.get_voicing_tuning_anchor_only_candidates,),
            bass_foundation_source=None,
        )
