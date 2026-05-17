from __future__ import annotations

from datetime import datetime

from .models import PracticePlan, PracticeSession, PracticeSessionStatus


class PracticeSessionEngine:
    def start_from_plan(self, plan: PracticePlan) -> PracticeSession:
        return PracticeSession(
            plan_id=plan.plan_id,
            started_at=datetime.now(),
            status=PracticeSessionStatus.ACTIVE,
            total_planned_minutes=plan.duration_minutes,
            current_block_id=plan.blocks[0].block_id if plan.blocks else None,
            blocks=plan.blocks,
        )
