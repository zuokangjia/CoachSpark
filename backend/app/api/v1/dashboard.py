from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session
from collections import Counter

from app.db.session import get_db
from app.db.models import Company, Interview, PrepPlan

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    # Only fetch columns actually needed to avoid loading full model instances
    company_statuses = db.query(Company.status).all()
    interview_analyses = db.query(Interview.ai_analysis).all()
    prep_plan_tasks = db.query(PrepPlan.daily_tasks).all()

    status_counts: Counter[str] = Counter(str(s) for (s,) in company_statuses)

    all_weak: dict[str, int] = {}
    for (analysis_json,) in interview_analyses:
        analysis = analysis_json if isinstance(analysis_json, dict) else {}
        for wp in analysis.get("weak_points", []):
            all_weak[wp] = all_weak.get(wp, 0) + 1

    top_weak = sorted(all_weak.items(), key=lambda x: x[1], reverse=True)[:5]

    scored_interviews: list[float] = []
    for (analysis_json,) in interview_analyses:
        analysis = analysis_json if isinstance(analysis_json, dict) else {}
        questions = analysis.get("questions", [])
        if not isinstance(questions, list) or not questions:
            continue
        scores: list[float] = []
        for q in questions:
            if not isinstance(q, dict):
                continue
            value = q.get("score")
            if isinstance(value, (int, float)):
                scores.append(float(value))
        if not scores:
            continue
        scored_interviews.append(round(sum(scores) / len(scores), 2))

    recent_slice = scored_interviews[-3:]
    previous_slice = scored_interviews[-6:-3]
    recent_avg = (
        round(sum(recent_slice) / len(recent_slice), 2) if recent_slice else 0.0
    )
    previous_avg = (
        round(sum(previous_slice) / len(previous_slice), 2) if previous_slice else 0.0
    )
    score_improvement = round(recent_avg - previous_avg, 2) if previous_slice else 0.0

    total_prep_tasks = 0
    completed_prep_tasks = 0
    for (daily_tasks_json,) in prep_plan_tasks:
        daily_tasks = daily_tasks_json if isinstance(daily_tasks_json, list) else []
        for day in daily_tasks:
            if not isinstance(day, dict):
                continue
            tasks = day.get("tasks", [])
            if not isinstance(tasks, list):
                continue
            total_prep_tasks += len(tasks)

            completed_indexes = day.get("completed_task_indexes", [])
            if not isinstance(completed_indexes, list):
                completed_indexes = []
            normalized_completed = {
                int(index)
                for index in completed_indexes
                if isinstance(index, int) and 0 <= index < len(tasks)
            }
            if normalized_completed:
                completed_prep_tasks += len(normalized_completed)
                continue

            if bool(day.get("completed", False)) and tasks:
                completed_prep_tasks += len(tasks)

    prep_completion_rate = (
        round((completed_prep_tasks / total_prep_tasks) * 100, 1)
        if total_prep_tasks > 0
        else 0.0
    )

    return {
        "total_companies": len(company_statuses),
        "applied": status_counts.get("applied", 0),
        "interviewing": status_counts.get("interviewing", 0),
        "rejected": status_counts.get("rejected", 0),
        "total_interviews": len(interview_analyses),
        "top_weak_points": top_weak,
        "day3_metrics": {
            "prep_completion_rate": prep_completion_rate,
            "completed_prep_tasks": completed_prep_tasks,
            "total_prep_tasks": total_prep_tasks,
            "recent_avg_score": recent_avg,
            "previous_avg_score": previous_avg,
            "score_improvement": score_improvement,
            "scored_interviews": len(scored_interviews),
        },
    }


@router.get("/today")
def get_today_briefing(db: Session = Depends(get_db)):
    today = date.today()
    tomorrow = today + timedelta(days=1)

    upcoming = (
        db.query(Interview, Company)
        .join(Company, Interview.company_id == Company.id)
        .filter(
            Interview.interview_date >= today,
            Interview.interview_date <= tomorrow + timedelta(days=7),
        )
        .order_by(Interview.interview_date.asc())
        .all()
    )
    upcoming_interviews = [
        {
            "company": c.name,
            "position": c.position,
            "round": iv.round,
            "date": str(iv.interview_date),
            "days_until": (iv.interview_date - today).days,
        }
        for iv, c in upcoming
    ]

    pending_results = (
        db.query(Interview, Company)
        .join(Company, Interview.company_id == Company.id)
        .filter(
            Interview.expected_result_date.isnot(None),
            Interview.expected_result_date < today,
            Interview.result_status == "pending",
        )
        .all()
    )
    pending_list = [
        {
            "company": c.name,
            "round": iv.round,
            "expected_date": str(iv.expected_result_date),
            "days_overdue": (today - iv.expected_result_date).days,
        }
        for iv, c in pending_results
    ]

    unreviewed = (
        db.query(Interview, Company)
        .join(Company, Interview.company_id == Company.id)
        .filter(
            Interview.ai_analysis == {},
            Interview.interview_date.isnot(None),
            Interview.interview_date < today - timedelta(days=2),
        )
        .all()
    )
    unreviewed_list = [
        {
            "company": c.name,
            "round": iv.round,
            "interview_date": str(iv.interview_date),
            "days_since": (today - iv.interview_date).days,
        }
        for iv, c in unreviewed
    ]

    return {
        "upcoming_interviews": upcoming_interviews,
        "pending_results": pending_list,
        "unreviewed": unreviewed_list,
    }


@router.get("/stale")
def get_stale_companies(db: Session = Depends(get_db)):
    """
    检测所有 next_event_date 已过但仍处于 applied 状态的投递，
    帮助用户清理积压的投递记录。
    """
    today = date.today()
    stale = (
        db.query(Company)
        .filter(
            Company.status == "applied",
            Company.next_event_date.isnot(None),
            Company.next_event_date < today,
        )
        .order_by(Company.next_event_date.asc())
        .all()
    )
    return {
        "total": len(stale),
        "items": [
            {
                "id": c.id,
                "name": c.name,
                "position": c.position,
                "next_event_date": str(c.next_event_date),
                "days_overdue": (today - c.next_event_date).days,
                "applied_date": str(c.applied_date) if c.applied_date else None,
            }
            for c in stale
        ],
    }


@router.get("/timeline")
def get_interview_timeline(
    months: int = Query(3, ge=1, le=12),
    db: Session = Depends(get_db),
):
    """
    按月统计面试数量分布，帮助用户了解面试节奏。
    """
    today = date.today()
    start = today - timedelta(days=months * 30)

    interviews = (
        db.query(Interview)
        .filter(
            Interview.interview_date.isnot(None),
            Interview.interview_date >= start,
        )
        .order_by(Interview.interview_date.asc())
        .all()
    )

    from collections import defaultdict
    monthly: dict[str, int] = defaultdict(int)
    for iv in interviews:
        if iv.interview_date:
            key = iv.interview_date.strftime("%Y-%m")
            monthly[key] += 1

    return {
        "months": months,
        "timeline": [
            {"month": k, "count": v} for k, v in sorted(monthly.items())
        ],
    }


@router.get("/skill-trend")
def get_skill_trend(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    从历史面试分析中提取薄弱点出现频次和得分趋势，
    帮助用户识别需要持续投入的技能方向。
    """
    from app.services.profile_service import get_or_create_profile

    profile = get_or_create_profile(db)
    weak_points = profile.weak_points if isinstance(profile.weak_points, dict) else {}

    sorted_wp = sorted(
        weak_points.items(),
        key=lambda x: x[1].get("count", 0),
        reverse=True,
    )[:limit]

    return {
        "total_dimensions": len(sorted_wp),
        "items": [
            {
                "dimension": name,
                "count": data.get("count", 0),
                "avg_score": data.get("avg_score", 0),
                "trend": data.get("trend", "new"),
                "first_seen": data.get("first_seen", ""),
                "last_seen": data.get("last_seen", ""),
            }
            for name, data in sorted_wp
        ],
    }
