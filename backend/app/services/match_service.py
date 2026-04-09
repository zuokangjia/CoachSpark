import asyncio
from sqlalchemy.orm import Session

from fastapi import HTTPException

from app.ai.graphs.match_graph import build_match_graph
from app.db.models import Resume
from app.core.logging import logger

_match_graph = None


def get_match_graph():
    global _match_graph
    if _match_graph is None:
        _match_graph = build_match_graph()
    return _match_graph


def build_resume_text_from_model(resume: Resume) -> str:
    parts = []
    if resume.full_name:
        parts.append(f"姓名: {resume.full_name}")
    if resume.email:
        parts.append(f"邮箱: {resume.email}")
    if resume.phone:
        parts.append(f"电话: {resume.phone}")
    if resume.summary:
        parts.append(f"\n个人简介:\n{resume.summary}")
    if resume.skills:
        parts.append(f"\n技能:\n{', '.join(resume.skills)}")
    if resume.education:
        parts.append("\n教育背景:")
        for edu in resume.education:
            school = edu.get("school", "")
            degree = edu.get("degree", "")
            major = edu.get("major", "")
            period = ""
            if edu.get("start_date") and edu.get("end_date"):
                period = f" ({edu['start_date']} - {edu['end_date']})"
            elif edu.get("start_date"):
                period = f" ({edu['start_date']} - 至今)"
            line = f"  {school} {degree} {major}{period}"
            if edu.get("description"):
                line += f"\n    {edu['description']}"
            parts.append(line)
    if resume.work_experience:
        parts.append("\n工作经历:")
        for work in resume.work_experience:
            company = work.get("company", "")
            position = work.get("position", "")
            period = ""
            if work.get("start_date") and work.get("end_date"):
                period = f" ({work['start_date']} - {work['end_date']})"
            elif work.get("start_date"):
                period = f" ({work['start_date']} - 至今)"
            parts.append(f"  {company} | {position}{period}")
            if work.get("description"):
                parts.append(f"    {work['description']}")
            if work.get("technologies"):
                parts.append(f"    技术栈: {work['technologies']}")
    if resume.projects:
        parts.append("\n项目经验:")
        for proj in resume.projects:
            name = proj.get("name", "")
            role = proj.get("role", "")
            period = ""
            if proj.get("start_date") and proj.get("end_date"):
                period = f" ({proj['start_date']} - {proj['end_date']})"
            elif proj.get("start_date"):
                period = f" ({proj['start_date']} - 至今)"
            parts.append(f"  {name} | {role}{period}")
            if proj.get("description"):
                parts.append(f"    {proj['description']}")
            if proj.get("technologies"):
                parts.append(f"    技术栈: {proj['technologies']}")
            if proj.get("achievements"):
                parts.append(f"    成果: {proj['achievements']}")
    if resume.certifications:
        parts.append(f"\n证书: {', '.join(resume.certifications)}")
    return "\n".join(parts)


async def analyze_match(jd_text: str, resume_text: str) -> dict:
    graph = get_match_graph()
    try:
        result = await asyncio.to_thread(
            graph.invoke,
            {
                "jd_text": jd_text,
                "resume_text": resume_text,
                "jd_requirements": [],
                "resume_info": [],
                "match_percentage": 0,
                "strengths": [],
                "gaps": [],
                "suggestions": [],
            },
        )
    except Exception as e:
        logger.error(f"Match analysis failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI analysis service is temporarily unavailable. Please try again later.",
        )
    return {
        "match_percentage": result.get("match_percentage", 0),
        "strengths": result.get("strengths", []),
        "gaps": result.get("gaps", []),
        "suggestions": result.get("suggestions", []),
    }


async def analyze_match_with_stored_resume(jd_text: str, db: Session) -> dict:
    resume = db.query(Resume).first()
    if not resume:
        return await analyze_match(jd_text, "")
    resume_text = build_resume_text_from_model(resume)
    return await analyze_match(jd_text, resume_text)
