from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.profile_service import (
    get_or_create_profile,
    rebuild_profile,
    get_profile_summary,
)

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/")
def get_profile(db: Session = Depends(get_db)):
    return get_or_create_profile(db)


@router.post("/rebuild")
def rebuild(db: Session = Depends(get_db)):
    return rebuild_profile(db)


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    return {"summary": get_profile_summary(db)}
