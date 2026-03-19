"""Tests for ASRS and SUS questionnaire scoring."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from evaluation.questionnaires import score_asrs, score_sus


class TestASRS:
    def test_positive_screen(self):
        """All high scores -> positive screen."""
        responses = [4, 4, 4, 4, 4, 4]
        result = score_asrs(responses)
        assert result["positive_screen"] is True
        assert result["items_above_threshold"] == 6
        assert result["total_score"] == 24
        assert result["max_score"] == 24

    def test_negative_screen(self):
        """All zero scores -> negative screen."""
        responses = [0, 0, 0, 0, 0, 0]
        result = score_asrs(responses)
        assert result["positive_screen"] is False
        assert result["items_above_threshold"] == 0
        assert result["total_score"] == 0

    def test_borderline_positive(self):
        """Exactly 4 items above threshold -> positive screen."""
        # Items 1-3 threshold = 2, Items 4-6 threshold = 3
        responses = [2, 2, 2, 3, 0, 0]  # 4 above threshold
        result = score_asrs(responses)
        assert result["positive_screen"] is True
        assert result["items_above_threshold"] == 4

    def test_borderline_negative(self):
        """Only 3 items above threshold -> negative screen."""
        responses = [2, 2, 2, 2, 2, 2]  # Items 1-3: >=2 (3 above), Items 4-6: >=3 (0 above)
        result = score_asrs(responses)
        assert result["positive_screen"] is False
        assert result["items_above_threshold"] == 3

    def test_invalid_length_raises(self):
        with pytest.raises(AssertionError, match="exactly 6"):
            score_asrs([1, 2, 3])

    def test_invalid_range_raises(self):
        with pytest.raises(AssertionError, match="0-4"):
            score_asrs([5, 0, 0, 0, 0, 0])

    def test_individual_scores_preserved(self):
        responses = [1, 2, 3, 4, 0, 1]
        result = score_asrs(responses)
        assert result["individual_scores"] == responses


class TestSUS:
    def test_perfect_score(self):
        """All positive -> 100."""
        responses = [5, 1, 5, 1, 5, 1, 5, 1, 5, 1]
        result = score_sus(responses)
        assert result["sus_score"] == 100.0
        assert result["grade"] == "A+ (Excellent)"

    def test_worst_score(self):
        """All negative -> 0."""
        responses = [1, 5, 1, 5, 1, 5, 1, 5, 1, 5]
        result = score_sus(responses)
        assert result["sus_score"] == 0.0
        assert result["grade"] == "F (Awful)"

    def test_neutral_score(self):
        """All 3s -> 50 (below C threshold of 51)."""
        responses = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
        result = score_sus(responses)
        assert result["sus_score"] == 50.0
        assert result["grade"] == "D (Poor)"

    def test_grade_boundaries(self):
        # B grade: score >= 68
        # For SUS: adjusted = [4, 4, 4, 4, 4, 4, 4, 4, 4, 4] -> 40 * 2.5 = 100 (too high)
        # We need score around 68 -> adjusted sum ~ 27.2
        # Let's compute: 68 / 2.5 = 27.2 adjusted sum needed
        # Build manually: score = [4,2,4,2,4,2,4,2,4,2] -> adj = [3,3,3,3,3,3,3,3,3,3] = 30 -> 75
        responses = [4, 2, 4, 2, 4, 2, 4, 2, 4, 2]
        result = score_sus(responses)
        assert result["sus_score"] == 75.0
        assert result["grade"] == "B (Good)"

    def test_invalid_length_raises(self):
        with pytest.raises(AssertionError, match="exactly 10"):
            score_sus([3, 3, 3])

    def test_invalid_range_raises(self):
        with pytest.raises(AssertionError, match="1-5"):
            score_sus([0, 3, 3, 3, 3, 3, 3, 3, 3, 3])

    def test_raw_scores_preserved(self):
        responses = [4, 2, 4, 2, 4, 2, 4, 2, 4, 2]
        result = score_sus(responses)
        assert result["raw_scores"] == responses
        assert result["max_score"] == 100.0
