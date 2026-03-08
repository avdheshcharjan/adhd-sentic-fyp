# Phase 7: On-Device LLM (Apple MLX)

> **Timeline**: Week 6–7  
> **Dependencies**: Phase 1 (backend), Phase 3 (SenticNet for context injection)  
> **Requirements**: Apple Silicon (M1+), 16GB RAM recommended

---

## Overview

On-device LLM inference using Apple's MLX framework. Models run on Apple Silicon unified memory with zero GPU transfer overhead. Provides low-latency response generation with SenticNet context injection and fast window title classification.

---

## Model Configuration

| Model | Size | Use Case | Latency |
|-------|------|----------|---------|
| **Llama 3.2 3B Instruct (4-bit)** | ~1.8GB | Chat responses, coaching | ~2–3s |
| **Llama 3.2 1B Instruct (4-bit)** | ~700MB | Fast classification (Layer 4 fallback) | ~200ms |

### Installation
```bash
pip install mlx-lm
# Models auto-download from Hugging Face on first load
# Or pre-download:
mlx_lm.convert --hf-path meta-llama/Llama-3.2-3B-Instruct -q 4bit
```

---

## Key Capabilities

### 1. Chat Response Generation

Generates empathetic ADHD coaching responses with SenticNet context injected into the prompt:

```xml
<senticnet_analysis>
Emotion: frustration
Intensity: 82/100
Engagement: -45/100
Wellbeing: -30/100
Safety level: normal
Key concepts: deadline, overwhelm, procrastination
</senticnet_analysis>
```

- **Max tokens**: 300 (keeps responses ADHD-friendly short)
- **Temperature**: 0.7 (balanced creativity/reliability)
- **Fallback**: Claude Sonnet for complex coaching queries

### 2. Window Title Classification (Layer 4)

Fast classification of ambiguous window titles that layers 1–3 couldn't categorize:

```
Input:  "Meeting Notes - Q4 Planning Session.docx"
Output: "productivity"
```

- **Max tokens**: 5 (single word)
- **Temperature**: 0.0 (deterministic)
- Uses 1B model for speed (~200ms)

---

## Key File

| File | Purpose |
|------|---------|
| `backend/services/mlx_inference.py` | Model loading + generation + classification |

---

## Resource Usage

- **Startup**: 5–10 seconds to load models into unified memory
- **Runtime**: ~1.8GB for 3B model (stays in memory)
- **Inference**: Runs on Apple Neural Engine + GPU cores

---

## Verification Checklist

- [ ] MLX loads Llama 3.2 3B model successfully
- [ ] Chat response generation works with SenticNet context
- [ ] Window title classification returns valid categories
- [ ] Responses stay under 300 tokens / 2–3 sentences
- [ ] Fallback to Claude works when MLX is unavailable

---

## Next Phase

→ [Phase 8: OpenClaw Integration](PHASE_8_OPENCLAW.md)
