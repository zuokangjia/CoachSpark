from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models import Company, Offer
from app.models.company import (
    OfferCreate,
    OfferUpdate,
    OfferResponse,
    StatusTransitionRequest,
)
from app.services.status_service import transition_company_status

router = APIRouter(prefix="/offers", tags=["offers"])


@router.get("/", response_model=List[OfferResponse])
def list_offers(db: Session = Depends(get_db)):
    offers = (
        db.query(Offer, Company).join(Company, Offer.company_id == Company.id).all()
    )
    return [
        {
            "id": o.id,
            "company_id": o.company_id,
            "company_name": c.name,
            "position": c.position,
            "salary": o.salary,
            "benefits": o.benefits,
            "offer_date": o.offer_date,
            "deadline": o.deadline,
            "status": o.status,
            "notes": o.notes,
            "created_at": o.created_at,
        }
        for o, c in offers
    ]


@router.post("/", response_model=OfferResponse)
def create_offer(data: OfferCreate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Company not found")

    from app.db.models import generate_uuid

    offer = Offer(
        id=generate_uuid(),
        company_id=data.company_id,
        salary=data.salary or "",
        benefits=data.benefits or "",
        offer_date=data.offer_date,
        deadline=data.deadline,
        notes=data.notes or "",
        status="pending",
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)

    return {
        "id": offer.id,
        "company_id": offer.company_id,
        "company_name": company.name,
        "position": company.position,
        "salary": offer.salary,
        "benefits": offer.benefits,
        "offer_date": offer.offer_date,
        "deadline": offer.deadline,
        "status": offer.status,
        "notes": offer.notes,
        "created_at": offer.created_at,
    }


@router.put("/{offer_id}", response_model=OfferResponse)
def update_offer(offer_id: str, data: OfferUpdate, db: Session = Depends(get_db)):
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Offer not found")

    update_data = data.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(offer, key, value)

    db.commit()
    db.refresh(offer)

    company = db.query(Company).filter(Company.id == offer.company_id).first()
    return {
        "id": offer.id,
        "company_id": offer.company_id,
        "company_name": company.name if company else "",
        "position": company.position if company else "",
        "salary": offer.salary,
        "benefits": offer.benefits,
        "offer_date": offer.offer_date,
        "deadline": offer.deadline,
        "status": offer.status,
        "notes": offer.notes,
        "created_at": offer.created_at,
    }


@router.delete("/{offer_id}")
def delete_offer(offer_id: str, db: Session = Depends(get_db)):
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Offer not found")
    db.delete(offer)
    db.commit()
    return {"message": "Deleted"}
