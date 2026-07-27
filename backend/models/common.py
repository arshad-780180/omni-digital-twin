from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class AIResponseBase(BaseModel):
    """
    Standard base schema for all AI engine responses across OMNI Digital Twin modules.
    Provides consistent metadata while preserving 100% backward compatibility for subclass fields.
    """
    success: bool = Field(default=True, description="Whether the AI operation succeeded")
    generated_by: str = Field(default="ai", description="Method used for generation: 'ai' or 'rule_based'")
    confidence: float = Field(default=1.0, description="Confidence score of the generated result (0.0 to 1.0)")
    processing_time: float = Field(default=0.0, description="Time taken to process in seconds")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of creation in UTC"
    )
