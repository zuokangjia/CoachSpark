"""Tests for Prep service (update_prep_task_completion)."""
import pytest

from app.db.models import PrepPlan, generate_uuid
from app.services.prep_service import update_prep_task_completion
from tests.conftest import TestingSessionLocal


def _seed_plan(db, company_id: str, daily_tasks=None):
    """Seed a prep plan directly in DB and return its id."""
    plan = PrepPlan(
        id=generate_uuid(),
        company_id=company_id,
        target_round=1,
        days_available=3,
        daily_tasks=daily_tasks or [
            {
                "day": 1,
                "focus": "Python",
                "priority": "high",
                "tasks": ["Task 1", "Task 2"],
                "completed_task_indexes": [],
            }
        ],
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan.id


class TestUpdatePrepTaskCompletion:
    """Tests for update_prep_task_completion using direct service calls."""

    def test_add_task(self, client):
        """Mark a task as completed adds it to completed_task_indexes."""
        # Create company via API
        resp = client.post(
            "/api/v1/companies/",
            json={"name": "Test Corp", "position": "Engineer"},
        )
        company_id = resp.json()["id"]

        # Seed plan using direct DB session
        db = TestingSessionLocal()
        try:
            plan_id = _seed_plan(db, company_id)
        finally:
            db.close()

        # Call service directly
        db = TestingSessionLocal()
        try:
            result = update_prep_task_completion(
                db, plan_id, day=1, task_index=0, completed=True
            )
            assert 0 in result["daily_tasks"][0]["completed_task_indexes"]
        finally:
            db.close()

    def test_remove_task(self, client):
        """Unmarking a completed task removes it from completed_task_indexes."""
        resp = client.post(
            "/api/v1/companies/",
            json={"name": "Test Corp", "position": "Engineer"},
        )
        company_id = resp.json()["id"]

        db = TestingSessionLocal()
        try:
            plan_id = _seed_plan(
                db,
                company_id,
                daily_tasks=[
                    {
                        "day": 1,
                        "focus": "Python",
                        "priority": "high",
                        "tasks": ["Task 1", "Task 2"],
                        "completed_task_indexes": [0],
                    }
                ],
            )
        finally:
            db.close()

        db = TestingSessionLocal()
        try:
            result = update_prep_task_completion(
                db, plan_id, day=1, task_index=0, completed=False
            )
            assert 0 not in result["daily_tasks"][0]["completed_task_indexes"]
        finally:
            db.close()

    def test_plan_not_found(self, client):
        """Non-existent plan raises 404."""
        db = TestingSessionLocal()
        try:
            with pytest.raises(Exception) as exc_info:
                update_prep_task_completion(
                    db, "nonexistent-id", day=1, task_index=0, completed=True
                )
            # FastAPI HTTPException is raised
            assert exc_info.value.status_code == 404
        finally:
            db.close()

    def test_day_not_found(self, client):
        """Non-existent day raises 404."""
        resp = client.post(
            "/api/v1/companies/",
            json={"name": "Test Corp", "position": "Engineer"},
        )
        company_id = resp.json()["id"]

        db = TestingSessionLocal()
        try:
            plan_id = _seed_plan(db, company_id)
        finally:
            db.close()

        db = TestingSessionLocal()
        try:
            with pytest.raises(Exception) as exc_info:
                update_prep_task_completion(
                    db, plan_id, day=99, task_index=0, completed=True
                )
            assert exc_info.value.status_code == 404
        finally:
            db.close()

    def test_double_remove_no_error(self, client):
        """Removing an already-removed task does not raise ValueError."""
        resp = client.post(
            "/api/v1/companies/",
            json={"name": "Test Corp", "position": "Engineer"},
        )
        company_id = resp.json()["id"]

        db = TestingSessionLocal()
        try:
            plan_id = _seed_plan(
                db,
                company_id,
                daily_tasks=[
                    {
                        "day": 1,
                        "focus": "Python",
                        "priority": "high",
                        "tasks": ["Task 1"],
                        "completed_task_indexes": [],  # Task 0 NOT in list
                    }
                ],
            )
        finally:
            db.close()

        db = TestingSessionLocal()
        try:
            # Task 0 is not in completed indexes — calling with completed=False
            # should be a no-op, not raise ValueError
            result = update_prep_task_completion(
                db, plan_id, day=1, task_index=0, completed=False
            )
            assert 0 not in result["daily_tasks"][0]["completed_task_indexes"]
        finally:
            db.close()
