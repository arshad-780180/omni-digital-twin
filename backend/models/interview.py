from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class FeedbackItem(BaseModel):
    question_index: int
    score: int
    critique: str

class InterviewGenerateRequest(BaseModel):
    target_role: str

class InterviewSessionBase(BaseModel):
    target_role: str
    questions: List[str]
    answers: List[str] = []
    feedback: List[FeedbackItem] = []
    overall_score: int = 0

class InterviewSessionInDB(InterviewSessionBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class InterviewSessionResponse(InterviewSessionBase):
    id: str
    user_id: str
    created_at: datetime

class InterviewEvaluateRequest(BaseModel):
    answers: List[str]
