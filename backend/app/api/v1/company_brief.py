from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Company, Interview

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/{company_id}/pre-interview-brief")
def get_pre_interview_brief(
    company_id: str, round: int = 1, db: Session = Depends(get_db)
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    interviews = (
        db.query(Interview)
        .filter(Interview.company_id == company_id)
        .order_by(Interview.round.asc())
        .all()
    )

    weak_points: dict[str, dict] = {}
    previous_questions = []
    next_round_predictions = []

    for iv in interviews:
        analysis = iv.ai_analysis if isinstance(iv.ai_analysis, dict) else {}
        for wp in analysis.get("weak_points", []):
            if wp not in weak_points:
                weak_points[wp] = {"count": 0, "scores": []}
            weak_points[wp]["count"] += 1
            for q in analysis.get("questions", []):
                if isinstance(q, dict) and "score" in q:
                    weak_points[wp]["scores"].append(q["score"])
        for q in analysis.get("questions", []):
            if isinstance(q, dict):
                previous_questions.append(q)
        for pred in analysis.get("next_round_prediction", []):
            if pred not in next_round_predictions:
                next_round_predictions.append(pred)

    top_weak = sorted(weak_points.items(), key=lambda x: x[1]["count"], reverse=True)[
        :5
    ]
    top_weak_summary = []
    for wp, data in top_weak:
        avg = (
            round(sum(data["scores"]) / len(data["scores"]), 1) if data["scores"] else 0
        )
        top_weak_summary.append({"point": wp, "avg_score": avg, "count": data["count"]})

    if top_weak_summary:
        weak_str = ", ".join(
            f"{w['point']}({w['avg_score']}/10)" for w in top_weak_summary[:3]
        )
        quick_review = f"重点复习: {weak_str}"
    else:
        quick_review = "暂无历史复盘数据，建议复习岗位 JD 核心技术要求"

    return {
        "company": company.name,
        "position": company.position,
        "next_round": round,
        "previous_weak_points": top_weak_summary,
        "previous_questions": previous_questions[-5:],
        "next_round_prediction": next_round_predictions[:5],
        "quick_review": quick_review,
    }
