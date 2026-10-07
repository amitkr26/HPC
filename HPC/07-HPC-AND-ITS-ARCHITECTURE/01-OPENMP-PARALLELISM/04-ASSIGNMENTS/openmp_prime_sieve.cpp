/*
 * Section 1 - Problem 3: Parallel Prime Sieve (Sieve of Eratosthenes)
 *
 * Finds all primes up to N = 10^8 with a vector<unsigned char> flag array
 * (N+1 bytes ~ 95 MB). A tiny serial sieve produces the base primes p <=
 * sqrt(N); the full marking loop over those base primes is then parallelized
 * with "#pragma omp parallel for" under static, dynamic and guided scheduling
 * and compared with the serial reference.
 *
 * The sheet's load-balancing discussion: the marking cost of base prime p is
 * about N/p, so the first few primes carry almost all of the work (p = 2 marks
 * ~5.0e7 locations, p = 9973 marks only ~1.0e4 - a ratio near 5000:1). A
 * static partition over the prime list therefore dumps the huge early primes
 * on one thread, while dynamic/guided redistribute them; the program prints
 * the measured schedule comparison, the analytic static partition shares, and
 * a conclusion line.
 *
 * Note: concurrent "#pragma omp parallel for" iterations store the SAME value
 * (0) to overlapping byte locations; byte stores of an identical value are
 * benign in practice on all supported platforms, and the result is verified
 * byte-for-byte against the serial sieve anyway.
 *
 * Build: g++ -std=c++17 -fopenmp -Wall -Wextra -O2 openmp_prime_sieve.cpp -o openmp_prime_sieve
 * Run:   openmp_prime_sieve.exe
 */

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <vector>
#include <omp.h>

namespace {

constexpr long long N = 100000000;
constexpr int THREADS = 8;
constexpr long long EXPECTED_PI = 5761455;

enum class Sched { Static, Dynamic, Guided };

std::vector<int> base_primes(long long limit) {
    std::vector<unsigned char> s(static_cast<size_t>(limit) + 1, 1);
    s[0] = 0;
    s[1] = 0;
    for (long long p = 2; p * p <= limit; ++p) {
        if (s[static_cast<size_t>(p)]) {
            for (long long m = p * p; m <= limit; m += p) s[static_cast<size_t>(m)] = 0;
        }
    }
    std::vector<int> bp;
    for (long long p = 2; p <= limit; ++p)
        if (s[static_cast<size_t>(p)]) bp.push_back(static_cast<int>(p));
    return bp;
}

void mark_serial(std::vector<unsigned char>& f, const std::vector<int>& bp) {
    f[0] = 0;
    f[1] = 0;
    for (size_t i = 0; i < bp.size(); ++i) {
        const long long p = bp[i];
        for (long long m = p * p; m <= N; m += p) f[static_cast<size_t>(m)] = 0;
    }
}

void mark_parallel(std::vector<unsigned char>& f, const std::vector<int>& bp, Sched sched, int chunk) {
    f[0] = 0;
    f[1] = 0;
    const int P = static_cast<int>(bp.size());
    if (sched == Sched::Static) {
#pragma omp parallel for num_threads(THREADS) schedule(static)
        for (int i = 0; i < P; ++i) {
            const long long p = bp[static_cast<size_t>(i)];
            for (long long m = p * p; m <= N; m += p) f[static_cast<size_t>(m)] = 0;
        }
    } else if (sched == Sched::Dynamic) {
#pragma omp parallel for num_threads(THREADS) schedule(dynamic, chunk)
        for (int i = 0; i < P; ++i) {
            const long long p = bp[static_cast<size_t>(i)];
            for (long long m = p * p; m <= N; m += p) f[static_cast<size_t>(m)] = 0;
        }
    } else {
#pragma omp parallel for num_threads(THREADS) schedule(guided, chunk)
        for (int i = 0; i < P; ++i) {
            const long long p = bp[static_cast<size_t>(i)];
            for (long long m = p * p; m <= N; m += p) f[static_cast<size_t>(m)] = 0;
        }
    }
}

long long count_primes(const std::vector<unsigned char>& f) {
    long long c = 0;
#pragma omp parallel for num_threads(THREADS) schedule(static) reduction(+ : c)
    for (long long i = 2; i <= N; ++i) c += f[static_cast<size_t>(i)];
    return c;
}

}

int main() {
    std::printf("Problem 3: Parallel Sieve of Eratosthenes  (N = %lld, flag array = %.0f MB, %d threads)\n",
                N, static_cast<double>(N + 1) / (1024.0 * 1024.0), THREADS);
    const std::vector<int> bp = base_primes(10000);
    std::printf("Base primes p <= sqrt(N) are found serially; the marking loop over that prime\n");
    std::printf("list (%zu primes up to 10000) is parallelized with static / dynamic / guided "
                "scheduling.  Expected pi(10^8) = %lld\n\n", bp.size(), EXPECTED_PI);

    std::vector<unsigned char> ref(static_cast<size_t>(N) + 1, 1);
    const double t0 = omp_get_wtime();
    mark_serial(ref, bp);
    const double serial_mark = omp_get_wtime() - t0;
    const double tc0 = omp_get_wtime();
    const long long serial_count = count_primes(ref);
    const double serial_count_time = omp_get_wtime() - tc0;
    std::printf("Serial marking time: %.4f s   primes found: %lld  %s\n",
                serial_mark, serial_count,
                serial_count == EXPECTED_PI ? "(matches pi(10^8))" : "(UNEXPECTED)");

    std::printf("\nUnequal marking cost across the range: N/p marks per base prime\n");
    std::printf("  p = %-6d -> %lld marks\n", bp[0], (N - 1LL * bp[0] * bp[0]) / bp[0] + 1);
    std::printf("  p = %-6d -> %lld marks   (smallest/largest ratio = %.0f : 1)\n",
                bp.back(), (N - 1LL * bp.back() * bp.back()) / bp.back() + 1,
                static_cast<double>(N / bp[0]) / static_cast<double>(N / bp.back()));

    double total_marks = 0.0;
    for (size_t i = 0; i < bp.size(); ++i) {
        const long long p = bp[i];
        total_marks += static_cast<double>((N - p * p) / p + 1);
    }
    const int np = static_cast<int>(bp.size());
    const int base_block = np / THREADS;
    const int rem_block = np % THREADS;
    const int first_size = base_block + (rem_block > 0 ? 1 : 0);
    const int last_size = base_block + (THREADS - 1 < rem_block ? 1 : 0);
    auto marks_of = [&](int from, int cnt) {
        double w = 0.0;
        for (int i = from; i < from + cnt && i < np; ++i) {
            const long long p = bp[static_cast<size_t>(i)];
            w += static_cast<double>((N - p * p) / p + 1);
        }
        return w;
    };
    const double static_first_thread = marks_of(0, first_size);
    const double static_last_thread = marks_of(np - last_size, last_size);
    std::printf("  static partition gives thread 0 %d primes = %.1f%% of all marking work, "
                "thread %d %d primes = %.2f%% (ideal %.0f%% each)\n",
                first_size, 100.0 * static_first_thread / total_marks,
                THREADS - 1, last_size, 100.0 * static_last_thread / total_marks,
                100.0 / THREADS);
    std::printf("  total marking work: %.2e locations\n\n", total_marks);

    std::printf("%14s %12s %10s %14s %10s %7s\n",
                "schedule", "time (s)", "speedup", "primes", "vs serial", "check");

    struct Row {
        const char* name;
        double time;
        bool ok;
    } rows[4];
    rows[0] = {"serial", serial_mark, serial_count == EXPECTED_PI};
    rows[1] = {"static", 0.0, false};
    rows[2] = {"dynamic", 0.0, false};
    rows[3] = {"guided", 0.0, false};

    bool all_ok = rows[0].ok;
    std::printf("%14s %12.4f %9s %14lld %10s %7s\n",
                "serial", serial_mark, "-", serial_count, "-", rows[0].ok ? "PASS" : "FAIL");

    std::vector<unsigned char> f(static_cast<size_t>(N) + 1, 1);
    const Sched scheds[3] = {Sched::Static, Sched::Dynamic, Sched::Guided};
    const char* names[3] = {"static", "dynamic", "guided"};
    for (int s = 0; s < 3; ++s) {
        std::fill(f.begin(), f.end(), static_cast<unsigned char>(1));
        const double t1 = omp_get_wtime();
        mark_parallel(f, bp, scheds[s], 16);
        rows[s + 1].time = omp_get_wtime() - t1;
        const long long c = count_primes(f);
        const bool same = std::memcmp(f.data(), ref.data(), static_cast<size_t>(N) + 1) == 0;
        rows[s + 1].ok = same && c == EXPECTED_PI;
        all_ok = all_ok && rows[s + 1].ok;
        std::printf("%14s %12.4f %9.2fx %14lld %10s %7s\n",
                    names[s], rows[s + 1].time, serial_mark / rows[s + 1].time, c,
                    same ? "identical" : "DIFFERS", rows[s + 1].ok ? "PASS" : "FAIL");
    }

    int best = 1;
    for (int s = 2; s < 4; ++s)
        if (rows[s].time < rows[best].time) best = s;
    const double stat = rows[1].time;
    const double bst = rows[best].time;
    const char* best_name = (best == 1) ? "static" : (best == 2) ? "dynamic" : "guided";

    std::printf("\nConclusion: %s scheduling is fastest (%.4f s vs %.4f s static, %.1f%% less "
                "time; serial marking %.4f s).\n",
                best_name, bst, stat, 100.0 * (stat - bst) / stat, serial_mark);
    if (best != 1) {
        std::printf("The marking cost of prime p is ~N/p, so the early primes dominate: a static "
                    "block of the prime list gives thread 0 %d primes = %.1f%% of all marking "
                    "while the last thread gets %.2f%%, so most cores sit idle. Dynamic hands "
                    "out one prime per dispatch and therefore spreads the expensive small primes "
                    "over all %d cores, which is why it cuts the time by %.1f%%.\n",
                    first_size, 100.0 * static_first_thread / total_marks,
                    100.0 * static_last_thread / total_marks, THREADS,
                    100.0 * (stat - bst) / stat);
        if (rows[3].time >= stat) {
            std::printf("Guided does not help here (%.4f s): its opening chunk is n/threads = %d "
                        "primes, i.e. it starts by handing thread 0 the same dominant block as "
                        "static, and only then shrinks the chunk - too late to fix the imbalance.\n",
                        rows[3].time, static_cast<int>((bp.size() + THREADS - 1) / THREADS));
        } else {
            std::printf("Guided (%.4f s) approaches dynamic because its shrinking chunks "
                        "redistribute the big early primes after the first round.\n",
                        rows[3].time);
        }
    } else {
        std::printf("With only %zu primes to schedule, the dispatch cost of dynamic/guided "
                    "outweighs their balance gain here, so static wins despite the %.1f%% / %.2f%% "
                    "work split between first and last thread; note guided still opens with a "
                    "chunk of %d primes, the same dominant block static would assign.\n",
                    bp.size(), 100.0 * static_first_thread / total_marks,
                    100.0 * static_last_thread / total_marks,
                    static_cast<int>((bp.size() + THREADS - 1) / THREADS));
    }

    std::printf("\n%s: parallel sieve is byte-for-byte identical to the serial sieve "
                "(%lld primes, counting done in %.4f s)\n",
                all_ok ? "PASS" : "FAIL", serial_count, serial_count_time);
    return all_ok ? 0 : 1;
}
