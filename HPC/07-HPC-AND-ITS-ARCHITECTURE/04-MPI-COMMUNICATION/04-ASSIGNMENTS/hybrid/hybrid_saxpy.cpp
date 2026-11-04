/*
hybrid_saxpy.cpp -- Section 3 (Hybrid MPI+OpenMP), Problem 1: Hybrid SAXPY  y = a*x + y

Build (cluster):
    mpic++ -std=c++17 -fopenmp -O2 hybrid_saxpy.cpp -o hybrid_saxpy
Run -- fixed total core count (12), vary P x T:
    OMP_NUM_THREADS=12  mpirun -np 1  ./hybrid_saxpy [n]     (OpenMP-only)
    OMP_NUM_THREADS=6   mpirun -np 2  ./hybrid_saxpy
    OMP_NUM_THREADS=4   mpirun -np 3  ./hybrid_saxpy
    OMP_NUM_THREADS=3   mpirun -np 4  ./hybrid_saxpy
    OMP_NUM_THREADS=2   mpirun -np 6  ./hybrid_saxpy
    OMP_NUM_THREADS=1   mpirun -np 12 ./hybrid_saxpy         (MPI-only)
sbatch:
    sbatch --nodes=1 --ntasks=4 --cpus-per-task=3 --time=00:10:00 \
           --env OMP_NUM_THREADS=3 --wrap="mpirun -np 4 ./hybrid_saxpy 20000000"

What it does:
  * Block-decomposes vectors x and y of length n across P MPI ranks
    (counts[r] = n/P + (r < n%P ? 1 : 0), non-divisible n handled), then runs
    the local SAXPY loop y = a*x + y with OpenMP inside each rank.
  * Within one run the local loop is timed for several thread counts
    (1, 2, 4, 8, max -- deduplicated and clipped to the local block size), so the
    process-count x thread-count table can be built from the printed rows; the
    docstring above lists the mpirun commands that fix the total core count at
    12 while varying P x T.
  * For every thread count the result is checked elementwise against a SERIAL
    reference computed for the same local block, and a global checksum is
    MPI_Reduce'd and compared with a serial checksum over all n elements
    computed in closed form at rank 0 (this also proves the distribution covered
    every index exactly once) -> PASS/FAIL.
  * Prints per-config time (rank max), bandwidth in GB/s, and the speedup of the
    largest thread count over the 1-thread (MPI-only style) run.
*/

#include <mpi.h>
#include <omp.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

static const double kA = 2.5;

static double x0_of(long long g) { return (double)(g % 1000); }
static double y0_of(long long g) { return (double)(g % 777); }

int main(int argc, char **argv)
{
    if (!std::getenv("OMP_NUM_THREADS")) omp_set_num_threads(omp_get_num_procs());

    MPI_Init(&argc, &argv);

    int rank = 0, size = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    long long n = 20000000;
    if (argc > 1) n = std::atoll(argv[1]);

    if (n <= 0 || n < (long long)size) {
        if (rank == 0) std::printf("ERROR: n must be >= number of processes\n");
        MPI_Finalize();
        return 1;
    }

    std::vector<int> counts((size_t)size), displs((size_t)size);
    int base = (int)(n / size), rem = (int)(n % size), off = 0;
    for (int i = 0; i < size; ++i) {
        counts[i] = base + (i < rem ? 1 : 0);
        displs[i] = off;
        off += counts[i];
    }

    const int myn = counts[rank];
    const long long g0 = displs[rank];

    std::vector<double> x((size_t)myn), y((size_t)myn), yref((size_t)myn);
    for (int i = 0; i < myn; ++i) {
        long long g = g0 + i;
        x[(size_t)i] = x0_of(g);
        y[(size_t)i] = y0_of(g);
        yref[(size_t)i] = kA * x0_of(g) + y0_of(g);
    }
    std::vector<double> y0 = y;

    std::vector<int> tcounts;
    int maxt = omp_get_max_threads();
    int cand[] = {1, 2, 4, 8, maxt};
    for (int i = 0; i < 5; ++i) {
        int tc = cand[i];
        if (tc < 1) tc = 1;
        if (tc > maxt) tc = maxt;
        if (tc > myn && myn > 0) tc = myn;
        if (std::find(tcounts.begin(), tcounts.end(), tc) == tcounts.end())
            tcounts.push_back(tc);
    }
    std::sort(tcounts.begin(), tcounts.end());

    if (rank == 0) {
        std::printf("=== Section 3.1 Hybrid Vector/SAXPY ===\n");
        std::printf("n = %lld, P = %d ranks, max threads/rank = %d (OMP_NUM_THREADS)\n",
                    n, size, maxt);
        std::printf("block distribution: counts[r] = n/P + (r < n%%P ? 1 : 0)\n");
        std::printf("%8s %18s %12s %12s\n", "threads", "time(ms) rank-max", "GB/s", "speedup");
    }

    double t1t = 0.0, tTt = 0.0;

    double serial_sum = 0.0;
    if (rank == 0)
        for (long long g = 0; g < n; ++g) serial_sum += kA * x0_of(g) + y0_of(g);

    bool all_elem_ok = true, all_sum_ok = true;

    for (size_t ci = 0; ci < tcounts.size(); ++ci) {
        int tc = tcounts[ci];
        y = y0;

        MPI_Barrier(MPI_COMM_WORLD);
        double t0 = omp_get_wtime();
        #pragma omp parallel for num_threads(tc) schedule(static)
        for (int i = 0; i < myn; ++i) y[(size_t)i] = kA * x[(size_t)i] + y[(size_t)i];
        double t1 = omp_get_wtime();

        long long bad = 0;
        for (int i = 0; i < myn; ++i)
            if (y[(size_t)i] != yref[(size_t)i]) ++bad;
        long long bad_all = 0;
        MPI_Reduce(&bad, &bad_all, 1, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);

        double my_sum = 0.0;
        for (int i = 0; i < myn; ++i) my_sum += y[(size_t)i];
        double sum_all = 0.0;
        MPI_Reduce(&my_sum, &sum_all, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

        double my_time = t1 - t0, max_time = 0.0;
        MPI_Reduce(&my_time, &max_time, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

        if (tc == 1) t1t = max_time;
        tTt = max_time;

        if (rank == 0) {
            double gb = 3.0 * 8.0 * (double)n / (max_time > 0.0 ? max_time : 1e-9) / 1e9;
            double sp = (max_time > 0.0 && t1t > 0.0) ? t1t / max_time : 1.0;
            std::printf("%8d %18.3f %12.3f %12.3f\n", tc, 1000.0 * max_time, gb, sp);

            double tol = 1e-9 * (serial_sum > 0.0 ? serial_sum : 1.0);
            if (bad_all != 0) all_elem_ok = false;
            if (std::fabs(sum_all - serial_sum) > tol) all_sum_ok = false;
        }
    }

    int status = 0;
    if (rank == 0) {
        bool ok = all_elem_ok && all_sum_ok;
        std::printf("elementwise vs serial reference (every thread count): %s\n",
                    all_elem_ok ? "PASS" : "FAIL");
        std::printf("global checksum vs serial checksum over all n elements: %s\n",
                    all_sum_ok ? "PASS" : "FAIL");
        std::printf("hybrid speedup (max threads vs 1 thread) = %.3f\n",
                    tTt > 0.0 ? t1t / tTt : 0.0);
        std::printf("RESULT: %s\n", ok ? "PASS" : "FAIL");
        if (!ok) status = 1;
    }

    MPI_Bcast(&status, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Finalize();
    return status;
}
