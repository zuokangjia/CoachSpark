from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import Company, Interview

"""
Design: Rejection Insight Analysis
核心思想：从面试历史中分析被拒原因，识别反复出现的薄弱点。
输出：可能原因、需保持的优势、下一步重点改进方向、鼓励话语。
帮助用户在失败中学习，而非简单归因。
"""


def analyze_rejection(db: Session, company_id: str) -> dict:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    interviews = (
        db.query(Interview)
        .filter(Interview.company_id == company_id)
        .order_by(Interview.round.asc())
        .all()
    )

    weak_points: dict[str, dict] = {}
    strong_points: list[str] = []
    lowest_score_wp = []

    for iv in interviews:
        analysis = iv.ai_analysis if isinstance(iv.ai_analysis, dict) else {}
        for wp in analysis.get("weak_points", []):
            if wp not in weak_points:
                weak_points[wp] = {"count": 0, "scores": []}
            weak_points[wp]["count"] += 1
            for q in analysis.get("questions", []):
                if isinstance(q, dict) and "score" in q:
                    weak_points[wp]["scores"].append(q["score"])
        for sp in analysis.get("strong_points", []):
            strong_points.append(sp)

    for wp, data in weak_points.items():
        if data["scores"]:
            avg = sum(data["scores"]) / len(data["scores"])
            lowest_score_wp.append((wp, avg, data["count"]))

    lowest_score_wp.sort(key=lambda x: x[1])

    likely_reasons = []
    for wp, avg, count in lowest_score_wp[:3]:
        if avg < 5:
            likely_reasons.append(f"{wp} 薄弱 (平均 {avg}/10，出现 {count} 次)")
        elif count >= 2:
            likely_reasons.append(f"{wp} 反复出现 ({count} 次，平均 {avg}/10)")

    strengths_to_keep = list(set(strong_points))[:3]

    next_focus = [wp for wp, _, _ in lowest_score_wp[:3]]

    improving_wps = []
    for wp, data in weak_points.items():
        scores = data["scores"]
        if len(scores) >= 2:
            recent = scores[-2:]
            older = scores[:-2]
            recent_avg = sum(recent) / len(recent)
            older_avg = sum(older) / len(older) if older else recent_avg
            if recent_avg > older_avg + 0.5:
                improving_wps.append(wp)

    encouragement_parts = []
    if improving_wps:
        encouragement_parts.append(f"你的 {', '.join(improving_wps)} 在进步，继续保持")
    if strengths_to_keep:
        encouragement_parts.append(f"你的 {strengths_to_keep[0]} 是优势")
    if not encouragement_parts:
        encouragement_parts.append("每次面试都是成长的机会，分析薄弱点针对性突破")

    return {
        "likely_reasons": likely_reasons
        if likely_reasons
        else ["需要更多复盘数据来分析原因"],
        "strengths_to_keep": strengths_to_keep,
        "next_focus": next_focus,
        "encouragement": "。".join(encouragement_parts) + "。",
    }
