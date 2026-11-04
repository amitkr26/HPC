"""Exercise 3: High-Level Concurrency with ThreadPoolExecutor.

Fetches 10 simulated endpoints concurrently with ThreadPoolExecutor(5),
maps each Future back to its URL, iterates with as_completed() to print byte
sizes for successes, catches ConnectionError from ``.error`` URLs without
crashing, and applies a per-task timeout of future.result(timeout=1.0) so an
endpoint that is still in flight after the 1.0 s harvest window is aborted.

Run with:  python ex03_futures_downloader.py
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

# (url, simulated latency in seconds) - delays span 0.2 .. 1.5 seconds
ENDPOINTS = [
    ("https://api.example.com/users.json", 0.2),
    ("https://api.example.com/orders.json", 0.35),
    ("https://api.example.com/products.json", 0.5),
    ("https://api.example.com/inventory.error", 0.4),
    ("https://api.example.com/payments.json", 0.6),
    ("https://api.example.com/reviews.error", 0.5),
    ("https://api.example.com/catalog.json", 0.45),
    ("https://api.example.com/profile.json", 0.25),
    ("https://api.example.com/notifications.json", 0.3),
    ("https://api.example.com/search.json", 1.5),
]

LATENCY = {url: delay for url, delay in ENDPOINTS}
TIMEOUT = 1.0


def download_endpoint(url):
    """Simulate fetching *url*: sleep for the latency, raise on ``.error``."""
    time.sleep(LATENCY[url])
    if url.endswith(".error"):
        raise ConnectionError(f"failed to connect to {url}")
    return f"<html><body>payload for {url}</body></html>"


def report_ok(url, payload, counters):
    """Record and print a successful download."""
    counters["ok"] += 1
    print(f"  OK       {url} -> {len(payload)} bytes")


def report_error(url, exc, counters):
    """Record and print a handled connection error."""
    counters["failed"] += 1
    print(f"  ERROR    {url} -> {exc}")


def main():
    """Submit all endpoints, harvest with as_completed, time out stragglers."""
    counters = {"ok": 0, "failed": 0, "timed_out": 0}
    print(f"Submitting {len(ENDPOINTS)} endpoints to ThreadPoolExecutor(max_workers=5)\n")

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(download_endpoint, url): url
                         for url, _ in ENDPOINTS}

        # Harvest everything that finishes within the 1.0 s per-task budget.
        handled = set()
        try:
            for future in as_completed(future_to_url, timeout=TIMEOUT):
                handled.add(future)
                url = future_to_url[future]
                try:
                    payload = future.result(timeout=TIMEOUT)
                except ConnectionError as exc:
                    report_error(url, exc, counters)
                else:
                    report_ok(url, payload, counters)
        except TimeoutError:
            print(f"  ...harvest window of {TIMEOUT}s closed, "
                  "applying per-task timeouts to pending futures\n")

        # Per-task timeout for anything still in flight.
        for future, url in future_to_url.items():
            if future in handled:
                continue
            try:
                payload = future.result(timeout=TIMEOUT)
            except TimeoutError:
                counters["timed_out"] += 1
                print(f"  TIMEOUT  {url} (no response within {TIMEOUT}s) "
                      "-> aborted")
                future.cancel()
            except ConnectionError as exc:
                report_error(url, exc, counters)
            else:
                report_ok(url, payload, counters)

    print(f"\nSummary: {counters['ok']} downloaded, "
          f"{counters['failed']} connection errors, "
          f"{counters['timed_out']} timed out (of {len(ENDPOINTS)})")


if __name__ == "__main__":
    main()
