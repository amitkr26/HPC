"""Exercise 9 - Parallel Speedup Analyzer.

Measures the parallel performance of a Monte Carlo pi estimation and
reports time, speedup, efficiency, Amdahl's and Gustafson's theoretical
speedups for 1, 2, 4, ... workers.
"""

import multiprocessing
import os
import random
import time

NUM_SAMPLES = 5_000_000
WORKER_COUNTS = sorted({1, 2, 4, 8, os.cpu_count() or 1})
REPEATS = 3
SERIAL_FRACTION = 0.03


def monte_carlo_pi(num_samples):
    """Return how many random points of ``num_samples`` fall inside the unit circle."""
    inside = 0
    for _ in range(num_samples):
        x = random.random()
        y = random.random()
        if x * x + y * y <= 1.0:
            inside += 1
    return inside


def sequential_baseline(samples):
    """Time a plain single-process run and return (seconds, pi estimate)."""
    start = time.perf_counter()
    inside = monte_carlo_pi(samples)
    elapsed = time.perf_counter() - start
    return elapsed, 4 * inside / samples


def parallel_run(workers, samples):
    """Split ``samples`` across ``workers`` processes and average over REPEATS runs.

    The pool is created before timing so the measurements cover the
    parallel computation itself rather than process startup.
    """
    per_worker = samples // workers
    times, estimates = [], []
    with multiprocessing.Pool(workers) as pool:
        for _ in range(REPEATS):
            start = time.perf_counter()
            counts = pool.map(monte_carlo_pi, [per_worker] * workers)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            estimates.append(4 * sum(counts) / (per_worker * workers))
    return sum(times) / len(times), sum(estimates) / len(estimates)


def amdahl_speedup(n, s=SERIAL_FRACTION):
    """Theoretical speedup 1 / (S + (1-S)/N)."""
    return 1.0 / (s + (1 - s) / n)


def gustafson_speedup(n, s=SERIAL_FRACTION):
    """Scaled speedup N - S x (N - 1)."""
    return n - s * (n - 1)


def print_table(rows, estimates):
    """Print the timing table plus the pi estimate from each run."""
    header = f"{'Workers':>7}  {'Time(s)':>7}  {'Speedup':>7}  {'Efficiency':>10}  {'Amdahl':>7}  {'Gustafson':>9}"
    print(header)
    print("─" * len(header))
    for workers, elapsed, speedup, estimate in rows:
        efficiency = speedup / workers * 100
        print(f"{workers:>7}  {elapsed:>7.3f}  {speedup:>7.2f}  "
              f"{efficiency:>9.1f}%  {amdahl_speedup(workers):>7.2f}  "
              f"{gustafson_speedup(workers):>9.2f}")
    print("\npi estimates:")
    for workers, _, _, estimate in rows:
        print(f"  N={workers:>2}: {estimate:.5f} "
              f"(error {abs(estimate - 3.14159265):.5f})")
    print(f"  sequential: {estimates:.5f} "
          f"(error {abs(estimates - 3.14159265):.5f})")


def main():
    """Measure sequential and parallel runs and print the analysis table."""
    print(f"Workload : monte_carlo_pi({NUM_SAMPLES:,}) per configuration")
    print(f"Repeats  : {REPEATS} averaged per configuration")
    print(f"Cores    : {os.cpu_count()}")
    print(f"Serial fraction for Amdahl/Gustafson: {SERIAL_FRACTION:.0%}")
    print("Note: pool startup is excluded from the parallel timings "
          "(the map call is what is measured).")

    seq_time, seq_pi = sequential_baseline(NUM_SAMPLES)
    print(f"\nSequential baseline: {seq_time:.3f} s, pi = {seq_pi:.5f}")

    rows = []
    for workers in WORKER_COUNTS:
        elapsed, estimate = parallel_run(workers, NUM_SAMPLES)
        rows.append((workers, elapsed, seq_time / elapsed, estimate))
        print(f"  N={workers:>2}: {elapsed:.3f} s, pi = {estimate:.5f}")

    print()
    print_table(rows, seq_pi)
    print("\nEfficiency = Speedup / N; Amdahl uses S=3%; "
          "Gustafson = N - S*(N-1).")


if __name__ == "__main__":
    main()
