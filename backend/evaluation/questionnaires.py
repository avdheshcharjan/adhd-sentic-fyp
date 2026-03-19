"""
Standardized questionnaire scoring for FYP evaluation.

Implements:
- ASRS-v1.1 Screener (6-item Part A) — WHO Adult ADHD Self-Report Scale
- SUS — System Usability Scale (Brooke, 1996)
"""


# ASRS-v1.1 Part A Screener
# Each item scored 0-4 (Never=0, Rarely=1, Sometimes=2, Often=3, Very Often=4)
# Items 1-3: threshold at "Sometimes" (score >= 2 counts)
# Items 4-6: threshold at "Often" (score >= 3 counts)
# 4+ items above threshold = positive screen

ASRS_QUESTIONS = [
    "How often do you have trouble wrapping up the final details of a project, once the challenging parts have been done?",
    "How often do you have difficulty getting things in order when you have to do a task that requires organization?",
    "How often do you have problems remembering appointments or obligations?",
    "When you have a task that requires a lot of thought, how often do you avoid or delay getting started?",
    "How often do you fidget or squirm with your hands or feet when you have to sit down for a long time?",
    "How often do you feel overly active and compelled to do things, like you were driven by a motor?",
]

ASRS_THRESHOLDS = [2, 2, 2, 3, 3, 3]  # Items 1-3: >=2, Items 4-6: >=3


def score_asrs(responses: list[int]) -> dict:
    """
    Score the ASRS-v1.1 Part A screener.

    Args:
        responses: List of 6 integers (0-4) corresponding to each question.

    Returns:
        Dict with total score, items above threshold, and screening result.
    """
    assert len(responses) == 6, "ASRS Part A requires exactly 6 responses"
    assert all(0 <= r <= 4 for r in responses), "Each response must be 0-4"

    items_above_threshold = sum(
        1 for score, threshold in zip(responses, ASRS_THRESHOLDS)
        if score >= threshold
    )

    return {
        "total_score": sum(responses),
        "max_score": 24,
        "items_above_threshold": items_above_threshold,
        "positive_screen": items_above_threshold >= 4,
        "individual_scores": responses,
    }


# SUS — System Usability Scale
# 10 items, scored 1-5 (Strongly Disagree to Strongly Agree)
# Odd items: score - 1; Even items: 5 - score
# Sum * 2.5 = final score (0-100)

SUS_QUESTIONS = [
    "I think that I would like to use this system frequently.",
    "I found the system unnecessarily complex.",
    "I thought the system was easy to use.",
    "I think that I would need the support of a technical person to be able to use this system.",
    "I found the various functions in this system were well integrated.",
    "I thought there was too much inconsistency in this system.",
    "I would imagine that most people would learn to use this system very quickly.",
    "I found the system very cumbersome to use.",
    "I felt very confident using the system.",
    "I needed to learn a lot of things before I could get going with this system.",
]


def score_sus(responses: list[int]) -> dict:
    """
    Score the System Usability Scale.

    Args:
        responses: List of 10 integers (1-5) corresponding to each question.

    Returns:
        Dict with SUS score (0-100) and interpretation.
    """
    assert len(responses) == 10, "SUS requires exactly 10 responses"
    assert all(1 <= r <= 5 for r in responses), "Each response must be 1-5"

    adjusted = []
    for i, score in enumerate(responses):
        if i % 2 == 0:  # Odd items (0-indexed even): score - 1
            adjusted.append(score - 1)
        else:            # Even items (0-indexed odd): 5 - score
            adjusted.append(5 - score)

    sus_score = sum(adjusted) * 2.5

    # Interpretation based on Bangor et al. (2009)
    if sus_score >= 85.5:
        grade = "A+ (Excellent)"
    elif sus_score >= 80.3:
        grade = "A (Excellent)"
    elif sus_score >= 68:
        grade = "B (Good)"
    elif sus_score >= 51:
        grade = "C (OK)"
    elif sus_score >= 25:
        grade = "D (Poor)"
    else:
        grade = "F (Awful)"

    return {
        "sus_score": sus_score,
        "max_score": 100.0,
        "grade": grade,
        "adjusted_item_scores": adjusted,
        "raw_scores": responses,
    }
