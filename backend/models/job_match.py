from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from models.common import AIResponseBase


class JobMatchAnalyzeRequest(BaseModel):
    job_title: str
    company: str = ""
    location: Optional[str] = ""
    employment_type: Optional[str] = ""
    job_description: str


class JobRequirements(BaseModel):
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    cloud_platforms: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    experience_requirements: List[str] = Field(default_factory=list)
    education_requirements: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)


class RoleRecommendationItem(BaseModel):
    role_name: str
    category: str = "best_matching"  # best_matching | alternative | stretch | avoid
    match_percentage: int = 80
    explanation: str = ""


class LearningGapItem(BaseModel):
    skill: str
    priority_order: int = 1
    estimated_difficulty: str = "Medium"  # Easy | Medium | Hard
    learning_timeline: str = "2 weeks"
    reasoning: str = ""


class SalaryInsights(BaseModel):
    junior_range: str = "$70,000 - $90,000"
    mid_level_range: str = "$95,000 - $125,000"
    senior_range: str = "$130,000 - $165,000"
    confidence_level: str = "High"  # High | Medium | Low
    disclaimer: str = "These salary ranges are estimates derived from profile metrics and market assumptions, not guaranteed offers."


class AICareerAdvice(BaseModel):
    executive_summary: str = ""
    interview_preparation_advice: List[str] = Field(default_factory=list)
    project_suggestions: List[str] = Field(default_factory=list)
    certification_suggestions: List[str] = Field(default_factory=list)
    portfolio_improvements: List[str] = Field(default_factory=list)
    resume_improvements: List[str] = Field(default_factory=list)
    github_improvements: List[str] = Field(default_factory=list)


class JobMatchAnalysisResponse(AIResponseBase):
    id: Optional[str] = None
    user_id: str
    job_title: str
    company: str = ""
    location: str = ""
    employment_type: str = ""
    job_description: str
    
    # Scores (0-100)
    overall_job_match_score: int = 0
    technical_match_score: int = 0
    experience_match_score: int = 0
    education_match_score: int = 0
    project_relevance_score: int = 0
    skill_coverage_percentage: int = 0
    
    # Skill Alignment
    missing_skills: List[Any] = Field(default_factory=list)
    matched_skills: List[Any] = Field(default_factory=list)
    missing_technologies: List[Any] = Field(default_factory=list)
    strength_areas: List[Any] = Field(default_factory=list)
    weak_areas: List[Any] = Field(default_factory=list)
    
    # Career evaluation
    career_readiness: str = "Intermediate"
    hiring_recommendation: str = "Consider"  # Strong Hire | Hire | Consider | Needs Development
    
    # Structured nested objects
    requirements: JobRequirements = Field(default_factory=JobRequirements)
    recommended_roles: List[RoleRecommendationItem] = Field(default_factory=list)
    learning_plan: List[LearningGapItem] = Field(default_factory=list)
    salary_estimate: SalaryInsights = Field(default_factory=SalaryInsights)
    career_advice: AICareerAdvice = Field(default_factory=AICareerAdvice)
    
    analysis_method: str = "ai"  # ai | rule_based
