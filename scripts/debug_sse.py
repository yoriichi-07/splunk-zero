"""Debug SSE streaming to understand why events aren't received."""
import httpx
import time

BASE_URL = "http://localhost:8888"

# Trigger
r = httpx.post(f"{BASE_URL}/trigger", timeout=10)
run_id = r.json()["run_id"]
print(f"Run: {run_id}")

# Try raw streaming
with httpx.stream("GET", f"{BASE_URL}/events/{run_id}", timeout=60) as resp:
    print(f"Status: {resp.status_code}")
    ct = resp.headers.get("content-type", "?")
    print(f"Content-Type: {ct}")
    buf = b""
    for chunk in resp.iter_bytes():
        buf += chunk
        chunk_preview = chunk[:300].decode("utf-8", errors="replace")
        print(f"Chunk ({len(chunk)} bytes): {chunk_preview}")
        if len(buf) > 10000 or b'"step": "done"' in buf:
            break
    print(f"\nTotal bytes received: {len(buf)}")
    print(f"\nFull content:\n{buf.decode('utf-8', errors='replace')[:3000]}")
