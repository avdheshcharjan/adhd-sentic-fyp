"""
4-layer Activity Classifier for the ADHD Second Brain system.

Classification pipeline:
  L0: User corrections     (highest priority, instant)
  L1: App name lookup      (~70% coverage, <1ms)
  L2: URL domain lookup    (~20% coverage, <1ms)
  L3: Window title keywords (~8% coverage, <2ms)
  L4: Embedding similarity  (~2%, <25ms, all-MiniLM-L6-v2)
"""

import json
import logging
from pathlib import Path
from urllib.parse import urlparse

import numpy as np

logger = logging.getLogger("adhd-brain.classifier")

# ── Constants ───────────────────────────────────────────────────────
KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

VALID_CATEGORIES = {
    "development", "writing", "research", "communication",
    "social_media", "entertainment", "news", "shopping",
    "productivity", "design", "finance", "browser", "system", "other",
}

# L3 — keyword -> category mapping for window title heuristics
TITLE_KEYWORDS: dict[str, str] = {
    "youtube": "entertainment",
    "netflix": "entertainment",
    "twitch": "entertainment",
    "spotify": "entertainment",
    "disney+": "entertainment",
    "reddit": "social_media",
    "twitter": "social_media",
    "instagram": "social_media",
    "tiktok": "social_media",
    "facebook": "social_media",
    "github": "development",
    "gitlab": "development",
    "stack overflow": "development",
    "pull request": "development",
    "localhost": "development",
    "terminal": "development",
    "amazon": "shopping",
    "shopee": "shopping",
    "cart": "shopping",
    "checkout": "shopping",
    "bbc": "news",
    "cnn": "news",
    "reuters": "news",
    "breaking news": "news",
    "notion": "productivity",
    "todoist": "productivity",
    "trello": "productivity",
    "trading": "finance",
    "coinmarketcap": "finance",
    "binance": "finance",
    "robinhood": "finance",
    "arxiv": "research",
    "scholar": "research",
    "wikipedia": "research",
    "pubmed": "research",
    "chatgpt": "other",
    "weather": "other",
    "maps": "other",
}

# Category descriptions for Layer 4 zero-shot embedding similarity
CATEGORY_DESCRIPTIONS = {
    "development": "Programming, coding, software development, debugging, terminal, IDE, code editor, GitHub, pull request, repository",
    "writing": "Writing documents, essays, reports, notes, drafting text, word processing, blogging, LaTeX, Overleaf",
    "research": "Academic research, reading papers, Wikipedia, scholarly articles, learning, studying, arxiv, library",
    "communication": "Email, messaging, video calls, chat, Slack, Teams, meetings, correspondence, Discord",
    "social_media": "Social media browsing, Twitter, Instagram, Reddit, TikTok, Facebook, LinkedIn feed, scrolling",
    "entertainment": "Watching videos, streaming, gaming, music, YouTube, Netflix, Twitch, Spotify, anime",
    "news": "Reading news articles, current events, BBC, CNN, news websites, journalism, headlines",
    "shopping": "Online shopping, browsing products, Amazon, Shopee, Lazada, comparing prices, e-commerce, cart",
    "design": "Graphic design, UI design, Figma, Sketch, Photoshop, illustration, prototyping, wireframe",
    "productivity": "Task management, calendars, to-do lists, project management, Notion, spreadsheets, Obsidian",
}


class ActivityClassifier:
    """
    Classifies screen activity into productivity categories using a 5-layer pipeline.

    Layer 0: User corrections (highest priority, instant)
    Layer 1: App name lookup (~70% of cases, <0.01ms)
    Layer 2: URL domain lookup (~20% of browser cases, <0.01ms)
    Layer 3: Window title keywords (~8% of remaining, <0.1ms)
    Layer 4: Zero-shot embedding similarity (~2% fallback, <25ms)
    """

    def __init__(self) -> None:
        self._app_categories = self._load_json("app_categories.json")
        self._url_categories = self._load_json("url_categories.json")
        self._embedding_model = None
        self._category_embeddings = None
        self.user_corrections: dict[str, str] = {}

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
            (category, layer) — the matched category and which layer matched (0-4).
        """
        # L0: User corrections (highest priority)
        correction_key = f"{app_name}|{window_title}".strip().lower()
        if correction_key in self.user_corrections:
            return self.user_corrections[correction_key], 0

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

        # L4: Zero-shot embedding similarity
        return self._classify_by_embedding(app_name, window_title)

    def record_correction(self, app_name: str, window_title: str, correct_category: str):
        """User corrects a misclassification. Takes effect immediately."""
        key = f"{app_name}|{window_title}".strip().lower()
        self.user_corrections[key] = correct_category

    def load_corrections_from_db(self, corrections: dict[str, str]):
        """Load persisted corrections on startup."""
        self.user_corrections = corrections

    # ── Private methods ─────────────────────────────────────────────

    def _ensure_embedding_model(self):
        """Lazy-load sentence transformer only when needed (Layer 4 fallback)."""
        if self._embedding_model is None:
            from sentence_transformers import SentenceTransformer
            self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            self._category_embeddings = self._embedding_model.encode(
                list(CATEGORY_DESCRIPTIONS.values()),
                normalize_embeddings=True,
            )
            logger.info("Loaded all-MiniLM-L6-v2 for Layer 4 classification")

    def _classify_by_embedding(self, app_name: str, window_title: str) -> tuple[str, int]:
        """L4: Zero-shot embedding similarity. <25ms on M4."""
        self._ensure_embedding_model()
        title_embedding = self._embedding_model.encode(
            f"{app_name}: {window_title}",
            normalize_embeddings=True,
        )
        similarities = np.dot(self._category_embeddings, title_embedding)
        best_idx = int(np.argmax(similarities))
        confidence = float(similarities[best_idx])
        category_names = list(CATEGORY_DESCRIPTIONS.keys())

        if confidence > 0.15:
            return category_names[best_idx], 4

        return "other", 4

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

            category = self._url_categories.get(hostname)
            if category:
                return category

            if hostname.startswith("www."):
                hostname = hostname[4:]
                category = self._url_categories.get(hostname)
                if category:
                    return category

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
            logger.warning(f"Knowledge base not found: {filepath}")
            return {}
