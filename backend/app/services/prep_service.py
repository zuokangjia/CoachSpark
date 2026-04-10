import asyncio
import copy
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.graphs.prep_graph import build_prep_graph
from app.services.context_builder import ContextBuilder
from app.db.models import PrepPlan, generate_uuid
from app.core.logging import logger

_prep_graph = None

"""
Design: Personalized Prep Plan Generation
核心思想：根据用户薄弱点和 JD 方向，通过 prep_graph 生成按日拆分的备战计划。
每日的任务通过优先级和 LLM 推理分配，确保薄弱点优先被覆盖。
支持任务完成进度跟踪（completed_task_indexes），实现增量更新。
"""


def get_prep_graph():
    global _prep_graph
    if _prep_graph is None:
        _prep_graph = build_prep_graph()
    return _prep_graph


async def generate_prep_plan(
    db: Session,
    company_id: str,
    target_round: int,
    days_available: int,
    weak_points: list | None = None,
    jd_directions: list | None = None,
    interview_chain: list | None = None,
) -> dict:
    graph = get_prep_graph()

    cb = ContextBuilder(db)
    context = cb.build_prep_context(company_id)

    try:
        result = await asyncio.to_thread(
            graph.invoke,
            {
                "company_id": company_id,
                "target_round": target_round,
                "days_available": days_available,
                "weak_points": weak_points or [],
                "jd_directions": jd_directions or [],
                "interview_chain": interview_chain or [],
                "context": context,
                "daily_tasks": [],
            }
        )
    except Exception as e:
        logger.error(f"Prep plan generation failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI analysis service is temporarily unavailable. Please try again later.",
        )
    daily_tasks = result.get("daily_tasks", [])

    plan = PrepPlan(
        id=generate_uuid(),
        company_id=company_id,
        target_round=target_round,
        days_available=days_available,
        daily_tasks=daily_tasks,
        generated_from=[str(wp) for wp in (weak_points or [])],
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    return {
        "prep_plan_id": plan.id,
        "daily_tasks": daily_tasks,
    }


def get_latest_prep_plan(db: Session, company_id: str) -> dict | None:
    plan = (
        db.query(PrepPlan)
        .filter(PrepPlan.company_id == company_id)
        .order_by(PrepPlan.created_at.desc())
        .first()
    )
    if not plan:
        return None
    return {
        "prep_plan_id": plan.id,
        "company_id": plan.company_id,
        "target_round": plan.target_round,
        "days_available": plan.days_available,
        "daily_tasks": plan.daily_tasks,
        "created_at": plan.created_at,
    }


def update_prep_task_completion(
    db: Session,
    prep_plan_id: str,
    day: int,
    task_index: int,
    completed: bool,
) -> dict:
    plan = db.query(PrepPlan).filter(PrepPlan.id == prep_plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Prep plan not found")

    raw_daily_tasks = getattr(plan, "daily_tasks", [])
    daily_tasks: list[dict[str, Any]] = (
        copy.deepcopy(raw_daily_tasks) if isinstance(raw_daily_tasks, list) else []
    )
    target_day = None
    for item in daily_tasks:
        if isinstance(item, dict) and int(item.get("day", -1)) == day:
            target_day = item
            break

    if not target_day:
        raise HTTPException(status_code=404, detail="Day task not found")

    tasks = target_day.get("tasks", [])
    if not isinstance(tasks, list) or task_index >= len(tasks):
        raise HTTPException(status_code=400, detail="Task index out of range")

    completed_indexes = target_day.get("completed_task_indexes", [])
    if not isinstance(completed_indexes, list):
        completed_indexes = []

    normalized_indexes = sorted(
        {
            int(idx)
            for idx in completed_indexes
            if isinstance(idx, int) and 0 <= idx < len(tasks)
        }
    )

    if completed and task_index not in normalized_indexes:
        normalized_indexes.append(task_index)
    elif not completed and task_index in normalized_indexes:
        normalized_indexes.remove(task_index)

    normalized_indexes = sorted(normalized_indexes)
    target_day["completed_task_indexes"] = normalized_indexes
    target_day["completed"] = len(tasks) > 0 and len(normalized_indexes) == len(tasks)

    setattr(plan, "daily_tasks", daily_tasks)
    db.commit()

    return {
        "prep_plan_id": plan.id,
        "daily_tasks": daily_tasks,
    }
