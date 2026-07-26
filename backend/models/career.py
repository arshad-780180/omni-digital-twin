from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# =========================================================
# Backward-Compatible Schemas (for legacy ATS job-match)
# =========================================================
class JobAnalyzeRequest(BaseModel):
    job_title: str
    job_description: str

class CareerReportBase(BaseModel):
    job_title: str
    match_score: int
    matched_skills: List[str]
    missing_skills: List[str]

class CareerReportInDB(CareerReportBase):
    id: str
    user_id: str
    created_at: datetime

class CareerReportResponse(CareerReportBase):
    id: str
    user_id: str
    created_at: datetime


# =========================================================
# Phase 3: AI Career Readiness Engine Schemas
# =========================================================
class CareerScoreBreakdown(BaseModel):
    technical_score: int = 80
    resume_score: int = 80
    github_score: int = 80
    project_score: int = 80
    communication_score: int = 80

class StrengthItem(BaseModel):
    title: str
    description: str = ""

class WeaknessItem(BaseModel):
    title: str
    description: str = ""
    recommendation: str = ""

class MissingSkillItem(BaseModel):
    skill: str
    importance: str = "High"
    category: str = "General"

class RecommendedRole(BaseModel):
    role: str
    match_percentage: int = 80
    description: str = ""

class CareerSummary(BaseModel):
    executive_summary: str
    key_highlights: List[str] = Field(default_factory=list)

class CareerAnalysis(BaseModel):
    overall_score: int = 80
    breakdown: CareerScoreBreakdown
    career_level: str = "Intermediate"  # Beginner | Intermediate | Placement Ready | Advanced
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    recommended_roles: List[str] = Field(default_factory=list)
    summary: str = ""

class CareerAnalyzeResponse(BaseModel):
    id: Optional[str] = None
    user_id: str
    career_score: int = 80
    technical_score: int = 80
    resume_score: int = 80
    github_score: int = 80
    project_score: int = 80
    communication_score: int = 80
    career_level: str = "Intermediate"
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    recommended_roles: List[str] = Field(default_factory=list)
    summary: str = ""
    analysis_method: str = "ai"  # "ai" | "rule_based"
    created_at: datetime
