"""
Google Calendar OAuth 2.0 service.
Handles token exchange, refresh, storage, and Calendar API calls.
Tokens are stored in a local JSON file (data/google_tokens.json).
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional

import httpx

from config import get_settings

logger = logging.getLogger("adhd-brain.google-calendar")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_API = "https://www.googleapis.com/calendar/v3"
SCOPES = "https://www.googleapis.com/auth/calendar.readonly"

TOKEN_FILE = Path("data/google_tokens.json")


class GoogleCalendarService:
    """Manages Google OAuth tokens and fetches calendar events."""

    def __init__(self) -> None:
        self._tokens: dict | None = None
        self._load_tokens()

    def _load_tokens(self) -> None:
        """Load tokens from disk if they exist."""
        if TOKEN_FILE.exists():
            try:
                self._tokens = json.loads(TOKEN_FILE.read_text())
                logger.info("Loaded Google Calendar tokens from disk")
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load Google tokens: {e}")
                self._tokens = None

    def _save_tokens(self) -> None:
        """Persist tokens to disk."""
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(json.dumps(self._tokens, indent=2))
        logger.info("Saved Google Calendar tokens to disk")

    @property
    def is_authenticated(self) -> bool:
        return self._tokens is not None and "access_token" in self._tokens

    def get_auth_url(self) -> str:
        """Build the Google OAuth consent URL."""
        settings = get_settings()
        params = {
            "client_id": settings.GOOGLE_CALENDAR_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_CALENDAR_REDIRECT_URI,
            "response_type": "code",
            "scope": SCOPES,
            "access_type": "offline",
            "prompt": "consent",
        }
        query = "&".join(f"{k}={httpx.URL('', params={k: v}).params[k]}" for k, v in params.items())
        return f"{GOOGLE_AUTH_URL}?{query}"

    async def exchange_code(self, code: str) -> dict:
        """Exchange the authorization code for access + refresh tokens."""
        settings = get_settings()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CALENDAR_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CALENDAR_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_CALENDAR_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        self._tokens = {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", self._tokens.get("refresh_token", "") if self._tokens else ""),
            "expires_at": time.time() + data.get("expires_in", 3600),
            "token_type": data.get("token_type", "Bearer"),
        }
        self._save_tokens()
        logger.info("Google Calendar OAuth tokens exchanged successfully")
        return self._tokens

    async def _refresh_access_token(self) -> None:
        """Use the refresh token to get a new access token."""
        if not self._tokens or not self._tokens.get("refresh_token"):
            raise RuntimeError("No refresh token available — re-authenticate via /api/auth/google")

        settings = get_settings()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CALENDAR_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CALENDAR_CLIENT_SECRET,
                    "refresh_token": self._tokens["refresh_token"],
                    "grant_type": "refresh_token",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        self._tokens["access_token"] = data["access_token"]
        self._tokens["expires_at"] = time.time() + data.get("expires_in", 3600)
        self._save_tokens()
        logger.info("Google Calendar access token refreshed")

    async def _get_valid_token(self) -> str:
        """Return a valid access token, refreshing if expired."""
        if not self._tokens:
            raise RuntimeError("Not authenticated — visit /api/auth/google first")

        if time.time() >= self._tokens.get("expires_at", 0) - 60:
            await self._refresh_access_token()

        return self._tokens["access_token"]

    async def get_upcoming_events(self, max_results: int = 3) -> list[dict]:
        """Fetch upcoming calendar events from the primary calendar."""
        token = await self._get_valid_token()

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GOOGLE_CALENDAR_API}/calendars/primary/events",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "timeMin": now,
                    "maxResults": max_results,
                    "singleEvents": "true",
                    "orderBy": "startTime",
                },
            )

            if resp.status_code == 401:
                # Token expired mid-request, refresh and retry once
                await self._refresh_access_token()
                token = self._tokens["access_token"]
                resp = await client.get(
                    f"{GOOGLE_CALENDAR_API}/calendars/primary/events",
                    headers={"Authorization": f"Bearer {token}"},
                    params={
                        "timeMin": now,
                        "maxResults": max_results,
                        "singleEvents": "true",
                        "orderBy": "startTime",
                    },
                )

            resp.raise_for_status()
            data = resp.json()

        events = []
        for item in data.get("items", []):
            start = item.get("start", {})
            start_str = start.get("dateTime", start.get("date", ""))

            # Parse to friendly time string
            friendly_time = self._format_event_time(start_str)

            events.append({
                "id": item.get("id", ""),
                "title": item.get("summary", "Untitled"),
                "start_time": friendly_time,
                "emoji": self._pick_emoji(item.get("summary", "")),
            })

        return events

    @staticmethod
    def _format_event_time(iso_str: str) -> str:
        """Convert ISO datetime to a friendly time like '2:00 PM'."""
        from datetime import datetime
        try:
            # Handle both datetime and date-only formats
            if "T" in iso_str:
                dt = datetime.fromisoformat(iso_str)
                return dt.strftime("%-I:%M %p")
            return iso_str  # All-day event, return date as-is
        except (ValueError, TypeError):
            return iso_str

    @staticmethod
    def _pick_emoji(summary: str) -> str:
        """Pick a contextual emoji based on event title keywords."""
        lower = summary.lower()
        if any(w in lower for w in ("meet", "sync", "standup", "1:1", "call")):
            return "\U0001F4F9"  # video camera
        if any(w in lower for w in ("lunch", "dinner", "coffee", "break")):
            return "\u2615"  # coffee
        if any(w in lower for w in ("deadline", "due", "submit")):
            return "\u23F0"  # alarm clock
        if any(w in lower for w in ("gym", "workout", "run", "exercise")):
            return "\U0001F3CB"  # weightlifter
        if any(w in lower for w in ("demo", "present", "review")):
            return "\U0001F680"  # rocket
        if any(w in lower for w in ("doctor", "dentist", "appointment")):
            return "\U0001FA7A"  # stethoscope
        return "\U0001F4C5"  # calendar emoji

    def revoke(self) -> None:
        """Clear stored tokens (logout)."""
        self._tokens = None
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
        logger.info("Google Calendar tokens revoked")


# Singleton
google_calendar_service = GoogleCalendarService()
