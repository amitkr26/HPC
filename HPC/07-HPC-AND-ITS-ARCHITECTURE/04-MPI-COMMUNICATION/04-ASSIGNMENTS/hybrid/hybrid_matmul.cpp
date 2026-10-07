/*
hybrid_matmul.cpp -- Section 3 (Hybrid MPI+OpenMP), Problem 2: Hybrid Matrix-Matrix Multiply

Build (cluster):
    mpic++ -std=c++17 -fopenmp -O2 hybrid_matmul.cpp -o hybrid_matmul
Run -- same problem, three ways, fixed total core count (12):
    OMP_NUM_THREADS=1  mpirun -np 12 ./hybrid_matmul [N]    MPI-only baseline
    OMP_NUM_THREADS=12 mpirun -np 1  ./hybrid_matmul [N]    OpenMP-only baseline
    OMP_NUM_THREADS=3  mpirun -np 4  ./hybrid_matmul [N]    hybrid 4 ranks x 3 threads
    OMP_NUM_THREADS=4  mpirun -np 3  ./hybrid_matmul [N]    hybrid 3 ranks x 4 threads
sbatch:
    sbatch --nodes=1 --ntasks=4 --cpus-per-task=3 --time=00:20:00 \
           --env OMP_NUM_THREADS=3 --wrap="mpirun -np 4 ./hybrid_matmul 768"

What it does:
  * C = A * B with N x N dense matrices (default N = 512). Rows of A (and of the
    result C) are block-decomposed across MPI ranks with counts[r] = N/P +
    (r < N%P ? 1 : 0) -- non-even row blocks handled; B is replicated and
    MPI_Bcast from rank 0. A is generated from a closed form using global row
    indices, so no full copy of A exists anywhere.
  * Each run times two kernels over the SAME distributed block:
      - a 1-thread kernel  == the per-rank work of an MPI-only run
                              (use OMP_NUM_THREADS=1 to make the whole run MPI-only)
      - an OpenMP kernel with the configured thread count
        (at P = 1 this IS the OpenMP-only version of the problem)
    so MPI-only vs OpenMP-only vs hybrid can be compared by running the four
    commands above and reading the printed "label" and rank-max times.
  * Correctness: the 1-thread and OpenMP results are compared elementwise
    (parallelised only over rows, inner k-loop order unchanged -> must match),
    and rank 0 gathers C with MPI_Gatherv and compares against a serial
    triple-loop reference over the whole matrix -> PASS/FAIL.
  * Prints label, per-kernel rank-max time, and the speedup of the OpenMP kernel
    over the 1-thread kernel (parallel efficiency within a rank).
*/

#include <mpi.h>
#include <omp.h>

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

static double a_val(int i, int k) { return 1.0 / (double)((i * 11 + k * 5) % 47 + 1); }
static double b_val(int k, int j) { return 1.0 / (double)((k * 7 + j * 3) % 53 + 1); }

static void mm_kernel(const std::vector<double> &A, const std::vector<double> &B,
                      std::vector<double> &C, int rows, int n, int threads)
{
    #pragma omp parallel for num_threads(threads) schedule(static)
    for (int i = 0; i < rows; ++i) {
        for (int j = 0; j < n; ++j) {
            double s = 0.0;
            for (int k = 0; k < n; ++k)
                s += A[(size_t)i * n + k] * B[(size_t)k * n + j];
            C[(size_t)i * n + j] = s;
        }
    }
}

int main(int argc, char **argv)
{
    if (!std::getenv("OMP_NUM_THREADS")) omp_set_num_threads(omp_get_num_procs());

    MPI_Init(&argc, &argv);

    int rank = 0, size = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int n = 512;
    if (argc > 1) n = std::atoi(argv[1]);

    if (n <= 0 || n < size) {
        if (rank == 0) std::printf("ERROR: N must be >= number of processes\n");
        MPI_Finalize();
        return 1;
    }

    const int maxt = omp_get_max_threads();

    std::vector<int> counts((size_t)size), displs((size_t)size);
    int base = n / size, rem = n % size, off = 0;
    for (int i = 0; i < size; ++i) {
        counts[i] = base + (i < rem ? 1 : 0);
        displs[i] = off;
        off += counts[i];
    }
    const int rows = counts[rank], row0 = displs[rank];

    std::vector<double> B((size_t)n * (size_t)n);
    if (rank == 0)
        for (int k = 0; k < n; ++k)
            for (int j = 0; j < n; ++j)
                B[(size_t)k * n + j] = b_val(k, j);
    MPI_Bcast(B.data(), n * n, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    std::vector<double> A((size_t)rows * (size_t)n);
    for (int i = 0; i < rows; ++i)
        for (int k = 0; k < n; ++k)
            A[(size_t)i * n + k] = a_val(row0 + i, k);

    std::vector<double> C1((size_t)rows * (size_t)n), C2((size_t)rows * (size_t)n);

    MPI_Barrier(MPI_COMM_WORLD);
    double ta = MPI_Wtime();
    mm_kernel(A, B, C1, rows, n, 1);
    double tb = MPI_Wtime();

    MPI_Barrier(MPI_COMM_WORLD);
    double tc = MPI_Wtime();
    mm_kernel(A, B, C2, rows, n, maxt);
    double td = MPI_Wtime();

    double t1 = 0.0, t2 = 0.0, m1 = tb - ta, m2 = td - tc;
    MPI_Reduce(&m1, &t1, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&m2, &t2, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    long long diff = 0;
    for (size_t i = 0; i < C1.size(); ++i)
        if (C1[i] != C2[i]) ++diff;
    long long diff_all = 0;
    MPI_Reduce(&diff, &diff_all, 1, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);

    std::vector<double> Cfull;
    std::vector<int> gc((size_t)size, 0), gd((size_t)size, 0);
    if (rank == 0) {
        Cfull.resize((size_t)n * (size_t)n, 0.0);
        int o = 0;
        for (int i = 0; i < size; ++i) {
            gc[(size_t)i] = counts[i] * n;
            gd[(size_t)i] = o;
            o += gc[(size_t)i];
        }
    }
    MPI_Gatherv(C2.data(), rows * n, MPI_DOUBLE,
                Cfull.data(), gc.data(), gd.data(), MPI_DOUBLE,
                0, MPI_COMM_WORLD);

    int status = 0;
    if (rank == 0) {
        long long bad = 0;
        double max_err = 0.0;
        bool reference_done = (n <= 1024);
        if (reference_done) {
            for (int i = 0; i < n; ++i) {
                for (int j = 0; j < n; ++j) {
                    double s = 0.0;
                    for (int k = 0; k < n; ++k) s += a_val(i, k) * b_val(k, j);
                    double got = Cfull[(size_t)i * n + j];
                    double err = std::fabs(s - got);
                    if (err > max_err) max_err = err;
                    if (err > 1e-12 * (1.0 + std::fabs(s))) ++bad;
                }
            }
        }

        const char *label;
        if (size == 1 && maxt > 1) label = "OpenMP-only (1 rank x T threads)";
        else if (maxt == 1) label = "MPI-only (P ranks x 1 thread)";
        else label = "hybrid (P ranks x T threads)";

        std::printf("=== Section 3.2 Hybrid Matrix-Matrix Multiply ===\n");
        std::printf("label: %s  --  P = %d, T = %d, N = %d\n", label, size, maxt, n);
        std::printf("row blocks:");
        for (int i = 0; i < size && i < 16; ++i)
            std::printf(" [%d]=%d", i, counts[i]);
        if (size > 16) std::printf(" ...");
        std::printf("\n");
        std::printf("1-thread kernel (MPI-only per-rank work): %.3f ms (rank max)\n", 1000.0 * t1);
        std::printf("OpenMP kernel                             : %.3f ms (rank max)\n", 1000.0 * t2);
        std::printf("intra-rank speedup (1 thread / T threads) : %.3f\n",
                    t2 > 0.0 ? t1 / t2 : 0.0);
        std::printf("1-thread vs OpenMP result mismatches      : %lld (must be 0)\n", diff_all);
        if (reference_done) {
            std::printf("vs serial triple-loop reference: max abs err = %.3e, mismatches = %lld / %d\n",
                        max_err, bad, n * n);
            std::printf("RESULT: %s\n", (bad == 0 && diff_all == 0) ? "PASS" : "FAIL");
            if (bad != 0 || diff_all != 0) status = 1;
        } else {
            std::printf("N > 1024: serial reference skipped, checking 1-thread vs OpenMP only\n");
            std::printf("RESULT: %s\n", diff_all == 0 ? "PASS" : "FAIL");
            if (diff_all != 0) status = 1;
        }
        std::printf("run all four docstring commands to compare MPI-only vs OpenMP-only vs hybrid\n");
    }

    MPI_Bcast(&status, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Finalize();
    return status;
}
