from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Question, QuestionCategory, UserQuestionPerformance
from app.services import practice_service


router = APIRouter(prefix="/practice", tags=["practice"])


class CategoryResponse(BaseModel):
    id: str
    name: str
    parent_id: str | None
    description: str

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    id: str
    category_id: str
    category_name: str
    title: str
    content: str
    difficulty: int
    knowledge_points: list[str]
    company_tags: list[str]
    question_type: str
    options: list[str] | None
    hints: list[str]

    class Config:
        from_attributes = True


class QuestionSubmitRequest(BaseModel):
    submitted_answer: str = Field(..., min_length=1)
    time_spent_seconds: int = Field(0, ge=0)


class SubmitResponse(BaseModel):
    performance_id: str
    score: int
    feedback: str
    evaluation_details: dict[str, Any]
    dimension_changes: list[dict[str, Any]]
    knowledge_points_recorded: list[str]  # 本次练习影响的知识点


class HistoryItem(BaseModel):
    id: str
    question_id: str
    question_title: str
    question_difficulty: int
    score: int
    submitted_at: str
    time_spent_seconds: int

    class Config:
        from_attributes = True


def _question_to_response(question: Question) -> dict[str, Any]:
    """转换 Question 模型为响应字典"""
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


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)) -> dict[str, Any]:
    """获取知识领域分类列表"""
    categories = db.query(QuestionCategory).all()
    return {
        "items": [
            {
                "id": c.id,
                "name": c.name,
                "parent_id": c.parent_id,
                "description": c.description or "",
            }
            for c in categories
        ]
    }


@router.get("/questions")
def list_questions(
    category: str | None = None,
    difficulty: int | None = Query(None, ge=1, le=5),
    knowledge_point: str | None = None,
    company: str | None = None,
    search: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """获取题目列表，支持过滤"""
    query = db.query(Question)

    if category:
        query = query.filter(Question.category_id == category)

    if difficulty:
        query = query.filter(Question.difficulty == difficulty)

    if knowledge_point:
        query = query.filter(
            Question.knowledge_points.contains(knowledge_point)
        )

    if company:
        query = query.filter(
            Question.company_tags.contains(company)
        )

    if search:
        search_filter = (
            Question.title.ilike(f"%{search}%") |
            Question.content.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    total = query.count()
    questions = query.order_by(Question.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "items": [_question_to_response(q) for q in questions],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/questions/{question_id}")
def get_question(question_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """获取题目详情"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return _question_to_response(question)


@router.post("/questions/{question_id}/submit", response_model=SubmitResponse)
def submit_answer(
    question_id: str,
    request: QuestionSubmitRequest,
    db: Session = Depends(get_db),
) -> SubmitResponse:
    """提交答案"""
    try:
        result = practice_service.submit_answer(
            db=db,
            question_id=question_id,
            submitted_answer=request.submitted_answer,
            time_spent_seconds=request.time_spent_seconds,
        )
        return SubmitResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/history")
def list_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user_id: str = Query("default-user"),
) -> dict[str, Any]:
    """获取练习历史"""
    query = db.query(UserQuestionPerformance).filter(
        UserQuestionPerformance.user_id == user_id
    )

    total = query.count()
    performances = (
        query.order_by(UserQuestionPerformance.submitted_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = []
    for p in performances:
        question = db.query(Question).filter(Question.id == p.question_id).first()
        items.append({
            "id": p.id,
            "question_id": p.question_id,
            "question_title": question.title if question else "",
            "question_difficulty": question.difficulty if question else 0,
            "score": p.score,
            "submitted_at": p.submitted_at.isoformat() if p.submitted_at else "",
            "time_spent_seconds": p.time_spent_seconds,
        })

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/recommend")
def recommend_questions(
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    user_id: str = Query("default-user"),
) -> dict[str, Any]:
    """基于薄弱点推荐题目"""
    return practice_service.recommend_questions(
        db=db,
        user_id=user_id,
        limit=limit,
    )


class GenerateDrillRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=50)
    num_questions: int = Field(default=3, ge=1, le=10)


class GenerateDrillResponse(BaseModel):
    topic: str
    user_level: int
    generated_count: int
    questions: list[dict[str, Any]]


@router.post("/generate", response_model=GenerateDrillResponse)
async def generate_topic_drill(
    request: GenerateDrillRequest,
    db: Session = Depends(get_db),
    user_id: str = Query("default-user"),
) -> GenerateDrillResponse:
    """
    专项强化：按领域生成新题目。

    根据用户在该领域的画像水平，动态调整难度分布。
    生成的题目会存入题库，可立即开始练习。
    """
    try:
        result = await practice_service.generate_topic_drill_questions(
            db=db,
            topic=request.topic,
            user_id=user_id,
            num_questions=request.num_questions,
        )
        return GenerateDrillResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class ImportTextRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=5000)
    category_name: str = Field(default="未分类", max_length=50)


class ImportTextResponse(BaseModel):
    imported_count: int
    questions: list[dict[str, Any]]


@router.post("/import-text", response_model=ImportTextResponse)
def import_questions_from_text(
    request: ImportTextRequest,
    db: Session = Depends(get_db),
) -> ImportTextResponse:
    """
    从大段文本中解析并导入题目。
    使用 LLM 自动识别题目结构：标题、内容、答案模板、知识点、难度等。
    """
    import asyncio
    import json
    from app.ai.llm import get_llm

    llm = get_llm()

    prompt = f"""你是一个面试题库管理员，负责从文本中解析出结构化的面试题目。

请从以下文本中提取所有面试题目，每道题目解析为 JSON 格式：

{{
    "questions": [
        {{
            "title": "题目标题/问题",
            "content": "题目详细描述或背景",
            "answer_template": "参考答案模板或要点",
            "difficulty": 1-5 的难度等级（1=入门，3=中等，5=极难）,
            "knowledge_points": ["知识点1", "知识点2"],
            "company_tags": ["公司名"]（如果没有可以不填）,
            "hints": ["提示1"]（如果没有可以不填）
        }}
    ]
}}

要求：
1. 难度根据题目复杂度判断：手写实现类=4-5，概念解释类=1-3
2. 知识点提取核心技术名词，如 React Hooks、闭包、Event Loop 等
3. 如果文本中没有提供难度/知识点，根據題目內容推斷
4. 只返回有效 JSON，不要有其他文字

待解析文本：
---
{request.text}
---
"""

    response = asyncio.run(llm.ainvoke(prompt))
    try:
        parsed = json.loads(response.content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="LLM 返回格式错误，无法解析")

    questions_list = parsed.get("questions", [])
    if not questions_list:
        raise HTTPException(status_code=400, detail="未识别到任何题目")

    # 查找或创建分类
    category = (
        db.query(QuestionCategory)
        .filter(QuestionCategory.name == request.category_name)
        .first()
    )
    if not category:
        from app.db.models import generate_uuid
        from datetime import datetime
        category = QuestionCategory(
            id=generate_uuid(),
            name=request.category_name,
            description=f"从文本导入的题目",
        )
        db.add(category)
        db.flush()

    from app.db.models import generate_uuid

    imported = []
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
        imported.append(_question_to_response(q))

    db.commit()

    return ImportTextResponse(
        imported_count=len(imported),
        questions=imported,
    )
