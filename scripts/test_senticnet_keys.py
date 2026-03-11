#!/usr/bin/env python3
"""
Validate all 13 SenticNet API keys with a test sentence.
Run: python scripts/test_senticnet_keys.py
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from services.senticnet_client import SenticNetClient, API_ENDPOINTS
from config import get_settings

TEST_TEXT = "I am feeling a bit stressed but trying to stay focused"

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


async def main():
    settings = get_settings()
    client = SenticNetClient()

    print(f"\n{BOLD}🧪 SenticNet API Key Validation{RESET}")
    print(f"   Text: \"{TEST_TEXT}\"\n")
    print("-" * 60)

    passed = 0
    failed = 0
    skipped = 0

    for api_name, config_key in API_ENDPOINTS.items():
        key = getattr(settings, config_key, "")
        if not key:
            print(f"  {YELLOW}⏭  {api_name:22s} — no key configured{RESET}")
            skipped += 1
            continue

        result = await client._call_api(api_name, TEST_TEXT)

        if result is not None:
            # Truncate long results for display
            display = result[:80] + "..." if len(result) > 80 else result
            print(f"  {GREEN}✅ {api_name:22s} → {display}{RESET}")
            passed += 1
        else:
            print(f"  {RED}❌ {api_name:22s} — FAILED{RESET}")
            failed += 1

    print("-" * 60)
    print(
        f"\n  {GREEN}{passed} passed{RESET}  "
        f"{RED}{failed} failed{RESET}  "
        f"{YELLOW}{skipped} skipped{RESET}\n"
    )

    await client.close()

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
