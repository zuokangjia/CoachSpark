from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Resume, generate_uuid
from app.models.company import ResumeCreate, ResumeUpdate, ResumeResponse

router = APIRouter(prefix="/resume", tags=["resume"])


def _get_or_create_resume(db: Session) -> Resume:
    resume = db.query(Resume).first()
    if not resume:
        resume = Resume(id=generate_uuid())
        db.add(resume)
        db.commit()
        db.refresh(resume)
    return resume


@router.get("/", response_model=ResumeResponse)
def get_resume(db: Session = Depends(get_db)):
    return _get_or_create_resume(db)


@router.put("/", response_model=ResumeResponse)
def update_resume(data: ResumeUpdate, db: Session = Depends(get_db)):
    resume = _get_or_create_resume(db)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(resume, key, value)
    db.commit()
    db.refresh(resume)
    return resume


@router.post("/rebuild", response_model=ResumeResponse)
def rebuild_resume(db: Session = Depends(get_db)):
    resume = _get_or_create_resume(db)
    for field in ["full_name", "phone", "email", "summary"]:
        setattr(resume, field, "")
    for field in [
        "skills",
        "education",
        "work_experience",
        "projects",
        "certifications",
    ]:
        setattr(resume, field, [] if field != "certifications" else [])
    db.commit()
    db.refresh(resume)
    return resume
