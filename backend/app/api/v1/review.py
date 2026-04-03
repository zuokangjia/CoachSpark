from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.company import ReviewRequest, ReviewResponse
from app.services.review_service import analyze_review, save_review_and_update_profile

router = APIRouter(prefix="/review", tags=["ai"])


@router.post("/analyze", response_model=ReviewResponse)
def run_review(data: ReviewRequest, db: Session = Depends(get_db)):
    result = analyze_review(
        db=db,
        raw_notes=data.raw_notes,
        company_name=data.company_name,
        position=data.position,
        round_num=data.round,
        jd_key_points=data.jd_key_points,
        company_id=data.company_id,
    )

    interview_id = None
    if data.company_id:
        interview_id = save_review_and_update_profile(
            db, data.company_id, result, data.round
        )

    response_data = {**result}
    if interview_id:
        response_data["interview_id"] = interview_id
    return response_data
