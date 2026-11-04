"""Exercise 3: Phased Multi-Stage Execution with threading.Barrier.

Four worker threads compute local values in phase 1, rendezvous at a
threading.Barrier(4), then aggregate globally in phase 2.
"""

import random
import threading

NUM_THREADS = 4

data = [0] * NUM_THREADS
barrier = threading.Barrier(NUM_THREADS)
phase2_started = threading.Event()


def worker(index):
    """Run phase 1 (local computation) then phase 2 (global aggregation)."""
    try:
        data[index] = random.randint(1, 50)
        print(f"[Thread {index}] Phase 1 complete, waiting at barrier... "
              f"(local value = {data[index]})")

        barrier.wait()

        if not phase2_started.is_set():
            phase2_started.set()
            print("-" * 70)
            print(f"all {NUM_THREADS} threads passed the barrier -> "
                  f"data = {data}")
            print("-" * 70)

        total = sum(data)
        share = data[index] / total * 100
        print(f"[Thread {index}] Share of total: {share:.2f}% "
              f"(value {data[index]} of {total})")
    except threading.BrokenBarrierError:
        print(f"[Thread {index}] Barrier broken - aborting phase 2.")


def main():
    print("=" * 70)
    print(f"{NUM_THREADS} threads, 2 phases, threading.Barrier({NUM_THREADS})")
    print("=" * 70)

    threads = [
        threading.Thread(target=worker, args=(i,), name=f"thread-{i}")
        for i in range(NUM_THREADS)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(10.0)

    hung = [t.name for t in threads if t.is_alive()]
    assert not hung, f"Threads hung at the barrier: {hung}"

    total = sum(data)
    shares = [v / total * 100 for v in data]
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"data             : {data} (sum = {total})")
    print(f"phase-2 shares % : {[round(s, 2) for s in shares]}")
    assert abs(sum(shares) - 100.0) < 1e-9, "Shares do not add up to 100%!"
    print("ASSERT OK: all 4 threads aligned at the barrier and shares sum "
          "to 100%.")


if __name__ == "__main__":
    main()
