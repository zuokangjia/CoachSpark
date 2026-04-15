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

请用 JSON 格式返回：
{{
    "scores": {{"completeness": int, "accuracy": int, "clarity": int, "depth": int}},
    "total_score": int,
    "feedback": str,
    "improvement_suggestions": list[str]
}}
"""
    response = await llm.ainvoke(prompt)
    result = json.loads(response.content)
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


def submit_answer(
    db: Session,
    question_id: str,
    submitted_answer: str,
    time_spent_seconds: int = 0,
    user_id: str = DEFAULT_USER_ID,
) -> dict[str, Any]:
    """
    提交答案的完整流程
    """
    import asyncio

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise ValueError(f"Question not found: {question_id}")

    before_dims = {
        d.dimension: d.level
        for d in db.query(UserSkillState).filter(UserSkillState.user_id == user_id).all()
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

    evaluation = asyncio.run(evaluate_answer(question, submitted_answer))

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
        for d in db.query(UserSkillState).filter(UserSkillState.user_id == user_id).all()
    }
    dimension_changes = []
    for dim, after_level in after_dims.items():
        before_level = before_dims.get(dim)
        if before_level is not None and before_level != after_level:
            dimension_changes.append({
                "dimension": dim,
                "before": before_level,
                "after": after_level,
                "delta": after_level - before_level,
            })

    return {
        "performance_id": performance.id,
        "score": evaluation["total_score"],
        "feedback": evaluation["feedback"],
        "evaluation_details": evaluation,
        "dimension_changes": dimension_changes,
        "knowledge_points_recorded": question.knowledge_points or [],
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
        questions = (
            db.query(Question)
            .order_by(func.random())
            .limit(limit)
            .all()
        )
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
        candidates = (
            db.query(Question)
            .filter(
                Question.id.notin_(seen_ids),
                Question.difficulty <= target_difficulty + 1,
            )
            .all()
        )

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
        remaining = (
            db.query(Question)
            .filter(
                Question.id.notin_(seen_ids),
                Question.id.notin_(done_question_ids),
            )
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
    专项强化：按领域生成新题目。

    难度策略（参考 TechSpar）：
    - 用户 level 1-2：基础概念为主（难度 1-2）
    - 用户 level 2-3：深度理解 + 简单应用（难度 3）
    - 用户 level 4-5：场景分析 + 系统设计（难度 4-5）

    生成后存入题库，返回生成的题目列表。
    """
    from app.ai.llm import get_llm
    from app.services.persona_v2_service import get_latest_persona

    llm = get_llm()

    # 查询用户在该领域的 skill level
    skill_state = (
        db.query(UserSkillState)
        .filter(
            UserSkillState.user_id == user_id,
            UserSkillState.dimension == topic,
        )
        .first()
    )
    user_level = skill_state.level if skill_state else 1

    # 根据 level 确定难度分布
    # Level 1-2: 基础为主；Level 3: 中等；Level 4-5: 进阶
    if user_level <= 2:
        difficulty_range = "1-2"
        focus_hint = "重点考察基础概念和核心原理"
    elif user_level == 3:
        difficulty_range = "2-3"
        focus_hint = "重点考察深度理解和实际应用"
    else:
        difficulty_range = "3-5"
        focus_hint = "重点考察场景分析和系统设计能力"

    # 获取用户画像上下文（薄弱点）
    persona = get_latest_persona(db, user_id=user_id)
    weak_points = persona.get("key_weaknesses", [])
    context_hint = ""
    if weak_points:
        context_hint = f"用户在以下知识点有薄弱点：{', '.join(weak_points[:3])}。生成题目时可适当覆盖这些方向。"

    prompt = f"""你是一个面试教练，负责根据用户的技能水平和薄弱点，生成针对性的面试练习题。

## 要求
1. 生成 {num_questions} 道题目，难度范围 {difficulty_range}
2. {focus_hint}
3. 题目类型包括：概念解释、手写实现、场景分析、系统设计等
4. 每道题目要有参考答案模板（关键得分点）
5. 提供 1-2 个 hints（启发思路但不直接给答案）

## 用户信息
- 领域：{topic}
- 当前水平：Level {user_level}/5
- {context_hint}

## 输出格式
请用 JSON 格式返回：
{{
    "questions": [
        {{
            "title": "题目标题（简洁描述问题）",
            "content": "题目详细描述，包含背景和具体要求",
            "answer_template": "参考答案模板，列出关键得分点",
            "difficulty": 1-5 的整数难度,
            "knowledge_points": ["知识点1", "知识点2"],
            "company_tags": [],
            "hints": ["提示1", "提示2"]
        }}
    ]
}}

请只返回 JSON，不要有其他文字。
"""
    response = await llm.ainvoke(prompt)
    try:
        parsed = json.loads(response.content)
    except json.JSONDecodeError:
        raise ValueError("LLM 返回格式错误，无法生成题目")

    questions_list = parsed.get("questions", [])
    if not questions_list:
        raise ValueError("未生成任何题目")

    # 查找或创建分类
    category = (
        db.query(QuestionCategory)
        .filter(QuestionCategory.name == topic)
        .first()
    )
    if not category:
        category = QuestionCategory(
            id=generate_uuid(),
            name=topic,
            description=f"专项强化生成 - {topic}",
        )
        db.add(category)
        db.flush()

    # 存入题库
    generated = []
    for q_data in questions_list:
        q = Question(
            id=generate_uuid(),
            category_id=category.id,
            title=q_data.get("title", "")[:255],
            content=q_data.get("content", ""),
            answer_template=q_data.get("answer_template", ""),
            difficulty=max(1, min(5, int(q_data.get("difficulty", 3)))),
            knowledge_points=q_data.get("knowledge_points", []),
            company_tags=q_data.get("company_tags", []),
            hints=q_data.get("hints", []),
        )
        db.add(q)
        generated.append(q)

    db.commit()

    return {
        "topic": topic,
        "user_level": user_level,
        "generated_count": len(generated),
        "questions": [_question_to_dict(q) for q in generated],
    }
