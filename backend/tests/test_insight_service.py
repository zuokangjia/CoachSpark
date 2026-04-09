"""Tests for Insight / Rejection Analysis API."""
import pytest
from fastapi.testclient import TestClient


def test_rejection_analysis_company_not_found(client: TestClient):
    """Test rejection analysis returns 404 for non-existent company."""
    response = client.post("/api/v1/companies/nonexistent-id/rejection-analysis")
    assert response.status_code == 404
    # Should be standard FastAPI error format with "detail" field
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Company not found"


def test_rejection_analysis_empty(client: TestClient):
    """Test rejection analysis with company but no interviews."""
    company_resp = client.post(
        "/api/v1/companies/",
        json={"name": "Test Corp", "position": "Engineer"},
    )
    company_id = company_resp.json()["id"]

    response = client.post(f"/api/v1/companies/{company_id}/rejection-analysis")
    assert response.status_code == 200
    data = response.json()
    assert "likely_reasons" in data
    assert "strengths_to_keep" in data
    assert "next_focus" in data
    assert "encouragement" in data


def test_rejection_analysis_with_interviews(client: TestClient):
    """Test rejection analysis with AI-analyzed interviews."""
    company_resp = client.post(
        "/api/v1/companies/",
        json={"name": "Test Corp", "position": "Engineer"},
    )
    company_id = company_resp.json()["id"]

    # Add interview with AI analysis
    client.post(
        f"/api/v1/companies/{company_id}/interviews",
        json={
            "round": 1,
            "raw_notes": "Went okay",
            "ai_analysis": {
                "questions": [
                    {"question": "What is Python?", "score": 6},
                    {"question": "Design patterns?", "score": 4},
                ],
                "weak_points": ["system design", "architecture"],
                "strong_points": ["coding", "testing"],
            },
        },
    )

    response = client.post(f"/api/v1/companies/{company_id}/rejection-analysis")
    assert response.status_code == 200
    data = response.json()
    assert len(data["strengths_to_keep"]) <= 3
    assert "encouragement" in data
