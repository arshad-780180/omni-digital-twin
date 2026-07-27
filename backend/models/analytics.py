from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone


class CareerHealthScore(BaseModel):
    """
    Deterministic weighted breakdown of the overall Career Health Score.
    """
    overall_score: int = Field(..., description="Overall Career Health Score (0-100)")
    readiness_component: float = 0.0
    ats_component: float = 0.0
    job_match_component: float = 0.0
    interview_component: float = 0.0
    learning_component: float = 0.0
    project_milestone_bonus: float = 0.0
    status: str = "Strong"  # "Excellent", "Strong", "Moderate", "Needs Attention"


class CareerAnalytics(BaseModel):
    """
    Career readiness trend and historical improvement metrics.
    """
    current_score: int = 0
    historical_trend: List[int] = Field(default_factory=list)
    monthly_improvement: float = 0.0
    target_score: int = 90
    estimated_goal_date: str = "Within 8 weeks"
    history_labels: List[str] = Field(default_factory=list)


class ATSAnalytics(BaseModel):
    """
    ATS resume optimization analytics and keyword coverage metrics.
    """
    latest_score: int = 0
    average_score: float = 0.0
    historical_trend: List[int] = Field(default_factory=list)
    keyword_coverage: float = 0.0
    top_missing_skills: List[str] = Field(default_factory=list)
    improvement_timeline: List[str] = Field(default_factory=list)


class JobMatchAnalytics(BaseModel):
    """
    Job matching evaluation analytics and skill gap evolution.
    """
    latest_match_score: int = 0
    average_match_score: float = 0.0
    best_matching_role: str = "Not Evaluated"
    alternative_roles: List[str] = Field(default_factory=list)
    hiring_recommendation_trend: List[str] = Field(default_factory=list)
    skill_gap_evolution: List[int] = Field(default_factory=list)


class InterviewAnalytics(BaseModel):
    """
    Multi-dimension mock interview performance trend analytics.
    """
    technical_score_trend: List[int] = Field(default_factory=list)
    communication_trend: List[int] = Field(default_factory=list)
    confidence_trend: List[int] = Field(default_factory=list)
    problem_solving_trend: List[int] = Field(default_factory=list)
    average_interview_score: float = 0.0
    most_improved_topic: str = "General Engineering"
    weakest_topic: str = "System Design"
    interview_success_rate: float = 0.0


class LearningAnalyticsSummary(BaseModel):
    """
    Learning roadmap progress, milestone velocity, and completion tracking.
    """
    learning_progress: float = 0.0
    completed_milestones: int = 0
    completed_projects: int = 0
    completed_certifications: int = 0
    learning_velocity: float = 0.0  # milestones completed per week
    weekly_streak: int = 1
    estimated_completion: str = "8 weeks"
    roadmap_progress: float = 0.0


class DigitalTwinAnalytics(BaseModel):
    """
    Living Digital Twin Memory evolution and competency metrics.
    """
    core_skills: List[str] = Field(default_factory=list)
    emerging_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    career_evolution_timeline: List[str] = Field(default_factory=list)
    strength_growth: int = 0
    weakness_reduction: int = 0
    memory_timeline: List[str] = Field(default_factory=list)


class SkillAnalytics(BaseModel):
    """
    Structured skill matrix item evaluating current level, trend, and target.
    """
    skill_name: str
    current_level: str = "Intermediate"  # "Beginner", "Intermediate", "Advanced", "Expert"
    growth_trend: str = "Upward"  # "Upward", "Stable", "Accelerating", "Developing"
    target_level: str = "Expert"  # "Advanced", "Expert", "Mastery"
    score: int = 70


class TimelineEvent(BaseModel):
    """
    Chronological career progression event across OMNI modules.
    """
    event_id: str
    event_type: str
    title: str
    description: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    module_source: str = "system"  # "resume", "github", "career", "ats", "interview", "learning", "job_match", "twin"
    impact_score: int = 5


class ExecutiveInsights(BaseModel):
    """
    Executive AI/Rule-Based synthesis of career health, strengths, risks, and next action.
    """
    current_strengths: List[str] = Field(default_factory=list)
    weakest_areas: List[str] = Field(default_factory=list)
    biggest_improvement: str = ""
    career_risks: List[str] = Field(default_factory=list)
    recommended_next_action: str = ""
    estimated_readiness: str = ""
    ai_generated: bool = True


class DashboardSummary(BaseModel):
    """
    Complete executive dashboard summary combining all analytics into one response.
    """
    user_id: str
    career_health_score: CareerHealthScore
    career_readiness_score: int = 0
    ats_score: int = 0
    job_match_score: int = 0
    interview_score: int = 0
    learning_progress: float = 0.0
    digital_twin_confidence: float = 0.0
    career_goal_progress: float = 0.0
    overall_career_health_score: int = 0
    career_analytics: CareerAnalytics
    ats_analytics: ATSAnalytics
    job_match_analytics: JobMatchAnalytics
    interview_analytics: InterviewAnalytics
    learning_analytics: LearningAnalyticsSummary
    digital_twin_analytics: DigitalTwinAnalytics
    skill_matrix: List[SkillAnalytics] = Field(default_factory=list)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    insights: ExecutiveInsights
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
