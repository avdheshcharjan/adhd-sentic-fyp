"""Whoop integration endpoints.

Provides access to Whoop physiological data via the whoopskill CLI.
All data fetching is delegated to the WhoopService which wraps the
whoopskill CLI (koala73/whoopskill).

Prerequisites:
    1. npm install -g whoopskill
    2. whoopskill auth login
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services.whoop_service import (
    WhoopService,
    WhoopNotInstalledError,
    WhoopNotAuthenticatedError,
    WhoopServiceError,
)

router = APIRouter(prefix="/whoop", tags=["whoop"])
whoop = WhoopService()


def _handle_whoop_error(e: WhoopServiceError) -> HTTPException:
    """Convert WhoopServiceError to appropriate HTTPException."""
    if isinstance(e, WhoopNotInstalledError):
        return HTTPException(status_code=503, detail=str(e))
    elif isinstance(e, WhoopNotAuthenticatedError):
        return HTTPException(status_code=401, detail=str(e))
    else:
        return HTTPException(status_code=502, detail=str(e))


@router.get("/status")
async def whoop_status():
    """Check whoopskill CLI installation and authentication status."""
    return await whoop.check_status()


@router.get("/auth")
async def start_oauth():
    """Get instructions for authenticating with Whoop.

    Since auth is handled by the whoopskill CLI (browser-based OAuth),
    this endpoint returns setup instructions rather than initiating a flow.
    """
    status = await whoop.check_status()
    return {
        "auth_method": "whoopskill CLI (browser-based OAuth)",
        "current_status": status,
        "instructions": [
            "1. Install whoopskill: npm install -g whoopskill",
            "2. Set environment variables: WHOOP_CLIENT_ID, WHOOP_CLIENT_SECRET",
            "3. Run: whoopskill auth login",
            "4. Complete OAuth in browser — tokens auto-saved to ~/.whoop-cli/tokens.json",
        ],
        "note": "Apps with <10 users don't need Whoop review (immediate use).",
    }


@router.get("/callback")
async def oauth_callback(code: str = "", state: str = "", scope: str = ""):
    """Handle Whoop OAuth callback.
    
    The whoopskill CLI initiates OAuth but the Whoop app is configured to redirect 
    to http://localhost:8420/whoop/callback. Since our FastAPI backend runs on 8420,
    it intercepts this instead of the whoopskill CLI. 
    
    We just need to tell the user to manually copy the URL to the CLI.
    """
    from fastapi.responses import HTMLResponse
    
    html_content = f"""
    <html>
        <head>
            <title>Whoop Authorization Redirect</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"; margin: 40px auto; max-width: 650px; line-height: 1.6; font-size: 18px; color: #444; padding: 0 10px; }}
                h1 {{ line-height: 1.2; color: #111; }}
                .code-block {{ background-color: #f4f4f4; border-radius: 6px; padding: 15px; font-family: monospace; word-break: break-all; margin: 20px 0; border: 1px solid #ddd; }}
                .info {{ background-color: #e8f4f8; border-left: 5px solid #2196F3; padding: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>Authorization Successful</h1>
            <div class="info">
                The Whoop API successfully authorized your request. To complete the login process, please copy the URL below and paste it back into your terminal where you ran <code>whoopskill auth login</code>.
            </div>
            <p><strong>Copy this exact URL:</strong></p>
            <div class="code-block">http://localhost:8420/whoop/callback?code={code}&state={state}&scope={scope}</div>
            <p>You can close this window after copying.</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@router.get("/recovery")
async def get_recovery(date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD")):
    """Fetch Whoop recovery data (recovery score, HRV, RHR, SpO2)."""
    try:
        records = await whoop.get_recovery(date)
        return {"recovery": [r.model_dump() for r in records]}
    except WhoopServiceError as e:
        raise _handle_whoop_error(e)


@router.get("/sleep")
async def get_sleep(date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD")):
    """Fetch Whoop sleep data (stages, performance, efficiency)."""
    try:
        records = await whoop.get_sleep(date)
        return {"sleep": [s.model_dump() for s in records]}
    except WhoopServiceError as e:
        raise _handle_whoop_error(e)


@router.get("/cycle")
async def get_cycle(date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD")):
    """Fetch Whoop cycle/strain data."""
    try:
        records = await whoop.get_cycle(date)
        return {"cycle": [c.model_dump() for c in records]}
    except WhoopServiceError as e:
        raise _handle_whoop_error(e)


@router.get("/raw")
async def get_raw_data(date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD")):
    """Fetch all raw Whoop data for a date (recovery + sleep + cycle)."""
    try:
        data = await whoop.get_all_data(date)
        return data
    except WhoopServiceError as e:
        raise _handle_whoop_error(e)


@router.get("/morning-briefing")
async def morning_briefing(date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD")):
    """Generate ADHD-tailored morning briefing from Whoop data.

    Maps recovery score to executive function predictions and sleep
    metrics to ADHD-specific recommendations. Returns focus block
    duration, recovery tier (green/yellow/red), and sleep notes.
    """
    try:
        briefing = await whoop.generate_morning_briefing(date)
        return briefing.model_dump()
    except WhoopServiceError as e:
        raise _handle_whoop_error(e)
