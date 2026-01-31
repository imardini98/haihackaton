from fastapi import APIRouter
from app.config import get_settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "service": "podask-api"}


@router.get("/services")
async def services_status():
    """Check status of external services."""
    settings = get_settings()

    services = {
        "supabase": bool(settings.supabase_url and settings.supabase_anon_key),
        "gemini": bool(settings.gemini_api_key),
        "elevenlabs": bool(settings.elevenlabs_api_key),
    }

    all_configured = all(services.values())

    return {
        "status": "ready" if all_configured else "missing_config",
        "services": services
    }
