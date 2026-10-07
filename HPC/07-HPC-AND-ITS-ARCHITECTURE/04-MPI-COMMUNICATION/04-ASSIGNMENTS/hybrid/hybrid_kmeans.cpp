/*
hybrid_kmeans.cpp -- Section 3 (Hybrid MPI+OpenMP), Problem 5: Hybrid Parallel K-Means Clustering

Build (cluster):
    mpic++ -std=c++17 -fopenmp -O2 hybrid_kmeans.cpp -o hybrid_kmeans
Run (compare MPI-only vs hybrid at fixed total core count, e.g. 12):
    OMP_NUM_THREADS=1  mpirun -np 12 ./hybrid_kmeans 100000 8
    OMP_NUM_THREADS=3  mpirun -np 4  ./hybrid_kmeans 100000 8
    OMP_NUM_THREADS=4  mpirun -np 3  ./hybrid_kmeans 100000 8
    OMP_NUM_THREADS=6  mpirun -np 2  ./hybrid_kmeans 100000 8
    OMP_NUM_THREADS=12 mpirun -np 1  ./hybrid_kmeans 100000 8
sbatch:
    sbatch --nodes=1 --ntasks=4 --cpus-per-task=3 --time=00:15:00 \
           --env OMP_NUM_THREADS=3 --wrap="mpirun -np 4 ./hybrid_kmeans 100000 8"

What it does:
  * N 2-D points are generated deterministically (per-rank seed) from K planted
    clusters and block-distributed over P ranks with counts[r] = N/P +
    (r < N%P ? 1 : 0) -- non-divisible N handled.
  * Convergence loop (identical logic for both variants):
      1. assign every local point to its nearest centroid (double loop, no
         communication) -- OpenMP-parallel; each thread accumulates into its own
         private sum/count arrays, merged once per thread under `critical`
         (no write races), while the shared centroid array is read-only;
      2. combine partial sums (K*D doubles) and counts (K long longs) with
         MPI_Allreduce (MPI_SUM);
      3. update centroids (empty clusters keep their old centre), and decide
         convergence with an MPI_Allreduce (MPI_LAND) over the per-rank
         "local max shift < tolerance" flags;
      4. repeat until converged or max iterations.
  * BOTH variants are executed in a single run from the SAME initial centroids:
      - "MPI-only"  = the same code forced to 1 OpenMP thread per rank (pure MPI)
      - "Hybrid"    = the same code with the configured thread count
    Convergence is recorded iteration by iteration (shift history printed side
    by side) and both wall times (barrier + MPI_Wtime, rank max) are reported
    with the speedup of hybrid over MPI-only.
  * Verification / PASS-FAIL:
      - the final objective (sum of squared distances of every point to its
        assigned centroid) is recomputed with MPI_Reduce during each run;
      - rank 0 gathers all points (MPI_Gatherv) and recomputes the objective
        serially from the hybrid final centroids -> must match the reported one;
      - the MPI-only objective and the hybrid objective must agree;
      - every point must be assigned exactly once (total counts == N).
  * Optional arguments: number of points (default 100000), K (default 8).
*/

#include <mpi.h>
#include <omp.h>

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <vector>

struct KMeansResult {
    int iters = 0;
    double time = 0.0;
    double final_shift = 0.0;
    double objective = 0.0;
    long long assigned = 0;
    std::vector<double> centroids;
    std::vector<double> shift_hist;
};

static void kmeans_run(const std::vector<double> &pts, long long local_n,
                       const std::vector<double> &init, int k, int d,
                       double tol, int max_iters, int threads,
                       KMeansResult &res)
{
    res.centroids = init;
    res.iters = 0;
    res.final_shift = 0.0;
    res.objective = 0.0;
    res.assigned = 0;
    res.shift_hist.clear();

    std::vector<double> sums((size_t)k * (size_t)d, 0.0);
    std::vector<long long> cnt((size_t)k, 0);
    std::vector<double> gsums((size_t)k * (size_t)d, 0.0);
    std::vector<long long> gcnt((size_t)k, 0);

    MPI_Barrier(MPI_COMM_WORLD);
    double t0 = MPI_Wtime();

    for (int it = 0; it < max_iters; ++it) {
        std::fill(sums.begin(), sums.end(), 0.0);
        std::fill(cnt.begin(), cnt.end(), 0);

        #pragma omp parallel num_threads(threads)
        {
            std::vector<double> ls((size_t)k * (size_t)d, 0.0);
            std::vector<long long> lc((size_t)k, 0);
            #pragma omp for schedule(static)
            for (long long i = 0; i < local_n; ++i) {
                const double *p = &pts[(size_t)i * (size_t)d];
                int best = 0;
                double bd = 0.0;
                for (int c = 0; c < k; ++c) {
                    const double *cen = &res.centroids[(size_t)c * (size_t)d];
                    double acc = 0.0;
                    for (int dd = 0; dd < d; ++dd) {
                        double diff = p[dd] - cen[dd];
                        acc += diff * diff;
                    }
                    if (c == 0 || acc < bd) { bd = acc; best = c; }
                }
                lc[(size_t)best] += 1;
                for (int dd = 0; dd < d; ++dd)
                    ls[(size_t)best * (size_t)d + (size_t)dd] += p[dd];
            }
            #pragma omp critical
            {
                for (int c = 0; c < k; ++c) {
                    cnt[(size_t)c] += lc[(size_t)c];
                    for (int dd = 0; dd < d; ++dd)
                        sums[(size_t)c * (size_t)d + (size_t)dd] +=
                            ls[(size_t)c * (size_t)d + (size_t)dd];
                }
            }
        }

        MPI_Allreduce(sums.data(), gsums.data(), k * d, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
        MPI_Allreduce(cnt.data(), gcnt.data(), k, MPI_LONG_LONG, MPI_SUM, MPI_COMM_WORLD);

        double shift = 0.0;
        for (int c = 0; c < k; ++c) {
            if (gcnt[(size_t)c] == 0) continue;
            double moved = 0.0;
            for (int dd = 0; dd < d; ++dd) {
                double nv = gsums[(size_t)c * (size_t)d + (size_t)dd] /
                            (double)gcnt[(size_t)c];
                double diff = nv - res.centroids[(size_t)c * (size_t)d + (size_t)dd];
                moved += diff * diff;
                res.centroids[(size_t)c * (size_t)d + (size_t)dd] = nv;
            }
            moved = std::sqrt(moved);
            if (moved > shift) shift = moved;
        }

        res.iters = it + 1;
        res.final_shift = shift;
        res.shift_hist.push_back(shift);

        int local_conv = (shift < tol) ? 1 : 0;
        int converged = 0;
        MPI_Allreduce(&local_conv, &converged, 1, MPI_INT, MPI_LAND, MPI_COMM_WORLD);
        if (converged) break;
    }

    double obj = 0.0;
    #pragma omp parallel num_threads(threads) reduction(+: obj)
    {
        #pragma omp for schedule(static)
        for (long long i = 0; i < local_n; ++i) {
            const double *p = &pts[(size_t)i * (size_t)d];
            double bd = 0.0;
            for (int c = 0; c < k; ++c) {
                const double *cen = &res.centroids[(size_t)c * (size_t)d];
                double acc = 0.0;
                for (int dd = 0; dd < d; ++dd) {
                    double diff = p[dd] - cen[dd];
                    acc += diff * diff;
                }
                if (c == 0 || acc < bd) bd = acc;
            }
            obj += bd;
        }
    }

    double obj_all = 0.0;
    MPI_Reduce(&obj, &obj_all, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

    long long assigned_local = 0;
    for (int c = 0; c < k; ++c) assigned_local += gcnt[(size_t)c];
    long long assigned_all = 0;
    MPI_Reduce(&assigned_local, &assigned_all, 1, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);

    double t1 = MPI_Wtime();
    double my_time = t1 - t0, max_time = 0.0;
    MPI_Reduce(&my_time, &max_time, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    res.time = max_time;
    res.objective = obj_all;
    res.assigned = assigned_all;
}

int main(int argc, char **argv)
{
    if (!std::getenv("OMP_NUM_THREADS")) omp_set_num_threads(omp_get_num_procs());

    MPI_Init(&argc, &argv);

    int rank = 0, size = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    long long n = 100000;
    int k = 8;
    if (argc > 1) n = std::atoll(argv[1]);
    if (argc > 2) k = std::atoi(argv[2]);

    const int d = 2;
    const double tol = 1e-6;
    const int max_iters = 60;

    if (n <= 0 || n < (long long)size || k < 2 || k > 64) {
        if (rank == 0) std::printf("ERROR: need N >= P and 2 <= K <= 64\n");
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
    const long long local_n = counts[rank];

    std::vector<double> pts((size_t)local_n * (size_t)d);
    {
        std::mt19937_64 rng(4242ULL + (unsigned long long)rank);
        std::uniform_real_distribution<double> U(-0.35, 0.35);
        for (long long i = 0; i < local_n; ++i) {
            int c = (int)(i % k);
            double cx = (double)(c % 4) * 2.0;
            double cy = (double)(c / 4) * 2.0;
            pts[(size_t)i * d] = cx + U(rng);
            pts[(size_t)i * d + 1] = cy + U(rng);
        }
    }

    std::vector<double> init((size_t)k * (size_t)d, 0.0);
    if (rank == 0)
        for (int c = 0; c < k; ++c) {
            init[(size_t)c * d] = (double)(c % 4) * 2.0 + 0.5;
            init[(size_t)c * d + 1] = (double)(c / 4) * 2.0 + 0.5;
        }
    MPI_Bcast(init.data(), k * d, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    const int maxt = omp_get_max_threads();

    KMeansResult r_mpi, r_hyb;
    kmeans_run(pts, local_n, init, k, d, tol, max_iters, 1, r_mpi);
    kmeans_run(pts, local_n, init, k, d, tol, max_iters, maxt, r_hyb);

    std::vector<int> gc((size_t)size, 0), gd((size_t)size, 0);
    if (rank == 0) {
        int o = 0;
        for (int i = 0; i < size; ++i) {
            gc[(size_t)i] = counts[i] * d;
            gd[(size_t)i] = o;
            o += gc[(size_t)i];
        }
    }
    std::vector<double> all_pts;
    if (rank == 0) all_pts.resize((size_t)n * (size_t)d, 0.0);
    MPI_Gatherv(pts.data(), (int)(local_n * d), MPI_DOUBLE,
                all_pts.data(), gc.data(), gd.data(), MPI_DOUBLE, 0, MPI_COMM_WORLD);

    int status = 0;
    if (rank == 0) {
        double ref_obj = 0.0;
        for (long long i = 0; i < n; ++i) {
            const double *p = &all_pts[(size_t)i * (size_t)d];
            double bd = 0.0;
            for (int c = 0; c < k; ++c) {
                const double *cen = &r_hyb.centroids[(size_t)c * (size_t)d];
                double acc = 0.0;
                for (int dd = 0; dd < d; ++dd) {
                    double diff = p[dd] - cen[dd];
                    acc += diff * diff;
                }
                if (c == 0 || acc < bd) bd = acc;
            }
            ref_obj += bd;
        }

        double e_hyb = std::fabs(ref_obj - r_hyb.objective) /
                       (1.0 + std::fabs(ref_obj));
        double e_cmp = std::fabs(r_mpi.objective - r_hyb.objective) /
                       (1.0 + std::fabs(ref_obj));
        bool obj_ok = e_hyb <= 1e-9 && e_cmp <= 1e-9;
        bool cnt_ok = (r_hyb.assigned == n) && (r_mpi.assigned == n);

        std::printf("=== Section 3.5 Hybrid Parallel K-Means ===\n");
        std::printf("N = %lld points, K = %d, D = %d, P = %d ranks, T = %d threads\n",
                    n, k, d, size, maxt);
        std::printf("distribution: counts[r] = N/P + (r < N%%P ? 1 : 0)\n\n");
        std::printf("%14s %8s %10s %16s %14s %12s\n",
                    "variant", "iters", "time(ms)", "objective", "final shift", "points");
        std::printf("%14s %8d %10.3f %16.6f %14.3e %12lld\n",
                    "MPI-only (T=1)", r_mpi.iters, 1000.0 * r_mpi.time,
                    r_mpi.objective, r_mpi.final_shift, r_mpi.assigned);
        std::printf("%14s %8d %10.3f %16.6f %14.3e %12lld\n",
                    "Hybrid (T=max)", r_hyb.iters, 1000.0 * r_hyb.time,
                    r_hyb.objective, r_hyb.final_shift, r_hyb.assigned);
        std::printf("speedup (MPI-only / hybrid) = %.3f\n",
                    r_hyb.time > 0.0 ? r_mpi.time / r_hyb.time : 0.0);
        std::printf("\nconvergence (centroid shift per iteration):\n");
        size_t rows = r_mpi.shift_hist.size();
        if (r_hyb.shift_hist.size() > rows) rows = r_hyb.shift_hist.size();
        for (size_t i = 0; i < rows; ++i) {
            double a = i < r_mpi.shift_hist.size() ? r_mpi.shift_hist[i] : -1.0;
            double b = i < r_hyb.shift_hist.size() ? r_hyb.shift_hist[i] : -1.0;
            std::printf("  it %3zu: MPI-only %.6e   hybrid %.6e%s\n",
                        i + 1, a, b, (b >= 0.0 && b < tol) ? "   <- converged" : "");
        }
        std::printf("\nobjective recomputed serially at root = %.6f\n", ref_obj);
        std::printf("hybrid reported objective             = %.6f (rel diff %.3e)\n",
                    r_hyb.objective, e_hyb);
        std::printf("MPI-only vs hybrid objective rel diff = %.3e (tol 1e-9)\n", e_cmp);
        std::printf("all points assigned exactly once: %s\n", cnt_ok ? "yes" : "NO");
        std::printf("RESULT: %s\n", (obj_ok && cnt_ok) ? "PASS" : "FAIL");
        if (!obj_ok || !cnt_ok) status = 1;
    }

    MPI_Bcast(&status, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Finalize();
    return status;
}
