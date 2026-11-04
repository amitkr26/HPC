"""Exercise 2: Connection Pool Rate-Limiter with Semaphores.

A threading.Semaphore(3) limits a simulated database connection pool to three
concurrent connections while 10 worker threads compete for slots.
"""

import random
import threading
import time

MAX_CONNECTIONS = 3
NUM_WORKERS = 10

semaphore = threading.Semaphore(MAX_CONNECTIONS)

state_lock = threading.Lock()
active_connections = 0
peak_connections = 0


def worker(worker_id):
    """Simulate one customer request using at most one pool slot."""
    global active_connections, peak_connections

    with semaphore:
        with state_lock:
            active_connections += 1
            peak_connections = max(peak_connections, active_connections)
            active = active_connections
        remaining = semaphore._value
        print(f"[Worker {worker_id}] Connected to Database "
              f"(active slots: {active}, free slots: {remaining})")

        query_time = random.uniform(0.3, 0.8)
        time.sleep(query_time)

        print(f"[Worker {worker_id}] Finished query "
              f"({query_time:.2f}s), releasing connection")
        with state_lock:
            active_connections -= 1


def main():
    print("=" * 70)
    print("Connection pool: 3 slots, 10 workers, queries of 0.3-0.8s")
    print("=" * 70)

    threads = [
        threading.Thread(target=worker, args=(i,), name=f"worker-{i}")
        for i in range(1, NUM_WORKERS + 1)
    ]
    start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - start

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Workers served                 : {NUM_WORKERS}")
    print(f"Peak concurrent connections    : {peak_connections} "
          f"(limit {MAX_CONNECTIONS})")
    print(f"Total elapsed time             : {elapsed:.2f}s")
    assert peak_connections <= MAX_CONNECTIONS, "Semaphore limit was violated!"
    assert peak_connections == MAX_CONNECTIONS, "Pool never saturated."
    print("ASSERT OK: never more than 3 workers held a connection at once, "
          "and the pool did reach full capacity.")


if __name__ == "__main__":
    main()
