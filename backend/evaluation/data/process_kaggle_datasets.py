"""
Process Kaggle datasets for ADHD emotion DistilBERT training.

Step 1: Map Mental Health Sentiment dataset (53K) to 6 ADHD categories
Step 2: Sample + LLM-label Reddit ADHD posts with Claude API
Step 3: Combine all data sources into training JSON

Usage:
    # Step 1 only (no API needed):
    python3.11 -m evaluation.data.process_kaggle_datasets --step mental-health

    # Step 2 only (needs ANTHROPIC_API_KEY):
    python3.11 -m evaluation.data.process_kaggle_datasets --step reddit-adhd --api-key YOUR_KEY

    # Step 3: Combine everything:
    python3.11 -m evaluation.data.process_kaggle_datasets --step combine

    # All steps:
    python3.11 -m evaluation.data.process_kaggle_datasets --step all --api-key YOUR_KEY
"""

import argparse
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "evaluation" / "data"
KAGGLE_RAW = DATA_DIR / "kaggle_raw"

EMOTION_LABELS = ["joyful", "focused", "frustrated", "anxious", "disengaged", "overwhelmed"]

# ─── Label mapping: Mental Health Sentiment → ADHD emotions ───────────────
# Anxiety → anxious
# Stress → overwhelmed
# Depression → disengaged
# Normal → joyful OR focused (split randomly, since "Normal" = neutral/positive)
# Suicidal → skip (too extreme, not an ADHD emotion category)
# Bipolar → skip (diagnostic, not an emotion)
# Personality disorder → skip (diagnostic, not an emotion)
MH_LABEL_MAP = {
    "Anxiety": "anxious",
    "Stress": "overwhelmed",
    "Depression": "disengaged",
    "Normal": "joyful_or_focused",  # special handling
    # Skip: Suicidal, Bipolar, Personality disorder
}


def process_mental_health() -> list[dict]:
    """Map Mental Health Sentiment dataset to ADHD emotion labels."""
    csv_path = KAGGLE_RAW / "Combined Data.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Mental Health CSV not found at {csv_path}")

    df = pd.read_csv(csv_path)
    print(f"Loaded Mental Health dataset: {len(df)} rows")
    print(f"Original labels: {df['status'].value_counts().to_dict()}")

    results: list[dict] = []
    skipped = Counter()

    for _, row in df.iterrows():
        text = str(row["statement"]).strip()
        status = str(row["status"]).strip()

        # Skip empty/nan text
        if not text or text == "nan" or len(text) < 10:
            skipped["too_short"] += 1
            continue

        # Truncate very long texts (DistilBERT max is 512 tokens, ~128 tokens used)
        if len(text) > 500:
            text = text[:500]

        mapped = MH_LABEL_MAP.get(status)
        if mapped is None:
            skipped[status] += 1
            continue

        if mapped == "joyful_or_focused":
            # Split Normal into joyful and focused randomly
            label = random.choice(["joyful", "focused"])
        else:
            label = mapped

        results.append({"sentence": text, "label": label})

    print(f"\nMapped {len(results)} sentences")
    print(f"Skipped: {dict(skipped)}")
    print(f"Label distribution: {Counter(r['label'] for r in results)}")

    # Save intermediate
    out_path = DATA_DIR / "kaggle_mental_health_mapped.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved to {out_path}")

    return results


def sample_reddit_adhd(n_samples: int = 5000) -> list[str]:
    """Sample n_samples Reddit ADHD posts using reservoir sampling (memory efficient)."""
    # Reservoir sampling: read in chunks, keep a random sample of n_samples
    reservoir: list[str] = []
    total_seen = 0

    for csv_name in ["ADHD.csv", "adhdwomen.csv"]:
        csv_path = KAGGLE_RAW / csv_name
        if not csv_path.exists():
            print(f"  Skipping {csv_name} (not found)", flush=True)
            continue

        print(f"  Streaming {csv_name} in chunks...", flush=True)
        chunk_num = 0
        for chunk in pd.read_csv(
            csv_path,
            usecols=["title", "selftext"],
            dtype=str,
            chunksize=10000,
            on_bad_lines="skip",
        ):
            chunk_num += 1
            if chunk_num % 20 == 0:
                print(f"    Chunk {chunk_num} ({total_seen} rows seen, {len(reservoir)} in reservoir)", flush=True)

            for _, row in chunk.iterrows():
                title = str(row.get("title", "")).strip()
                selftext = str(row.get("selftext", "")).strip()

                if title in ("nan", "") and selftext in ("nan", ""):
                    continue

                # Combine title + selftext
                if selftext not in ("nan", "", "[removed]", "[deleted]"):
                    text = f"{title}. {selftext}" if title not in ("nan", "") else selftext
                else:
                    text = title

                if len(text) < 30:
                    continue
                if len(text) > 500:
                    text = text[:500]

                total_seen += 1
                # Reservoir sampling
                if len(reservoir) < n_samples:
                    reservoir.append(text)
                else:
                    j = random.randint(0, total_seen - 1)
                    if j < n_samples:
                        reservoir[j] = text

    print(f"  Total eligible posts seen: {total_seen}", flush=True)
    print(f"  Sampled: {len(reservoir)}", flush=True)
    return reservoir


def llm_label_batch(texts: list[str], api_key: str) -> list[dict]:
    """Use Claude API to label texts with ADHD emotions."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    results: list[dict] = []
    errors = 0

    system_prompt = """You are an ADHD emotion classifier. Given text from ADHD communities, classify the dominant emotion into EXACTLY ONE of these 6 categories:

- joyful: happiness, accomplishment, celebration, positive surprise, pride in managing ADHD
- focused: concentration, flow state, hyperfocus, productivity, being in the zone
- frustrated: anger, irritation, annoyance, setbacks, things not working, feeling stuck
- anxious: worry, nervousness, fear, dread, anticipatory stress, imposter syndrome
- disengaged: boredom, numbness, apathy, brain fog, inability to start, lack of motivation
- overwhelmed: too many tasks, sensory overload, emotional flooding, burnout, can't cope

Respond with ONLY the emotion label (one word, lowercase). Nothing else."""

    checkpoint_path = DATA_DIR / "kaggle_reddit_adhd_labeled_checkpoint.json"
    print(f"  Labeling {len(texts)} texts...", flush=True)

    for i, text in enumerate(texts):
        if (i + 1) % 100 == 0 or i == 0:
            print(f"  Progress: {i + 1}/{len(texts)} ({len(results)} labeled, {errors} errors)", flush=True)

        # Save checkpoint every 500
        if (i + 1) % 500 == 0 and results:
            with open(checkpoint_path, "w") as f:
                json.dump(results, f)
            print(f"  Checkpoint saved: {len(results)} results", flush=True)

        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=10,
                system=system_prompt,
                messages=[{"role": "user", "content": text}],
            )
            label = response.content[0].text.strip().lower()

            if label in EMOTION_LABELS:
                results.append({"sentence": text, "label": label})
            else:
                errors += 1
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  Error: {e}", flush=True)
            if errors == 50:
                print("  Too many errors, stopping.", flush=True)
                break

        # Rate limiting
        time.sleep(0.02)

    print(f"\n  Labeled: {len(results)}, Errors: {errors}", flush=True)
    print(f"  Distribution: {Counter(r['label'] for r in results)}", flush=True)

    # Clean up checkpoint
    if checkpoint_path.exists():
        checkpoint_path.unlink()

    return results


def label_reddit_adhd(api_key: str, n_samples: int = 5000) -> list[dict]:
    """Full pipeline: sample Reddit ADHD posts and label with Claude."""
    print("Sampling Reddit ADHD posts...")
    texts = sample_reddit_adhd(n_samples)

    print("\nLabeling with Claude API...")
    results = llm_label_batch(texts, api_key)

    # Save intermediate
    out_path = DATA_DIR / "kaggle_reddit_adhd_labeled.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved to {out_path}")

    return results


def combine_all() -> list[dict]:
    """Combine Mental Health mapped + Reddit ADHD labeled + ADHD base 210."""
    all_data: list[dict] = []

    # 1. Mental Health mapped
    mh_path = DATA_DIR / "kaggle_mental_health_mapped.json"
    if mh_path.exists():
        with open(mh_path) as f:
            mh_data = json.load(f)
        print(f"Mental Health mapped: {len(mh_data)}")
        all_data.extend(mh_data)
    else:
        print(f"WARNING: {mh_path} not found — run --step mental-health first")

    # 2. Reddit ADHD labeled
    reddit_path = DATA_DIR / "kaggle_reddit_adhd_labeled.json"
    if reddit_path.exists():
        with open(reddit_path) as f:
            reddit_data = json.load(f)
        print(f"Reddit ADHD labeled: {len(reddit_data)}")
        all_data.extend(reddit_data)
    else:
        print(f"WARNING: {reddit_path} not found — run --step reddit-adhd first")

    # 3. ADHD base 210 sentences
    base_path = DATA_DIR / "emotion_training_sentences.json"
    if base_path.exists():
        with open(base_path) as f:
            base_data = json.load(f)
        base_mapped = [{"sentence": d["sentence"], "label": d["label"]} for d in base_data]
        print(f"ADHD base sentences: {len(base_mapped)}")
        all_data.extend(base_mapped)

    print(f"\nTotal combined: {len(all_data)}")
    dist = Counter(d["label"] for d in all_data)
    print(f"Distribution: {dict(sorted(dist.items()))}")

    # Deduplicate by sentence text
    seen: set[str] = set()
    unique: list[dict] = []
    for d in all_data:
        key = d["sentence"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(d)

    print(f"After dedup: {len(unique)}")
    dist = Counter(d["label"] for d in unique)
    print(f"Distribution: {dict(sorted(dist.items()))}")

    # Keep all data (unbalanced) — use class weights in trainer instead
    balanced = unique[:]
    random.shuffle(balanced)
    print(f"\nFinal dataset (unbalanced, will use class weights): {len(balanced)}")
    print(f"Distribution: {Counter(d['label'] for d in balanced)}")

    # Save
    out_path = DATA_DIR / "kaggle_combined_training_data.json"
    with open(out_path, "w") as f:
        json.dump(balanced, f, indent=2)
    print(f"\nSaved to {out_path}")

    return balanced


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", choices=["mental-health", "reddit-adhd", "combine", "all"], required=True)
    parser.add_argument("--api-key", type=str, help="Anthropic API key for Reddit ADHD labeling")
    parser.add_argument("--n-samples", type=int, default=5000, help="Number of Reddit posts to sample")
    args = parser.parse_args()

    random.seed(42)

    if args.step in ("mental-health", "all"):
        print("=" * 70)
        print("STEP 1: PROCESS MENTAL HEALTH SENTIMENT DATASET")
        print("=" * 70)
        process_mental_health()

    if args.step in ("reddit-adhd", "all"):
        print("\n" + "=" * 70)
        print("STEP 2: SAMPLE + LLM-LABEL REDDIT ADHD POSTS")
        print("=" * 70)
        if not args.api_key:
            print("ERROR: --api-key required for Reddit ADHD labeling")
            sys.exit(1)
        label_reddit_adhd(args.api_key, args.n_samples)

    if args.step in ("combine", "all"):
        print("\n" + "=" * 70)
        print("STEP 3: COMBINE ALL DATASETS")
        print("=" * 70)
        combine_all()
