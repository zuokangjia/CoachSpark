from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from collections import Counter

from app.db.session import get_db
from app.db.models import Company, Interview

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    companies = db.query(Company).all()
    interviews = db.query(Interview).all()

    status_counts = Counter(c.status for c in companies)

    all_weak: dict[str, int] = {}
    for iv in interviews:
        analysis = iv.ai_analysis if isinstance(iv.ai_analysis, dict) else {}
        for wp in analysis.get("weak_points", []):
            all_weak[wp] = all_weak.get(wp, 0) + 1

    top_weak = sorted(all_weak.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_companies": len(companies),
        "applied": status_counts.get("applied", 0),
        "interviewing": status_counts.get("interviewing", 0),
        "rejected": status_counts.get("rejected", 0),
        "total_interviews": len(interviews),
        "top_weak_points": top_weak,
    }


@router.get("/today")
def get_today_briefing(db: Session = Depends(get_db)):
    today = date.today()
    tomorrow = today + timedelta(days=1)

    upcoming = (
        db.query(Interview, Company)
        .join(Company, Interview.company_id == Company.id)
        .filter(
            Interview.interview_date >= today,
            Interview.interview_date <= tomorrow + timedelta(days=7),
        )
        .order_by(Interview.interview_date.asc())
        .all()
    )
    upcoming_interviews = [
        {
            "company": c.name,
            "position": c.position,
            "round": iv.round,
            "date": str(iv.interview_date),
            "days_until": (iv.interview_date - today).days,
        }
        for iv, c in upcoming
    ]

    pending_results = (
        db.query(Interview, Company)
        .join(Company, Interview.company_id == Company.id)
        .filter(
            Interview.expected_result_date.isnot(None),
            Interview.expected_result_date < today,
            Interview.result_status == "pending",
        )
        .all()
    )
    pending_list = [
        {
            "company": c.name,
            "round": iv.round,
            "expected_date": str(iv.expected_result_date),
            "days_overdue": (today - iv.expected_result_date).days,
        }
        for iv, c in pending_results
    ]

    unreviewed = (
        db.query(Interview, Company)
        .join(Company, Interview.company_id == Company.id)
        .filter(
            Interview.ai_analysis == {},
            Interview.interview_date.isnot(None),
            Interview.interview_date < today - timedelta(days=2),
        )
        .all()
    )
    unreviewed_list = [
        {
            "company": c.name,
            "round": iv.round,
            "interview_date": str(iv.interview_date),
            "days_since": (today - iv.interview_date).days,
        }
        for iv, c in unreviewed
    ]

    return {
        "upcoming_interviews": upcoming_interviews,
        "pending_results": pending_list,
        "unreviewed": unreviewed_list,
    }
