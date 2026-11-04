"""Exercise 2 - Pickle a Task Queue.

Demonstrates pickling a queue of computational tasks: some tasks are
executed before pickling, the rest afterwards, proving that pickle
preserves the exact state of Python objects.
"""

import math
import os
import pickle


class ComputeTask:
    """A single unit of work that can be executed and serialized."""

    def __init__(self, task_id, operation, input_value, result=None):
        self.task_id = task_id
        self.operation = operation
        self.input_value = input_value
        self.result = result

    def execute(self):
        """Compute the configured operation and store it in ``result``."""
        if self.operation == "square":
            self.result = self.input_value ** 2
        elif self.operation == "cube":
            self.result = self.input_value ** 3
        elif self.operation == "factorial":
            self.result = math.factorial(self.input_value)
        else:
            raise ValueError(f"Unknown operation: {self.operation}")
        return self.result

    def __repr__(self):
        return (f"ComputeTask(id={self.task_id}, op={self.operation!r}, "
                f"input={self.input_value}, result={self.result})")


def print_tasks(tasks, heading):
    """Print every task in ``tasks`` under ``heading``."""
    print(f"\n--- {heading} ---")
    for task in tasks:
        print(f"  {task}")


def main():
    """Create, partially execute, pickle, unpickle and finish the tasks."""
    tasks = [
        ComputeTask(1, "square", 7),
        ComputeTask(2, "cube", 5),
        ComputeTask(3, "factorial", 6),
        ComputeTask(4, "square", 12),
        ComputeTask(5, "factorial", 10),
    ]

    print_tasks(tasks, "Initial task queue (all pending)")

    for task in tasks[:2]:
        task.execute()
    print_tasks(tasks, "After executing the first 2 tasks")

    pkl_path = "task_queue.pkl"
    with open(pkl_path, "wb") as f:
        pickle.dump(tasks, f)
    print(f"\nPickled {len(tasks)} tasks to {pkl_path}")

    with open(pkl_path, "rb") as f:
        loaded = pickle.load(f)
    print(f"Unpickled {len(loaded)} tasks from {pkl_path}")
    print_tasks(loaded, "State after unpickling (first 2 done, rest pending)")

    done_before = sum(1 for t in loaded if t.result is not None)
    pending_before = sum(1 for t in loaded if t.result is None)
    print(f"\nVerification: {done_before} completed, {pending_before} pending "
          f"(expected 2 / 3)")

    for task in loaded:
        if task.result is None:
            task.execute()
    print_tasks(loaded, "Final state after executing the remaining tasks")

    os.remove(pkl_path)
    print(f"\nCleaned up temporary file {pkl_path}")


if __name__ == "__main__":
    main()
