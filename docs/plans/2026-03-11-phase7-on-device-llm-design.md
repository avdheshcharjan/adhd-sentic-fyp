# Phase 7 Design: On-Device LLM via Apple MLX

> Date: 2026-03-11
> Overrides: `docs/PHASE_7_ON_DEVICE_LLM.md` (which specified Llama 3.2 3B)
> Authoritative spec: `adhd-second-brain-models.md`

---

## Decision Summary

- **Coaching LLM**: Qwen3-4B 4-bit via MLX (~2.3 GB, load-on-demand)
- **Classification Layer 4**: all-MiniLM-L6-v2 sentence transformer (~80 MB, lazy-loaded)
- **LoRA**: Adapter path support coded in, actual fine-tuning deferred
- **Crisis resources**: Singapore (SOS CareText, IMH, National Care Hotline)
- **Architecture**: Direct integration, synchronous generation, no streaming

---

## New Files

| File | Purpose |
|------|---------|
| `backend/services/mlx_inference.py` | MLXInference class: load/generate/unload Qwen3-4B on-demand |
| `backend/services/chat_processor.py` | Full chat pipeline: SenticNet -> safety -> context -> LLM -> Mem0 |
| `backend/services/constants.py` | ADHD coaching system prompt + Singapore crisis resources |

## Modified Files

| File | Change |
|------|--------|
| `backend/config.py` | Add MLX settings: MLX_PRIMARY_MODEL, MLX_LIGHT_MODEL, MLX_ADAPTER_PATH, MLX_KEEP_ALIVE_SECONDS, EMBEDDING_MODEL |
| `backend/requirements.txt` | Add mlx-lm>=0.31.0, sentence-transformers>=3.0.0, numpy>=1.26.0 |
| `backend/main.py` | Add background model_cleanup_task() every 30s |
| `backend/api/chat.py` | Replace hardcoded responses with chat_processor.process_vent_message() |
| `backend/services/activity_classifier.py` | Add Layer 4 embedding similarity + user correction cache |
| `backend/models/chat_message.py` | Add thinking_mode and used_llm fields to ChatResponse |

## Data Flow

```
User sends POST /chat/message {text, conversation_id}
  -> chat_processor.process_vent_message()
    -> SenticNet full_analysis(text)        [existing pipeline]
    -> Safety check: if critical -> crisis resources, no LLM
    -> Build structured context (emotion, whoop, ADHD profile)
    -> Determine /think vs /no_think mode
    -> mlx_inference.generate_coaching_response()
      -> _load_model() if not loaded (~2-5s first time on M4)
      -> tokenizer.apply_chat_template()
      -> mlx_lm.generate()
    -> memory_service.add_conversation_memory()
  -> Return {response, senticnet, used_llm, thinking_mode}
```

## Memory Management

- Qwen3-4B loads on first chat request (~2-5s on M4 SSD)
- Stays resident while user is actively chatting
- Background task checks every 30s, unloads after 120s idle
- gc.collect() frees Metal GPU memory via MLX lazy evaluation
- Peak AI stack: ~2.5 GB (330 MB always-on + 2.3 GB on-demand)
- Leaves 3-5 GB headroom on 16 GB M4

## Activity Classifier Upgrade

Replace Layer 4 placeholder with:
- Lazy-loaded all-MiniLM-L6-v2 (~80 MB, only loads when L1-L3 fail)
- Zero-shot embedding similarity against 10 category descriptions
- Confidence threshold: 0.35 (below returns "other")
- User correction cache: record_correction() + load_corrections_from_db()

## Not In Scope

- LoRA fine-tuning (adapter path support only)
- SSE/WebSocket streaming
- Cloud fallback (Claude API)
- React dashboard
- OpenClaw integration
