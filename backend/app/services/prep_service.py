from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.graphs.prep_graph import build_prep_graph
from app.services.context_builder import ContextBuilder
from app.db.models import PrepPlan, generate_uuid
from app.core.logging import logger

_prep_graph = None


def get_prep_graph():
    global _prep_graph
    if _prep_graph is None:
        _prep_graph = build_prep_graph()
    return _prep_graph


def generate_prep_plan(
    db: Session,
    company_id: str,
    target_round: int,
    days_available: int,
    weak_points: list = None,
    jd_directions: list = None,
    interview_chain: list = None,
) -> dict:
    graph = get_prep_graph()

    cb = ContextBuilder(db)
    context = cb.build_prep_context(company_id)

    try:
        result = graph.invoke(
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
        "id": plan.id,
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
        "id": plan.id,
        "company_id": plan.company_id,
        "target_round": plan.target_round,
        "days_available": plan.days_available,
        "daily_tasks": plan.daily_tasks,
        "created_at": plan.created_at,
    }
