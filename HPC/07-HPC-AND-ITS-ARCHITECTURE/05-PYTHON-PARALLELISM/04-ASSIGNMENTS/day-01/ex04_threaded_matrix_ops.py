"""Exercise 4 - Matrix Operations with Threads.

Computes the element-wise sum of two 5x5 matrices using one thread per
row (shared memory, no locks needed) and verifies against a sequential
computation.
"""

import random
import threading


def add_row(a, b, result, row_index):
    """Store the element-wise sum of row ``row_index`` of ``a`` and ``b``."""
    result[row_index] = [a[row_index][j] + b[row_index][j]
                         for j in range(len(a[row_index]))]


def print_matrix(matrix, heading):
    """Print ``matrix`` under ``heading``."""
    print(f"\n--- {heading} ---")
    for row in matrix:
        print("  " + " ".join(f"{value:3d}" for value in row))


def add_sequential(a, b):
    """Compute the element-wise sum without threads."""
    result = [[0] * len(row) for row in a]
    for i in range(len(a)):
        add_row(a, b, result, i)
    return result


def main():
    """Run the threaded addition and compare it with the sequential one."""
    random.seed(42)
    matrix_a = [[random.randint(1, 10) for _ in range(5)] for _ in range(5)]
    matrix_b = [[random.randint(1, 10) for _ in range(5)] for _ in range(5)]
    result = [[0] * 5 for _ in range(5)]

    print_matrix(matrix_a, "Matrix A")
    print_matrix(matrix_b, "Matrix B")

    threads = []
    for i in range(5):
        thread = threading.Thread(target=add_row,
                                  args=(matrix_a, matrix_b, result, i))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

    print_matrix(result, "Threaded result (5 threads, one per row)")

    expected = add_sequential(matrix_a, matrix_b)
    print_matrix(expected, "Sequential result (expected)")

    print("\nVerification:")
    print(f"  Threaded result matches sequential result: {result == expected}")
    print("  Each thread wrote to a different row, so no lock was required.")


if __name__ == "__main__":
    main()
