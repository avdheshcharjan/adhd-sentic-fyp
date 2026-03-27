"""
Collect and map multiple public emotion datasets to our 6 ADHD emotion categories.

Downloads from HuggingFace:
    1. dair-ai/emotion           (~416K samples, 6 labels)
    2. GoEmotions                (~58K samples, 27+1 labels)
    3. Empathetic Dialogues      (~25K conversations, 32 labels)
    4. SWMH                      (~54K Reddit mental health posts)
    5. SuperEmotion              (~520K samples, 7 labels)
    6. CrowdFlower/Emotion in Text (via tasksource, ~40K, 13 labels)
    7. DailyDialog               (~73K utterances, 7 labels)

Maps all labels to our 6 ADHD categories:
    joyful, focused, frustrated, anxious, disengaged, overwhelmed

Outputs a single JSON file: augmented_emotion_training_data.json

Usage:
    python -m evaluation.data.collect_emotion_datasets
    python -m evaluation.data.collect_emotion_datasets --max-per-class 2000
    python -m evaluation.data.collect_emotion_datasets --max-per-class 5000 --include-adhd-base
"""

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

OUTPUT_DIR = Path(__file__).parent
ADHD_BASE_PATH = OUTPUT_DIR / "emotion_training_data.json"

ADHD_LABELS = ["joyful", "focused", "frustrated", "anxious", "disengaged", "overwhelmed"]


# ── Label Mappings ─────────────────────────────────────────────────────

# dair-ai/emotion: sadness(0), joy(1), love(2), anger(3), fear(4), surprise(5)
DAIR_EMOTION_MAP: dict[int, str] = {
    0: "disengaged",     # sadness → apathy, withdrawal
    1: "joyful",         # joy
    2: "joyful",         # love
    3: "frustrated",     # anger
    4: "anxious",        # fear
    5: "focused",        # surprise → alertness, attention shift
}

# GoEmotions (27 labels) → our 6 ADHD categories
GOEMOTIONS_MAP: dict[str, str] = {
    "admiration": "joyful",
    "amusement": "joyful",
    "approval": "joyful",
    "caring": "joyful",
    "excitement": "joyful",
    "gratitude": "joyful",
    "joy": "joyful",
    "love": "joyful",
    "optimism": "joyful",
    "pride": "joyful",
    "relief": "joyful",
    "curiosity": "focused",
    "realization": "focused",
    "desire": "focused",
    "anger": "frustrated",
    "annoyance": "frustrated",
    "disapproval": "frustrated",
    "disgust": "frustrated",
    "disappointment": "frustrated",
    "embarrassment": "overwhelmed",
    "fear": "anxious",
    "nervousness": "anxious",
    "confusion": "anxious",
    "grief": "overwhelmed",
    "remorse": "overwhelmed",
    "sadness": "overwhelmed",
    "surprise": "focused",
    # "neutral" → skip
}

# Empathetic Dialogues (32 labels)
EMPDIAL_MAP: dict[str, str] = {
    "joyful": "joyful",
    "excited": "joyful",
    "content": "joyful",
    "grateful": "joyful",
    "proud": "joyful",
    "hopeful": "joyful",
    "caring": "joyful",
    "trusting": "joyful",
    "faithful": "joyful",
    "impressed": "joyful",
    "surprised": "focused",
    "confident": "focused",
    "prepared": "focused",
    "anticipating": "focused",
    "angry": "frustrated",
    "annoyed": "frustrated",
    "furious": "frustrated",
    "disappointed": "frustrated",
    "disgusted": "frustrated",
    "jealous": "frustrated",
    "anxious": "anxious",
    "apprehensive": "anxious",
    "afraid": "anxious",
    "terrified": "anxious",
    "lonely": "disengaged",
    "sad": "disengaged",
    "nostalgic": "disengaged",
    "sentimental": "disengaged",
    "devastated": "overwhelmed",
    "ashamed": "overwhelmed",
    "guilty": "overwhelmed",
    "embarrassed": "overwhelmed",
}

# CrowdFlower / Emotion in Text (13 labels)
CROWDFLOWER_MAP: dict[str, str] = {
    "happiness": "joyful",
    "fun": "joyful",
    "love": "joyful",
    "enthusiasm": "joyful",
    "relief": "joyful",
    "anger": "frustrated",
    "hate": "frustrated",
    "worry": "anxious",
    "boredom": "disengaged",
    "empty": "disengaged",
    "neutral": "disengaged",
    "sadness": "overwhelmed",
    "surprise": "focused",
}

# DailyDialog emotion labels (0-6)
DAILYDIALOG_MAP: dict[int, str | None] = {
    0: None,             # no emotion → skip (too many, dilutes quality)
    1: "frustrated",     # anger
    2: "frustrated",     # disgust
    3: "anxious",        # fear
    4: "joyful",         # happiness
    5: "overwhelmed",    # sadness
    6: "focused",        # surprise
}

# SWMH (Reddit mental health): subreddit-based labels
SWMH_MAP: dict[str, str] = {
    "anxiety": "anxious",
    "depression": "disengaged",
    "bipolar": "overwhelmed",
    "suicidewatch": "overwhelmed",
}

# SuperEmotion labels
SUPEREMOTION_MAP: dict[str, str] = {
    "joy": "joyful",
    "love": "joyful",
    "anger": "frustrated",
    "fear": "anxious",
    "sadness": "overwhelmed",
    "surprise": "focused",
    # "neutral" → skip
}


# ── Dataset Loaders ────────────────────────────────────────────────────

def load_dair_emotion() -> list[dict[str, str]]:
    """Load dair-ai/emotion dataset (~416K samples)."""
    print("  Loading dair-ai/emotion (unsplit = 416K)...")
    from datasets import load_dataset
    # The unsplit config has ~416K samples vs split's 16K
    try:
        ds = load_dataset("dair-ai/emotion", "unsplit", split="train")
    except Exception:
        ds = load_dataset("dair-ai/emotion", split="train")

    samples: list[dict[str, str]] = []
    for item in ds:
        mapped = DAIR_EMOTION_MAP.get(item["label"])
        if mapped:
            samples.append({"sentence": item["text"].strip(), "label": mapped})

    print(f"    → {len(samples)} samples loaded")
    return samples


def load_goemotions() -> list[dict[str, str]]:
    """Load GoEmotions dataset (~58K Reddit comments, 27 fine-grained labels)."""
    print("  Loading GoEmotions...")
    from datasets import load_dataset
    ds = load_dataset("google-research-datasets/go_emotions", "simplified", split="train")

    # GoEmotions simplified has integer label IDs
    # Need the label names
    label_names = ds.features["labels"].feature.names

    samples: list[dict[str, str]] = []
    for item in ds:
        text = item["text"].strip()
        if not text or len(text) < 10:
            continue
        # Item may have multiple labels; use the first mappable one
        for label_id in item["labels"]:
            label_name = label_names[label_id]
            mapped = GOEMOTIONS_MAP.get(label_name)
            if mapped:
                samples.append({"sentence": text, "label": mapped})
                break  # Only one label per text

    print(f"    → {len(samples)} samples loaded")
    return samples


def load_empathetic_dialogues() -> list[dict[str, str]]:
    """Load Empathetic Dialogues (~25K conversations, 32 emotion labels).

    The official facebook/empathetic_dialogues uses a deprecated loading script.
    Try alternative mirrors on HuggingFace first, then download CSV directly.
    """
    print("  Loading Empathetic Dialogues...")
    from datasets import load_dataset

    ds = None
    # Try alternative mirrors that have Parquet format
    alternatives = [
        "Nailab/empathetic_dialogues",
        "aseifert/empathetic_dialogues",
    ]
    for alt in alternatives:
        try:
            ds = load_dataset(alt, split="train")
            print(f"    Using mirror: {alt}")
            break
        except Exception:
            continue

    if ds is None:
        # Last resort: download CSV from Facebook's GitHub
        try:
            import urllib.request
            import csv
            import tempfile

            url = "https://dl.fbaipublicfiles.com/parlai/empatheticdialogues/empatheticdialogues.tar.gz"
            print("    Downloading from FB AI directly...")
            tmpdir = Path(tempfile.mkdtemp())
            tgz_path = tmpdir / "ed.tar.gz"
            urllib.request.urlretrieve(url, tgz_path)

            import tarfile
            with tarfile.open(tgz_path, "r:gz") as tar:
                tar.extractall(tmpdir)

            train_csv = tmpdir / "empatheticdialogues" / "train.csv"
            samples: list[dict[str, str]] = []
            seen_texts: set[str] = set()

            with open(train_csv, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    context = row.get("context", "").strip()
                    mapped = EMPDIAL_MAP.get(context)
                    if not mapped:
                        continue
                    text = row.get("utterance", "").strip().replace("_comma_", ",")
                    if not text or len(text) < 15 or text in seen_texts:
                        continue
                    seen_texts.add(text)
                    samples.append({"sentence": text, "label": mapped})

            print(f"    → {len(samples)} samples loaded (from CSV)")
            return samples
        except Exception as e:
            print(f"    ⚠ Empathetic Dialogues not available: {e}")
            return []

    # If we got a HuggingFace dataset
    samples = []
    seen_texts: set[str] = set()
    for item in ds:
        context = item.get("context", "").strip()
        mapped = EMPDIAL_MAP.get(context)
        if not mapped:
            continue
        text = item.get("utterance", "").strip()
        if not text or len(text) < 15 or text in seen_texts:
            continue
        text = text.replace("_comma_", ",")
        seen_texts.add(text)
        samples.append({"sentence": text, "label": mapped})

    print(f"    → {len(samples)} samples loaded")
    return samples


def load_swmh() -> list[dict[str, str]]:
    """Load SWMH Reddit mental health dataset (~54K posts)."""
    print("  Loading SWMH (Reddit Mental Health)...")
    from datasets import load_dataset
    try:
        ds = load_dataset("AIMH/SWMH", split="train")
    except Exception as e:
        print(f"    ⚠ SWMH not available: {e}")
        return []

    samples: list[dict[str, str]] = []
    for item in ds:
        text = item.get("text", "").strip()
        label_str = item.get("label")

        # SWMH uses integer labels: try mapping
        if isinstance(label_str, int):
            # Map: 0=normal, 1=depression, 2=anxiety, 3=bipolar, 4=suicidewatch
            int_map = {1: "disengaged", 2: "anxious", 3: "overwhelmed", 4: "overwhelmed"}
            mapped = int_map.get(label_str)
        elif isinstance(label_str, str):
            mapped = SWMH_MAP.get(label_str.lower())
        else:
            continue

        if not mapped or not text or len(text) < 20:
            continue

        # Truncate very long posts to first 512 chars
        if len(text) > 512:
            text = text[:512].rsplit(" ", 1)[0] + "..."

        samples.append({"sentence": text, "label": mapped})

    print(f"    → {len(samples)} samples loaded")
    return samples


def load_super_emotion() -> list[dict[str, str]]:
    """Load SuperEmotion dataset (~520K samples, unified from 6 datasets).

    Schema: text, labels (list[int]), labels_str (list[str]), labels_source, source
    labels_str values: Joy, Sadness, Anger, Fear, Love, Surprise, Neutral
    """
    print("  Loading SuperEmotion...")
    from datasets import load_dataset
    try:
        ds = load_dataset("cirimus/super-emotion", split="train")
    except Exception as e:
        print(f"    ⚠ SuperEmotion not available: {e}")
        return []

    samples: list[dict[str, str]] = []
    for item in ds:
        text = item.get("text", "").strip()
        if not text or len(text) < 10:
            continue

        # labels_str is a list of label strings (multilabel)
        labels_str = item.get("labels_str", [])
        if not labels_str:
            continue

        # Use the first mappable label
        for label_raw in labels_str:
            label = label_raw.lower().strip()
            mapped = SUPEREMOTION_MAP.get(label)
            if mapped:
                samples.append({"sentence": text, "label": mapped})
                break

    print(f"    → {len(samples)} samples loaded")
    return samples


def load_xed_english() -> list[dict[str, str]]:
    """Load XED English emotion dataset (~17K annotated sentences, Plutchik's 8 emotions).

    Unique value: has 'anticipation' label which maps well to 'focused'.
    Schema: sentence (str), labels (list[int]) where labels map to Plutchik's 8.
    """
    print("  Loading XED English (Plutchik's 8 emotions)...")
    from datasets import load_dataset

    # Plutchik label indices
    PLUTCHIK_LABELS = [
        "anger", "anticipation", "disgust", "fear",
        "joy", "sadness", "surprise", "trust",
    ]
    PLUTCHIK_MAP: dict[str, str] = {
        "anger": "frustrated",
        "anticipation": "focused",   # Best proxy for focused in any standard taxonomy
        "disgust": "frustrated",
        "fear": "anxious",
        "joy": "joyful",
        "sadness": "overwhelmed",
        "surprise": "focused",
        "trust": "joyful",
    }

    try:
        ds = load_dataset("Helsinki-NLP/xed_en_fi", "en_annotated", split="train")
    except Exception:
        try:
            ds = load_dataset("Helsinki-NLP/xed_en_fi", split="train")
        except Exception as e:
            print(f"    ⚠ XED not available: {e}")
            return []

    samples: list[dict[str, str]] = []
    for item in ds:
        text = item.get("sentence", "").strip()
        if not text or len(text) < 10:
            continue

        labels = item.get("labels", [])
        if not labels:
            continue

        # Use first mappable label
        for label_id in labels:
            if 0 <= label_id < len(PLUTCHIK_LABELS):
                label_name = PLUTCHIK_LABELS[label_id]
                mapped = PLUTCHIK_MAP.get(label_name)
                if mapped:
                    samples.append({"sentence": text, "label": mapped})
                    break

    print(f"    → {len(samples)} samples loaded")
    return samples


def load_dailydialog() -> list[dict[str, str]]:
    """Load DailyDialog dataset (~87K utterances).

    Uses benjaminbeilharz/better_daily_dialog which has a flat Parquet format
    (the original li2017dailydialog uses a deprecated loading script).
    Schema: dialog_id, utterance, turn_type, emotion (int 0-6)
    """
    print("  Loading DailyDialog (better_daily_dialog)...")
    from datasets import load_dataset
    try:
        ds = load_dataset("benjaminbeilharz/better_daily_dialog", split="train")
    except Exception as e:
        print(f"    ⚠ DailyDialog not available: {e}")
        return []

    samples: list[dict[str, str]] = []
    for item in ds:
        text = item.get("utterance", "").strip()
        emotion_id = item.get("emotion", 0)
        mapped = DAILYDIALOG_MAP.get(emotion_id)
        if mapped and text and len(text) >= 15:
            samples.append({"sentence": text, "label": mapped})

    print(f"    → {len(samples)} samples loaded (non-neutral only)")
    return samples


# ── Main Pipeline ──────────────────────────────────────────────────────

def collect_all_datasets(
    max_per_class: int = 3000,
    include_adhd_base: bool = True,
    seed: int = 42,
) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Download and collect all datasets, balance classes.

    Args:
        max_per_class: Maximum samples per ADHD emotion category.
        include_adhd_base: Whether to include our 210 ADHD base training sentences.
        seed: Random seed for reproducibility.

    Returns:
        (samples, class_counts) tuple.
    """
    rng = random.Random(seed)
    all_samples: list[dict[str, str]] = []

    # Load our base ADHD training data first (highest priority)
    if include_adhd_base and ADHD_BASE_PATH.exists():
        print("\n Loading base ADHD training data...")
        with open(ADHD_BASE_PATH) as f:
            adhd_base = json.load(f)
        all_samples.extend(adhd_base)
        print(f"    → {len(adhd_base)} ADHD base samples")

    # Load each external dataset
    print("\n Downloading external datasets from HuggingFace...\n")

    loaders = [
        ("dair-ai/emotion", load_dair_emotion),
        ("GoEmotions", load_goemotions),
        ("Empathetic Dialogues", load_empathetic_dialogues),
        ("SWMH", load_swmh),
        ("SuperEmotion", load_super_emotion),
        ("XED English", load_xed_english),
        ("DailyDialog", load_dailydialog),
    ]

    dataset_stats: dict[str, int] = {}

    for name, loader_fn in loaders:
        try:
            samples = loader_fn()
            dataset_stats[name] = len(samples)
            all_samples.extend(samples)
        except Exception as e:
            print(f"    ⚠ Failed to load {name}: {e}")
            dataset_stats[name] = 0

    # Deduplicate by normalized sentence text
    print(f"\n Total raw samples: {len(all_samples)}")
    seen: set[str] = set()
    unique_samples: list[dict[str, str]] = []
    for s in all_samples:
        key = s["sentence"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique_samples.append(s)

    print(f"  After dedup: {len(unique_samples)}")

    # Count per class before balancing
    class_counts_raw = Counter(s["label"] for s in unique_samples)
    print(f"\n  Raw class distribution:")
    for label in ADHD_LABELS:
        print(f"    {label:>15s}: {class_counts_raw.get(label, 0):>6d}")

    # Balance: cap each class at max_per_class
    class_buckets: dict[str, list[dict[str, str]]] = {label: [] for label in ADHD_LABELS}
    for s in unique_samples:
        if s["label"] in class_buckets:
            class_buckets[s["label"]].append(s)

    balanced: list[dict[str, str]] = []
    for label in ADHD_LABELS:
        bucket = class_buckets[label]
        rng.shuffle(bucket)
        selected = bucket[:max_per_class]
        balanced.extend(selected)

    rng.shuffle(balanced)

    class_counts_final = Counter(s["label"] for s in balanced)
    print(f"\n  Balanced class distribution (max {max_per_class}/class):")
    for label in ADHD_LABELS:
        print(f"    {label:>15s}: {class_counts_final.get(label, 0):>6d}")

    print(f"\n  Final dataset size: {len(balanced)}")
    print(f"\n  Dataset source stats:")
    for name, count in dataset_stats.items():
        print(f"    {name:>25s}: {count:>6d} samples")

    return balanced, dict(class_counts_final)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect and map external emotion datasets to ADHD categories"
    )
    parser.add_argument(
        "--max-per-class",
        type=int,
        default=3000,
        help="Maximum samples per emotion class (default: 3000)",
    )
    parser.add_argument(
        "--include-adhd-base",
        action="store_true",
        default=True,
        help="Include our 210 base ADHD training sentences (default: True)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: augmented_emotion_training_data.json)",
    )
    args = parser.parse_args()

    samples, class_counts = collect_all_datasets(
        max_per_class=args.max_per_class,
        include_adhd_base=args.include_adhd_base,
    )

    output_path = Path(args.output) if args.output else OUTPUT_DIR / "augmented_emotion_training_data.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(samples, f, indent=2)

    print(f"\n Saved {len(samples)} samples to {output_path}")
    print(f"  Class counts: {class_counts}")
    print(f"\n  To train DistilBERT with this data:")
    print(f"    python -m evaluation.accuracy.train_and_eval_finetune_augmented")


if __name__ == "__main__":
    main()
