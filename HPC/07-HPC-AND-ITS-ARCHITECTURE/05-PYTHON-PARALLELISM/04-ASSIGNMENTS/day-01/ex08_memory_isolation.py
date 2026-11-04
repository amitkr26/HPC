"""Exercise 8 - Process vs Thread Memory Isolation Lab.

Part A shows that child processes do not see the parent's list updates,
Part B shares data through multiprocessing.Array, and Part C passes
results back with multiprocessing.Queue.
"""

import multiprocessing
import os

shared_log = []


def log_message(msg):
    """Append ``msg`` to this process's copy of ``shared_log``."""
    shared_log.append(msg)
    print(f"  [child pid={os.getpid()}] appended {msg!r} -> "
          f"len(shared_log) = {len(shared_log)}", flush=True)


def fill_range(arr, start, end, value):
    """Fill ``arr[start:end]`` with ``value`` in shared memory."""
    for i in range(start, end):
        arr[i] = value


def square_worker(q, number):
    """Put ``(number, number**2)`` into the shared process queue."""
    q.put((number, number ** 2))


def part_a():
    """Show that each process gets its own copy of the global list."""
    print("=== Part A: memory isolation ===", flush=True)
    processes = [multiprocessing.Process(target=log_message,
                                         args=(f"message-{i}",))
                 for i in range(3)]
    for process in processes:
        process.start()
    for process in processes:
        process.join()
    print(f"  Parent's shared_log after children finish: {shared_log}")
    print("  Observation: the parent list is empty - each child had its "
          "own copy.\n")


def part_b():
    """Share a C-style integer array between two processes."""
    print("=== Part B: multiprocessing.Array ===")
    shared_array = multiprocessing.Array("i", 10)
    processes = [
        multiprocessing.Process(target=fill_range,
                                args=(shared_array, 0, 5, 1)),
        multiprocessing.Process(target=fill_range,
                                args=(shared_array, 5, 10, 2)),
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join()
    values = [shared_array[i] for i in range(10)]
    print(f"  Array from parent: {values}")
    print(f"  Matches expected : {values == [1, 1, 1, 1, 1, 2, 2, 2, 2, 2]}\n")


def part_c():
    """Collect results computed by four worker processes."""
    print("=== Part C: multiprocessing.Queue ===")
    q = multiprocessing.Queue()
    numbers = [3, 5, 7, 11]
    processes = [multiprocessing.Process(target=square_worker,
                                         args=(q, number))
                 for number in numbers]
    for process in processes:
        process.start()
    for process in processes:
        process.join()

    results = [q.get() for _ in numbers]
    print(f"  Results received from {len(numbers)} workers:")
    for number, square in results:
        print(f"    {number}^2 = {square}")
    print(f"  All squares correct: "
          f"{all(sq == n * n for n, sq in results)}\n")


def main():
    """Run all three parts of the isolation lab."""
    part_a()
    part_b()
    part_c()
    print("Summary: processes do not share ordinary Python objects; use "
          "Array, Queue or Pipe for IPC.")


if __name__ == "__main__":
    main()
