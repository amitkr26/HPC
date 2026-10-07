/*
mpi_scatter_reduce_sum.cpp -- Section 2 (MPI), Problem 1: Distributed Array Sum

Build (cluster):
    mpic++ -std=c++17 -O2 mpi_scatter_reduce_sum.cpp -o mpi_scatter_reduce_sum
Run:
    mpirun -np 4 ./mpi_scatter_reduce_sum 10000000
sbatch:
    sbatch --nodes=1 --ntasks=4 --time=00:10:00 \
           --wrap="mpirun -np 4 ./mpi_scatter_reduce_sum 10000000"

What it does:
  * Generates N doubles on rank 0 with a closed-form pattern (default N = 10^7).
  * Splits N over P processes with sendcounts/displs arrays so that a NON-divisible
    N is handled: rank r gets N/P + (r < N%P ? 1 : 0) elements.
  * Distributes with MPI_Scatter when N % P == 0 and with MPI_Scatterv otherwise
    (both paths are exercised depending on the arguments you pass).
  * Each rank sums its chunk (partial sum), results are combined with MPI_Reduce
    (MPI_SUM) at rank 0.
  * Rank 0 recomputes the sum serially over the full array and compares against
    the reduced distributed result, printing PASS/FAIL.
  * Timing is measured per rank (barrier before, MPI_Wtime) and the rank-maximum
    time is reported, as is the serial time for reference.

Try a non-divisible size to see the Scatterv path, e.g. -np 4 with N = 10000003.
*/

#include <mpi.h>

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

int main(int argc, char **argv)
{
    MPI_Init(&argc, &argv);

    int rank = 0, size = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    long long n = 10000000;
    if (argc > 1) n = std::atoll(argv[1]);

    if (n <= 0 || n < (long long)size) {
        if (rank == 0)
            std::printf("ERROR: n (%lld) must be positive and >= number of processes (%d)\n",
                        n, size);
        MPI_Finalize();
        return 1;
    }

    std::vector<int> counts((size_t)size), displs((size_t)size);
    int base = (int)(n / size);
    int rem = (int)(n % size);
    int off = 0;
    for (int i = 0; i < size; ++i) {
        counts[i] = base + (i < rem ? 1 : 0);
        displs[i] = off;
        off += counts[i];
    }

    std::vector<double> full;
    if (rank == 0) {
        full.resize((size_t)n);
        for (long long i = 0; i < n; ++i)
            full[(size_t)i] = 1.0 / (1.0 + (double)(i % 1000));
    }

    std::vector<double> local((size_t)counts[rank]);

    MPI_Barrier(MPI_COMM_WORLD);
    double t0 = MPI_Wtime();

    if (n % size == 0) {
        MPI_Scatter(full.data(), (int)(n / size), MPI_DOUBLE,
                    local.data(), counts[rank], MPI_DOUBLE, 0, MPI_COMM_WORLD);
    } else {
        MPI_Scatterv(full.data(), counts.data(), displs.data(), MPI_DOUBLE,
                     local.data(), counts[rank], MPI_DOUBLE, 0, MPI_COMM_WORLD);
    }

    double local_sum = 0.0;
    for (int i = 0; i < counts[rank]; ++i) local_sum += local[(size_t)i];

    double global_sum = 0.0;
    MPI_Reduce(&local_sum, &global_sum, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

    double t1 = MPI_Wtime();

    double max_time = 0.0;
    double my_time = t1 - t0;
    MPI_Reduce(&my_time, &max_time, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    long long distributed_elems = 0;
    long long my_count = counts[rank];
    MPI_Reduce(&my_count, &distributed_elems, 1, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);

    int status = 0;
    if (rank == 0) {
        double serial_sum = 0.0;
        for (long long i = 0; i < n; ++i) serial_sum += full[(size_t)i];

        double tol = 1e-8 * (serial_sum > 0.0 ? serial_sum : 1.0);
        bool ok = std::fabs(global_sum - serial_sum) <= tol &&
                  distributed_elems == n;

        std::printf("=== Section 2.1 Distributed Array Sum ===\n");
        std::printf("n = %lld, P = %d, distribution: N/P + (r < N%%P ? 1 : 0)\n", n, size);
        std::printf("path used: %s\n", n % size == 0 ? "MPI_Scatter (evenly divisible)"
                                                      : "MPI_Scatterv (NOT divisible)");
        std::printf("per-rank counts:");
        for (int i = 0; i < size && i < 16; ++i) std::printf(" [%d]=%d", i, counts[i]);
        if (size > 16) std::printf(" ...");
        std::printf("\n");
        std::printf("elements distributed: %lld (expected %lld)\n", distributed_elems, n);
        std::printf("serial sum      = %.10f\n", serial_sum);
        std::printf("MPI_Reduce sum  = %.10f\n", global_sum);
        std::printf("abs difference  = %.3e (tol %.3e)\n",
                    std::fabs(global_sum - serial_sum), tol);
        std::printf("time (rank max) = %.3f ms\n", 1000.0 * max_time);
        std::printf("RESULT: %s\n", ok ? "PASS" : "FAIL");
        if (!ok) status = 1;
    }

    MPI_Bcast(&status, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Finalize();
    return status;
}
