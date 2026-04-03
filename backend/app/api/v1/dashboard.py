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
        "closed": status_counts.get("closed", 0),
        "total_interviews": len(interviews),
        "top_weak_points": top_weak,
    }
