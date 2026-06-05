"""
Splunk Zero — Synthetic Data Loader

Sends realistic log data to Splunk via HTTP Event Collector (HEC).
Creates sourcetypes that will appear in Splunk's _internal metrics
as high-volume sources. Since nobody searches for them, they will
be detected as "wasteful" by the agent.

Usage:
    python -m scripts.synthetic_data

Prerequisites:
    1. Splunk HEC enabled (Settings > Data inputs > HTTP Event Collector)
    2. HEC token created and added to .env as SPLUNK_HEC_TOKEN
    3. SPLUNK_HEC_PORT in .env (default: 8088)
"""

import os
import sys
import json
import time
import random
import string
import httpx
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config


# ── Synthetic sourcetypes and their log patterns ──────────
# These are designed to look like real application logs
SYNTHETIC_SOURCES = [
    {
        "sourcetype": "app:payment-service:debug",
        "source": "/var/log/payment-service/debug.log",
        "host": "payment-svc-01",
        "log_templates": [
            "DEBUG [PaymentProcessor] Processing transaction txn_{txn_id} for user usr_{user_id} amount=${amount}",
            "DEBUG [PaymentValidator] Validating card ending in {card_last4} for txn_{txn_id}",
            "DEBUG [PaymentGateway] Sending request to gateway endpoint /api/v2/charge timeout=30s",
            "DEBUG [PaymentProcessor] Transaction txn_{txn_id} completed in {duration}ms status=SUCCESS",
            "DEBUG [PaymentCache] Cache hit ratio: {cache_ratio}% for payment tokens",
            "DEBUG [PaymentDB] Query executed in {query_time}ms: SELECT * FROM transactions WHERE id = ?",
            "DEBUG [PaymentProcessor] Heartbeat check: connections={conn_count}, queue_depth={queue_depth}",
            "DEBUG [PaymentRetry] No failed transactions in retry queue. Next check in 60s.",
        ],
        "events_per_batch": 200,
        "batches": 5,
    },
    {
        "sourcetype": "app:user-auth:debug",
        "source": "/var/log/auth-service/debug.log",
        "host": "auth-svc-01",
        "log_templates": [
            "DEBUG [AuthService] Login attempt for user {username} from IP {ip_addr}",
            "DEBUG [SessionManager] Session created: sid={session_id} ttl=3600s",
            "DEBUG [TokenService] JWT token generated for user {username} exp={exp_time}",
            "DEBUG [AuthCache] Token cache size: {cache_size} entries, memory: {memory_mb}MB",
            "DEBUG [RateLimiter] Request count for IP {ip_addr}: {req_count}/100 (window=60s)",
            "DEBUG [AuthDB] User lookup completed in {query_time}ms for {username}",
        ],
        "events_per_batch": 150,
        "batches": 4,
    },
    {
        "sourcetype": "app:inventory-api:debug",
        "source": "/var/log/inventory-api/debug.log",
        "host": "inventory-api-01",
        "log_templates": [
            "DEBUG [InventoryService] Stock check for SKU-{sku} warehouse={warehouse}: qty={quantity}",
            "DEBUG [InventoryCache] Cache miss for SKU-{sku}, fetching from database",
            "DEBUG [InventoryDB] Query: SELECT stock_level FROM products WHERE sku = ? [{query_time}ms]",
            "DEBUG [InventorySync] Syncing {sync_count} items with external catalog",
            "DEBUG [InventoryService] Healthcheck: db_pool={pool_size}, active_queries={active}",
        ],
        "events_per_batch": 100,
        "batches": 3,
    },
]


def _generate_event(template: str) -> str:
    """Generate a random log event from a template."""
    replacements = {
        "{txn_id}": "".join(random.choices(string.hexdigits[:16], k=12)),
        "{user_id}": str(random.randint(10000, 99999)),
        "{amount}": f"{random.uniform(5.0, 500.0):.2f}",
        "{card_last4}": str(random.randint(1000, 9999)),
        "{duration}": str(random.randint(1, 200)),
        "{cache_ratio}": str(random.randint(60, 99)),
        "{query_time}": str(random.randint(1, 50)),
        "{conn_count}": str(random.randint(5, 50)),
        "{queue_depth}": str(random.randint(0, 10)),
        "{username}": random.choice(["alice", "bob", "charlie", "diana", "eve", "frank"]),
        "{ip_addr}": f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
        "{session_id}": "".join(random.choices(string.hexdigits[:16], k=16)),
        "{exp_time}": str(int(time.time()) + 3600),
        "{cache_size}": str(random.randint(100, 5000)),
        "{memory_mb}": str(random.randint(10, 200)),
        "{req_count}": str(random.randint(1, 100)),
        "{sku}": str(random.randint(100000, 999999)),
        "{warehouse}": random.choice(["US-EAST", "US-WEST", "EU-CENTRAL", "AP-SOUTH"]),
        "{quantity}": str(random.randint(0, 1000)),
        "{sync_count}": str(random.randint(10, 500)),
        "{pool_size}": str(random.randint(5, 20)),
        "{active}": str(random.randint(0, 10)),
    }

    result = template
    for key, value in replacements.items():
        result = result.replace(key, value)
    return result


def send_batch(
    hec_url: str,
    hec_token: str,
    sourcetype: str,
    source: str,
    host: str,
    events: list[str],
    verify_ssl: bool = False,
) -> dict:
    """Send a batch of events to Splunk HEC."""

    # HEC accepts NDJSON (one JSON object per line, no array wrapper)
    payload = ""
    for event_text in events:
        event_obj = {
            "event": event_text,
            "sourcetype": sourcetype,
            "source": source,
            "host": host,
            "time": time.time() - random.uniform(0, 86400),  # Random time in last 24h
        }
        payload += json.dumps(event_obj) + "\n"

    headers = {
        "Authorization": f"Splunk {hec_token}",
        "Content-Type": "application/json",
    }

    with httpx.Client(verify=verify_ssl) as client:
        response = client.post(hec_url, content=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()


def load_synthetic_data():
    """Load all synthetic data into Splunk."""
    print("\n" + "=" * 60)
    print("  Splunk Zero -- Synthetic Data Loader")
    print("=" * 60)

    # Check config
    hec_token = os.getenv("SPLUNK_HEC_TOKEN", "")
    hec_port = int(os.getenv("SPLUNK_HEC_PORT", "8088"))
    hec_host = Config.SPLUNK_HOST

    if not hec_token:
        print("\n  [FAIL] SPLUNK_HEC_TOKEN not set in .env")
        print("  Please create an HEC token in Splunk Web:")
        print("    Settings > Data inputs > HTTP Event Collector > New Token")
        print("  Then add to .env: SPLUNK_HEC_TOKEN=<your token>")
        return False

    # Determine URL scheme based on SSL setting
    hec_url = f"https://{hec_host}:{hec_port}/services/collector"
    print(f"\n  HEC URL: {hec_url}")
    print(f"  Token:   {hec_token[:8]}...")

    total_events = 0
    total_sources = len(SYNTHETIC_SOURCES)

    for i, source_config in enumerate(SYNTHETIC_SOURCES, 1):
        sourcetype = source_config["sourcetype"]
        source = source_config["source"]
        host = source_config["host"]
        templates = source_config["log_templates"]
        events_per_batch = source_config["events_per_batch"]
        batches = source_config["batches"]

        print(f"\n  [{i}/{total_sources}] Loading: {sourcetype}")
        print(f"       Events per batch: {events_per_batch}")
        print(f"       Batches: {batches}")

        for batch_num in range(1, batches + 1):
            events = [
                _generate_event(random.choice(templates))
                for _ in range(events_per_batch)
            ]

            try:
                result = send_batch(
                    hec_url=hec_url,
                    hec_token=hec_token,
                    sourcetype=sourcetype,
                    source=source,
                    host=host,
                    events=events,
                )
                status = result.get("text", "unknown")
                print(f"       Batch {batch_num}/{batches}: {len(events)} events -> {status}")
                total_events += len(events)
            except Exception as e:
                print(f"       Batch {batch_num}/{batches}: FAILED - {e}")

            # Small delay between batches
            time.sleep(0.5)

    print(f"\n  {'=' * 50}")
    print(f"  DONE! Sent {total_events} events across {total_sources} sourcetypes.")
    print(f"  {'=' * 50}")
    print(f"\n  These will appear in Splunk's _internal metrics within ~60 seconds.")
    print(f"  Verify in Splunk Web:")
    print(f"    Search: index=_internal source=*metrics.log group=per_sourcetype_thruput")
    print(f"            | stats sum(kb) as total_kb by series | sort - total_kb")
    print(f"\n  Since nobody will search for these sourcetypes, the agent will")
    print(f"  detect them as wasteful when it runs.\n")

    return True


if __name__ == "__main__":
    # Load .env
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")

    load_synthetic_data()
