from fastapi import APIRouter

from app.models.company import ReviewRequest, ReviewResponse
from app.services.review_service import analyze_review

router = APIRouter(prefix="/review", tags=["ai"])


@router.post("/analyze", response_model=ReviewResponse)
def run_review(data: ReviewRequest):
    result = analyze_review(
        raw_notes=data.raw_notes,
        company_name=data.company_name,
        position=data.position,
        round_num=data.round,
        jd_key_points=data.jd_key_points,
    )
    return result
