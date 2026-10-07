"""Exercise 1: Distributed Scientific Computing with SCOOP.

Monte-Carlo estimation of the definite integral

        I = integral of sin(x) * exp(-x) dx   for x in [0, pi]

The rectangle [0, pi] x [0, 1] is a bounding box of area pi, so every random
point that lands under the curve is a "hit" and

        I ~= box_area * hits / total_samples

The total workload (10,000,000 evaluations) is split into 16 discrete task
chunks that are shipped to every available worker with scoop.futures.map().
The same chunk list is then replayed sequentially in a plain for loop so the
two elapsed times can be compared.

Run distributed :  python -m scoop ex01_scoop_monte_carlo.py [total] [chunks]
Run sequential  :  python ex01_scoop_monte_carlo.py [total] [chunks]
                   (needs scoop installed; without -m scoop everything runs
                    inside the launching process)
"""

import math
import os
import random
import sys
import time

from scoop import futures

TOTAL_EVALUATIONS = 10_000_000
NUM_CHUNKS = 16

X_MIN = 0.0
X_MAX = math.pi
Y_MAX = 1.0
BOX_AREA = (X_MAX - X_MIN) * Y_MAX
ANALYTIC_VALUE = 0.5 * (1.0 + math.exp(-math.pi))


def evaluate_subrange(subrange_id, samples_count):
    # Perform heavy mathematical simulation for samples_count iterations
    # Example: Monte Carlo estimation of points under curve y = sin(x) * exp(-x)
    rng = random.Random(1_000_003 * (subrange_id + 1))
    hits = 0
    for _ in range(samples_count):
        x = rng.uniform(X_MIN, X_MAX)
        y = rng.random() * Y_MAX
        if y <= math.sin(x) * math.exp(-x):
            hits += 1
    print(
        f"[pid {os.getpid():6}] chunk {subrange_id:2}: "
        f"{samples_count:,} samples -> {hits:,} hits"
    )
    return {"subrange_id": subrange_id, "hits": hits, "total": samples_count}


def evaluate_chunk(task):
    """Module-level adapter so map() can consume a single iterable of tuples."""
    subrange_id, samples_count = task
    return evaluate_subrange(subrange_id, samples_count)


def build_workload(total_evaluations, num_chunks):
    """Split total_evaluations into num_chunks nearly equal (id, size) pairs."""
    if num_chunks <= 0:
        raise ValueError("num_chunks must be positive")
    if total_evaluations <= 0:
        raise ValueError("total_evaluations must be positive")
    base, extra = divmod(total_evaluations, num_chunks)
    return [
        (chunk_id, base + (1 if chunk_id < extra else 0))
        for chunk_id in range(num_chunks)
    ]


def aggregate(results):
    """Fold the partial worker results into hits, samples and the estimate."""
    total_hits = sum(entry["hits"] for entry in results)
    total_samples = sum(entry["total"] for entry in results)
    estimate = BOX_AREA * total_hits / total_samples
    return total_hits, total_samples, estimate


def report(label, elapsed, hits, samples, estimate):
    """Print timing, estimate and error against the analytic value."""
    error = estimate - ANALYTIC_VALUE
    relative = abs(error) / abs(ANALYTIC_VALUE)
    print(f"[{label}] elapsed time : {elapsed:.3f} s")
    print(f"[{label}] hits/samples : {hits:,} / {samples:,}")
    print(f"[{label}] estimate     : {estimate:.6f}")
    print(f"[{label}] analytic     : {ANALYTIC_VALUE:.6f}")
    print(f"[{label}] abs error    : {abs(error):.6f}   rel error: {relative:.2%}")


def parse_cli(argv):
    """Read optional [total_samples] [num_chunks] overrides from the command line."""
    try:
        total = int(argv[1]) if len(argv) >= 2 else TOTAL_EVALUATIONS
        num_chunks = int(argv[2]) if len(argv) >= 3 else NUM_CHUNKS
        build_workload(total, num_chunks)
    except ValueError:
        print(f"Usage: {argv[0]} [total_samples:int] [num_chunks:int]")
        sys.exit(2)
    return total, num_chunks


def main():
    """Split the workload, run it distributed, then replay it sequentially."""
    total, num_chunks = parse_cli(sys.argv)
    workload = build_workload(total, num_chunks)
    print(f"Workload: {total:,} evaluations split into {num_chunks} chunks")
    print(f"Bounding box area: {BOX_AREA:.6f}")

    print("\n--- DISTRIBUTED RUN (scoop.futures.map) ---")
    start = time.perf_counter()
    results = list(futures.map(evaluate_chunk, workload))
    distributed_elapsed = time.perf_counter() - start
    hits, samples, estimate = aggregate(results)
    report("distributed", distributed_elapsed, hits, samples, estimate)

    print("\n--- SEQUENTIAL RUN (plain for loop) ---")
    start = time.perf_counter()
    sequential_results = []
    for task in workload:
        sequential_results.append(evaluate_chunk(task))
    sequential_elapsed = time.perf_counter() - start
    seq_hits, seq_samples, seq_estimate = aggregate(sequential_results)
    report("sequential ", sequential_elapsed, seq_hits, seq_samples, seq_estimate)

    print("\n--- COMPARISON ---")
    if distributed_elapsed > 0:
        print(
            f"speedup (sequential / distributed) = "
            f"{sequential_elapsed / distributed_elapsed:.2f}x"
        )
    else:
        print("speedup (sequential / distributed) = n/a (distributed run was instant)")


if __name__ == "__main__":
    main()
