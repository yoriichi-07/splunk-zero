"""
Google AI Studio Gemini API Connection Test -- Phase 1 Verification
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from langchain_google_genai import ChatGoogleGenerativeAI

import pytest

@pytest.mark.asyncio
async def test_llm():
    print("\n" + "=" * 60)
    print("  Splunk Zero -- LLM (Vertex AI) Test")
    print("=" * 60)

    Config.print_status()
    missing = Config.validate()
    
    if "GCP_PROJECT" in missing:
        print("[FAIL] GCP_PROJECT is not set. Cannot proceed.")
        assert False, "GCP_PROJECT is not set"

    print(f"LLM Model to test: {Config.LLM_MODEL}")
    print("Initializing Unified Google GenAI Client (Vertex Mode)...")

    success = False
    try:
        # Passing 'project' directly triggers Vertex AI mode natively 
        # in the langchain-google-genai package.
        llm = ChatGoogleGenerativeAI(
            model=Config.LLM_MODEL,
            project=Config.GCP_PROJECT,
            location=Config.GCP_LOCATION,
            temperature=0.0
        )

        print("Sending prompt: 'Say hello and tell me what model you are running on.'")
        response = await llm.ainvoke(
            "Say hello and tell me what model you are running on."
        )

        print("\n[OK] LLM Response received successfully:")
        print("-" * 50)
        print(response.content)
        print("-" * 50)
        success = True
    except Exception as e:
        print(f"\n[FAIL] LLM Test failed: {e}")
        import traceback
        traceback.print_exc()
        success = False

    assert success is True

if __name__ == "__main__":
    asyncio.run(test_llm())