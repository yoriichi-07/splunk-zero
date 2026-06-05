"""Quick test: trigger pipeline and wait for it to complete."""
import httpx
import json
import time

BASE_URL = "http://localhost:8888"

# Trigger a run
r = httpx.post(f"{BASE_URL}/trigger", timeout=10)
data = r.json()
run_id = data["run_id"]
print(f"Triggered run: {run_id}")

# Wait for pipeline to complete
print("Waiting 25 seconds for pipeline...")
time.sleep(25)

# Check server is still up
r2 = httpx.get(f"{BASE_URL}/health", timeout=10)
health = r2.json()
print(f"Server status: {health['status']}")
print(f"Splunk: {health['splunk']['status']}")
