from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models import Company, Interview
from app.models.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyDetail,
    InterviewBrief,
)
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/", response_model=List[CompanyResponse])
def list_companies(db: Session = Depends(get_db)):
    service = CompanyService(db)
    return service.get_all()


@router.post("/", response_model=CompanyResponse)
def create_company(data: CompanyCreate, db: Session = Depends(get_db)):
    service = CompanyService(db)
    return service.create(data)


@router.get("/{company_id}", response_model=CompanyDetail)
def get_company(company_id: str, db: Session = Depends(get_db)):
    service = CompanyService(db)
    company = service.get_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    interviews = [InterviewBrief.model_validate(i) for i in company.interviews]
    return CompanyDetail(
        id=company.id,
        name=company.name,
        position=company.position,
        status=company.status,
        applied_date=company.applied_date,
        next_event_date=company.next_event_date,
        next_event_type=company.next_event_type,
        notes=company.notes,
        created_at=company.created_at,
        updated_at=company.updated_at,
        interviews=interviews,
    )


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(company_id: str, data: CompanyUpdate, db: Session = Depends(get_db)):
    service = CompanyService(db)
    updated = service.update(company_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Company not found")
    return updated


@router.delete("/{company_id}")
def delete_company(company_id: str, db: Session = Depends(get_db)):
    service = CompanyService(db)
    deleted = service.delete(company_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"message": "Deleted"}
