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
