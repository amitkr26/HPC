/*
 * Section 1 - Problem 1: Parallel Array Sum & Statistics
 *
 * Computes the sum, mean and population standard deviation of N = 10^7 doubles
 * with "#pragma omp parallel for" using a reduction(+ : sum, sumsq) clause.
 * Execution time and speedup are compared against the sequential version for
 * 1, 2, 4 and 8 threads (each configuration is averaged over several passes so
 * the timings are stable). Every parallel result is checked against the
 * sequential reference and a PASS/FAIL verdict is printed.
 *
 * Build: g++ -std=c++17 -fopenmp -Wall -Wextra -O2 openmp_array_sum_stats.cpp -o openmp_array_sum_stats
 * Run:   openmp_array_sum_stats.exe
 */

#include <cmath>
#include <cstdio>
#include <vector>
#include <omp.h>

namespace {

constexpr long long N = 10000000;
constexpr int REPS = 5;
constexpr double REL_TOL = 1e-9;

struct Stats {
    double sum = 0.0;
    double mean = 0.0;
    double stddev = 0.0;
};

Stats make_stats(double sum, double sumsq, long long n) {
    Stats s;
    s.sum = sum;
    s.mean = sum / static_cast<double>(n);
    double var = sumsq / static_cast<double>(n) - s.mean * s.mean;
    if (var < 0.0) var = 0.0;
    s.stddev = std::sqrt(var);
    return s;
}

Stats compute_serial(const std::vector<double>& a) {
    const long long n = static_cast<long long>(a.size());
    double sum = 0.0;
    double sumsq = 0.0;
    for (long long i = 0; i < n; ++i) {
        sum += a[i];
        sumsq += a[i] * a[i];
    }
    return make_stats(sum, sumsq, n);
}

Stats compute_parallel(const std::vector<double>& a, int threads) {
    const long long n = static_cast<long long>(a.size());
    double sum = 0.0;
    double sumsq = 0.0;
#pragma omp parallel for num_threads(threads) schedule(static) reduction(+ : sum, sumsq)
    for (long long i = 0; i < n; ++i) {
        sum += a[i];
        sumsq += a[i] * a[i];
    }
    return make_stats(sum, sumsq, n);
}

bool close_enough(double a, double b) {
    const double scale = std::fabs(b) > 1.0 ? std::fabs(b) : 1.0;
    return std::fabs(a - b) <= REL_TOL * scale;
}

}

int main() {
    std::printf("Problem 1: Parallel Array Sum & Statistics  (N = %lld doubles, %.0f MB)\n",
                N, static_cast<double>(N) * sizeof(double) / (1024.0 * 1024.0));
    std::printf("Formula: mean = sum/N, stddev = sqrt(E[x^2] - mean^2) (population)\n\n");

    std::vector<double> a(static_cast<size_t>(N));
    for (long long i = 0; i < N; ++i) {
        a[static_cast<size_t>(i)] = 1.0 + static_cast<double>((i * 37) % 1000) * 0.001;
    }

    double t0 = omp_get_wtime();
    Stats ref;
    for (int r = 0; r < REPS; ++r) ref = compute_serial(a);
    const double serial_time = (omp_get_wtime() - t0) / REPS;

    std::printf("Sequential reference: sum = %.10f  mean = %.10f  stddev = %.10f  time = %.6f s\n",
                ref.sum, ref.mean, ref.stddev, serial_time);
    std::printf("Verification tolerance: relative %.1e\n\n", REL_TOL);

    std::printf("%8s %12s %10s %20s %16s %16s %6s\n",
                "threads", "time (s)", "speedup", "sum", "mean", "stddev", "check");
    std::printf("%8s %12.6f %10s %20.6f %16.10f %16.10f %6s\n",
                "serial", serial_time, "-", ref.sum, ref.mean, ref.stddev, "PASS");

    bool all_ok = true;
    double speedup8 = 0.0;
    const int thread_list[] = {1, 2, 4, 8};
    for (int t : thread_list) {
        double pt0 = omp_get_wtime();
        Stats st;
        for (int r = 0; r < REPS; ++r) st = compute_parallel(a, t);
        const double ptime = (omp_get_wtime() - pt0) / REPS;
        const bool ok = close_enough(st.sum, ref.sum) && close_enough(st.mean, ref.mean) &&
                        close_enough(st.stddev, ref.stddev);
        all_ok = all_ok && ok;
        const double sp = serial_time / ptime;
        if (t == 8) speedup8 = sp;
        std::printf("%8d %12.6f %9.2fx %20.6f %16.10f %16.10f %6s\n",
                    t, ptime, sp, st.sum, st.mean, st.stddev, ok ? "PASS" : "FAIL");
    }

    std::printf("\nConclusion: speedup at 8 threads = %.2fx. ", speedup8);
    if (speedup8 < 3.0) {
        std::printf("The reduction streams %.0f MB per pass, so scaling is limited by memory "
                    "bandwidth rather than by the addition itself; adding threads beyond the "
                    "point where the bus saturates yields little extra speed.\n",
                    static_cast<double>(N) * sizeof(double) / (1024.0 * 1024.0));
    } else {
        std::printf("Each thread reduces an independent chunk and combines via the reduction "
                    "tree, so per-thread memory traffic overlaps well and the kernel scales "
                    "close to the core count until bandwidth saturates.\n");
    }

    std::printf("\n%s: statistics verified against sequential reference on all thread counts\n",
                all_ok ? "PASS" : "FAIL");
    return all_ok ? 0 : 1;
}
