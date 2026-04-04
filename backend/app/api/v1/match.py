from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.company import MatchRequest, MatchResponse
from app.services.match_service import analyze_match, analyze_match_with_stored_resume

router = APIRouter(prefix="/match", tags=["ai"])


@router.post("/", response_model=MatchResponse)
def run_match(data: MatchRequest, db: Session = Depends(get_db)):
    if data.use_stored_resume:
        result = analyze_match_with_stored_resume(data.jd_text, db)
    else:
        result = analyze_match(data.jd_text, data.resume_text)
    return result
