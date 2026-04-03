from fastapi import APIRouter

from app.models.company import MatchRequest, MatchResponse
from app.services.match_service import analyze_match

router = APIRouter(prefix="/match", tags=["ai"])


@router.post("/", response_model=MatchResponse)
def run_match(data: MatchRequest):
    result = analyze_match(data.jd_text, data.resume_text)
    return result
