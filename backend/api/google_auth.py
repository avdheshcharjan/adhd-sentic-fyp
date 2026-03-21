"""
Google Calendar OAuth 2.0 authentication endpoints.

Flow:
1. GET  /api/auth/google          → Redirects user to Google consent screen
2. GET  /api/auth/google/callback  → Receives auth code, exchanges for tokens
3. GET  /api/auth/google/status    → Check if Google Calendar is connected
4. POST /api/auth/google/revoke    → Disconnect Google Calendar
"""

import logging

from fastapi import APIRouter
from fastapi.responses import RedirectResponse, HTMLResponse

from services.google_calendar import google_calendar_service

logger = logging.getLogger("adhd-brain.google-auth")

router = APIRouter(prefix="/api/auth/google", tags=["google-auth"])


@router.get("")
async def google_auth_redirect():
    """Redirect the user to Google's OAuth consent screen."""
    auth_url = google_calendar_service.get_auth_url()
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def google_auth_callback(code: str):
    """Handle the OAuth callback from Google — exchange code for tokens."""
    try:
        await google_calendar_service.exchange_code(code)
        return HTMLResponse(
            content="""
            <html>
            <body style="font-family: -apple-system, sans-serif; display: flex;
                         justify-content: center; align-items: center; height: 100vh;
                         background: #0E0E10; color: #E5E5E7;">
                <div style="text-align: center;">
                    <h1 style="color: #73C8A9;">Connected!</h1>
                    <p>Google Calendar is now linked to ADHD Second Brain.</p>
                    <p style="color: #75757B;">You can close this tab.</p>
                </div>
            </body>
            </html>
            """,
            status_code=200,
        )
    except Exception as e:
        logger.error(f"Google OAuth callback failed: {e}")
        return HTMLResponse(
            content=f"""
            <html>
            <body style="font-family: -apple-system, sans-serif; display: flex;
                         justify-content: center; align-items: center; height: 100vh;
                         background: #0E0E10; color: #E5E5E7;">
                <div style="text-align: center;">
                    <h1 style="color: #FF6F61;">Authentication Failed</h1>
                    <p>{e}</p>
                    <p style="color: #75757B;">Try again at <a href="/api/auth/google" style="color: #99CDF0;">/api/auth/google</a></p>
                </div>
            </body>
            </html>
            """,
            status_code=400,
        )


@router.get("/status")
async def google_auth_status():
    """Check whether Google Calendar is authenticated."""
    return {
        "connected": google_calendar_service.is_authenticated,
    }


@router.post("/revoke")
async def google_auth_revoke():
    """Disconnect Google Calendar (clear stored tokens)."""
    google_calendar_service.revoke()
    return {"status": "revoked"}
