"""
PodAsk AI Backend
Main FastAPI application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.api.routes import auth, health
from app.routes import audio, podcast


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    print(f"Starting PodAsk API in {settings.app_env} mode")
    yield
    # Shutdown
    print("Shutting down PodAsk API")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="PodAsk API",
        description="Transform scientific papers into interactive podcasts",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API Routes (from main branch)
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    
    # Audio Pipeline Routes (from our branch)
    app.include_router(audio.router)
    app.include_router(podcast.router)

    @app.get("/")
    async def root():
        return {
            "service": "PodAsk API",
            "version": "0.1.0",
            "tagline": "Don't just listen. Ask the science.",
            "docs": "/docs" if settings.is_development else None
        }

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


app = create_app()
