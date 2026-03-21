"""Whoop integration endpoints.

Provides access to Whoop physiological data via the whoopskill CLI.
All data fetching is delegated to the WhoopService which wraps the
whoopskill CLI (koala73/whoopskill).

Two routers are exported:
- auth_router  — mounted at /api/auth/whoop (auth flow, status, disconnect)
- data_router  — mounted at /whoop (recovery, sleep, cycle, briefing data)

Prerequisites:
    1. npm install -g whoopskill
    2. whoopskill auth login
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from services.whoop_service import (
    WhoopService,
    WhoopNotInstalledError,
    WhoopNotAuthenticatedError,
    WhoopServiceError,
)

# Auth router — mirrors Google auth pattern at /api/auth/whoop
auth_router = APIRouter(prefix="/api/auth/whoop", tags=["whoop-auth"])

# Data router — Whoop data endpoints at /whoop
data_router = APIRouter(prefix="/whoop", tags=["whoop-data"])

whoop = WhoopService()


def _handle_whoop_error(e: WhoopServiceError) -> HTTPException:
    """Convert WhoopServiceError to appropriate HTTPException."""
    if isinstance(e, WhoopNotInstalledError):
        return HTTPException(status_code=503, detail=str(e))
    elif isinstance(e, WhoopNotAuthenticatedError):
        return HTTPException(status_code=401, detail=str(e))
    else:
        return HTTPException(status_code=502, detail=str(e))


# ── Auth Router (/api/auth/whoop) ─────────────────────────────────────


@auth_router.get("")
async def start_auth():
    """Start Whoop authentication.

    Triggers `whoopskill auth login` via subprocess. If already authenticated,
    returns instructions page. Otherwise initiates the CLI OAuth flow and
    returns setup instructions for the user.
    """
    status = await whoop.check_status()
    if status["authenticated"]:
        return HTMLResponse(
            content="""
            <html>
            <body style="font-family: -apple-system, sans-serif; display: flex;
                         justify-content: center; align-items: center; height: 100vh;
                         background: #0E0E10; color: #E5E5E7;">
                <div style="text-align: center;">
                    <h1 style="color: #73C8A9;">Already Connected!</h1>
                    <p>Whoop is already linked to ADHD Second Brain.</p>
                    <p style="color: #75757B;">You can close this tab.</p>
                </div>
            </body>
            </html>
            """,
            status_code=200,
        )

    return HTMLResponse(
        content="""
        <html>
        <body style="font-family: -apple-system, sans-serif; display: flex;
                     justify-content: center; align-items: center; height: 100vh;
                     background: #0E0E10; color: #E5E5E7;">
            <div style="text-align: center; max-width: 500px;">
                <h1>Connect Whoop</h1>
                <p>Whoop uses the <code style="color: #99CDF0;">whoopskill</code> CLI for authentication.</p>
                <ol style="text-align: left; color: #ABAAB1; line-height: 2;">
                    <li>Install: <code style="color: #99CDF0;">npm install -g whoopskill</code></li>
                    <li>Run: <code style="color: #99CDF0;">whoopskill auth login</code></li>
                    <li>Complete OAuth in your browser</li>
                    <li>Return here and refresh to verify</li>
                </ol>
                <p style="color: #75757B; margin-top: 20px;">
                    Apps with &lt;10 users don't need Whoop review (immediate use).
                </p>
            </div>
        </body>
        </html>
        """,
        status_code=200,
    )


@auth_router.get("/status")
async def whoop_auth_status():
    """Check whether Whoop is connected.

    Returns {"connected": bool} to match the Google auth status contract.
    """
    status = await whoop.check_status()
    return {
        "connected": status["authenticated"],
    }


@auth_router.post("/disconnect")
async def whoop_disconnect():
    """Disconnect Whoop (logout via whoopskill CLI)."""
    await whoop.logout()
    return {"status": "disconnected"}


@auth_router.get("/callback")
async def oauth_callback(code: str = "", state: str = "", scope: str = ""):
    """Handle Whoop OAuth callback.

    The whoopskill CLI initiates OAuth but the Whoop app is configured to redirect
    to http://localhost:8420/api/auth/whoop/callback. Since our FastAPI backend runs
    on 8420, it intercepts this instead of the whoopskill CLI.
    """
    html_content = f"""
    <html>
        <head>
            <title>Whoop Authorization Redirect</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                        margin: 40px auto; max-width: 650px; line-height: 1.6;
                        font-size: 18px; color: #444; padding: 0 10px; }}
                h1 {{ line-height: 1.2; color: #111; }}
                .code-block {{ background-color: #f4f4f4; border-radius: 6px;
                               padding: 15px; font-family: monospace;
                               word-break: break-all; margin: 20px 0;
                               border: 1px solid #ddd; }}
                .info {{ background-color: #e8f4f8; border-left: 5px solid #2196F3;
                         padding: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>Authorization Successful</h1>
            <div class="info">
                The Whoop API successfully authorized your request.
                To complete the login process, please copy the URL below
                and paste it back into your terminal where you ran
                <code>whoopskill auth login</code>.
            </div>
            <p><strong>Copy this exact URL:</strong></p>
            <div class="code-block">
                http://localhost:8420/api/auth/whoop/callback?code={code}&amp;state={state}&amp;scope={scope}
            </div>
            <p>You can close this window after copying.</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


# ── Data Router (/whoop) ──────────────────────────────────────────────


@data_router.get("/status")
async def whoop_data_status():
    """Check whoopskill CLI installation and authentication status (raw)."""
    return await whoop.check_status()


@data_router.get("/recovery")
async def get_recovery(date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD")):
    """Fetch Whoop recovery data (recovery score, HRV, RHR, SpO2)."""
    try:
        records = await whoop.get_recovery(date)
        return {"recovery": [r.model_dump() for r in records]}
    except WhoopServiceError as e:
        raise _handle_whoop_error(e)


@data_router.get("/sleep")
async def get_sleep(date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD")):
    """Fetch Whoop sleep data (stages, performance, efficiency)."""
    try:
        records = await whoop.get_sleep(date)
        return {"sleep": [s.model_dump() for s in records]}
    except WhoopServiceError as e:
        raise _handle_whoop_error(e)


@data_router.get("/cycle")
async def get_cycle(date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD")):
    """Fetch Whoop cycle/strain data."""
    try:
        records = await whoop.get_cycle(date)
        return {"cycle": [c.model_dump() for c in records]}
    except WhoopServiceError as e:
        raise _handle_whoop_error(e)


@data_router.get("/raw")
async def get_raw_data(date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD")):
    """Fetch all raw Whoop data for a date (recovery + sleep + cycle)."""
    try:
        data = await whoop.get_all_data(date)
        return data
    except WhoopServiceError as e:
        raise _handle_whoop_error(e)


@data_router.get("/morning-briefing")
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
