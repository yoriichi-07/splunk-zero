import httpx

BASE_URL = "http://localhost:8888"

def test_trigger():
    print("Triggering run...")
    r = httpx.post(f"{BASE_URL}/trigger", timeout=10)
    print("Response:", r.status_code, r.json())
    run_id = r.json()["run_id"]
    
    print(f"Connecting to /events/{run_id}...")
    try:
        with httpx.stream("GET", f"{BASE_URL}/events/{run_id}", timeout=30) as response:
            print("Status:", response.status_code)
            print("Headers:", response.headers)
            for line in response.iter_lines():
                if line:
                    print("Received line:", line)
    except Exception as e:
        print("Error during stream:", e)

if __name__ == "__main__":
    test_trigger()
