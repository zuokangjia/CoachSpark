"""Tests for input validation on Pydantic models."""
import pytest
from pydantic import ValidationError

from app.models.company import (
    CompanyCreate,
    CompanyUpdate,
    MatchRequest,
    ReviewRequest,
    PrepRequest,
)


class TestCompanyCreate:
    def test_valid_company(self):
        company = CompanyCreate(name="Acme", position="Engineer")
        assert company.name == "Acme"
        assert company.status == "applied"

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            CompanyCreate(name="", position="Engineer")

    def test_name_too_long_rejected(self):
        with pytest.raises(ValidationError):
            CompanyCreate(name="A" * 256, position="Engineer")

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            CompanyCreate(name="Acme", position="Engineer", status="unknown")

    def test_valid_statuses_accepted(self):
        for status in ("applied", "interviewing", "passed", "rejected"):
            c = CompanyCreate(name="Acme", position="Eng", status=status)
            assert c.status == status

    def test_jd_text_too_long_rejected(self):
        with pytest.raises(ValidationError):
            CompanyCreate(name="Acme", position="Eng", jd_text="x" * 50001)

    def test_notes_too_long_rejected(self):
        with pytest.raises(ValidationError):
            CompanyCreate(name="Acme", position="Eng", notes="n" * 5001)


class TestCompanyUpdate:
    def test_partial_update_valid(self):
        update = CompanyUpdate(name="New Name")
        assert update.name == "New Name"
        assert update.position is None

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            CompanyUpdate(name="")

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            CompanyUpdate(status="bad_status")


class TestMatchRequest:
    def test_valid_request(self):
        req = MatchRequest(jd_text="Software Engineer role at Acme...")
        assert req.jd_text.startswith("Software Engineer")
        assert req.use_stored_resume is False

    def test_empty_jd_text_rejected(self):
        with pytest.raises(ValidationError):
            MatchRequest(jd_text="")

    def test_jd_text_too_long_rejected(self):
        with pytest.raises(ValidationError):
            MatchRequest(jd_text="x" * 50001)

    def test_resume_text_too_long_rejected(self):
        with pytest.raises(ValidationError):
            MatchRequest(jd_text="Valid JD", resume_text="r" * 50001)


class TestReviewRequest:
    def test_valid_request(self):
        req = ReviewRequest(raw_notes="The interview was about algorithms and system design.")
        assert req.round == 1

    def test_empty_notes_rejected(self):
        with pytest.raises(ValidationError):
            ReviewRequest(raw_notes="")

    def test_notes_too_long_rejected(self):
        with pytest.raises(ValidationError):
            ReviewRequest(raw_notes="n" * 20001)

    def test_round_must_be_positive(self):
        with pytest.raises(ValidationError):
            ReviewRequest(raw_notes="Some notes", round=0)

    def test_round_upper_limit(self):
        with pytest.raises(ValidationError):
            ReviewRequest(raw_notes="Some notes", round=51)


class TestPrepRequest:
    def test_valid_request(self):
        req = PrepRequest(company_id="some-uuid", target_round=2, days_available=7)
        assert req.days_available == 7

    def test_days_available_too_low(self):
        with pytest.raises(ValidationError):
            PrepRequest(company_id="uuid", target_round=1, days_available=0)

    def test_days_available_too_high(self):
        with pytest.raises(ValidationError):
            PrepRequest(company_id="uuid", target_round=1, days_available=31)
