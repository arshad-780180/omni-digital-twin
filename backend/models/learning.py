from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone


class Milestone(BaseModel):
    milestone_id: str
    title: str
    phase: int = 1
    category: str = "skill"  # "skill", "project", "course", "interview"
    description: str = ""
    skills_unlocked: List[str] = Field(default_factory=list)
    completed: bool = False
    completed_at: Optional[datetime] = None


class ProjectRecommendation(BaseModel):
    project_id: str
    title: str
    description: str
    difficulty: str = "Intermediate"  # "Beginner", "Intermediate", "Advanced"
    estimated_time: str = "15 hours"
    skills_covered: List[str] = Field(default_factory=list)
    portfolio_value: str = "High"  # "High", "Medium", "Standard"


class CertificationRecommendation(BaseModel):
    cert_id: str
    title: str
    issuer: str
    difficulty: str = "Intermediate"
    priority: str = "High"
    relevance: str = "Directly validates core competency"


class LearningResource(BaseModel):
    resource_id: str
    title: str
    type: str = "Official Documentation"  # "Official Documentation", "YouTube Course", "Book", "Interactive Platform", "LeetCode Problem", "System Design"
    url: str = ""
    priority: str = "High"  # "High", "Medium", "Low"
    difficulty: str = "Intermediate"


class LearningPhase(BaseModel):
    phase_number: int = 1
    title: str = "Fundamentals & Core Skills"
    objectives: List[str] = Field(default_factory=list)
    expected_outcomes: List[str] = Field(default_factory=list)
    estimated_hours: int = 40
    difficulty: str = "Intermediate"
    prerequisites: List[str] = Field(default_factory=list)
    milestones: List[Milestone] = Field(default_factory=list)
    projects: List[ProjectRecommendation] = Field(default_factory=list)
    resources: List[LearningResource] = Field(default_factory=list)
    checkpoint: str = "Complete phase milestones to unlock the next level"


class ProgressSummary(BaseModel):
    completed_milestones: int = 0
    total_milestones: int = 0
    progress_percentage: float = 0.0
    completed_phases: int = 0
    total_phases: int = 0
    current_phase: int = 1
    skills_acquired_count: int = 0


class LearningAnalytics(BaseModel):
    learning_velocity: float = 0.0  # milestones per week
    skills_learned_count: int = 0
    projects_completed_count: int = 0
    readiness_growth: int = 0  # target_readiness - current_readiness
    interview_improvement: int = 0
    ats_improvement: int = 0
    job_match_improvement: int = 0
    estimated_completion_weeks: int = 8


class LearningRoadmap(BaseModel):
    target_role: str = "Software Engineer"
    current_readiness: int = 45  # 0-100
    target_readiness: int = 95  # 0-100
    estimated_completion: str = "8 weeks"
    priority_skills: List[str] = Field(default_factory=list)
    learning_phases: List[LearningPhase] = Field(default_factory=list)
    milestones: List[Milestone] = Field(default_factory=list)
    projects: List[ProjectRecommendation] = Field(default_factory=list)
    certifications: List[CertificationRecommendation] = Field(default_factory=list)
    resources: List[LearningResource] = Field(default_factory=list)
    practice_schedule: List[str] = Field(default_factory=list)
    mock_interview_schedule: List[str] = Field(default_factory=list)
    revision_plan: List[str] = Field(default_factory=list)
    final_career_goal: str = "Secure a position as Software Engineer"


class LearningRoadmapGenerateRequest(BaseModel):
    target_role: Optional[str] = None
    target_timeframe_weeks: int = 8
    focus_areas: List[str] = Field(default_factory=list)


class MilestoneCompleteRequest(BaseModel):
    milestone_id: Optional[str] = None
    notes: Optional[str] = None
    completed_items: List[str] = Field(default_factory=list)


class LearningRoadmapInDB(BaseModel):
    id: str
    user_id: str
    target_role: str
    current_readiness: int
    target_readiness: int
    roadmap: LearningRoadmap
    milestones: List[Milestone] = Field(default_factory=list)
    completed_items: List[str] = Field(default_factory=list)
    progress_percentage: float = 0.0
    estimated_completion: str = "8 weeks"
    created_at: datetime
    updated_at: datetime


class LearningRoadmapResponse(BaseModel):
    id: str
    user_id: str
    target_role: str
    current_readiness: int
    target_readiness: int
    roadmap: LearningRoadmap
    milestones: List[Milestone] = Field(default_factory=list)
    completed_items: List[str] = Field(default_factory=list)
    progress_percentage: float = 0.0
    estimated_completion: str = "8 weeks"
    analytics: LearningAnalytics = Field(default_factory=LearningAnalytics)
    progress_summary: ProgressSummary = Field(default_factory=ProgressSummary)
    created_at: datetime
    updated_at: Optional[datetime] = None


class LearningHistoryItem(BaseModel):
    id: str
    user_id: str
    target_role: str
    current_readiness: int
    target_readiness: int
    progress_percentage: float = 0.0
    created_at: datetime
    updated_at: Optional[datetime] = None


class LearningRoadmapHistoryResponse(BaseModel):
    user_id: str
    total_roadmaps: int = 0
    latest_roadmap: Optional[LearningRoadmapResponse] = None
    history: List[LearningHistoryItem] = Field(default_factory=list)
