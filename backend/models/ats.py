from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class ATSAnalyzeRequest(BaseModel):
    job_title: str
    company: str = ""
    job_description: str


class ATSFeedback(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    section_feedback: Dict[str, str] = Field(default_factory=dict)


class ATSSuggestions(BaseModel):
    improved_summary: str = ""
    improved_projects: List[str] = Field(default_factory=list)
    grammar_feedback: List[str] = Field(default_factory=list)
    keyword_injection: List[str] = Field(default_factory=list)
    action_verbs: List[str] = Field(default_factory=list)


from models.common import AIResponseBase

class ATSAnalysisResponse(AIResponseBase):
    id: Optional[str] = None
    user_id: str
    resume_id: Optional[str] = None
    job_title: str
    company: str = ""
    job_description: str
    required_keywords: List[str] = Field(default_factory=list)
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    ats_score: int = 0
    resume_feedback: ATSFeedback = Field(default_factory=ATSFeedback)
    ai_suggestions: ATSSuggestions = Field(default_factory=ATSSuggestions)
    analysis_method: str = "ai"
