"""Exercise 3 - Parallel File Word Counter.

Counts words in 6 generated text files both sequentially and in parallel
with multiprocessing.Pool, then reports timings and speedup.
"""

import multiprocessing
import os
import random
import time

SAMPLE_WORDS = ["python", "parallel", "computing", "process", "thread",
                "memory", "data", "algorithm", "performance", "speedup"]
NUM_FILES = 6
WORDS_PER_FILE = 8000
SLOW_READ_DELAY = 0.5


def count_words(filepath):
    """Return ``(filepath, word_count)`` after a simulated slow read."""
    time.sleep(SLOW_READ_DELAY)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return filepath, len(content.split())


def generate_files():
    """Create file_0.txt .. file_5.txt and return their paths."""
    paths = []
    for i in range(NUM_FILES):
        path = f"file_{i}.txt"
        content = " ".join(random.choices(SAMPLE_WORDS, k=WORDS_PER_FILE))
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        paths.append(path)
    return paths


def print_results(rows, heading):
    """Print a per-file word-count table."""
    print(f"\n--- {heading} ---")
    print(f"  {'File':<12} {'Words':>8}")
    print(f"  {'-' * 12} {'-' * 8}")
    for path, count in rows:
        print(f"  {path:<12} {count:>8}")
    total = sum(c for _, c in rows)
    print(f"  {'TOTAL':<12} {total:>8}")


def main():
    """Generate data, run sequentially and in parallel, compare, clean up."""
    paths = generate_files()
    print(f"Generated {len(paths)} test files with {WORDS_PER_FILE} words each")

    start = time.time()
    sequential = [count_words(p) for p in paths]
    seq_time = time.time() - start
    print(f"\nSequential run: {seq_time:.4f} s")

    start = time.time()
    with multiprocessing.Pool() as pool:
        parallel = pool.map(count_words, paths)
    par_time = time.time() - start
    print(f"Parallel run  : {par_time:.4f} s  "
          f"({multiprocessing.cpu_count()} workers)")

    print_results(sequential, "Sequential results")
    print_results(parallel, "Parallel results")

    print("\nVerification:")
    print(f"  Results identical: {sorted(sequential) == sorted(parallel)}")

    speedup = seq_time / par_time if par_time else float("inf")
    print(f"\nSpeedup = {seq_time:.4f} / {par_time:.4f} = {speedup:.2f}x")
    print("(Each worker sleeps 0.5 s to simulate a slow disk, which is what "
          "makes the parallel run win.)")

    for path in paths:
        if os.path.exists(path):
            os.remove(path)
    print(f"\nCleaned up {len(paths)} generated test files")


if __name__ == "__main__":
    main()
