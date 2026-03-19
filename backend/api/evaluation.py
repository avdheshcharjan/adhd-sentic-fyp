"""
Evaluation endpoints for ablation mode toggling and evaluation session management.
"""

from fastapi import APIRouter

from config import get_settings

router = APIRouter(prefix="/eval", tags=["evaluation"])

settings = get_settings()


@router.post("/ablation")
async def toggle_ablation(enabled: bool):
    """Toggle SenticNet ablation mode for A/B evaluation."""
    settings.ABLATION_MODE = enabled
    return {
        "ablation_mode": enabled,
        "sentic_net": "disabled" if enabled else "enabled",
    }


@router.get("/ablation")
async def get_ablation_status():
    """Get current ablation mode status."""
    return {
        "ablation_mode": settings.ABLATION_MODE,
        "sentic_net": "disabled" if settings.ABLATION_MODE else "enabled",
    }


@router.post("/logging")
async def toggle_evaluation_logging(enabled: bool):
    """Toggle evaluation logging on/off."""
    settings.EVALUATION_LOGGING = enabled
    return {
        "evaluation_logging": enabled,
        "log_path": settings.EVALUATION_LOG_PATH,
    }
