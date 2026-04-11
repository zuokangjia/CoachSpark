import asyncio
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.graphs.review_graph import build_review_graph
from app.services.context_builder import ContextBuilder
from app.services.persona_v2_service import (
    ingest_review_evidence,
    rebuild_persona_snapshot,
)
from app.db.models import Interview, Company, UserSkillState, generate_uuid
from app.core.logging import logger

_review_graph = None

"""
Design: Review Analysis Orchestration
核心思想：analyze_review 调用 review_graph 分析面试笔记，save_review_and_update_profile
负责持久化结果并触发 persona 系统更新（证据摄入 + 快照重建）。
采用异步 LangGraph 调用，避免阻塞 FastAPI 请求。
"""


def get_review_graph():
    global _review_graph
    if _review_graph is None:
        _review_graph = build_review_graph()
    return _review_graph


async def analyze_review(
    db: Session,
    raw_notes: str,
    company_name: str = "",
    position: str = "",
    round_num: int = 1,
    jd_key_points: list = None,
    company_id: str = "",
) -> dict:
    graph = get_review_graph()

    context = ""
    if company_id:
        cb = ContextBuilder(db)
        context = cb.build_review_context(company_id)

    try:
        payload = {
            "raw_notes": raw_notes,
            "company_name": company_name,
            "position": position,
            "round_num": round_num,
            "jd_key_points": jd_key_points or [],
            "context": context,
            "questions": [],
            "weak_points": [],
            "strong_points": [],
            "next_round_prediction": [],
            "interviewer_signals": [],
            "analysis_complete": False,
        }

        result = await asyncio.to_thread(graph.invoke, payload)
    except Exception as e:
        logger.error(f"Review analysis failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI analysis service is temporarily unavailable. Please try again later.",
        )

    # 获取当前画像快照（轻量，不新建 endpoint）
    from app.services.persona_v2_service import get_latest_persona
    persona = get_latest_persona(db)

    return {
        "questions": result.get("questions", []),
        "weak_points": result.get("weak_points", []),
        "strong_points": result.get("strong_points", []),
        "next_round_prediction": result.get("next_round_prediction", []),
        "interviewer_signals": result.get("interviewer_signals", []),
        "persona_snapshot": {
            "headline": persona.get("headline", ""),
            "key_weaknesses": persona.get("key_weaknesses", [])[:3],
            "key_strengths": persona.get("key_strengths", [])[:2],
            "dimensions": persona.get("dimensions", [])[:5],
        },
    }


def save_review_and_update_profile(
    db: Session,
    company_id: str,
    result: dict,
    round_num: int,
    raw_notes: str = "",
    interview_id: str = "",
    interview_date: str = "",
    interview_format: str = "",
    interviewer: str = "",
) -> dict:
    """
    Returns dict with:
      interview_id: 本次关联的面试记录 ID
      dimension_changes: 本次复盘影响的维度 level 变化
    """
    interview = None

    if interview_id:
        interview = db.query(Interview).filter(Interview.id == interview_id).first()

    if not interview:
        interview = (
            db.query(Interview)
            .filter(Interview.company_id == company_id, Interview.round == round_num)
            .first()
        )

    # 记录复盘前的维度状态
    before_dimensions = {}
    if interview:
        before_dims = (
            db.query(UserSkillState)
            .filter(UserSkillState.user_id == "default-user")
            .all()
        )
        for d in before_dims:
            before_dimensions[d.dimension] = d.level

    if interview:
        interview.raw_notes = raw_notes
        interview.ai_analysis = {
            "questions": result.get("questions", []),
            "weak_points": result.get("weak_points", []),
            "strong_points": result.get("strong_points", []),
            "next_round_prediction": result.get("next_round_prediction", []),
            "interviewer_signals": result.get("interviewer_signals", []),
        }
        if interview_date:
            interview.interview_date = date.fromisoformat(interview_date)
        if interview_format:
            interview.format = interview_format
        if interviewer:
            interview.interviewer = interviewer
    else:
        interview = Interview(
            id=generate_uuid(),
            company_id=company_id,
            round=round_num,
            raw_notes=raw_notes,
            ai_analysis={
                "questions": result.get("questions", []),
                "weak_points": result.get("weak_points", []),
                "strong_points": result.get("strong_points", []),
                "next_round_prediction": result.get("next_round_prediction", []),
                "interviewer_signals": result.get("interviewer_signals", []),
            },
        )
        if interview_date:
            interview.interview_date = date.fromisoformat(interview_date)
        if interview_format:
            interview.format = interview_format
        if interviewer:
            interview.interviewer = interviewer
        db.add(interview)

    company = db.query(Company).filter(Company.id == company_id).first()
    if company and company.status == "applied":
        company.status = "interviewing"

    db.commit()
    db.refresh(interview)

    ingest_review_evidence(
        db,
        interview_id=interview.id,
        round_num=interview.round,
        analysis=interview.ai_analysis
        if isinstance(interview.ai_analysis, dict)
        else {},
        raw_notes=interview.raw_notes or "",
    )
    rebuild_persona_snapshot(db, source_event_id=interview.id)

    # 计算维度变化
    after_dims = (
        db.query(UserSkillState)
        .filter(UserSkillState.user_id == "default-user")
        .all()
    )
    dimension_changes = []
    for d in after_dims:
        before_level = before_dimensions.get(d.dimension)
        if before_level is not None and before_level != d.level:
            dimension_changes.append({
                "dimension": d.dimension,
                "before": before_level,
                "after": d.level,
                "delta": d.level - before_level,
                "trend": d.trend,
            })

    return {
        "interview_id": interview.id,
        "dimension_changes": dimension_changes,
    }
