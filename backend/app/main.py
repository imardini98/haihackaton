"""
PodAsk AI Backend
Main FastAPI application - Matches CLAUDE.md structure
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.api.routes import auth, health, podcasts, interaction, audio_files, simulation


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

    # CORS — in development allow all origins so simulation works from file:// or any localhost
    cors_origins = ["*"] if settings.is_development else settings.cors_origins_list
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=cors_origins != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API v1 Routes (CLAUDE.md structure)
    app.include_router(health.router, prefix="/api/v1/health")
    app.include_router(auth.router, prefix="/api/v1/auth")
    app.include_router(podcasts.router, prefix="/api/v1")
    app.include_router(interaction.router, prefix="/api/v1")
    app.include_router(audio_files.router, prefix="/api/v1")
    app.include_router(simulation.router, prefix="/api/v1")

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
        """Legacy health endpoint"""
        return {"status": "healthy"}

    return app


app = create_app()
