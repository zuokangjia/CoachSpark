from typing import TypeVar, Type, Optional, List, Generic
from sqlalchemy.orm import Session

from app.db.session import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def get_by_id(self, id: str) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def create(self, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, id: str, obj_in: dict) -> Optional[ModelType]:
        db_obj = self.get_by_id(id)
        if not db_obj:
            return None
        for key, value in obj_in.items():
            setattr(db_obj, key, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: str) -> bool:
        db_obj = self.get_by_id(id)
        if not db_obj:
            return False
        self.db.delete(db_obj)
        self.db.commit()
        return True


class CompanyRepository(BaseRepository):
    def __init__(self, db: Session):
        from app.db.models import Company

        super().__init__(Company, db)

    def get_with_interviews(self, company_id: str):
        from app.db.models import Company

        return self.db.query(Company).filter(Company.id == company_id).first()


class InterviewRepository(BaseRepository):
    def __init__(self, db: Session):
        from app.db.models import Interview

        super().__init__(Interview, db)

    def get_by_company(self, company_id: str):
        from app.db.models import Interview

        return (
            self.db.query(Interview)
            .filter(Interview.company_id == company_id)
            .order_by(Interview.round.asc())
            .all()
        )


class PrepPlanRepository(BaseRepository):
    def __init__(self, db: Session):
        from app.db.models import PrepPlan

        super().__init__(PrepPlan, db)

    def get_by_company(self, company_id: str):
        from app.db.models import PrepPlan

        return (
            self.db.query(PrepPlan)
            .filter(PrepPlan.company_id == company_id)
            .order_by(PrepPlan.created_at.desc())
            .all()
        )
