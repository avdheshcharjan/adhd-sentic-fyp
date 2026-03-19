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
import os
from datetime import datetime

import httpx

# The app's base URL (assumes the Second Brain backend is running locally)
APP_BASE_URL = "http://localhost:8420"

# External LLM providers for persona simulation
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

        conversation_id = (
            f"eval_{persona['id']}_{'ablation' if ablation_mode else 'sentic'}"
            f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
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
                    "text": persona_message,
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

            print(f"    Turn {turn + 1}/{persona['num_messages']} complete")

        return log


async def _call_external_llm(provider: str, messages: list[dict]) -> str:
    """Call an external LLM API to generate the persona's next message."""
    config = PROVIDERS[provider]
    api_key = os.environ.get(config["api_key_env"], "")

    if not api_key:
        raise ValueError(
            f"Missing API key: set {config['api_key_env']} environment variable"
        )

    async with httpx.AsyncClient(timeout=60.0) as client:
        if provider == "google":
            # Google Gemini API format
            contents = []
            for msg in messages:
                role = "user" if msg["role"] in ("system", "user") else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})

            resp = await client.post(
                f"{config['url']}?key={api_key}",
                json={"contents": contents},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

        else:
            # OpenAI-compatible format (openai, qwen_cloud)
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            resp = await client.post(
                config["url"],
                headers=headers,
                json={
                    "model": config["model"],
                    "messages": messages,
                    "max_tokens": 150,
                    "temperature": 0.8,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]


async def run_all_personas(provider: str):
    """Run all personas through both SenticNet and ablation modes."""
    config_path = os.path.join(os.path.dirname(__file__), "personas_config.json")
    with open(config_path) as f:
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
        config_path = os.path.join(os.path.dirname(__file__), "personas_config.json")
        with open(config_path) as f:
            personas = {p["id"]: p for p in json.load(f)}
        if args.persona in personas:
            asyncio.run(simulate_conversation(personas[args.persona], args.provider))
        else:
            print(f"Persona {args.persona} not found")
    else:
        parser.print_help()
