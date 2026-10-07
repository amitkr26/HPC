/*
 * Section 1 - Problem 2: Parallel Matrix Multiplication (static vs dynamic)
 *
 * Dense C = A x B for N x N doubles (N = 1000) with the OUTER loop over rows
 * parallelized. Compares the sequential version with static scheduling, dynamic
 * scheduling (chunk 1 and chunk 16) and guided scheduling, verifies every
 * parallel result element-by-element against the sequential reference, and
 * reports which schedule performs better and why (load balance vs cache/TLB
 * locality effects).
 *
 * Build: g++ -std=c++17 -fopenmp -Wall -Wextra -O2 openmp_matmul_scheduling.cpp -o openmp_matmul_scheduling
 * Run:   openmp_matmul_scheduling.exe
 */

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <vector>
#include <omp.h>

namespace {

constexpr int N = 1000;
constexpr int THREADS = 8;

using Mat = std::vector<double>;

void mul_serial(const Mat& A, const Mat& B, Mat& C, int n) {
    std::fill(C.begin(), C.end(), 0.0);
    for (int i = 0; i < n; ++i) {
        for (int k = 0; k < n; ++k) {
            const double aik = A[static_cast<size_t>(i) * n + k];
            for (int j = 0; j < n; ++j) {
                C[static_cast<size_t>(i) * n + j] += aik * B[static_cast<size_t>(k) * n + j];
            }
        }
    }
}

void mul_static(const Mat& A, const Mat& B, Mat& C, int n, int threads) {
    std::fill(C.begin(), C.end(), 0.0);
#pragma omp parallel for num_threads(threads) schedule(static)
    for (int i = 0; i < n; ++i) {
        for (int k = 0; k < n; ++k) {
            const double aik = A[static_cast<size_t>(i) * n + k];
            for (int j = 0; j < n; ++j) {
                C[static_cast<size_t>(i) * n + j] += aik * B[static_cast<size_t>(k) * n + j];
            }
        }
    }
}

void mul_dynamic(const Mat& A, const Mat& B, Mat& C, int n, int threads, int chunk) {
    std::fill(C.begin(), C.end(), 0.0);
#pragma omp parallel for num_threads(threads) schedule(dynamic, chunk)
    for (int i = 0; i < n; ++i) {
        for (int k = 0; k < n; ++k) {
            const double aik = A[static_cast<size_t>(i) * n + k];
            for (int j = 0; j < n; ++j) {
                C[static_cast<size_t>(i) * n + j] += aik * B[static_cast<size_t>(k) * n + j];
            }
        }
    }
}

void mul_guided(const Mat& A, const Mat& B, Mat& C, int n, int threads, int chunk) {
    std::fill(C.begin(), C.end(), 0.0);
#pragma omp parallel for num_threads(threads) schedule(guided, chunk)
    for (int i = 0; i < n; ++i) {
        for (int k = 0; k < n; ++k) {
            const double aik = A[static_cast<size_t>(i) * n + k];
            for (int j = 0; j < n; ++j) {
                C[static_cast<size_t>(i) * n + j] += aik * B[static_cast<size_t>(k) * n + j];
            }
        }
    }
}

double max_diff(const Mat& X, const Mat& Y) {
    double m = 0.0;
    for (size_t i = 0; i < X.size(); ++i) {
        const double d = std::fabs(X[i] - Y[i]);
        if (d > m) m = d;
    }
    return m;
}

struct Trial {
    const char* name;
    double time;
    double maxerr;
    bool ok;
};

}

int main() {
    std::printf("Problem 2: Parallel Matrix Multiplication  (C = A x B, %d x %d doubles, %d threads)\n",
                N, N, THREADS);
    std::printf("Outer loop over rows is parallelized; loop order i-k-j keeps both operands "
                "streamed row-wise for cache locality.\n\n");

    Mat A(static_cast<size_t>(N) * N);
    Mat B(static_cast<size_t>(N) * N);
    Mat C(static_cast<size_t>(N) * N);
    Mat ref(static_cast<size_t>(N) * N);

    for (int i = 0; i < N; ++i) {
        for (int k = 0; k < N; ++k) {
            A[static_cast<size_t>(i) * N + k] = static_cast<double>((i * 17 + k * 13) % 100) / 100.0;
            B[static_cast<size_t>(k) * N + i] = static_cast<double>((k * 7 + i * 11) % 100) / 100.0;
        }
    }

    const double st0 = omp_get_wtime();
    mul_serial(A, B, ref, N);
    const double serial_time = omp_get_wtime() - st0;
    std::printf("Sequential time: %.6f s\n\n", serial_time);

    std::printf("%22s %12s %10s %14s %7s\n", "configuration", "time (s)", "speedup", "max |diff|", "check");

    Trial trials[4];
    trials[0] = {"static (default)", 0.0, 0.0, false};
    trials[1] = {"dynamic, chunk 1", 0.0, 0.0, false};
    trials[2] = {"dynamic, chunk 16", 0.0, 0.0, false};
    trials[3] = {"guided, chunk 16", 0.0, 0.0, false};

    bool all_ok = true;
    for (int t = 0; t < 4; ++t) {
        const double t0 = omp_get_wtime();
        if (t == 0) mul_static(A, B, C, N, THREADS);
        else if (t == 1) mul_dynamic(A, B, C, N, THREADS, 1);
        else if (t == 2) mul_dynamic(A, B, C, N, THREADS, 16);
        else mul_guided(A, B, C, N, THREADS, 16);
        trials[t].time = omp_get_wtime() - t0;
        trials[t].maxerr = max_diff(C, ref);
        trials[t].ok = trials[t].maxerr <= 1e-9;
        all_ok = all_ok && trials[t].ok;
        std::printf("%22s %12.6f %9.2fx %14.3e %7s\n",
                    trials[t].name, trials[t].time, serial_time / trials[t].time,
                    trials[t].maxerr, trials[t].ok ? "PASS" : "FAIL");
    }

    int best = 0;
    for (int t = 1; t < 4; ++t)
        if (trials[t].time < trials[best].time) best = t;

    std::printf("\nConclusion: %s is fastest for this shape (%.6f s, %.2fx over serial); "
                "static %.6f s, dynamic(1) %.6f s, dynamic(16) %.6f s, guided(16) %.6f s.\n",
                trials[best].name, trials[best].time, serial_time / trials[best].time,
                trials[0].time, trials[1].time, trials[2].time, trials[3].time);
    if (best == 0) {
        std::printf("Static wins because every row costs the same (uniform i-k-j work), so "
                    "static scheduling already balances the load perfectly and lets each thread "
                    "keep a contiguous block of rows of C - better cache/TLB locality - while "
                    "dynamic pays dispatch overhead and scatters distant rows of C across "
                    "cores, interleaving their working sets in the shared cache.\n");
    } else {
        std::printf("Dynamic/guided beat static by %.1f%% here even though row costs are "
                    "uniform: interleaving rows across cores spreads the %dx%d working set of C "
                    "more evenly over the private caches while dispatching only %d iterations "
                    "costs almost nothing, and static's contiguous blocks contend for the same "
                    "cache/DRAM banks. On shapes with unequal row cost (sparse or banded A) the "
                    "dynamic advantage grows further; when rows stream uniformly and fit in "
                    "cache, static's locality usually comes out ahead.\n",
                    100.0 * (trials[0].time - trials[best].time) / trials[0].time, N, N, N);
    }

    std::printf("\n%s: all parallel results match the sequential product element-wise\n",
                all_ok ? "PASS" : "FAIL");
    return all_ok ? 0 : 1;
}
