from __future__ import annotations

from fastapi import APIRouter

from jammate_agent.capabilities.practice.models import ExerciseBlock, ExerciseBlockType

router = APIRouter(prefix="/practice", tags=["practice"])


@router.get("/routines/templates")
def list_routine_templates() -> dict:
    # P0 template response is intentionally JSON-only so HarmonyOS can cache it.
    return {
        "ok": True,
        "routines": [
            {
                "routine_id": "routine_jazz_daily_30",
                "title": "Jazz Daily 30",
                "description": "30分钟基础爵士日常练习。",
                "source": "system_template",
                "total_duration_minutes": 30,
                "blocks": [
                    ExerciseBlock(type=ExerciseBlockType.TECHNIQUE, title="Sound / Warmup", intent="建立声音与手感", duration_minutes=5).to_dict(),
                    ExerciseBlock(type=ExerciseBlockType.GUIDE_TONE, title="Guide Tone", intent="连接和声骨架", duration_minutes=8).to_dict(),
                    ExerciseBlock(type=ExerciseBlockType.IMPROVISATION, title="Short Solo Lab", intent="把材料放进伴奏语境", duration_minutes=12).to_dict(),
                    ExerciseBlock(type=ExerciseBlockType.REVIEW, title="Review", intent="记录问题与下次动作", duration_minutes=5).to_dict(),
                ],
                "tags": ["jazz", "daily", "balanced"],
            },
            {
                "routine_id": "routine_comping_focus_30",
                "title": "Comping Focus 30",
                "description": "30分钟钢琴伴奏专项。",
                "source": "system_template",
                "total_duration_minutes": 30,
                "blocks": [
                    ExerciseBlock(type=ExerciseBlockType.VOICING, title="Voicing Continuity", intent="控制和声连接与音区", duration_minutes=10).to_dict(),
                    ExerciseBlock(type=ExerciseBlockType.COMPING, title="Comping With Rhythm Section", intent="在 bass/drums 中练伴奏", duration_minutes=15).to_dict(),
                    ExerciseBlock(type=ExerciseBlockType.REVIEW, title="Review", intent="记录左手、密度、time feel 问题", duration_minutes=5).to_dict(),
                ],
                "tags": ["jazz", "comping", "piano"],
            },
        ],
    }
