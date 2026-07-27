from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone

class FeedbackItem(BaseModel):
    question_index: int
    score: int
    critique: str

class InterviewQuestion(BaseModel):
    question_id: str
    question: str
    difficulty: str = "Medium"  # "Easy", "Medium", "Hard"
    category: str = "Technical"
    topic: str = "General"
    expected_skills: List[str] = Field(default_factory=list)
    estimated_time: int = 180
    generated_from: str = "Digital Twin Context"
    order: int = 1

class InterviewAnswer(BaseModel):
    question_id: str
    content: str
    content_type: str = "Text"  # "Text", "Voice", "Video"
    transcript: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InterviewQuestionEvaluation(BaseModel):
    question_id: str
    technical_score: int = 0
    communication_score: int = 0
    confidence_score: int = 0
    problem_solving_score: int = 0
    completeness_score: int = 0
    real_world_thinking_score: int = 0
    feedback: str = ""
    ideal_answer: str = ""
    improvement_suggestions: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    weak_topics: List[str] = Field(default_factory=list)
    strong_topics: List[str] = Field(default_factory=list)

class InterviewReport(BaseModel):
    overall_score: int = 0
    technical_score: int = 0
    communication_score: int = 0
    confidence_score: int = 0
    problem_solving_score: int = 0
    interview_readiness: str = "Developing"
    hiring_recommendation: str = "Consider"
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    missed_concepts: List[str] = Field(default_factory=list)
    learning_priorities: List[str] = Field(default_factory=list)
    recommended_projects: List[str] = Field(default_factory=list)
    recommended_certifications: List[str] = Field(default_factory=list)
    executive_summary: str = ""

class InterviewStartRequest(BaseModel):
    role: str
    company: str = ""
    difficulty: str = "Medium"
    interview_type: str = "Technical"
    question_count: int = 5

class InterviewGenerateRequest(BaseModel):
    target_role: str

class InterviewAnswerSubmitRequest(BaseModel):
    question_id: str
    content: str
    content_type: str = "Text"

class InterviewEvaluateRequest(BaseModel):
    session_id: Optional[str] = None
    answers: List[str] = Field(default_factory=list)

class InterviewSessionBase(BaseModel):
    role: str
    company: str = ""
    difficulty: str = "Medium"
    interview_type: str = "Technical"
    status: str = "NOT_STARTED"  # "NOT_STARTED", "IN_PROGRESS", "COMPLETED", "CANCELLED"
    questions: List[InterviewQuestion] = Field(default_factory=list)
    answers: List[InterviewAnswer] = Field(default_factory=list)
    evaluations: List[InterviewQuestionEvaluation] = Field(default_factory=list)
    report: Optional[InterviewReport] = None
    overall_score: int = 0
    technical_score: int = 0
    communication_score: int = 0
    confidence_score: int = 0

class InterviewSessionInDB(InterviewSessionBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class InterviewSessionResponse(InterviewSessionBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Backward compatibility aliases
    target_role: Optional[str] = None
    feedback: List[FeedbackItem] = Field(default_factory=list)

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.target_role and self.role:
            self.target_role = self.role

class InterviewHistoryResponse(BaseModel):
    sessions: List[InterviewSessionResponse] = Field(default_factory=list)
    average_score: float = 0.0
    technical_trend: List[float] = Field(default_factory=list)
    communication_trend: List[float] = Field(default_factory=list)
    confidence_trend: List[float] = Field(default_factory=list)
    improvement_percentage: float = 0.0
    best_interview: Optional[InterviewSessionResponse] = None
    weakest_topics: List[str] = Field(default_factory=list)
    most_improved_topics: List[str] = Field(default_factory=list)
    average_interview_duration: float = 0.0
    total_interviews: int = 0
