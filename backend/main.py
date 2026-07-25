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
    "http://127.0.0.1:5173",
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

app.include_router(auth_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to the OmniMind API!"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
