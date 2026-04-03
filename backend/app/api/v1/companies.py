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
from app.services.profile_service import get_profile_summary
from app.services.insight_service import analyze_rejection

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


@router.get("/{company_id}/interview-chain")
def get_interview_chain(company_id: str, db: Session = Depends(get_db)):
    interviews = (
        db.query(Interview)
        .filter(Interview.company_id == company_id)
        .order_by(Interview.round.asc())
        .all()
    )
    if not interviews:
        return {"rounds": [], "weak_point_tracking": {}}

    rounds = []
    weak_point_counts: dict[str, dict] = {}

    for iv in interviews:
        analysis = iv.ai_analysis if isinstance(iv.ai_analysis, dict) else {}
        round_data = {
            "id": iv.id,
            "round": iv.round,
            "interview_date": str(iv.interview_date) if iv.interview_date else None,
            "format": iv.format,
            "interviewer": iv.interviewer,
            "weak_points": analysis.get("weak_points", []),
            "strong_points": analysis.get("strong_points", []),
            "questions_count": len(analysis.get("questions", [])),
        }
        rounds.append(round_data)

        for wp in analysis.get("weak_points", []):
            if wp not in weak_point_counts:
                weak_point_counts[wp] = {"count": 0, "rounds": []}
            weak_point_counts[wp]["count"] += 1
            weak_point_counts[wp]["rounds"].append(iv.round)

    weak_point_tracking = {}
    for wp, data in weak_point_counts.items():
        weak_point_tracking[wp] = {
            "count": data["count"],
            "first_round": data["rounds"][0],
            "last_round": data["rounds"][-1],
            "is_persistent": data["count"] >= 2,
        }

    return {"rounds": rounds, "weak_point_tracking": weak_point_tracking}


@router.get("/{company_id}/stats")
def get_company_stats(company_id: str, db: Session = Depends(get_db)):
    interviews = db.query(Interview).filter(Interview.company_id == company_id).all()
    all_weak: dict[str, int] = {}
    all_strong: dict[str, int] = {}
    total_questions = 0

    for iv in interviews:
        analysis = iv.ai_analysis if isinstance(iv.ai_analysis, dict) else {}
        for wp in analysis.get("weak_points", []):
            all_weak[wp] = all_weak.get(wp, 0) + 1
        for sp in analysis.get("strong_points", []):
            all_strong[sp] = all_strong.get(sp, 0) + 1
        total_questions += len(analysis.get("questions", []))

    return {
        "interview_count": len(interviews),
        "total_questions": total_questions,
        "top_weak_points": sorted(all_weak.items(), key=lambda x: x[1], reverse=True)[
            :5
        ],
        "top_strong_points": sorted(
            all_strong.items(), key=lambda x: x[1], reverse=True
        )[:5],
    }


@router.post("/{company_id}/rejection-analysis")
def get_rejection_analysis(company_id: str, db: Session = Depends(get_db)):
    return analyze_rejection(db, company_id)
