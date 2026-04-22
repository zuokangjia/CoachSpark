import asyncio
import copy
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.graphs.prep_graph import build_prep_graph
from app.services.context_builder import ContextBuilder
from app.db.models import PrepPlan, Question, generate_uuid
from app.core.logging import logger
from app.core.skill_mapping import normalize_skill_name, expand_weak_points

_prep_graph = None

"""
Design: Personalized Prep Plan Generation
核心思想：根据用户薄弱点和 JD 方向，通过 prep_graph 生成按日拆分的备战计划。
每日的任务通过优先级和 LLM 推理分配，确保薄弱点优先被覆盖。
支持任务完成进度跟踪（completed_task_indexes），实现增量更新。
"""


def get_prep_graph():
    global _prep_graph
    if _prep_graph is None:
        _prep_graph = build_prep_graph()
    return _prep_graph


def find_questions_by_skill(
    db: Session,
    skill_name: str,
    limit: int = 2,
    exclude_ids: list[str] | None = None,
) -> list[Question]:
    """
    根据技能名称查找匹配的题库题目
    
    匹配策略：
    1. 将输入技能名标准化（映射到 canonical name）
    2. 查找 knowledge_points 包含该技能或其别名的题目
    3. 优先返回难度适中（2-4）的题目
    
    Args:
        db: 数据库会话
        skill_name: 技能名称（可以是 weak_point 或 knowledge_point）
        limit: 最多返回几道题目
        exclude_ids: 要排除的题目ID（已做过的）
    
    Returns:
        匹配的题目列表
    """
    from sqlalchemy import or_
    
    canonical = normalize_skill_name(skill_name)
    aliases = [canonical]  # 标准名本身
    
    # 获取所有可能的匹配名称
    from app.core.skill_mapping import get_skill_aliases
    aliases.extend(get_skill_aliases(canonical))
    
    # 去重并过滤空值
    aliases = list(dict.fromkeys([a.lower() for a in aliases if a]))
    
    if not aliases:
        return []
    
    # 构建查询：knowledge_points JSON 字段包含任一别名
    query = db.query(Question)
    
    # 使用 JSON 字段查询（SQLite 兼容方式）
    conditions = []
    for alias in aliases:
        # 检查 knowledge_points 是否包含该别名（JSON 数组包含查询）
        conditions.append(
            Question.knowledge_points.contains([alias])
        )
        # 也尝试大小写不敏感的匹配
        conditions.append(
            Question.knowledge_points.contains([alias.title()])
        )
    
    if conditions:
        query = query.filter(or_(*conditions))
    
    # 排除已做过的题目
    if exclude_ids:
        query = query.filter(~Question.id.in_(exclude_ids))
    
    # 按难度排序（优先 2-4 难度）
    questions = query.order_by(Question.difficulty).limit(limit * 2).all()
    
    # 优先选择难度适中的题目
    preferred = [q for q in questions if 2 <= q.difficulty <= 4]
    if len(preferred) >= limit:
        return preferred[:limit]
    
    # 不足时补充其他题目
    result = preferred
    for q in questions:
        if q not in result:
            result.append(q)
        if len(result) >= limit:
            break
    
    return result


def enrich_plan_with_questions(
    db: Session,
    daily_tasks: list[dict],
    weak_points: list[str],
) -> list[dict]:
    """
    为备战计划的每一天匹配具体的题库题目
    
    Args:
        db: 数据库会话
        daily_tasks: 生成的每日任务列表
        weak_points: 薄弱点列表
    
    Returns:
        增加了 question_ids 的每日任务列表
    """
    # 扩展薄弱点列表（包含别名）
    expanded_weak_points = expand_weak_points(weak_points)
    
    # 已分配的题目ID（避免重复）
    assigned_question_ids: set[str] = set()
    
    for day in daily_tasks:
        knowledge_points = day.get("knowledge_points", [])
        
        # 如果已有 knowledge_points，直接使用
        if knowledge_points:
            skills_to_match = knowledge_points
        else:
            # 否则从 focus 和 weak_points 推断
            focus = day.get("focus", "")
            # 匹配 focus 中包含的薄弱点
            skills_to_match = []
            for wp in expanded_weak_points:
                if wp.lower() in focus.lower() or focus.lower() in wp.lower():
                    skills_to_match.append(wp)
        
        # 为每个 skill 查找题目
        matched_questions = []
        for skill in skills_to_match[:2]:  # 每天最多关联 2 个技能
            questions = find_questions_by_skill(
                db,
                skill,
                limit=2,
                exclude_ids=list(assigned_question_ids),
            )
            for q in questions:
                if q.id not in assigned_question_ids:
                    matched_questions.append(q)
                    assigned_question_ids.add(q.id)
        
        # 更新 day 的 question_ids
        if matched_questions:
            day["question_ids"] = [q.id for q in matched_questions]
            day["matched_skills"] = skills_to_match[:2]  # 记录匹配的技能
            
            # 如果没有题库练习任务，添加一个
            has_practice_task = any(
                "题库练习" in task or "题目" in task
                for task in day.get("tasks", [])
            )
            if not has_practice_task:
                skill_name = skills_to_match[0] if skills_to_match else "相关知识点"
                day["tasks"].append(
                    f"完成 2 道 {skill_name} 题库练习，提交答案并查看评估（30 分钟）"
                )
    
    return daily_tasks


async def generate_prep_plan(
    db: Session,
    company_id: str,
    target_round: int,
    days_available: int,
    weak_points: list | None = None,
    jd_directions: list | None = None,
    interview_chain: list | None = None,
) -> dict:
    graph = get_prep_graph()

    cb = ContextBuilder(db)
    context = cb.build_prep_context(company_id)

    try:
        result = await asyncio.to_thread(
            graph.invoke,
            {
                "company_id": company_id,
                "target_round": target_round,
                "days_available": days_available,
                "weak_points": weak_points or [],
                "jd_directions": jd_directions or [],
                "interview_chain": interview_chain or [],
                "context": context,
                "daily_tasks": [],
            }
        )
    except Exception as e:
        logger.error(f"Prep plan generation failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI analysis service is temporarily unavailable. Please try again later.",
        )
    daily_tasks = result.get("daily_tasks", [])
    
    # 为薄弱点匹配具体题库题目
    if weak_points:
        daily_tasks = enrich_plan_with_questions(
            db,
            daily_tasks,
            weak_points,
        )
        logger.info(f"为备战计划匹配了 {sum(1 for d in daily_tasks if d.get('question_ids'))} 天的题库练习")

    plan = PrepPlan(
        id=generate_uuid(),
        company_id=company_id,
        target_round=target_round,
        days_available=days_available,
        daily_tasks=daily_tasks,
        generated_from=[str(wp) for wp in (weak_points or [])],
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    return {
        "prep_plan_id": plan.id,
        "daily_tasks": daily_tasks,
    }


def get_latest_prep_plan(db: Session, company_id: str) -> dict | None:
    plan = (
        db.query(PrepPlan)
        .filter(PrepPlan.company_id == company_id)
        .order_by(PrepPlan.created_at.desc())
        .first()
    )
    if not plan:
        return None
    return {
        "prep_plan_id": plan.id,
        "company_id": plan.company_id,
        "target_round": plan.target_round,
        "days_available": plan.days_available,
        "daily_tasks": plan.daily_tasks,
        "created_at": plan.created_at,
    }


def update_prep_task_completion(
    db: Session,
    prep_plan_id: str,
    day: int,
    task_index: int,
    completed: bool,
) -> dict:
    plan = db.query(PrepPlan).filter(PrepPlan.id == prep_plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Prep plan not found")

    raw_daily_tasks = getattr(plan, "daily_tasks", [])
    daily_tasks: list[dict[str, Any]] = (
        copy.deepcopy(raw_daily_tasks) if isinstance(raw_daily_tasks, list) else []
    )
    target_day = None
    for item in daily_tasks:
        if isinstance(item, dict) and int(item.get("day", -1)) == day:
            target_day = item
            break

    if not target_day:
        raise HTTPException(status_code=404, detail="Day task not found")

    tasks = target_day.get("tasks", [])
    if not isinstance(tasks, list) or task_index >= len(tasks):
        raise HTTPException(status_code=400, detail="Task index out of range")

    completed_indexes = target_day.get("completed_task_indexes", [])
    if not isinstance(completed_indexes, list):
        completed_indexes = []

    normalized_indexes = sorted(
        {
            int(idx)
            for idx in completed_indexes
            if isinstance(idx, int) and 0 <= idx < len(tasks)
        }
    )

    if completed and task_index not in normalized_indexes:
        normalized_indexes.append(task_index)
    elif not completed and task_index in normalized_indexes:
        normalized_indexes.remove(task_index)

    normalized_indexes = sorted(normalized_indexes)
    target_day["completed_task_indexes"] = normalized_indexes
    target_day["completed"] = len(tasks) > 0 and len(normalized_indexes) == len(tasks)

    setattr(plan, "daily_tasks", daily_tasks)
    db.commit()

    return {
        "prep_plan_id": plan.id,
        "daily_tasks": daily_tasks,
    }
