"""Tests for Dashboard API endpoints."""
import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta

from app.db.models import Company, Interview, PrepPlan, generate_uuid
from tests.conftest import TestingSessionLocal


def test_dashboard_stats_empty(client: TestClient):
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_companies"] == 0
    assert data["applied"] == 0
    assert data["interviewing"] == 0
    assert data["rejected"] == 0
    assert data["total_interviews"] == 0
    assert data["top_weak_points"] == []


def test_dashboard_stats_with_companies(client: TestClient):
    # Create a company
    client.post(
        "/api/v1/companies/",
        json={"name": "Test Corp", "position": "Engineer", "status": "applied"},
    )
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_companies"] == 1
    assert data["applied"] == 1
    assert data["interviewing"] == 0


def test_dashboard_today_empty(client: TestClient):
    response = client.get("/api/v1/dashboard/today")
    assert response.status_code == 200
    data = response.json()
    assert data["upcoming_interviews"] == []
    assert data["pending_results"] == []
    assert data["unreviewed"] == []


def test_dashboard_stats_with_interviews(client: TestClient):
    """Test that interviews with AI analysis are correctly counted in stats."""
    # Create company
    company_resp = client.post(
        "/api/v1/companies/",
        json={"name": "Test Corp", "position": "Engineer"},
    )
    company_id = company_resp.json()["id"]

    # Create interview with AI analysis directly in DB
    db = TestingSessionLocal()
    try:
        iv = Interview(
            id=generate_uuid(),
            company_id=company_id,
            round=1,
            ai_analysis={
                "questions": [{"question": "What is Python?", "score": 7}],
                "weak_points": ["system design"],
                "strong_points": ["coding"],
            },
        )
        db.add(iv)
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_interviews"] == 1
    assert data["top_weak_points"] == [["system design", 1]]


def test_dashboard_today_with_upcoming_interview(client: TestClient):
    # Create company
    company_resp = client.post(
        "/api/v1/companies/",
        json={"name": "Test Corp", "position": "Engineer"},
    )
    company_id = company_resp.json()["id"]

    # Create interview with future date directly in DB
    db = TestingSessionLocal()
    try:
        iv = Interview(
            id=generate_uuid(),
            company_id=company_id,
            round=1,
            interview_date=date.today() + timedelta(days=2),
        )
        db.add(iv)
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/dashboard/today")
    assert response.status_code == 200
    data = response.json()
    assert len(data["upcoming_interviews"]) == 1
