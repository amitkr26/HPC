"""Exercise 6 - GIL Impact Experiment.

Empirically demonstrates the Global Interpreter Lock by running a
CPU-bound workload (naive fibonacci) and an I/O-bound workload
(simulated download) in sequential, threaded and multiprocess modes.
"""

import multiprocessing
import random
import threading
import time


def fibonacci(n):
    """Naive recursive Fibonacci - intentionally slow and CPU-bound."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def download_simulation(url_id):
    """Simulate a network download with a random 0.5-1.5 s delay."""
    time.sleep(random.uniform(0.5, 1.5))
    return f"data_from_{url_id}"


def benchmark(func, args_list, mode):
    """Run ``func`` over ``args_list`` in ``mode`` and return elapsed time."""
    start = time.perf_counter()
    if mode == "sequential":
        for args in args_list:
            func(args)
    elif mode == "threaded":
        threads = [threading.Thread(target=func, args=(args,))
                   for args in args_list]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    elif mode == "multiprocess":
        processes = [multiprocessing.Process(target=func, args=(args,))
                     for args in args_list]
        for process in processes:
            process.start()
        for process in processes:
            process.join()
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return time.perf_counter() - start


def print_table(title, rows):
    """Print a timing table with speedups relative to the baseline."""
    print(f"\n=== {title} ===")
    print(f"  {'Mode':<14} {'Time(s)':>9} {'Speedup':>9}")
    print(f"  {'-' * 14} {'-' * 9} {'-' * 9}")
    baseline = rows[0][1]
    for mode, elapsed in rows:
        print(f"  {mode:<14} {elapsed:>9.3f} {baseline / elapsed:>8.2f}x")


def main():
    """Benchmark both workloads across all three concurrency modes."""
    cpu_args = [30] * 4
    io_args = list(range(8))
    modes = ["sequential", "threaded", "multiprocess"]

    print(f"CPU-bound : fibonacci(30) x {len(cpu_args)}")
    print(f"I/O-bound : download_simulation(i) for i in range({len(io_args)})")
    print(f"Machine   : {multiprocessing.cpu_count()} CPUs")

    cpu_rows, io_rows = [], []
    for mode in modes:
        cpu_rows.append((mode, benchmark(fibonacci, cpu_args, mode)))
        io_rows.append((mode, benchmark(download_simulation, io_args, mode)))

    print_table("CPU-bound (fibonacci) - GIL serialises the threads",
                cpu_rows)
    print_table("I/O-bound (download) - threads release the GIL while "
                "sleeping", io_rows)

    cpu_seq, cpu_thr, cpu_proc = [t for _, t in cpu_rows]
    io_seq, io_thr, io_proc = [t for _, t in io_rows]
    print("\nObserved conclusions:")
    print(f"  CPU-bound : threads give no speedup "
          f"({cpu_seq / cpu_thr:.2f}x - the GIL serialises them, and "
          f"contention can make them slower than sequential), processes "
          f"give {cpu_seq / cpu_proc:.2f}x.")
    print(f"  I/O-bound : threads ({io_seq / io_thr:.2f}x) and processes "
          f"({io_seq / io_proc:.2f}x) both beat sequential because the "
          f"GIL is released while sleeping.")


if __name__ == "__main__":
    main()
