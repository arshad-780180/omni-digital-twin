from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from models.common import AIResponseBase


class DigitalTwinTimelineEvent(BaseModel):
    date: str
    event: str
    source_module: str
    category: Optional[str] = "milestone"
    details: Optional[str] = ""


class DigitalTwinMemoryResponse(AIResponseBase):
    id: Optional[str] = None
    user_id: str
    current_role: Optional[str] = None
    target_roles: List[str] = Field(default_factory=list)
    core_skills: List[str] = Field(default_factory=list)
    emerging_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    preferred_domains: List[str] = Field(default_factory=list)
    preferred_companies: List[str] = Field(default_factory=list)
    github_strengths: List[str] = Field(default_factory=list)
    resume_strengths: List[str] = Field(default_factory=list)
    career_strengths: List[str] = Field(default_factory=list)
    ats_history_summary: List[str] = Field(default_factory=list)
    job_matching_summary: List[str] = Field(default_factory=list)
    learning_history: List[Dict[str, Any]] = Field(default_factory=list)
    interview_history: List[Dict[str, Any]] = Field(default_factory=list)
    personality_observations: List[str] = Field(default_factory=list)
    communication_observations: List[str] = Field(default_factory=list)
    career_goals: List[str] = Field(default_factory=list)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    timeline: List[DigitalTwinTimelineEvent] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of last memory update in UTC"
    )

    class Config:
        populate_by_name = True


class DigitalTwinSummaryResponse(AIResponseBase):
    executive_summary: str
    top_strengths: List[str] = Field(default_factory=list)
    primary_skill_gaps: List[str] = Field(default_factory=list)
    recommended_trajectory: str = ""
    confidence_score: float = 0.85
    key_milestones: List[str] = Field(default_factory=list)
