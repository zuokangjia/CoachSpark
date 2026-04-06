"""Tests for Company API endpoints."""
import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_list_companies_empty(client: TestClient):
    response = client.get("/api/v1/companies/")
    assert response.status_code == 200
    assert response.json() == []


def test_create_company(client: TestClient):
    payload = {
        "name": "Test Corp",
        "position": "Software Engineer",
        "jd_text": "We are looking for a software engineer...",
        "status": "applied",
    }
    response = client.post("/api/v1/companies/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Corp"
    assert data["position"] == "Software Engineer"
    assert data["status"] == "applied"
    assert "id" in data
    assert "created_at" in data


def test_create_company_invalid_status(client: TestClient):
    payload = {
        "name": "Test Corp",
        "position": "Software Engineer",
        "status": "invalid_status",
    }
    response = client.post("/api/v1/companies/", json=payload)
    assert response.status_code == 422


def test_create_company_missing_required_fields(client: TestClient):
    response = client.post("/api/v1/companies/", json={"name": "Only Name"})
    assert response.status_code == 422


def test_create_company_name_too_long(client: TestClient):
    payload = {
        "name": "A" * 256,
        "position": "Software Engineer",
    }
    response = client.post("/api/v1/companies/", json=payload)
    assert response.status_code == 422


def test_get_company(client: TestClient):
    create_resp = client.post(
        "/api/v1/companies/",
        json={"name": "Acme Inc", "position": "Dev"},
    )
    company_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/companies/{company_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == company_id
    assert data["name"] == "Acme Inc"
    assert "interviews" in data


def test_get_company_not_found(client: TestClient):
    response = client.get("/api/v1/companies/nonexistent-id")
    assert response.status_code == 404


def test_update_company(client: TestClient):
    create_resp = client.post(
        "/api/v1/companies/",
        json={"name": "Old Name", "position": "Old Position"},
    )
    company_id = create_resp.json()["id"]

    response = client.put(
        f"/api/v1/companies/{company_id}",
        json={"name": "New Name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"
    assert response.json()["position"] == "Old Position"


def test_delete_company(client: TestClient):
    create_resp = client.post(
        "/api/v1/companies/",
        json={"name": "To Delete", "position": "Dev"},
    )
    company_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/v1/companies/{company_id}")
    assert delete_resp.status_code == 200

    get_resp = client.get(f"/api/v1/companies/{company_id}")
    assert get_resp.status_code == 404


def test_list_companies_pagination(client: TestClient):
    for i in range(5):
        client.post(
            "/api/v1/companies/",
            json={"name": f"Company {i}", "position": "Dev"},
        )

    resp_all = client.get("/api/v1/companies/")
    assert len(resp_all.json()) == 5

    resp_limited = client.get("/api/v1/companies/?limit=3")
    assert len(resp_limited.json()) == 3

    resp_skipped = client.get("/api/v1/companies/?skip=3&limit=10")
    assert len(resp_skipped.json()) == 2


def test_list_companies_invalid_pagination(client: TestClient):
    response = client.get("/api/v1/companies/?skip=-1")
    assert response.status_code == 422


def test_get_interview_chain_empty(client: TestClient):
    create_resp = client.post(
        "/api/v1/companies/",
        json={"name": "Corp", "position": "Dev"},
    )
    company_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/companies/{company_id}/interview-chain")
    assert response.status_code == 200
    data = response.json()
    assert data["rounds"] == []
    assert data["weak_point_tracking"] == {}
