"""
Unit tests for CoachSpark backend.

These tests cover:
- Pydantic model validation (status, field constraints, LLM input limits)
- Repository layer with an in-memory SQLite database
- Service-layer helper utilities (profile_service, insight_service)
- Health-check endpoint
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime

# ---------------------------------------------------------------------------
# In-memory SQLite engine shared across tests
# ---------------------------------------------------------------------------
from app.db.session import Base
from app.db.models import Company, Interview, UserProfile, generate_uuid

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test and drop them afterwards."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Pydantic model validation
# ---------------------------------------------------------------------------


class TestCompanyModelValidation:
    def test_valid_company_create(self):
        from app.models.company import CompanyCreate

        c = CompanyCreate(name="Acme", position="Engineer", status="applied")
        assert c.status == "applied"
        assert c.name == "Acme"

    def test_invalid_status_raises(self):
        from app.models.company import CompanyCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="status must be one of"):
            CompanyCreate(name="Acme", position="Engineer", status="unknown_status")

    def test_all_valid_statuses(self):
        from app.models.company import CompanyCreate

        for s in ("applied", "interviewing", "offer", "rejected"):
            c = CompanyCreate(name="X", position="Y", status=s)
            assert c.status == s

    def test_name_max_length_enforced(self):
        from app.models.company import CompanyCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CompanyCreate(name="A" * 256, position="Y")

    def test_company_update_status_validation(self):
        from app.models.company import CompanyUpdate
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="status must be one of"):
            CompanyUpdate(status="bad_status")

    def test_company_update_none_status_allowed(self):
        from app.models.company import CompanyUpdate

        u = CompanyUpdate(status=None)
        assert u.status is None

    def test_match_request_jd_max_length(self):
        from app.models.company import MatchRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            MatchRequest(jd_text="x" * 8_001, resume_text="y")

    def test_review_request_notes_max_length(self):
        from app.models.company import ReviewRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ReviewRequest(raw_notes="n" * 10_001)

    def test_prep_request_days_available_bounds(self):
        from app.models.company import PrepRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PrepRequest(company_id="1", target_round=1, days_available=0)

        with pytest.raises(ValidationError):
            PrepRequest(company_id="1", target_round=1, days_available=31)


# ---------------------------------------------------------------------------
# Repository layer
# ---------------------------------------------------------------------------


class TestBaseRepository:
    def test_create_and_get_by_id(self, db):
        from app.db.repository import CompanyRepository

        repo = CompanyRepository(db)
        company_id = generate_uuid()
        company = repo.create(
            {
                "id": company_id,
                "name": "TestCorp",
                "position": "Backend Engineer",
                "status": "applied",
                "applied_date": date.today(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )
        assert company.id == company_id
        fetched = repo.get_by_id(company_id)
        assert fetched is not None
        assert fetched.name == "TestCorp"

    def test_get_all_with_pagination(self, db):
        from app.db.repository import CompanyRepository

        repo = CompanyRepository(db)
        for i in range(5):
            repo.create(
                {
                    "id": generate_uuid(),
                    "name": f"Corp{i}",
                    "position": "Engineer",
                    "status": "applied",
                    "applied_date": date.today(),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            )

        page1 = repo.get_all(skip=0, limit=3)
        page2 = repo.get_all(skip=3, limit=3)
        assert len(page1) == 3
        assert len(page2) == 2

    def test_update(self, db):
        from app.db.repository import CompanyRepository

        repo = CompanyRepository(db)
        company_id = generate_uuid()
        repo.create(
            {
                "id": company_id,
                "name": "OldName",
                "position": "Engineer",
                "status": "applied",
                "applied_date": date.today(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )
        updated = repo.update(company_id, {"name": "NewName"})
        assert updated.name == "NewName"

    def test_delete(self, db):
        from app.db.repository import CompanyRepository

        repo = CompanyRepository(db)
        company_id = generate_uuid()
        repo.create(
            {
                "id": company_id,
                "name": "ToDelete",
                "position": "Engineer",
                "status": "applied",
                "applied_date": date.today(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )
        result = repo.delete(company_id)
        assert result is True
        assert repo.get_by_id(company_id) is None

    def test_delete_nonexistent_returns_false(self, db):
        from app.db.repository import CompanyRepository

        repo = CompanyRepository(db)
        assert repo.delete(generate_uuid()) is False

    def test_get_by_id_nonexistent_returns_none(self, db):
        from app.db.repository import CompanyRepository

        repo = CompanyRepository(db)
        assert repo.get_by_id(generate_uuid()) is None


# ---------------------------------------------------------------------------
# Profile service helpers
# ---------------------------------------------------------------------------


class TestProfileService:
    def test_get_or_create_profile_creates_once(self, db):
        from app.services.profile_service import get_or_create_profile

        p1 = get_or_create_profile(db)
        p2 = get_or_create_profile(db)
        assert p1.id == p2.id  # Same row returned on second call

    def test_calculate_trend_improving(self):
        from app.services.profile_service import _calculate_trend

        assert _calculate_trend([3, 4, 7, 8]) == "improving"

    def test_calculate_trend_declining(self):
        from app.services.profile_service import _calculate_trend

        assert _calculate_trend([8, 7, 4, 3]) == "declining"

    def test_calculate_trend_stable(self):
        from app.services.profile_service import _calculate_trend

        assert _calculate_trend([5, 5, 5, 5]) == "stable"

    def test_calculate_trend_new_single_score(self):
        from app.services.profile_service import _calculate_trend

        assert _calculate_trend([7]) == "new"

    def test_extract_keywords(self):
        from app.services.profile_service import _extract_keywords

        keywords = _extract_keywords("We use Python and Docker for CI/CD pipelines")
        assert "Python" in keywords
        assert "Docker" in keywords
        assert "CI/CD" in keywords


# ---------------------------------------------------------------------------
# Insight service
# ---------------------------------------------------------------------------


class TestInsightService:
    def _make_company_with_interviews(self, db):
        company_id = generate_uuid()
        company = Company(
            id=company_id,
            name="TestCo",
            position="SWE",
            status="rejected",
            applied_date=date.today(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(company)
        db.flush()

        iv1 = Interview(
            id=generate_uuid(),
            company_id=company_id,
            round=1,
            ai_analysis={
                "weak_points": ["系统设计", "并发编程"],
                "strong_points": ["Python"],
                "questions": [
                    {"question": "Q1", "your_answer_summary": "A", "score": 4},
                    {"question": "Q2", "your_answer_summary": "B", "score": 3},
                ],
            },
            created_at=datetime.utcnow(),
        )
        db.add(iv1)
        db.commit()
        return company_id

    def test_analyze_rejection_returns_dict(self, db):
        from app.services.insight_service import analyze_rejection

        company_id = self._make_company_with_interviews(db)
        result = analyze_rejection(db, company_id)
        assert isinstance(result, dict)
        assert "likely_reasons" in result
        assert "next_focus" in result

    def test_analyze_rejection_missing_company(self, db):
        from app.services.insight_service import analyze_rejection

        result = analyze_rejection(db, generate_uuid())
        assert result.get("error") == "Company not found"


# ---------------------------------------------------------------------------
# FastAPI health check endpoint
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        from fastapi.testclient import TestClient

        # Patch settings so the app can start without a real OPENAI_API_KEY
        import os
        os.environ.setdefault("OPENAI_API_KEY", "test-key")

        from app.main import app

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "db" in data
