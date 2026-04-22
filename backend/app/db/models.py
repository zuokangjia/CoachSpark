import uuid
from datetime import date, datetime

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Date,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


def generate_uuid():
    return str(uuid.uuid4())


"""
Design: Core Data Models
核心设计：
- Company 是核心实体，通过 status 字段驱动状态机（applied -> interviewing -> passed/rejected）
- Interview 保存每次面试记录，包含 ai_analysis JSON 字段存储 LLM 分析结果
- ProfileEvidence 是画像证据系统的基础，每条证据关联 source 和 polarity（强弱标志）
- UserSkillState 聚合某维度的证据，计算 level/trend/confidence
- UserProfileSnapshot 是时点快照，支持历史对比
- PrepPlan 通过 daily_tasks JSON 存储按日拆分的备战计划
"""


class Company(Base):
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    position = Column(String(255), nullable=False)
    jd_text = Column(Text, nullable=True, default="")
    status = Column(String(50), nullable=False, default="applied")
    applied_date = Column(Date, nullable=False, default=date.today)
    next_event_date = Column(Date, nullable=True)
    next_event_type = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_companies_status", "status"),
        Index("ix_companies_applied_date", "applied_date"),
    )

    interviews = relationship(
        "Interview", back_populates="company", cascade="all, delete-orphan"
    )
    prep_plans = relationship(
        "PrepPlan", back_populates="company", cascade="all, delete-orphan"
    )
    offers = relationship(
        "Offer", back_populates="company", cascade="all, delete-orphan"
    )


class Offer(Base):
    __tablename__ = "offers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    salary = Column(String(255), nullable=True, default="")
    benefits = Column(Text, nullable=True, default="")
    offer_date = Column(Date, nullable=True)
    deadline = Column(Date, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    notes = Column(Text, nullable=True, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    company = relationship("Company", back_populates="offers")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    round = Column(Integer, nullable=False)
    interview_date = Column(Date, nullable=True)
    format = Column(String(50), nullable=True)
    interviewer = Column(String(255), nullable=True)
    raw_notes = Column(Text, nullable=True, default="")
    ai_analysis = Column(JSON, nullable=False, default=dict)
    expected_result_date = Column(Date, nullable=True)
    result_status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_interviews_company_id", "company_id"),
        Index("ix_interviews_company_round", "company_id", "round"),
    )

    company = relationship("Company", back_populates="interviews")


class PrepPlan(Base):
    __tablename__ = "prep_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    target_round = Column(Integer, nullable=False)
    days_available = Column(Integer, nullable=False)
    daily_tasks = Column(JSON, nullable=False, default=list)
    generated_from = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (Index("ix_prep_plans_company_id", "company_id"),)

    company = relationship("Company", back_populates="prep_plans")


class Resume(Base):
    __tablename__ = "resume"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    full_name = Column(String(100), nullable=True, default="")
    phone = Column(String(50), nullable=True, default="")
    email = Column(String(255), nullable=True, default="")
    summary = Column(Text, nullable=True, default="")
    skills = Column(JSON, nullable=False, default=list)
    education = Column(JSON, nullable=False, default=list)
    work_experience = Column(JSON, nullable=False, default=list)
    projects = Column(JSON, nullable=False, default=list)
    certifications = Column(JSON, nullable=False, default=list)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class UserProfile(Base):
    __tablename__ = "user_profile"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    skills = Column(JSON, nullable=False, default=list)
    weak_points = Column(JSON, nullable=False, default=dict)
    strong_points = Column(JSON, nullable=False, default=list)
    career_direction = Column(String(255), nullable=False, default="")
    interview_count = Column(Integer, nullable=False, default=0)
    offer_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class SkillTaxonomy(Base):
    __tablename__ = "skill_taxonomy"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    canonical_name = Column(String(255), nullable=False, unique=True)
    aliases = Column(JSON, nullable=False, default=list)
    category = Column(String(100), nullable=False, default="general")
    external_refs = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ProfileEvidence(Base):
    __tablename__ = "profile_evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False)
    source_type = Column(String(50), nullable=False)
    source_id = Column(String(36), nullable=True)
    dimension = Column(String(100), nullable=False)
    skill_name = Column(String(255), nullable=True, default="")
    signal_type = Column(String(50), nullable=False)
    polarity = Column(Integer, nullable=False, default=-1)
    score = Column(Integer, nullable=False, default=0)
    confidence = Column(Integer, nullable=False, default=50)
    round_no = Column(Integer, nullable=True)
    quote_text = Column(Text, nullable=False, default="")
    metadata_json = Column(JSON, nullable=False, default=dict)
    # 向量列：pgvector 迁移时改为 `vector` 类型（Vector(1024) for BGE-M3），存储到这一列而非 metadata_json
    # 当前 SQLite/JSON 环境下存 JSON 列表，切换 pgvector 后需重建向量数据
    # BGE-M3 维度: 1024；如更换模型需同步修改 VECTOR_DIMENSION 常量
    vector = Column(JSON, nullable=True, default=None)
    event_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_profile_evidence_user_event", "user_id", "event_time"),
        Index("ix_profile_evidence_user_dimension", "user_id", "dimension"),
    )


class UserSkillState(Base):
    __tablename__ = "user_skill_state"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False)
    dimension = Column(String(100), nullable=False)
    skill_name = Column(String(255), nullable=True, default="")
    level = Column(Integer, nullable=False, default=1)
    trend = Column(String(50), nullable=False, default="new")
    confidence = Column(Integer, nullable=False, default=0)
    evidence_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_user_skill_state_user", "user_id"),
        Index("ix_user_skill_state_user_dimension", "user_id", "dimension"),
    )


class UserProfileSnapshot(Base):
    __tablename__ = "user_profile_snapshot"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False)
    version = Column(String(50), nullable=False, default="v2")
    headline = Column(Text, nullable=False, default="")
    summary = Column(JSON, nullable=False, default=dict)
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    source_event_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_profile_snapshot_user_time", "user_id", "generated_at"),
    )


class Notification(Base):
    """
    Design: Push Notification System
    核心设计：
    - 通知分为不同类型：interview_reminder（面试提醒）、stale_alert（投递过期提醒）
    - 通过 channel 指定发送通道：webhook（钉钉/企微/飞书）、email
    - 状态流转：pending -> sent / failed，每次发送记录 sent_at 和 error_msg
    - 支持 scheduled_at 延迟发送，sent_at 非空表示已发送
    """

    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False, default="default-user")
    notif_type = Column(String(50), nullable=False)  # interview_reminder | stale_alert
    channel = Column(String(20), nullable=False, default="webhook")  # webhook | email
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending | sent | failed
    title = Column(String(255), nullable=False, default="")
    content = Column(Text, nullable=False, default="")
    target_id = Column(String(36), nullable=True)  # company_id / interview_id
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    error_msg = Column(Text, nullable=True, default="")
    webhook_url = Column(String(500), nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_notifications_user_status", "user_id", "status"),
        Index("ix_notifications_scheduled", "scheduled_at"),
    )


class QuestionCategory(Base):
    """
    Design: Question Training System - Knowledge Category
    知识领域分类，支持树形结构（parent_id 自关联）
    """

    __tablename__ = "question_categories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)
    parent_id = Column(String(36), ForeignKey("question_categories.id"), nullable=True)
    description = Column(Text, nullable=True, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    parent = relationship("QuestionCategory", remote_side=[id], backref="children")
    questions = relationship("Question", back_populates="category")


class Question(Base):
    """
    Design: Question Training System - Question Bank
    题目表：支持多种题型，按知识点/难度/公司标签组织
    """

    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    category_id = Column(
        String(36), ForeignKey("question_categories.id"), nullable=False
    )
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    answer_template = Column(Text, nullable=False)
    difficulty = Column(Integer, nullable=False, default=3)  # 1-5
    knowledge_points = Column(JSON, nullable=False, default=list)
    company_tags = Column(JSON, nullable=False, default=list)
    question_type = Column(
        String(50), nullable=False, default="open_ended"
    )  # open_ended | multiple_choice
    options = Column(JSON, nullable=True, default=None)  # 选择题选项
    hints = Column(JSON, nullable=False, default=list)
    vector = Column(JSON, nullable=True, default=None)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_questions_category", "category_id"),
        Index("ix_questions_difficulty", "difficulty"),
    )

    category = relationship("QuestionCategory", back_populates="questions")
    performances = relationship("UserQuestionPerformance", back_populates="question")


class UserQuestionPerformance(Base):
    """
    Design: Question Training System - User Performance Record
    用户练习表现记录，关联 Question 和画像 Evidence
    """

    __tablename__ = "user_question_performance"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False)
    question_id = Column(String(36), ForeignKey("questions.id"), nullable=False)
    submitted_answer = Column(Text, nullable=False)
    score = Column(Integer, nullable=False, default=0)  # 0-100
    feedback = Column(Text, nullable=False, default="")
    evaluation_details = Column(JSON, nullable=False, default=dict)
    time_spent_seconds = Column(Integer, nullable=False, default=0)
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_user_question_performance_user", "user_id"),
        Index("ix_user_question_performance_question", "question_id"),
    )

    question = relationship("Question", back_populates="performances")


class Drill(Base):
    """
    领域题目组：按领域/知识点组织的一组题目
    """

    __tablename__ = "drills"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)  # 题目组名称
    description = Column(Text, nullable=False, default="")  # 描述
    topic = Column(String(100), nullable=False)  # 领域/主题
    difficulty = Column(Integer, nullable=False, default=3)  # 整体难度 1-5
    question_ids = Column(JSON, nullable=False, default=list)  # 题目ID列表
    knowledge_points = Column(JSON, nullable=False, default=list)  # 关联知识点
    estimated_duration_minutes = Column(
        Integer, nullable=False, default=30
    )  # 预计完成时间
    is_system = Column(Integer, nullable=False, default=0)  # 0=用户创建, 1=系统预置
    created_by = Column(String(36), nullable=False, default="system")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_drills_topic", "topic"),
        Index("ix_drills_created_by", "created_by"),
    )


class DrillSession(Base):
    """
    题目组练习会话：记录整组题目的完成情况
    """

    __tablename__ = "drill_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False)
    drill_id = Column(String(36), ForeignKey("drills.id"), nullable=False)
    status = Column(
        String(50), nullable=False, default="in_progress"
    )  # in_progress, completed, abandoned
    current_question_index = Column(
        Integer, nullable=False, default=0
    )  # 当前做到第几题
    answers = Column(
        JSON, nullable=False, default=list
    )  # [{question_id, answer, score, time_spent_seconds, submitted_at}]
    total_score = Column(Integer, nullable=True)  # 整组总分（满分100*题目数）
    average_score = Column(Integer, nullable=True)  # 平均分 0-100
    total_time_spent_seconds = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_drill_sessions_user", "user_id"),
        Index("ix_drill_sessions_drill", "drill_id"),
        Index("ix_drill_sessions_status", "status"),
        Index("ix_drill_sessions_user_completed", "user_id", "completed_at"),
    )

    drill = relationship("Drill")


class EightPartTemplate(Base):
    """八股题目模板：固定面试题型"""

    __tablename__ = "eight_part_templates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    category = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    answer_template = Column(Text, nullable=False, default="")
    difficulty = Column(Integer, nullable=False, default=3)
    tips = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (Index("ix_eight_part_category", "category"),)


class KnowledgeItem(Base):
    """知识库条目：存储可生成题目的知识点"""

    __tablename__ = "knowledge_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    category = Column(String(100), nullable=False, default="未分类")
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False, default="")
    concepts = Column(JSON, nullable=False, default=list)
    examples = Column(JSON, nullable=False, default=list)
    tags = Column(JSON, nullable=False, default=list)
    difficulty_min = Column(Integer, nullable=False, default=1)
    difficulty_max = Column(Integer, nullable=False, default=5)
    vector = Column(JSON, nullable=True, default=None)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_knowledge_items_category", "category"),
        Index("ix_knowledge_items_tags", "tags"),
    )


class GeneratedQuestion(Base):
    """AI生成的题目（基于知识库实时生成）"""

    __tablename__ = "generated_questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    drill_id = Column(String(36), ForeignKey("drills.id"), nullable=False)
    knowledge_item_id = Column(
        String(36), ForeignKey("knowledge_items.id"), nullable=True
    )
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    answer_template = Column(Text, nullable=False, default="")
    difficulty = Column(Integer, nullable=False, default=3)
    knowledge_points = Column(JSON, nullable=False, default=list)
    hints = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_generated_questions_drill", "drill_id"),
        Index("ix_generated_questions_knowledge_item", "knowledge_item_id"),
    )
