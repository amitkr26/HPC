/*
mpi_sample_sort.cpp -- Section 2 (MPI), Problem 5: Parallel Sample Sort

Build (cluster):
    mpic++ -std=c++17 -O2 mpi_sample_sort.cpp -o mpi_sample_sort
Run:
    mpirun -np 4 ./mpi_sample_sort 1000000
    mpirun -np 8 ./mpi_sample_sort 2000000
sbatch:
    sbatch --nodes=1 --ntasks=8 --time=00:10:00 --wrap="mpirun -np 8 ./mpi_sample_sort 2000000"

What it does:
  * Each rank generates its own deterministic chunk of uniform doubles
    (size n/P + (r < n%P ? 1 : 0), non-divisible n handled), then sorts it
    locally with std::sort.
  * Splitters: every rank picks P-1 candidates evenly spaced from its sorted
    chunk; they are gathered at rank 0 (MPI_Gather), rank 0 sorts the candidates
    and selects P-1 splitters that cut the global data into P roughly equal
    buckets; the splitters are MPI_Bcast to everyone.
  * Redistribution: each element's bucket is found by binary search on the
    splitters, per-destination sendcounts are built, recvcounts are obtained
    with MPI_Alltoall over the count array, and the data is moved with
    MPI_Alltoallv using explicit sendcounts/displs and recvcounts/displs.
  * Final local sort on each rank of its received bucket.
  * Verification of the GLOBAL order at rank 0: sizes are gathered (MPI_Gather),
    all data is gathered (MPI_Gatherv) and checked to be non-decreasing and to
    contain exactly n elements; additionally a checksum is compared against the
    MPI_Reduce sum of the per-rank local sums (detects lost/duplicated data),
    and each rank checks its own bucket is sorted. PASS/FAIL printed.
*/

#include <mpi.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <vector>

int main(int argc, char **argv)
{
    MPI_Init(&argc, &argv);

    int rank = 0, size = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    long long n = 1000000;
    if (argc > 1) n = std::atoll(argv[1]);

    if (n <= 0 || n < (long long)size) {
        if (rank == 0) std::printf("ERROR: n must be >= number of processes\n");
        MPI_Finalize();
        return 1;
    }

    std::vector<int> counts((size_t)size);
    int base = (int)(n / size), rem = (int)(n % size);
    for (int i = 0; i < size; ++i)
        counts[i] = base + (i < rem ? 1 : 0);
    const int myn = counts[rank];

    if (rank == 0) {
        std::printf("=== Section 2.5 Parallel Sample Sort ===\n");
        std::printf("n = %lld, P = %d (chunk sizes:", n, size);
        for (int i = 0; i < size && i < 16; ++i) std::printf(" %d", counts[i]);
        if (size > 16) std::printf(" ...");
        std::printf(")\n");
    }

    MPI_Barrier(MPI_COMM_WORLD);
    double wall0 = MPI_Wtime();

    std::vector<double> data((size_t)myn);
    std::mt19937_64 rng(12345ULL + (unsigned long long)rank);
    std::uniform_real_distribution<double> U(0.0, 1.0);
    for (int i = 0; i < myn; ++i) data[(size_t)i] = U(rng);

    double t0 = MPI_Wtime();
    std::sort(data.begin(), data.end());
    double t_local_sort = MPI_Wtime() - t0;

    const int nsplit = size - 1;
    std::vector<double> cand((size_t)(nsplit > 0 ? nsplit : 1), 0.0);
    for (int k = 0; k < nsplit; ++k) {
        long long idx = (long long)((double)(k + 1) * (double)myn / (double)(nsplit + 1));
        if (idx >= myn) idx = myn - 1;
        if (idx < 0) idx = 0;
        cand[(size_t)k] = data[(size_t)idx];
    }

    std::vector<double> allcand;
    if (rank == 0) allcand.resize((size_t)(size * (nsplit > 0 ? nsplit : 1)));
    MPI_Gather(cand.data(), nsplit, MPI_DOUBLE,
               allcand.data(), nsplit, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    std::vector<double> splitters((size_t)(nsplit > 0 ? nsplit : 1), 0.0);
    if (rank == 0 && nsplit > 0) {
        std::sort(allcand.begin(), allcand.end());
        int total = size * nsplit;
        for (int k = 0; k < nsplit; ++k) {
            int idx = (int)((long long)(k + 1) * total / size);
            if (idx >= total) idx = total - 1;
            splitters[(size_t)k] = allcand[(size_t)idx];
        }
    }
    if (nsplit > 0)
        MPI_Bcast(splitters.data(), nsplit, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    if (rank == 0 && nsplit > 0) {
        std::printf("splitters:");
        for (int k = 0; k < nsplit && k < 16; ++k)
            std::printf(" %.6f", splitters[(size_t)k]);
        if (nsplit > 16) std::printf(" ...");
        std::printf("\n");
    }

    std::vector<int> sendc((size_t)size, 0), sdispl((size_t)size, 0);
    for (int i = 0; i < myn; ++i) {
        int b = (int)(std::lower_bound(splitters.begin(), splitters.begin() + nsplit,
                                        data[(size_t)i]) - splitters.begin());
        ++sendc[(size_t)b];
    }
    int soff = 0;
    for (int i = 0; i < size; ++i) {
        sdispl[(size_t)i] = soff;
        soff += sendc[(size_t)i];
    }

    std::vector<int> recvc((size_t)size, 0), rdispl((size_t)size, 0);
    MPI_Alltoall(sendc.data(), 1, MPI_INT, recvc.data(), 1, MPI_INT, MPI_COMM_WORLD);

    int recv_total = 0;
    for (int i = 0; i < size; ++i) {
        rdispl[(size_t)i] = recv_total;
        recv_total += recvc[(size_t)i];
    }

    long long sent = 0, recvd = 0;
    for (int i = 0; i < size; ++i) { sent += sendc[(size_t)i]; recvd += recvc[(size_t)i]; }

    t0 = MPI_Wtime();
    std::vector<double> buf((size_t)recv_total);
    MPI_Alltoallv(data.data(), sendc.data(), sdispl.data(), MPI_DOUBLE,
                  buf.data(), recvc.data(), rdispl.data(), MPI_DOUBLE, MPI_COMM_WORLD);
    double t_alltoall = MPI_Wtime() - t0;

    t0 = MPI_Wtime();
    std::sort(buf.begin(), buf.end());
    double t_final_sort = MPI_Wtime() - t0;

    bool local_sorted = true;
    for (int i = 1; i < recv_total; ++i)
        if (buf[(size_t)i] < buf[(size_t)i - 1]) local_sorted = false;

    int local_sorted_i = local_sorted ? 1 : 0;
    int all_sorted = 0;
    MPI_Allreduce(&local_sorted_i, &all_sorted, 1, MPI_INT, MPI_LAND, MPI_COMM_WORLD);

    double local_sum = 0.0;
    for (int i = 0; i < recv_total; ++i) local_sum += buf[(size_t)i];
    double sum_global = 0.0;
    MPI_Reduce(&local_sum, &sum_global, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

    std::vector<int> gcounts((size_t)size), gdispls((size_t)size);
    MPI_Gather(&recv_total, 1, MPI_INT, gcounts.data(), 1, MPI_INT, 0, MPI_COMM_WORLD);

    long long all_recv = 0, all_sent = 0;
    MPI_Allreduce(&recvd, &all_recv, 1, MPI_LONG_LONG, MPI_SUM, MPI_COMM_WORLD);
    MPI_Allreduce(&sent, &all_sent, 1, MPI_LONG_LONG, MPI_SUM, MPI_COMM_WORLD);

    std::vector<double> all;
    if (rank == 0) {
        int goff = 0;
        for (int i = 0; i < size; ++i) { gdispls[(size_t)i] = goff; goff += gcounts[(size_t)i]; }
        all.resize((size_t)n);
    }
    MPI_Gatherv(buf.data(), recv_total, MPI_DOUBLE,
                all.data(), gcounts.data(), gdispls.data(), MPI_DOUBLE, 0, MPI_COMM_WORLD);

    double wall1 = MPI_Wtime();

    int status = 0;
    if (rank == 0) {
        bool global_sorted = true;
        long long out_of_order = 0;
        for (long long i = 1; i < n; ++i)
            if (all[(size_t)i] < all[(size_t)i - 1]) { global_sorted = false; ++out_of_order; }

        double all_sum = 0.0;
        for (long long i = 0; i < n; ++i) all_sum += all[(size_t)i];
        double sum_tol = 1e-9 * n + 1e-6;
        bool sums_ok = std::fabs(all_sum - sum_global) <= sum_tol;
        bool counts_ok = (all_recv == n) && (all_sent == n);
        bool ok = global_sorted && sums_ok && counts_ok && all_sorted != 0;

        std::printf("total elements sent = %lld, received = %lld (n = %lld)\n",
                    all_sent, all_recv, n);
        std::printf("recv bucket sizes:");
        for (int i = 0; i < size && i < 16; ++i) std::printf(" %d", gcounts[(size_t)i]);
        if (size > 16) std::printf(" ...");
        std::printf("\n");
        std::printf("local sort  = %.3f ms\n", 1000.0 * t_local_sort);
        std::printf("alltoallv   = %.3f ms\n", 1000.0 * t_alltoall);
        std::printf("final sort  = %.3f ms\n", 1000.0 * t_final_sort);
        std::printf("total       = %.3f ms\n", 1000.0 * (wall1 - wall0));
        std::printf("globally non-decreasing: %s (%lld inversions)\n",
                    global_sorted ? "yes" : "NO", out_of_order);
        std::printf("each rank's bucket sorted: %s\n", all_sorted ? "yes" : "NO");
        std::printf("checksum serial-vs-MPI: %.10f vs %.10f (diff %.3e, tol %.3e)\n",
                    all_sum, sum_global, std::fabs(all_sum - sum_global), sum_tol);
        std::printf("RESULT: %s\n", ok ? "PASS" : "FAIL");
        if (!ok) status = 1;
    }

    MPI_Bcast(&status, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Finalize();
    return status;
}
