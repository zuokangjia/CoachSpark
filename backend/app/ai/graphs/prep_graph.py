from typing import TypedDict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.ai.llm import get_llm
from app.ai.prompts.prep import PREP_SYSTEM_PROMPT, PREP_USER_PROMPT


class PrepState(TypedDict):
    company_id: str
    target_round: int
    days_available: int
    weak_points: List[str]
    jd_directions: List[str]
    interview_chain: List[dict]
    context: str
    daily_tasks: List[dict]


def prioritize_weak_points(state: PrepState) -> dict:
    weak_points = state.get("weak_points", [])
    if not isinstance(weak_points, list):
        weak_points = []
    return {"weak_points": weak_points}


def extract_jd_directions(state: PrepState) -> dict:
    existing = state.get("jd_directions", [])
    if existing:
        return {"jd_directions": existing}

    company_id = state.get("company_id", "")
    if not company_id:
        return {"jd_directions": []}

    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是资深技术面试官。从以下岗位描述中提取核心技术方向和关键技能，重点关注候选人应该为下一轮面试准备的技术领域。返回 5-8 个具体的技术话题，使用中文。",
            ),
            ("human", "{jd_text}"),
        ]
    )
    chain = prompt | llm | JsonOutputParser()

    from app.db.session import SessionLocal
    from app.db.models import Company

    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        jd_text = company.jd_text if company and company.jd_text else ""
    finally:
        db.close()

    if not jd_text or len(jd_text) < 10:
        return {"jd_directions": []}

    try:
        result = chain.invoke({"jd_text": jd_text})
        directions = result if isinstance(result, list) else []
    except Exception:
        directions = []

    return {"jd_directions": directions}


def allocate_tasks_by_day(state: PrepState) -> dict:
    llm = get_llm()
    context = state.get("context", "")
    context_section = f"\n\n## 用户历史上下文\n{context}" if context else ""

    system_prompt = PREP_SYSTEM_PROMPT + context_section
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", PREP_USER_PROMPT),
        ]
    )
    chain = prompt | llm | JsonOutputParser()
    result = chain.invoke(
        {
            "target_round": state.get("target_round", 1),
            "days_available": state.get("days_available", 3),
            "weak_points": state.get("weak_points", []),
            "jd_directions": state.get("jd_directions", []),
            "interview_chain": state.get("interview_chain", []),
        }
    )
    daily_tasks = result.get("daily_tasks", []) if isinstance(result, dict) else []
    for i, task in enumerate(daily_tasks):
        if isinstance(task, dict):
            task.setdefault("day", i + 1)
            task.setdefault("completed", False)
    return {"daily_tasks": daily_tasks}


def generate_daily_details(state: PrepState) -> dict:
    daily_tasks = state.get("daily_tasks", [])
    if not daily_tasks:
        return {"daily_tasks": []}

    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是资深面试备战教练。以下是一份逐日备战计划，请为每天的任务补充更具体的细节：推荐具体的学习资源（文章名、文档章节、视频课程名）、具体的练习题目和口头复述的提示。保持原有结构但让每个任务更具可操作性。返回增强后的 daily_tasks JSON 数组。使用中文。",
            ),
            (
                "human",
                "薄弱点：{weak_points}\nJD 方向：{jd_directions}\n\n当前计划：\n{plan}",
            ),
        ]
    )
    chain = prompt | llm | JsonOutputParser()
    try:
        result = chain.invoke(
            {
                "weak_points": state.get("weak_points", []),
                "jd_directions": state.get("jd_directions", []),
                "plan": str(daily_tasks),
            }
        )
        enhanced = result if isinstance(result, list) else daily_tasks
        if isinstance(enhanced, dict) and "daily_tasks" in enhanced:
            enhanced = enhanced["daily_tasks"]
    except Exception:
        enhanced = daily_tasks

    for i, task in enumerate(enhanced):
        if isinstance(task, dict):
            task.setdefault("day", i + 1)
            task.setdefault("completed", False)

    return {"daily_tasks": enhanced}


def build_prep_graph():
    from langgraph.graph import StateGraph, END

    graph = StateGraph(PrepState)
    graph.add_node("prioritize", prioritize_weak_points)
    graph.add_node("extract_jd", extract_jd_directions)
    graph.add_node("allocate", allocate_tasks_by_day)
    graph.add_node("details", generate_daily_details)

    graph.set_entry_point("prioritize")
    graph.add_edge("prioritize", "extract_jd")
    graph.add_edge("extract_jd", "allocate")
    graph.add_edge("allocate", "details")
    graph.add_edge("details", END)

    return graph.compile()
