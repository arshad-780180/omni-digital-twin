from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from utils.logger import get_logger
from utils.errors import register_exception_handlers
from utils.env_validator import validate_environment
from database.connection import get_db
from database.indexes import ensure_indexes

# Load environment variables
load_dotenv()

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation and MongoDB index registration
    logger.info("Initializing OMNI Digital Twin Platform...")
    validate_environment(strict=False)
    try:
        db = await get_db()
        await ensure_indexes(db)
    except Exception as e:
        logger.warning(f"Notice during startup index verification: {e}")
    yield
    logger.info("OMNI Digital Twin Platform shut down cleanly.")


app = FastAPI(
    title="OmniMind API",
    description="Backend for the OmniMind AI Personal Digital Twin",
    version="1.0.0",
    lifespan=lifespan,
)

# Register centralized exception handlers
register_exception_handlers(app)

# Configure CORS
origins = [
    "http://localhost:5173", # Vite default port
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from auth.routes import router as auth_router
from profile.routes import router as profile_router
from github.routes import router as github_router
from career.routes import router as career_router
from interview.routes import router as interview_router
from ats.routes import router as ats_router
from job_matching.routes import router as job_matching_router
from digital_twin.routes import router as digital_twin_router
from learning.routes import router as learning_router
from analytics.routes import router as analytics_router

app.include_router(auth_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(github_router, prefix="/api")
app.include_router(career_router, prefix="/api")
app.include_router(interview_router, prefix="/api")
app.include_router(ats_router, prefix="/api")
app.include_router(job_matching_router, prefix="/api")
app.include_router(digital_twin_router, prefix="/api")
app.include_router(learning_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to the OmniMind API!"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
