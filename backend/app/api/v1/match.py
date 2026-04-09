from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.company import MatchRequest, MatchResponse
from app.services.match_service import analyze_match, analyze_match_with_stored_resume

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/match", tags=["ai"])


@router.post("/", response_model=MatchResponse)
@limiter.limit("10/minute")
async def run_match(request: Request, data: MatchRequest, db: Session = Depends(get_db)):
    if data.use_stored_resume:
        result = await analyze_match_with_stored_resume(data.jd_text, db)
    else:
        result = await analyze_match(data.jd_text, data.resume_text)
    return result
