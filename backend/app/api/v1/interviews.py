from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.company import (
    InterviewCreate,
    InterviewUpdate,
    InterviewResponse,
)
from app.services.company_service import InterviewService

router = APIRouter(
    prefix="/companies/{company_id}/interviews",
    tags=["interviews"],
)


@router.get("/", response_model=List[InterviewResponse])
def list_interviews(company_id: str, db: Session = Depends(get_db)):
    service = InterviewService(db)
    return service.get_by_company(company_id)


@router.post("/", response_model=InterviewResponse)
def create_interview(
    company_id: str, data: InterviewCreate, db: Session = Depends(get_db)
):
    service = InterviewService(db)
    return service.create(company_id, data)


@router.get("/{interview_id}", response_model=InterviewResponse)
def get_interview(company_id: str, interview_id: str, db: Session = Depends(get_db)):
    service = InterviewService(db)
    interview = service.get_by_id(interview_id)
    if not interview or interview.company_id != company_id:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview
