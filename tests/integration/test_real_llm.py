"""Real LLM integration test — tests the full harness with actual API calls."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, "src")

from harness import CognitiveHarness, load_config


async def main():
    print("=== Cognitive Harness Integration Test ===\n")

    # Load config
    config = load_config("config/default.yaml")
    print(f"Model: {config.model}")
    print(f"API base: {config.api_base}")
    print(f"Max iterations: {config.max_iterations}")
    print(f"Sub-agent count: {config.sub_agent_count}")
    print()

    # Test 1: Simple non-stuck completion
    print("--- Test 1: Simple completion ---")
    harness = CognitiveHarness(config)
    result = await harness.invoke("What is 2 + 2? Reply with just the number.")
    print(f"Response: {result}")
    assert "4" in result, f"Expected '4' in response, got: {result}"
    print("PASS\n")

    # Test 2: Slightly harder reasoning
    print("--- Test 2: Reasoning task ---")
    harness2 = CognitiveHarness(config)
    result2 = await harness2.invoke(
        "I have 3 apples. I give away 1 and buy 5 more. "
        "How many apples do I have? Reply with just the number."
    )
    print(f"Response: {result2}")
    assert "7" in result2, f"Expected '7' in response, got: {result2}"
    print("PASS\n")

    print("=== All integration tests passed ===")


if __name__ == "__main__":
    asyncio.run(main())
