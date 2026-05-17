from __future__ import annotations

from .models import (
    AccompanimentPracticeConfig,
    ExerciseBlock,
    ExerciseBlockType,
    PracticeMaterial,
    PracticePlan,
)


class PracticePlanner:
    """P0 deterministic planner for JamMate Agent.

    This planner is intentionally LLM-free. It provides a stable fallback and a
    JSON-compatible contract for HarmonyOS before the LLM planner is added.
    """

    def build_plan(
        self,
        user_input: str,
        available_minutes: int = 45,
        instrument: str = "piano",
    ) -> PracticePlan:
        tune = self._infer_tune(user_input)
        style = self._infer_style(user_input)
        text = user_input.lower()
        if "comping" in text or "伴奏" in user_input or "和声" in user_input:
            return self._comping_plan(tune, style, available_minutes)
        if "solo" in text or "即兴" in user_input:
            return self._solo_plan(tune, style, available_minutes)
        return self._balanced_plan(tune, style, available_minutes)

    def _comping_plan(self, tune: str | None, style: str, minutes: int) -> PracticePlan:
        tune_name = tune or "selected material"
        material = PracticeMaterial(type="tune", tune=tune) if tune else None
        a = max(8, round(minutes * 0.3))
        b = max(10, round(minutes * 0.55))
        r = max(3, minutes - a - b)
        blocks = [
            ExerciseBlock(
                type=ExerciseBlockType.VOICING,
                title=f"{tune_name} voicing continuity",
                intent="控制 lower foundation、voice-leading 与和声密度。",
                duration_minutes=a,
                material=material,
                tempo=76 if style == "jazz_ballad" else 110,
                style=style,
            ),
            ExerciseBlock(
                type=ExerciseBlockType.COMPING,
                title=f"{tune_name} comping with rhythm section",
                intent="关闭 piano 伴奏声部，跟 bass/drums 练 comping。",
                duration_minutes=b,
                material=material,
                tempo=76 if style == "jazz_ballad" else 110,
                style=style,
                accompaniment_config=AccompanimentPracticeConfig(
                    style=style,
                    tempo=76 if style == "jazz_ballad" else 110,
                    muted_roles=["piano"],
                    practice_role="piano_comping",
                ),
            ),
            ExerciseBlock(
                type=ExerciseBlockType.REVIEW,
                title="Review",
                intent="记录左手、密度、time feel 与卡点。",
                duration_minutes=r,
            ),
        ]
        self._fix_duration(blocks, minutes)
        return PracticePlan(
            title=f"{tune_name} Comping {minutes}",
            duration_minutes=minutes,
            main_focus=f"{tune_name} comping with controlled voicing and time feel",
            blocks=blocks,
            explanation="P0 rule-based JamMate Agent plan. LLM planner will later replace only the semantic planning step.",
        )

    def _solo_plan(self, tune: str | None, style: str, minutes: int) -> PracticePlan:
        tune_name = tune or "selected material"
        material = PracticeMaterial(type="tune", tune=tune) if tune else None
        a = max(8, round(minutes * 0.25))
        b = max(12, round(minutes * 0.6))
        r = max(4, minutes - a - b)
        blocks = [
            ExerciseBlock(
                type=ExerciseBlockType.GUIDE_TONE,
                title=f"{tune_name} guide-tone map",
                intent="先听到并连接 3/7，再进入完整即兴。",
                duration_minutes=a,
                material=material,
                tempo=100,
                style=style,
            ),
            ExerciseBlock(
                type=ExerciseBlockType.IMPROVISATION,
                title=f"{tune_name} solo lab",
                intent="使用 rhythm section 伴奏练多遍，即兴时避免只跑音阶。",
                duration_minutes=b,
                material=material,
                tempo=100,
                style=style,
                accompaniment_config=AccompanimentPracticeConfig(
                    style=style,
                    tempo=100,
                    muted_roles=["melody"],
                    practice_role="solo_improvisation",
                ),
            ),
            ExerciseBlock(type=ExerciseBlockType.REVIEW, title="Review", intent="标记最好/最卡的段落。", duration_minutes=r),
        ]
        self._fix_duration(blocks, minutes)
        return PracticePlan(
            title=f"{tune_name} Improvisation {minutes}",
            duration_minutes=minutes,
            main_focus=f"{tune_name} improvisation with guide-tone and phrase focus",
            blocks=blocks,
            explanation="P0 rule-based JamMate Agent plan.",
        )

    def _balanced_plan(self, tune: str | None, style: str, minutes: int) -> PracticePlan:
        tune_name = tune or "Jazz"
        material = PracticeMaterial(type="tune", tune=tune) if tune else None
        blocks = [
            ExerciseBlock(type=ExerciseBlockType.TECHNIQUE, title="Sound / Warmup", intent="稳定触键、音色与节奏入口。", duration_minutes=max(5, round(minutes * 0.12))),
            ExerciseBlock(type=ExerciseBlockType.GUIDE_TONE, title="Guide Tone Map", intent="明确和声目标音。", duration_minutes=max(8, round(minutes * 0.22)), material=material, style=style),
            ExerciseBlock(type=ExerciseBlockType.VOICING, title="Voicing / Comping", intent="把和声落成可演奏的伴奏语汇。", duration_minutes=max(8, round(minutes * 0.26)), material=material, style=style),
            ExerciseBlock(type=ExerciseBlockType.IMPROVISATION, title="Improvisation Lab", intent="在真实伴奏环境里应用材料。", duration_minutes=max(8, round(minutes * 0.3)), material=material, style=style),
            ExerciseBlock(type=ExerciseBlockType.REVIEW, title="Review", intent="复盘本次练习并确定下一步。", duration_minutes=5),
        ]
        self._fix_duration(blocks, minutes)
        return PracticePlan(title=f"{tune_name} Practice {minutes}", duration_minutes=minutes, main_focus="balanced jazz practice session", blocks=blocks, explanation="P0 rule-based balanced plan.")

    def _fix_duration(self, blocks: list[ExerciseBlock], target: int) -> None:
        if not blocks:
            return
        diff = target - sum(b.duration_minutes for b in blocks)
        blocks[-1].duration_minutes = max(1, blocks[-1].duration_minutes + diff)

    def _infer_style(self, text: str) -> str:
        lower = text.lower()
        if "bossa" in lower or "波萨" in text:
            return "bossa_nova"
        if "ballad" in lower or "misty" in lower or "抒情" in text:
            return "jazz_ballad"
        return "medium_swing"

    def _infer_tune(self, text: str) -> str | None:
        known = ["All The Things You Are", "Autumn Leaves", "Blue Bossa", "Misty", "Minimal Ii V I"]
        lower = text.lower()
        for tune in known:
            if tune.lower() in lower:
                return tune
        return None
