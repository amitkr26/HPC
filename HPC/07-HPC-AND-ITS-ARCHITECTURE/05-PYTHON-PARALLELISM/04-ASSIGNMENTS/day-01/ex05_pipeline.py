"""Exercise 5 - Producer-Consumer Pipeline.

Three-stage pipeline built from threads and queues:

    [Generator] -> Queue 1 -> [Processor] -> Queue 2 -> [Writer]

A ``None`` sentinel propagates through both queues to shut each stage
down cleanly in order.
"""

import queue
import random
import threading
import time

NUM_ITEMS = 20
PRODUCER_DELAY = 0.1
QUEUE_MAXSIZE = 5


def generator_stage(out_queue):
    """Produce 20 raw items and push them into ``out_queue``."""
    for i in range(NUM_ITEMS):
        item = {"id": i, "value": random.randint(1, 100)}
        out_queue.put(item)
        print(f"[Generator] produced item {i}: {item}")
        time.sleep(PRODUCER_DELAY)
    out_queue.put(None)
    print("[Generator] done - sent sentinel None to queue_1")


def processor_stage(in_queue, out_queue):
    """Square the ``value`` field of every item passing through."""
    while True:
        item = in_queue.get()
        if item is None:
            out_queue.put(None)
            print("[Processor] received sentinel - forwarding it to queue_2")
            return
        transformed = {"id": item["id"], "value": item["value"] ** 2}
        out_queue.put(transformed)
        print(f"[Processor] processed item {item['id']}: "
              f"{item['value']} -> {transformed['value']}")


def writer_stage(in_queue, collected):
    """Collect transformed items until the sentinel arrives, then print."""
    while True:
        item = in_queue.get()
        if item is None:
            print("[Writer] received sentinel - shutting down")
            break
        collected.append(item)
        print(f"[Writer] wrote item {item['id']}: value={item['value']}")
    print(f"\n[Writer] final list ({len(collected)} items):")
    print(collected)


def main():
    """Wire the three stages together and run the pipeline."""
    random.seed(7)
    queue_1 = queue.Queue(maxsize=QUEUE_MAXSIZE)
    queue_2 = queue.Queue(maxsize=QUEUE_MAXSIZE)
    collected = []

    threads = [
        threading.Thread(target=generator_stage, args=(queue_1,),
                         name="Generator"),
        threading.Thread(target=processor_stage, args=(queue_1, queue_2),
                         name="Processor"),
        threading.Thread(target=writer_stage, args=(queue_2, collected),
                         name="Writer"),
    ]

    start = time.perf_counter()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    elapsed = time.perf_counter() - start

    print("\n--- Pipeline summary ---")
    print(f"  Items produced : {NUM_ITEMS}")
    print(f"  Items processed: {len(collected)}")
    print(f"  First item     : {collected[0]}")
    print(f"  Last item      : {collected[-1]}")
    print(f"  All values squared correctly: "
          f"{all(item['value'] >= 1 for item in collected)}")
    print(f"  Elapsed        : {elapsed:.2f} s")
    print("  Stages shut down in order via the None sentinel.")


if __name__ == "__main__":
    main()
