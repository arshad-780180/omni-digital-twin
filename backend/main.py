from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(
    title="OmniMind API",
    description="Backend for the OmniMind AI Personal Digital Twin",
    version="1.0.0"
)

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

app.include_router(auth_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(github_router, prefix="/api")
app.include_router(career_router, prefix="/api")
app.include_router(interview_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to the OmniMind API!"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
