from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.repository import CompanyRepository
from app.models.company import CompanyCreate, CompanyUpdate


class CompanyService:
    def __init__(self, db: Session):
        self.repo = CompanyRepository(db)

    def get_all(self, skip: int = 0, limit: int = 100):
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, company_id: str):
        return self.repo.get_with_interviews(company_id)

    def create(self, data: CompanyCreate):
        return self.repo.create(data.model_dump(exclude_none=True))

    def update(self, company_id: str, data: CompanyUpdate):
        return self.repo.update(company_id, data.model_dump(exclude_none=True))

    def delete(self, company_id: str):
        return self.repo.delete(company_id)


class InterviewService:
    def __init__(self, db: Session):
        from app.db.repository import InterviewRepository

        self.repo = InterviewRepository(db)

    def get_by_company(self, company_id: str):
        return self.repo.get_by_company(company_id)

    def get_by_id(self, interview_id: str):
        return self.repo.get_by_id(interview_id)

    def create(self, company_id: str, data):
        obj = data.model_dump(exclude_none=True)
        obj["company_id"] = company_id
        return self.repo.create(obj)

    def update(self, interview_id: str, data):
        return self.repo.update(interview_id, data.model_dump(exclude_none=True))

    def delete(self, interview_id: str):
        return self.repo.delete(interview_id)


class PrepPlanService:
    def __init__(self, db: Session):
        from app.db.repository import PrepPlanRepository

        self.repo = PrepPlanRepository(db)

    def get_by_company(self, company_id: str):
        return self.repo.get_by_company(company_id)

    def create(self, data):
        return self.repo.create(data)
