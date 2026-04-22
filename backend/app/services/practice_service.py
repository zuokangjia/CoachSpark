from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import (
    Question,
    QuestionCategory,
    UserQuestionPerformance,
    ProfileEvidence,
    UserSkillState,
    Drill,
    DrillSession,
    KnowledgeItem,
    GeneratedQuestion,
    generate_uuid,
)
from app.services.rag_retrieval_service import embed_evidence_texts


DEFAULT_USER_ID = "default-user"

"""
Design: Question Training System - Practice Service
核心流程：
1. evaluate_answer() - LLM 评估用户答案
2. ingest_practice_evidence() - 将练习表现转化为 ProfileEvidence
3. submit_answer() - 完整提交流程：评估 → 保存表现 → 生成证据 → 重建快照
4. recommend_questions() - 基于画像薄弱点推荐题目
"""

from app.ai.json_utils import safe_parse_json, clean_llm_response, call_llm_with_retries

import logging
import re

logger = logging.getLogger(__name__)


def _clean_llm_response(content: str) -> str:
    if not content:
        return ""
    # 移除 AI 思考标签 (Claude/Gemini 等)
    content = re.sub(
        r"<start_of_thought>.*?</end_of_thought>",
        "",
        content,
        flags=re.DOTALL | re.IGNORECASE,
    )
    content = re.sub(r"<think>.*?", "", content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r"<think>.*?", "", content, flags=re.DOTALL | re.IGNORECASE)
    return content.strip()


def _parse_feedback_text(content: str) -> dict[str, Any]:
    """
    从纯文本反馈中提取评分信息
    支持格式：
    - 综合得分: XX分
    - 完整性: X/20, 准确性: X/20 等
    """
    default_result = {
        "scores": {"completeness": 10, "accuracy": 10, "clarity": 10, "depth": 10},
        "total_score": 50,
        "feedback": content[:200] if content else "系统无法解析评估结果",
        "improvement_suggestions": ["请稍后重新提交获取完整评估"],
    }

    if not content:
        return default_result

    scores = {"completeness": 10, "accuracy": 10, "clarity": 10, "depth": 10}
    total_score = 50

    # 尝试提取综合得分
    score_match = re.search(r"[综总]分[：:]\s*(\d+)", content)
    if score_match:
        total_score = max(0, min(100, int(score_match.group(1))))

    # 尝试提取各项分数 (格式: "完整性: 15分" 或 "完整性 15/20")
    score_patterns = [
        (r"完整性[：:]\s*(\d+)", "completeness"),
        (r"准确[性度][：:]\s*(\d+)", "accuracy"),
        (r"逻辑[清晰度][：:]\s*(\d+)", "clarity"),
        (r"深度[与广度][：:]\s*(\d+)", "depth"),
    ]

    for pattern, key in score_patterns:
        match = re.search(pattern, content)
        if match:
            scores[key] = max(1, min(20, int(match.group(1))))

    return {
        "scores": scores,
        "total_score": total_score,
        "feedback": content[:200] if content else "系统无法解析评估结果",
        "improvement_suggestions": ["请稍后重新提交获取完整评估"],
    }


async def evaluate_answer(
    question: Question,
    submitted_answer: str,
) -> dict[str, Any]:
    """
    使用 LLM 评估用户答案，返回评分和反馈
    """
    from app.ai.llm import get_llm

    llm = get_llm()

    prompt = f"""你是一个面试教练，负责评估候选人的回答。

题目: {question.title}
题目描述: {question.content}
参考答案模板: {question.answer_template}
用户回答: {submitted_answer}

请从以下维度评估（每个维度 1-20 分）：
1. 答案完整性
2. 技术准确性
3. 逻辑清晰度
4. 深度与广度

最后给出 0-100 的综合得分和详细反馈。

请用严格 JSON 格式返回（不要包含 markdown 代码块标记）：
{{
    "scores": {{"completeness": int, "accuracy": int, "clarity": int, "depth": int}},
    "total_score": int,
    "feedback": str,
    "improvement_suggestions": list[str]
}}
"""
    try:
        response = await llm.ainvoke(prompt)
        content = response.content.strip() if response.content else ""
    except Exception as e:
        logger.error(f"LLM invoke error in evaluate_answer: {e}")
        content = ""

    # 清理 LLM 返回的特殊标记
    content = _clean_llm_response(content)

    # 如果内容为空，返回默认评估
    if not content:
        logger.warning(f"LLM returned empty content for question: {question.id}")
        return {
            "scores": {"completeness": 10, "accuracy": 10, "clarity": 10, "depth": 10},
            "total_score": 50,
            "feedback": "系统暂时无法评估，请稍后查看详细反馈。（LLM 返回为空）",
            "improvement_suggestions": ["请稍后重新提交获取完整评估"],
        }

    # 尝试从 markdown 代码块中提取 JSON
    if content.startswith("```"):
        # 提取 ```json ... ``` 或 ``` ... ``` 中的内容
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
        if match:
            content = match.group(1).strip()

    # 尝试解析 JSON
    try:
        result = json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning(
            f"JSON parse error in evaluate_answer: {e}, content: {content[:200]}"
        )
        # 尝试从文本中提取第一个 { } 包裹的内容
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(0))
            except json.JSONDecodeError:
                result = _parse_feedback_text(content)
        else:
            result = _parse_feedback_text(content)

    return result


def ingest_practice_evidence(
    db: Session,
    *,
    user_id: str = DEFAULT_USER_ID,
    question_id: str,
    score: int,
    evaluation_details: dict,
) -> list[ProfileEvidence]:
    """
    将练习表现转化为 ProfileEvidence
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return []

    knowledge_points = question.knowledge_points or []
    polarity = 1 if score >= 70 else -1
    event_time = datetime.now(timezone.utc).replace(tzinfo=None)

    evidences = []
    for kp in knowledge_points:
        evidence = ProfileEvidence(
            id=generate_uuid(),
            user_id=user_id,
            source_type="question_practice",
            source_id=question_id,
            dimension=str(kp),
            skill_name=str(kp),
            signal_type="strength" if polarity > 0 else "weakness",
            polarity=polarity,
            score=score,
            confidence=60,
            quote_text=f"题目: {question.title}",
            metadata_json={
                "from": "practice",
                "question_difficulty": question.difficulty,
                "evaluation": evaluation_details,
            },
            event_time=event_time,
        )
        evidences.append(evidence)
        db.add(evidence)

    if evidences:
        db.commit()
        embed_evidence_texts(db, user_id=user_id)

    return evidences


def update_matching_prep_plan(
    db: Session,
    question: Question,
    user_id: str = DEFAULT_USER_ID,
) -> dict[str, Any] | None:
    """
    检查是否有在途的备战计划包含此题目的知识点，返回匹配信息和提示

    Args:
        db: 数据库会话
        question: 刚完成的题目
        user_id: 用户ID

    Returns:
        匹配的计划信息或 None
    """
    from app.db.models import PrepPlan, Company
    from app.core.skill_mapping import normalize_skill_name

    if not question.knowledge_points:
        return None

    # 标准化题目的知识点
    question_skills = set()
    for kp in question.knowledge_points:
        canonical = normalize_skill_name(kp)
        if canonical:
            question_skills.add(canonical)
            # 也添加别名
            from app.core.skill_mapping import get_skill_aliases

            question_skills.update([a.lower() for a in get_skill_aliases(canonical)])

    if not question_skills:
        return None

    # 查找最新的在途备战计划（关联有 next_event_date 的公司）
    # 即：备战计划对应的公司有即将到来的面试
    latest_plan = (
        db.query(PrepPlan, Company)
        .join(Company, PrepPlan.company_id == Company.id)
        .filter(
            Company.next_event_date.isnot(None),  # 有 upcoming 面试
            Company.status.in_(["interviewing", "applied"]),  # 仍在面试流程中
        )
        .order_by(PrepPlan.created_at.desc())
        .first()
    )

    if not latest_plan:
        return None

    plan, company = latest_plan
    daily_tasks = plan.daily_tasks or []

    matched_days = []
    for day_idx, day in enumerate(daily_tasks):
        if not isinstance(day, dict):
            continue

        # 检查 knowledge_points 匹配
        day_skills = day.get("knowledge_points", [])
        day_question_ids = day.get("question_ids", [])

        # 匹配方式1：知识点名称匹配
        skill_match = False
        for ds in day_skills:
            canonical_ds = normalize_skill_name(ds)
            if canonical_ds and canonical_ds in question_skills:
                skill_match = True
                break

        # 匹配方式2：题目ID直接匹配
        id_match = question.id in day_question_ids

        if skill_match or id_match:
            matched_days.append(
                {
                    "day": day.get("day", day_idx + 1),
                    "focus": day.get("focus", ""),
                    "completed": day.get("completed", False),
                }
            )

    if matched_days:
        return {
            "matched": True,
            "prep_plan_id": plan.id,
            "company_id": company.id,
            "company_name": company.name,
            "matched_days": matched_days,
            "message": f"练习完成！该题目与 '{company.name}' 的备战计划相关，可前往更新进度。",
        }

    return None


async def submit_answer(
    db: Session,
    question_id: str,
    submitted_answer: str,
    time_spent_seconds: int = 0,
    user_id: str = DEFAULT_USER_ID,
) -> dict[str, Any]:
    """
    提交答案的完整流程
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise ValueError(f"Question not found: {question_id}")

    before_dims = {
        d.dimension: d.level
        for d in db.query(UserSkillState)
        .filter(UserSkillState.user_id == user_id)
        .all()
    }

    performance = UserQuestionPerformance(
        id=generate_uuid(),
        user_id=user_id,
        question_id=question_id,
        submitted_answer=submitted_answer,
        score=0,
        feedback="",
        evaluation_details={},
        time_spent_seconds=time_spent_seconds,
    )
    db.add(performance)
    db.commit()

    evaluation = await evaluate_answer(question, submitted_answer)

    performance.score = evaluation["total_score"]
    performance.feedback = evaluation["feedback"]
    performance.evaluation_details = evaluation
    db.commit()

    ingest_practice_evidence(
        db,
        user_id=user_id,
        question_id=question_id,
        score=evaluation["total_score"],
        evaluation_details=evaluation,
    )

    from app.services.persona_v2_service import rebuild_persona_snapshot

    rebuild_persona_snapshot(db, user_id=user_id, source_event_id=performance.id)

    after_dims = {
        d.dimension: d.level
        for d in db.query(UserSkillState)
        .filter(UserSkillState.user_id == user_id)
        .all()
    }
    dimension_changes = []
    for dim, after_level in after_dims.items():
        before_level = before_dims.get(dim)
        if before_level is not None and before_level != after_level:
            dimension_changes.append(
                {
                    "dimension": dim,
                    "before": before_level,
                    "after": after_level,
                    "delta": after_level - before_level,
                }
            )

    # 检查是否有匹配的备战计划
    prep_plan_match = update_matching_prep_plan(db, question, user_id=user_id)

    return {
        "performance_id": performance.id,
        "score": evaluation["total_score"],
        "feedback": evaluation["feedback"],
        "evaluation_details": evaluation,
        "dimension_changes": dimension_changes,
        "knowledge_points_recorded": question.knowledge_points or [],
        "prep_plan_match": prep_plan_match,  # 新增：匹配的备战计划信息
    }


def recommend_questions(
    db: Session,
    user_id: str = DEFAULT_USER_ID,
    limit: int = 5,
    exclude_done: bool = True,
) -> dict[str, Any]:
    """
    基于画像薄弱点推荐题目。

    推荐策略：
    1. 优先推荐薄弱点相关题目（level 最低的维度）
    2. 难度适配：略高于当前 level
    3. 知识点匹配：精确匹配或包含关系
    4. 排除已做过的题目
    5. 无画像时返回随机题目
    """
    # 获取用户的技能状态（不依赖快照，直接查表）
    skill_states = (
        db.query(UserSkillState)
        .filter(UserSkillState.user_id == user_id)
        .order_by(UserSkillState.level.asc(), UserSkillState.confidence.desc())
        .all()
    )

    # 有画像数据时：按 level 升序取前 N 个作为薄弱点
    # 无画像数据时：返回随机题目
    if not skill_states:
        questions = db.query(Question).order_by(func.random()).limit(limit).all()
        return {
            "recommended_questions": [_question_to_dict(q) for q in questions],
            "based_on_weak_points": [],
        }

    # 取 level 最低的 3 个作为推荐依据
    weak_states = skill_states[:3]
    weak_point_names = [s.dimension for s in weak_states]

    # 已做过的题目 ID
    done_question_ids = set()
    if exclude_done:
        done_ids = (
            db.query(UserQuestionPerformance.question_id)
            .filter(UserQuestionPerformance.user_id == user_id)
            .distinct()
            .all()
        )
        done_question_ids = {r[0] for r in done_ids}

    recommended = []
    seen_ids = set()

    for state in weak_states:
        if len(recommended) >= limit:
            break

        # 目标难度：当前 level + 1，向上取整
        target_difficulty = min((state.level or 1) + 1, 5)

        # 构建查询条件，只在有值时添加 notin_ 过滤
        query_filters = [Question.difficulty <= target_difficulty + 1]
        if seen_ids:
            query_filters.append(Question.id.notin_(seen_ids))

        candidates = db.query(Question).filter(*query_filters).all()

        for q in candidates:
            if q.id in done_question_ids:
                continue

            # 知识点匹配：精确匹配或包含关系
            # 例如：dimension="React Hooks"，question knowledge_points=["React Hooks", "useEffect"]
            q_kps = set(q.knowledge_points or [])
            matched = any(
                state.dimension == kp or state.dimension in kp or kp in state.dimension
                for kp in q_kps
            )
            if not matched:
                continue

            recommended.append(q)
            seen_ids.add(q.id)

    # 推荐不足时，补充随机新题
    if len(recommended) < limit:
        remaining_filters = [Question.id.notin_(done_question_ids)]
        if seen_ids:
            remaining_filters.append(Question.id.notin_(seen_ids))

        remaining = (
            db.query(Question)
            .filter(*remaining_filters)
            .order_by(func.random())
            .limit(limit - len(recommended))
            .all()
        )
        recommended.extend(remaining)

    return {
        "recommended_questions": [_question_to_dict(q) for q in recommended[:limit]],
        "based_on_weak_points": weak_point_names,
    }


def _question_to_dict(question: Question) -> dict[str, Any]:
    """转换 Question 模型为字典"""
    return {
        "id": question.id,
        "category_id": question.category_id,
        "category_name": question.category.name if question.category else "",
        "title": question.title,
        "content": question.content,
        "difficulty": question.difficulty,
        "knowledge_points": question.knowledge_points or [],
        "company_tags": question.company_tags or [],
        "question_type": question.question_type,
        "options": question.options,
        "hints": question.hints or [],
    }


async def generate_topic_drill_questions(
    db: Session,
    topic: str,
    user_id: str = DEFAULT_USER_ID,
    num_questions: int = 3,
) -> dict[str, Any]:
    """
    专项强化：基于知识库生成新题目。

    1. RAG 检索相关知识项
    2. AI 生成题目（基于知识项）
    3. 存储 GeneratedQuestion
    4. 创建 Drill
    """
    from app.ai.llm import get_llm
    from app.services.persona_v2_service import get_latest_persona

    llm = get_llm()

    skill_state = (
        db.query(UserSkillState)
        .filter(UserSkillState.user_id == user_id, UserSkillState.dimension == topic)
        .first()
    )
    user_level = skill_state.level if skill_state else 1

    difficulty_map = {1: "1-2", 2: "1-2", 3: "2-3", 4: "3-5", 5: "3-5"}
    focus_map = {
        1: "重点考察基础概念和核心原理",
        2: "重点考察基础概念和核心原理",
        3: "重点考察深度理解和实际应用",
        4: "重点考察场景分析和系统设计能力",
        5: "重点考察场景分析和系统设计能力",
    }
    difficulty_range = difficulty_map.get(user_level, "2-3")
    focus_hint = focus_map.get(user_level, "重点考察深度理解")

    knowledge_items = (
        db.query(KnowledgeItem).filter(KnowledgeItem.category == topic).limit(10).all()
    )

    if knowledge_items:
        knowledge_context = "\n\n".join(
            [
                f"### {k.title}\n{k.content}\n概念: {', '.join(k.concepts)}\n示例: {'; '.join(k.examples)}"
                for k in knowledge_items
            ]
        )
    else:
        knowledge_context = f"领域: {topic}（暂无知识库数据）"

    persona = get_latest_persona(db, user_id=user_id)
    weak_points = persona.get("key_weaknesses", [])
    context_hint = (
        f"用户在以下知识点有薄弱点：{', '.join(weak_points[:3])}。"
        if weak_points
        else ""
    )

    prompt = f"""你是一个面试教练，基于以下知识库内容生成面试练习题。

## 知识库内容
{knowledge_context}

## 要求
1. 生成 {num_questions} 道题目，难度范围 {difficulty_range}
2. {focus_hint}
3. {context_hint}
4. 每道题目要有参考答案模板和 hints

## 输出格式
JSON，只输出 JSON：
{{
    "questions": [
        {{
            "title": "题目标题",
            "content": "题目详细描述",
            "answer_template": "参考答案模板",
            "difficulty": 1-5,
            "knowledge_points": ["知识点"],
            "hints": ["提示"]
        }}
    ]
}}
"""

    result, raw_content = await call_llm_with_retries(
        llm, prompt, max_retries=2, parse_json=True
    )

    if result is None:
        logger.warning(f"LLM returned None, raw_content: {raw_content[:500]}")
        raise ValueError("LLM 返回格式错误")

    logger.info(f"LLM result type: {type(result)}, result: {str(result)[:300]}")

    if isinstance(result, dict):
        questions_list = result.get("questions", [])
    elif isinstance(result, list):
        questions_list = result
    else:
        questions_list = []

    if not questions_list:
        logger.warning(f"LLM returned no questions, result: {str(result)[:500]}")
        raise ValueError("未生成任何题目")

    try:
        avg_difficulty = sum(
            max(1, min(5, int(q.get("difficulty", 3)))) for q in questions_list
        ) // len(questions_list)
        if avg_difficulty < 1:
            avg_difficulty = 3

        all_kps = []
        for q in questions_list:
            all_kps.extend(q.get("knowledge_points", []))
        all_knowledge_points = list(set(all_kps))

        drill = Drill(
            id=generate_uuid(),
            name=f"{topic} 专项练习",
            description=f"AI 生成 - 包含 {len(questions_list)} 道题目",
            topic=topic,
            difficulty=avg_difficulty,
            question_ids=[],
            knowledge_points=all_knowledge_points,
            estimated_duration_minutes=len(questions_list) * 10,
            is_system=0,
            created_by=user_id,
        )
        db.add(drill)
        db.flush()

        generated = []
        for i, q_data in enumerate(questions_list):
            k_item = (
                knowledge_items[i % len(knowledge_items)] if knowledge_items else None
            )
            gq = GeneratedQuestion(
                id=generate_uuid(),
                drill_id=drill.id,
                knowledge_item_id=k_item.id if k_item else None,
                title=q_data.get("title", "")[:255],
                content=q_data.get("content", ""),
                answer_template=q_data.get("answer_template", ""),
                difficulty=max(1, min(5, int(q_data.get("difficulty", 3)))),
                knowledge_points=q_data.get("knowledge_points", []),
                hints=q_data.get("hints", []),
            )
            db.add(gq)
            generated.append(gq)

        drill.question_ids = [gq.id for gq in generated]
        db.commit()

        return {
            "topic": topic,
            "user_level": user_level,
            "generated_count": len(generated),
            "drill_id": drill.id,
            "drill_name": drill.name,
            "questions": [
                {
                    "id": gq.id,
                    "title": gq.title,
                    "difficulty": gq.difficulty,
                }
                for gq in generated
            ],
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save generated questions: {e}")
        raise ValueError(f"保存题目失败: {str(e)}")
