"""
Async HTTP client for SenticNet's 13 affective computing APIs.

API Response Format (confirmed via live testing):
- Individual APIs return plain text: "NEGATIVE", "41", "33.33%", "fear (99.7%) & annoyance (50.0%)"
- Ensemble returns semicolon-delimited: "NEGATIVE;41;fear...;0;-16.5;0;-65.9;ENTJ...;...;33.33%;33.33%;-33.33%;-33.33%"
- Percentages include '%' suffix
- HTML entities: &#8593; = ↑, &#8595; = ↓
- Illegal chars in input: & # ; { } → must be stripped

API URL format: https://sentic.net/api/{LANG}/{KEY}.py?text={TEXT}
"""

import re
import logging
from typing import Optional

import httpx

from config import get_settings

settings = get_settings()

logger = logging.getLogger("adhd-brain")

# ── Constants ───────────────────────────────────────────────────────
MAX_TEXT_LENGTH = 8000
ILLEGAL_CHARS_SET = set(["&", "#", ";", "{", "}"])

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# ── API Key → Endpoint Mapping ──────────────────────────────────────
# Each key from SENTIC-API.md mapped to its function
API_ENDPOINTS = {
    "concept_parsing":    "SENTIC_CONCEPT_PARSING",
    "subjectivity":       "SENTIC_SUBJECTIVITY",
    "polarity":           "SENTIC_POLARITY",
    "intensity":          "SENTIC_INTENSITY",
    "emotion":            "SENTIC_EMOTION",
    "aspect":             "SENTIC_ASPECT",
    "personality":        "SENTIC_PERSONALITY",
    "sarcasm":            "SENTIC_SARCASM",
    "depression":         "SENTIC_DEPRESSION",
    "toxicity":           "SENTIC_TOXICITY",
    "engagement":         "SENTIC_ENGAGEMENT",
    "wellbeing":          "SENTIC_WELLBEING",
    "ensemble":           "SENTIC_ENSEMBLE",
}

# Ensemble response field order (14 fields, semicolon-delimited)
ENSEMBLE_FIELDS = [
    "polarity", "intensity", "emotions",
    "introspection", "temper", "attitude", "sensitivity",
    "personality", "aspects", "sarcasm",
    "depression", "toxicity", "engagement", "wellbeing",
]


class SenticNetClient:
    """Async HTTP client for SenticNet APIs.

    Usage:
        client = SenticNetClient()
        emotion = await client.get_emotion("I can't focus today")
        depression = await client.get_depression("I feel hopeless")
    """

    def __init__(self, lang: str = "en", timeout: float = 30.0):
        self.lang = lang
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    # ── Lifecycle ────────────────────────────────────────────────────

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy-init the async client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": USER_AGENT},
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ── Text Sanitization ────────────────────────────────────────────

    @staticmethod
    def sanitize(text: str) -> str:
        """Sanitize text for SenticNet API.

        - Remove illegal characters: & # ; { }
        - Cap at 8000 characters
        - Strip whitespace
        """
        if not text:
            return ""

        # Replace illegal characters with ':' to preserve token boundaries
        out = []
        for ch in text:
            if ch in ILLEGAL_CHARS_SET:
                out.append(":")
            else:
                out.append(ch)

        clean = ("".join(out)).strip()
        return clean[:MAX_TEXT_LENGTH]

    # ── Core API Call ────────────────────────────────────────────────

    async def _call_api(self, api_name: str, text: str) -> Optional[str]:
        """Make a single API call and return raw response text.

        Returns None on any error (timeout, connection, invalid key).
        """
        config_key = API_ENDPOINTS.get(api_name)
        if not config_key:
            logger.error(f"Unknown API: {api_name}")
            return None

        api_key = getattr(settings, config_key, None)
        if not api_key:
            logger.warning(f"No API key configured for {api_name} ({config_key})")
            return None

        # Respect whether SenticNet calls are allowed (user consent / config)
        if not getattr(settings, "SENTICNET_ENABLED", True):
            logger.info("SenticNet calls are disabled by configuration; skipping API call")
            return None

        sanitized = self.sanitize(text)
        if not sanitized:
            return None

        url = f"https://sentic.net/api/{self.lang}/{api_key}.py"

        try:
            client = await self._get_client()
            response = await client.get(url, params={"text": sanitized})
            response.raise_for_status()

            raw = response.text.strip()
            # Clean HTML entities
            raw = raw.replace("&#8593;", "↑").replace("&#8595;", "↓")

            if "Internal Server Error" in raw:
                logger.warning(f"SenticNet {api_name} returned error for text: {text[:50]}...")
                return None

            return raw
        except httpx.TimeoutException:
            logger.warning(f"SenticNet {api_name} timed out")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"SenticNet {api_name} HTTP {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"SenticNet {api_name} error: {e}")
            return None

    # ── Individual API Methods ───────────────────────────────────────

    async def get_polarity(self, text: str) -> Optional[str]:
        """Returns "POSITIVE", "NEGATIVE", or "NEUTRAL"."""
        return await self._call_api("polarity", text)

    async def get_intensity(self, text: str) -> Optional[float]:
        """Returns intensity score (-100 to 100)."""
        raw = await self._call_api("intensity", text)
        return self._parse_number(raw)

    async def get_emotion(self, text: str) -> Optional[str]:
        """Returns emotion string, e.g. 'fear (99.7%) & annoyance (50.0%)'."""
        return await self._call_api("emotion", text)

    async def get_subjectivity(self, text: str) -> Optional[str]:
        """Returns subjectivity detection result."""
        return await self._call_api("subjectivity", text)

    async def get_sarcasm(self, text: str) -> Optional[str]:
        """Returns sarcasm detection result."""
        return await self._call_api("sarcasm", text)

    async def get_depression(self, text: str) -> Optional[float]:
        """Returns depression score (0-100, from percentage)."""
        raw = await self._call_api("depression", text)
        return self._parse_percentage(raw)

    async def get_toxicity(self, text: str) -> Optional[float]:
        """Returns toxicity score (0-100, from percentage)."""
        raw = await self._call_api("toxicity", text)
        return self._parse_percentage(raw)

    async def get_engagement(self, text: str) -> Optional[float]:
        """Returns engagement score (-100 to 100, from percentage)."""
        raw = await self._call_api("engagement", text)
        return self._parse_percentage(raw)

    async def get_wellbeing(self, text: str) -> Optional[float]:
        """Returns well-being score (-100 to 100, from percentage)."""
        raw = await self._call_api("wellbeing", text)
        return self._parse_percentage(raw)

    async def get_personality(self, text: str) -> Optional[str]:
        """Returns personality string, e.g. 'ENTJ (O↑C↑E↑A↓N↓)'."""
        return await self._call_api("personality", text)

    async def get_concepts(self, text: str) -> Optional[str]:
        """Returns concept parsing result."""
        return await self._call_api("concept_parsing", text)

    async def get_aspects(self, text: str) -> Optional[str]:
        """Returns aspect extraction result."""
        return await self._call_api("aspect", text)

    async def get_ensemble(self, text: str) -> Optional[dict]:
        """Call the ensemble API and parse the semicolon-delimited response.

        Returns a dict with all 14 fields, or None on failure.
        Response format: POLARITY;INTENSITY;EMOTIONS;INTROSPECTION;TEMPER;ATTITUDE;
                         SENSITIVITY;PERSONALITY;ASPECTS;SARCASM;DEPRESSION%;TOXICITY%;
                         ENGAGEMENT%;WELLBEING%
        """
        raw = await self._call_api("ensemble", text)
        if raw is None:
            return None

        values = raw.split(";")
        if len(values) < len(ENSEMBLE_FIELDS):
            logger.warning(
                f"Ensemble returned {len(values)} fields, expected {len(ENSEMBLE_FIELDS)}"
            )
            # Pad with empty strings
            values.extend([""] * (len(ENSEMBLE_FIELDS) - len(values)))

        return dict(zip(ENSEMBLE_FIELDS, [v.strip() for v in values]))

    # ── Response Parsers ─────────────────────────────────────────────

    @staticmethod
    def _parse_number(raw: Optional[str]) -> Optional[float]:
        """Parse a plain number like '41' or '-16.5'."""
        if raw is None:
            return None
        try:
            return float(raw.strip())
        except ValueError:
            return None

    @staticmethod
    def _parse_percentage(raw: Optional[str]) -> Optional[float]:
        """Parse a percentage like '33.33%' or '-33.33%' → 33.33 or -33.33."""
        if raw is None:
            return None
        try:
            return float(raw.strip().rstrip("%"))
        except ValueError:
            return None

    @staticmethod
    def parse_emotion_string(raw: str) -> dict:
        """Parse emotion string like 'fear (99.7%) & annoyance (50.0%)'.

        Returns: {"primary": "fear", "primary_score": 99.7,
                  "secondary": "annoyance", "secondary_score": 50.0}
        """
        result = {"primary": "unknown", "primary_score": 0.0}

        if not raw or raw == "No emotions detected":
            return result

        # Pattern: emotion_name (score%)
        pattern = r"(\w+)\s*\((\d+\.?\d*)%\)"
        matches = re.findall(pattern, raw)

        if matches:
            result["primary"] = matches[0][0]
            result["primary_score"] = float(matches[0][1])
            if len(matches) > 1:
                result["secondary"] = matches[1][0]
                result["secondary_score"] = float(matches[1][1])

        return result

    @staticmethod
    def parse_personality_string(raw: str) -> dict:
        """Parse personality like 'ENTJ (O↑C↑E↑A↓N↓)'.

        Returns: {"mbti": "ENTJ", "O": "↑", "C": "↑", "E": "↑", "A": "↓", "N": "↓"}
        """
        result = {"mbti": "", "O": "", "C": "", "E": "", "A": "", "N": ""}

        if not raw or "No personality" in raw:
            return result

        parts = raw.split("(")
        if parts:
            result["mbti"] = parts[0].strip()

        for trait in ["O", "C", "E", "A", "N"]:
            if f"{trait}↑" in raw:
                result[trait] = "↑"
            elif f"{trait}↓" in raw:
                result[trait] = "↓"

        return result
