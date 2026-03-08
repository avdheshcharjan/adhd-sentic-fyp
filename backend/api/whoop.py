"""Whoop integration endpoints — stubs for Phase 1, implemented in Phase 5."""

from fastapi import APIRouter

router = APIRouter(prefix="/whoop", tags=["whoop"])


@router.get("/auth")
async def start_oauth():
    """Initiate Whoop OAuth 2.0 flow (stub)."""
    return {"message": "Whoop OAuth not yet implemented. Coming in Phase 5."}


@router.get("/callback")
async def oauth_callback(code: str = ""):
    """Handle Whoop OAuth callback (stub)."""
    return {"message": "Whoop OAuth callback not yet implemented. Coming in Phase 5."}


@router.get("/morning-briefing")
async def morning_briefing():
    """Generate daily morning briefing from Whoop data (stub)."""
    return {"message": "Morning briefing not yet implemented. Coming in Phase 5."}
