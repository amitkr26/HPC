"""Exercise 5: Bridging Asyncio with CPU-Heavy Workloads.

A background heartbeat task ticks every 0.25 s while a heavy synchronous
fibonacci_cpu(35) is offloaded to the default thread pool executor via
loop.run_in_executor(), so the single-threaded event loop keeps ticking.
The heartbeat is cancelled cleanly with task.cancel() afterwards.

Run with:  python ex05_async_cpu_bridge.py
"""

import asyncio
import contextlib
import time

HEARTBEAT_INTERVAL = 0.25
FIB_N = 35


async def heartbeat_ticker():
    """Print a heartbeat every 0.25 s until cancelled cleanly."""
    ticks = 0
    try:
        while True:
            ticks += 1
            print(f"[Heartbeat {ticks}] Active and responsive...", flush=True)
            await asyncio.sleep(HEARTBEAT_INTERVAL)
    except asyncio.CancelledError:
        print(f"[Heartbeat] Cancelled cleanly after {ticks} ticks - "
              "shutting down.")
        raise


def fibonacci_cpu(n):
    """Compute the n-th Fibonacci number with heavy recursive CPU work."""
    if n < 2:
        return n
    return fibonacci_cpu(n - 1) + fibonacci_cpu(n - 2)


async def main():
    """Run the heartbeat alongside the offloaded CPU computation."""
    print(f"Starting heartbeat (every {HEARTBEAT_INTERVAL}s) and "
          f"offloading fibonacci_cpu({FIB_N}) to the thread pool executor.\n")

    heartbeat_task = asyncio.create_task(heartbeat_ticker())

    loop = asyncio.get_running_loop()
    start = time.perf_counter()
    result = await loop.run_in_executor(None, fibonacci_cpu, FIB_N)
    elapsed = time.perf_counter() - start

    heartbeat_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await heartbeat_task

    print(f"\nfibonacci_cpu({FIB_N}) = {result:,}")
    print(f"CPU computation took {elapsed:.3f}s while the event loop "
          "kept serving the heartbeat.")
    print(f"fib({FIB_N}) correct : {result == 9227465}")
    print("Heartbeat task cancelled and awaited: no pending-task warning.")


if __name__ == "__main__":
    asyncio.run(main())
