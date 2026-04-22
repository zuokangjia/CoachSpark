import re
import asyncio
import json as json_lib
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import (
    Question,
    QuestionCategory,
    UserQuestionPerformance,
    KnowledgeItem,
    GeneratedQuestion,
    EightPartTemplate,
    Drill,
    DrillSession,
    generate_uuid,
)
from app.services import practice_service
from app.core.logging import logger
from app.ai.json_utils import safe_parse_json, call_llm_with_retries


router = APIRouter(prefix="/practice", tags=["practice"])


class CategoryResponse(BaseModel):
    id: str
    name: str
    parent_id: str | None
    description: str

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}


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
    """获取知识领域分类列表（基于知识库类别）"""
    categories = (
        db.query(
            KnowledgeItem.category,
            func.count(KnowledgeItem.id).label("count"),
        )
        .group_by(KnowledgeItem.category)
        .order_by(KnowledgeItem.category)
        .all()
    )
    return {
        "items": [
            {
                "id": c[0],
                "name": c[0],
                "parent_id": None,
                "description": f"{c[1]} 条知识",
            }
            for c in categories
        ]
    }


class CreateCategoryRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    parent_id: str | None = None


class UpdateCategoryRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    parent_id: str | None = None


@router.post("/categories", response_model=CategoryResponse)
def create_category(
    request: CreateCategoryRequest,
    db: Session = Depends(get_db),
) -> CategoryResponse:
    """创建知识领域分类"""
    existing = (
        db.query(QuestionCategory).filter(QuestionCategory.name == request.name).first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="分类已存在")

    category = QuestionCategory(
        id=generate_uuid(),
        name=request.name,
        description=request.description,
        parent_id=request.parent_id,
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    return CategoryResponse(
        id=category.id,
        name=category.name,
        parent_id=category.parent_id,
        description=category.description or "",
    )


@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: str,
    request: UpdateCategoryRequest,
    db: Session = Depends(get_db),
) -> CategoryResponse:
    """更新知识领域分类"""
    category = (
        db.query(QuestionCategory).filter(QuestionCategory.id == category_id).first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    if request.name is not None:
        existing = (
            db.query(QuestionCategory)
            .filter(
                QuestionCategory.name == request.name,
                QuestionCategory.id != category_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="分类名称已存在")
        category.name = request.name

    if request.description is not None:
        category.description = request.description

    if request.parent_id is not None:
        if request.parent_id == category_id:
            raise HTTPException(status_code=400, detail="不能将自己设为父分类")
        category.parent_id = request.parent_id

    db.commit()
    db.refresh(category)

    return CategoryResponse(
        id=category.id,
        name=category.name,
        parent_id=category.parent_id,
        description=category.description or "",
    )


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: str,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """删除知识领域分类"""
    category = (
        db.query(QuestionCategory).filter(QuestionCategory.id == category_id).first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    questions_in_category = (
        db.query(Question).filter(Question.category_id == category_id).count()
    )
    if questions_in_category > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该分类下有 {questions_in_category} 道题目，无法删除",
        )

    drills_with_topic = db.query(Drill).filter(Drill.topic == category.name).count()
    if drills_with_topic > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该分类下有 {drills_with_topic} 个题目组，无法删除",
        )

    db.delete(category)
    db.commit()

    return {"message": "分类删除成功"}


# ============== 知识库 (Knowledge Base) API ==============


class KnowledgeItemResponse(BaseModel):
    id: str
    category: str
    title: str
    content: str
    concepts: list[str]
    examples: list[str]
    tags: list[str]
    difficulty_min: int
    difficulty_max: int
    created_at: str

    model_config = {"from_attributes": True}


class CreateKnowledgeItemRequest(BaseModel):
    category: str = Field(default="未分类", max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(default="")
    concepts: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    difficulty_min: int = Field(default=1, ge=1, le=5)
    difficulty_max: int = Field(default=5, ge=1, le=5)


class UpdateKnowledgeItemRequest(BaseModel):
    category: str | None = None
    title: str | None = None
    content: str | None = None
    concepts: list[str] | None = None
    examples: list[str] | None = None
    tags: list[str] | None = None
    difficulty_min: int | None = None
    difficulty_max: int | None = None


@router.get("/knowledge")
def list_knowledge_items(
    category: str | None = None,
    search: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    query = db.query(KnowledgeItem)
    if category:
        query = query.filter(KnowledgeItem.category == category)
    if search:
        query = query.filter(
            KnowledgeItem.title.ilike(f"%{search}%")
            | KnowledgeItem.content.ilike(f"%{search}%")
        )
    total = query.count()
    items = (
        query.order_by(KnowledgeItem.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {
                "id": k.id,
                "category": k.category,
                "title": k.title,
                "content": k.content,
                "concepts": k.concepts or [],
                "examples": k.examples or [],
                "tags": k.tags or [],
                "difficulty_min": k.difficulty_min,
                "difficulty_max": k.difficulty_max,
                "created_at": k.created_at.isoformat() if k.created_at else "",
            }
            for k in items
        ],
        "total": total,
    }


@router.post("/knowledge", response_model=KnowledgeItemResponse)
def create_knowledge_item(
    request: CreateKnowledgeItemRequest,
    db: Session = Depends(get_db),
) -> KnowledgeItemResponse:
    item = KnowledgeItem(
        id=generate_uuid(),
        category=request.category,
        title=request.title,
        content=request.content,
        concepts=request.concepts,
        examples=request.examples,
        tags=request.tags,
        difficulty_min=request.difficulty_min,
        difficulty_max=request.difficulty_max,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return KnowledgeItemResponse(
        id=item.id,
        category=item.category,
        title=item.title,
        content=item.content,
        concepts=item.concepts or [],
        examples=item.examples or [],
        tags=item.tags or [],
        difficulty_min=item.difficulty_min,
        difficulty_max=item.difficulty_max,
        created_at=item.created_at.isoformat() if item.created_at else "",
    )


@router.put("/knowledge/{item_id}", response_model=KnowledgeItemResponse)
def update_knowledge_item(
    item_id: str,
    request: UpdateKnowledgeItemRequest,
    db: Session = Depends(get_db),
) -> KnowledgeItemResponse:
    item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="知识项不存在")
    if request.category is not None:
        item.category = request.category
    if request.title is not None:
        item.title = request.title
    if request.content is not None:
        item.content = request.content
    if request.concepts is not None:
        item.concepts = request.concepts
    if request.examples is not None:
        item.examples = request.examples
    if request.tags is not None:
        item.tags = request.tags
    if request.difficulty_min is not None:
        item.difficulty_min = request.difficulty_min
    if request.difficulty_max is not None:
        item.difficulty_max = request.difficulty_max
    db.commit()
    db.refresh(item)
    return KnowledgeItemResponse(
        id=item.id,
        category=item.category,
        title=item.title,
        content=item.content,
        concepts=item.concepts or [],
        examples=item.examples or [],
        tags=item.tags or [],
        difficulty_min=item.difficulty_min,
        difficulty_max=item.difficulty_max,
        created_at=item.created_at.isoformat() if item.created_at else "",
    )


@router.delete("/knowledge/{item_id}")
def delete_knowledge_item(
    item_id: str, db: Session = Depends(get_db)
) -> dict[str, str]:
    item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="知识项不存在")
    db.delete(item)
    db.commit()
    return {"message": "删除成功"}


# ============== 八股题目模板 (Eight-Part Template) API ==============


class EightPartTemplateResponse(BaseModel):
    id: str
    category: str
    title: str
    content: str
    answer_template: str
    difficulty: int
    tips: list[str]
    created_at: str

    model_config = {"from_attributes": True}


class CreateEightPartTemplateRequest(BaseModel):
    category: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(default="")
    answer_template: str = Field(default="")
    difficulty: int = Field(default=3, ge=1, le=5)
    tips: list[str] = Field(default_factory=list)


class UpdateEightPartTemplateRequest(BaseModel):
    category: str | None = None
    title: str | None = None
    content: str | None = None
    answer_template: str | None = None
    difficulty: int | None = None
    tips: list[str] | None = None


@router.get("/eight-part")
def list_eight_part_templates(
    category: str | None = None,
    difficulty: int | None = Query(None, ge=1, le=5),
    search: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """获取八股题目模板列表"""
    query = db.query(EightPartTemplate)
    if category:
        query = query.filter(EightPartTemplate.category == category)
    if difficulty:
        query = query.filter(EightPartTemplate.difficulty == difficulty)
    if search:
        query = query.filter(
            EightPartTemplate.title.ilike(f"%{search}%")
            | EightPartTemplate.content.ilike(f"%{search}%")
        )
    total = query.count()
    items = (
        query.order_by(EightPartTemplate.category, EightPartTemplate.difficulty)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {
                "id": t.id,
                "category": t.category,
                "title": t.title,
                "content": t.content,
                "answer_template": t.answer_template,
                "difficulty": t.difficulty,
                "tips": t.tips or [],
                "created_at": t.created_at.isoformat() if t.created_at else "",
            }
            for t in items
        ],
        "total": total,
    }


@router.get("/eight-part/categories")
def list_eight_part_categories(db: Session = Depends(get_db)) -> dict[str, Any]:
    """获取八股题目分类列表"""
    categories = (
        db.query(
            EightPartTemplate.category, func.count(EightPartTemplate.id).label("count")
        )
        .group_by(EightPartTemplate.category)
        .all()
    )
    return {
        "items": [{"name": c[0], "count": c[1]} for c in categories],
    }


@router.post("/eight-part", response_model=EightPartTemplateResponse)
def create_eight_part_template(
    request: CreateEightPartTemplateRequest,
    db: Session = Depends(get_db),
) -> EightPartTemplateResponse:
    """创建八股题目模板"""
    item = EightPartTemplate(
        id=generate_uuid(),
        category=request.category,
        title=request.title,
        content=request.content,
        answer_template=request.answer_template,
        difficulty=request.difficulty,
        tips=request.tips,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return EightPartTemplateResponse(
        id=item.id,
        category=item.category,
        title=item.title,
        content=item.content,
        answer_template=item.answer_template,
        difficulty=item.difficulty,
        tips=item.tips or [],
        created_at=item.created_at.isoformat() if item.created_at else "",
    )


@router.put("/eight-part/{item_id}", response_model=EightPartTemplateResponse)
def update_eight_part_template(
    item_id: str,
    request: UpdateEightPartTemplateRequest,
    db: Session = Depends(get_db),
) -> EightPartTemplateResponse:
    """更新八股题目模板"""
    item = db.query(EightPartTemplate).filter(EightPartTemplate.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="模板不存在")
    if request.category is not None:
        item.category = request.category
    if request.title is not None:
        item.title = request.title
    if request.content is not None:
        item.content = request.content
    if request.answer_template is not None:
        item.answer_template = request.answer_template
    if request.difficulty is not None:
        item.difficulty = request.difficulty
    if request.tips is not None:
        item.tips = request.tips
    db.commit()
    db.refresh(item)
    return EightPartTemplateResponse(
        id=item.id,
        category=item.category,
        title=item.title,
        content=item.content,
        answer_template=item.answer_template,
        difficulty=item.difficulty,
        tips=item.tips or [],
        created_at=item.created_at.isoformat() if item.created_at else "",
    )


@router.delete("/eight-part/{item_id}")
def delete_eight_part_template(
    item_id: str, db: Session = Depends(get_db)
) -> dict[str, str]:
    """删除八股题目模板"""
    item = db.query(EightPartTemplate).filter(EightPartTemplate.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="模板不存在")
    db.delete(item)
    db.commit()
    return {"message": "删除成功"}


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
        query = query.filter(Question.knowledge_points.contains(knowledge_point))

    if company:
        query = query.filter(Question.company_tags.contains(company))

    if search:
        search_filter = Question.title.ilike(f"%{search}%") | Question.content.ilike(
            f"%{search}%"
        )
        query = query.filter(search_filter)

    total = query.count()
    questions = (
        query.order_by(Question.created_at.desc()).offset(offset).limit(limit).all()
    )

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


class GenerateDrillRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=50)
    num_questions: int = Field(default=3, ge=1, le=10)


class GenerateDrillResponse(BaseModel):
    topic: str
    user_level: int
    generated_count: int
    drill_id: str
    drill_name: str
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
    drill_id: str | None = None
    drill_name: str | None = None
    questions: list[dict[str, Any]]


@router.post("/import-text", response_model=ImportTextResponse)
async def import_questions_from_text(
    request: ImportTextRequest,
    db: Session = Depends(get_db),
) -> ImportTextResponse:
    """
    从大段文本中解析并导入题目。
    使用 LLM 自动识别题目结构：标题、内容、答案模板、知识点、难度等。
    """
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

    result, raw_content = await call_llm_with_retries(
        llm, prompt, max_retries=2, parse_json=True
    )

    if result is None:
        logger.error(f"Import text parse error, raw: {raw_content[:200]}")
        raise HTTPException(status_code=400, detail="LLM 返回格式错误，无法解析")

    questions_list = result.get("questions", []) if isinstance(result, dict) else []
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

    db.flush()

    # 创建 Drill（题目组）
    question_ids = [q["id"] for q in imported]
    all_knowledge_points = []
    for q in imported:
        all_knowledge_points.extend(q.get("knowledge_points", []))
    all_knowledge_points = list(set(all_knowledge_points))
    avg_difficulty = (
        sum(q.get("difficulty", 3) for q in imported) // len(imported)
        if imported
        else 3
    )

    drill = Drill(
        id=generate_uuid(),
        name=f"{request.category_name} 导入练习",
        description=f"文本导入 - 包含 {len(imported)} 道题目",
        topic=request.category_name,
        difficulty=avg_difficulty,
        question_ids=question_ids,
        knowledge_points=all_knowledge_points,
        estimated_duration_minutes=len(imported) * 10,
        is_system=0,
        created_by="default-user",
    )
    db.add(drill)
    db.commit()

    return ImportTextResponse(
        imported_count=len(imported),
        drill_id=drill.id,
        drill_name=drill.name,
        questions=imported,
    )


# ============== 题目组 (Drill) API ==============


class DrillResponse(BaseModel):
    id: str
    name: str
    description: str
    topic: str
    difficulty: int
    question_count: int
    knowledge_points: list[str]
    estimated_duration_minutes: int
    is_system: int
    created_at: str


class DrillListResponse(BaseModel):
    items: list[DrillResponse]
    total: int


class DrillDetailResponse(BaseModel):
    id: str
    name: str
    description: str
    topic: str
    difficulty: int
    knowledge_points: list[str]
    estimated_duration_minutes: int
    questions: list[dict[str, Any]]


class StartDrillSessionRequest(BaseModel):
    drill_id: str


class StartDrillSessionResponse(BaseModel):
    session_id: str
    drill_id: str
    drill_name: str
    total_questions: int
    current_question_index: int
    current_question: dict[str, Any] | None


class SubmitDrillAnswerRequest(BaseModel):
    answer: str
    time_spent_seconds: int = 0


class SubmitDrillAnswerResponse(BaseModel):
    session_id: str
    question_index: int
    is_correct: bool
    score: int
    feedback: str
    next_question: dict[str, Any] | None
    is_complete: bool
    progress: dict[str, Any]


class DrillSessionHistoryItem(BaseModel):
    id: str
    drill_id: str
    drill_name: str
    drill_topic: str
    status: str
    total_questions: int
    answered_count: int
    average_score: int | None
    total_time_spent_seconds: int
    completed_at: str | None
    started_at: str


class DrillSessionHistoryResponse(BaseModel):
    items: list[DrillSessionHistoryItem]
    total: int


def _drill_to_response(drill: Drill) -> DrillResponse:
    return DrillResponse(
        id=drill.id,
        name=drill.name,
        description=drill.description or "",
        topic=drill.topic,
        difficulty=drill.difficulty,
        question_count=len(drill.question_ids) if drill.question_ids else 0,
        knowledge_points=drill.knowledge_points or [],
        estimated_duration_minutes=drill.estimated_duration_minutes,
        is_system=drill.is_system,
        created_at=drill.created_at.isoformat() if drill.created_at else "",
    )


@router.get("/drills", response_model=DrillListResponse)
def list_drills(
    topic: str | None = None,
    difficulty: int | None = Query(None, ge=1, le=5),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> DrillListResponse:
    """获取题目组列表，可按领域和难度过滤"""
    query = db.query(Drill)

    if topic:
        query = query.filter(Drill.topic == topic)
    if difficulty:
        query = query.filter(Drill.difficulty == difficulty)

    total = query.count()
    drills = (
        query.order_by(Drill.is_system.desc(), Drill.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return DrillListResponse(
        items=[_drill_to_response(d) for d in drills],
        total=total,
    )


@router.get("/drills/history", response_model=DrillSessionHistoryResponse)
def get_drill_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user_id: str = Query("default-user"),
) -> DrillSessionHistoryResponse:
    """获取题目组练习历史（整组记录）"""
    query = (
        db.query(DrillSession)
        .filter(
            DrillSession.user_id == user_id,
            DrillSession.status.in_(["completed", "abandoned"]),
        )
        .order_by(DrillSession.created_at.desc())
    )

    total = query.count()
    sessions = query.offset(offset).limit(limit).all()

    items = []
    for s in sessions:
        drill = db.query(Drill).filter(Drill.id == s.drill_id).first()
        items.append(
            DrillSessionHistoryItem(
                id=s.id,
                drill_id=s.drill_id,
                drill_name=drill.name if drill else "Unknown",
                drill_topic=drill.topic if drill else "Unknown",
                status=s.status,
                total_questions=len(drill.question_ids)
                if drill and drill.question_ids
                else 0,
                answered_count=len(s.answers) if s.answers else 0,
                average_score=s.average_score,
                total_time_spent_seconds=s.total_time_spent_seconds,
                completed_at=s.completed_at.isoformat() if s.completed_at else None,
                started_at=s.started_at.isoformat() if s.started_at else "",
            )
        )

    return DrillSessionHistoryResponse(items=items, total=total)


@router.get("/drills/{drill_id}", response_model=DrillDetailResponse)
def get_drill_detail(
    drill_id: str,
    db: Session = Depends(get_db),
) -> DrillDetailResponse:
    """获取题目组详情，包含所有题目"""
    drill = db.query(Drill).filter(Drill.id == drill_id).first()
    if not drill:
        raise HTTPException(status_code=404, detail="Drill not found")

    questions = []
    if drill.question_ids:
        for gid in drill.question_ids:
            gq = db.query(GeneratedQuestion).filter(GeneratedQuestion.id == gid).first()
            if gq:
                questions.append(
                    {
                        "id": gq.id,
                        "title": gq.title,
                        "content": gq.content,
                        "difficulty": gq.difficulty,
                        "knowledge_points": gq.knowledge_points or [],
                        "hints": gq.hints or [],
                        "answer_template": gq.answer_template,
                    }
                )

    return DrillDetailResponse(
        id=drill.id,
        name=drill.name,
        description=drill.description or "",
        topic=drill.topic,
        difficulty=drill.difficulty,
        knowledge_points=drill.knowledge_points or [],
        estimated_duration_minutes=drill.estimated_duration_minutes,
        questions=questions,
    )


@router.post("/drills/{drill_id}/start", response_model=StartDrillSessionResponse)
def start_drill_session(
    drill_id: str,
    db: Session = Depends(get_db),
    user_id: str = Query("default-user"),
) -> StartDrillSessionResponse:
    """开始一个题目组练习会话"""
    drill = db.query(Drill).filter(Drill.id == drill_id).first()
    if not drill:
        raise HTTPException(status_code=404, detail="Drill not found")

    # 检查是否有进行中的会话
    existing = (
        db.query(DrillSession)
        .filter(
            DrillSession.user_id == user_id,
            DrillSession.drill_id == drill_id,
            DrillSession.status == "in_progress",
        )
        .first()
    )

    if existing:
        current_question = None
        if drill.question_ids and existing.current_question_index < len(
            drill.question_ids
        ):
            gid = drill.question_ids[existing.current_question_index]
            gq = db.query(GeneratedQuestion).filter(GeneratedQuestion.id == gid).first()
            if gq:
                current_question = {
                    "id": gq.id,
                    "title": gq.title,
                    "content": gq.content,
                    "difficulty": gq.difficulty,
                    "knowledge_points": gq.knowledge_points or [],
                    "hints": gq.hints or [],
                }

        return StartDrillSessionResponse(
            session_id=existing.id,
            drill_id=drill.id,
            drill_name=drill.name,
            total_questions=len(drill.question_ids) if drill.question_ids else 0,
            current_question_index=existing.current_question_index,
            current_question=current_question,
        )

    # 创建新会话
    session = DrillSession(
        id=generate_uuid(),
        user_id=user_id,
        drill_id=drill_id,
        status="in_progress",
        current_question_index=0,
        answers=[],
        total_time_spent_seconds=0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # 获取第一题
    current_question = None
    if drill.question_ids:
        gid = drill.question_ids[0]
        gq = db.query(GeneratedQuestion).filter(GeneratedQuestion.id == gid).first()
        if gq:
            current_question = {
                "id": gq.id,
                "title": gq.title,
                "content": gq.content,
                "difficulty": gq.difficulty,
                "knowledge_points": gq.knowledge_points or [],
                "hints": gq.hints or [],
            }

    logger.info(f"Started drill session: {session.id} for drill: {drill_id}")
    return StartDrillSessionResponse(
        session_id=session.id,
        drill_id=drill.id,
        drill_name=drill.name,
        total_questions=len(drill.question_ids) if drill.question_ids else 0,
        current_question_index=0,
        current_question=current_question,
    )


async def _evaluate_drill_answer_async(
    db_session_factory,
    session_id: str,
    question_index: int,
    generated_question_id: str,
    answer: str,
    max_retries: int = 2,
):
    """后台异步评估答案并更新记录"""
    from app.ai.llm import get_llm

    db = db_session_factory()
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            gq = (
                db.query(GeneratedQuestion)
                .filter(GeneratedQuestion.id == generated_question_id)
                .first()
            )
            if not gq:
                logger.error(
                    f"GeneratedQuestion not found in async evaluation: {generated_question_id}"
                )
                return

            llm = get_llm()
            prompt = f"""你是一个面试教练，负责评估候选人的回答。

题目: {gq.title}
题目描述: {gq.content}
参考答案模板: {gq.answer_template}
用户回答: {answer}

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
    "feedback": str
}}
"""
            try:
                response = await llm.ainvoke(prompt)
                content = response.content.strip() if response.content else ""
            except Exception as e:
                logger.error(f"LLM invoke error in _evaluate_drill_answer_async: {e}")
                content = ""

            import re

            content = re.sub(
                r"<start_of_thought>.*?</end_of_thought>",
                "",
                content,
                flags=re.DOTALL | re.IGNORECASE,
            )
            content = re.sub(
                r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE
            )
            content = content.strip()

            if not content:
                evaluation = {"total_score": 50, "feedback": "评估服务暂时不可用"}
            elif content.startswith("```"):
                match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
                if match:
                    content = match.group(1).strip()
            try:
                import json as json_lib

                evaluation = json_lib.loads(content)
            except:
                evaluation = {
                    "total_score": 50,
                    "feedback": content[:200] if content else "评估失败",
                }

            session = (
                db.query(DrillSession).filter(DrillSession.id == session_id).first()
            )
            if session and session.answers:
                updated_answers = []
                matched = False
                for ans in session.answers:
                    if ans.get("question_index") == question_index:
                        ans["score"] = evaluation["total_score"]
                        ans["feedback"] = evaluation["feedback"]
                        ans["status"] = "evaluated"
                        ans["evaluation_details"] = evaluation
                        matched = True
                    updated_answers.append(ans)

                if matched:
                    raw_answers_json = json_lib.dumps(updated_answers)
                    db.execute(
                        text(
                            "UPDATE drill_sessions SET answers = :json WHERE id = :id"
                        ),
                        {"json": raw_answers_json, "id": session_id},
                    )
                    db.commit()

                    evaluated_scores = [
                        a.get("score")
                        for a in updated_answers
                        if a.get("score") is not None
                    ]
                    if evaluated_scores:
                        avg_score = round(sum(evaluated_scores) / len(evaluated_scores))
                        total_score = sum(evaluated_scores)
                        db.execute(
                            text(
                                "UPDATE drill_sessions SET average_score = :avg, total_score = :total WHERE id = :id"
                            ),
                            {"avg": avg_score, "total": total_score, "id": session_id},
                        )
                        db.commit()

                logger.info(
                    f"Async evaluation completed: session={session_id}, question={question_index}, score={evaluation['total_score']}"
                )
                return

        except Exception as e:
            last_error = str(e)
            logger.warning(f"Async evaluation attempt {attempt + 1} failed: {e}")
            if attempt < max_retries:
                import asyncio

                await asyncio.sleep(2**attempt)
                continue

    if last_error:
        try:
            session = (
                db.query(DrillSession).filter(DrillSession.id == session_id).first()
            )
            if session and session.answers:
                answers = list(session.answers)
                for ans in answers:
                    if ans.get("question_index") == question_index:
                        ans["status"] = "failed"
                        ans["feedback"] = f"评估失败: {last_error[:100]}"
                        ans["error"] = last_error
                        break
                session.answers = answers
                db.commit()
        except Exception as log_err:
            logger.error(f"Failed to mark answer as failed: {log_err}")
    else:
        logger.error(
            f"Async evaluation failed after {max_retries} retries: session={session_id}, question={question_index}"
        )
    db.close()


@router.post(
    "/drills/sessions/{session_id}/submit", response_model=SubmitDrillAnswerResponse
)
def submit_drill_answer(
    session_id: str,
    request: SubmitDrillAnswerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: str = Query("default-user"),
) -> SubmitDrillAnswerResponse:
    """
    提交题目组中当前题目的答案。

    设计原则：
    1. 立即返回下一题，不阻塞用户继续做题
    2. 后台异步评估答案（LLM调用可能较慢）
    3. 前端可以通过轮询获取评估结果
    """
    session = (
        db.query(DrillSession)
        .filter(
            DrillSession.id == session_id,
            DrillSession.user_id == user_id,
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Session is not in progress")

    drill = db.query(Drill).filter(Drill.id == session.drill_id).first()
    if not drill or not drill.question_ids:
        raise HTTPException(status_code=404, detail="Drill not found or empty")

    current_idx = session.current_question_index
    if current_idx >= len(drill.question_ids):
        raise HTTPException(status_code=400, detail="All questions already answered")

    generated_question_id = drill.question_ids[current_idx]
    gq = (
        db.query(GeneratedQuestion)
        .filter(GeneratedQuestion.id == generated_question_id)
        .first()
    )
    if not gq:
        raise HTTPException(status_code=404, detail="Question not found")

    answer_record = {
        "question_id": generated_question_id,
        "question_index": current_idx,
        "answer": request.answer,
        "score": None,
        "feedback": "正在评估中...",
        "time_spent_seconds": request.time_spent_seconds,
        "submitted_at": datetime.utcnow().isoformat(),
        "status": "pending",
    }

    answers = list(session.answers or [])
    answers.append(answer_record)
    session.answers = answers
    session.total_time_spent_seconds += request.time_spent_seconds

    is_complete = current_idx + 1 >= len(drill.question_ids)
    next_question = None

    if is_complete:
        session.status = "completed"
        session.completed_at = datetime.utcnow()
    else:
        session.current_question_index = current_idx + 1
        next_gid = drill.question_ids[current_idx + 1]
        next_gq = (
            db.query(GeneratedQuestion).filter(GeneratedQuestion.id == next_gid).first()
        )
        if next_gq:
            next_question = {
                "id": next_gq.id,
                "title": next_gq.title,
                "content": next_gq.content,
                "difficulty": next_gq.difficulty,
                "knowledge_points": next_gq.knowledge_points or [],
                "hints": next_gq.hints or [],
            }

    db.commit()

    from app.db.session import SessionLocal

    background_tasks.add_task(
        _evaluate_drill_answer_async,
        SessionLocal,
        session_id,
        current_idx,
        generated_question_id,
        request.answer,
    )

    # 构建进度
    progress = {
        "current": current_idx + 1,
        "total": len(drill.question_ids),
        "answered": len(answers),
        "average_score": session.average_score,
    }

    logger.info(
        f"Submitted drill answer (async): session={session_id}, question={current_idx}"
    )

    return SubmitDrillAnswerResponse(
        session_id=session_id,
        question_index=current_idx,
        is_correct=False,  # 尚未评估，默认为 false
        score=0,  # 尚未评估，默认为 0
        feedback="答案已提交，正在后台评估...",
        next_question=next_question,
        is_complete=is_complete,
        progress=progress,
    )


@router.get("/drills/sessions/{session_id}/result")
def get_drill_session_result(
    session_id: str,
    db: Session = Depends(get_db),
    user_id: str = Query("default-user"),
) -> dict[str, Any]:
    """获取题目组会话的完整结果，包含题目详情"""
    session = (
        db.query(DrillSession)
        .filter(
            DrillSession.id == session_id,
            DrillSession.user_id == user_id,
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    drill = db.query(Drill).filter(Drill.id == session.drill_id).first()

    answers_with_questions = []
    if session.answers:
        for ans in session.answers:
            gq = (
                db.query(GeneratedQuestion)
                .filter(GeneratedQuestion.id == ans.get("question_id"))
                .first()
                if ans.get("question_id")
                else None
            )
            answers_with_questions.append(
                {
                    "question_index": ans.get("question_index"),
                    "question_id": ans.get("question_id"),
                    "question_title": gq.title if gq else "",
                    "question_content": gq.content if gq else "",
                    "question_difficulty": gq.difficulty if gq else 0,
                    "answer": ans.get("answer"),
                    "score": ans.get("score"),
                    "feedback": ans.get("feedback"),
                    "status": ans.get("status"),
                    "time_spent_seconds": ans.get("time_spent_seconds"),
                    "submitted_at": ans.get("submitted_at"),
                    "evaluation_details": ans.get("evaluation_details"),
                }
            )

    return {
        "session_id": session.id,
        "drill_id": session.drill_id,
        "drill_name": drill.name if drill else "Unknown",
        "drill_topic": drill.topic if drill else "Unknown",
        "status": session.status,
        "total_questions": len(drill.question_ids)
        if drill and drill.question_ids
        else 0,
        "answered_count": len(session.answers) if session.answers else 0,
        "average_score": session.average_score,
        "total_score": session.total_score,
        "total_time_spent_seconds": session.total_time_spent_seconds,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat()
        if session.completed_at
        else None,
        "answers": answers_with_questions,
    }
