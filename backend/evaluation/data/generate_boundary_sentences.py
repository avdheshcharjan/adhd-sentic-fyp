"""
Generate boundary + general ADHD training sentences using Claude API.

Generates:
    1. Boundary sentences for confused class pairs (~30 per pair)
    2. General ADHD sentences (15-20 per class)

Usage:
    CLAUDE_API_KEY=sk-... python3.11 -m evaluation.data.generate_boundary_sentences

Output: evaluation/data/generated_sentences.json (review before merging)
"""

import json
import os
import sys
from pathlib import Path

import anthropic

ROOT = Path(__file__).parent.parent.parent
OUTPUT_PATH = Path(__file__).parent / "generated_sentences.json"
TRAINING_DATA_PATH = Path(__file__).parent / "emotion_training_data.json"

LABELS = ["joyful", "focused", "frustrated", "anxious", "disengaged", "overwhelmed"]

LABEL_DESCRIPTIONS: dict[str, str] = {
    "joyful": "happiness, excitement, gratitude, pride, connection, celebration",
    "focused": "deep concentration, flow state, being locked in, productive immersion, clarity",
    "frustrated": "irritation, impatience, repeated failures, annoyance, anger at obstacles",
    "anxious": "worry about the future, fear, catastrophizing, dread, nervous anticipation, imposter syndrome",
    "disengaged": "boredom, apathy, numbness, lost interest, going through the motions, disconnection",
    "overwhelmed": "too many tasks, sensory overload, paralysis from too much, shutdown, cognitive flooding",
}

HARD_NEGATIVE_PAIRS: list[tuple[str, str]] = [
    ("anxious", "overwhelmed"),
    ("frustrated", "overwhelmed"),
    ("anxious", "frustrated"),
    ("disengaged", "overwhelmed"),
    ("focused", "frustrated"),
    ("disengaged", "joyful"),
]


def _call_claude(client: anthropic.Anthropic, prompt: str) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _parse_sentences(raw: str) -> list[str]:
    """Parse numbered or bulleted sentences from Claude's response."""
    lines = raw.strip().split("\n")
    sentences: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Strip numbering like "1. ", "- ", "* "
        for prefix_pattern in [".", ")", "-", "*"]:
            parts = line.split(prefix_pattern, 1)
            if len(parts) == 2 and parts[0].strip().isdigit():
                line = parts[1].strip()
                break
            if prefix_pattern in ("-", "*") and line.startswith(prefix_pattern):
                line = line[1:].strip()
                break
        # Strip surrounding quotes
        if (line.startswith('"') and line.endswith('"')) or (
            line.startswith("'") and line.endswith("'")
        ):
            line = line[1:-1]
        if len(line) > 10:
            sentences.append(line)
    return sentences


def generate_boundary_sentences(
    client: anthropic.Anthropic,
) -> list[dict[str, str]]:
    """Generate boundary sentences for confused class pairs."""
    all_sentences: list[dict[str, str]] = []

    for class_a, class_b in HARD_NEGATIVE_PAIRS:
        desc_a = LABEL_DESCRIPTIONS[class_a]
        desc_b = LABEL_DESCRIPTIONS[class_b]

        # 15 sentences clearly class_a and NOT class_b
        prompt_a = (
            f"Generate 15 short first-person sentences (1-2 sentences each) that are clearly "
            f"{class_a.upper()} ({desc_a}) and NOT {class_b} ({desc_b}).\n"
            f"Context: ADHD university student.\n"
            f"Make them natural, varied, and clearly distinguishable from {class_b}.\n"
            f"Output ONLY the numbered sentences, nothing else."
        )

        # 15 sentences clearly class_b and NOT class_a
        prompt_b = (
            f"Generate 15 short first-person sentences (1-2 sentences each) that are clearly "
            f"{class_b.upper()} ({desc_b}) and NOT {class_a} ({desc_a}).\n"
            f"Context: ADHD university student.\n"
            f"Make them natural, varied, and clearly distinguishable from {class_a}.\n"
            f"Output ONLY the numbered sentences, nothing else."
        )

        print(f"  Generating boundary: {class_a} vs {class_b}...")
        raw_a = _call_claude(client, prompt_a)
        raw_b = _call_claude(client, prompt_b)

        sents_a = _parse_sentences(raw_a)
        sents_b = _parse_sentences(raw_b)

        print(f"    {class_a}: {len(sents_a)} sentences")
        print(f"    {class_b}: {len(sents_b)} sentences")

        for s in sents_a:
            all_sentences.append({"sentence": s, "label": class_a, "source": f"boundary_{class_a}_vs_{class_b}"})
        for s in sents_b:
            all_sentences.append({"sentence": s, "label": class_b, "source": f"boundary_{class_b}_vs_{class_a}"})

    return all_sentences


def generate_general_sentences(
    client: anthropic.Anthropic,
) -> list[dict[str, str]]:
    """Generate 15-20 general ADHD sentences per emotion class."""
    all_sentences: list[dict[str, str]] = []

    for label in LABELS:
        desc = LABEL_DESCRIPTIONS[label]
        prompt = (
            f"Generate 18 short first-person sentences (1-2 sentences each) expressing "
            f"{label.upper()} ({desc}).\n"
            f"Context: ADHD university student dealing with academic life, relationships, "
            f"medication, daily routines, and executive function challenges.\n"
            f"Make them natural, diverse in topic, and clearly {label}.\n"
            f"Output ONLY the numbered sentences, nothing else."
        )

        print(f"  Generating general: {label}...")
        raw = _call_claude(client, prompt)
        sents = _parse_sentences(raw)
        print(f"    {label}: {len(sents)} sentences")

        for s in sents:
            all_sentences.append({"sentence": s, "label": label, "source": f"general_{label}"})

    return all_sentences


def main() -> None:
    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        print("ERROR: CLAUDE_API_KEY environment variable not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("=" * 60)
    print("GENERATING BOUNDARY + GENERAL ADHD TRAINING SENTENCES")
    print("=" * 60)

    print("\n── Boundary Sentences ──")
    boundary = generate_boundary_sentences(client)

    print("\n── General Sentences ──")
    general = generate_general_sentences(client)

    all_generated = boundary + general

    # Summary
    from collections import Counter
    label_counts = Counter(s["label"] for s in all_generated)
    print(f"\n── Summary ──")
    print(f"Total generated: {len(all_generated)}")
    for label in LABELS:
        print(f"  {label}: {label_counts.get(label, 0)}")

    # Save for review
    with open(OUTPUT_PATH, "w") as f:
        json.dump(all_generated, f, indent=2)
    print(f"\nSaved to: {OUTPUT_PATH}")
    print("Review the sentences, then merge into emotion_training_data.json")


if __name__ == "__main__":
    main()
