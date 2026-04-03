from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.company import PrepRequest, PrepResponse
from app.services.prep_service import generate_prep_plan, get_latest_prep_plan

router = APIRouter(prefix="/prep", tags=["ai"])


@router.post("/generate", response_model=PrepResponse)
def run_prep(data: PrepRequest, db: Session = Depends(get_db)):
    result = generate_prep_plan(
        db=db,
        company_id=data.company_id,
        target_round=data.target_round,
        days_available=data.days_available,
        weak_points=data.weak_points,
        jd_directions=data.jd_directions,
        interview_chain=data.interview_chain,
    )
    return result


@router.get("/latest/{company_id}")
def get_latest(company_id: str, db: Session = Depends(get_db)):
    plan = get_latest_prep_plan(db, company_id)
    if not plan:
        return {"daily_tasks": []}
    return plan
