from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    name: str
    position: str
    jd_text: Optional[str] = ""
    status: str = "applied"
    applied_date: Optional[date] = None
    next_event_date: Optional[date] = None
    next_event_type: Optional[str] = None
    notes: Optional[str] = ""


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    jd_text: Optional[str] = None
    status: Optional[str] = None
    applied_date: Optional[date] = None
    next_event_date: Optional[date] = None
    next_event_type: Optional[str] = None
    notes: Optional[str] = None


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
    jd_text: str = Field(..., description="Full job description text")
    resume_text: str = Field(..., description="Resume text")


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
    raw_notes: str
    company_name: Optional[str] = ""
    position: Optional[str] = ""
    round: Optional[int] = 1
    jd_key_points: Optional[List[str]] = []
    company_id: Optional[str] = ""
    interview_id: Optional[str] = ""
    interview_date: Optional[str] = ""
    interview_format: Optional[str] = ""
    interviewer: Optional[str] = ""


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
    completed: bool = False


class PrepRequest(BaseModel):
    company_id: str
    target_round: int
    days_available: int = Field(..., ge=1, le=30)
    weak_points: List[str] = []
    jd_directions: List[str] = []
    interview_chain: List[dict] = []


class PrepResponse(BaseModel):
    daily_tasks: List[DailyTask]


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
