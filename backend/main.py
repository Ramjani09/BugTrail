import os
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

# Load environment variables from .env file at root or backend level
load_dotenv()
load_dotenv(Path(__file__).parent.parent / ".env")

from backend.models import (
    BugReport,
    BugResolution,
    InvestigationResult,
    HealthResponse,
    ResolutionResponse
)
from backend.hindsight_service import hindsight_service
from backend.agent import agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bugtrail.main")

app = FastAPI(
    title="BugTrail API",
    description="AI Bug Investigation Memory Agent powered by Hindsight Cloud",
    version="1.0.0"
)

# Enable CORS for local testing and cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to frontend directory
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

@app.get("/api/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="ok",
        gemini_connected=agent.is_gemini_connected(),
        hindsight_connected=hindsight_service.is_connected(),
        bank_id="bugtrail-memory"
    )

@app.post("/api/investigate", response_model=InvestigationResult)
def investigate_bug(bug: BugReport):
    logger.info(f"Received investigation request: {bug.title}")
    
    if not bug.title or not bug.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bug title is required for investigation."
        )

    # 1. Query Hindsight for relevant previous bug experiences
    query_text = f"{bug.title} {bug.description} {bug.recent_change} {bug.error_logs}".strip()
    memories = hindsight_service.recall_memories(query_text)
    
    # 2. Invoke AI Agent (Gemini or Demo Mode) to generate structured investigation
    result = agent.investigate(
        bug=bug,
        memories=memories,
        hindsight_connected=hindsight_service.is_connected()
    )
    
    return result

@app.post("/api/resolve", response_model=ResolutionResponse)
def resolve_bug(resolution: BugResolution):
    logger.info(f"Received bug resolution request: {resolution.bug_title}")
    
    if not resolution.bug_title or not resolution.root_cause or not resolution.fix_applied:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bug title, root cause, and fix applied are required."
        )

    # Store resolution in Hindsight memory
    saved_to_hindsight, message = hindsight_service.retain_resolution(resolution)
    
    return ResolutionResponse(
        success=True,
        message=message,
        hindsight_saved=saved_to_hindsight
    )

@app.post("/api/demo/reset")
def reset_demo():
    return {"status": "reset", "message": "Demo state ready for testing."}

# Mount static files and fallback to index.html
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def read_root():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/{full_path:path}")
    def serve_frontend_assets(full_path: str):
        asset_file = FRONTEND_DIR / full_path
        if asset_file.exists() and asset_file.is_file():
            return FileResponse(str(asset_file))
        return FileResponse(str(FRONTEND_DIR / "index.html"))
