from typing import TypedDict, List, Any
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.ai.llm import get_llm
from app.ai.prompts.prep import PREP_SYSTEM_PROMPT, PREP_USER_PROMPT

"""
Design: Interview Prep Plan LangGraph
核心思想：状态机流水线：prioritize (优先级排序) -> extract_jd (JD方向提取)
-> allocate (按日任务分配) -> details (每日任务细节补全)。
通过 _promote_weak_points 确保薄弱点在前两天被优先覆盖，
通过 _normalize_daily_tasks 标准化 LLM 输出，确保数据一致性。
"""


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


def _extract_question_knowledge_points(task_text: str) -> List[str]:
    """从题库练习任务中提取知识点标签
    
    匹配格式如：
    - "完成 2 道 python_async 题库练习"
    - "完成 3 道微服务架构相关题目"
    """
    import re
    patterns = [
        r"完成\s*\d+\s*道\s*([a-z_]+)\s*题库练习",
        r"完成\s*\d+\s*道\s*(.+?)(?:相关|专项)?(?:题目|练习|题库)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, task_text, re.IGNORECASE)
        if match:
            kp = match.group(1).strip()
            return [kp]
    return []


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
        
        # 提取知识点标签（用于后续匹配题库题目）
        knowledge_points = raw.get("knowledge_points", [])
        if not knowledge_points:
            # 从任务文本中自动提取
            for task in tasks:
                kps = _extract_question_knowledge_points(task)
                knowledge_points.extend(kps)
            # 也去重
            knowledge_points = list(dict.fromkeys(knowledge_points))

        normalized_days.append(
            {
                "day": day,
                "focus": focus,
                "priority": priority,
                "tasks": tasks,
                "total_minutes": total_minutes,
                "completed_task_indexes": completed_indexes,
                "completed": completed,
                "knowledge_points": knowledge_points,  # 新增：关联的知识点
                "question_ids": raw.get("question_ids", []),  # 新增：关联的题目ID
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
                "knowledge_points": [],
                "question_ids": [],
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
    """
    单次 LLM 调用生成完整备战计划。
    优化：合并 allocate + details 为一次调用，减少网络延迟。
    """
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


def build_prep_graph():
    """
    优化后的图：3 节点 -> 2 节点
    prioritize -> extract_jd -> allocate (END)
    移除了单独的 details 节点，在 allocate 中直接生成完整计划。
    """
    from langgraph.graph import StateGraph, END

    graph = StateGraph(PrepState)
    graph.add_node("prioritize", prioritize_weak_points)
    graph.add_node("extract_jd", extract_jd_directions)
    graph.add_node("allocate", allocate_tasks_by_day)

    graph.set_entry_point("prioritize")
    graph.add_edge("prioritize", "extract_jd")
    graph.add_edge("extract_jd", "allocate")
    graph.add_edge("allocate", END)

    return graph.compile()
