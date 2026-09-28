from pydantic import BaseModel, Field
from typing import List, Optional

class BugReport(BaseModel):
    title: str = Field(..., description="Title of the bug report")
    description: str = Field(..., description="Detailed description of the bug")
    environment: str = Field(default="Production", description="Environment where bug occurred")
    recent_change: str = Field(default="", description="Recent changes or deployments made")
    error_logs: str = Field(default="", description="Error messages or log details")

class BugResolution(BaseModel):
    bug_title: str = Field(..., description="Title or summary of the bug being resolved")
    root_cause: str = Field(..., description="Identified root cause")
    fix_applied: str = Field(..., description="Fix or resolution applied")
    result: str = Field(default="Resolved", description="Outcome after applying fix")
    additional_lesson: str = Field(default="", description="Lessons learned or advice for future bugs")

class MemoryItem(BaseModel):
    incident: str
    root_cause: str
    fix: str
    context: Optional[str] = ""
    relevance_score: Optional[float] = None

class InvestigationResult(BaseModel):
    probable_cause: str
    investigation_steps: List[str]
    recommended_first_check: str
    why_recommendation_made: str
    confidence_explanation: str
    memory_influenced: bool
    memories_recalled: List[MemoryItem] = []
    ai_mode: str = "Demo Mode"
    hindsight_status: str = "Not Connected"

class HealthResponse(BaseModel):
    status: str = "ok"
    gemini_connected: bool
    hindsight_connected: bool
    bank_id: str

class ResolutionResponse(BaseModel):
    success: bool
    message: str
    hindsight_saved: bool
