from __future__ import annotations

from jammate_agent.capabilities.practice.models import PracticePlan


class PracticePlanGuardrails:
    def normalize(self, plan: PracticePlan) -> PracticePlan:
        if plan.blocks:
            diff = plan.duration_minutes - sum(block.duration_minutes for block in plan.blocks)
            plan.blocks[-1].duration_minutes = max(1, plan.blocks[-1].duration_minutes + diff)
        return plan

    def validate(self, plan: PracticePlan) -> list[str]:
        errors: list[str] = []
        if not plan.blocks:
            errors.append("PracticePlan must contain at least one ExerciseBlock.")
        if sum(block.duration_minutes for block in plan.blocks) != plan.duration_minutes:
            errors.append("Block durations must sum to plan duration.")
        return errors
