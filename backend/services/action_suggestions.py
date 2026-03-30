"""Shared action-suggestion logic used by both REST API and Telegram bot."""

from services.constants import CRISIS_RESOURCES_SG


def get_suggested_actions(result: dict) -> list[dict]:
    """Generate suggested actions based on pipeline result.

    Args:
        result: Dict from ChatProcessor.process_vent_message().

    Returns:
        List of action dicts with 'id' and 'label' keys (max 3).
    """
    if not result["used_llm"]:
        return [
            {"id": r["id"], "label": r["label"]}
            for r in CRISIS_RESOURCES_SG
        ]

    senticnet = result.get("senticnet", {})
    if not senticnet:
        # Ablation mode — return default actions
        return [
            {"id": "continue", "label": "Tell me more"},
            {"id": "breathe", "label": "Quick breathing"},
            {"id": "break", "label": "Take a break"},
        ]

    intensity = abs(senticnet.get("intensity_score", 0))
    engagement = senticnet.get("engagement_score", 0)

    actions = []
    if intensity > 60:
        actions.append({"id": "breathe", "label": "2-minute breathing exercise"})
    if engagement < -30:
        actions.append({"id": "smallest_step", "label": "Pick the smallest next step"})
    if intensity < -50:
        actions.append({"id": "break", "label": "Take a short break"})

    if not actions:
        actions = [
            {"id": "continue", "label": "Tell me more"},
            {"id": "breathe", "label": "Quick breathing"},
            {"id": "break", "label": "Take a break"},
        ]

    return actions[:3]
