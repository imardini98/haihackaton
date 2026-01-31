"""
PodAsk AI Backend
Main FastAPI application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import audio

app = FastAPI(
    title="PodAsk AI",
    description="Interactive AI-powered podcast platform for scientific literature",
    version="0.1.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(audio.router)


@app.get("/")
async def root():
    return {
        "name": "PodAsk AI",
        "tagline": "Don't just listen. Ask the science.",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
