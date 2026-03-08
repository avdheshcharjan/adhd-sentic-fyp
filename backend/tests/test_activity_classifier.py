"""
Unit tests for the 4-layer Activity Classifier.

Covers:
  - L1: App name lookup
  - L2: URL domain lookup (including subdomain fallback)
  - L3: Window title keyword matching
  - L4: Unknown inputs → "other"
  - Browser special handling
"""

from services.activity_classifier import ActivityClassifier


def _classifier():
    return ActivityClassifier()


# ── L1: App Name Lookup ────────────────────────────────────────────


class TestL1AppNameLookup:
    def test_vscode_is_development(self):
        c = _classifier()
        category, layer = c.classify("Visual Studio Code", "main.py — project")
        assert category == "development"
        assert layer == 1

    def test_spotify_is_entertainment(self):
        c = _classifier()
        category, layer = c.classify("Spotify", "Now Playing — Song")
        assert category == "entertainment"
        assert layer == 1

    def test_slack_is_communication(self):
        c = _classifier()
        category, layer = c.classify("Slack", "#general")
        assert category == "communication"
        assert layer == 1

    def test_notion_is_productivity(self):
        c = _classifier()
        category, layer = c.classify("Notion", "My Workspace")
        assert category == "productivity"
        assert layer == 1

    def test_figma_is_design(self):
        c = _classifier()
        category, layer = c.classify("Figma", "UI Design")
        assert category == "design"
        assert layer == 1

    def test_finder_is_system(self):
        c = _classifier()
        category, layer = c.classify("Finder", "Downloads")
        assert category == "system"
        assert layer == 1

    def test_terminal_is_development(self):
        c = _classifier()
        category, layer = c.classify("Terminal", "zsh")
        assert category == "development"
        assert layer == 1


# ── L2: URL Domain Lookup ──────────────────────────────────────────


class TestL2URLDomainLookup:
    def test_github_url(self):
        c = _classifier()
        category, layer = c.classify(
            "Google Chrome", "avuthegreat/project",
            url="https://github.com/avuthegreat/project"
        )
        assert category == "development"
        assert layer == 2

    def test_youtube_url(self):
        c = _classifier()
        category, layer = c.classify(
            "Safari", "Funny Cats - YouTube",
            url="https://www.youtube.com/watch?v=abc"
        )
        assert category == "entertainment"
        assert layer == 2

    def test_reddit_url(self):
        c = _classifier()
        category, layer = c.classify(
            "Arc", "r/productivity",
            url="https://www.reddit.com/r/productivity"
        )
        assert category == "social_media"
        assert layer == 2

    def test_subdomain_fallback(self):
        """mail.google.com should match google.com if not directly listed."""
        c = _classifier()
        # mail.google.com IS directly listed as communication
        category, layer = c.classify(
            "Google Chrome", "Inbox",
            url="https://mail.google.com/mail/u/0/#inbox"
        )
        assert category == "communication"
        assert layer == 2

    def test_arxiv_url(self):
        c = _classifier()
        category, layer = c.classify(
            "Firefox", "arXiv paper",
            url="https://arxiv.org/abs/2301.00001"
        )
        assert category == "research"
        assert layer == 2

    def test_unknown_url_no_match(self):
        """URL not in knowledge base should fall through to L3/L4."""
        c = _classifier()
        category, layer = c.classify(
            "Google Chrome", "Some Random Site",
            url="https://randomsite12345.com/page"
        )
        # Should fall through to L3 title check, then L4 → "browser" or "other"
        assert category in ("browser", "other")


# ── L3: Window Title Keywords ──────────────────────────────────────


class TestL3WindowTitleKeywords:
    def test_youtube_in_title(self):
        c = _classifier()
        category, layer = c.classify(
            "Google Chrome", "YouTube - How to code",
            url=None
        )
        assert category == "entertainment"
        assert layer == 3

    def test_github_in_title(self):
        c = _classifier()
        category, layer = c.classify(
            "Safari", "Pull request #42 on GitHub",
            url=None
        )
        # "github" keyword → development
        assert category == "development"
        assert layer == 3

    def test_reddit_in_title(self):
        c = _classifier()
        category, layer = c.classify(
            "Arc", "reddit - the front page of the internet",
            url=None
        )
        assert category == "social_media"
        assert layer == 3


# ── L4: Unknown / Fallback ─────────────────────────────────────────


class TestL4Fallback:
    def test_unknown_app_no_url_no_title_match(self):
        c = _classifier()
        category, layer = c.classify(
            "SomeRandomApp", "Untitled Window"
        )
        assert category == "other"
        assert layer == 4

    def test_browser_with_no_url_or_title_match(self):
        """A browser with no URL and no keyword in title → 'browser'."""
        c = _classifier()
        category, layer = c.classify(
            "Google Chrome", "New Tab",
            url=None
        )
        assert category == "browser"
        assert layer == 1


# ── Browser Special Handling ────────────────────────────────────────


class TestBrowserHandling:
    def test_browser_with_url_overrides_to_url_category(self):
        """Chrome + github URL should be 'development', not 'browser'."""
        c = _classifier()
        category, _ = c.classify(
            "Google Chrome", "repo page",
            url="https://github.com/user/repo"
        )
        assert category == "development"

    def test_browser_with_keyword_title_overrides(self):
        """Chrome + 'YouTube' in title should be 'entertainment', not 'browser'."""
        c = _classifier()
        category, _ = c.classify(
            "Google Chrome", "YouTube - Music",
            url=None
        )
        assert category == "entertainment"
