"""Exercise 5: Asynchronous Process Pool with Result Callbacks.

Submits 8 tasks to a multiprocessing.Pool with apply_async() callbacks while
the main process keeps running a lightweight dot ticker, proving it is not
blocked by the workers.
"""

import hashlib
import multiprocessing as mp
import random
import threading
import time

NUM_TASKS = 8

completed_records = []
records_lock = None  # created in main before the pool starts


def process_record(record_id, data_chunk):
    """CPU-bound worker: sort, hash and summarise one data chunk."""
    time.sleep(random.uniform(0.3, 0.9))
    sorted_chunk = sorted(data_chunk)
    digest = hashlib.sha256(
        ",".join(str(x) for x in sorted_chunk).encode("utf-8")
    ).hexdigest()[:16]
    return {
        "record_id": record_id,
        "processed_elements": len(data_chunk),
        "checksum": sum(data_chunk),
        "sha256_16": digest,
    }


def make_collect_result(lock):
    """Build a lightweight callback that appends results and prints progress."""

    def collect_result(result):
        with lock:
            completed_records.append(result)
            count = len(completed_records)
        print(f"\n[callback] record {result['record_id']} done "
              f"({count}/{NUM_TASKS} collected)")

    return collect_result


def log_error(err):
    """Error callback: never let a child-process failure pass silently."""
    print(f"\n[error_callback] worker failed: {err!r}")


def main():
    global completed_records, records_lock
    completed_records = []
    records_lock = threading.Lock()

    print("=" * 70)
    print(f"Pool of {mp.cpu_count()} CPUs, {NUM_TASKS} async tasks, "
          f"0.1s main-process ticker")
    print("=" * 70)

    random.seed(7)
    chunks = [
        (i, [random.randint(1, 1000) for _ in range(5000)])
        for i in range(1, NUM_TASKS + 1)
    ]

    collect_result = make_collect_result(records_lock)

    with mp.Pool() as pool:
        async_results = [
            pool.apply_async(process_record, args=(rid, chunk),
                             callback=collect_result,
                             error_callback=log_error)
            for rid, chunk in chunks
        ]

        print("[main] ticker running while workers compute: ", end="",
              flush=True)
        ticks = 0
        while not all(r.ready() for r in async_results):
            print(".", end="", flush=True)
            ticks += 1
            time.sleep(0.1)
        print(f"  ({ticks} ticks / {ticks * 0.1:.1f}s elapsed)")

        for r in async_results:
            r.get()

        pool.close()
        pool.join()

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    assert len(completed_records) == NUM_TASKS, (
        f"Expected {NUM_TASKS} results, got {len(completed_records)}"
    )
    for rec in sorted(completed_records, key=lambda r: r["record_id"]):
        print(f"  record {rec['record_id']}: "
              f"elements={rec['processed_elements']}, "
              f"checksum={rec['checksum']}, sha256={rec['sha256_16']}")
    total_elements = sum(r["processed_elements"] for r in completed_records)
    print(f"ASSERT OK: {len(completed_records)} records collected via "
          f"callbacks, {total_elements} elements processed in total.")
    print("The dot ticker proved the main process stayed responsive while "
          "the pool worked.")


if __name__ == "__main__":
    main()
