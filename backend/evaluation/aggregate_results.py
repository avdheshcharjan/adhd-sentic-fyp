"""
Aggregate all evaluation results into a single summary.

Reads JSON files from evaluation/results/ and produces:
1. Formatted console summary
2. JSON summary: evaluation/results/summary_{timestamp}.json
3. Markdown summary: evaluation/results/summary_{timestamp}.md
   (structured to paste into FYP report Chapter 5)

Usage:
    python -m evaluation.aggregate_results
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"


def _load_latest(prefix: str) -> dict | None:
    """Load the latest JSON file matching a prefix from results/."""
    matches = sorted(
        [f for f in os.listdir(RESULTS_DIR) if f.startswith(prefix) and f.endswith(".json")],
        reverse=True,
    )
    if not matches:
        return None
    path = RESULTS_DIR / matches[0]
    with open(path) as f:
        data = json.load(f)
    data["_source_file"] = matches[0]
    return data


def _safe_get(data: dict | None, *keys, default="N/A"):
    """Safely traverse nested dict keys."""
    if data is None:
        return default
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


def _fmt(val, fmt_str=".1f", default="N/A") -> str:
    """Format a numeric value or return default."""
    if val is None or val == "N/A":
        return default
    try:
        return f"{float(val):{fmt_str}}"
    except (ValueError, TypeError):
        return default


# ── Data Collectors ───────────────────────────────────────────────


def _collect_llm_metrics(llm: dict | None) -> dict:
    """Extract LLM benchmark metrics."""
    if llm is None:
        return {}
    m = llm.get("metrics", {})
    return {
        "cold_start_mean_s": _safe_get(m, "cold_start", "mean_s"),
        "cold_start_stdev_s": _safe_get(m, "cold_start", "stdev_s"),
        "gen_short_mean_ms": _safe_get(m, "generation_time", "short", "mean_ms"),
        "gen_medium_mean_ms": _safe_get(m, "generation_time", "medium", "mean_ms"),
        "gen_long_mean_ms": _safe_get(m, "generation_time", "long", "mean_ms"),
        "gen_short_p95_ms": _safe_get(m, "generation_time", "short", "p95_ms"),
        "throughput_short_tok_s": _safe_get(m, "throughput", "short", "mean_tok_s"),
        "throughput_medium_tok_s": _safe_get(m, "throughput", "medium", "mean_tok_s"),
        "throughput_long_tok_s": _safe_get(m, "throughput", "long", "mean_tok_s"),
        "memory_with_model_mb": _safe_get(m, "memory", "rss_with_model_mb"),
        "memory_peak_generation_mb": _safe_get(m, "memory", "rss_peak_generation_mb"),
        "memory_after_unload_mb": _safe_get(m, "memory", "rss_after_unload_mb"),
        "model_footprint_mb": _safe_get(m, "memory", "model_footprint_mb"),
        "think_mean_ms": _safe_get(m, "thinking_mode", "think", "mean_ms"),
        "no_think_mean_ms": _safe_get(m, "thinking_mode", "no_think", "mean_ms"),
    }


def _collect_classification_metrics(clf: dict | None) -> dict:
    """Extract classification benchmark metrics."""
    if clf is None:
        return {}
    m = clf.get("metrics", {})
    result = {}
    # Tier coverage
    coverage = m.get("tier_coverage", {})
    for tier_name, tier_data in coverage.items():
        if isinstance(tier_data, dict) and "pct" in tier_data:
            result[f"coverage_{tier_name}_pct"] = tier_data["pct"]
    result["rules_total_pct"] = _safe_get(coverage, "rules_total_pct")
    # Per-tier latency
    for tier in ["tier_1", "tier_3", "tier_4"]:
        result[f"latency_{tier}_mean_ms"] = _safe_get(m, "per_tier_latency", tier, "mean_ms")
        result[f"latency_{tier}_p95_ms"] = _safe_get(m, "per_tier_latency", tier, "p95_ms")
    # Embedding memory
    result["embedding_memory_delta_mb"] = _safe_get(m, "embedding_memory", "delta_mb")
    return result


def _collect_senticnet_bench_metrics(sn: dict | None) -> dict:
    """Extract SenticNet benchmark metrics."""
    if sn is None:
        return {}
    m = sn.get("metrics", {})
    return {
        "single_lookup_mean_ms": _safe_get(m, "single_lookup_latency", "mean_ms"),
        "single_lookup_p95_ms": _safe_get(m, "single_lookup_latency", "p95_ms"),
        "single_lookup_p99_ms": _safe_get(m, "single_lookup_latency", "p99_ms"),
        "api_success_rate_pct": _safe_get(m, "api_reliability", "success_rate_pct"),
        "pipeline_10w_mean_ms": _safe_get(m, "pipeline_latency_by_length", "10_words", "mean_ms"),
        "pipeline_50w_mean_ms": _safe_get(m, "pipeline_latency_by_length", "50_words", "mean_ms"),
        "pipeline_100w_mean_ms": _safe_get(m, "pipeline_latency_by_length", "100_words", "mean_ms"),
        "pipeline_200w_mean_ms": _safe_get(m, "pipeline_latency_by_length", "200_words", "mean_ms"),
    }


def _collect_memory_bench_metrics(mem: dict | None) -> dict:
    """Extract memory benchmark metrics."""
    if mem is None:
        return {}
    m = mem.get("metrics", {})
    return {
        "store_mean_ms": _safe_get(m, "store_latency", "mean_ms"),
        "store_p95_ms": _safe_get(m, "store_latency", "p95_ms"),
        "retrieval_mean_ms": _safe_get(m, "retrieval_latency", "mean_ms"),
        "retrieval_p95_ms": _safe_get(m, "retrieval_latency", "p95_ms"),
        "retrieval_hit_rate_pct": _safe_get(m, "retrieval_relevance", "hit_rate_pct"),
        "memory_rss_mb": _safe_get(m, "memory_footprint", "rss_mb"),
    }


def _collect_pipeline_metrics(pipe: dict | None) -> dict:
    """Extract end-to-end pipeline metrics."""
    if pipe is None:
        return {}
    m = pipe.get("metrics", {})
    avg = _safe_get(m, "latency_waterfall", "averages", default={})
    result = {}
    for stage in ["senticnet_analysis_ms", "safety_check_ms", "memory_retrieval_ms",
                   "prompt_assembly_ms", "llm_generation_ms", "memory_store_ms", "total_ms"]:
        stage_data = avg.get(stage, {}) if isinstance(avg, dict) else {}
        result[f"pipe_{stage}_mean"] = stage_data.get("mean", "N/A") if isinstance(stage_data, dict) else "N/A"
        result[f"pipe_{stage}_median"] = stage_data.get("median", "N/A") if isinstance(stage_data, dict) else "N/A"
    result["pipe_bottleneck"] = _safe_get(m, "latency_waterfall", "bottleneck")
    result["warm_mean_ms"] = _safe_get(m, "warm_vs_cold", "warm_mean_ms")
    result["cold_first_ms"] = _safe_get(m, "warm_vs_cold", "estimated_cold_first_ms")
    result["full_pipeline_mean_ms"] = _safe_get(m, "ablation_timing", "full_pipeline_mean_ms")
    result["ablation_mean_ms"] = _safe_get(m, "ablation_timing", "ablation_mean_ms")
    result["senticnet_cost_pct"] = _safe_get(m, "ablation_timing", "senticnet_cost_pct")
    result["peak_cpu_pct"] = _safe_get(m, "burst_resources", "peak_cpu_pct")
    result["peak_rss_mb"] = _safe_get(m, "burst_resources", "peak_rss_mb")
    return result


def _collect_energy_metrics(energy: dict | None) -> dict:
    """Extract energy benchmark metrics."""
    if energy is None:
        return {}
    m = energy.get("metrics", {})
    return {
        "idle_watts": _safe_get(m, "idle_power", "estimated_watts"),
        "energy_per_inference_mean_mj": _safe_get(m, "energy_per_inference", "total_mj", "mean"),
        "energy_per_inference_median_mj": _safe_get(m, "energy_per_inference", "total_mj", "median"),
        "battery_active_hours": _safe_get(m, "battery_estimate", "active_coaching", "estimated_battery_hours"),
        "battery_casual_hours": _safe_get(m, "battery_estimate", "casual_use", "estimated_battery_hours"),
        "battery_capacity_wh": _safe_get(m, "battery_estimate", "battery_capacity_wh"),
    }


def _collect_classification_accuracy(clf_acc: dict | None) -> dict:
    """Extract classification accuracy metrics."""
    if clf_acc is None:
        return {}
    gm = clf_acc.get("granular_category_metrics", {})
    result = {
        "clf_accuracy": _safe_get(gm, "accuracy"),
        "clf_macro_f1": _safe_get(gm, "macro_f1"),
        "clf_weighted_f1": _safe_get(gm, "weighted_f1"),
    }
    # Per-class F1
    per_class = gm.get("per_class_report", {})
    for cls_name, cls_data in per_class.items():
        if isinstance(cls_data, dict) and "f1-score" in cls_data:
            result[f"clf_f1_{cls_name}"] = cls_data["f1-score"]
    return result


def _collect_coaching_quality(coaching: dict | None) -> dict:
    """Extract coaching quality metrics."""
    if coaching is None:
        return {}
    m = coaching.get("metrics", {})
    dm = m.get("dimension_metrics", {})
    result = {}
    for dim in ["empathy", "helpfulness", "adhd_appropriateness", "coherence", "informativeness"]:
        dim_data = dm.get(dim, {})
        result[f"coaching_{dim}_with_mean"] = _safe_get(dim_data, "with_sentic_mean")
        result[f"coaching_{dim}_with_std"] = _safe_get(dim_data, "with_sentic_std")
        result[f"coaching_{dim}_without_mean"] = _safe_get(dim_data, "without_sentic_mean")
        result[f"coaching_{dim}_without_std"] = _safe_get(dim_data, "without_sentic_std")
        result[f"coaching_{dim}_p"] = _safe_get(dim_data, "wilcoxon_p")
        result[f"coaching_{dim}_significant"] = _safe_get(dim_data, "significant")

    comp = m.get("comparison_metrics", {})
    result["coaching_wins"] = _safe_get(comp, "wins")
    result["coaching_ties"] = _safe_get(comp, "ties")
    result["coaching_losses"] = _safe_get(comp, "losses")
    result["coaching_total"] = _safe_get(comp, "total")
    result["coaching_win_rate"] = _safe_get(comp, "win_rate")

    safety = m.get("safety_metrics", {})
    result["coaching_safety_with_rate"] = _safe_get(safety, "with_sentic_pass_rate")
    result["coaching_safety_without_rate"] = _safe_get(safety, "without_sentic_pass_rate")
    return result


def _collect_senticnet_accuracy(sn_acc: dict | None) -> dict:
    """Extract SenticNet emotion detection accuracy."""
    if sn_acc is None:
        return {}
    ec = sn_acc.get("emotion_classification", {})
    result = {
        "sentic_accuracy": _safe_get(ec, "accuracy"),
        "sentic_macro_f1": _safe_get(ec, "macro_f1"),
        "sentic_weighted_f1": _safe_get(ec, "weighted_f1"),
    }
    per_class = ec.get("per_class_report", {})
    for cls_name, cls_data in per_class.items():
        if isinstance(cls_data, dict) and "f1-score" in cls_data:
            result[f"sentic_f1_{cls_name}"] = cls_data["f1-score"]
    return result


def _collect_memory_retrieval(mem_ret: dict | None) -> dict:
    """Extract memory retrieval accuracy."""
    if mem_ret is None:
        return {}
    am = mem_ret.get("aggregate_metrics", {})
    return {
        "mem_hit_at_1": _safe_get(am, "hit_at_1"),
        "mem_hit_at_3": _safe_get(am, "hit_at_3"),
        "mem_hit_at_5": _safe_get(am, "hit_at_5"),
        "mem_ndcg_at_3": _safe_get(am, "ndcg_at_3"),
        "mem_mean_latency_ms": _safe_get(am, "mean_latency_ms"),
        "mem_p95_latency_ms": _safe_get(am, "p95_latency_ms"),
    }


def _collect_emotion_comparison(comp: dict | None) -> dict:
    """Extract emotion classifier comparison report."""
    if comp is None:
        return {}
    result = {
        "baseline_accuracy": _safe_get(comp, "baseline", "senticnet_word_level", "accuracy"),
    }
    approaches = comp.get("approaches", {})
    for key, approach_data in approaches.items():
        if isinstance(approach_data, dict):
            result[f"approach_{key}_accuracy"] = _safe_get(approach_data, "accuracy")
            result[f"approach_{key}_macro_f1"] = _safe_get(approach_data, "macro_f1")
    ranking = comp.get("ranking", [])
    for entry in ranking:
        result[f"rank_{entry.get('rank', '?')}_approach"] = entry.get("approach", "")
        result[f"rank_{entry.get('rank', '?')}_accuracy"] = entry.get("accuracy", 0)
    result["winner"] = _safe_get(comp, "recommendation", "winner")
    return result


# ── Console Output ────────────────────────────────────────────────


def _print_summary(summary: dict) -> str:
    """Print formatted console summary and return the text."""
    llm = summary.get("llm", {})
    clf = summary.get("classification_bench", {})
    sn = summary.get("senticnet_bench", {})
    mem = summary.get("memory_bench", {})
    pipe = summary.get("pipeline", {})
    energy = summary.get("energy", {})
    clf_acc = summary.get("classification_accuracy", {})
    coaching = summary.get("coaching_quality", {})
    sn_acc = summary.get("senticnet_accuracy", {})
    mem_ret = summary.get("memory_retrieval", {})
    emo_comp = summary.get("emotion_comparison", {})

    lines = []
    def p(text=""):
        lines.append(text)
        print(text)

    p("=" * 64)
    p("  ADHD Second Brain Pipeline — Evaluation Summary")
    p(f"  Date: {summary.get('date', 'N/A')} | Hardware: {summary.get('hardware', 'N/A')}")
    p("=" * 64)
    p()

    # System Performance
    p("SYSTEM PERFORMANCE")
    p("─" * 54)
    p(f"  LLM cold start:          {_fmt(llm.get('cold_start_mean_s'))}s ± {_fmt(llm.get('cold_start_stdev_s'))}s")
    p(f"  LLM gen (short):         {_fmt(llm.get('gen_short_mean_ms'), '.0f')}ms (p95: {_fmt(llm.get('gen_short_p95_ms'), '.0f')}ms)")
    p(f"  LLM gen (medium):        {_fmt(llm.get('gen_medium_mean_ms'), '.0f')}ms")
    p(f"  LLM gen (long):          {_fmt(llm.get('gen_long_mean_ms'), '.0f')}ms")
    p(f"  LLM throughput (short):  {_fmt(llm.get('throughput_short_tok_s'))} tok/s")
    p(f"  LLM throughput (medium): {_fmt(llm.get('throughput_medium_tok_s'))} tok/s")
    p(f"  LLM throughput (long):   {_fmt(llm.get('throughput_long_tok_s'))} tok/s")
    p(f"  LLM peak memory:         {_fmt(llm.get('memory_peak_generation_mb'), '.0f')}MB")
    p(f"  LLM model footprint:     {_fmt(llm.get('model_footprint_mb'), '.0f')}MB")
    p(f"  Think mode mean:         {_fmt(llm.get('think_mean_ms'), '.0f')}ms")
    p(f"  No-think mode mean:      {_fmt(llm.get('no_think_mean_ms'), '.0f')}ms")
    p()
    p(f"  Classification (T1):     {_fmt(clf.get('latency_tier_1_mean_ms'))}ms (p95: {_fmt(clf.get('latency_tier_1_p95_ms'))}ms)")
    p(f"  Classification (T4):     {_fmt(clf.get('latency_tier_4_mean_ms'))}ms (p95: {_fmt(clf.get('latency_tier_4_p95_ms'))}ms)")
    p(f"  Rules coverage:          {_fmt(clf.get('rules_total_pct'))}%")
    p(f"  Embedding memory delta:  {_fmt(clf.get('embedding_memory_delta_mb'))}MB")
    p()
    p(f"  SenticNet single:        {_fmt(sn.get('single_lookup_mean_ms'), '.0f')}ms (p95: {_fmt(sn.get('single_lookup_p95_ms'), '.0f')}ms)")
    p(f"  SenticNet API success:   {_fmt(sn.get('api_success_rate_pct'))}%")
    p(f"  SenticNet (10 words):    {_fmt(sn.get('pipeline_10w_mean_ms'), '.0f')}ms")
    p(f"  SenticNet (50 words):    {_fmt(sn.get('pipeline_50w_mean_ms'), '.0f')}ms")
    p()
    p(f"  Mem0 store:              {_fmt(mem.get('store_mean_ms'), '.0f')}ms (p95: {_fmt(mem.get('store_p95_ms'), '.0f')}ms)")
    p(f"  Mem0 retrieval:          {_fmt(mem.get('retrieval_mean_ms'), '.0f')}ms (p95: {_fmt(mem.get('retrieval_p95_ms'), '.0f')}ms)")
    p(f"  Mem0 hit rate:           {_fmt(mem.get('retrieval_hit_rate_pct'))}%")
    p()
    p(f"  Pipeline total (warm):   {_fmt(pipe.get('warm_mean_ms'), '.0f')}ms")
    p(f"  Pipeline total (cold):   {_fmt(pipe.get('cold_first_ms'), '.0f')}ms")
    p(f"  Pipeline full mean:      {_fmt(pipe.get('full_pipeline_mean_ms'), '.0f')}ms")
    p(f"  Pipeline ablation mean:  {_fmt(pipe.get('ablation_mean_ms'), '.0f')}ms")
    p(f"  SenticNet cost:          {_fmt(pipe.get('senticnet_cost_pct'))}%")
    p(f"  Pipeline bottleneck:     {pipe.get('pipe_bottleneck', 'N/A')}")
    p(f"  Peak CPU:                {_fmt(pipe.get('peak_cpu_pct'))}%")
    p(f"  Peak RSS:                {_fmt(pipe.get('peak_rss_mb'), '.0f')}MB")
    p()

    # Energy
    if energy:
        p("ENERGY & BATTERY")
        p("─" * 54)
        p(f"  Idle power:              {_fmt(energy.get('idle_watts'))}W")
        p(f"  Energy per inference:     {_fmt(energy.get('energy_per_inference_mean_mj'), '.0f')}mJ (mean)")
        p(f"  Battery (active coach):  {_fmt(energy.get('battery_active_hours'))} hours")
        p(f"  Battery (casual use):    {_fmt(energy.get('battery_casual_hours'))} hours")
        p(f"  Battery capacity:        {_fmt(energy.get('battery_capacity_wh'))}Wh")
        p()

    # ML Accuracy
    p("ML ACCURACY")
    p("─" * 54)

    # Classification
    p(f"  Classification accuracy: {_fmt(clf_acc.get('clf_accuracy'), '.3f')}")
    p(f"  Classification macro-F1: {_fmt(clf_acc.get('clf_macro_f1'), '.3f')}")
    for key, val in clf_acc.items():
        if key.startswith("clf_f1_") and key not in ("clf_f1_macro avg", "clf_f1_weighted avg"):
            class_name = key.replace("clf_f1_", "")
            p(f"    {class_name:20s} F1={_fmt(val, '.2f')}")
    p()

    # Coaching Quality
    p("  Coaching quality (1-5):")
    for dim in ["empathy", "helpfulness", "adhd_appropriateness", "coherence", "informativeness"]:
        with_mean = coaching.get(f"coaching_{dim}_with_mean", "N/A")
        with_std = coaching.get(f"coaching_{dim}_with_std", "N/A")
        without_mean = coaching.get(f"coaching_{dim}_without_mean", "N/A")
        p_val = coaching.get(f"coaching_{dim}_p", "N/A")
        sig = coaching.get(f"coaching_{dim}_significant", "N/A")
        p(f"    {dim:25s} with={_fmt(with_mean, '.2f')} ± {_fmt(with_std, '.2f')}  without={_fmt(without_mean, '.2f')}  p={_fmt(p_val, '.4f')}  sig={sig}")
    p()
    wins = coaching.get("coaching_wins", "N/A")
    ties = coaching.get("coaching_ties", "N/A")
    losses = coaching.get("coaching_losses", "N/A")
    total = coaching.get("coaching_total", "N/A")
    win_rate = coaching.get("coaching_win_rate", "N/A")
    p(f"  SenticNet ablation (win/tie/loss): {wins}/{ties}/{losses} of {total}  win rate={_fmt(win_rate, '.1f')}%")
    p(f"  Safety pass rate (with):    {_fmt(coaching.get('coaching_safety_with_rate'), '.1f')}%")
    p(f"  Safety pass rate (without): {_fmt(coaching.get('coaching_safety_without_rate'), '.1f')}%")
    p()

    # Emotion detection
    p(f"  SenticNet emotion accuracy: {_fmt(sn_acc.get('sentic_accuracy'), '.3f')}")
    p(f"  SenticNet emotion macro-F1: {_fmt(sn_acc.get('sentic_macro_f1'), '.3f')}")
    for key, val in sn_acc.items():
        if key.startswith("sentic_f1_"):
            class_name = key.replace("sentic_f1_", "")
            p(f"    {class_name:20s} F1={_fmt(val, '.2f')}")
    p()

    # Emotion classifier comparison
    if emo_comp:
        p("  Emotion classifier comparison:")
        p(f"    Baseline (SenticNet):  {_fmt(emo_comp.get('baseline_accuracy'), '.2f')}")
        for i in range(1, 9):
            approach = emo_comp.get(f"rank_{i}_approach", "")
            acc = emo_comp.get(f"rank_{i}_accuracy", "")
            if approach:
                p(f"    #{i}: {approach:45s} acc={_fmt(acc, '.2f')}")
        p(f"    Winner: {emo_comp.get('winner', 'N/A')}")
        p()

    # Memory retrieval
    p(f"  Memory retrieval:")
    p(f"    Hit@1:      {_fmt(mem_ret.get('mem_hit_at_1'), '.2f')}")
    p(f"    Hit@3:      {_fmt(mem_ret.get('mem_hit_at_3'), '.2f')}")
    p(f"    Hit@5:      {_fmt(mem_ret.get('mem_hit_at_5'), '.2f')}")
    p(f"    nDCG@3:     {_fmt(mem_ret.get('mem_ndcg_at_3'), '.3f')}")
    p(f"    Latency:    {_fmt(mem_ret.get('mem_mean_latency_ms'), '.0f')}ms (p95: {_fmt(mem_ret.get('mem_p95_latency_ms'), '.0f')}ms)")
    p()

    p("=" * 64)
    return "\n".join(lines)


# ── Markdown Output ───────────────────────────────────────────────


def _generate_markdown(summary: dict) -> str:
    """Generate FYP Chapter 5 compatible markdown."""
    llm = summary.get("llm", {})
    clf = summary.get("classification_bench", {})
    sn = summary.get("senticnet_bench", {})
    mem = summary.get("memory_bench", {})
    pipe = summary.get("pipeline", {})
    energy = summary.get("energy", {})
    clf_acc = summary.get("classification_accuracy", {})
    coaching = summary.get("coaching_quality", {})
    sn_acc = summary.get("senticnet_accuracy", {})
    mem_ret = summary.get("memory_retrieval", {})
    emo_comp = summary.get("emotion_comparison", {})

    md = []

    md.append(f"---")
    md.append(f"title: \"ADHD Second Brain — Evaluation Results Summary\"")
    md.append(f"date: {summary.get('date', 'N/A')}")
    md.append(f"hardware: {summary.get('hardware', 'N/A')}")
    md.append(f"---")
    md.append("")
    md.append("# Evaluation Results Summary")
    md.append("")
    md.append(f"Generated: {summary.get('date', 'N/A')}")
    md.append(f"Hardware: {summary.get('hardware', 'N/A')}")
    md.append("")

    # 5.3 LLM Performance
    md.append("## 5.3 LLM Performance Evaluation")
    md.append("")
    md.append("### Cold Start")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Cold start (mean) | {_fmt(llm.get('cold_start_mean_s'))}s ± {_fmt(llm.get('cold_start_stdev_s'))}s |")
    md.append("")
    md.append("### Generation Time by Prompt Length")
    md.append("")
    md.append("| Prompt Length | Mean (ms) | P95 (ms) | Throughput (tok/s) |")
    md.append("|-------------|-----------|---------|-------------------|")
    md.append(f"| Short | {_fmt(llm.get('gen_short_mean_ms'), '.0f')} | {_fmt(llm.get('gen_short_p95_ms'), '.0f')} | {_fmt(llm.get('throughput_short_tok_s'))} |")
    md.append(f"| Medium | {_fmt(llm.get('gen_medium_mean_ms'), '.0f')} | N/A | {_fmt(llm.get('throughput_medium_tok_s'))} |")
    md.append(f"| Long | {_fmt(llm.get('gen_long_mean_ms'), '.0f')} | N/A | {_fmt(llm.get('throughput_long_tok_s'))} |")
    md.append("")
    md.append("### Memory Usage")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| With model loaded | {_fmt(llm.get('memory_with_model_mb'), '.0f')} MB |")
    md.append(f"| Peak during generation | {_fmt(llm.get('memory_peak_generation_mb'), '.0f')} MB |")
    md.append(f"| After unload | {_fmt(llm.get('memory_after_unload_mb'), '.0f')} MB |")
    md.append(f"| Model footprint | {_fmt(llm.get('model_footprint_mb'), '.0f')} MB |")
    md.append("")
    md.append("### Thinking Mode Comparison")
    md.append("")
    md.append("| Mode | Mean Latency (ms) |")
    md.append("|------|------------------|")
    md.append(f"| /think | {_fmt(llm.get('think_mean_ms'), '.0f')} |")
    md.append(f"| /no_think | {_fmt(llm.get('no_think_mean_ms'), '.0f')} |")
    md.append("")

    # 5.4 Sentiment Analysis Accuracy
    md.append("## 5.4 Sentiment Analysis Accuracy")
    md.append("")
    md.append("### SenticNet Word-Level Emotion Detection")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Accuracy | {_fmt(sn_acc.get('sentic_accuracy'), '.3f')} |")
    md.append(f"| Macro-F1 | {_fmt(sn_acc.get('sentic_macro_f1'), '.3f')} |")
    md.append(f"| Weighted-F1 | {_fmt(sn_acc.get('sentic_weighted_f1'), '.3f')} |")
    md.append("")
    md.append("### Per-Class F1 (SenticNet)")
    md.append("")
    md.append("| Emotion | F1 Score |")
    md.append("|---------|----------|")
    for key, val in sn_acc.items():
        if key.startswith("sentic_f1_"):
            class_name = key.replace("sentic_f1_", "")
            md.append(f"| {class_name} | {_fmt(val, '.3f')} |")
    md.append("")

    # Emotion Classifier Comparison
    if emo_comp:
        md.append("### Emotion Classifier Comparison")
        md.append("")
        md.append("| Rank | Approach | Accuracy | Macro-F1 |")
        md.append("|------|----------|----------|----------|")
        for i in range(1, 9):
            approach = emo_comp.get(f"rank_{i}_approach", "")
            acc = emo_comp.get(f"rank_{i}_accuracy", "")
            if approach:
                md.append(f"| {i} | {approach} | {_fmt(acc, '.2f')} | N/A |")
        md.append("")
        md.append(f"**Winner:** {emo_comp.get('winner', 'N/A')}")
        md.append("")

    # Coaching quality ablation
    md.append("### Coaching Quality (SenticNet Ablation)")
    md.append("")
    md.append("| Dimension | With SenticNet | Without SenticNet | p-value | Significant |")
    md.append("|-----------|---------------|-------------------|---------|-------------|")
    for dim in ["empathy", "helpfulness", "adhd_appropriateness", "coherence", "informativeness"]:
        w_mean = _fmt(coaching.get(f"coaching_{dim}_with_mean"), ".2f")
        w_std = _fmt(coaching.get(f"coaching_{dim}_with_std"), ".2f")
        wo_mean = _fmt(coaching.get(f"coaching_{dim}_without_mean"), ".2f")
        wo_std = _fmt(coaching.get(f"coaching_{dim}_without_std"), ".2f")
        p_val = _fmt(coaching.get(f"coaching_{dim}_p"), ".4f")
        sig = coaching.get(f"coaching_{dim}_significant", "N/A")
        md.append(f"| {dim} | {w_mean} ± {w_std} | {wo_mean} ± {wo_std} | {p_val} | {sig} |")
    md.append("")
    md.append(f"**Ablation Win/Tie/Loss:** {coaching.get('coaching_wins', 'N/A')}/{coaching.get('coaching_ties', 'N/A')}/{coaching.get('coaching_losses', 'N/A')} of {coaching.get('coaching_total', 'N/A')}")
    md.append("")

    # 5.5 Distraction Detection
    md.append("## 5.5 Distraction Detection Accuracy")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Accuracy | {_fmt(clf_acc.get('clf_accuracy'), '.3f')} |")
    md.append(f"| Macro-F1 | {_fmt(clf_acc.get('clf_macro_f1'), '.3f')} |")
    md.append(f"| Weighted-F1 | {_fmt(clf_acc.get('clf_weighted_f1'), '.3f')} |")
    md.append("")
    md.append("### Per-Class F1")
    md.append("")
    md.append("| Category | F1 Score |")
    md.append("|----------|----------|")
    for key, val in clf_acc.items():
        if key.startswith("clf_f1_") and key not in ("clf_f1_macro avg", "clf_f1_weighted avg"):
            class_name = key.replace("clf_f1_", "")
            md.append(f"| {class_name} | {_fmt(val, '.3f')} |")
    md.append("")

    # Memory Retrieval
    md.append("### Memory Retrieval Accuracy")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Hit@1 | {_fmt(mem_ret.get('mem_hit_at_1'), '.2f')} |")
    md.append(f"| Hit@3 | {_fmt(mem_ret.get('mem_hit_at_3'), '.2f')} |")
    md.append(f"| Hit@5 | {_fmt(mem_ret.get('mem_hit_at_5'), '.2f')} |")
    md.append(f"| nDCG@3 | {_fmt(mem_ret.get('mem_ndcg_at_3'), '.3f')} |")
    md.append(f"| Mean Latency | {_fmt(mem_ret.get('mem_mean_latency_ms'), '.0f')} ms |")
    md.append(f"| P95 Latency | {_fmt(mem_ret.get('mem_p95_latency_ms'), '.0f')} ms |")
    md.append("")

    # 5.6 System Resource Usage
    md.append("## 5.6 System Resource Usage")
    md.append("")
    md.append("### Pipeline Latency Waterfall")
    md.append("")
    md.append("| Stage | Mean (ms) | Median (ms) |")
    md.append("|-------|-----------|-------------|")
    for stage in ["senticnet_analysis_ms", "safety_check_ms", "memory_retrieval_ms",
                   "prompt_assembly_ms", "llm_generation_ms", "memory_store_ms", "total_ms"]:
        stage_label = stage.replace("_ms", "").replace("_", " ").title()
        mean_val = pipe.get(f"pipe_{stage}_mean", "N/A")
        median_val = pipe.get(f"pipe_{stage}_median", "N/A")
        md.append(f"| {stage_label} | {_fmt(mean_val, '.0f')} | {_fmt(median_val, '.0f')} |")
    md.append("")
    md.append(f"**Bottleneck:** {pipe.get('pipe_bottleneck', 'N/A')}")
    md.append("")
    md.append("### Warm vs Cold Start")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Warm pipeline mean | {_fmt(pipe.get('warm_mean_ms'), '.0f')} ms |")
    md.append(f"| Estimated cold first | {_fmt(pipe.get('cold_first_ms'), '.0f')} ms |")
    md.append(f"| Full pipeline mean | {_fmt(pipe.get('full_pipeline_mean_ms'), '.0f')} ms |")
    md.append(f"| Ablation mean | {_fmt(pipe.get('ablation_mean_ms'), '.0f')} ms |")
    md.append(f"| SenticNet cost | {_fmt(pipe.get('senticnet_cost_pct'))}% |")
    md.append("")
    md.append("### System Resources Under Load")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Peak CPU | {_fmt(pipe.get('peak_cpu_pct'))}% |")
    md.append(f"| Peak RSS | {_fmt(pipe.get('peak_rss_mb'), '.0f')} MB |")
    md.append("")

    # Energy
    if energy:
        md.append("### Energy & Battery")
        md.append("")
        md.append("| Metric | Value |")
        md.append("|--------|-------|")
        md.append(f"| Idle power | {_fmt(energy.get('idle_watts'))} W |")
        md.append(f"| Energy per inference | {_fmt(energy.get('energy_per_inference_mean_mj'), '.0f')} mJ |")
        md.append(f"| Battery (active coaching) | {_fmt(energy.get('battery_active_hours'))} hours |")
        md.append(f"| Battery (casual use) | {_fmt(energy.get('battery_casual_hours'))} hours |")
        md.append(f"| Battery capacity | {_fmt(energy.get('battery_capacity_wh'))} Wh |")
        md.append("")

    # 5.7 SenticNet Benchmarks
    md.append("### SenticNet API Performance")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Single lookup mean | {_fmt(sn.get('single_lookup_mean_ms'), '.0f')} ms |")
    md.append(f"| Single lookup P95 | {_fmt(sn.get('single_lookup_p95_ms'), '.0f')} ms |")
    md.append(f"| API success rate | {_fmt(sn.get('api_success_rate_pct'))}% |")
    md.append(f"| Pipeline (10 words) | {_fmt(sn.get('pipeline_10w_mean_ms'), '.0f')} ms |")
    md.append(f"| Pipeline (50 words) | {_fmt(sn.get('pipeline_50w_mean_ms'), '.0f')} ms |")
    md.append(f"| Pipeline (100 words) | {_fmt(sn.get('pipeline_100w_mean_ms'), '.0f')} ms |")
    md.append(f"| Pipeline (200 words) | {_fmt(sn.get('pipeline_200w_mean_ms'), '.0f')} ms |")
    md.append("")

    # Classification Benchmark
    md.append("### Classification Cascade Performance")
    md.append("")
    md.append("| Tier | Mean Latency (ms) | P95 Latency (ms) |")
    md.append("|------|------------------|------------------|")
    for tier in ["tier_1", "tier_3", "tier_4"]:
        md.append(f"| {tier.replace('_', ' ').title()} | {_fmt(clf.get(f'latency_{tier}_mean_ms'))} | {_fmt(clf.get(f'latency_{tier}_p95_ms'))} |")
    md.append("")
    md.append(f"Rules coverage: {_fmt(clf.get('rules_total_pct'))}%")
    md.append(f"Embedding memory delta: {_fmt(clf.get('embedding_memory_delta_mb'))} MB")
    md.append("")

    # Mem0 Benchmark
    md.append("### Mem0 Memory Service Performance")
    md.append("")
    md.append("| Operation | Mean (ms) | P95 (ms) |")
    md.append("|-----------|-----------|---------|")
    md.append(f"| Store | {_fmt(mem.get('store_mean_ms'), '.0f')} | {_fmt(mem.get('store_p95_ms'), '.0f')} |")
    md.append(f"| Retrieval | {_fmt(mem.get('retrieval_mean_ms'), '.0f')} | {_fmt(mem.get('retrieval_p95_ms'), '.0f')} |")
    md.append("")

    return "\n".join(md)


# ── Main ──────────────────────────────────────────────────────────


def main():
    """Run the aggregator."""
    print(f"Scanning {RESULTS_DIR} for evaluation results...\n")

    # Load all result files
    llm_data = _load_latest("benchmark_llm_")
    clf_data = _load_latest("benchmark_classification_")
    sn_data = _load_latest("benchmark_senticnet_")
    mem_data = _load_latest("benchmark_memory_")
    pipe_data = _load_latest("benchmark_pipeline_")
    energy_data = _load_latest("benchmark_energy_")
    clf_acc_data = _load_latest("classification_accuracy_")
    coaching_data = _load_latest("coaching_quality_")
    sn_acc_data = _load_latest("senticnet_accuracy_")
    mem_ret_data = _load_latest("memory_retrieval_")
    comp_data = _load_latest("comparison_report")

    loaded = {
        "benchmark_llm": llm_data is not None,
        "benchmark_classification": clf_data is not None,
        "benchmark_senticnet": sn_data is not None,
        "benchmark_memory": mem_data is not None,
        "benchmark_pipeline": pipe_data is not None,
        "benchmark_energy": energy_data is not None,
        "classification_accuracy": clf_acc_data is not None,
        "coaching_quality": coaching_data is not None,
        "senticnet_accuracy": sn_acc_data is not None,
        "memory_retrieval": mem_ret_data is not None,
        "comparison_report": comp_data is not None,
    }
    print("Files loaded:")
    for name, ok in loaded.items():
        status = "OK" if ok else "MISSING"
        print(f"  {name:30s} {status}")
    print()

    # Collect metrics
    now = datetime.now(timezone.utc)
    summary = {
        "date": now.strftime("%Y-%m-%d"),
        "timestamp": now.isoformat(),
        "hardware": "Apple M4, 16GB Unified Memory",
        "source_files": {k: v.get("_source_file", "") for k, v in {
            "llm": llm_data or {},
            "classification_bench": clf_data or {},
            "senticnet_bench": sn_data or {},
            "memory_bench": mem_data or {},
            "pipeline": pipe_data or {},
            "energy": energy_data or {},
            "classification_accuracy": clf_acc_data or {},
            "coaching_quality": coaching_data or {},
            "senticnet_accuracy": sn_acc_data or {},
            "memory_retrieval": mem_ret_data or {},
            "emotion_comparison": comp_data or {},
        }.items() if v.get("_source_file")},
        "llm": _collect_llm_metrics(llm_data),
        "classification_bench": _collect_classification_metrics(clf_data),
        "senticnet_bench": _collect_senticnet_bench_metrics(sn_data),
        "memory_bench": _collect_memory_bench_metrics(mem_data),
        "pipeline": _collect_pipeline_metrics(pipe_data),
        "energy": _collect_energy_metrics(energy_data),
        "classification_accuracy": _collect_classification_accuracy(clf_acc_data),
        "coaching_quality": _collect_coaching_quality(coaching_data),
        "senticnet_accuracy": _collect_senticnet_accuracy(sn_acc_data),
        "memory_retrieval": _collect_memory_retrieval(mem_ret_data),
        "emotion_comparison": _collect_emotion_comparison(comp_data),
    }

    # Print console summary
    console_text = _print_summary(summary)

    # Save JSON
    ts = now.strftime("%Y%m%dT%H%M%SZ")
    json_path = RESULTS_DIR / f"summary_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nJSON summary saved: {json_path}")

    # Save Markdown
    md_text = _generate_markdown(summary)
    md_path = RESULTS_DIR / f"summary_{ts}.md"
    with open(md_path, "w") as f:
        f.write(md_text)
    print(f"Markdown summary saved: {md_path}")

    return summary


if __name__ == "__main__":
    main()
