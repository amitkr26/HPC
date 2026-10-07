"""Exercise 2: Distributed Monte Carlo Pi with MPI Collectives.

Rank 0 broadcasts the sample count, every rank generates its own local
random points (seeded independently per rank), counts the points inside the
unit circle, and rank 0 reduces all local counts with MPI.SUM to approximate
pi = 4 * total_inside / total_samples.

Launch with:  mpirun -n 4 python ex02_mpi_collective_pi.py
"""

import math
import random

from mpi4py import MPI

DEFAULT_SAMPLES = 12_000_000


def main():
    """Compute pi in parallel using bcast / reduce collectives."""
    start_time = MPI.Wtime()

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # 1. Broadcast configuration from rank 0
    if rank == 0:
        total_samples = DEFAULT_SAMPLES
    else:
        total_samples = None
    total_samples = comm.bcast(total_samples, root=0)

    # 2. Parallel sampling: independent stream per rank
    local_samples = total_samples // size
    random.seed(rank * 100 + 42)

    local_inside = 0
    for _ in range(local_samples):
        x = random.random()
        y = random.random()
        if x * x + y * y <= 1.0:
            local_inside += 1

    # 3. Global reduction of the local counts onto rank 0
    total_inside = comm.reduce(local_inside, op=MPI.SUM, root=0)

    # 4. Result calculation on rank 0
    if rank == 0:
        pi_approx = 4.0 * total_inside / total_samples
        error = abs(pi_approx - math.pi)
        print(f"Processes        : {size}")
        print(f"Total samples    : {total_samples:,}")
        print(f"Inside circle    : {total_inside:,}")
        print(f"pi approximation : {pi_approx:.10f}")
        print(f"math.pi          : {math.pi:.10f}")
        print(f"Absolute error   : {error:.10f}")
        print(f"Runtime (s)      : {MPI.Wtime() - start_time:.4f}")


if __name__ == "__main__":
    main()
