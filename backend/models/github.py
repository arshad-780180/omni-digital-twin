from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

# =========================================================
# Backward-Compatible Schemas (for legacy /sync and /report)
# =========================================================
class GitHubDataBase(BaseModel):
    username: str
    total_commits: int = 0
    top_languages: List[Dict[str, int]] = []  # e.g. [{"language": "Python", "count": 120}]
    total_repos: int = 0

class GitHubDataCreate(GitHubDataBase):
    pass

class GitHubDataInDB(GitHubDataBase):
    id: str
    user_id: str
    last_synced_at: datetime

class GitHubDataResponse(GitHubDataBase):
    id: str
    user_id: str
    last_synced_at: datetime


# =========================================================
# Phase 2: AI GitHub Intelligence Engine Schemas
# =========================================================
class GitHubProfileInfo(BaseModel):
    username: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    public_repos: int = 0
    followers: int = 0
    following: int = 0
    html_url: Optional[str] = None

class RepositoryInfo(BaseModel):
    name: str
    description: Optional[str] = None
    html_url: Optional[str] = None
    language: Optional[str] = None
    stargazers_count: int = 0
    forks_count: int = 0
    updated_at: Optional[str] = None
    readme_snippet: Optional[str] = None

class RepositoryAnalysisItem(BaseModel):
    name: str
    summary: str = ""
    architecture_score: int = 70
    quality_score: int = 75
    technologies: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)

class RoadmapStepItem(BaseModel):
    step_number: int
    title: str
    description: str
    recommended_resources: List[str] = Field(default_factory=list)

class GitHubAIAnalysis(BaseModel):
    developer_level: str = "Mid-Level"
    github_score: int = 75
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    portfolio_review: str = ""
    repository_analysis: List[RepositoryAnalysisItem] = Field(default_factory=list)
    career_recommendations: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    personalized_roadmap: List[RoadmapStepItem] = Field(default_factory=list)

class GitHubAnalyzeRequest(BaseModel):
    username: str

from models.common import AIResponseBase

class GitHubAnalyzeResponse(AIResponseBase):
    id: Optional[str] = None
    user_id: str
    username: str
    profile: GitHubProfileInfo
    repositories: List[RepositoryInfo] = Field(default_factory=list)
    analysis: GitHubAIAnalysis
    analyzed_at: datetime
    parsing_method: str = "ai"
