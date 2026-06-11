import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.agent.graph import splunk_zero_graph
from src.config import Config

load_dotenv(Path(__file__).parent.parent / ".env")

async def run_direct():
    print("Starting direct pipeline run...")
    Config.print_status()
    
    initial_state = {
        "run_id": "direct1",
        "trigger_type": "manual",
        "target_period_days": Config.ANALYSIS_PERIOD_DAYS,
        "events": [],
        "errors": [],
        "current_step": "starting",
    }
    
    try:
        result = await splunk_zero_graph.ainvoke(initial_state)
        print("\nPipeline execution complete!")
        print(f"Waste found: {result.get('waste_found', False)}")
        if result.get("wasteful_sources"):
            print("Wasteful sources:")
            for ws in result["wasteful_sources"]:
                print(f"  - {ws['sourcetype']}: {ws['daily_gb']} GB/day, est savings: ${ws['est_monthly_cost']}/mo")
        if result.get("pull_requests"):
            print("Pull requests created:")
            for pr in result["pull_requests"]:
                print(f"  - {pr['sourcetype']}: {pr['pr_url']}")
        if result.get("errors"):
            print("Errors encountered:")
            for err in result["errors"]:
                print(f"  - {err}")
    except Exception:
        print("\nPipeline execution failed with exception:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_direct())
