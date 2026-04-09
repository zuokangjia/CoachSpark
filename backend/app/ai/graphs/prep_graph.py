from typing import TypedDict, List, Any
import re

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


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _normalize_priority(value: Any) -> str:
    text = _to_text(value).lower()
    if text in {"high", "h", "p0", "高", "高优先级"}:
        return "high"
    if text in {"low", "l", "p2", "低", "低优先级"}:
        return "low"
    return "medium"


def _extract_minutes(task_text: str) -> int:
    match = re.search(r"(\d+)\s*(分钟|min)", task_text, re.IGNORECASE)
    if not match:
        return 0
    minutes = int(match.group(1))
    return max(0, min(240, minutes))


def _normalize_tasks(tasks: Any) -> List[str]:
    if not isinstance(tasks, list):
        tasks = []
    normalized: List[str] = []
    seen = set()
    for task in tasks:
        text = _to_text(task)
        if not text:
            continue
        if text in seen:
            continue
        seen.add(text)
        normalized.append(text)
        if len(normalized) >= 5:
            break
    return normalized


def _build_fallback_tasks(focus: str) -> List[str]:
    topic = focus or "核心薄弱点"
    return [
        f"阅读 {topic} 相关官方文档并整理 8 条关键笔记（45 分钟）",
        f"完成 2 道 {topic} 练习题并写下解题思路（35 分钟）",
        f"围绕 {topic} 进行 1 次 3 分钟口述复盘并记录 3 个卡点（20 分钟）",
    ]


def _promote_weak_points(
    normalized_days: List[dict], weak_points: List[str]
) -> List[dict]:
    if not normalized_days or not weak_points:
        return normalized_days

    weak_topic_pairs = [
        (_to_text(topic), _to_text(topic).lower())
        for topic in weak_points
        if _to_text(topic)
    ]
    if not weak_topic_pairs:
        return normalized_days

    def day_score(day: dict) -> int:
        focus_text = _to_text(day.get("focus", "")).lower()
        tasks_text = " ".join(_to_text(task).lower() for task in day.get("tasks", []))
        score = 0
        for _, topic_key in weak_topic_pairs:
            if topic_key and topic_key in focus_text:
                score += 2
            if topic_key and topic_key in tasks_text:
                score += 1
        return score

    scored_indices = [(idx, day_score(day)) for idx, day in enumerate(normalized_days)]
    candidates = [
        idx
        for idx, score in sorted(scored_indices, key=lambda item: item[1], reverse=True)
        if score > 0
    ]

    promoted = list(normalized_days)
    for target_pos in range(min(2, len(promoted))):
        if target_pos >= len(candidates):
            break
        source_idx = candidates[target_pos]
        if source_idx == target_pos:
            continue
        promoted[target_pos], promoted[source_idx] = (
            promoted[source_idx],
            promoted[target_pos],
        )
        for i, value in enumerate(candidates):
            if value == target_pos:
                candidates[i] = source_idx
                break

    for idx, day in enumerate(promoted):
        day["day"] = idx + 1
        if idx < min(2, len(weak_topic_pairs)) and day_score(day) == 0:
            topic = weak_topic_pairs[idx][0]
            day["focus"] = f"{_to_text(day.get('focus'))} · {topic}强化".strip(" ·")
    return promoted


def _normalize_daily_tasks(
    raw_tasks: Any,
    days_available: int,
    weak_points: List[str],
) -> List[dict]:
    if not isinstance(raw_tasks, list):
        raw_tasks = []

    normalized_days: List[dict] = []
    max_days = max(1, min(30, days_available or 1))

    for idx, raw in enumerate(raw_tasks):
        if not isinstance(raw, dict):
            continue
        day = raw.get("day", idx + 1)
        if not isinstance(day, int):
            day = idx + 1
        day = max(1, min(max_days, day))

        focus = _to_text(raw.get("focus")) or f"第 {day} 天重点"
        priority = _normalize_priority(raw.get("priority"))
        tasks = _normalize_tasks(raw.get("tasks", []))
        if len(tasks) < 3:
            tasks = _build_fallback_tasks(focus)

        raw_completed_indexes = raw.get("completed_task_indexes", [])
        if not isinstance(raw_completed_indexes, list):
            raw_completed_indexes = []
        completed_indexes = sorted(
            {
                int(index)
                for index in raw_completed_indexes
                if isinstance(index, int) and 0 <= index < len(tasks)
            }
        )
        completed = bool(raw.get("completed", False))
        if completed and not completed_indexes and tasks:
            completed_indexes = list(range(len(tasks)))
        completed = len(tasks) > 0 and len(completed_indexes) == len(tasks)

        total_minutes = sum(_extract_minutes(task) for task in tasks)
        if total_minutes <= 0:
            total_minutes = 100
        total_minutes = min(240, total_minutes)

        normalized_days.append(
            {
                "day": day,
                "focus": focus,
                "priority": priority,
                "tasks": tasks,
                "total_minutes": total_minutes,
                "completed_task_indexes": completed_indexes,
                "completed": completed,
            }
        )

        if len(normalized_days) >= max_days:
            break

    if not normalized_days:
        normalized_days = [
            {
                "day": 1,
                "focus": "核心薄弱点强化",
                "priority": "high",
                "tasks": _build_fallback_tasks("核心薄弱点"),
                "total_minutes": 100,
                "completed_task_indexes": [],
                "completed": False,
            }
        ]

    normalized_days.sort(key=lambda item: item["day"])
    return _promote_weak_points(normalized_days, weak_points)


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
    jd_text = ""
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if company is not None:
            jd_text = _to_text(getattr(company, "jd_text", ""))
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
    normalized = _normalize_daily_tasks(
        daily_tasks,
        state.get("days_available", 1),
        state.get("weak_points", []),
    )
    return {"daily_tasks": normalized}


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
    enhanced: Any = daily_tasks
    try:
        result = chain.invoke(
            {
                "weak_points": state.get("weak_points", []),
                "jd_directions": state.get("jd_directions", []),
                "plan": str(daily_tasks),
            }
        )
        if isinstance(result, dict):
            candidate = result.get("daily_tasks", [])
            enhanced = candidate if isinstance(candidate, list) else daily_tasks
        elif isinstance(result, list):
            enhanced = result
    except Exception:
        enhanced = daily_tasks

    normalized = _normalize_daily_tasks(
        enhanced,
        state.get("days_available", 1),
        state.get("weak_points", []),
    )
    return {"daily_tasks": normalized}


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
