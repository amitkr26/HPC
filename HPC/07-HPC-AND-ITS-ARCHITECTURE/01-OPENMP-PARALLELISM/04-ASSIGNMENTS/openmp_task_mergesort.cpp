/*
 * Section 1 - Problem 5: Parallel Merge Sort with Tasks
 *
 * Classic top-down merge sort. The divide step spawns an OpenMP task for the
 * left half, sorts the right half in the current task, then synchronizes with
 * "#pragma omp taskwait" before merging (merge happens in the parent, so the
 * two halves never touch the same memory concurrently). Subarrays no larger
 * than the SEQUENTIAL CUTOFF are sorted with std::sort instead of spawning
 * more tasks, which bounds the task count and avoids task-scheduling overhead
 * on tiny ranges.
 *
 * Measurements: for array sizes 100000 and 1000000 and cutoffs 1024 / 16384 /
 * 131072, the sort is run with 1, 2, 4 and 8 threads. Each run is verified
 * element-by-element against a std::sort reference. The sequential baseline is
 * the same task-based merge sort executed outside any parallel region (tasks
 * then run inline), and std::sort is printed as an extra reference line. A
 * speedup bar chart shows the effect of the thread count.
 *
 * Build: g++ -std=c++17 -fopenmp -Wall -Wextra -O2 openmp_task_mergesort.cpp -o openmp_task_mergesort
 * Run:   openmp_task_mergesort.exe
 */

#include <algorithm>
#include <cstdio>
#include <random>
#include <string>
#include <vector>
#include <omp.h>

namespace {

void msort_range(int* a, int* tmp, int lo, int hi, int cutoff) {
    if (hi - lo <= 1) return;
    if (hi - lo <= cutoff) {
        std::sort(a + lo, a + hi);
        return;
    }
    const int mid = lo + (hi - lo) / 2;
#pragma omp task firstprivate(a, tmp, lo, mid, cutoff)
    msort_range(a, tmp, lo, mid, cutoff);
#pragma omp task firstprivate(a, tmp, mid, hi, cutoff)
    msort_range(a, tmp, mid, hi, cutoff);
#pragma omp taskwait
    std::merge(a + lo, a + mid, a + mid, a + hi, tmp + lo);
    std::copy(tmp + lo, tmp + hi, a + lo);
}

double sort_serial(std::vector<int>& a, std::vector<int>& tmp, int cutoff) {
    const double t0 = omp_get_wtime();
    msort_range(a.data(), tmp.data(), 0, static_cast<int>(a.size()), cutoff);
    return omp_get_wtime() - t0;
}

double sort_parallel(std::vector<int>& a, std::vector<int>& tmp, int cutoff, int threads) {
    const double t0 = omp_get_wtime();
#pragma omp parallel num_threads(threads)
    {
#pragma omp single
        msort_range(a.data(), tmp.data(), 0, static_cast<int>(a.size()), cutoff);
    }
    return omp_get_wtime() - t0;
}

std::string bar(double speedup) {
    const int n = static_cast<int>(speedup * 16.0 + 0.5);
    return std::string(n > 0 ? n : 0, '#');
}

}

int main() {
    std::printf("Problem 5: Parallel Merge Sort with Tasks (task / taskwait + sequential cutoff)\n\n");

    const int sizes[] = {100000, 1000000};
    const int cutoffs[] = {1024, 16384, 131072};
    const int threads_sweep[] = {1, 2, 4, 8};
    bool all_ok = true;

    for (int si = 0; si < 2; ++si) {
        const int n = sizes[si];
        std::vector<int> base(static_cast<size_t>(n));
        std::mt19937 gen(12345);
        std::uniform_int_distribution<int> dist(0, 2000000000);
        for (int i = 0; i < n; ++i) base[static_cast<size_t>(i)] = dist(gen);

        std::vector<int> reference = base;
        const double ref_t0 = omp_get_wtime();
        std::sort(reference.begin(), reference.end());
        const double stdsort_time = omp_get_wtime() - ref_t0;

        std::printf("=== size = %d elements (random ints)  |  std::sort reference = %.6f s ===\n",
                    n, stdsort_time);
        std::printf("%9s %8s %12s %10s %8s  %s\n",
                    "cutoff", "threads", "time (s)", "speedup", "check", "speedup bar");

        double best_speedup = 0.0;
        double best_time = 0.0;
        int best_threads = 0;
        int best_cutoff = 0;
        double sp8[3] = {0.0, 0.0, 0.0};

        for (int ci = 0; ci < 3; ++ci) {
            const int cutoff = cutoffs[ci];
            std::vector<int> work = base;
            std::vector<int> tmp(static_cast<size_t>(n));
            const double serial_t = sort_serial(work, tmp, cutoff);
            const bool serial_ok = work == reference;
            all_ok = all_ok && serial_ok;
            std::printf("%9d %8s %12.6f %9s %4s  (same algorithm, no parallel region)\n",
                        cutoff, "serial", serial_t, "-", serial_ok ? "PASS" : "FAIL");
            if (cutoff >= n) {
                std::printf("   (note: cutoff >= array size, so the sequential-cutoff path "
                            "sorts everything and no tasks are spawned - this row measures "
                            "only parallel-region overhead)\n");
            }

            for (int ti = 0; ti < 4; ++ti) {
                const int t = threads_sweep[ti];
                work = base;
                const double ptime = sort_parallel(work, tmp, cutoff, t);
                const bool ok = work == reference;
                all_ok = all_ok && ok;
                const double sp = serial_t / ptime;
                if (t == 8) sp8[ci] = sp;
                if (sp > best_speedup) {
                    best_speedup = sp;
                    best_time = ptime;
                    best_threads = t;
                    best_cutoff = cutoff;
                }
                std::printf("%9d %8d %12.6f %8.2fx %4s  |%s|\n",
                            cutoff, t, ptime, sp, ok ? "PASS" : "FAIL", bar(sp).c_str());
            }
            std::printf("\n");
        }

        std::printf("Conclusion (size %d): best configuration = cutoff %d with %d threads, "
                    "%.2fx over the sequential version of the same algorithm (parallel best "
                    "%.4f s vs std::sort %.4f s -> %.2fx).\n", n, best_cutoff, best_threads,
                    best_speedup, best_time, stdsort_time, stdsort_time / best_time);
        std::printf("Thread effect at 8 threads: cutoff %d -> %.2fx, %d -> %.2fx, %d -> %.2fx. "
                    "The 1-thread rows sit at or below 1.0x because task creation/taskwait is "
                    "pure overhead there; raising the cutoff removes that overhead while there "
                    "are still many more leaf tasks than threads, and cutting it too small "
                    "floods the runtime with tiny tasks that never pay off.\n\n",
                    cutoffs[0], sp8[0], cutoffs[1], sp8[1], cutoffs[2], sp8[2]);
    }

    std::printf("%s: every run matched the std::sort reference element-for-element\n",
                all_ok ? "PASS" : "FAIL");
    return all_ok ? 0 : 1;
}
