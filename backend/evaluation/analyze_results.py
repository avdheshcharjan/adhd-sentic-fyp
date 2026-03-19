"""
Post-hoc analysis of evaluation data.

Computes:
1. Ablation comparison: response quality WITH vs WITHOUT SenticNet
2. Hourglass-to-ADHD correlation: SenticNet emotion dimensions vs ADHD subtype/severity
3. Per-persona intervention effectiveness summary
"""

import json
import os
import statistics
from collections import defaultdict


def load_all_persona_results(log_dir: str = "data/evaluation_logs/persona_runs") -> list[dict]:
    """Load all persona evaluation results."""
    results = []
    if not os.path.exists(log_dir):
        return results
    for filename in os.listdir(log_dir):
        if filename.endswith("_results.json"):
            with open(os.path.join(log_dir, filename)) as f:
                results.append(json.load(f))
    return results


def ablation_comparison(results: list[dict]) -> dict:
    """
    Compare response characteristics between SenticNet-enabled and disabled modes.

    Metrics:
    - Average response length (proxy for engagement depth)
    - Emotion-related word frequency in responses
    - Latency difference
    - Whether responses reference emotional state
    """
    EMOTION_WORDS = {
        "feel", "feeling", "frustrat", "overwhelm", "stress", "anxious",
        "worry", "hear you", "understand", "tough", "difficult", "hard",
        "emotion", "mood", "calm", "breath", "relax",
    }

    summary = {}
    for result in results:
        persona_id = result["persona"]["id"]
        persona_name = result["persona"]["name"]
        adhd_subtype = result["persona"]["adhd_subtype"]

        sentic_responses = [turn["app_response"] for turn in result["sentic_enabled"]]
        ablation_responses = [turn["app_response"] for turn in result["sentic_disabled"]]

        # Compare response lengths
        sentic_lengths = [len(r.get("response", "")) for r in sentic_responses]
        ablation_lengths = [len(r.get("response", "")) for r in ablation_responses]

        # Count emotion-word mentions
        def count_emotion_words(responses):
            count = 0
            for r in responses:
                text = r.get("response", "").lower()
                count += sum(1 for w in EMOTION_WORDS if w in text)
            return count

        # Average latency
        sentic_latencies = [r.get("latency_ms", 0) for r in sentic_responses]
        ablation_latencies = [r.get("latency_ms", 0) for r in ablation_responses]

        summary[persona_id] = {
            "persona_name": persona_name,
            "adhd_subtype": adhd_subtype,
            "avg_response_length_sentic": statistics.mean(sentic_lengths) if sentic_lengths else 0,
            "avg_response_length_ablation": statistics.mean(ablation_lengths) if ablation_lengths else 0,
            "emotion_word_count_sentic": count_emotion_words(sentic_responses),
            "emotion_word_count_ablation": count_emotion_words(ablation_responses),
            "avg_latency_ms_sentic": statistics.mean(sentic_latencies) if sentic_latencies else 0,
            "avg_latency_ms_ablation": statistics.mean(ablation_latencies) if ablation_latencies else 0,
        }

    return summary


def hourglass_adhd_correlation(log_dir: str = "data/evaluation_logs") -> dict:
    """
    Analyze correlation between SenticNet Hourglass dimensions and ADHD subtypes.

    Groups emotion dimension averages by ADHD subtype (Combined, Inattentive,
    Hyperactive-Impulsive) to see if different subtypes produce different
    emotional profiles in their messages.

    This produces NOVEL EMPIRICAL EVIDENCE for the Hourglass-to-ADHD mapping.
    """
    subtype_emotions = defaultdict(lambda: {
        "pleasantness": [],
        "attention": [],
        "sensitivity": [],
        "aptitude": [],
    })

    persona_results = load_all_persona_results(
        os.path.join(log_dir, "persona_runs")
    )
    for result in persona_results:
        subtype = result["persona"]["adhd_subtype"]
        for turn in result["sentic_enabled"]:
            resp = turn["app_response"]
            emotion = resp.get("emotion_context", {})
            if emotion:
                dim_map = {
                    "pleasantness": "hourglass_pleasantness",
                    "attention": "hourglass_attention",
                    "sensitivity": "hourglass_sensitivity",
                    "aptitude": "hourglass_aptitude",
                }
                for dim, key in dim_map.items():
                    val = emotion.get(key)
                    if val is not None:
                        subtype_emotions[subtype][dim].append(val)

    # Compute averages per subtype per dimension
    correlation_table = {}
    for subtype, dims in subtype_emotions.items():
        correlation_table[subtype] = {
            dim: {
                "mean": statistics.mean(vals) if vals else None,
                "stdev": statistics.stdev(vals) if len(vals) > 1 else None,
                "n": len(vals),
            }
            for dim, vals in dims.items()
        }

    return correlation_table


if __name__ == "__main__":
    print("=" * 60)
    print("ABLATION COMPARISON")
    print("=" * 60)
    results = load_all_persona_results()
    if results:
        ablation = ablation_comparison(results)
        print(json.dumps(ablation, indent=2))
    else:
        print("No persona results found. Run persona_runner.py first.")

    print("\n" + "=" * 60)
    print("HOURGLASS-TO-ADHD CORRELATION")
    print("=" * 60)
    correlation = hourglass_adhd_correlation()
    if correlation:
        print(json.dumps(correlation, indent=2, default=str))
    else:
        print("No correlation data found. Run persona_runner.py with SenticNet enabled first.")
