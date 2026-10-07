"""Exercise 4: Multi-Stage Inter-Process Pipeline (Queue & Pipe).

    [Producer] --(Queue)--> [Filter] --(Pipe)--> [Writer]

The producer pushes 15 random integers plus a None sentinel into a
multiprocessing.Queue, the filter keeps only even numbers and forwards them
(plus the sentinel) over a Pipe, and the writer collects them.
"""

import multiprocessing as mp
import random


def producer(queue, count=15):
    """Generate random integers, push them into the Queue, then a sentinel."""
    values = [random.randint(1, 100) for _ in range(count)]
    print(f"[Producer] generated {count} integers: {values}")
    for value in values:
        queue.put(value)
    queue.put(None)
    print("[Producer] sentinel (None) pushed to the Queue - done.")


def filter_stage(queue, conn):
    """Read from the Queue, keep evens, send them through the Pipe."""
    kept = []
    while True:
        item = queue.get()
        if item is None:
            conn.send(None)
            print(f"[Filter] sentinel received; forwarded {len(kept)} even "
                  f"numbers through the Pipe.")
            break
        if item % 2 == 0:
            conn.send(item)
            kept.append(item)
            print(f"[Filter] {item} is even -> sent through Pipe")
        else:
            print(f"[Filter] {item} is odd  -> discarded")
    conn.close()


def writer(conn):
    """Collect filtered numbers from the Pipe until the sentinel arrives."""
    collected = []
    while True:
        value = conn.recv()
        if value is None:
            print(f"[Writer] sentinel received; terminating. "
                  f"Accepted {len(collected)} values.")
            break
        collected.append(value)
        print(f"[Writer] accepted: {value}")
    conn.close()
    print(f"[Writer] final list: {collected}")
    return collected


def main():
    print("=" * 70)
    print("3-process pipeline: Producer -(Queue)-> Filter -(Pipe)-> Writer")
    print("=" * 70)

    queue = mp.Queue()
    filter_conn, writer_conn = mp.Pipe()

    producer_proc = mp.Process(target=producer, args=(queue, 15),
                               name="Producer")
    filter_proc = mp.Process(target=filter_stage, args=(queue, filter_conn),
                             name="Filter")
    writer_proc = mp.Process(target=writer, args=(writer_conn,),
                             name="Writer")

    writer_proc.start()
    filter_proc.start()
    producer_proc.start()

    filter_conn.close()
    writer_conn.close()

    producer_proc.join()
    filter_proc.join()
    writer_proc.join()

    for proc in (producer_proc, filter_proc, writer_proc):
        assert proc.exitcode == 0, f"{proc.name} failed: {proc.exitcode}"

    queue.close()
    queue.join_thread()
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("All three processes exited cleanly; only even numbers reached "
          "the Writer, terminated by the None sentinel.")


if __name__ == "__main__":
    main()
