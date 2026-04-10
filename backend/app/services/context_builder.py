from sqlalchemy.orm import Session

from app.services.profile_service import get_profile_summary
from app.db.models import Interview, Company, Resume


"""
Design: LLM Context Enrichment
核心思想：为 AI 分析构建丰富的上下文信息，包括用户技能、简历摘要、公司信息、
历史面试弱点趋势等。不同的分析场景（review/prep/match）使用不同的 context 构建逻辑。
这样可以让 LLM 在分析时具备个性化背景，产生更贴合用户实际情况的建议。
"""


class ContextBuilder:
    """
    Context builder for LLM.
    Builds enriched context from user profile, resume, company info, and interview history.
    """
    def __init__(self, db: Session):
        self.db = db

    def build_review_context(self, company_id: str) -> str:
        parts = []
        resume = self.db.query(Resume).first()
        if resume and resume.skills:
            parts.append(f"[User Skills] {', '.join(resume.skills)}")
        profile_summary = get_profile_summary(self.db)
        if profile_summary:
            parts.append(f"[User Profile] {profile_summary}")

        company = self.db.query(Company).filter(Company.id == company_id).first()
        if company:
            parts.append(f"[Current Company] {company.name} - {company.position}")
            if company.jd_text and len(company.jd_text) > 10:
                parts.append(f"[JD Summary] {company.jd_text[:500]}")

        recent_interviews = (
            self.db.query(Interview)
            .filter(Interview.company_id == company_id, Interview.ai_analysis != {})
            .order_by(Interview.created_at.desc())
            .limit(2)
            .all()
        )
        if recent_interviews:
            weak_history = []
            for iv in recent_interviews:
                wp = iv.ai_analysis.get("weak_points", [])
                if wp:
                    weak_history.append(
                        f"Round {iv.round} weak points: {', '.join(wp)}"
                    )
            if weak_history:
                parts.append("[Recent Weak Points]\n" + "\n".join(weak_history))

        trend_info = self._get_weak_point_trends()
        if trend_info:
            parts.append(f"[Weak Point Trends]\n{trend_info}")

        return "\n".join(parts)

    def build_prep_context(self, company_id: str) -> str:
        parts = []
        resume = self.db.query(Resume).first()
        if resume and resume.skills:
            parts.append(f"[User Skills] {', '.join(resume.skills)}")
        profile_summary = get_profile_summary(self.db)
        if profile_summary:
            parts.append(f"[User Profile] {profile_summary}")

        company = self.db.query(Company).filter(Company.id == company_id).first()
        if company and company.position:
            parts.append(f"[Target Role] {company.position}")

        all_interviews = (
            self.db.query(Interview)
            .filter(Interview.company_id == company_id, Interview.ai_analysis != {})
            .order_by(Interview.round.asc())
            .all()
        )
        if all_interviews:
            weak_all: dict[str, int] = {}
            for iv in all_interviews:
                for wp in iv.ai_analysis.get("weak_points", []):
                    weak_all[wp] = weak_all.get(wp, 0) + 1
            if weak_all:
                sorted_weak = sorted(weak_all.items(), key=lambda x: x[1], reverse=True)
                parts.append(
                    "[Weak Point Frequency] "
                    + ", ".join(f"{k}({v} times)" for k, v in sorted_weak[:5])
                )

        trend_info = self._get_weak_point_trends()
        if trend_info:
            parts.append(f"[Weak Point Trends]\n{trend_info}")

        return "\n".join(parts)

    def build_match_context(self) -> str:
        profile_summary = get_profile_summary(self.db)
        if profile_summary:
            return f"[User Profile] {profile_summary}"
        return ""

    def _get_weak_point_trends(self) -> str:
        from app.services.profile_service import get_or_create_profile

        profile = get_or_create_profile(self.db)
        if not profile.weak_points or not isinstance(profile.weak_points, dict):
            return ""

        trend_lines = []
        for wp, data in sorted(
            profile.weak_points.items(),
            key=lambda x: x[1].get("count", 0),
            reverse=True,
        )[:5]:
            count = data.get("count", 0)
            avg = data.get("avg_score", 0)
            trend = data.get("trend", "new")
            trend_icon = {
                "improving": "↑",
                "declining": "↓",
                "stable": "→",
                "new": "◆",
            }.get(trend, "?")
            trend_lines.append(
                f"  {trend_icon} {wp}: {count} times, avg {avg}/10 ({trend})"
            )

        return "\n".join(trend_lines) if trend_lines else ""
