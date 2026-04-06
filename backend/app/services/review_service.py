from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.graphs.review_graph import build_review_graph
from app.services.context_builder import ContextBuilder
from app.services.profile_service import update_profile_incremental
from app.db.models import Interview, Company, generate_uuid
from app.core.logging import logger

_review_graph = None


def get_review_graph():
    global _review_graph
    if _review_graph is None:
        _review_graph = build_review_graph()
    return _review_graph


def analyze_review(
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
        result = graph.invoke(
            {
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
        )
    except Exception as e:
        logger.error(f"Review analysis failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI analysis service is temporarily unavailable. Please try again later.",
        )
    return {
        "questions": result.get("questions", []),
        "weak_points": result.get("weak_points", []),
        "strong_points": result.get("strong_points", []),
        "next_round_prediction": result.get("next_round_prediction", []),
        "interviewer_signals": result.get("interviewer_signals", []),
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
) -> str:
    interview = None

    if interview_id:
        interview = db.query(Interview).filter(Interview.id == interview_id).first()

    if not interview:
        interview = (
            db.query(Interview)
            .filter(Interview.company_id == company_id, Interview.round == round_num)
            .first()
        )

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

    update_profile_incremental(db, interview.id)
    return interview.id
