from __future__ import annotations

from .models import NextStepRecommendation, SessionReview


class ReviewEngine:
    def recommend_next_step(self, review: SessionReview) -> NextStepRecommendation:
        if review.tempo_result and review.tempo_result.get("stable") and review.tempo_result.get("tempo"):
            next_tempo = int(review.tempo_result["tempo"]) + 10
            return NextStepRecommendation(
                summary=f"本次 tempo {review.tempo_result['tempo']} 已较稳定，下次可以尝试升到 {next_tempo}。",
                actions=[{"type": "raise_tempo", "target_tempo": next_tempo}],
            )
        if review.difficulty == "too_hard":
            return NextStepRecommendation(summary="本次难度偏高，下次建议降速或缩小练习片段。", actions=[{"type": "lower_tempo_or_narrow_section"}])
        if review.stuck_points:
            return NextStepRecommendation(summary="本次有明确卡点，下次建议围绕卡点小段循环练习。", actions=[{"type": "repeat_focus_section"}])
        return NextStepRecommendation(summary="本次完成情况正常，下次可以延续当前方向。", actions=[{"type": "continue"}])
