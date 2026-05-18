from __future__ import annotations

from jammate_agent.capabilities.practice.models import PracticePlan


class PracticePlanGuardrails:
    def normalize(self, plan: PracticePlan) -> PracticePlan:
        if not plan.blocks:
            return plan
        target = max(len(plan.blocks), int(plan.duration_minutes))
        plan.duration_minutes = target
        diff = target - sum(block.duration_minutes for block in plan.blocks)
        if diff >= 0:
            plan.blocks[-1].duration_minutes += diff
            return plan

        # Remove excess minutes from later blocks first while preserving a
        # one-minute minimum per block. This keeps short Routine plans valid
        # even when planner templates used conservative per-block minimums.
        remaining_to_remove = -diff
        for block in reversed(plan.blocks):
            if remaining_to_remove <= 0:
                break
            removable = max(0, block.duration_minutes - 1)
            removed = min(removable, remaining_to_remove)
            block.duration_minutes -= removed
            remaining_to_remove -= removed
        return plan

    def validate(self, plan: PracticePlan) -> list[str]:
        errors: list[str] = []
        if not plan.blocks:
            errors.append("PracticePlan must contain at least one ExerciseBlock.")
        if sum(block.duration_minutes for block in plan.blocks) != plan.duration_minutes:
            errors.append("Block durations must sum to plan duration.")
        return errors
