"""
4-layer Activity Classifier for the ADHD Second Brain system.

Classification pipeline:
  L1: App name lookup       (~70% coverage, <1ms)
  L2: URL domain lookup     (~20% coverage, <1ms)
  L3: Window title keywords (~8% coverage, <2ms)
  L4: MLX fallback          (~2%, placeholder — implemented in Phase 7)
"""

import json
import re
from pathlib import Path
from urllib.parse import urlparse

# ── Constants ───────────────────────────────────────────────────────
KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

VALID_CATEGORIES = {
    "development", "writing", "research", "communication",
    "social_media", "entertainment", "news", "shopping",
    "productivity", "design", "finance", "browser", "system", "other",
}

# L3 — keyword → category mapping for window title heuristics
TITLE_KEYWORDS: dict[str, str] = {
    # Entertainment
    "youtube": "entertainment",
    "netflix": "entertainment",
    "twitch": "entertainment",
    "spotify": "entertainment",
    "disney+": "entertainment",
    # Social media
    "reddit": "social_media",
    "twitter": "social_media",
    "instagram": "social_media",
    "tiktok": "social_media",
    "facebook": "social_media",
    # Development
    "github": "development",
    "gitlab": "development",
    "stack overflow": "development",
    "pull request": "development",
    "localhost": "development",
    "terminal": "development",
    # Shopping
    "amazon": "shopping",
    "shopee": "shopping",
    "cart": "shopping",
    "checkout": "shopping",
    # News
    "bbc": "news",
    "cnn": "news",
    "reuters": "news",
    "breaking news": "news",
    # Productivity
    "notion": "productivity",
    "todoist": "productivity",
    "trello": "productivity",
    # Finance
    "trading": "finance",
    "coinmarketcap": "finance",
    "binance": "finance",
    "robinhood": "finance",
    # Research
    "arxiv": "research",
    "scholar": "research",
    "wikipedia": "research",
    "pubmed": "research",
}


class ActivityClassifier:
    """Classifies screen activity into productivity categories using a 4-layer pipeline."""

    def __init__(self) -> None:
        self._app_categories = self._load_json("app_categories.json")
        self._url_categories = self._load_json("url_categories.json")

    # ── Public API ──────────────────────────────────────────────────

    def classify(
        self,
        app_name: str,
        window_title: str,
        url: str | None = None,
    ) -> tuple[str, int]:
        """
        Classify the current screen activity.

        Returns:
            (category, layer) — the matched category and which layer matched (1–4).
        """
        # L1: App name lookup
        category = self._classify_by_app(app_name)
        if category and category != "browser":
            return category, 1

        # L2: URL domain lookup (only if URL is provided)
        if url:
            category = self._classify_by_url(url)
            if category:
                return category, 2

        # L3: Window title keyword matching
        category = self._classify_by_title(window_title)
        if category:
            return category, 3

        # If app was classified as "browser" but no URL/title match, return browser
        if self._classify_by_app(app_name) == "browser":
            return "browser", 1

        # L4: MLX fallback (placeholder — returns "other" for now)
        return "other", 4

    # ── Private methods ─────────────────────────────────────────────

    def _classify_by_app(self, app_name: str) -> str | None:
        """L1: Direct app name lookup."""
        return self._app_categories.get(app_name)

    def _classify_by_url(self, url: str) -> str | None:
        """L2: Domain extraction + lookup with parent-domain fallback."""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                return None

            # Direct domain lookup
            category = self._url_categories.get(hostname)
            if category:
                return category

            # Strip 'www.' prefix
            if hostname.startswith("www."):
                hostname = hostname[4:]
                category = self._url_categories.get(hostname)
                if category:
                    return category

            # Parent domain fallback (e.g., mail.google.com → google.com)
            parts = hostname.split(".")
            if len(parts) > 2:
                parent = ".".join(parts[-2:])
                category = self._url_categories.get(parent)
                if category:
                    return category

            return None
        except Exception:
            return None

    def _classify_by_title(self, window_title: str) -> str | None:
        """L3: Keyword matching in window title (case-insensitive)."""
        title_lower = window_title.lower()
        for keyword, category in TITLE_KEYWORDS.items():
            if keyword in title_lower:
                return category
        return None

    def _load_json(self, filename: str) -> dict:
        """Load a JSON knowledge base file."""
        filepath = KNOWLEDGE_DIR / filename
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠ Knowledge base not found: {filepath}")
            return {}
