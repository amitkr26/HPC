/*
hybrid_monte_carlo_pi.cpp -- Section 3 (Hybrid MPI+OpenMP), Problem 4: Hybrid Monte Carlo pi

Build (cluster):
    mpic++ -std=c++17 -fopenmp -O2 hybrid_monte_carlo_pi.cpp -o hybrid_monte_carlo_pi
Run (vary P and T at a fixed total core count, e.g. 12):
    OMP_NUM_THREADS=12 mpirun -np 1  ./hybrid_monte_carlo_pi 10000000
    OMP_NUM_THREADS=6  mpirun -np 2  ./hybrid_monte_carlo_pi 10000000
    OMP_NUM_THREADS=4  mpirun -np 4  ./hybrid_monte_carlo_pi 10000000
    OMP_NUM_THREADS=3  mpirun -np 4  ./hybrid_monte_carlo_pi 10000000
    OMP_NUM_THREADS=1  mpirun -np 12 ./hybrid_monte_carlo_pi 10000000
sbatch:
    sbatch --nodes=1 --ntasks=4 --cpus-per-task=3 --time=00:10:00 \
           --env OMP_NUM_THREADS=3 --wrap="mpirun -np 4 ./hybrid_monte_carlo_pi 10000000"

What it does:
  * Estimates pi by throwing total/1 "darts" at the unit square and counting how
    many land inside the quarter unit circle: pi ~= 4 * hits / total.
  * The sample count is block-distributed over P ranks (count = total/P +
    (r < total%P ? 1 : 0), non-divisible total handled).
  * Inside each rank the local loop is parallelised with OpenMP; every thread
    owns its own std::mt19937_64 engine seeded from (fixed base, rank, thread
    id), so the generators are THREAD-SAFE and independent -- no shared RNG and
    no locks. Sampling uses std::uniform_real_distribution per thread.
  * Two passes are run per invocation (schedule(static) and schedule(dynamic))
    to show the result is stable regardless of how work is divided between
    threads; partial hit counts are combined across ranks with MPI_Reduce
    (MPI_LONG_LONG, MPI_SUM).
  * Timing: barrier + omp_get_wtime around the sampling, rank-max reported, plus
    samples/second.
  * PASS: both estimates must satisfy |pi_est - pi| <= 12/sqrt(total)
    (a ~7-sigma statistical bound for total = 10^7).
*/

#include <mpi.h>
#include <omp.h>

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <vector>

static const double kPi = 3.14159265358979323846;
static const unsigned long long kSeedBase = 20261007ULL;

int main(int argc, char **argv)
{
    if (!std::getenv("OMP_NUM_THREADS")) omp_set_num_threads(omp_get_num_procs());

    MPI_Init(&argc, &argv);

    int rank = 0, size = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    long long total = 10000000;
    if (argc > 1) total = std::atoll(argv[1]);

    if (total <= 0 || total < (long long)size) {
        if (rank == 0) std::printf("ERROR: total must be >= number of processes\n");
        MPI_Finalize();
        return 1;
    }

    std::vector<int> counts((size_t)size), displs((size_t)size);
    int base = (int)(total / size), rem = (int)(total % size), off = 0;
    for (int i = 0; i < size; ++i) {
        counts[i] = base + (i < rem ? 1 : 0);
        displs[i] = off;
        off += counts[i];
    }
    const long long local = counts[rank];
    const int maxt = omp_get_max_threads();

    if (rank == 0) {
        std::printf("=== Section 3.4 Hybrid Monte Carlo pi ===\n");
        std::printf("samples = %lld, P = %d ranks, T = %d threads/rank\n",
                    total, size, maxt);
        std::printf("per-rank share = total/P + (r < total%%P ? 1 : 0)\n");
        std::printf("%10s %8s %14s %12s %16s %12s\n",
                    "schedule", "hits", "pi estimate", "|error|", "time(ms rank-max)", "Msamples/s");
    }

    int status = 0;
    bool all_ok = true;
    const double tol = 12.0 / std::sqrt((double)total);
    const int schedules[2] = {0, 1};

    for (int si = 0; si < 2; ++si) {
        int sched = schedules[si];
        long long hits = 0;

        MPI_Barrier(MPI_COMM_WORLD);
        double t0 = omp_get_wtime();

        #pragma omp parallel reduction(+:hits)
        {
            const int tid = omp_get_thread_num();
            std::mt19937_64 gen(kSeedBase + 1000003ULL * (unsigned long long)rank +
                                7919ULL * (unsigned long long)tid);
            std::uniform_real_distribution<double> U(0.0, 1.0);
            if (sched == 0) {
                #pragma omp for schedule(static)
                for (long long i = 0; i < local; ++i) {
                    double x = U(gen), y = U(gen);
                    if (x * x + y * y <= 1.0) ++hits;
                }
            } else {
                #pragma omp for schedule(dynamic)
                for (long long i = 0; i < local; ++i) {
                    double x = U(gen), y = U(gen);
                    if (x * x + y * y <= 1.0) ++hits;
                }
            }
        }

        double t1 = omp_get_wtime();

        long long hits_all = 0;
        MPI_Reduce(&hits, &hits_all, 1, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);

        double my_time = t1 - t0, max_time = 0.0;
        MPI_Reduce(&my_time, &max_time, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

        if (rank == 0) {
            double est = 4.0 * (double)hits_all / (double)total;
            double err = std::fabs(est - kPi);
            bool ok = err <= tol;
            if (!ok) all_ok = false;
            double msps = (double)total / (max_time > 0.0 ? max_time : 1e-9) / 1e6;
            std::printf("%10s %8lld %14.9f %12.3e %16.3f %12.3f\n",
                        sched == 0 ? "static" : "dynamic", hits_all, est, err,
                        1000.0 * max_time, msps);
        }
    }

    if (rank == 0) {
        bool ok = all_ok;
        std::printf("tolerance = 12/sqrt(total) = %.3e (statistical, ~7 sigma)\n", tol);
        std::printf("RNG: one std::mt19937_64 per (rank, thread) -- thread-safe, no locks\n");
        std::printf("RESULT: %s\n", ok ? "PASS" : "FAIL");
        if (!ok) status = 1;
    }

    MPI_Bcast(&status, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Finalize();
    return status;
}
