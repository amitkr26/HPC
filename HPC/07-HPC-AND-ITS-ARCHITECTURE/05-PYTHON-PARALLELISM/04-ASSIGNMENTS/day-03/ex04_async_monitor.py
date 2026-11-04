"""Exercise 4: Cooperative Concurrency with asyncio.

Three health-check coroutines (database 0.4s, cache 0.2s, storage 0.6s) are
launched concurrently with asyncio.gather() on a single-threaded event loop.
The total wall-clock time must be close to the slowest check (~0.6s) rather
than the sequential sum (1.2s).

Run with:  python ex04_async_monitor.py
"""

import asyncio
import time

SEQUENTIAL_SUM = 0.4 + 0.2 + 0.6
SLOWEST = 0.6


async def check_database():
    """Simulate a 0.4 s database health probe."""
    await asyncio.sleep(0.4)
    return {"db": "HEALTHY", "latency_ms": 12}


async def check_redis_cache():
    """Simulate a 0.2 s cache health probe."""
    await asyncio.sleep(0.2)
    return {"cache": "HEALTHY", "latency_ms": 4}


async def check_storage_service():
    """Simulate a 0.6 s storage health probe."""
    await asyncio.sleep(0.6)
    return {"storage": "HEALTHY", "latency_ms": 28}


async def run_health_checks():
    """Run all probes concurrently and verify the concurrency benefit."""
    print("Launching 3 health checks concurrently with asyncio.gather() ...")
    start = time.perf_counter()

    results = await asyncio.gather(
        check_database(),
        check_redis_cache(),
        check_storage_service(),
    )

    elapsed = time.perf_counter() - start

    print("\nResults:")
    for result in results:
        service = next(key for key in result if key != "latency_ms")
        print(f"  {service:<10} : {result[service]} "
              f"(latency_ms={result['latency_ms']})")

    print(f"\nSequential sum would be : {SEQUENTIAL_SUM:.2f}s")
    print(f"Slowest single check    : {SLOWEST:.2f}s")
    print(f"Concurrent elapsed time : {elapsed:.3f}s")

    within_bound = elapsed < SEQUENTIAL_SUM - 0.1
    matches_slowest = abs(elapsed - SLOWEST) < 0.15
    print(f"\nCheck: elapsed < sequential sum (1.2s)      -> "
          f"{'PASS' if within_bound else 'FAIL'}")
    print(f"Check: elapsed ~ slowest check (0.6s)       -> "
          f"{'PASS' if matches_slowest else 'FAIL'}")
    print("Conclusion: checks ran concurrently on one event loop, "
          "not sequentially.")
    return within_bound and matches_slowest


def main():
    """Drive the top-level coroutine with asyncio.run()."""
    ok = asyncio.run(run_health_checks())
    if not ok:
        raise SystemExit("timing verification failed")


if __name__ == "__main__":
    main()
