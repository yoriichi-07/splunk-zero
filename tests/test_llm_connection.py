"""
Google AI Studio Gemini API Connection Test -- Phase 1 Verification

Tests connection to Google AI Studio Gemini API using langchain-google-genai.

Usage:
    python -m tests.test_llm_connection
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from langchain_google_genai import ChatGoogleGenerativeAI


async def test_llm():
    print("\n" + "=" * 60)
    print("  Splunk Zero -- LLM (Google AI Studio) Test")
    print("=" * 60)

    # Validate config
    Config.print_status()
    missing = Config.validate()
    if "GOOGLE_API_KEY" in missing:
        print("[FAIL] GOOGLE_API_KEY is not set. Cannot proceed.")
        return False

    print(f"LLM Model to test: {Config.LLM_MODEL}")
    print("Initializing ChatGoogleGenerativeAI client...")

    try:
        # Initialize the Chat model
        llm = ChatGoogleGenerativeAI(
            model=Config.LLM_MODEL,
            google_api_key=Config.GOOGLE_API_KEY,
            temperature=0.0,
        )

        # Test call (invoking synchronously or asynchronously)
        print("Sending prompt: 'Say hello and tell me what model you are running on.'")
        response = await llm.ainvoke(
            "Say hello and tell me what model you are running on."
        )

        print("\n[OK] LLM Response received successfully:")
        print("-" * 50)
        print(response.content)
        print("-" * 50)
        return True
    except Exception as e:
        print(f"\n[FAIL] LLM Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(test_llm())
