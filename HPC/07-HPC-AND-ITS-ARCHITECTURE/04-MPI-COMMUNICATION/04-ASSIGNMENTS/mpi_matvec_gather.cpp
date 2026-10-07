/*
mpi_matvec_gather.cpp -- Section 2 (MPI), Problem 2: Parallel Matrix-Vector Multiply

Build (cluster):
    mpic++ -std=c++17 -O2 mpi_matvec_gather.cpp -o mpi_matvec_gather
Run:
    mpirun -np 4 ./mpi_matvec_gather [M] [N]
sbatch:
    sbatch --nodes=1 --ntasks=4 --time=00:10:00 \
           --wrap="mpirun -np 4 ./mpi_matvec_gather 997 1013"

What it does:
  * Multiplies an M x N matrix by a length-N vector. Defaults M = 997, N = 1013,
    i.e. NON-square and NOT divisible by typical process counts (try -np 4/5/8).
  * Block row decomposition: rank r owns rows [displs[r], displs[r]+counts[r])
    with counts[r] = M/P + (r < M%P ? 1 : 0), so uneven blocks are handled.
  * Matrix and vector are generated from closed-form formulas, so every rank only
    stores its own block of A (no root-side copy of the full matrix is needed).
  * Each rank computes its partial product y_r = A_r * x locally (loop over the
    owned rows, inner dot product over all N columns).
  * Partial vectors are collected at rank 0 with MPI_Gatherv (variable counts
    because the row blocks differ in size), NOT plain MPI_Gather.
  * Rank 0 recomputes y = A*x with a serial triple loop over the whole matrix and
    compares elementwise against the gathered result -> PASS/FAIL.
  * Timing: barrier + MPI_Wtime around local multiply and gather, rank-max time
    reported together with the serial reference time.
*/

#include <mpi.h>

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

static double a_val(int i, int j)
{
    return 1.0 / (double)((i * 31 + j * 17) % 97 + 1);
}

static double x_val(int j)
{
    return 1.0 + (double)(j % 37);
}

int main(int argc, char **argv)
{
    MPI_Init(&argc, &argv);

    int rank = 0, size = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int m = 997, n = 1013;
    if (argc > 2) { m = std::atoi(argv[1]); n = std::atoi(argv[2]); }

    if (m <= 0 || n <= 0 || m < size) {
        if (rank == 0)
            std::printf("ERROR: need M >= P and N >= 1 (got M=%d N=%d P=%d)\n", m, n, size);
        MPI_Finalize();
        return 1;
    }

    std::vector<int> counts((size_t)size), displs((size_t)size);
    int base = m / size, rem = m % size, off = 0;
    for (int i = 0; i < size; ++i) {
        counts[i] = base + (i < rem ? 1 : 0);
        displs[i] = off;
        off += counts[i];
    }

    const int rows = counts[rank];
    const int row0 = displs[rank];

    std::vector<double> A((size_t)rows * (size_t)n);
    std::vector<double> x((size_t)n);
    for (int j = 0; j < n; ++j) x[(size_t)j] = x_val(j);
    for (int i = 0; i < rows; ++i)
        for (int j = 0; j < n; ++j)
            A[(size_t)i * n + j] = a_val(row0 + i, j);

    std::vector<double> y_local((size_t)rows, 0.0);
    std::vector<double> y_gathered;
    if (rank == 0) y_gathered.resize((size_t)m, 0.0);

    MPI_Barrier(MPI_COMM_WORLD);
    double t0 = MPI_Wtime();

    for (int i = 0; i < rows; ++i) {
        double s = 0.0;
        const double *ar = &A[(size_t)i * n];
        for (int j = 0; j < n; ++j) s += ar[j] * x[(size_t)j];
        y_local[(size_t)i] = s;
    }

    MPI_Gatherv(y_local.data(), rows, MPI_DOUBLE,
                y_gathered.data(), counts.data(), displs.data(), MPI_DOUBLE,
                0, MPI_COMM_WORLD);

    double t1 = MPI_Wtime();
    double my_time = t1 - t0, max_time = 0.0;
    MPI_Reduce(&my_time, &max_time, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    int status = 0;
    if (rank == 0) {
        double t2 = MPI_Wtime();
        std::vector<double> ref((size_t)m, 0.0);
        for (int i = 0; i < m; ++i) {
            double s = 0.0;
            for (int j = 0; j < n; ++j) s += a_val(i, j) * x_val(j);
            ref[(size_t)i] = s;
        }
        double t3 = MPI_Wtime();

        long long bad = 0;
        double max_err = 0.0;
        for (int i = 0; i < m; ++i) {
            double err = std::fabs(ref[(size_t)i] - y_gathered[(size_t)i]);
            if (err > 1e-9 * (1.0 + std::fabs(ref[(size_t)i]))) ++bad;
            if (err > max_err) max_err = err;
        }

        std::printf("=== Section 2.2 Parallel Matrix-Vector Multiply ===\n");
        std::printf("A is %d x %d (non-square, uneven rows), P = %d\n", m, n, size);
        std::printf("block row decomposition:\n");
        for (int i = 0; i < size && i < 16; ++i)
            std::printf("  rank %d: rows [%d, %d)  count = %d\n",
                        i, displs[i], displs[i] + counts[i], counts[i]);
        if (size > 16) std::printf("  ...\n");
        std::printf("gathered with MPI_Gatherv (variable recv counts)\n");
        std::printf("serial reference time = %.3f ms\n", 1000.0 * (t3 - t2));
        std::printf("MPI kernel time (rank max) = %.3f ms\n", 1000.0 * max_time);
        std::printf("y[0] = %.10f (ref %.10f)\n", y_gathered[0], ref[0]);
        std::printf("y[M-1] = %.10f (ref %.10f)\n", y_gathered[(size_t)m - 1],
                    ref[(size_t)m - 1]);
        std::printf("max abs error = %.3e, mismatches = %lld / %d\n",
                    max_err, bad, m);
        std::printf("RESULT: %s\n", bad == 0 ? "PASS" : "FAIL");
        if (bad != 0) status = 1;
    }

    MPI_Bcast(&status, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Finalize();
    return status;
}
