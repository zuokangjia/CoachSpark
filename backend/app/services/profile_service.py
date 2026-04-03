from sqlalchemy.orm import Session
from collections import Counter

from app.db.models import UserProfile, Interview, Company, generate_uuid


def get_or_create_profile(db: Session) -> UserProfile:
    profile = db.query(UserProfile).first()
    if not profile:
        profile = UserProfile(id=generate_uuid())
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def rebuild_profile(db: Session) -> UserProfile:
    interviews = db.query(Interview).order_by(Interview.created_at.asc()).all()
    companies = db.query(Company).all()

    weak_points_counter: dict[str, dict] = {}
    strong_points_list: list[str] = []
    skills_counter: Counter = Counter()

    for iv in interviews:
        analysis = iv.ai_analysis
        if not isinstance(analysis, dict):
            continue

        for wp in analysis.get("weak_points", []):
            if wp not in weak_points_counter:
                weak_points_counter[wp] = {
                    "count": 0,
                    "scores": [],
                    "first_seen": str(iv.created_at),
                    "last_seen": str(iv.created_at),
                    "rounds": [],
                }
            weak_points_counter[wp]["count"] += 1
            weak_points_counter[wp]["last_seen"] = str(iv.created_at)
            weak_points_counter[wp]["rounds"].append(iv.round)
            for q in analysis.get("questions", []):
                if isinstance(q, dict) and "score" in q:
                    weak_points_counter[wp]["scores"].append(q["score"])

        for sp in analysis.get("strong_points", []):
            strong_points_list.append(sp)

    for c in companies:
        if c.position:
            skills_counter.update(c.position.split())
        if c.jd_text and len(c.jd_text) > 10:
            for keyword in _extract_keywords(c.jd_text):
                skills_counter[keyword] += 1

    top_skills = [s for s, _ in skills_counter.most_common(10)]
    top_strong = [s for s, _ in Counter(strong_points_list).most_common(5)]

    weak_points_summary = {}
    for wp, data in sorted(
        weak_points_counter.items(), key=lambda x: x[1]["count"], reverse=True
    )[:10]:
        scores = data["scores"]
        avg = round(sum(scores) / len(scores), 1) if scores else 0
        trend = _calculate_trend(scores)
        weak_points_summary[wp] = {
            "count": data["count"],
            "avg_score": avg,
            "first_seen": data["first_seen"],
            "last_seen": data["last_seen"],
            "trend": trend,
            "rounds": data["rounds"],
        }

    profile = get_or_create_profile(db)
    profile.skills = top_skills
    profile.weak_points = weak_points_summary
    profile.strong_points = top_strong
    profile.interview_count = len(interviews)
    profile.offer_count = sum(1 for c in companies if c.status == "rejected")
    db.commit()
    db.refresh(profile)
    return profile


def update_profile_incremental(db: Session, interview_id: str) -> UserProfile:
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        return get_or_create_profile(db)

    profile = get_or_create_profile(db)
    analysis = interview.ai_analysis
    if not isinstance(analysis, dict):
        return profile

    if not isinstance(profile.weak_points, dict):
        profile.weak_points = {}
    if not isinstance(profile.skills, list):
        profile.skills = []
    if not isinstance(profile.strong_points, list):
        profile.strong_points = []

    for wp in analysis.get("weak_points", []):
        if wp not in profile.weak_points:
            profile.weak_points[wp] = {
                "count": 0,
                "scores": [],
                "first_seen": str(interview.created_at),
                "last_seen": str(interview.created_at),
                "rounds": [],
            }
        profile.weak_points[wp]["count"] += 1
        profile.weak_points[wp]["last_seen"] = str(interview.created_at)
        profile.weak_points[wp]["rounds"].append(interview.round)
        for q in analysis.get("questions", []):
            if isinstance(q, dict) and "score" in q:
                profile.weak_points[wp]["scores"].append(q["score"])
        profile.weak_points[wp]["trend"] = _calculate_trend(
            profile.weak_points[wp]["scores"]
        )

    for sp in analysis.get("strong_points", []):
        if sp not in profile.strong_points:
            profile.strong_points.append(sp)

    if interview.company:
        company = interview.company
        if company.position:
            for kw in company.position.split():
                if kw not in profile.skills:
                    profile.skills.append(kw)
        if company.jd_text and len(company.jd_text) > 10:
            for kw in _extract_keywords(company.jd_text):
                if kw not in profile.skills:
                    profile.skills.append(kw)

    profile.interview_count += 1
    db.commit()
    db.refresh(profile)
    return profile


def _calculate_trend(scores: list) -> str:
    if len(scores) < 2:
        return "new"
    recent = scores[-2:]
    older = scores[:-2]
    recent_avg = sum(recent) / len(recent)
    older_avg = sum(older) / len(older) if older else recent_avg
    if recent_avg > older_avg + 1.0:
        return "improving"
    elif recent_avg < older_avg - 1.0:
        return "declining"
    return "stable"


def get_profile_summary(db: Session) -> str:
    profile = get_or_create_profile(db)
    top_weak = list(profile.weak_points.keys())[:3] if profile.weak_points else []
    parts = []
    if profile.career_direction:
        parts.append(f"方向: {profile.career_direction}")
    if profile.interview_count:
        parts.append(f"面试{profile.interview_count}次")
    if top_weak:
        parts.append(f"薄弱: {', '.join(top_weak)}")
    if profile.strong_points:
        parts.append(f"优势: {', '.join(profile.strong_points[:2])}")
    return " | ".join(parts) if parts else ""


def _extract_keywords(text: str) -> list[str]:
    common_tech = [
        "React",
        "Vue",
        "Angular",
        "TypeScript",
        "JavaScript",
        "Python",
        "Java",
        "Go",
        "Rust",
        "Node.js",
        "Django",
        "Flask",
        "FastAPI",
        "Spring",
        "PostgreSQL",
        "MySQL",
        "MongoDB",
        "Redis",
        "Docker",
        "Kubernetes",
        "AWS",
        "GCP",
        "Azure",
        "CI/CD",
        "GraphQL",
        "REST",
        "微服务",
        "系统设计",
        "性能优化",
        "并发编程",
        "消息队列",
        "缓存",
    ]
    found = [kw for kw in common_tech if kw.lower() in text.lower()]
    return found
