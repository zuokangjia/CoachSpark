from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.company import ReviewRequest, ReviewResponse
from app.services.review_service import analyze_review, save_review_and_update_profile

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/review", tags=["review-v2"])


@router.post("/analyze", response_model=ReviewResponse)
@limiter.limit("10/minute")
def run_review(request: Request, data: ReviewRequest, db: Session = Depends(get_db)):
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
            db=db,
            company_id=data.company_id,
            result=result,
            round_num=data.round,
            raw_notes=data.raw_notes,
            interview_id=data.interview_id,
            interview_date=data.interview_date,
            interview_format=data.interview_format,
            interviewer=data.interviewer,
        )

    response_data = {**result}
    if interview_id:
        response_data["interview_id"] = interview_id
    return response_data
