"""Exercise 10 - Build Your Own Parallel Toolkit.

A cohesive data-processing pipeline: JSON config in -> parallel process
pool -> Pickle results out -> performance report with speedup and
efficiency.
"""

import json
import multiprocessing
import os
import pickle
import time

TASKS_FILE = "tasks.json"
RESULTS_FILE = "results.pkl"
REQUIRED_KEYS = ("id", "operation", "n")
TASKS = [
    {"id": 1, "operation": "sum_of_squares", "n": 2000000},
    {"id": 2, "operation": "sum_of_squares", "n": 3000000},
    {"id": 3, "operation": "sum_of_squares", "n": 1500000},
    {"id": 4, "operation": "sum_of_squares", "n": 2500000},
    {"id": 5, "operation": "sum_of_squares", "n": 1000000},
    {"id": 6, "operation": "sum_of_squares", "n": 3500000},
]


def create_tasks_file(path):
    """Write the task list to ``path`` as JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(TASKS, f, indent=4)
    print(f"Created {path} with {len(TASKS)} tasks")


def load_tasks(path):
    """Read and validate the task list from ``path``."""
    with open(path, "r", encoding="utf-8") as f:
        tasks = json.load(f)
    for task in tasks:
        missing = [key for key in REQUIRED_KEYS if key not in task]
        if missing:
            raise ValueError(f"Task {task} is missing keys: {missing}")
    print(f"Loaded {len(tasks)} tasks from {path}")
    return tasks


def execute_task(task):
    """Execute a single task and return the result."""
    start = time.time()
    result = sum(i * i for i in range(task["n"]))
    elapsed = time.time() - start
    return {
        "id": task["id"],
        "n": task["n"],
        "result": result,
        "time": round(elapsed, 4)
    }


def save_results(results, path):
    """Pickle the result dictionaries to ``path``."""
    with open(path, "wb") as f:
        pickle.dump(results, f)
    print(f"Saved {len(results)} results to {path}")


def load_results(path):
    """Read the pickled result list back from ``path``."""
    with open(path, "rb") as f:
        return pickle.load(f)


def print_task_table(results, heading):
    """Print ID, n, result and per-task execution time."""
    print(f"\n--- {heading} ---")
    print(f"  {'ID':>2}  {'n':>9}  {'Result':>20}  {'Time(s)':>8}")
    print(f"  {'-' * 2}  {'-' * 9}  {'-' * 20}  {'-' * 8}")
    for r in results:
        print(f"  {r['id']:>2}  {r['n']:>9}  {r['result']:>20}  "
              f"{r['time']:>8.4f}")


def print_performance(seq_time, par_time, workers):
    """Print totals, speedup and efficiency after correctness is verified."""
    speedup = seq_time / par_time
    efficiency = speedup / workers * 100
    print("\n--- Performance ---")
    print(f"  Sequential time : {seq_time:.4f} s")
    print(f"  Parallel time   : {par_time:.4f} s  ({workers} workers)")
    print(f"  Speedup         : {speedup:.2f}x")
    print(f"  Efficiency      : {efficiency:.1f}%")


def main():
    """Run the full load -> process -> save -> report pipeline."""
    create_tasks_file(TASKS_FILE)
    tasks = load_tasks(TASKS_FILE)

    start = time.perf_counter()
    sequential_results = [execute_task(t) for t in tasks]
    seq_time = time.perf_counter() - start

    workers = min(len(tasks), multiprocessing.cpu_count() or 1)
    start = time.perf_counter()
    with multiprocessing.Pool(workers) as pool:
        parallel_results = pool.map(execute_task, tasks)
    par_time = time.perf_counter() - start

    print_task_table(sequential_results, "Sequential results")
    print_task_table(parallel_results, "Parallel results")

    matches = ([r["result"] for r in sequential_results]
               == [r["result"] for r in parallel_results])
    print(f"\nVerification: sequential and parallel results match: {matches}")

    save_results(parallel_results, RESULTS_FILE)
    reloaded = load_results(RESULTS_FILE)
    print(f"Reloaded {len(reloaded)} results from {RESULTS_FILE} - "
          f"ids: {[r['id'] for r in reloaded]}")

    if matches:
        print_performance(seq_time, par_time, workers)
    else:
        print("Results do not match - speedup not reported.")

    print("\nWorkflow: tasks.json (human-readable config in) -> "
          "process pool -> results.pkl (machine-efficient results out).")


if __name__ == "__main__":
    main()
