# Code Changes Based on Dr. Rui Mao's Feedback (19 March 2026)

## Context

Dr. Rui Mao (co-supervisor) provided feedback on the ADHD Second Brain project on 18 March 2026. This document translates his technical suggestions into concrete code changes. These changes create the **evaluation infrastructure** needed to validate the system for the FYP report.

**Priority**: These changes should be implemented AFTER the core Phase 7 pipeline (on-device LLM) is working end-to-end. They are evaluation-layer additions, not core architecture changes.

**Reference files**: `blueprint.md`, `supplement.md`, `models.md`, `sentic.txt`. For AI-related decisions, `models.md` takes priority.

---

## Change 1: Ablation Mode — SenticNet ON/OFF Toggle

### Why

Dr. Rui said: *"This is great for your report to prove that the SenticNet layer actually adds value over a vanilla LLM."*

We need the ability to run the coaching LLM **with and without** SenticNet emotion injection, so we can compare response quality and prove the affective computing layer isn't just overhead.

### What to change

#### 1a. Add ablation config setting

In the app's config/settings (wherever `MLX_MODEL_PATH`, `MLX_MODEL_TTL` etc. are defined), add:

```python
# Evaluation / ablation settings
ABLATION_MODE: bool = False              # When True, disables SenticNet in chat pipeline
EVALUATION_LOGGING: bool = False         # When True, logs all interactions for analysis
EVALUATION_LOG_PATH: str = "data/evaluation_logs/"
```

#### 1b. Modify the chat processor pipeline

In the chat processor (Task 6 from Phase 7 plan — the pipeline that goes SenticNet → safety → LLM → Mem0), add a conditional bypass:

```python
# In the chat processor pipeline:
async def process_message(self, user_message: str, conversation_id: str) -> ChatResponse:
    # Step 1: SenticNet emotion analysis (skip if ablation mode)
    emotion_context = None
    if not settings.ABLATION_MODE:
        emotion_context = await self.sentic_service.analyze(user_message)
    
    # Step 2: Safety check (always runs)
    safety_result = await self.safety_checker.check(user_message)
    
    # Step 3: Build system prompt — with or without emotion injection
    system_prompt = self._build_system_prompt(
        emotion_context=emotion_context,  # None when ablation mode is on
        user_memory=await self.memory_service.get_context(conversation_id),
    )
    
    # Step 4: LLM inference
    response = await self.mlx_service.generate(system_prompt, user_message)
    
    # Step 5: Log for evaluation if enabled
    if settings.EVALUATION_LOGGING:
        await self._log_evaluation_data(
            user_message=user_message,
            emotion_context=emotion_context,
            response=response,
            ablation_mode=settings.ABLATION_MODE,
            conversation_id=conversation_id,
        )
    
    # Step 6: Store in Mem0
    await self.memory_service.store(conversation_id, user_message, response)
    
    return response
```

#### 1c. Add an API endpoint to toggle ablation mode at runtime

This allows switching during evaluation sessions without restarting the app:

```python
# New endpoint: POST /eval/ablation
@router.post("/eval/ablation")
async def toggle_ablation(enabled: bool):
    """Toggle SenticNet ablation mode for A/B evaluation."""
    settings.ABLATION_MODE = enabled
    return {"ablation_mode": enabled, "sentic_net": "disabled" if enabled else "enabled"}
```

#### 1d. Ensure the system prompt builder handles `emotion_context=None` gracefully

In `_build_system_prompt()`, the emotion injection block should be skipped entirely when `emotion_context` is `None`, not just show empty emotion fields. The vanilla LLM prompt should be a clean ADHD coaching prompt with no mention of emotions from SenticNet.

---

## Change 2: Evaluation Data Logger

### Why

Dr. Rui's three-pronged evaluation approach (within-subjects study, LLM personas, SenticNet ablation) all require structured logging of interactions so we can analyze them later.

### What to create

#### 2a. New file: `services/evaluation_logger.py`

```python
"""
Evaluation data logger for FYP evaluation.

Logs all chat interactions in a structured format for:
1. Ablation analysis (with vs without SenticNet)
2. Persona simulation analysis
3. Within-subjects study data collection
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel


class EvaluationLogEntry(BaseModel):
    timestamp: str
    conversation_id: str
    session_id: str                    # Groups interactions within one evaluation session
    ablation_mode: bool                # True = SenticNet disabled
    persona_id: Optional[str] = None   # Set when running LLM persona simulation
    
    # Input
    user_message: str
    
    # SenticNet output (null when ablation_mode=True)
    sentic_polarity: Optional[float] = None
    sentic_mood_tags: Optional[list[str]] = None
    hourglass_pleasantness: Optional[float] = None
    hourglass_attention: Optional[float] = None
    hourglass_sensitivity: Optional[float] = None
    hourglass_aptitude: Optional[float] = None
    
    # LLM output
    llm_response: str
    llm_latency_ms: float
    llm_token_count: int
    
    # Memory context used
    memory_context_summary: Optional[str] = None


class EvaluationLogger:
    def __init__(self, log_dir: str = "data/evaluation_logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
    
    async def log(self, entry: EvaluationLogEntry) -> None:
        """Append a log entry as a JSON line to the session log file."""
        filename = f"{entry.session_id}.jsonl"
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, "a") as f:
            f.write(entry.model_dump_json() + "\n")
    
    def load_session(self, session_id: str) -> list[EvaluationLogEntry]:
        """Load all entries for a given evaluation session."""
        filepath = os.path.join(self.log_dir, f"{session_id}.jsonl")
        entries = []
        with open(filepath, "r") as f:
            for line in f:
                entries.append(EvaluationLogEntry.model_validate_json(line.strip()))
        return entries
```

#### 2b. Wire the logger into the chat processor

The `_log_evaluation_data` method in the chat processor should construct an `EvaluationLogEntry` from the pipeline's intermediate state and call `EvaluationLogger.log()`. Make sure to capture LLM latency (time the `mlx_service.generate()` call) and token count.

---

## Change 3: LLM Persona Simulation Test Harness

### Why

Dr. Rui said: *"If recruiting human participants becomes a bottleneck, use LLMs (Gemini, ChatGPT, Qwen) to simulate different personas. Assign them specific 'ADHD profiles' (e.g., gender/age/job/...) and evaluate how the system's interventions perform across these varied contexts."*

This is a **test harness / evaluation script**, not part of the main app. It lives in a separate `evaluation/` directory.

### What to create

#### 3a. New directory: `evaluation/`

```
evaluation/
├── __init__.py
├── personas.py          # ADHD persona definitions
├── persona_runner.py    # Orchestrates simulated conversations
├── analyze_results.py   # Post-hoc analysis scripts
└── personas_config.json # Persona profiles
```

#### 3b. `evaluation/personas_config.json`

Define 5–8 diverse ADHD personas. Each has demographic info and an ADHD profile that the external LLM will role-play:

```json
[
  {
    "id": "persona_01",
    "name": "Alex",
    "age": 28,
    "gender": "Male",
    "occupation": "Software Engineer",
    "adhd_subtype": "Combined",
    "severity": "Moderate",
    "context": "Frequently gets hyperfocused on coding side projects and misses deadlines for main work. Struggles with task-switching between meetings and deep work. Recently started medication.",
    "emotional_tendency": "Gets frustrated quickly when interrupted, but enthusiastic about new projects",
    "num_messages": 10
  },
  {
    "id": "persona_02",
    "name": "Priya",
    "age": 34,
    "gender": "Female",
    "occupation": "Marketing Manager",
    "adhd_subtype": "Predominantly Inattentive",
    "severity": "Mild",
    "context": "Diagnosed late at 32. Manages a team of 5 but struggles with email overload and loses track of follow-ups. Uses many productivity apps but abandons them after a few weeks.",
    "emotional_tendency": "Anxious about forgetting things, self-critical when missing details",
    "num_messages": 10
  },
  {
    "id": "persona_03",
    "name": "Jordan",
    "age": 21,
    "gender": "Non-binary",
    "occupation": "University Student",
    "adhd_subtype": "Predominantly Hyperactive-Impulsive",
    "severity": "Severe",
    "context": "Final year CS student. Cannot sit through lectures. Submits assignments at the last minute. Social media is the primary distraction trigger. Unmedicated by choice.",
    "emotional_tendency": "Restless and impatient, mood swings between excitement and despair about grades",
    "num_messages": 10
  },
  {
    "id": "persona_04",
    "name": "Mei Ling",
    "age": 42,
    "gender": "Female",
    "occupation": "Freelance Graphic Designer",
    "adhd_subtype": "Combined",
    "severity": "Moderate",
    "context": "Works from home with no external structure. Diagnosed 5 years ago. Struggles with time blindness and project estimation. Has two children, adding to executive function demands.",
    "emotional_tendency": "Overwhelmed by competing priorities, guilt about productivity gaps",
    "num_messages": 10
  },
  {
    "id": "persona_05",
    "name": "Daniel",
    "age": 55,
    "gender": "Male",
    "occupation": "Financial Analyst",
    "adhd_subtype": "Predominantly Inattentive",
    "severity": "Mild",
    "context": "Late diagnosis at 50. Has developed strong coping mechanisms over decades but still struggles with long reports and detail-oriented tasks. Prefers structured approaches.",
    "emotional_tendency": "Calm exterior but internal frustration; values efficiency and dislikes 'touchy-feely' approaches",
    "num_messages": 10
  }
]
```

#### 3c. `evaluation/persona_runner.py`

This script:
1. Loads a persona definition
2. Initializes an external LLM (via API) to role-play that persona
3. Sends messages from the persona-LLM to your ADHD Second Brain's `/chat/message` endpoint
4. Runs the conversation for N turns
5. Logs everything via the evaluation logger
6. Runs both WITH and WITHOUT SenticNet (ablation) for each persona

```python
"""
LLM Persona Simulation Runner

Drives simulated ADHD user conversations against the Second Brain app.
Runs each persona in two modes: with SenticNet (default) and without (ablation).

Usage:
    python -m evaluation.persona_runner --persona persona_01 --provider openai
    python -m evaluation.persona_runner --all --provider openai
"""

import argparse
import asyncio
import json
import httpx
import os
from datetime import datetime


# The app's base URL (assumes the Second Brain backend is running locally)
APP_BASE_URL = "http://localhost:8000"

# External LLM providers for persona simulation
# The user should set their own API keys as environment variables
PROVIDERS = {
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o",
        "api_key_env": "OPENAI_API_KEY",
    },
    "google": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        "api_key_env": "GOOGLE_API_KEY",
    },
    # Qwen Cloud API (DashScope) - optional
    "qwen_cloud": {
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen-max",
        "api_key_env": "DASHSCOPE_API_KEY",
    },
}


def build_persona_system_prompt(persona: dict) -> str:
    """Build a system prompt that makes the external LLM role-play as the ADHD persona."""
    return f"""You are role-playing as {persona['name']}, a {persona['age']}-year-old {persona['gender']} {persona['occupation']}.

ADHD Profile:
- Subtype: {persona['adhd_subtype']}
- Severity: {persona['severity']}
- Context: {persona['context']}
- Emotional tendency: {persona['emotional_tendency']}

RULES:
- Stay in character at all times. You ARE this person talking to an ADHD coaching assistant.
- Write naturally as this person would — use their vocabulary, emotional state, and concerns.
- Show realistic ADHD behaviors: tangential thoughts, frustration, emotional reactions, executive function struggles.
- Do NOT break character or mention that you are an AI.
- Each message should be 1-3 sentences, like a real chat message.
- React authentically to the coaching assistant's responses — sometimes positively, sometimes with resistance or skepticism.
- Vary your emotional state across the conversation based on your emotional tendency profile.

Start by describing a current struggle or asking for help with something specific to your situation."""


async def simulate_conversation(
    persona: dict,
    provider: str,
    ablation_mode: bool = False,
) -> list[dict]:
    """Run a full simulated conversation between a persona-LLM and the Second Brain app."""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Set ablation mode on the app
        await client.post(
            f"{APP_BASE_URL}/eval/ablation",
            params={"enabled": ablation_mode},
        )
        
        conversation_id = f"eval_{persona['id']}_{'ablation' if ablation_mode else 'sentic'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        persona_system_prompt = build_persona_system_prompt(persona)
        
        # Track the external LLM's conversation history for continuity
        persona_chat_history = [
            {"role": "system", "content": persona_system_prompt},
        ]
        
        log = []
        
        for turn in range(persona["num_messages"]):
            # Step 1: Get the persona's next message from external LLM
            persona_message = await _call_external_llm(
                provider, persona_chat_history
            )
            persona_chat_history.append({"role": "assistant", "content": persona_message})
            
            # Step 2: Send the persona's message to the Second Brain app
            app_response = await client.post(
                f"{APP_BASE_URL}/chat/message",
                json={
                    "message": persona_message,
                    "conversation_id": conversation_id,
                },
            )
            app_reply = app_response.json()
            
            # Step 3: Feed the app's response back to the persona-LLM
            persona_chat_history.append(
                {"role": "user", "content": f"The ADHD coaching assistant replied: {app_reply.get('response', '')}"}
            )
            
            log.append({
                "turn": turn + 1,
                "persona_message": persona_message,
                "app_response": app_reply,
                "ablation_mode": ablation_mode,
            })
        
        return log


async def _call_external_llm(provider: str, messages: list[dict]) -> str:
    """Call an external LLM API to generate the persona's next message."""
    # Implementation depends on provider — use OpenAI-compatible format for openai/qwen_cloud,
    # Google's format for Gemini. Return the generated text.
    # IMPLEMENT THIS based on the PROVIDERS config above.
    raise NotImplementedError("Implement per-provider API call logic here")


async def run_all_personas(provider: str):
    """Run all personas through both SenticNet and ablation modes."""
    with open("evaluation/personas_config.json") as f:
        personas = json.load(f)
    
    for persona in personas:
        print(f"\n{'='*60}")
        print(f"Running persona: {persona['name']} ({persona['id']})")
        
        # Run WITH SenticNet
        print(f"  Mode: SenticNet ENABLED")
        sentic_log = await simulate_conversation(persona, provider, ablation_mode=False)
        
        # Run WITHOUT SenticNet (ablation)
        print(f"  Mode: SenticNet DISABLED (ablation)")
        ablation_log = await simulate_conversation(persona, provider, ablation_mode=True)
        
        # Save logs
        output_dir = "data/evaluation_logs/persona_runs"
        os.makedirs(output_dir, exist_ok=True)
        with open(f"{output_dir}/{persona['id']}_results.json", "w") as f:
            json.dump({
                "persona": persona,
                "sentic_enabled": sentic_log,
                "sentic_disabled": ablation_log,
            }, f, indent=2)
        
        print(f"  Saved to {output_dir}/{persona['id']}_results.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ADHD persona simulations")
    parser.add_argument("--persona", type=str, help="Specific persona ID to run")
    parser.add_argument("--all", action="store_true", help="Run all personas")
    parser.add_argument("--provider", type=str, default="openai", choices=list(PROVIDERS.keys()))
    args = parser.parse_args()
    
    if args.all:
        asyncio.run(run_all_personas(args.provider))
    elif args.persona:
        # Load and run single persona
        with open("evaluation/personas_config.json") as f:
            personas = {p["id"]: p for p in json.load(f)}
        if args.persona in personas:
            asyncio.run(simulate_conversation(personas[args.persona], args.provider))
        else:
            print(f"Persona {args.persona} not found")
```

---

## Change 4: Hourglass-to-ADHD Correlation Logging

### Why

Dr. Rui said: *"Not sure if [your Hourglass-to-ADHD mapping] is supported by literature. If not, you can analyse the correlation between emotion classes (from SenticNet) and ADHD types (from human/LLM self-reports during the evaluation)."*

Instead of claiming the mapping is literature-backed, we **generate empirical evidence** for it. This requires logging the Hourglass dimensions alongside ADHD profile data, then computing correlations.

### What to change

#### 4a. Ensure the evaluation logger captures all four Hourglass dimensions

Already covered in Change 2's `EvaluationLogEntry` model — the fields `hourglass_pleasantness`, `hourglass_attention`, `hourglass_sensitivity`, `hourglass_aptitude` must be populated from the SenticNet response.

In the SenticNet service, when analyzing text, make sure the response object exposes all four Hourglass dimensions separately (not just a combined polarity score). If the current SenticNet integration only returns polarity, extend it to also return the four Hourglass values.

#### 4b. New analysis script: `evaluation/analyze_results.py`

```python
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
    for filename in os.listdir(log_dir):
        if filename.endswith("_results.json"):
            with open(os.path.join(log_dir, filename)) as f:
                results.append(json.load(f))
    return results


def ablation_comparison(results: list[dict]) -> dict:
    """
    Compare response characteristics between SenticNet-enabled and disabled modes.
    
    Metrics to compare:
    - Average response length (proxy for engagement depth)
    - Emotion-related word frequency in responses
    - Latency difference
    - Whether responses reference emotional state
    """
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
        
        summary[persona_id] = {
            "persona_name": persona_name,
            "adhd_subtype": adhd_subtype,
            "avg_response_length_sentic": statistics.mean(sentic_lengths) if sentic_lengths else 0,
            "avg_response_length_ablation": statistics.mean(ablation_lengths) if ablation_lengths else 0,
            # Add more metrics as the response model becomes clearer:
            # - emotion acknowledgment rate
            # - strategy specificity score
            # - conversation coherence
        }
    
    return summary


def hourglass_adhd_correlation(log_dir: str = "data/evaluation_logs") -> dict:
    """
    Analyze correlation between SenticNet Hourglass dimensions and ADHD subtypes.
    
    Groups emotion dimension averages by ADHD subtype (Combined, Inattentive,
    Hyperactive-Impulsive) to see if different subtypes produce different 
    emotional profiles in their messages.
    
    This produces NOVEL EMPIRICAL EVIDENCE for the Hourglass-to-ADHD mapping
    rather than relying on literature that may not exist.
    """
    # Load all JSONL evaluation logs (non-persona-run files)
    subtype_emotions = defaultdict(lambda: {
        "pleasantness": [],
        "attention": [],
        "sensitivity": [],
        "aptitude": [],
    })
    
    # Also load from persona runs
    persona_results = load_all_persona_results()
    for result in persona_results:
        subtype = result["persona"]["adhd_subtype"]
        for turn in result["sentic_enabled"]:
            resp = turn["app_response"]
            # Extract Hourglass values from the app response's emotion data
            # The exact field path depends on your ChatResponse model
            emotion = resp.get("emotion_context", {})
            if emotion:
                for dim in ["pleasantness", "attention", "sensitivity", "aptitude"]:
                    val = emotion.get(f"hourglass_{dim}")
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
    ablation = ablation_comparison(results)
    print(json.dumps(ablation, indent=2))
    
    print("\n" + "=" * 60)
    print("HOURGLASS-TO-ADHD CORRELATION")
    print("=" * 60)
    correlation = hourglass_adhd_correlation()
    print(json.dumps(correlation, indent=2, default=str))
```

---

## Change 5: Expose Hourglass Dimensions in ChatResponse

### Why

The current `ChatResponse` model (Task 5 from Phase 7) may only include a summary emotion label or polarity. For evaluation, we need the raw Hourglass dimensions exposed in the API response.

### What to change

Extend the `ChatResponse` model to include optional emotion detail:

```python
class EmotionDetail(BaseModel):
    """SenticNet analysis output, included in response for evaluation."""
    polarity: float                          # Overall sentiment polarity [-1, 1]
    mood_tags: list[str]                     # e.g., ["#frustrated", "#anxious"]
    hourglass_pleasantness: float            # [-1, 1]
    hourglass_attention: float               # [-1, 1]
    hourglass_sensitivity: float             # [-1, 1]
    hourglass_aptitude: float                # [-1, 1]
    sentic_concepts: list[str]               # Top matched SenticNet concepts


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    emotion_context: Optional[EmotionDetail] = None   # Populated when SenticNet is active
    ablation_mode: bool = False                        # Indicates if SenticNet was bypassed
    latency_ms: float                                  # End-to-end processing time
    token_count: int                                   # LLM tokens generated
```

This ensures the persona runner and evaluation scripts can extract Hourglass dimensions from every response.

---

## Change 6: ASRS and SUS Scoring Utilities

### Why

Dr. Rui recommended a within-subjects study using the **ASRS** (Adult ADHD Self-Report Scale) for ADHD symptom screening and **SUS** (System Usability Scale) for usability validation.

These are scoring utilities for the FYP evaluation — they don't go into the main app, but into `evaluation/`.

### What to create

#### 6a. `evaluation/questionnaires.py`

```python
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
# Sum × 2.5 = final score (0-100)

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
```

---

## Summary of file changes

### Modified existing files

| File | Change |
|------|--------|
| Config/settings | Add `ABLATION_MODE`, `EVALUATION_LOGGING`, `EVALUATION_LOG_PATH` |
| Chat processor (pipeline) | Add ablation conditional bypass around SenticNet call |
| Chat processor (pipeline) | Add evaluation logging hook after LLM response |
| `_build_system_prompt()` | Handle `emotion_context=None` cleanly (no empty emotion fields) |
| `ChatResponse` model | Add `EmotionDetail` with Hourglass dimensions, `ablation_mode`, `latency_ms`, `token_count` |
| SenticNet service | Ensure all 4 Hourglass dimensions are extracted and returned (not just polarity) |
| API routes | Add `POST /eval/ablation` endpoint |

### New files

| File | Purpose |
|------|---------|
| `services/evaluation_logger.py` | Structured JSONL logging for all evaluation interactions |
| `evaluation/__init__.py` | Package init |
| `evaluation/personas_config.json` | 5 diverse ADHD persona definitions |
| `evaluation/persona_runner.py` | Orchestrates simulated conversations via external LLMs |
| `evaluation/analyze_results.py` | Ablation comparison + Hourglass-to-ADHD correlation analysis |
| `evaluation/questionnaires.py` | ASRS-v1.1 and SUS scoring utilities |

### New directories

| Directory | Purpose |
|-----------|---------|
| `evaluation/` | All evaluation scripts (separate from main app) |
| `data/evaluation_logs/` | Evaluation log output (gitignored) |
| `data/evaluation_logs/persona_runs/` | Persona simulation results |

---

## Implementation order

1. **Change 5** — Extend `ChatResponse` with `EmotionDetail` and Hourglass dimensions (small, no dependencies)
2. **Change 1a** — Add ablation config settings
3. **Change 1b+1d** — Modify chat processor pipeline with ablation bypass
4. **Change 1c** — Add `/eval/ablation` endpoint
5. **Change 2** — Create evaluation logger and wire into chat processor
6. **Change 6** — Create questionnaire scoring utilities (standalone, no dependencies)
7. **Change 4** — Create analysis script (depends on logger output format)
8. **Change 3** — Create persona runner (depends on all the above being in place)

**Important**: Do NOT start these changes until the core Phase 7 pipeline (Tasks 1-10) is complete and the app can handle a basic chat interaction end-to-end. These are evaluation-layer additions.

---

## Implementation Notes

- Read `models.md` for all AI-related architecture decisions — it takes priority over `blueprint.md`
- Read `sentic.txt` for SenticNet API details and the Hourglass of Emotions model
- The 10-task Phase 7 plan is at `docs/plans/2026-03-11-phase7-on-device-llm.md`
- The SenticNet service should already exist from earlier phases — check `services/` for the current implementation
- Use Pydantic v2 patterns (`model_validate_json`, `model_dump_json`) not v1
- All async — use `async/await` consistently
- The `evaluation/` directory is a separate concern from the main app — it imports from the app but lives outside the main package
