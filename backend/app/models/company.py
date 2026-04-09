from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    position: str = Field(..., min_length=1, max_length=255)
    jd_text: Optional[str] = Field("", max_length=50000)
    status: str = Field("applied", pattern="^(applied|interviewing|passed|rejected)$")
    applied_date: Optional[date] = None
    next_event_date: Optional[date] = None
    next_event_type: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field("", max_length=5000)


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    position: Optional[str] = Field(None, min_length=1, max_length=255)
    jd_text: Optional[str] = Field(None, max_length=50000)
    status: Optional[str] = Field(
        None, pattern="^(applied|interviewing|passed|rejected)$"
    )
    applied_date: Optional[date] = None
    next_event_date: Optional[date] = None
    next_event_type: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=5000)


class InterviewBrief(BaseModel):
    id: str
    round: int
    interview_date: Optional[date]
    format: Optional[str]
    interviewer: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyResponse(BaseModel):
    id: str
    name: str
    position: str
    status: str
    applied_date: Optional[date]
    next_event_date: Optional[date]
    next_event_type: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyDetail(CompanyResponse):
    interviews: List[InterviewBrief] = []


class InterviewCreate(BaseModel):
    round: int
    interview_date: Optional[date] = None
    format: Optional[str] = None
    interviewer: Optional[str] = None
    raw_notes: Optional[str] = ""
    expected_result_date: Optional[date] = None


class InterviewUpdate(BaseModel):
    round: Optional[int] = None
    interview_date: Optional[date] = None
    format: Optional[str] = None
    interviewer: Optional[str] = None
    raw_notes: Optional[str] = None
    ai_analysis: Optional[dict] = None
    expected_result_date: Optional[date] = None
    result_status: Optional[str] = None


class InterviewResponse(BaseModel):
    id: str
    company_id: str
    round: int
    interview_date: Optional[date]
    format: Optional[str]
    interviewer: Optional[str]
    raw_notes: Optional[str]
    ai_analysis: dict
    expected_result_date: Optional[date]
    result_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MatchRequest(BaseModel):
    jd_text: str = Field(
        ..., min_length=1, max_length=50000, description="Full job description text"
    )
    resume_text: str = Field(
        "", max_length=50000, description="Resume text (empty if using stored resume)"
    )
    use_stored_resume: bool = Field(
        False, description="Use stored resume from database"
    )


class MatchResponse(BaseModel):
    match_percentage: int = Field(..., ge=0, le=100)
    strengths: List[str]
    gaps: List[str]
    suggestions: List[str]


class ReviewQuestion(BaseModel):
    question: str
    your_answer_summary: str
    score: int = Field(..., ge=1, le=10)
    assessment: str
    improvement: str


class ReviewRequest(BaseModel):
    raw_notes: str = Field(..., min_length=1, max_length=20000)
    company_name: Optional[str] = Field("", max_length=255)
    position: Optional[str] = Field("", max_length=255)
    round: Optional[int] = Field(1, ge=1, le=50)
    jd_key_points: Optional[List[str]] = []
    company_id: Optional[str] = ""
    interview_id: Optional[str] = ""
    interview_date: Optional[str] = ""
    interview_format: Optional[str] = Field("", max_length=50)
    interviewer: Optional[str] = Field("", max_length=255)


class ReviewResponse(BaseModel):
    questions: List[ReviewQuestion]
    weak_points: List[str]
    strong_points: List[str]
    next_round_prediction: List[str]
    interviewer_signals: List[str]


class DailyTask(BaseModel):
    day: int
    focus: str
    priority: str
    tasks: List[str]
    total_minutes: Optional[int] = Field(None, ge=0, le=240)
    completed_task_indexes: List[int] = Field(default_factory=list)
    completed: bool = False


class PrepRequest(BaseModel):
    company_id: str
    target_round: int
    days_available: int = Field(..., ge=1, le=30)
    weak_points: List[str] = []
    jd_directions: List[str] = []
    interview_chain: List[dict] = []


class PrepResponse(BaseModel):
    prep_plan_id: Optional[str] = None
    daily_tasks: List[DailyTask]


class PrepTaskUpdateRequest(BaseModel):
    day: int = Field(..., ge=1, le=30)
    task_index: int = Field(..., ge=0, le=20)
    completed: bool


class OfferCreate(BaseModel):
    company_id: str
    salary: Optional[str] = ""
    benefits: Optional[str] = ""
    offer_date: Optional[date] = None
    deadline: Optional[date] = None
    notes: Optional[str] = ""


class OfferUpdate(BaseModel):
    salary: Optional[str] = None
    benefits: Optional[str] = None
    offer_date: Optional[date] = None
    deadline: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class OfferResponse(BaseModel):
    id: str
    company_id: str
    company_name: str
    position: str
    salary: Optional[str]
    benefits: Optional[str]
    offer_date: Optional[date]
    deadline: Optional[date]
    status: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TransitionOfferData(BaseModel):
    """Offer data for status transition (company_id is inferred from URL path)."""

    salary: Optional[str] = ""
    benefits: Optional[str] = ""
    offer_date: Optional[date] = None
    deadline: Optional[date] = None
    notes: Optional[str] = ""


class StatusTransitionRequest(BaseModel):
    new_status: str
    offer_data: Optional[TransitionOfferData] = None


class EducationEntry(BaseModel):
    school: str = ""
    degree: str = ""
    major: str = ""
    start_date: Optional[str] = ""
    end_date: Optional[str] = ""
    description: str = ""


class WorkExperienceEntry(BaseModel):
    company: str = ""
    position: str = ""
    start_date: Optional[str] = ""
    end_date: Optional[str] = ""
    description: str = ""
    technologies: str = ""


class ProjectEntry(BaseModel):
    name: str = ""
    description: str = ""
    role: str = ""
    start_date: Optional[str] = ""
    end_date: Optional[str] = ""
    technologies: str = ""
    achievements: str = ""


class ResumeCreate(BaseModel):
    full_name: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    summary: Optional[str] = ""
    skills: Optional[List[str]] = []
    education: Optional[List[dict]] = []
    work_experience: Optional[List[dict]] = []
    projects: Optional[List[dict]] = []
    certifications: Optional[List[str]] = []


class ResumeUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    summary: Optional[str] = None
    skills: Optional[List[str]] = None
    education: Optional[List[dict]] = None
    work_experience: Optional[List[dict]] = None
    projects: Optional[List[dict]] = None
    certifications: Optional[List[str]] = None


class ResumeResponse(BaseModel):
    id: str
    full_name: str
    phone: str
    email: str
    summary: str
    skills: List[str]
    education: List[dict]
    work_experience: List[dict]
    projects: List[dict]
    certifications: List[str]
    updated_at: datetime

    class Config:
        from_attributes = True
