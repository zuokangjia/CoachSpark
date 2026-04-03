from fastapi import APIRouter

from app.models.company import PrepRequest, PrepResponse
from app.services.prep_service import generate_prep_plan

router = APIRouter(prefix="/prep", tags=["ai"])


@router.post("/generate", response_model=PrepResponse)
def run_prep(data: PrepRequest):
    result = generate_prep_plan(
        company_id=data.company_id,
        target_round=data.target_round,
        days_available=data.days_available,
        weak_points=data.weak_points,
        jd_directions=data.jd_directions,
        interview_chain=data.interview_chain,
    )
    return result
